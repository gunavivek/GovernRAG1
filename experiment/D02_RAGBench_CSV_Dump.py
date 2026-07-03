"""
D02_RAGBench_CSV_Dump.py
========================
Minimal raw extractor. Downloads (id, documents) from all three splits of
galileo-ai/ragbench / delucionqa and emanual, dumps to CSV.

One CSV row per (split, id, doc_index, document_text).
No dedup, no stats, no profiling — caller does pre-formatting.

Usage:
    pip install datasets huggingface_hub
    python D02_RAGBench_CSV_Dump.py
    python D02_RAGBench_CSV_Dump.py --out ./data
    python D02_RAGBench_CSV_Dump.py --only delucionqa
"""
import argparse
import csv
import sys
from pathlib import Path

from datasets import load_dataset

HF_REPO = "galileo-ai/ragbench"
CORPORA = ["delucionqa", "emanual"]


def dump(corpus: str, out_path: Path) -> None:
    print(f"[{corpus}] loading {HF_REPO} / {corpus} ...")
    ds = load_dataset(HF_REPO, corpus)
    splits = list(ds.keys())
    print(f"[{corpus}] splits found: {splits}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["split", "id", "doc_index", "document"])
        for split in splits:
            for row in ds[split]:
                rid = row.get("id", "")
                docs = row.get("documents") or []
                for i, doc in enumerate(docs):
                    if isinstance(doc, str):
                        w.writerow([split, rid, i, doc])
                        rows_written += 1

    print(f"[{corpus}] wrote {rows_written} rows -> {out_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Raw CSV dump of RAGBench (id, documents).")
    ap.add_argument("--out", type=str, default="./data", help="Output directory (default ./data)")
    ap.add_argument("--only", type=str, default=None, choices=CORPORA, help="Run on only one corpus.")
    args = ap.parse_args()

    out_dir = Path(args.out)
    keys = [args.only] if args.only else CORPORA
    for k in keys:
        dump(k, out_dir / f"{k}_raw.csv")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
