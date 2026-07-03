"""
D02_RAGBench_Parquet_Loader.py
==============================
Reads the 6 RAGBench parquet files (downloaded locally from HF) and emits
D-pipeline-ready inputs for both A1 (corpus build) and A2 (per-question runs).

Inputs (local parquet files in --in_dir):
    delucionqa-train.parquet · delucionqa-validation.parquet · delucionqa-test.parquet
    emanual-train.parquet    · emanual-validation.parquet    · emanual-test.parquet

Outputs (per corpus, in --out_dir):
    <corpus>_corpus.jsonl     -- 1 record with all UNIQUE chunks       (feeds A1 / D0 / M0)
    <corpus>_questions.jsonl  -- 1 record per UNIQUE question id       (feeds A2 / Q0 per record)

Also prints a summary: rows per split, unique ids, columns kept, unique chunks.

Usage:
    pip install pandas pyarrow
    python D02_RAGBench_Parquet_Loader.py --in_dir ./data/parquet --out_dir ./data
    python D02_RAGBench_Parquet_Loader.py --in_dir ./data/parquet --only delucionqa
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


CORPORA = ["delucionqa", "emanual"]
SPLITS = ["train", "validation", "test"]

# Columns to preserve in questions.jsonl (kept if present; ignored if absent)
QUESTION_COLS = [
    "id", "split",
    "question", "response",
    "adherence_score", "relevance_score", "utilization_score", "completeness_score",
    "supporting_sentence_keys", "unsupported_response_sentence_keys",
    "all_relevant_sentence_keys", "all_utilized_sentence_keys",
    "documents_sentences", "response_sentences",
]


def _to_native(v):
    """Convert numpy/pandas values to JSON-serialisable Python natives."""
    if hasattr(v, "tolist"):
        return v.tolist()
    return v


def load_corpus(in_dir: Path, corpus: str) -> pd.DataFrame:
    frames = []
    for split in SPLITS:
        path = in_dir / f"{corpus}-{split}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Missing parquet file: {path}")
        df = pd.read_parquet(path)
        df["split"] = split
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def write_corpus_jsonl(df: pd.DataFrame, corpus: str, out_path: Path) -> int:
    """Single record with the de-duplicated chunk corpus. Feeds A1 (M-pipeline build)."""
    seen, unique_chunks = set(), []
    for docs in df["documents"]:
        if docs is None:
            continue
        for chunk in docs:
            if not isinstance(chunk, str) or not chunk.strip():
                continue
            h = hashlib.sha1(chunk.encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            unique_chunks.append(chunk)

    record = {
        "id":        f"{corpus.upper()}_CORPUS",
        "question":  "CORPUS_INIT",
        "documents": unique_chunks,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(unique_chunks)


def write_questions_jsonl(df: pd.DataFrame, corpus: str, out_path: Path) -> int:
    """One record per unique question id. Feeds A2 (Q-pipeline iteration)."""
    cols = [c for c in QUESTION_COLS if c in df.columns]
    df_uniq = df.drop_duplicates(subset=["id"], keep="first")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for _, row in df_uniq.iterrows():
            rec = {c: _to_native(row[c]) for c in cols}
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            n += 1
    return n, cols


def process(corpus: str, in_dir: Path, out_dir: Path) -> None:
    print(f"\n[{corpus}] loading parquet from {in_dir}/")
    df = load_corpus(in_dir, corpus)

    print(f"[{corpus}] rows total      : {len(df)}")
    print(f"[{corpus}] splits          : {df['split'].value_counts().to_dict()}")
    print(f"[{corpus}] unique ids      : {df['id'].nunique()}")
    print(f"[{corpus}] columns in file : {list(df.columns)}")

    n_chunks = write_corpus_jsonl(df, corpus, out_dir / f"{corpus}_corpus.jsonl")
    n_questions, cols_kept = write_questions_jsonl(df, corpus, out_dir / f"{corpus}_questions.jsonl")

    print(f"[{corpus}] -> {corpus}_corpus.jsonl     ({n_chunks} unique chunks)")
    print(f"[{corpus}] -> {corpus}_questions.jsonl  ({n_questions} unique questions, {len(cols_kept)} columns)")
    print(f"[{corpus}]    columns kept : {cols_kept}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Load RAGBench parquet files into D-pipeline-ready JSONL.")
    ap.add_argument("--in_dir",  type=str, default="./data/parquet", help="Directory containing the 6 parquet files")
    ap.add_argument("--out_dir", type=str, default="./data",         help="Directory to write JSONL outputs")
    ap.add_argument("--only",    type=str, default=None, choices=CORPORA, help="Run on only one corpus")
    args = ap.parse_args()

    in_dir, out_dir = Path(args.in_dir), Path(args.out_dir)
    if not in_dir.exists():
        print(f"[FATAL] --in_dir does not exist: {in_dir}", file=sys.stderr)
        return 2

    keys = [args.only] if args.only else CORPORA
    for corpus in keys:
        try:
            process(corpus, in_dir, out_dir)
        except FileNotFoundError as e:
            print(f"[FATAL] {e}", file=sys.stderr)
            return 2

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
