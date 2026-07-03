#!/usr/bin/env python3
"""
ABL1_Q5_Ablation_Runner.py
===========================
Ablation pipeline runner for the §6.2 Q5 (Reference Monitor) ablation study.

STRICT ISOLATION GUARANTEE
--------------------------
This runner does NOT touch `Code-Freeze/output/`. Every input is read from
preserved per-case folders in `analysis_dropzone/`, and every output is
written to a per-case workdir under `ablation_dropzone/<record_id>/`.

WHY PER-CASE WORKDIRS
---------------------
The frozen `Code-Freeze/output/` directory only ever holds the artifacts
from the most recent A0 run — it gets overwritten on every run by design.
But the Z3/Z4 dropzone sync (which runs at the end of every A0) preserves
each completed case's outputs to:

    analysis_dropzone/run_<timestamp>_rgb_<id>_<P|N>_<positive|negative>/
        d/D5_Extraction_Manifest.jsonl
        q/Q3_retrieved_evidence.jsonl
        ... (and the rest)

So there are 10 separately-preserved Q3 outputs (one per case), each in its
own dropzone folder. ABL1 reads from those 10 preserved copies.

For each case, ABL1 creates its own workdir at:

    ablation_dropzone/<record_id>/
        output/
            D5_Extraction_Manifest.jsonl   (copied from baseline dropzone)
            Q3_retrieved_evidence.jsonl    (copied from baseline dropzone)
            Q5_routed_context.jsonl        (written by ablated Q5)
            Q6_final_answers.jsonl         (written by frozen Q6)
        ablation_manifest.json

The ablated Q5 takes explicit paths via its constructor.
The frozen Q6 uses CWD-relative paths, so the runner `os.chdir()`s to
`ablation_dropzone/<record_id>/` while Q6 runs, then `chdir`s back.

USAGE
-----
  cd <project_root>                                     # Documentation/GovRAG/
  python ./Ablation/ABL1_Q5_Ablation_Runner.py

PREREQUISITES
-------------
  - GEMINI_API_KEY is set (frozen Q6 calls Gemma-3-4B-IT once per case)
  - The 10 baseline runs exist under analysis_dropzone/
  - ablation_dropzone/ is writable

Expected runtime: ~5–10 minutes total. Expected API cost: < $1.
"""

import os
import sys
import json
import shutil
import re
import time
from pathlib import Path
from datetime import datetime

# --- Path discovery (read-only references to the project layout) ---
SCRIPT_DIR = Path(__file__).resolve().parent       # Documentation/GovRAG/Ablation/
GOVRAG_ROOT = SCRIPT_DIR.parent                    # Documentation/GovRAG/
ABLATION_DIR = SCRIPT_DIR
FROZEN_DIR = GOVRAG_ROOT / "Code-Freeze"           # READ-ONLY (we import Q6 from here)
ANALYSIS_DROPZONE = GOVRAG_ROOT / "analysis_dropzone"   # READ-ONLY (preserved baseline artifacts)
ABLATION_DROPZONE = GOVRAG_ROOT / "ablation_dropzone"   # we own this — created if absent

