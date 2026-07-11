#!/usr/bin/env python3
"""
preflight_check.py -- READ-ONLY pre-flight for the full batched run. Verifies gold-map join
coverage, answerability composition, uniqueness, and split composition over the FULL records
file, and prints the K-batch math. Changes nothing.
RUN from repo root:
  python preflight_check.py --records "<path to delucionqa_records.csv>" --k 25
  python preflight_check.py --records "<...>" --split test    # restrict counts to one split
"""
import argparse, csv, json, os, re, sys
from collections import Counter

def norm_q(q):  # must match trace_scorer.norm_q exactly
    return re.sub(r"\s+", " ", (q or "").strip().lower())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--gold-map", default=os.path.join("results", "gold_map.json"))
    ap.add_argument("--k", type=int, default=25)
    ap.add_argument("--split", default=None, help="if set, restrict counts to this split (e.g. test)")
    args = ap.parse_args()

    if not os.path.exists(args.records):
        sys.exit("[FATAL] records not found: %s" % args.records)
    if not os.path.exists(args.gold_map):
        sys.exit("[FATAL] gold_map not found: %s (run build_gold_map.py first)" % args.gold_map)

    gold = json.load(open(args.gold_map, encoding="utf-8"))
    csv.field_size_limit(10_000_000)
    rows = list(csv.DictReader(open(args.records, encoding="utf-8")))
    qcol = "question" if rows and "question" in rows[0] else next((c for c in (rows[0].keys() if rows else []) if "quest" in c.lower()), None)
    if not qcol:
        sys.exit("[FATAL] no question column found in records. Columns: %s" % (list(rows[0].keys()) if rows else []))

    if args.split:
        rows = [r for r in rows if str((gold.get(norm_q(r.get(qcol, ""))) or {}).get("split", "")) == args.split]

    total = len(rows)
    matched = unmatched = empty_gold = 0
    ans_true = ans_false = ans_none = 0
    misses = []
    splits = Counter()
    for r in rows:
        k = norm_q(r.get(qcol, ""))
        g = gold.get(k)
        if g is None:
            unmatched += 1
            if len(misses) < 5: misses.append(r.get(qcol, "")[:80])
            continue
        matched += 1
        splits[str(g.get("split", "?"))] += 1
        if not str(g.get("gold_response", "")).strip():
            empty_gold += 1
        a = g.get("answerable")
        if a is True: ans_true += 1
        elif a is False: ans_false += 1
        else: ans_none += 1

    idxs = [r.get("idx") for r in rows if r.get("idx") is not None]
    uniq_idx = len(set(idxs)); uniq_q = len(set(norm_q(r.get(qcol, "")) for r in rows))

    print("=" * 64)
    print("PRE-FLIGHT  records=%s%s" % (os.path.basename(args.records), (" split=%s" % args.split) if args.split else ""))
    print("=" * 64)
    print("  total rows ............... %d" % total)
    print("  gold-map JOIN matched .... %d (%.1f%%)" % (matched, 100*matched/total if total else 0))
    print("  gold-map UNMATCHED ....... %d   <- must be ~0" % unmatched)
    print("  matched but EMPTY gold ... %d   <- must be 0" % empty_gold)
    if misses:
        print("  sample unmatched questions:")
        for m in misses: print("     - %s" % m)
    print("-" * 64)
    print("UNIQUENESS / SPLITS:")
    print("  unique record idx ........ %d (of %d rows)" % (uniq_idx, total))
    print("  unique questions ......... %d   <- if << rows, questions are duplicated" % uniq_q)
    print("  split composition ........ %s" % dict(splits))
    print("     -> for the benchmark, evaluate ONE split (usually test), not all combined")
    print("-" * 64)
    print("ANSWERABILITY (of matched):")
    print("  answerable (P) ........... %d (%.1f%%)" % (ans_true, 100*ans_true/matched if matched else 0))
    print("  UNanswerable (N) ......... %d (%.1f%%)   <- corrRef / falseRej denominator" % (ans_false, 100*ans_false/matched if matched else 0))
    print("  answerability UNKNOWN .... %d   <- should be 0" % ans_none)
    print("-" * 64)
    k = args.k
    nb = (total + k - 1) // k
    print("BATCH MATH  K=%d -> %d batches; offsets: 0,%d,...,%d; last batch = %d rows"
          % (k, nb, k, (nb-1)*k, total - (nb-1)*k))
    verdict = "READY" if (unmatched == 0 and empty_gold == 0 and ans_none == 0 and ans_false > 0) else "NOT READY -- see flags above"
    print("VERDICT:", verdict)

if __name__ == "__main__":
    main()
