#!/usr/bin/env python3
"""
E3_Parallel_Evaluation.py -- parallel + checkpointed variant of E3_Unified_Evaluation.py.
Approved by Vivek 2026-07-10 (after run-1 E3 slowed to ~2 min/record under overnight API
throttling with no checkpoint). SAME metrics, SAME judge prompts/calls, SAME output schema.
E3_Unified_Evaluation.py is left untouched as the audit reference.

Adds (measurement-layer only; no frozen code touched):
  1. CONCURRENCY  -- ThreadPool over (record, config) scoring tasks (--workers, default 6).
  2. CHECKPOINT   -- every scored pair appended to results/<prefix>_checkpoint.jsonl;
                     rerunning the same command skips finished pairs (crash/interrupt safe).
  3. RETRY        -- judge errors (correctness 'ERROR:*' / trace None) retried with
                     exponential backoff instead of being silently recorded as failures.
  4. --out-prefix -- isolate replication runs (e.g. E3_run2) without clobbering run 1.

RUN from repo root:
  python E3_Parallel_Evaluation.py --judge-model gemini-3.1-pro-preview --workers 6
  python E3_Parallel_Evaluation.py ... --out-prefix E3_run2      # replication
  (interrupted? rerun the same command -- resumes from the checkpoint)
"""
import argparse, csv, json, os, random, re, threading, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import trace_scorer as ts

TAU = os.getenv("SWEEP_TAU", "0.35")
CONFIGS = [  # must stay in lockstep with B3_spectrum_axes.py / E3_Unified_Evaluation.py / B4
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


ROOT = find_root(Path.cwd()); RES = ROOT / "results"; RES.mkdir(exist_ok=True)


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name)


def token_f1(pred, gold):
    """SQuAD-style bag-of-tokens F1 (citation markers stripped). Identical to E3."""
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
    """Identical to E3."""
    if answerable is True:
        return "SUCCESS" if verdict == "MATCH" else "FAILURE_%s" % verdict
    if answerable is False:
        if verdict == "SAFE_SILENCE": return "SUCCESS_boundary"
        if verdict == "MATCH":        return "FAILURE_leakage"
        return "FAILURE_badoutput"
    return "NA"


# ---------- thread-local judge client + retrying wrappers ----------
_TL = threading.local()


def get_client():
    if not hasattr(_TL, "client"):
        from google import genai
        from google.genai import types as _t
        # 120s per-call ceiling (approved 2026-07-19): a hung judge socket becomes a
        # timeout error that feeds the retry/backoff instead of freezing a worker.
        _TL.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"),
                                  http_options=_t.HttpOptions(timeout=120_000))
    return _TL.client


def judged_correctness(gold, ans, mode, model, types, tries=5):
    """ts.correctness with exponential backoff on ERROR verdicts (throttling/5xx)."""
    for attempt in range(tries):
        v = ts.correctness(gold, ans, mode, model, get_client(), types)
        if not str(v).startswith("ERROR"):
            return v
        time.sleep(min(60, 2 ** attempt) + random.random())
    return "ERROR_FINAL"


def judged_trace(q, ctx, ans, model, types, tries=3):
    """ts.judge_tuple with retry; empty context is a legitimate None (no retry)."""
    if not ts.sentences(ctx):
        return None
    for attempt in range(tries):
        t = ts.judge_tuple(q, ctx, ans, model, get_client(), types)
        if t is not None:
            return t
        time.sleep(min(60, 2 ** attempt) + random.random())
    return None