# --- .env discovery and loading ---
# Frozen Q6 calls `load_dotenv()` at module import time, which searches from
# the current working directory upward. Because ABL1 chdir's into a per-case
# workdir under ablation_dropzone/<rid>/ before importing Q6, Q6's load_dotenv()
# walks up from there and may NOT find your .env file (depending on where you
# keep it). To avoid that fragility, ABL1 finds and loads the .env file ITSELF
# at startup, before any Q6 import. Once env vars are set, they persist for
# the whole process — chdir does not unset them.
def _find_and_load_dotenv():
    """Look for a .env file in likely project locations and load it."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[WARN] python-dotenv not installed; relying on shell-exported env vars.")
        return None

    # Candidate locations in order of preference.
    # Add yours here if it lives somewhere else.
    candidates = [
        GOVRAG_ROOT / ".env",                          # Documentation/GovRAG/.env
        GOVRAG_ROOT.parent / ".env",                   # Documentation/.env
        GOVRAG_ROOT.parent.parent / ".env",            # conceptual_GraphRAG/.env
        GOVRAG_ROOT.parent.parent / "experiment" / ".env",  # conceptual_GraphRAG/experiment/.env
        FROZEN_DIR / ".env",                           # Documentation/GovRAG/Code-Freeze/.env
        Path.cwd() / ".env",                           # wherever the user invoked python from
    ]
    for env_path in candidates:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path))
            print(f"[ENV] Loaded .env from {env_path}")
            return env_path
    print("[WARN] No .env file found in expected locations. "
          "Relying on shell-exported env vars.")
    print("       Searched:")
    for c in candidates:
        print(f"         - {c}")
    return None


# --- Module imports ---
# Make both directories importable. Ablated Q5 from Ablation/; frozen Q6 from Code-Freeze/.
for d in (str(ABLATION_DIR), str(FROZEN_DIR)):
    if d not in sys.path:
        sys.path.insert(0, d)

# Load .env BEFORE any module that depends on GEMINI_API_KEY gets imported.
_find_and_load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    print("[FATAL] GEMINI_API_KEY is not set after .env loading. "
          "Frozen Q6 will fail. Aborting before running cases.")
    sys.exit(1)
else:
    print(f"[ENV] GEMINI_API_KEY is set (length={len(os.getenv('GEMINI_API_KEY'))}).")


def discover_baseline_runs():
    """Find the most-recent preserved dropzone folder per rgb_<id>_<P|N> case."""
    if not ANALYSIS_DROPZONE.exists():
        raise FileNotFoundError(f"analysis_dropzone not found at {ANALYSIS_DROPZONE}")

    by_record = {}
    for run_folder in sorted(ANALYSIS_DROPZONE.glob("run_*_rgb_*"), reverse=True):
        m = re.search(r"rgb_(\d+)_([PN])", run_folder.name)
        if not m:
            continue
        record_id = f"rgb_{m.group(1)}_{m.group(2)}"
        if not (run_folder / "q" / "Q3_retrieved_evidence.jsonl").exists():
            continue
        if not (run_folder / "d" / "D5_Extraction_Manifest.jsonl").exists():
            continue
        if record_id not in by_record:
            by_record[record_id] = run_folder
    return by_record


def stage_inputs(baseline_run: Path, case_workdir: Path):
    """Copy preserved D5 + Q3 into the per-case ablation workdir's output/ folder.

    The output/ subdirectory is required because frozen Q6 hard-codes
    `output/Q5_routed_context.jsonl` as its input path. We give Q6 an output/
    that lives inside the ablation workdir, NOT in Code-Freeze/.
    """
    case_output = case_workdir / "output"
    case_output.mkdir(parents=True, exist_ok=True)
    shutil.copy(baseline_run / "d" / "D5_Extraction_Manifest.jsonl",
                case_output / "D5_Extraction_Manifest.jsonl")
    shutil.copy(baseline_run / "q" / "Q3_retrieved_evidence.jsonl",
                case_output / "Q3_retrieved_evidence.jsonl")
    return case_output


def run_ablated_q5(case_output: Path):
    """Invoke the ablated Q5 with explicit paths under the case workdir.

    Reads from case_output/D5_*.jsonl and case_output/Q3_*.jsonl.
    Writes to  case_output/Q5_routed_context.jsonl.
    Code-Freeze/output/ is NOT touched.
    """
    import importlib
    if "Q5_Gov_Context_Router_Ablated" in sys.modules:
        del sys.modules["Q5_Gov_Context_Router_Ablated"]
    Q5A = importlib.import_module("Q5_Gov_Context_Router_Ablated")
    router = Q5A.GovContextRouterAblated(
        manifest_path=str(case_output / "D5_Extraction_Manifest.jsonl"),
        evidence_path=str(case_output / "Q3_retrieved_evidence.jsonl"),
        output_path=str(case_output / "Q5_routed_context.jsonl"),
    )
    router.process_file()


def run_frozen_q6_in_workdir(case_workdir: Path):
    """Invoke frozen Q6 from inside the case workdir.

    Frozen Q6 uses CWD-relative paths (`output/Q5_routed_context.jsonl`).
    We chdir to case_workdir so it reads/writes from case_workdir/output/.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(case_workdir)
        import importlib
        if "Q6_Gov_Answer_Generation" in sys.modules:
            del sys.modules["Q6_Gov_Answer_Generation"]
        Q6 = importlib.import_module("Q6_Gov_Answer_Generation")
        Q6.run_q6_synthesis()
    finally:
        os.chdir(original_cwd)


