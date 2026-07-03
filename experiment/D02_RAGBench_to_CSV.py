"""
D02_RAGBench_to_CSV.py
======================
Single-pass extractor: parquet -> exploded CSV.

Reads the 3 parquet splits per corpus, combines them, dedupes the 2x
system-response duplication, explodes the documents list to one row per
chunk, and writes a clean CSV.

Each output row = one unique (id, doc_index, document) triple, with the
corresponding question and TRACe scores carried alongside.

Composite primary key: record_id = "<id>_<doc_index>"

Inputs (--in_dir):
    delucionqa-train.parquet  delucionqa-validation.parquet  delucionqa-test.parquet
    emanual-train.parquet     emanual-validation.parquet     emanual-test.parquet

Outputs (--out_dir):
    delucionqa.csv     2,739 rows  (913 questions x 3 doc_indexes)
    emanual.csv        1,977 rows  (659 questions x 3 doc_indexes)

Output columns (in order):
    record_id, id, doc_index, split, question, document, response,
    adherence_score, relevance_score, utilization_score, completeness_score

Usage:
    pip install pandas pyarrow
    python D02_RAGBench_to_CSV.py --in_dir ./data/parquet --out_dir ./data
    python D02_RAGBench_to_CSV.py --in_dir ./data/parquet --only delucionqa
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


CORPORA = ["delucionqa", "emanual"]
SPLITS = ["train", "validation", "test"]

KEEP_COLS = [
    "record_id", "id", "doc_index", "split",
    "question", "document", "response",
    "adherence_score", "relevance_score", "utilization_score", "completeness_score",
]


def build(corpus: str, in_dir: Path, out_dir: Path) -> None:
    print(f"\n[{corpus}] reading parquet from {in_dir}/")

    # 1) Read 3 splits, add split column, concat
    frames = []
    for sp in SPLITS:
        path = in_dir / f"{corpus}-{sp}.parquet"
        if not path.exists():
            print(f"[FATAL] missing parquet: {path}")
            sys.exit(2)
        df = pd.read_parquet(path)
        df["split"] = sp
        frames.append(df)
        print(f"  {sp:<11}: {len(df)} rows")
    df = pd.concat(frames, ignore_index=True)
    print(f"  total           : {len(df)} rows")

    # 2) Dedupe 2x system-response duplication (one row per question id; first system kept)
    df = df.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)
    print(f"  unique question ids       : {len(df)}")

    # 3) Explode documents -> one row per chunk
    df = df.explode("documents").reset_index(drop=True)
    df["doc_index"] = df.groupby("id").cumcount()
    df["record_id"] = df["id"].astype(str) + "_" + df["doc_index"].astype(str)
    df = df.rename(columns={"documents": "document"})
    print(f"  after explode             : {len(df)} rows")

    # 4) Select + write
    available = [c for c in KEEP_COLS if c in df.columns]
    out_path = out_dir / f"{corpus}.csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    df[available].to_csv(out_path, index=False, encoding="utf-8")
    print(f"  -> {out_path}  ({len(df)} rows, {len(available)} cols)")

    # 5) Integrity sanity
    n_unique = df["record_id"].nunique()
    n_per_id = df.groupby("id").size()
    print(f"  record_id uniqueness      : {n_unique}/{len(df)}  -> "
          f"{'PASS' if n_unique == len(df) else 'FAIL'}")
    print(f"  ids with exactly 3 rows   : {(n_per_id == 3).sum()}/{len(n_per_id)}  -> "
          f"{'PASS' if (n_per_id == 3).all() else 'FAIL'}")


def main() -> int:
    ap = argparse.ArgumentParser(description="parquet -> exploded CSV (single-pass).")
    ap.add_argument("--in_dir",  default="./data/parquet")
    ap.add_argument("--out_dir", default="./data")
    ap.add_argument("--only",    default=None, choices=CORPORA)
    args = ap.parse_args()

    in_dir, out_dir = Path(args.in_dir), Path(args.out_dir)
    if not in_dir.exists():
        print(f"[FATAL] --in_dir does not exist: {in_dir}")
        return 2

    keys = [args.only] if args.only else CORPORA
    for corpus in keys:
        build(corpus, in_dir, out_dir)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
