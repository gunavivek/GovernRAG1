#!/usr/bin/env python3
"""
B3_spectrum.py -- run the REAL governance spectrum G0..G4 through the (parameterized)
frozen pipeline, then score + plot the risk-coverage frontier.

Requires the level patches applied (apply_q6_levels.py, apply_q5_g1.py) and the last
serve run's intermediates present (output/Q3_retrieved_evidence.jsonl, output/
D5_Extraction_Manifest.jsonl, results/serve_results.jsonl, results/gold_map.json).

Q1-Q3 are level-independent (already produced). For each GOVERNED level this re-runs
ONLY Q5 + Q6 with GOVRAG_LEVEL set, and reads that level's answers. G0 = naive (reused).

RUN from repo root:
  python B3_spectrum.py --judge-model gemini-2.5-pro
"""
import argparse, json, os, statistics as st, subprocess, sys
from pathlib import Path
import trace_scorer as ts

GOV_LEVELS = ["G1", "G2", "G3", "G4"]
ALL_LEVELS = ["G0"] + GOV_LEVELS
NAMES = {"G0": "G0_Naive", "G1": "G1_Cited", "G2": "G2_Grounded", "G3": "G3_Strict", "G4": "G4_Corrob"}


def find_root(start):
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start


ROOT = find_root(Path.cwd())
EXP = ROOT / "experiment"
OUT = ROOT / "output"
RES = ROOT / "results"


