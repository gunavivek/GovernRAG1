#!/usr/bin/env python3
"""
B5_Build_Runner.py -- hardened build orchestrator (approved by Vivek 2026-07-19).
Wraps the FROZEN D/M build stages the way B4 wraps the serve stages. Frozen scripts
untouched. One command builds a corpus end-to-end with guards, live output, stall
detection, retries, stage checkpoints, and the B1 index snapshot at the end:

  python B5_Build_Runner.py --corpus expertqa_run2
  python B5_Build_Runner.py --corpus hagrid_run3            # run 3 = same one line
  (resume after any failure: rerun the SAME command -- completed stages are skipped)

HARDENING (all the things that cost 2026-07-18/19 a day):
  * SELF-ANCHORING: chdirs to its own repo root -- launching from a wrong folder is
    impossible; loads GEMINI_API_KEY itself from the repo .env (quote-safe) -- no ritual.
  * CORPUS GUARD: refuses to run M-stages unless output/D5_Extraction_Manifest.jsonl
    carries <CORPUS>_CORPUS -- the wrong-corpus class of error dies here.
  * KEY GUARD: --expect-key prefix check before any spend.
  * LIVE OUTPUT: every stage streamed unbuffered to console AND runs/B5_<corpus>/<stage>.log.
  * STALL WATCHDOG: a stage with no stdout, no output-file growth, and no process-tree
    CPU accrual for --stall-minutes (default 10) is killed and retried (max 2) --
    a dead socket costs minutes, not an afternoon.
  * HARD CAPS: per-stage wall-clock ceilings; exceeding one kills + retries.
  * CHECKPOINTS: results/b5_state_<corpus>.json marks completed stages; reruns resume.
  * FLIGHT CARD: expected calls/duration/output printed before each stage spends money.
  * FINISH: runs B1_Build_Index.py <corpus> --skip-build automatically (index snapshot).
"""
import argparse, json, os, re, subprocess, sys, threading, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "experiment"
OUT = ROOT / "output"
RES = ROOT / "results"

# name, script, hard-cap minutes, flight card (expectation printed before launch), watch file
STAGES = [
    ("M1",   "M1_Gov_Chunking_V5.py",                     300, "LLM chunking: ~(evidence/6KB) x domains calls, sequential ~6-15s each; SILENT until each domain completes; CSV written only at the END", "M1_Governed_Chunks.csv"),
    ("M1.5", "M1_5_Gov_Chunking_Audit.py",                 15, "local lineage audit, seconds, no LLM",                            "M1_Governed_Chunks.csv"),
    ("M2",   "M2_Gov_Extraction_v4_Async.py",             180, "ASYNC triple extraction: many concurrent LLM calls; fast counter growth; prints per batch", "M2_telemetry.json"),
    ("M3",   "M3_Gov_Graph_Construction_V4.py",            60, "local graph construction, minutes, no LLM",                       None),
    ("M3.3", "M3.3_Gov_Concept_Augmentation_V3_HARDENED.py", 240, "LLM concept augmentation, HARDENED (retry+checkpoint)",       None),
    ("M4",   "M4_Gov_Concept_Alignment_V3_PARALLEL.py",    240, "PARALLEL ontological alignment (Sprint-1, output-equivalent)",   None),
    ("M5",   "M5_Gov_Graph_Embedding_V4_HARDENED.py",      180, "graph embedding, HARDENED; writes M5_Embedded_Graph.graphml",    "M5_Embedded_Graph.graphml"),
]
MAX_ATTEMPTS = 3          # 1 try + 2 retries per stage
POLL_SECONDS = 15


def load_repo_env():
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*GEMINI_API_KEY\s*=\s*(.+)\s*$", line)
            if m:
                os.environ["GEMINI_API_KEY"] = m.group(1).strip().strip('"').strip("'")


def corpus_guard(corpus):
    man = OUT / "D5_Extraction_Manifest.jsonl"
    if not man.exists():
        sys.exit("[B5][GUARD] no D5 manifest in output/ -- run the D stages first (D1 then D0).")
    rec = json.loads(man.open(encoding="utf-8").readline())
    want = "%s_CORPUS" % corpus.split("_")[0].upper()
    got = str(rec.get("record_id", ""))
    if got != want:
        sys.exit("[B5][GUARD] D5 manifest is for %r but --corpus expects %r.\n"
                 "REFUSING to build the wrong corpus. Re-run D stages for this corpus first." % (got, want))
    return got, [d.get("domain") for d in rec.get("governance_profile", [])]


def tree_cpu(pid):
    try:
        import psutil
        p = psutil.Process(pid)
        total = p.cpu_times().user + p.cpu_times().system
        for c in p.children(recursive=True):
            try:
                total += c.cpu_times().user + c.cpu_times().system
            except Exception:
                pass
        return total
    except Exception:
        return None


def kill_tree(pid):
    try:
        import psutil
        p = psutil.Process(pid)
        for c in p.children(recursive=True):
            try: c.kill()
            except Exception: pass
        p.kill()
    except Exception:
        pass


