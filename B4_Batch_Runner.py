#!/usr/bin/env python3
"""
B4_Batch_Runner.py -- drives the FULL DelucionQA evaluation in K-record batches (912 records,
K=25 -> 37 batches). Written to replace the batch driver lost with the previous session.

Per batch (offset = b*K):
  1. B2_Serve.py --records <csv> --offset <o> --limit <K>   (stages the slice, runs the frozen
     Q1..Q6 governed pipeline + naive baseline; writes results/serve_results.jsonl for the batch)
  2. For each governed config (same list as B3_spectrum_axes/E3): re-run Q5 with the config's
     env vars, snapshot the evidence reduction from output/Q5_routed_context.jsonl, re-run Q6,
     collect output/Q6_final_answers.jsonl.  GENERATION ONLY -- no judging here; E3 is the scorer.
  3. Append the batch's serve rows + per-config answers/reductions to results/full_run/*_all.jsonl.
  4. Mark the batch complete in results/full_run/state.json  ->  the run is RESUMABLE: rerun the
     same command after a crash and finished batches are skipped.

After the last batch: merged copies (deduped by record id, first occurrence wins) are written to
the canonical paths E3 reads -- results/serve_results.jsonl, results/_spec_<cfg>.jsonl,
results/_spec_<cfg>_red.jsonl -- and the E3 command is printed (or run with --run-e3).

RUN from repo root:
  python B4_Batch_Runner.py --records "data\expertqa_run2_records.csv" --k 25 --run-tag run2_expertqa
  python B4_Batch_Runner.py ... --batches 0          # smoke test batch 0 only

RUN GUARD (added 2026-07-12, approved by Vivek): --run-tag is REQUIRED. All accumulators
live in results\full_run_<tag>\; B4 REFUSES to start if that folder belongs to a different
records file (no silent resets, no cross-dataset mixing). Merged outputs are written BOTH
to the canonical results\ names (working slot, for the scorer) AND archived automatically
to results\<tag>\ together with the gold map and records checksum context.

PRE-REQS: build_gold_map.py done (results/gold_map.json), serve map present
(output/serve_question_chunk_map.jsonl), preflight_check.py says READY.
"""
import argparse, csv, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

csv.field_size_limit(10_000_000)

TAU = os.getenv("SWEEP_TAU", "0.35")
CONFIGS = [  # must stay in lockstep with B3_spectrum_axes.py / E3_Unified_Evaluation.py
    ("G1_Cited",     {"GOVRAG_LEVEL": "G1"}),
    ("G2_Grounded",  {"GOVRAG_LEVEL": "G2"}),
    ("G3_Strict",    {"GOVRAG_LEVEL": "G3"}),
    ("G4_Corrob",    {"GOVRAG_LEVEL": "G4"}),
    ("G2+OntNU",     {"GOVRAG_LEVEL": "G2", "GOVRAG_ONTOLOGY": "not_unmapped"}),
    ("G2+OntConf",   {"GOVRAG_LEVEL": "G2", "GOVRAG_ONTOLOGY": "conformant"}),
    ("G2+Aff",       {"GOVRAG_LEVEL": "G2", "GOVRAG_AFFINITY_MIN": TAU}),
    ("G2+OntNU+Aff", {"GOVRAG_LEVEL": "G2", "GOVRAG_ONTOLOGY": "not_unmapped", "GOVRAG_AFFINITY_MIN": TAU}),
]


def find_root(start):
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start


ROOT = find_root(Path.cwd()); EXP = ROOT / "experiment"; OUT = ROOT / "output"
RES = ROOT / "results"
FULL = None   # set per --run-tag in main(): results/full_run_<tag>/
STATE = None


def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name)


