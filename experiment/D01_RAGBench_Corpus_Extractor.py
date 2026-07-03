"""
D01_RAGBench_Corpus_Extractor.py
================================
Reads galileo-ai/ragbench (DelucionQA + Emanual) from Hugging Face and
writes ONE consolidated corpus file per dataset.

Each output file is a one-record JSONL containing all unique chunks of
the corpus, in the shape your D-pipeline (D00 / flatten_evidence) expects:

    {"id": "DELUCIONQA_CORPUS",
     "question": "CORPUS_INIT",
     "documents": [<all unique chunks as strings>]}

Outputs (default):
    ./data/delucionqa_corpus.jsonl
    ./data/emanual_corpus.jsonl

Usage:
    pip install datasets huggingface_hub          (one-time)
    python D01_RAGBench_Corpus_Extractor.py
    python D01_RAGBench_Corpus_Extractor.py --out ./data
    python D01_RAGBench_Corpus_Extractor.py --only delucionqa

Notes:
- Single source: galileo-ai/ragbench. No fallbacks.
- Deduplicates chunks by exact text match (SHA-1 hash). Same chunk reused
  across multiple questions appears once in the output.
- All splits (train / validation / test) are merged into one corpus record,
  because the manual is a single document and split membership doesn't
  matter for graph construction.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from datasets import load_dataset


HF_REPO = "galileo-ai/ragbench"

CORPORA = {
    "delucionqa": {
        "config":             "delucionqa",
        "expected_chunks":    1046,
        "label":              "Jeep Gladiator manual",
    },
    "emanual": {
        "config":             "emanual",
        "expected_chunks":    261,
        "label":              "Samsung TV manual",
    },
}


def extract_corpus(corpus_key: str, spec: dict, out_path: Path) -> None:
    config = spec["config"]
    print(f"\n[{corpus_key}] loading {HF_REPO} / {config}  ({spec['label']})")

    ds = load_dataset(HF_REPO, config)
    splits = list(ds.keys()) if hasattr(ds, "keys") else ["default"]
    print(f"[{corpus_key}] splits found: {splits}")

    seen_hashes: set = set()
    unique_chunks: list = []
    total_rows = 0

    for split_name in splits:
        ds_split = ds[split_name] if hasattr(ds, "keys") else ds
        for row in ds_split:
            total_rows += 1
            for chunk in row.get("documents", []):
                if not isinstance(chunk, str) or not chunk.strip():
                    continue
                h = hashlib.sha1(chunk.encode("utf-8")).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                unique_chunks.append(chunk)

    print(f"[{corpus_key}] rows scanned : {total_rows}")
    print(f"[{corpus_key}] unique chunks: {len(unique_chunks)}  "
          f"(expected ~{spec['expected_chunks']})")

    record = {
        "id":        f"{corpus_key.upper()}_CORPUS",
        "question":  "CORPUS_INIT",
        "documents": unique_chunks,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[{corpus_key}] wrote: {out_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract RAGBench corpus to a single consolidated JSONL per dataset.")
    ap.add_argument("--out",  type=str, default="./data",
                    help="Output directory (default ./data)")
    ap.add_argument("--only", type=str, default=None, choices=list(CORPORA),
                    help="Run on only one corpus.")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    keys = [args.only] if args.only else list(CORPORA)
    for k in keys:
        out_path = out_dir / f"{k}_corpus.jsonl"
        extract_corpus(k, CORPORA[k], out_path)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
