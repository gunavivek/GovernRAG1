"""
D02_RAGBench_Parent_Extractor.py
================================
Stage 1 of the data-prep pipeline.

Reads the 6 RAGBench parquet files (3 splits × 2 corpora) and writes ONE
canonical parent JSONL per corpus that contains ALL columns from ALL splits.
The parent file is the immutable single source of truth; derivations
(corpus.jsonl, questions.jsonl, any future view) come from D03.

Inputs (--in_dir):
    delucionqa-train.parquet · delucionqa-validation.parquet · delucionqa-test.parquet
    emanual-train.parquet    · emanual-validation.parquet    · emanual-test.parquet

Outputs (--out_dir):
    delucionqa_parent.jsonl    -- ~1826 rows: 913 questions × 2 system responses
    emanual_parent.jsonl       -- ~1318 rows: 659 questions × 2 system responses

Each line of the parent JSONL is one HF row, preserving every column from
the parquet PLUS a 'split' field naming the source split (train/val/test).

Usage:
    pip install pandas pyarrow
    python D02_RAGBench_Parent_Extractor.py --in_dir ./data/parquet --out_dir ./data
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


CORPORA = ["delucionqa", "emanual"]
SPLITS = ["train", "validation", "test"]


def _to_native(v):
    """Recursively convert numpy / pandas / array values to JSON-native Python types.
    Recursion is essential: documents_sentences and the keys columns are
    list-of-numpy-arrays, and a non-recursive .tolist() leaves the inner arrays
    as opaque str(array(...)) blobs."""
    if hasattr(v, "tolist"):
        return _to_native(v.tolist())
    if isinstance(v, list):
        return [_to_native(x) for x in v]
    if isinstance(v, tuple):
        return [_to_native(x) for x in v]
    if isinstance(v, dict):
        return {k: _to_native(val) for k, val in v.items()}
    return v


def extract_parent(corpus: str, in_dir: Path, out_path: Path) -> int:
    print(f"\n[{corpus}] reading parquet files from {in_dir}/")
    rows = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out_f:
        for split in SPLITS:
            path = in_dir / f"{corpus}-{split}.parquet"
            if not path.exists():
                raise FileNotFoundError(f"Missing parquet: {path}")
            df = pd.read_parquet(path)
            print(f"  {split:<11}: {len(df)} rows  ·  columns: {list(df.columns)}")
            for _, row in df.iterrows():
                rec = {col: _to_native(row[col]) for col in df.columns}
                rec["split"] = split
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                rows += 1
    print(f"[{corpus}] -> {out_path}  ({rows} total rows)")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 1: parquet -> parent JSONL.")
    ap.add_argument("--in_dir",  type=str, default="./data/parquet")
    ap.add_argument("--out_dir", type=str, default="./data")
    ap.add_argument("--only",    type=str, default=None, choices=CORPORA)
    args = ap.parse_args()

    in_dir, out_dir = Path(args.in_dir), Path(args.out_dir)
    if not in_dir.exists():
        print(f"[FATAL] --in_dir does not exist: {in_dir}", file=sys.stderr)
        return 2

    keys = [args.only] if args.only else CORPORA
    for corpus in keys:
        extract_parent(corpus, in_dir, out_dir / f"{corpus}_parent.jsonl")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