def load_jsonl(p):
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_jsonl(p, rows):
    with open(p, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


TIMING_LOG = None   # set per --run-tag in main(): execution log batch,phase,config,seconds,n_records,ok,when


def log_timing(batch, phase, config, seconds, n_records, ok=True):
    new = not TIMING_LOG.exists()
    with open(TIMING_LOG, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["batch", "phase", "config", "seconds", "n_records", "ok", "when"])
        w.writerow([batch, phase, config, "%.3f" % seconds, n_records, ok,
                    time.strftime("%Y-%m-%d %H:%M:%S")])


def run(cmd, envd=None):
    env = dict(os.environ)
    if envd:
        env.update({k: str(v) for k, v in envd.items()})
    return subprocess.run(cmd, cwd=str(ROOT), env=env).returncode == 0


def read_reduction():
    reds = []
    for r in load_jsonl(OUT / "Q5_routed_context.jsonl"):
        er = (r.get("audit_metadata") or {}).get("evidence_reduction")
        if er:
            reds.append(er)
    return reds


def load_state(records, k, tag):
    if STATE.exists():
        s = json.load(open(STATE, encoding="utf-8"))
        if s.get("records") == records and s.get("k") == k:
            return s
        sys.exit("[B4][GUARD] results/full_run_%s belongs to a DIFFERENT run:\n"
                 "  existing: records=%s k=%s\n  requested: records=%s k=%s\n"
                 "REFUSING to mix runs. Use a new --run-tag (or move that folder aside deliberately)."
                 % (tag, s.get("records"), s.get("k"), records, k))
    # brand-new tag: refuse if leftover accumulators exist without a state file (half-copied dir)
    stray = list(FULL.glob("*_all.jsonl"))
    if stray:
        sys.exit("[B4][GUARD] results/full_run_%s has %d accumulator file(s) but no state.json -- "
                 "refusing to append blindly. Inspect or remove that folder first." % (tag, len(stray)))
    return {"records": records, "k": k, "tag": tag, "done": []}


def save_state(s):
    tmp = FULL / "state.tmp"
    tmp.write_text(json.dumps(s, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


def merge(all_path, out_path, idkey):
    """Dedup by record id (first occurrence wins -- protects against a re-appended crash batch).
    Rows WITHOUT the id key (e.g. evidence-reduction snapshots) are kept as-is, never deduped."""
    seen, out = set(), []
    for r in load_jsonl(all_path):
        k = r.get(idkey)
        if k is None:
            out.append(r); continue
        if str(k) in seen:
            continue
        seen.add(str(k)); out.append(r)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(out)


def main():
    global FULL, STATE, TIMING_LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--run-tag", required=True,
                    help="run identifier, e.g. run2_expertqa -- isolates accumulators and auto-archives outputs")
    ap.add_argument("--k", type=int, default=25)
    ap.add_argument("--batches", type=int, nargs="*", default=None,
                    help="explicit batch indices to run (default: all remaining)")
    ap.add_argument("--run-e3", action="store_true", help="run E3_Unified_Evaluation.py after the merge")
    ap.add_argument("--judge-model", default="gemini-2.5-pro")
    ap.add_argument("--no-linking", action="store_true", help="pass through to B2 (ablation)")
    args = ap.parse_args()

    tag = re.sub(r"[^A-Za-z0-9_]+", "_", args.run_tag)
    FULL = RES / ("full_run_%s" % tag); FULL.mkdir(parents=True, exist_ok=True)
    STATE = FULL / "state.json"
    TIMING_LOG = FULL / "timing_log.csv"

    if not os.path.exists(args.records):
        sys.exit("[B4][FATAL] records not found: %s" % args.records)
    rows = list(csv.DictReader(open(args.records, encoding="utf-8")))
    total = len(rows); k = args.k
    nb = (total + k - 1) // k
    state = load_state(os.path.abspath(args.records), k, tag)
    todo = args.batches if args.batches is not None else [b for b in range(nb) if b not in state["done"]]
    todo = [b for b in todo if b not in state["done"]]
    print("[B4] %d records, K=%d -> %d batches | done=%d | running %d: %s"
          % (total, k, nb, len(state["done"]), len(todo), todo[:12] + (["..."] if len(todo) > 12 else [])))

    for b in todo:
        off = b * k
        t0 = time.time()
        print("\n" + "=" * 70)
        print("[B4] BATCH %d/%d  offset=%d  limit=%d" % (b + 1, nb, off, k))
        print("=" * 70)

        # 1) serve the slice through the full governed pipeline + naive baseline
        cmd = [sys.executable, "-u", str(ROOT / "B2_Serve.py"), "--records", args.records,
               "--offset", str(off), "--limit", str(k)]
        if args.no_linking:
            cmd.append("--no-linking")
        tb2 = time.perf_counter()
        ok = run(cmd)
        log_timing(b, "B2_serve", "", time.perf_counter() - tb2, k, ok)
        if not ok:
            sys.exit("[B4][FATAL] B2_Serve failed on batch %d -- fix and rerun (this batch will retry)." % b)
        serve_rows = load_jsonl(RES / "serve_results.jsonl")
        if not serve_rows:
            sys.exit("[B4][FATAL] batch %d produced no serve_results rows." % b)
        # fold B2's per-stage detail (Q1..Q6) into the execution log
        for t in (load_jsonl(RES / "serve_stage_timings.jsonl")[:1] or [{}]):
            for s in t.get("stages", []):
                log_timing(b, "B2_stage:%s" % s.get("stage"), "", s.get("seconds", 0),
                           len(serve_rows), s.get("ok", True))

        # 2) per-config Q5+Q6 regeneration (generation only; E3 judges later)
        batch_cfg = {}
        for name, envd in CONFIGS:
            print("[B4] --- config %-14s env=%s" % (name, envd))
            t5 = time.perf_counter()
            ok = run([sys.executable, "-u", str(EXP / "Q5_Gov_Context_Router.py")], envd)
            log_timing(b, "Q5", name, time.perf_counter() - t5, len(serve_rows), ok)
            if not ok:
                sys.exit("[B4][FATAL] Q5 failed (batch %d, %s) -- rerun to retry this batch." % (b, name))
            reds = read_reduction()
            t6 = time.perf_counter()
            ok = run([sys.executable, "-u", str(EXP / "Q6_Gov_Answer_Generation.py")], envd)
            log_timing(b, "Q6", name, time.perf_counter() - t6, len(serve_rows), ok)
            if not ok:
                sys.exit("[B4][FATAL] Q6 failed (batch %d, %s) -- rerun to retry this batch." % (b, name))
            batch_cfg[name] = (load_jsonl(OUT / "Q6_final_answers.jsonl"), reds)

        # 3) append everything for this batch, then 4) checkpoint
        append_jsonl(FULL / "serve_results_all.jsonl", serve_rows)
        for name, (answers, reds) in batch_cfg.items():
            append_jsonl(FULL / ("_spec_%s_all.jsonl" % slug(name)), answers)
            append_jsonl(FULL / ("_spec_%s_red_all.jsonl" % slug(name)), reds)
        state["done"] = sorted(set(state["done"]) | {b})
        save_state(state)
        log_timing(b, "BATCH_TOTAL", "", time.time() - t0, len(serve_rows))
        done_n = len(state["done"])
        elapsed_min = (time.time() - t0) / 60
        print("[B4] batch %d done in %.1f min  (%d/%d batches complete; ~%.1f h remaining at this pace)"
              % (b, elapsed_min, done_n, nb, elapsed_min * (nb - done_n) / 60))

    if len(state["done"]) < nb:
        print("\n[B4] stopped with %d/%d batches complete -- rerun the same command to continue."
              % (len(state["done"]), nb))
        return

    # 5) merge accumulators into the canonical paths (working slot) AND the per-run archive
    ARCH = RES / tag; ARCH.mkdir(parents=True, exist_ok=True)
    print("\n[B4] all %d batches complete -- merging into results/ (working) + results/%s/ (archive)" % (nb, tag))
    n = merge(FULL / "serve_results_all.jsonl", RES / "serve_results.jsonl", "idx")
    shutil.copy(RES / "serve_results.jsonl", ARCH / "serve_results.jsonl")
    print("[B4]   serve_results.jsonl: %d records" % n)
    for name, _ in CONFIGS:
        s = slug(name)
        na = merge(FULL / ("_spec_%s_all.jsonl" % s), RES / ("_spec_%s.jsonl" % s), "record_id")
        nr = merge(FULL / ("_spec_%s_red_all.jsonl" % s), RES / ("_spec_%s_red.jsonl" % s), "record_id")
        shutil.copy(RES / ("_spec_%s.jsonl" % s), ARCH / ("_spec_%s.jsonl" % s))
        shutil.copy(RES / ("_spec_%s_red.jsonl" % s), ARCH / ("_spec_%s_red.jsonl" % s))
        print("[B4]   %-14s answers=%d reductions=%d" % (name, na, nr))
    for extra in ("gold_map.json",):
        if (RES / extra).exists():
            shutil.copy(RES / extra, ARCH / extra)
    shutil.copy(STATE, ARCH / "state.json")
    if TIMING_LOG.exists():
        shutil.copy(TIMING_LOG, ARCH / "timing_log.csv")
    print("[B4] archive -> %s (records CSV: %s)" % (ARCH, os.path.abspath(args.records)))

    # 6) score (checkpointed parallel scorer; sequential E3 kept via --run-e3 for compatibility)
    e3p = [sys.executable, "-u", str(ROOT / "E3_Parallel_Evaluation.py"),
           "--judge-model", args.judge_model, "--workers", "12", "--out-prefix", "E3_%s" % tag]
    if args.run_e3:
        print("[B4] running sequential E3 (legacy) ...")
        if not run([sys.executable, "-u", str(ROOT / "E3_Unified_Evaluation.py"), "--judge-model", args.judge_model]):
            sys.exit("[B4][FATAL] E3 failed -- caches are merged, rerun the scorer alone.")
    else:
        print("[B4] NEXT (recommended): %s" % " ".join(e3p))


if __name__ == "__main__":
    main()