def write_case_manifest(case_workdir: Path, record_id: str, baseline_run: Path):
    manifest = {
        "record_id": record_id,
        "ablation_pipeline": "Q5 Reference Monitor — DP3 (predicate enforcement) disabled",
        "ablated_module": "Q5_Gov_Context_Router_Ablated.GovContextRouterAblated",
        "frozen_modules_invoked": ["Q6_Gov_Answer_Generation.run_q6_synthesis"],
        "baseline_run_used": str(baseline_run.relative_to(GOVRAG_ROOT)),
        "inputs_staged_from": {
            "D5_Extraction_Manifest.jsonl": str((baseline_run / "d" / "D5_Extraction_Manifest.jsonl").relative_to(GOVRAG_ROOT)),
            "Q3_retrieved_evidence.jsonl":  str((baseline_run / "q" / "Q3_retrieved_evidence.jsonl").relative_to(GOVRAG_ROOT)),
        },
        "outputs_written_to": {
            "Q5_routed_context.jsonl": str((case_workdir / "output" / "Q5_routed_context.jsonl").relative_to(GOVRAG_ROOT)),
            "Q6_final_answers.jsonl":  str((case_workdir / "output" / "Q6_final_answers.jsonl").relative_to(GOVRAG_ROOT)),
        },
        "baseline_outputs_for_comparison": {
            "Q5_routed_context.jsonl": str((baseline_run / "q" / "Q5_routed_context.jsonl").relative_to(GOVRAG_ROOT)),
            "Q6_final_answers.jsonl":  str((baseline_run / "q" / "Q6_final_answers.jsonl").relative_to(GOVRAG_ROOT)),
        },
        "ablation_run_at": datetime.now().isoformat(),
    }
    with open(case_workdir / "ablation_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def main():
    print("=" * 80)
    print("  ABL1: Q5 Reference-Monitor Ablation Pipeline Runner")
    print("=" * 80)
    print(f"  ABLATION_DIR      : {ABLATION_DIR}")
    print(f"  FROZEN_DIR        : {FROZEN_DIR}     (READ-ONLY, frozen Q6 imported)")
    print(f"  ANALYSIS_DROPZONE : {ANALYSIS_DROPZONE} (READ-ONLY, baseline artifacts)")
    print(f"  ABLATION_DROPZONE : {ABLATION_DROPZONE} (per-case workdirs created here)")
    print(f"  Code-Freeze/output/ is NOT touched by this runner.")
    print()

    baseline_runs = discover_baseline_runs()
    if not baseline_runs:
        print("[FATAL] No baseline runs found in analysis_dropzone/.")
        sys.exit(1)

    print(f"  Discovered {len(baseline_runs)} baseline runs:")
    for rid, folder in sorted(baseline_runs.items()):
        print(f"    {rid:14s}  <-  {folder.name}")
    print()

    ABLATION_DROPZONE.mkdir(parents=True, exist_ok=True)

    summary = []
    t0 = time.time()
    for i, (record_id, baseline_run) in enumerate(sorted(baseline_runs.items()), 1):
        print(f"\n[{i}/{len(baseline_runs)}] Ablating {record_id} (baseline: {baseline_run.name})")
        print("-" * 80)
        case_t0 = time.time()
        case_workdir = ABLATION_DROPZONE / record_id

        try:
            # 1. Per-case workdir + staged inputs (NOTHING in Code-Freeze/output/)
            case_output = stage_inputs(baseline_run, case_workdir)

            # 2. Ablated Q5 reads/writes inside case_output/ via constructor injection
            run_ablated_q5(case_output)

            # 3. Frozen Q6 invoked with chdir = case_workdir so its `output/...` paths
            #    resolve to case_workdir/output/ (NOT Code-Freeze/output/)
            run_frozen_q6_in_workdir(case_workdir)

            # 4. Per-case manifest
            write_case_manifest(case_workdir, record_id, baseline_run)

            # 5. Read back for summary
            with open(case_workdir / "output" / "Q6_final_answers.jsonl", 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        new_ans = json.loads(line)
                        break
            with open(baseline_run / "q" / "Q6_final_answers.jsonl", 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        old_ans = json.loads(line)
                        break

            summary.append({
                "record_id": record_id,
                "baseline_mode": old_ans.get("mode"),
                "baseline_answer": (old_ans.get("generated_answer") or "")[:200],
                "ablation_mode": new_ans.get("mode"),
                "ablation_answer": (new_ans.get("generated_answer") or "")[:200],
                "case_time_seconds": round(time.time() - case_t0, 1),
                "status": "OK"
            })
            print(f"  [OK] {record_id} ablated in {summary[-1]['case_time_seconds']}s")

        except Exception as e:
            print(f"  [FAIL] {record_id}: {e}")
            summary.append({"record_id": record_id, "status": "FAIL", "error": str(e)})

    summary_path = ABLATION_DROPZONE / "ABLATION_SUMMARY.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_cases": len(summary),
            "total_time_seconds": round(time.time() - t0, 1),
            "ablation_pipeline": "Q5 DP3 disabled (frozen Q6 reused, scratch isolated per case)",
            "scratch_strategy": "per-case workdir under ablation_dropzone/<record_id>/",
            "cases": summary
        }, f, indent=2)

    print()
    print("=" * 80)
    print(f"  ABL1 complete in {round(time.time() - t0, 1)}s")
    print(f"  Per-case workdirs in: {ABLATION_DROPZONE}")
    print(f"  Summary:              {summary_path}")
    print(f"  Code-Freeze/output/ was NOT modified.")
    print("=" * 80)
    print()
    print("  Baseline vs Ablation (first 100 chars of each answer):")
    print("  " + "-" * 76)
    for s in summary:
        if s.get("status") == "OK":
            print(f"  {s['record_id']:14s}")
            print(f"    BASELINE [{s['baseline_mode']:25s}]: {s['baseline_answer'][:100]}")
            print(f"    ABLATION [{s['ablation_mode']:25s}]: {s['ablation_answer'][:100]}")
        else:
            print(f"  {s['record_id']:14s}  FAILED: {s.get('error', 'unknown')}")
    print()
    print("  Next step: run ABL2_Verdict_Grader.py to produce ABLATION_REPORT.md.")


if __name__ == "__main__":
    main()
