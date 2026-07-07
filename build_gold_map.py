#!/usr/bin/env python3
"""
build_gold_map.py -- build the RAGBench gold + answerability map for scoring (task #34).

The pipeline's records CSV has NO gold answer and NO answerability field. The real
RAGBench DelucionQA gold lives in delucionqa_questions.jsonl. This joins by QUESTION
(100% coverage on the 913 unique DelucionQA questions) and emits a compact map that
trace_scorer consumes.

OUTPUT  results/gold_map.json  =  { norm_question : {
    "question", "gold_response",           # gold answer (fixes the empty-gold bug)
    "adherence", "answerable",             # answerability label (gold adherence)
    "relevance", "utilization", "completeness",  # RAGBench GOLD TRACe (reference)
    "split" } }

ANSWERABILITY (provisional; confirm w/ Dr. Xu, task #39):
  answerable = gold adherence_score is True  (the reference answer IS supported by the
  provided context). adherence False -> unsupported/unanswerable-from-context.

RUN from repo root (point --source at your delucionqa_questions.jsonl):
  python build_gold_map.py --source data/delucionqa_questions.jsonl
"""
import argparse, json, os, re, sys


def norm_q(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def as_bool(v):
    return str(v).strip().lower() in ("true", "1", "yes")


def as_float(v):
    try:
        return float(v)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="path to delucionqa_questions.jsonl (RAGBench gold)")
    ap.add_argument("--out", default=os.path.join("results", "gold_map.json"))
    args = ap.parse_args()

    if not os.path.exists(args.source):
        sys.exit("[FATAL] source not found: %s" % args.source)

    gm, n, dup = {}, 0, 0
    ans = {"answerable": 0, "unanswerable": 0}
    splits = {}
    for line in open(args.source, encoding="utf-8"):
        if not line.strip():
            continue
        d = json.loads(line)
        q = d.get("question", "")
        k = norm_q(q)
        if not k:
            continue
        if k in gm:
            dup += 1
        adh = as_bool(d.get("adherence_score"))
        answerable = adh  # provisional label
        gm[k] = {
            "question": q,
            "gold_response": d.get("response", ""),
            "adherence": adh,
            "answerable": answerable,
            "relevance": as_float(d.get("relevance_score")),
            "utilization": as_float(d.get("utilization_score")),
            "completeness": as_float(d.get("completeness_score")),
            "split": d.get("split"),
        }
        n += 1
        ans["answerable" if answerable else "unanswerable"] += 1
        s = d.get("split"); splits[s] = splits.get(s, 0) + 1

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(gm, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    print("[OK] gold map -> %s" % args.out)
    print("     records read      : %d (%d duplicate-question keys collapsed)" % (n, dup))
    print("     unique questions  : %d" % len(gm))
    print("     answerability      : answerable=%d  unanswerable=%d" % (ans["answerable"], ans["unanswerable"]))
    print("     splits             : %s" % splits)
    with_gold = sum(1 for v in gm.values() if str(v["gold_response"]).strip())
    print("     have gold_response : %d / %d" % (with_gold, len(gm)))


if __name__ == "__main__":
    main()
