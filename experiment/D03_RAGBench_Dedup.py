"""
D03_RAGBench_Dedup.py
=====================
Deduplicates the raw CSV produced by D02_RAGBench_CSV_Dump.py.

Each (id, doc_index) pair appears 2x in the raw dump because RAGBench
includes multiple LLM-system responses per question. We collapse those
duplicates by keeping the FIRST occurrence per (id, doc_index) and
emit a new CSV with a composite primary key.

Output schema (5 columns):
    record_id   -- "<id>_<doc_index>"   (unique primary key)
    split       -- train / validation / test
    id          -- original RAGBench id
    doc_index   -- 0..2
    document    -- chunk text

Usage:
    python D03_RAGBench_Dedup.py ./data/delucionqa_raw.csv ./data/emanual_raw.csv

Outputs land beside each input as <stem-without-_raw>_dedup.csv:
    ./data/delucionqa_dedup.csv
    ./data/emanual_dedup.csv
"""

import csv
import sys
from collections import OrderedDict
from pathlib import Path


def _bump_csv_field_limit():
    """Set csv field-size limit portably (sys.maxsize overflows on Windows)."""
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            return
        except OverflowError:
            max_int = int(max_int / 10)


def dedup_file(in_path: str):
    in_path = Path(in_path)
    stem = in_path.stem
    if stem.endswith("_raw"):
        stem = stem[:-4]
    out_path = in_path.parent / f"{stem}_dedup.csv"

    seen = OrderedDict()
    rows_in = 0
    with in_path.open(encoding="utf-8") as fi:
        reader = csv.DictReader(fi)
        for row in reader:
            rows_in += 1
            key = (row["id"], row["doc_index"])
            if key in seen:
                continue
            seen[key] = row

    with out_path.open("w", encoding="utf-8", newline="") as fo:
        writer = csv.writer(fo)
        writer.writerow(["record_id", "split", "id", "doc_index", "document"])
        for (rid, di), row in seen.items():
            record_id = f"{rid}_{di}"
            writer.writerow([record_id, row["split"], rid, di, row["document"]])

    return out_path, rows_in, len(seen)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python D03_RAGBench_Dedup.py <csv_path> [<csv_path> ...]")
        return 2
    _bump_csv_field_limit()
    print(f"{'INPUT':<46} {'IN':>8} {'OUT':>8} {'OUTPUT':<60}")
    for path in sys.argv[1:]:
        out, n_in, n_out = dedup_file(path)
        print(f"{str(path):<46} {n_in:>8} {n_out:>8}  ->  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
