#!/usr/bin/env python3
"""
dedup_records.py -- DelucionQA records are duplicated (1826 = 913 x 2). This ANALYZES the
duplication and, with --write, produces a deduplicated benchmark CSV of unique records.

SAFETY FIRST: before collapsing, it verifies each duplicate group is truly redundant (same
context + same gold). If copies DIFFER, it STOPS -- they may be distinct retrieval instances or
positive/negative variants, and must not be blindly deduped by question.

RUN from repo root:
  python dedup_records.py --records "<...delucionqa_records.csv>"                    # analyze (dry-run)
  python dedup_records.py --records "<...>" --key fullrow                            # analyze exact-row dups
  python dedup_records.py --records "<...>" --key fullrow --write delucionqa_records_913.csv
"""
import argparse, csv, hashlib, re, sys
from collections import defaultdict, Counter

def norm_q(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--write", default=None, help="output path for the deduped CSV")
    ap.add_argument("--key", default="question", choices=["question", "idx", "fullrow"],
                    help="dedup key: question (default), idx, or fullrow (exact-identical rows only)")
    ap.add_argument("--allow-divergent", action="store_true",
                    help="proceed despite divergent groups; keep FIRST occurrence per key")
    args = ap.parse_args()

    csv.field_size_limit(10_000_000)
    with open(args.records, encoding="utf-8") as f:
        rd = csv.DictReader(f); cols = rd.fieldnames; rows = list(rd)
    total = len(rows)

    def col(*cands):
        for c in cands:
            if c in (cols or []): return c
        return None
    qcol = col("question") or next((c for c in cols if "quest" in c.lower()), None)
    ctxcol = col("documents_joined", "documents", "context", "positive", "negative")
    goldcol = col("gold", "response", "answer")
    print("columns:", cols)
    print("using  question=%s  context=%s  gold=%s" % (qcol, ctxcol, goldcol))

    def keyfor(r):
        if args.key == "idx":
            return str(r.get("idx"))
        if args.key == "fullrow":
            return hashlib.md5("|".join(str(r.get(c, "")) for c in cols).encode("utf-8")).hexdigest()
        return norm_q(r.get(qcol, ""))

    groups = defaultdict(list)
    for r in rows:
        groups[keyfor(r)].append(r)
    sizes = Counter(len(v) for v in groups.values())
    print("-" * 60)
    print("total rows=%d  unique(%s)=%d  group-size dist=%s" % (total, args.key, len(groups), dict(sizes)))

    # divergence check within multi-row groups
    divergent = []
    multi = 0
    for k, v in groups.items():
        if len(v) < 2: continue
        multi += 1
        sig = set((str(r.get(ctxcol, "")), str(r.get(goldcol, ""))) for r in v)
        if len(sig) > 1:
            divergent.append((k, v))
    print("groups with >1 row: %d ; of which DIVERGENT (context/gold differ): %d" % (multi, len(divergent)))
    for k, v in divergent[:3]:
        print("  DIVERGENT key=%s" % str(k)[:50])
        for r in v[:2]:
            print("     ctx=%-50s | gold=%s" % (str(r.get(ctxcol, ""))[:50], str(r.get(goldcol, ""))[:50]))

    if divergent and not args.allow_divergent:
        print("\n[STOP] %d group(s) differ on context/gold -- likely distinct retrieval instances, not copies." % len(divergent))
        print("       Dedup by '%s' would keep the FIRST occurrence per key and drop the variants." % args.key)
        print("       If one representative context per question is intended, re-run adding --allow-divergent.")
        return

    if args.write:
        seen = set(); out = []
        for r in rows:
            k = keyfor(r)
            if k in seen: continue
            seen.add(k); out.append(r)
        with open(args.write, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
        print("\n[OK] wrote %d unique rows -> %s" % (len(out), args.write))
        print("     -> re-run preflight_check.py on this file to confirm before the run.")
    else:
        print("\n(dry-run) re-run with --write <path> to produce the deduped CSV.")

if __name__ == "__main__":
    main()
