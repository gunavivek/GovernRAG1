from datasets import load_dataset

# Scan one subset, but ALL splits in one run
SUBSET = "covidqa"   # change to "emanual", "cuad", etc. if needed
SPLITS = ["train", "validation", "test"]

needle = (
    "The Annual Business Plan for 2025 emphasizes three core pillars: "
    "Digital Transformation, Customer Experience (CX) Enhancement, and Operational Efficiency."
)

def row_contains(row: dict, needle: str) -> bool:
    """Check whether the needle text appears anywhere in the nested `documents` field."""
    docs = row.get("documents")
    if not docs:
        return False

    parts = []
    for doc in docs:
        # each doc is typically a list like ["0a", "Title: ..."] or ["0b", "Passage: ..."]
        for item in doc:
            if isinstance(item, str):
                parts.append(item)

    big_text = " ".join(parts)
    return needle in big_text

def search_split(subset: str, split: str):
    print(f"\n=== Searching subset='{subset}', split='{split}' ===")
    try:
        ds = load_dataset("galileo-ai/ragbench", subset, split=split)
    except Exception as e:
        print(f"  Could not load this split ({e}). Skipping.")
        return

    print(f"  Dataset loaded: {len(ds)} rows")

    matches = []

    # IMPORTANT: iterate over rows; each `row` is a dict
    for idx, row in enumerate(ds):
        if row_contains(row, needle):
            matches.append(idx)

    if not matches:
        print("  No matches found in this split.")
        return

    print(f"  Found {len(matches)} matching row(s): {matches}")
    for idx in matches:
        r = ds[idx]
        print("\n" + "-" * 80)
        print(f"ROW INDEX: {idx}")
        print(f"id: {r.get('id')}")
        print(f"dataset_name: {r.get('dataset_name')}")
        print(f"question: {r.get('question')}")
        print("documents:")
        for doc in r.get("documents", []):
            print("  ", doc)

def main():
    for split in SPLITS:
        search_split(SUBSET, split)

if __name__ == "__main__":
    main()