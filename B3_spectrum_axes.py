#!/usr/bin/env python3
"""
B3_spectrum_axes.py -- like B3_spectrum.py, but sweeps a list of NAMED CONFIGS instead of
just the G0..G4 strictness levels, so the two ontology-derived axes (Axis A ontology
conformance via GOVRAG_ONTOLOGY, Axis B domain affinity via GOVRAG_AFFINITY_MIN) can be
exercised on top of a base level. For each governed config this re-runs ONLY Q5 + Q6 with
the config's env vars, caches answers AND the per-record evidence-set reduction, then scores
every config stratified by answerability and reports BOTH the risk-coverage frontier and the
mean evidence-set reduction (so the "scopes evidence, not answers" claim has numbers).

PRE-REQS: apply_q3_ontology_tag.py + apply_q5_axes.py + apply_q5_evidence_log.py applied, then
B2 re-run once so Q3 emits alignment-tagged triplets. Also apply_q6_levels.py + apply_q5_g1.py.

RUN from repo root:
  python B3_spectrum_axes.py --judge-model gemini-2.5-pro
  python B3_spectrum_axes.py --no-trace --judge-model gemini-2.5-flash   # fast dry pass
  python B3_spectrum_axes.py --regen ...                                 # force Q5+Q6 (needed once
                                                                         # after adding the evlog patch)
"""
import argparse, json, os, re, statistics as st, subprocess, sys
from pathlib import Path
import trace_scorer as ts

TAU = os.getenv("SWEEP_TAU", "0.35")
CONFIGS = [
    ("G0_Naive",     None),
    ("G1_Cited",     {"GOVRAG_LEVEL": "G1"}),
    ("G2_Grounded",  {"GOVRAG_LEVEL": "G2"}),
    ("G3_Strict",    {"GOVRAG_LEVEL": "G3"}),
    ("G4_Corrob",    {"GOVRAG_LEVEL": "G4"}),
    ("G2+OntNU",     {"GOVRAG_LEVEL": "G2", "GOVRAG_ONTOLOGY": "not_unmapped"}),
    ("G2+OntConf",   {"GOVRAG_LEVEL": "G2", "GOVRAG_ONTOLOGY": "conformant"}),
    ("G2+Aff",       {"GOVRAG_LEVEL": "G2", "GOVRAG_AFFINITY_MIN": TAU}),
    ("G2+OntNU+Aff", {"GOVRAG_LEVEL": "G2", "GOVRAG_ONTOLOGY": "not_unmapped", "GOVRAG_AFFINITY_MIN": TAU}),
]
RED_KEYS = ["predicate_triplets_dropped", "ontology_triplets_dropped", "affinity_chunks_dropped",
            "chunks_dropped_total", "triplets_kept", "primary_chunks_kept"]

def find_root(start):
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start

ROOT = find_root(Path.cwd()); EXP = ROOT / "experiment"; OUT = ROOT / "output"; RES = ROOT / "results"

def load_jsonl(p):
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    return rows

def run_stage(script, envd):
    env = dict(os.environ); env.update({k: str(v) for k, v in envd.items()})
    cmd = [sys.executable, "-u", str(EXP / script)]
    return subprocess.run(cmd, cwd=str(ROOT), env=env).returncode == 0

def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name)