def run_stage(name, script, cap_min, watch_file, log_path, stall_minutes):
    path = EXP / script
    if not path.exists():
        return "MISSING", 0.0, "script not found: %s" % path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    last_signal = time.time()
    proc = subprocess.Popen([sys.executable, "-u", str(path)], cwd=str(ROOT),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", bufsize=1)

    def pump():
        nonlocal last_signal
        with log_path.open("a", encoding="utf-8") as lf:
            for line in proc.stdout:
                lf.write(line); lf.flush()
                print("  | " + line.rstrip(), flush=True)
                last_signal = time.time()
    t = threading.Thread(target=pump, daemon=True); t.start()

    wf = (OUT / watch_file) if watch_file else None
    wf_last = wf.stat().st_mtime if (wf and wf.exists()) else None
    cpu_last = tree_cpu(proc.pid)

    while proc.poll() is None:
        time.sleep(POLL_SECONDS)
        now = time.time()
        # signal 2: watched output file growing
        if wf and wf.exists():
            m = wf.stat().st_mtime
            if wf_last is None or m > wf_last:
                wf_last = m; last_signal = now
        # signal 3: process-tree CPU accruing (the hung-socket detector)
        c = tree_cpu(proc.pid)
        if c is not None and cpu_last is not None and c > cpu_last + 0.05:
            last_signal = now
        if c is not None:
            cpu_last = c
        stalled = (now - last_signal) > stall_minutes * 60
        over_cap = (now - t0) > cap_min * 60
        if stalled or over_cap:
            reason = "STALLED %.0f min (no output, no file growth, no CPU)" % ((now - last_signal) / 60) \
                     if stalled else "exceeded hard cap %d min" % cap_min
            kill_tree(proc.pid)
            return "KILLED", time.time() - t0, reason
    t.join(timeout=5)
    rc = proc.returncode
    return ("SUCCESS" if rc == 0 else "FAILED"), time.time() - t0, "exit code %s" % rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="e.g. expertqa_run2, hagrid_run3")
    ap.add_argument("--expect-key", default=None, help="required key prefix, e.g. AIzaSyDhK")
    ap.add_argument("--stall-minutes", type=float, default=10.0)
    ap.add_argument("--from-stage", default=None, help="force start at this stage (overrides checkpoint)")
    ap.add_argument("--no-snapshot", action="store_true", help="skip the B1 index snapshot at the end")
    args = ap.parse_args()

    os.chdir(ROOT)                          # self-anchoring: wrong launch folder is impossible
    load_repo_env()                         # key from repo .env: no terminal ritual required
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        sys.exit("[B5][GUARD] no GEMINI_API_KEY in repo .env -- refusing to run.")
    if args.expect_key and not key.startswith(args.expect_key):
        sys.exit("[B5][GUARD] key prefix %r != expected %r -- wrong key for this run." % (key[:10], args.expect_key))

    rid, domains = corpus_guard(args.corpus)
    state_path = RES / ("b5_state_%s.json" % args.corpus)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"corpus": args.corpus, "done": [], "log": []}
    if state.get("corpus") != args.corpus:
        sys.exit("[B5][GUARD] state file %s belongs to %r -- refusing." % (state_path, state.get("corpus")))

    logdir = ROOT / "runs" / ("B5_%s_%s" % (args.corpus, datetime.now().strftime("%Y%m%d_%H%M%S")))
    started = args.from_stage is None
    print("=" * 74)
    print(" B5 HARDENED BUILD  corpus=%s  manifest=%s  domains=%s" % (args.corpus, rid, domains))
    print(" repo=%s  key=%s...  stall-limit=%d min  logs=%s" % (ROOT, key[:10], args.stall_minutes, logdir))
    print(" completed stages (checkpoint): %s" % (state["done"] or "none"))
    print("=" * 74)

    for name, script, cap, card, watch in STAGES:
        if args.from_stage and not started:
            if name == args.from_stage:
                started = True
            else:
                print("[B5] %-5s skipped (--from-stage %s)" % (name, args.from_stage)); continue
        if name in state["done"] and not (args.from_stage == name):
            print("[B5] %-5s already complete (checkpoint) -- skipping" % name); continue

        print("\n" + "-" * 74)
        print("[B5] STAGE %s :: %s" % (name, script))
        print("[B5] EXPECT: %s" % card)
        print("[B5] hard cap %d min | stall kill after %d min of silence | attempts %d" % (cap, args.stall_minutes, MAX_ATTEMPTS))
        print("-" * 74, flush=True)

        ok = False
        for attempt in range(1, MAX_ATTEMPTS + 1):
            status, secs, why = run_stage(name, script, cap, watch, logdir / ("%s_attempt%d.log" % (name.replace('.', '_'), attempt)), args.stall_minutes)
            entry = {"stage": name, "attempt": attempt, "status": status, "minutes": round(secs / 60, 1),
                     "why": why, "at": datetime.now().isoformat(timespec="seconds")}
            state["log"].append(entry)
            state_path.parent.mkdir(exist_ok=True)
            state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
            print("[B5] %s attempt %d -> %s (%.1f min) %s" % (name, attempt, status, secs / 60, why))
            if status == "SUCCESS":
                ok = True; break
            if status == "MISSING":
                sys.exit("[B5][FATAL] %s" % why)
            if attempt < MAX_ATTEMPTS:
                print("[B5] retrying %s in 30s ..." % name); time.sleep(30)
        if not ok:
            sys.exit("[B5][HALT] stage %s failed %d attempts. Fix and rerun the SAME command -- "
                     "completed stages will be skipped. Logs: %s" % (name, MAX_ATTEMPTS, logdir))
        state["done"].append(name)
        state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")

    print("\n[B5] all build stages complete.")
    if not args.no_snapshot:
        print("[B5] snapshotting via B1_Build_Index.py %s --skip-build" % args.corpus)
        rc = subprocess.run([sys.executable, "-u", str(ROOT / "B1_Build_Index.py"), args.corpus, "--skip-build"],
                            cwd=str(ROOT)).returncode
        if rc != 0:
            sys.exit("[B5][WARN] B1 snapshot failed (exit %d) -- run it manually." % rc)
    print("[B5] DONE. Build state: %s | stage logs: %s" % (state_path, logdir))


if __name__ == "__main__":
    main()
