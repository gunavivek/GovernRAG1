# --------------------------------------------------------------------------
# A0_RAGBench_PrepFixA.py
#
# One-shot preparation script for Fix A:
#   1. Re-saves "RAGBench dataset description.csv" without BOM
#      (D1 reads pandas DataFrame columns by name; BOM corrupts column key)
#   2. Adds the `dataset` field to <corpus>_corpus.jsonl
#      (D2 looks up D1 mapping by record['dataset'], not record['id'])
#   3. Re-stages corpus.jsonl -> data/RGB_Single_Record.jsonl
#
# Run BEFORE D1 + A1.
#
# Usage:
#   python ./experiment/A0_RAGBench_PrepFixA.py delucionqa
#   python ./experiment/A0_RAGBench_PrepFixA.py emanual
# --------------------------------------------------------------------------
import json
import shutil
import sys
from pathlib import Path


CORPORA = ["delucionqa", "emanual"]

# Map our internal corpus key -> RAGBench dataset name in the CSV
CORPUS_TO_DATASET_NAME = {
    "delucionqa": "DelucionQA",
    "emanual":    "Emanual",
}


def project_root() -> Path:
    here = Path(__file__).resolve()
    if here.parent.name.lower() == "experiment":
        return here.parent.parent
    return here.parent.parent


def fix_csv_bom(csv_path: Path) -> bool:
    """Re-save the CSV as UTF-8 without BOM. Idempotent."""
    raw = csv_path.read_bytes()
    if not raw.startswith(b'\xef\xbb\xbf'):
        print(f"  [csv] no BOM detected, leaving as-is")
        return False
    cleaned = raw[3:]  # strip the 3-byte BOM
    csv_path.write_bytes(cleaned)
    print(f"  [csv] BOM stripped: {csv_path}")
    return True


def add_dataset_field_to_corpus(corpus_path: Path, dataset_name: str) -> dict:
    """Read corpus.jsonl, add `dataset` field, write back. Idempotent."""
    with corpus_path.open(encoding="utf-8") as f:
        rec = json.loads(f.readline())

    if rec.get("dataset") == dataset_name:
        print(f"  [corpus] dataset field already set to '{dataset_name}'")
        return rec

    rec["dataset"] = dataset_name
    with corpus_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  [corpus] added dataset='{dataset_name}'")
    return rec


def restage_to_RGB_Single_Record(corpus_path: Path, root: Path) -> Path:
    """Copy the patched corpus to the canonical D-pipeline input path."""
    dst = root / "data" / "RGB_Single_Record.jsonl"
    shutil.copy2(corpus_path, dst)
    print(f"  [stage] restaged -> {dst}")
    return dst


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1].lower() not in CORPORA:
        print(f"Usage: python A0_RAGBench_PrepFixA.py <{ '|'.join(CORPORA) }>")
        return 2
    corpus_key = sys.argv[1].lower()
    dataset_name = CORPUS_TO_DATASET_NAME[corpus_key]

    root = project_root()
    csv_path = root / "data" / "RAGBench dataset description.csv"
    corpus_path = root / "data" / f"{corpus_key}_corpus.jsonl"

    print(f"\n[Fix A — Prep for {corpus_key}]")
    print(f"  project_root  : {root}")
    print(f"  dataset_name  : {dataset_name}\n")

    # --- 1. CSV BOM fix ---
    print(f"[1/3] Sanitising RAGBench dataset description CSV")
    if not csv_path.exists():
        print(f"  [FATAL] CSV not found: {csv_path}")
        return 2
    fix_csv_bom(csv_path)

    # --- 2. Add `dataset` field to corpus ---
    print(f"\n[2/3] Patching corpus.jsonl")
    if not corpus_path.exists():
        print(f"  [FATAL] Corpus not found: {corpus_path}")
        return 2
    rec = add_dataset_field_to_corpus(corpus_path, dataset_name)
    print(f"        id={rec.get('id')!r}  dataset={rec.get('dataset')!r}  "
          f"chunks={len(rec.get('documents', []))}")

    # --- 3. Re-stage to RGB_Single_Record.jsonl ---
    print(f"\n[3/3] Re-staging to data/RGB_Single_Record.jsonl")
    restage_to_RGB_Single_Record(corpus_path, root)

    print(f"\n[Done]")
    print(f"\nNext steps:")
    print(f"  1. Run D1 to produce the global mapping JSON:")
    print(f"     python .\\experiment\\D1_Global_Domain_Matcher.py")
    print(f"  2. Re-run the build-phase orchestrator:")
    print(f"     python .\\experiment\\A1_RAGBench_D0_M0_Runner.py {corpus_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
