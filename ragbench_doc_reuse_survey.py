#!/usr/bin/env python3
"""
ragbench_doc_reuse_survey.py -- download every RAGBench subset and rank them by DOCUMENT
REUSE (questions per document), to pick the Run-2/Run-3 corpora (advisor guidance
2026-07-11: choose records that reuse documents, so a small build serves many questions).

For each subset this reports:
  rows, unique questions, distinct documents, answerability mix (adherence_score),
  max questions touching one document, and GREEDY COVER: how many questions are FULLY
  answerable from only the top 5/10/20/30 documents (a question counts only when ALL
  of its documents are selected -- that is what bounds the build corpus).

READ-ONLY apart from: downloading missing parquets to --parquet-dir and writing the
summary CSV. Existing parquets (delucionqa, emanual) are reused, never re-downloaded.

RUN from repo root (venv active; needs: pandas, pyarrow, datasets):
  python ragbench_doc_reuse_survey.py
  python ragbench_doc_reuse_survey.py --only techqa cuad finqa      # subset of subsets
  python ragbench_doc_reuse_survey.py --no-download                 # local parquets only
"""
import argparse, hashlib, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

SUBSETS = ["covidqa", "cuad", "delucionqa", "emanual", "expertqa", "finqa",
           "hagrid", "hotpotqa", "msmarco", "pubmedqa", "tatqa", "techqa"]
SPLITS = ["train", "validation", "test"]
ALREADY_USED = {"delucionqa", "emanual"}
GREEDY_KS = (5, 10, 20, 30)


def norm_q(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def download_missing(subsets, pdir, skip_download):
    have, missing = [], []
    for name in subsets:
        files = [pdir / ("%s-%s.parquet" % (name, s)) for s in SPLITS]
        if any(f.exists() for f in files):
            have.append(name); continue
        missing.append(name)
    if not missing:
        return have
    if skip_download:
        print("[survey] --no-download set; skipping missing subsets: %s" % missing)
        return have
    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("[FATAL] `datasets` not installed. Run: pip install datasets")
    for name in missing:
        got = False
        for s in SPLITS:
            try:
                ds = load_dataset("rungalileo/ragbench", name, split=s)
                ds.to_parquet(str(pdir / ("%s-%s.parquet" % (name, s))))
                print("[dl] %s-%s: %d rows" % (name, s, len(ds)))
                got = True
            except Exception as e:
                print("[dl] %s-%s: skipped (%s)" % (name, s, str(e)[:80]))
        if got:
            have.append(name)
    return have


def load_subset(name, pdir):
    import pandas as pd
    frames = []
    for s in SPLITS:
        f = pdir / ("%s-%s.parquet" % (name, s))
        if f.exists():
            df = pd.read_parquet(f, columns=None)
            df["__split"] = s
            frames.append(df)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def analyze(name, df):
    rows = len(df)
    qcol = "question" if "question" in df.columns else None
    dcol = "documents" if "documents" in df.columns else None
    if not qcol or not dcol:
        return {"subset": name, "rows": rows, "error": "missing question/documents column"}

    # unique questions (first occurrence), like the delucionqa dedup decision
    seen, qdocs, ans_t, ans_f, ans_u = set(), {}, 0, 0, 0
    for _, r in df.iterrows():
        k = norm_q(str(r[qcol]))
        if k in seen:
            continue
        seen.add(k)
        docs = r[dcol]
        if hasattr(docs, "tolist"):
            docs = docs.tolist()
        if isinstance(docs, str):
            docs = [docs]
        qdocs[k] = frozenset(hashlib.md5(str(d).strip().encode("utf-8")).hexdigest() for d in docs)
        a = r.get("adherence_score")
        if a is True or str(a) == "True": ans_t += 1
        elif a is False or str(a) == "False": ans_f += 1
        else: ans_u += 1

    doc_q = defaultdict(set)
    for q, ds in qdocs.items():
        for d in ds:
            doc_q[d].add(q)
    n_docs = len(doc_q)
    touch = sorted((len(v) for v in doc_q.values()), reverse=True)

    # greedy full-cover (lazy-exact): pending[q] = #unchosen docs of q
    pending = {q: len(ds) for q, ds in qdocs.items()}
    chosen, covered, curve = set(), set(), {}
    cand = sorted(doc_q, key=lambda d: len(doc_q[d]), reverse=True)[:2000]
    for k in range(1, max(GREEDY_KS) + 1):
        best, gain = None, -1
        for d in cand:
            if d in chosen:
                continue
            g = sum(1 for q in doc_q[d] if q not in covered and pending[q] == 1)
            if g > gain:
                best, gain = d, g
        if best is None:                       # subset has fewer docs than max K
            for kk in GREEDY_KS:
                curve.setdefault(kk, len(covered))
            break
        chosen.add(best)
        for q in doc_q[best]:
            pending[q] -= 1
            if pending[q] == 0:
                covered.add(q)
        if k in GREEDY_KS:
            curve[k] = len(covered)
    return {"subset": name, "rows": rows, "unique_q": len(qdocs), "docs": n_docs,
            "q_per_doc": round(len(qdocs) / n_docs, 2) if n_docs else 0,
            "max_touch": touch[0] if touch else 0,
            "answerable": ans_t, "unanswerable": ans_f, "ans_unknown": ans_u,
            **{("cover_top%d" % k): curve.get(k, "") for k in GREEDY_KS}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet-dir", default=os.path.join("data", "parquet"))
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--out", default=os.path.join("data", "ragbench_doc_reuse_survey.csv"))
    args = ap.parse_args()

    pdir = Path(args.parquet_dir); pdir.mkdir(parents=True, exist_ok=True)
    subsets = args.only if args.only else SUBSETS
    have = download_missing(subsets, pdir, args.no_download)

    results = []
    for name in have:
        df = load_subset(name, pdir)
        if df is None:
            continue
        print("[survey] analyzing %s (%d rows) ..." % (name, len(df)))
        results.append(analyze(name, df))

    import csv as _csv
    cols = ["subset", "rows", "unique_q", "docs", "q_per_doc", "max_touch",
            "answerable", "unanswerable", "ans_unknown"] + ["cover_top%d" % k for k in GREEDY_KS]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)

    print("\n%-11s %6s %7s %6s %7s %6s %6s %6s | %s" %
          ("subset", "rows", "uniqQ", "docs", "Q/doc", "ansP", "ansN", "maxTch",
           "  ".join("top%d" % k for k in GREEDY_KS)))
    for r in sorted(results, key=lambda x: -(x.get("cover_top20") or 0)):
        flag = " *used*" if r["subset"] in ALREADY_USED else ""
        if "error" in r:
            print("%-11s %6d  ERROR: %s" % (r["subset"], r["rows"], r["error"])); continue
        print("%-11s %6d %7d %6d %7.2f %6d %6d %6d | %s%s" %
              (r["subset"], r["rows"], r["unique_q"], r["docs"], r["q_per_doc"],
               r["answerable"], r["unanswerable"], r["max_touch"],
               "  ".join("%4s" % r["cover_top%d" % k] for k in GREEDY_KS), flag))
    print("\n[survey] CSV -> %s" % args.out)
    print("[survey] pick by: high cover_top20/30 (small build, many questions) AND non-zero")
    print("         unanswerable count (needed for the corrRef/abstention metrics).")


if __name__ == "__main__":
    main()
