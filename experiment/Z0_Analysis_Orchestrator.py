#!/usr/bin/env python3
"""
Z0_Analysis_Orchestrator.py
---------------------------
Orchestrates the post-run analysis Z-pipeline:
  Z1 (Paper Analysis) -> Z2 (Decision Trace) -> Z3 (Evidence Append) -> Z4 (Dropzone Sync)

Place at experiment/Z0_Analysis_Orchestrator.py.

Called by A0 as a single non-blocking post-run stage, replacing three separate
Z1/Z2/Z3 stage invocations. Mirrors the orchestration pattern of D0/M0/Q0.

Also runnable standalone (recommended after the final batch run, to capture the
last run's row in the dropzone after master_runs.csv has been appended):
    python experiment/Z0_Analysis_Orchestrator.py

Failure semantics:
- Continue-on-failure across Z1/Z2/Z3/Z4 (they are independent).
- Exit 0 if ALL succeeded; exit 1 if ANY failed (A0 treats the whole stage as
  non-blocking, so a non-zero exit doesn't kill the run).
"""
import subprocess
import os
import sys
import time

# Resolve project root: script lives in experiment/, project root is one level up
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if "experiment" in PROJECT_ROOT:
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
EXPERIMENT_DIR = os.path.join(PROJECT_ROOT, "experiment")

# --- The Z-pipeline manifest (frozen sequence) ---
Z_PIPELINE_TASKS = [
    ("Z1: Paper Analysis",   "Z1_Paper_analysis.py"),
    ("Z2: Decision Trace",   "Z2_Decision_Trace.py"),
    ("Z3: Evidence Append",  "Z3_Evidence_Append.py"),
    ("Z4: Dropzone Sync",    "Z4_Dropzone_Sync.py"),
]


def run_module_streaming(name: str, script_name: str) -> bool:
    """
    Execute a Z sub-script and stream stdout in real time.
    Returns True on exit code 0; False otherwise (incl. missing script).
    """
    script_path = os.path.join(EXPERIMENT_DIR, script_name)

    print("\n" + "=" * 70)
    print(f" EXECUTING: {name}")
    print(f"SOURCE FILE: {script_name}")
    print("=" * 70 + "\n")

    if not os.path.exists(script_path):
        print(f" [WARN] Script file not found: {script_path}")
        return False

    start_time = time.time()

    try:
        process = subprocess.Popen(
            [sys.executable, "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Stream sub-script output as it arrives
        assert process.stdout is not None
        for line in process.stdout:
            print(f"  {line.rstrip()}")
            sys.stdout.flush()

        process.wait()

        elapsed = time.time() - start_time
        if process.returncode == 0:
            print(f"\n [SUCCESS] {name} finalized in {elapsed:.2f} seconds.")
            return True
        else:
            print(f"\n [FAILED] {name} exited with code {process.returncode} after {elapsed:.2f}s.")
            return False

    except Exception as e:
        print(f"[Z0 ERROR] Unexpected failure executing {name}: {e}")
        return False


def main() -> None:
    print("\n" + "X" * 80)
    print("      PHD RESEARCH: Z-PIPELINE POST-RUN ANALYSIS ORCHESTRATOR")
    print("      STAGES: Z1 (Paper Analysis) -> Z2 (Decision Trace) -> Z3 (Evidence Append) -> Z4 (Dropzone Sync)")
    print("X" * 80)

    overall_start = time.time()
    failures = []
    successes = []

    # Continue-on-failure: each Z stage is independent
    for name, script in Z_PIPELINE_TASKS:
        if run_module_streaming(name, script):
            successes.append(name)
        else:
            failures.append(name)

    total_time = time.time() - overall_start
    print("\n" + "#" * 40)
    print(f"# Z-PIPELINE COMPLETE")
    print(f"# TOTAL EXECUTION TIME: {total_time:.2f} seconds")
    print(f"# SUCCEEDED: {len(successes)} / {len(Z_PIPELINE_TASKS)}")
    if failures:
        print(f"# FAILURES (non-fatal at A0 level): {', '.join(failures)}")
    print("#" * 40)

    # Non-zero exit if any sub-stage failed (A0 treats Z0 as non-blocking)
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()