def load_jsonl(p):
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_stage(script, level):
    env = dict(os.environ); env["GOVRAG_LEVEL"] = level
    cmd = [sys.executable, "-u", str(EXP / script)]
    return subprocess.run(cmd, cwd=str(ROOT), env=env).returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="gemini-2.5-pro")
    ap.add_argument("--serve", default=str(RES / "serve_results.jsonl"))
    ap.add_argument("--gold-map", default=str(RES / "gold_map.json"))
    ap.add_argument("--regen", action="store_true", help="force re-run Q5+Q6 even if a level cache exists")
    ap.add_argument("--no-trace", action="store_true", help="skip faithfulness (TRACe) judging -> ~2x faster")
    args = ap.parse_args()

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    serve = load_jsonl(args.serve)
    gold_map = json.load(open(args.gold_map, encoding="utf-8")) if os.path.exists(args.gold_map) else {}
    if not serve:
        sys.exit("[FATAL] no serve_results.jsonl -- run B2 first.")
    print("[B3] %d questions | judge=%s | levels=%s" % (len(serve), args.judge_model, ALL_LEVELS))

    # 1) run Q5+Q6 per governed level (cached; reuse unless --regen), collect answers by record_id
    level_ans = {L: {} for L in GOV_LEVELS}
    for L in GOV_LEVELS:
        cache = RES / ("_spec_%s.jsonl" % L)
        if cache.exists() and not args.regen:
            for r in load_jsonl(cache):
                level_ans[L][str(r.get("record_id"))] = r
            print("[B3] === level %s : reused cache (%d answers) ===" % (L, len(level_ans[L])))
            continue
        print("[B3] === level %s : running Q5 + Q6 ===" % L)
        if not run_stage("Q5_Gov_Context_Router.py", L):
            print("[WARN] Q5 failed at %s" % L); continue
        if not run_stage("Q6_Gov_Answer_Generation.py", L):
            print("[WARN] Q6 failed at %s" % L); continue
        answers = load_jsonl(OUT / "Q6_final_answers.jsonl")
        with open(cache, "w", encoding="utf-8") as f:
            for r in answers:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        for r in answers:
            level_ans[L][str(r.get("record_id"))] = r

    # 2) score every level, stratified by answerability
    per = {L: {"total": 0, "answered": 0, "adh_total": 0, "adh_match": 0, "faith": []} for L in ALL_LEVELS}
    detail = []
    print("[B3] scoring %d questions x %d levels with %s%s ..."
          % (len(serve), len(ALL_LEVELS), args.judge_model, " (no TRACe)" if args.no_trace else ""))
    for i, row in enumerate(serve):
        idx = str(row.get("idx")); rid = "delucionqa_q%05d" % int(idx)
        q = row.get("question", "")
        g = gold_map.get(ts.norm_q(q), {})
        gold = g.get("gold_response", row.get("gold", "")); answerable = g.get("answerable")
        naive = row.get("naive", {})
        rec = {"idx": idx, "question": q, "answerable": answerable, "levels": {}}
        for L in ALL_LEVELS:
            if L == "G0":
                ans = naive.get("answer", ""); mode = ""; ctx = naive.get("context", "")
            else:
                o = level_ans[L].get(rid, {})
                ans = o.get("generated_answer", ""); mode = o.get("mode", "")
                ctx = o.get("final_prompt", "") or ""
            refused = str(mode).startswith("BLOCKED") or ts.is_refusal(ans, mode)
            verdict = "SAFE_SILENCE" if refused else ts.correctness(gold, ans, mode, args.judge_model, client, types)
            trace = None if (refused or args.no_trace) else ts.judge_tuple(q, ctx, ans, args.judge_model, client, types)
            s = per[L]; s["total"] += 1
            if not refused:
                s["answered"] += 1
                if trace:
                    s["faith"].append(trace["adherence"])
            if answerable is True:
                s["adh_total"] += 1
                if verdict == "MATCH":
                    s["adh_match"] += 1
            rec["levels"][L] = {"refused": refused, "verdict": verdict,
                                "adherence": (trace["adherence"] if trace else None)}
        detail.append(rec)
        print("  [score] %d/%d" % (i + 1, len(serve)))

    RES.mkdir(exist_ok=True)
    with open(RES / "spectrum_real_scores.jsonl", "w", encoding="utf-8") as f:
        for r in detail:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 3) frontier
    print("\n" + "=" * 74)
    print("REAL GOVERNANCE SPECTRUM (through frozen pipeline)   N=%d" % len(serve))
    print("=" * 74)
    print("%-14s %10s %14s %14s" % ("level", "coverage", "accuracy(adh)", "faithfulness"))
    csv = [("level", "coverage", "accuracy_adherent", "faithfulness")]
    xs, ys, labs = [], [], []
    for L in ALL_LEVELS:
        s = per[L]
        cov = s["answered"] / s["total"] if s["total"] else 0.0
        acc = s["adh_match"] / s["adh_total"] if s["adh_total"] else 0.0
        faith = st.mean(s["faith"]) if s["faith"] else float("nan")
        print("%-14s %9.0f%% %13.0f%% %14.3f" % (NAMES[L], 100 * cov, 100 * acc, faith))
        csv.append((NAMES[L], "%.4f" % cov, "%.4f" % acc, "%.4f" % (faith if faith == faith else 0)))
        xs.append(cov); ys.append(acc); labs.append(L)
    with open(RES / "spectrum_real_frontier.csv", "w", encoding="utf-8") as f:
        for r in csv:
            f.write(",".join(map(str, r)) + "\n")
    print("-" * 74)
    print("[B3] scores -> results/spectrum_real_scores.jsonl ; frontier -> results/spectrum_real_frontier.csv")
    print("NOTE: output/Q5_*, Q6_* now reflect the LAST level (G4). Re-run B2 to restore a single-level state.")

    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 4.2)); plt.plot(xs, ys, "-o", color="#2E75B6")
        for L, x, y in zip(labs, xs, ys):
            plt.annotate(L, (x, y), textcoords="offset points", xytext=(6, 5))
        plt.xlabel("Coverage (answer rate)"); plt.ylabel("Accuracy on adherent stratum")
        plt.title("Real governance spectrum: risk-coverage frontier"); plt.grid(alpha=0.3); plt.tight_layout()
        plt.savefig(RES / "spectrum_real_frontier.png", dpi=150)
        print("[B3] plot -> results/spectrum_real_frontier.png")
    except Exception as e:
        print("[B3] plot skipped (%s)" % e)


if __name__ == "__main__":
    main()
