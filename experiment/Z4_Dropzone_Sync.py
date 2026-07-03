#!/usr/bin/env python3
"""
Z4_Dropzone_Sync.py
-------------------
Mirrors the latest run's outputs to a controlled drop-zone folder so external
analysis (e.g., Cowork mode) can read run data without needing direct access
to the production runs/ tree.

The dropzone accumulates per-run snapshots across a batch (older snapshots are
preserved). Cumulative CSVs are overwritten each sync so the dropzone always
reflects the latest analysis state.

Place at experiment/Z4_Dropzone_Sync.py.
Runs as the third Z stage in A0 after Z1 and Z2.

Usage:
    python experiment/Z4_Dropzone_Sync.py

Output (in Documentation/GovRAG/analysis_dropzone/):
    master_runs.csv               (cumulative, overwritten)
    Z1_PAPER_ANALYSIS.csv         (cumulative, overwritten)
    Z2_DECISION_TRACE.csv         (cumulative, overwritten)
    MASTER_EVALUATION_LOG.csv     (cumulative, overwritten)
    <run_id>/                     (per-run snapshot; accumulated across batch)
"""
import shutil
import sys
from pathlib import Path

# Script lives in experiment/; project root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "runs"
OUTPUT_DIR = PROJECT_ROOT / "output"
DROPZONE = PROJECT_ROOT / "Documentation" / "GovRAG" / "analysis_dropzone"

# Cumulative analysis files (overwritten per sync)
CUMULATIVE_FILES = [
    RUNS_DIR / "master_runs.csv",
    RUNS_DIR / "Z1_PAPER_ANALYSIS.csv",
    RUNS_DIR / "Z2_DECISION_TRACE.csv",
    OUTPUT_DIR / "MASTER_EVALUATION_LOG.csv",
]


def find_latest_run() -> Path:
    """Find the most recent run_<id>_<...> folder by modification time."""
    if not RUNS_DIR.exists():
        return None
    candidates = [
        d for d in RUNS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("run_")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def safe_copy_file(src: Path, dst_dir: Path) -> str:
    """Copy a single file into dst_dir, overwriting if it exists."""
    if not src.exists() or not src.is_file():
        return f"   [skip] {src.name} (not found at {src})"
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst_dir / src.name)
    return f"   [copy] {src.name}"

import time

def safe_copy_run_snapshot(src: Path, dst: Path) -> str:
    if not src.exists() or not src.is_dir():
        return f"   [skip] {src.name} (not a directory)"
    if dst.exists():
        for attempt in range(3):
            try:
                shutil.rmtree(dst)
                break
            except PermissionError:
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                # Last resort: overlay copy without delete
                try:
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    return f"   [overlay] {src.name}/ (could not delete first; files overwritten)"
                except Exception as e:
                    return f"   [error] {src.name}/ — {type(e).__name__}: {e}"
    try:
        shutil.copytree(src, dst)
        return f"   [copy] {src.name}/ (full run snapshot)"
    except Exception as e:
        return f"   [error] {src.name}/ — {type(e).__name__}: {e}"


def main() -> None:
    print("--- Z3: Dropzone Sync ---")
    print(f"Target dropzone: {DROPZONE}")

    DROPZONE.mkdir(parents=True, exist_ok=True)

    # 1. Cumulative CSVs (overwrite each sync)
    print("\nCumulative analysis files:")
    for src in CUMULATIVE_FILES:
        print(safe_copy_file(src, DROPZONE))

    # 2. Latest run snapshot (accumulates across batch)
    print("\nLatest run snapshot:")
    latest = find_latest_run()
    if latest:
        dst = DROPZONE / latest.name
        print(safe_copy_run_snapshot(latest, dst))
    else:
        print("   [skip] no run folders found in runs/")

    # 3. Summary
    snapshot_count = sum(
        1 for d in DROPZONE.iterdir()
        if d.is_dir() and d.name.startswith("run_")
    )
    print(f"\n--- Z3 Complete ---")
    print(f"   Dropzone:        {DROPZONE}")
    print(f"   Run snapshots:   {snapshot_count}")


if __name__ == "__main__":
    main()