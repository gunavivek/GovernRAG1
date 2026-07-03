"""
validate_ragbench_csv_dump.py
=============================
Quick validator for the CSV files produced by D02_RAGBench_CSV_Dump.py.

Checks:
  1. (id, doc_index) uniqueness
  2. duplicate (id, doc_index) pairs (true CSV-row duplicates)
  3. unique id count + ids that appear multiple times
  4. row count per split
  5. content duplicates (same document text under different ids)
  6. ids appearing in multiple splits (cross-split contamination check)

Usage:
    python validate_ragbench_csv_dump.py ./data/delucionqa_raw.csv ./data/emanual_raw.csv
"""

import csv
import sys
from collections import Counter, defaultdict


def _bump_csv_field_limit():
    """Set csv field-size limit to the largest value the platform allows.
    sys.maxsize overflows C long on Windows, so we step down until it accepts."""
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            return
        except OverflowError:
            max_int = int(max_int / 10)


def validate(csv_path: str) -> None:
    print(f"\n{'=' * 78}\n  {csv_path}\n{'=' * 78}")

    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    n = len(rows)
    print(f"  total rows                  : {n}")

    # 1. (id, doc_index) uniqueness
    pair_counts = Counter((r["id"], r["doc_index"]) for r in rows)
    unique_pairs = len(pair_counts)
    duplicates = {k: v for k, v in pair_counts.items() if v > 1}
    print(f"  unique (id, doc_index)      : {unique_pairs}")
    print(f"  duplicate (id, doc_index)   : {len(duplicates)} pairs duplicated")
    if duplicates:
        for (rid, di), c in list(duplicates.items())[:5]:
            print(f"    -> id={rid!r}  doc_index={di}  appears {c}x")

    # 2. unique id count
    id_counts = Counter(r["id"] for r in rows)
    print(f"  unique ids                  : {len(id_counts)}")
    most_freq = id_counts.most_common(5)
    print(f"  top 5 most-frequent ids:")
    for rid, c in most_freq:
        print(f"    -> id={rid!r}  appears {c}x")

    # 3. rows per split
    split_counts = Counter(r["split"] for r in rows)
    print(f"  rows per split:")
    for split, c in sorted(split_counts.items()):
        print(f"    -> {split:<14}: {c}")

    # 4. ids appearing in multiple splits
    id_to_splits = defaultdict(set)
    for r in rows:
        id_to_splits[r["id"]].add(r["split"])
    multi_split_ids = {rid: sps for rid, sps in id_to_splits.items() if len(sps) > 1}
    print(f"  ids appearing in >1 split   : {len(multi_split_ids)}")
    if multi_split_ids:
        for rid, sps in list(multi_split_ids.items())[:3]:
            print(f"    -> id={rid!r}  splits={sorted(sps)}")

    # 5. content duplicates (same document text appearing under different (id, doc_index))
    doc_text_to_keys = defaultdict(list)
    for r in rows:
        doc_text_to_keys[r["document"]].append((r["split"], r["id"], r["doc_index"]))
    content_dup_groups = {t: ks for t, ks in doc_text_to_keys.items() if len(ks) > 1}
    print(f"  unique document texts       : {len(doc_text_to_keys)}")
    print(f"  document texts shared by >1 (id, doc_index) : {len(content_dup_groups)}")
    total_repeated_rows = sum(len(ks) for ks in content_dup_groups.values())
    print(f"  total CSV rows participating in such groups : {total_repeated_rows}")
    if content_dup_groups:
        top = sorted(content_dup_groups.items(), key=lambda x: -len(x[1]))[:3]
        for text, keys in top:
            preview = text.strip()[:80].replace("\n", " ")
            print(f"    -> {len(keys)} rows share doc: {preview!r}...")
            for sp, rid, di in keys[:3]:
                print(f"        {sp}  id={rid!r}  doc_index={di}")
            if len(keys) > 3:
                print(f"        ... and {len(keys) - 3} more")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validate_ragbench_csv_dump.py <csv_path> [<csv_path> ...]")
        return 2
    _bump_csv_field_limit()
    for path in sys.argv[1:]:
        validate(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
