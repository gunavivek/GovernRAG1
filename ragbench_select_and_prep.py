#!/usr/bin/env python3
"""
ragbench_select_and_prep.py -- Run-2/3 corpus construction (approved by Vivek 2026-07-12).
Implements the advisor-directed document-reuse selection: choose the top-K most-reused
documents of a RAGBench subset (greedy full-cover), keep every question FULLY answerable
from those documents, and emit the same D-pipeline/B-harness inputs DelucionQA had:

  data/<subset>_<label>_corpus.jsonl     one record, unique chunks of the K docs (feeds A1/D0/M0 build)
  data/<subset>_<label>_questions.jsonl  D02-format rows for the selected questions (feeds build_gold_map)
  data/<subset>_<label>_records.csv      idx,question,n_docs,documents_joined (' ||| ') (feeds serve map/B2/B4)
  data/<subset>_<label>_selection.json   provenance: config, doc hashes, question ids, P/N mix

Deterministic: greedy ties broken by document hash; question order = first occurrence in
the fixed train/validation/test concatenation. Read-only w.r.t. everything else.

RUN from repo root:
  python ragbench_select_and_prep.py --subset expertqa --label run2 --top-docs 60
  python ragbench_select_and_prep.py --subset hagrid   --label run3 --top-docs 60
"""
import argparse, csv, hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path

SPLITS = ["train", "validation", "test"]
QUESTION_COLS = [  # identical to D02_RAGBench_Parquet_Loader.QUESTION_COLS
    "id", "split", "question", "response",
    "adherence_score", "relevance_score", "utilization_score", "completeness_score",
    "supporting_sentence_keys", "unsupported_response_sentence_keys",
    "all_relevant_sentence_keys", "all_utilized_sentence_keys",
    "documents_sentences", "response_sentences",
]


def norm_q(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def to_native(v):
    return v.tolist() if hasattr(v, "tolist") else v


def dhash(doc):
    return hashlib.md5(str(doc).strip().encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", required=True)
    ap.add_argument("--label", required=True, help="run label, e.g. run2")
    ap.add_argument("--top-docs", type=int, default=60)
    ap.add_argument("--parquet-dir", default=str(Path("data") / "parquet"))
    ap.add_argument("--out-dir", default="data")
    args = ap.parse_args()

    import pandas as pd
    pdir, odir = Path(args.parquet_dir), Path(args.out_dir)
    frames = []
    for s in SPLITS:
        f = pdir / ("%s-%s.parquet" % (args.subset, s))
        if f.exists():
            df = pd.read_parquet(f); df["split"] = s; frames.append(df)
    if not frames:
        sys.exit("[FATAL] no parquet files for subset '%s' in %s (run ragbench_doc_reuse_survey.py first)"
                 % (args.subset, pdir))
    df = pd.concat(frames, ignore_index=True)
    print("[prep] %s: %d rows across %d split files" % (args.subset, len(df), len(frames)))

    # unique questions, first occurrence (same rule as the delucionqa benchmark dedup)
    rows, seen = [], set()
    for _, r in df.iterrows():
        k = norm_q(str(r.get("question", "")))
        if not k or k in seen:
            continue
        seen.add(k)
        docs = r["documents"]
        if hasattr(docs, "tolist"):
            docs = docs.tolist()
        if isinstance(docs, str):
            docs = [docs]
        docs = [str(d) for d in docs if str(d).strip()]
        if not docs:
            continue
        rows.append((k, r, docs, frozenset(dhash(d) for d in docs)))
    print("[prep] unique questions: %d" % len(rows))

    # greedy full-cover selection of top-K documents (deterministic tie-break by hash)
    doc_q = defaultdict(set); doc_text = {}
    for i, (_, _, docs, hs) in enumerate(rows):
        for d in docs:
            h = dhash(d); doc_q[h].add(i); doc_text[h] = d
    pending = {i: len(hs) for i, (_, _, _, hs) in enumerate(rows)}
    chosen, covered = [], set()
    cand = sorted(doc_q, key=lambda h: (-len(doc_q[h]), h))[:4000]
    for _ in range(min(args.top_docs, len(doc_q))):
        best, gain = None, -1
        for h in cand:
            if h in chosen:
                continue
            g = sum(1 for i in doc_q[h] if i not in covered and pending[i] == 1)
            if g > gain or (g == gain and best is not None and h < best):
                best, gain = h, g
        chosen.append(best)
        for i in doc_q[best]:
            pending[i] -= 1
            if pending[i] == 0:
                covered.add(i)
    sel = sorted(covered)
    print("[prep] selected %d documents -> %d fully covered questions" % (len(chosen), len(sel)))

    # answerability mix of the selection
    def as_bool(v):
        return str(v).strip().lower() in ("true", "1", "yes")
    n_p = sum(1 for i in sel if as_bool(rows[i][1].get("adherence_score")))
    n_n = len(sel) - n_p
    print("[prep] selection answerability: %d answerable / %d unanswerable" % (n_p, n_n))
    if n_n == 0:
        print("[prep][WARN] selection has ZERO unanswerable questions -- corrRef metric will be undefined!")

    base = "%s_%s" % (args.subset, args.label)
    odir.mkdir(parents=True, exist_ok=True)

    # 1) corpus jsonl (D02 format): unique chunks of the CHOSEN documents only
    corpus_docs = [doc_text[h] for h in chosen]
    with (odir / ("%s_corpus.jsonl" % base)).open("w", encoding="utf-8") as f:
        f.write(json.dumps({"id": "%s_CORPUS" % args.subset.upper(),
                            "question": "CORPUS_INIT",
                            "documents": corpus_docs}, ensure_ascii=False) + "\n")

    # 2) questions jsonl (D02 columns) for selected questions
    with (odir / ("%s_questions.jsonl" % base)).open("w", encoding="utf-8") as f:
        for i in sel:
            r = rows[i][1]
            rec = {c: to_native(r[c]) for c in QUESTION_COLS if c in r.index}
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    # 3) records CSV (idx, question, n_docs, documents_joined) -- ' ||| ' join, like delucionqa
    with (odir / ("%s_records.csv" % base)).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "question", "n_docs", "documents_joined"])
        for new_idx, i in enumerate(sel):
            _, r, docs, _ = rows[i]
            w.writerow([new_idx, r.get("question", ""), len(docs), " ||| ".join(docs)])

    # 4) selection provenance manifest
    manifest = {"subset": args.subset, "label": args.label, "top_docs": args.top_docs,
                "documents_chosen": len(chosen), "doc_hashes": chosen,
                "questions_selected": len(sel), "answerable": n_p, "unanswerable": n_n,
                "source_rows": int(len(df)), "unique_questions_in_subset": len(rows),
                "rule": "greedy full-cover by md5(doc); question kept iff ALL its docs chosen; "
                        "first-occurrence order over train+validation+test"}
    (odir / ("%s_selection.json" % base)).write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    print("[prep] wrote: %s_corpus.jsonl (%d docs), %s_questions.jsonl (%d), %s_records.csv, %s_selection.json"
          % (base, len(corpus_docs), base, len(sel), base, base))
    print("[prep] NEXT: python build_gold_map.py --source data/%s_questions.jsonl" % base)


if __name__ == "__main__":
    main()
