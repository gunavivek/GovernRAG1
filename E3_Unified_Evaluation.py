#!/usr/bin/env python3
"""
E3_Unified_Evaluation.py -- unified DelucionQA evaluator. Retains E2's per-record verdict trace
and P/N grading, and ADDS every evaluation dimension developed in the Q-pipeline work:
governance spectrum (G0-G4) + two ontology axes, answerability stratification, risk-coverage
frontier, the governance metric triad, evidence-set reduction, governance ratio, and Constrained-F1.

Pure SCORER + REPORTER: reuses the per-config answer/evidence caches that B3_spectrum_axes.py
writes (results/_spec_*.jsonl, _spec_*_red.jsonl). No generation, no pipeline re-run.
PRE-REQ: run B3_spectrum_axes.py once (produces the caches). Models: judge = stable independent
(gemini-2.5-pro default); G0 naive baseline is the parity model already in serve_results.jsonl.

E2 mapping: P (positive/answerable) -> MATCH is SUCCESS; N (negative/unanswerable) -> SAFE_SILENCE
is SUCCESS (boundary maintained), MATCH is FAILURE (parametric leakage).

RUN from repo root:
  python E3_Unified_Evaluation.py --judge-model gemini-2.5-pro
  python E3_Unified_Evaluation.py --no-trace --judge-model gemini-2.5-flash   # fast
  python E3_Unified_Evaluation.py --record 3                                   # E2-style single-record trace
"""
import argparse, csv, json, os, re, statistics as st
from collections import Counter
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

ROOT = find_root(Path.cwd()); OUT = ROOT / "output"; RES = ROOT / "results"; RES.mkdir(exist_ok=True)

def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []

def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name)

def token_f1(pred, gold):
    """SQuAD-style bag-of-tokens F1 (citation markers stripped)."""
    def toks(s):
        return re.findall(r"[a-z0-9]+", ts.strip_markers(str(s)).lower())
    p, g = toks(pred), toks(gold)
    if not p or not g:
        return 0.0
    cp, cg = Counter(p), Counter(g)
    common = sum((cp & cg).values())
    if common == 0:
        return 0.0
    prec, rec = common / len(p), common / len(g)
    return 2 * prec * rec / (prec + rec)