def read_reduction():
    """Pull audit_metadata.evidence_reduction from the just-written Q5 routed context."""
    reds = []
    for r in load_jsonl(OUT / "Q5_routed_context.jsonl"):
        er = (r.get("audit_metadata") or {}).get("evidence_reduction")
        if er:
            reds.append(er)
    return reds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="gemini-2.5-pro")
    ap.add_argument("--serve", default=str(RES / "serve_results.jsonl"))
    ap.add_argument("--gold-map", default=str(RES / "gold_map.json"))
    ap.add_argument("--regen", action="store_true", help="force re-run Q5+Q6 even if a config cache exists")
    ap.add_argument("--no-trace", action="store_true", help="skip faithfulness (TRACe) judging -> ~2x faster")
    args = ap.parse_args()

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    serve = load_jsonl(args.serve)
    gold_map = json.load(open(args.gold_map, encoding="utf-8")) if os.path.exists(args.gold_map) else {}
    if not serve:
        sys.exit("[FATAL] no serve_results.jsonl -- run B2 first.")
    names = [c[0] for c in CONFIGS]
    print("[B3ax] %d questions | judge=%s | configs=%s" % (len(serve), args.judge_model, names))

    # 1) run Q5+Q6 per governed config (answers + evidence-reduction cached; reuse unless --regen)
    cfg_ans = {n: {} for n, _ in CONFIGS}
    cfg_red = {n: [] for n, _ in CONFIGS}
    for name, envd in CONFIGS:
        if envd is None:
            continue
        cache = RES / ("_spec_%s.jsonl" % slug(name))
        redcache = RES / ("_spec_%s_red.jsonl" % slug(name))
        if cache.exists() and not args.regen:
            for r in load_jsonl(cache):
                cfg_ans[name][str(r.get("record_id"))] = r
            cfg_red[name] = load_jsonl(redcache)
            note = "" if cfg_red[name] else " (no reduction snapshot -- re-run with --regen after apply_q5_evidence_log.py)"
            print("[B3ax] === %s : reused cache (%d answers)%s ===" % (name, len(cfg_ans[name]), note))
            continue
        print("[B3ax] === %s : running Q5 + Q6  env=%s ===" % (name, envd))
        if not run_stage("Q5_Gov_Context_Router.py", envd):
            print("[WARN] Q5 failed at %s" % name); continue
        reds = read_reduction()                       # snapshot BEFORE Q6 overwrites nothing (Q5 output is stable)
        if not run_stage("Q6_Gov_Answer_Generation.py", envd):
            print("[WARN] Q6 failed at %s" % name); continue
        answers = load_jsonl(OUT / "Q6_final_answers.jsonl")
        with open(cache, "w", encoding="utf-8") as f:
            for r in answers:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(redcache, "w", encoding="utf-8") as f:
            for r in reds:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        cfg_red[name] = reds
        for r in answers:
            cfg_ans[name][str(r.get("record_id"))] = r

    # 2) score every config, stratified by answerability
    per = {n: {"total": 0, "answered": 0, "adh_total": 0, "adh_match": 0, "faith": []} for n in names}
    detail = []
    print("[B3ax] scoring %d questions x %d configs with %s%s ..."
          % (len(serve), len(names), args.judge_model, " (no TRACe)" if args.no_trace else ""))
    for i, row in enumerate(serve):
        idx = str(row.get("idx")); rid = "delucionqa_q%05d" % int(idx)
        q = row.get("question", "")
        g = gold_map.get(ts.norm_q(q), {})
        gold = g.get("gold_response", row.get("gold", "")); answerable = g.get("answerable")
        naive = row.get("naive", {})
        rec = {"idx": idx, "question": q, "answerable": answerable, "configs": {}}
        for name, envd in CONFIGS:
            if envd is None:
                ans = naive.get("answer", ""); mode = ""; ctx = naive.get("context", "")
            else:
                o = cfg_ans[name].get(rid, {})
                ans = o.get("generated_answer", ""); mode = o.get("mode", "")
                ctx = o.get("final_prompt", "") or ""
            refused = str(mode).startswith("BLOCKED") or ts.is_refusal(ans, mode)
            verdict = "SAFE_SILENCE" if refused else ts.correctness(gold, ans, mode, args.judge_model, client, types)
            trace = None if (refused or args.no_trace) else ts.judge_tuple(q, ctx, ans, args.judge_model, client, types)
            s = per[name]; s["total"] += 1
            if not refused:
                s["answered"] += 1
                if trace:
                    s["faith"].append(trace["adherence"])
            if answerable is True:
                s["adh_total"] += 1
                if verdict == "MATCH":
                    s["adh_match"] += 1
            rec["configs"][name] = {"refused": refused, "verdict": verdict,
                                    "adherence": (trace["adherence"] if trace else None)}
        detail.append(rec)
        print("  [score] %d/%d" % (i + 1, len(serve)))

    RES.mkdir(exist_ok=True)
    with open(RES / "spectrum_axes_scores.jsonl", "w", encoding="utf-8") as f:
        for r in detail:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 3) frontier
    print("\n" + "=" * 82)
    print("GOVERNANCE SPECTRUM + ONTOLOGY AXES (through frozen pipeline)   N=%d" % len(serve))
    print("=" * 82)
    print("%-16s %10s %14s %14s" % ("config", "coverage", "accuracy(adh)", "faithfulness"))
    out = [("config", "coverage", "accuracy_adherent", "faithfulness")]
    for name in names:
        s = per[name]
        cov = s["answered"] / s["total"] if s["total"] else 0.0
        acc = s["adh_match"] / s["adh_total"] if s["adh_total"] else 0.0
        faith = st.mean(s["faith"]) if s["faith"] else float("nan")
        print("%-16s %9.0f%% %13.0f%% %14.3f" % (name, 100 * cov, 100 * acc, faith))
        out.append((name, "%.4f" % cov, "%.4f" % acc, "%.4f" % (faith if faith == faith else 0)))
    with open(RES / "spectrum_axes_frontier.csv", "w", encoding="utf-8") as f:
        for r in out:
            f.write(",".join(map(str, r)) + "\n")

    # 4) evidence-set reduction table (mean dropped per record) -- the "scopes evidence" numbers
    def mean(xs): return (sum(xs) / len(xs)) if xs else float("nan")
    print("\n" + "=" * 82)
    print("EVIDENCE-SET REDUCTION (mean per record; how much each setting SCOPES the evidence)")
    print("=" * 82)
    print("%-16s %8s %8s %8s %9s %9s %9s" %
          ("config", "predTrp", "ontTrp", "affChk", "chkTot", "trpKept", "chkKept"))
    rout = [("config",) + tuple(RED_KEYS)]
    for name, envd in CONFIGS:
        if envd is None:
            print("%-16s %8s" % (name, "(naive: ungoverned, no reduction)")); continue
        reds = cfg_red.get(name, [])
        if not reds:
            print("%-16s  %s" % (name, "(no snapshot -- run once with --regen after apply_q5_evidence_log.py)"))
            rout.append((name,) + tuple("" for _ in RED_KEYS)); continue
        m = {k: mean([r.get(k, 0) for r in reds]) for k in RED_KEYS}
        print("%-16s %8.2f %8.2f %8.2f %9.2f %9.2f %9.2f" %
              (name, m["predicate_triplets_dropped"], m["ontology_triplets_dropped"],
               m["affinity_chunks_dropped"], m["chunks_dropped_total"],
               m["triplets_kept"], m["primary_chunks_kept"]))
        rout.append((name,) + tuple("%.4f" % m[k] for k in RED_KEYS))
    with open(RES / "evidence_reduction.csv", "w", encoding="utf-8") as f:
        for r in rout:
            f.write(",".join(map(str, r)) + "\n")
    print("-" * 82)
    print("[B3ax] frontier -> results/spectrum_axes_frontier.csv ; scores -> results/spectrum_axes_scores.jsonl")
    print("[B3ax] evidence reduction -> results/evidence_reduction.csv")
    print("READ: if ontTrp/affChk > 0 while accuracy/faithfulness are flat vs G2 -> the axes SCOPE evidence")
    print("      without changing the answer (dissociation). If they are 0 -> filters were inert on this data.")
    print("NOTE: output/Q5_*, Q6_* now reflect the LAST config. Re-run B2 to restore a single-level state.")

if __name__ == "__main__":
    main()