def score_pair(task, args, types):
    """One (record, config) scoring unit. Returns the checkpoint record."""
    refused = task["refused"]
    verdict = "SAFE_SILENCE" if refused else judged_correctness(
        task["gold"], task["ans"], task["mode"], args.judge_model, types)
    trace = None if (refused or args.no_trace) else judged_trace(
        task["q"], task["ctx"], task["ans"], args.judge_model, types)
    f1 = token_f1(task["ans"], task["gold"]) if (not refused and task["answerable"] is True) else None
    return {"idx": task["idx"], "config": task["config"], "answerable": task["answerable"],
            "question": task["q"][:120], "gold": str(task["gold"])[:120], "answer": str(task["ans"])[:200],
            "refused": refused, "verdict": verdict,
            "grade": condition_grade(task["answerable"], verdict),
            "faith": (trace["adherence"] if trace else None),
            "f1": (round(f1, 4) if f1 is not None else None),
            "gov_ratio": task["gr"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="gemini-3.1-pro-preview")
    ap.add_argument("--serve", default=str(RES / "serve_results.jsonl"))
    ap.add_argument("--gold-map", default=str(RES / "gold_map.json"))
    ap.add_argument("--no-trace", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out-prefix", default="E3P",
                    help="output/checkpoint prefix (e.g. E3_run2). Default E3P so run-1's E3_* files are never clobbered.")
    args = ap.parse_args()

    from google.genai import types  # noqa: F401  (client is thread-local)

    serve = load_jsonl(args.serve)
    gold_map = json.load(open(args.gold_map, encoding="utf-8")) if os.path.exists(args.gold_map) else {}
    if not serve:
        raise SystemExit("[FATAL] no serve_results -- run B2/B4 first.")
    names = [c[0] for c in CONFIGS]

    # per-config caches written by B3/B4 (answers + evidence reduction)
    cfg_ans, cfg_red = {n: {} for n in names}, {n: [] for n in names}
    for name, envd in CONFIGS:
        if envd is None:
            continue
        for r in load_jsonl(RES / ("_spec_%s.jsonl" % slug(name))):
            # join by NUMERIC index parsed from the record_id tail ("<anything>_qNNNNN"):
            # prefix-agnostic (2026-07-19 fix -- B2 now stamps run-derived prefixes,
            # the old hardcoded "delucionqa_q%05d" reconstruction broke the join)
            rid_tail = str(r.get("record_id", "")).rsplit("_q", 1)[-1]
            key = str(int(rid_tail)) if rid_tail.isdigit() else str(r.get("record_id"))
            cfg_ans[name][key] = r
        cfg_red[name] = load_jsonl(RES / ("_spec_%s_red.jsonl" % slug(name)))

    # build all (record, config) tasks
    tasks = []
    for row in serve:
        idx = str(row.get("idx")); rid = str(int(idx))  # numeric join key, prefix-agnostic
        q = row.get("question", "")
        g = gold_map.get(ts.norm_q(q), {})
        gold = g.get("gold_response", row.get("gold", "")); answerable = g.get("answerable")
        naive = row.get("naive", {})
        for name, envd in CONFIGS:
            if envd is None:
                ans, mode, ctx, gr = naive.get("answer", ""), "", naive.get("context", ""), None
            else:
                o = cfg_ans[name].get(rid, {})
                ans, mode = o.get("generated_answer", ""), o.get("mode", "")
                ctx = o.get("final_prompt", "") or ""
                gr = o.get("gov_ratio", o.get("governance_ratio"))
            refused = str(mode).startswith("BLOCKED") or ts.is_refusal(ans, mode)
            tasks.append({"idx": idx, "config": name, "q": q, "gold": gold, "answerable": answerable,
                          "ans": ans, "mode": mode, "ctx": ctx, "gr": gr, "refused": refused})

    # checkpoint: skip finished pairs
    ckpt_path = RES / ("%s_checkpoint.jsonl" % args.out_prefix)
    done = {}
    for r in load_jsonl(ckpt_path):
        done[(str(r["idx"]), r["config"])] = r
    todo = [t for t in tasks if (t["idx"], t["config"]) not in done]
    print("[E3P] %d records x %d configs = %d pairs | done %d | scoring %d | judge=%s workers=%d"
          % (len(serve), len(names), len(tasks), len(done), len(todo), args.judge_model, args.workers))

    lock = threading.Lock()
    n_done = len(done); n_total = len(tasks); t0 = time.time()
    with open(ckpt_path, "a", encoding="utf-8") as ck:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(score_pair, t, args, types): t for t in todo}
            for fu in as_completed(futs):
                try:
                    rec = fu.result()
                except Exception as e:  # 2026-07-19: a single malformed judge response must
                    t = futs[fu]        # not kill 1,400 good pairs; record ERROR, rerun retries it
                    rec = {"idx": str(t["idx"]), "config": t["config"],
                           "answerable": str(t.get("answerable")), "question": t.get("q", ""),
                           "gold": t.get("gold", ""), "answer": t.get("ans", ""),
                           "refused": str(t.get("refused")), "verdict": "ERROR_WORKER",
                           "grade": "ERROR", "faith": None, "f1": None, "gov_ratio": None,
                           "error": str(e)[:200]}
                with lock:
                    ck.write(json.dumps(rec, ensure_ascii=False) + "\n"); ck.flush()
                    done[(str(rec["idx"]), rec["config"])] = rec
                    n_done += 1
                    if n_done % 25 == 0 or n_done == n_total:
                        rate = (n_done - len(futs) + len([1 for f in futs if f.done()])) or 1
                        el = time.time() - t0
                        print("  [score] %d/%d pairs  (%.1f min elapsed)" % (n_done, n_total, el / 60), flush=True)

    err = sum(1 for r in done.values() if str(r["verdict"]).startswith("ERROR"))
    if err:
        print("[E3P][WARN] %d pairs still ERROR after retries -- rerun the same command to retry ONLY those" % err)
        # drop them from the checkpoint so a rerun re-judges them
        keep = [r for r in done.values() if not str(r["verdict"]).startswith("ERROR")]
        with open(ckpt_path, "w", encoding="utf-8") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---------- master log + summary (identical schema to E3) ----------
    order = {n: i for i, n in enumerate(names)}
    recs = sorted(done.values(), key=lambda r: (int(r["idx"]), order.get(r["config"], 99)))
    master = [("record_idx", "config", "answerable", "question", "gold", "answer",
               "verdict", "condition_grade", "faithfulness", "token_f1", "gov_ratio")]
    for r in recs:
        master.append((r["idx"], r["config"], r["answerable"], r["question"], r["gold"], r["answer"],
                       r["verdict"], r["grade"], ("" if r["faith"] is None else r["faith"]),
                       ("" if r["f1"] is None else "%.3f" % r["f1"]),
                       ("" if r["gov_ratio"] is None else r["gov_ratio"])))
    with open(RES / ("%s_master_eval_log.csv" % args.out_prefix), "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(master)

    def mean(xs): return (sum(xs) / len(xs)) if xs else float("nan")
    print("\n" + "=" * 118)
    print("E3P UNIFIED EVALUATION   N=%d   judge=%s" % (len(serve), args.judge_model))
    print("=" * 118)
    hdr = ("config", "cov", "acc(adh)", "faith", "refuse", "corrRef", "falseRej", "tokF1", "GA", "C-F1")
    print("%-15s %5s %8s %6s %7s %8s %9s %6s %5s %6s" % hdr)
    summ = [("config", "coverage", "accuracy_adherent", "faithfulness", "refusal_rate",
             "correct_refusal_rate", "false_rejection_rate", "token_f1", "governance_accuracy",
             "constrained_f1") + tuple(RED_KEYS) + ("gov_ratio",)]
    for name in names:
        rs = [r for r in recs if r["config"] == name]
        t = len(rs)
        answered = [r for r in rs if not r["refused"]]
        adh = [r for r in rs if r["answerable"] is True]
        una = [r for r in rs if r["answerable"] is False]
        cov = len(answered) / t if t else 0
        acc = (sum(1 for r in adh if r["verdict"] == "MATCH") / len(adh)) if adh else 0
        faith = mean([r["faith"] for r in answered if r["faith"] is not None])
        refuse = 1 - cov
        corr_ref = (sum(1 for r in una if r["verdict"] == "SAFE_SILENCE") / len(una)) if una else float("nan")
        false_rej = (sum(1 for r in adh if r["refused"]) / len(adh)) if adh else 0
        f1 = mean([r["f1"] for r in rs if r["f1"] is not None])
        ga = sum(1 for r in rs if str(r["grade"]).startswith("SUCCESS")) / t if t else 0
        cf1 = 0.5 * (f1 if f1 == f1 else 0) + 0.5 * ga
        grs = [float(r["gov_ratio"]) for r in rs if r["gov_ratio"] not in (None, "")]
        reds = cfg_red.get(name, [])
        rmean = {k: mean([x.get(k, 0) for x in reds]) for k in RED_KEYS} if reds else {k: float("nan") for k in RED_KEYS}
        print("%-15s %4.0f%% %7.0f%% %6.2f %6.0f%% %7s %8.0f%% %6.2f %4.0f%% %6.3f"
              % (name, 100*cov, 100*acc, (faith if faith == faith else 0),
                 100*refuse, ("%.0f%%" % (100*corr_ref) if corr_ref == corr_ref else "  n/a"),
                 100*false_rej, (f1 if f1 == f1 else 0), 100*ga, cf1))
        summ.append((name, "%.4f"%cov, "%.4f"%acc, "%.4f"%(faith if faith==faith else 0),
                     "%.4f"%refuse, "%.4f"%(corr_ref if corr_ref==corr_ref else 0), "%.4f"%false_rej,
                     "%.4f"%(f1 if f1==f1 else 0), "%.4f"%ga, "%.4f"%cf1)
                    + tuple("%.4f"%rmean[k] for k in RED_KEYS)
                    + ("%.4f" % (mean(grs) if grs else 0),))
    with open(RES / ("%s_frontier_summary.csv" % args.out_prefix), "w", encoding="utf-8") as f:
        csv.writer(f).writerows(summ)
    print("-" * 118)
    print("[E3P] per-record -> results/%s_master_eval_log.csv ; summary -> results/%s_frontier_summary.csv"
          % (args.out_prefix, args.out_prefix))
    print("[E3P] checkpoint -> %s (delete it to force a full re-score)" % ckpt_path)


if __name__ == "__main__":
    main()