def condition_grade(answerable, verdict):
    """E2 P/N semantics generalized to DelucionQA answerability."""
    if answerable is True:                       # P: expect MATCH
        return "SUCCESS" if verdict == "MATCH" else "FAILURE_%s" % verdict
    if answerable is False:                      # N: expect SAFE_SILENCE
        if verdict == "SAFE_SILENCE": return "SUCCESS_boundary"
        if verdict == "MATCH":        return "FAILURE_leakage"
        return "FAILURE_badoutput"
    return "NA"                                   # answerability unknown

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="gemini-2.5-pro")
    ap.add_argument("--serve", default=str(RES / "serve_results.jsonl"))
    ap.add_argument("--gold-map", default=str(RES / "gold_map.json"))
    ap.add_argument("--no-trace", action="store_true", help="skip TRACe faithfulness judging")
    ap.add_argument("--record", type=int, default=None, help="print an E2-style verdict trace for one record index")
    args = ap.parse_args()

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    serve = load_jsonl(args.serve)
    gold_map = json.load(open(args.gold_map, encoding="utf-8")) if os.path.exists(args.gold_map) else {}
    if not serve:
        raise SystemExit("[FATAL] no serve_results.jsonl -- run B2 first.")
    names = [c[0] for c in CONFIGS]

    # load per-config caches (answers + evidence reduction) written by B3_spectrum_axes.py
    cfg_ans, cfg_red = {n: {} for n, _ in CONFIGS}, {n: [] for n, _ in CONFIGS}
    missing = []
    for name, envd in CONFIGS:
        if envd is None:
            continue
        cache = RES / ("_spec_%s.jsonl" % slug(name)); red = RES / ("_spec_%s_red.jsonl" % slug(name))
        if not cache.exists():
            missing.append(name); continue
        for r in load_jsonl(cache):
            cfg_ans[name][str(r.get("record_id"))] = r
        cfg_red[name] = load_jsonl(red)
    if missing:
        print("[WARN] missing caches for %s -- run B3_spectrum_axes.py first." % missing)
    print("[E3] %d records | judge=%s | configs=%s" % (len(serve), args.judge_model, names))

    # per (record, config) scoring
    per = {n: {"total": 0, "answered": 0, "adh_total": 0, "adh_match": 0, "faith": [], "f1": [],
               "ans_total": 0, "unans_total": 0, "false_reject": 0, "correct_refuse": 0,
               "refused": 0, "ga_ok": 0, "gr": []} for n in names}
    master_rows = [("record_idx", "config", "answerable", "question", "gold",
                    "answer", "verdict", "condition_grade", "faithfulness", "token_f1", "gov_ratio")]
    for i, row in enumerate(serve):
        idx = str(row.get("idx")); rid = "delucionqa_q%05d" % int(idx)
        q = row.get("question", "")
        g = gold_map.get(ts.norm_q(q), {})
        gold = g.get("gold_response", row.get("gold", "")); answerable = g.get("answerable")
        naive = row.get("naive", {})
        for name, envd in CONFIGS:
            if envd is None:
                ans = naive.get("answer", ""); mode = ""; ctx = naive.get("context", ""); gr = None
            else:
                o = cfg_ans[name].get(rid, {})
                ans = o.get("generated_answer", ""); mode = o.get("mode", "")
                ctx = o.get("final_prompt", "") or ""
                gr = o.get("gov_ratio", o.get("governance_ratio"))
            refused = str(mode).startswith("BLOCKED") or ts.is_refusal(ans, mode)
            verdict = "SAFE_SILENCE" if refused else ts.correctness(gold, ans, mode, args.judge_model, client, types)
            trace = None if (refused or args.no_trace) else ts.judge_tuple(q, ctx, ans, args.judge_model, client, types)
            grade = condition_grade(answerable, verdict)
            f1 = token_f1(ans, gold) if (not refused and answerable is True) else None

            s = per[name]; s["total"] += 1
            if not refused:
                s["answered"] += 1
                if trace: s["faith"].append(trace["adherence"])
            else:
                s["refused"] += 1
            if gr is not None:
                try: s["gr"].append(float(gr))
                except (TypeError, ValueError): pass
            if answerable is True:
                s["ans_total"] += 1; s["adh_total"] += 1
                if verdict == "MATCH": s["adh_match"] += 1
                if refused: s["false_reject"] += 1
                if f1 is not None: s["f1"].append(f1)
            elif answerable is False:
                s["unans_total"] += 1
                if verdict == "SAFE_SILENCE": s["correct_refuse"] += 1
            if grade.startswith("SUCCESS"): s["ga_ok"] += 1
            master_rows.append((idx, name, answerable, q[:120], str(gold)[:120], str(ans)[:200],
                                verdict, grade, (trace["adherence"] if trace else ""),
                                ("%.3f" % f1 if f1 is not None else ""), (gr if gr is not None else "")))

        print("  [score] %d/%d" % (i + 1, len(serve)))

    # master per-(record,config) log (E2-style, extended)
    with open(RES / "E3_master_eval_log.csv", "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(master_rows)

    # per-config summary: frontier + triad + Constrained-F1 + evidence reduction
    def mean(xs): return (sum(xs) / len(xs)) if xs else float("nan")
    print("\n" + "=" * 118)
    print("E3 UNIFIED EVALUATION (DelucionQA)   N=%d   judge=%s" % (len(serve), args.judge_model))
    print("=" * 118)
    hdr = ("config", "cov", "acc(adh)", "faith", "refuse", "corrRef", "falseRej", "tokF1", "GA", "C-F1")
    print("%-15s %5s %8s %6s %7s %8s %9s %6s %5s %6s" % hdr)
    summ = [("config", "coverage", "accuracy_adherent", "faithfulness", "refusal_rate",
             "correct_refusal_rate", "false_rejection_rate", "token_f1", "governance_accuracy",
             "constrained_f1") + tuple(RED_KEYS) + ("gov_ratio",)]
    for name in names:
        s = per[name]; t = s["total"]
        cov = s["answered"] / t if t else 0
        acc = s["adh_match"] / s["adh_total"] if s["adh_total"] else 0
        faith = mean(s["faith"])
        refuse = s["refused"] / t if t else 0
        corr_ref = s["correct_refuse"] / s["unans_total"] if s["unans_total"] else float("nan")
        false_rej = s["false_reject"] / s["ans_total"] if s["ans_total"] else 0
        f1 = mean(s["f1"]); ga = s["ga_ok"] / t if t else 0
        cf1 = 0.5 * (f1 if f1 == f1 else 0) + 0.5 * ga
        reds = cfg_red.get(name, [])
        rmean = {k: mean([r.get(k, 0) for r in reds]) for k in RED_KEYS} if reds else {k: float("nan") for k in RED_KEYS}
        gr = mean(s["gr"])
        print("%-15s %4.0f%% %7.0f%% %6.2f %6.0f%% %7s %8.0f%% %6.2f %4.0f%% %6.3f"
              % (name, 100*cov, 100*acc, faith,
                 100*refuse, ("%.0f%%" % (100*corr_ref) if corr_ref == corr_ref else "  n/a"),
                 100*false_rej, (f1 if f1 == f1 else 0), 100*ga, cf1))
        summ.append((name, "%.4f"%cov, "%.4f"%acc, "%.4f"%(faith if faith==faith else 0),
                     "%.4f"%refuse, "%.4f"%(corr_ref if corr_ref==corr_ref else 0), "%.4f"%false_rej,
                     "%.4f"%(f1 if f1==f1 else 0), "%.4f"%ga, "%.4f"%cf1)
                    + tuple("%.4f"%rmean[k] for k in RED_KEYS) + ("%.4f"%(gr if gr==gr else 0),))
    with open(RES / "E3_frontier_summary.csv", "w", encoding="utf-8") as f:
        csv.writer(f).writerows(summ)
    print("-" * 118)
    print("cov=coverage acc(adh)=accuracy on answerable stratum  faith=TRACe adherence")
    print("refuse=refusal rate  corrRef=correct-refusal (of unanswerable)  falseRej=false-rejection (of answerable)")
    print("tokF1=mean token-F1 (answerable answered)  GA=governance accuracy (correct-per-condition)  C-F1=Constrained-F1=0.5*tokF1+0.5*GA")
    print("[E3] per-record -> results/E3_master_eval_log.csv ; summary -> results/E3_frontier_summary.csv")

    # optional E2-style single-record verdict trace
    if args.record is not None and 0 <= args.record < len(serve):
        row = serve[args.record]; idx = str(row.get("idx")); rid = "delucionqa_q%05d" % int(idx)
        q = row.get("question", ""); g = gold_map.get(ts.norm_q(q), {})
        gold = g.get("gold_response", ""); answerable = g.get("answerable")
        print("\n" + "=" * 70)
        print(" E3 VERDICT TRACE  record idx=%s  (%s)" % (idx, "answerable" if answerable else "UNanswerable"))
        print("=" * 70)
        print(" [Q] %s" % q)
        print(" [A] GROUND TRUTH: %s" % gold)
        for name, envd in CONFIGS:
            if envd is None:
                ans = row.get("naive", {}).get("answer", ""); mode = ""
            else:
                o = cfg_ans[name].get(rid, {}); ans = o.get("generated_answer", ""); mode = o.get("mode", "")
            refused = str(mode).startswith("BLOCKED") or ts.is_refusal(ans, mode)
            verdict = "SAFE_SILENCE" if refused else ts.correctness(gold, ans, mode, args.judge_model, client, types)
            print(" ---- %-14s verdict=%-12s grade=%s" % (name, verdict, condition_grade(answerable, verdict)))
            print("      %s" % (str(ans)[:240]))

if __name__ == "__main__":
    main()
