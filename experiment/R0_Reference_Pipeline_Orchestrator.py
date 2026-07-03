# --------------------------------------------------------------------------
# MODULE 0: R0_Reference_Pipeline_Orchestrator.py
# ARCHITECTURE: Streaming Executive Process Controller (mirrors M0 pattern)
# DISSERTATION PHASE: Reference Ontology Construction (Frozen Codebase)
# --------------------------------------------------------------------------
# PURPOSE
# - Orchestrate the two active R-pipeline scripts in sequence:
#       R3.5  Reference Ontology Builder
#       R4    Embedded Reference Ontology + Statistical Baseline
#
# - Mirror the M0 orchestrator structure so the conventions are identical
#   across pipelines (frozen-code discipline: do not modify R3.5 or R4).
#
# - Legacy R1 / R2 / R3 are prototype master orchestrators (HotpotQA-era)
#   and are NOT invoked here. They should be archived under
#   experiment/_archive/ for provenance.
#
# - Outputs (consumed downstream):
#       output/R_Reference_Ontology.gml              (intermediate)
#       output/R_Embedded_Reference_Ontology.graphml (feeds M3/M4 alignment)
#       output/R_Statistical_Baseline.json           (feeds D2 gatekeeper)
# --------------------------------------------------------------------------
import subprocess
import os
import time
import sys


# --- 0. Path Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if "experiment" in PROJECT_ROOT:
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
EXPERIMENT_DIR = os.path.join(PROJECT_ROOT, "experiment")

# Final assets the R-pipeline must produce
FINAL_ASSETS = [
    os.path.join(PROJECT_ROOT, "output", "R_Reference_Ontology.gml"),
    os.path.join(PROJECT_ROOT, "output", "R_Embedded_Reference_Ontology.graphml"),
    os.path.join(PROJECT_ROOT, "output", "R_Statistical_Baseline.json"),
]


# --- 1. THE TASK MANIFEST (Frozen & Sequenced) ---
R_PIPELINE_TASKS = [
    ("R3.5: Reference Ontology Construction", "R3.5_Reference_Ontology_Builder.py"),
    ("R4:   Embedded Ontology + Statistical Baseline", "R4_Embed_Reference_Ontology_V2.py"),
]


def get_task_subset(tasks, start_from=None):
    """Return full task list or tasks starting from a named stage/script."""
    if not start_from:
        return tasks

    start_from = start_from.strip().lower()

    for idx, (name, script) in enumerate(tasks):
        if start_from in {name.lower(), script.lower(), name.split(":")[0].lower()}:
            return tasks[idx:]

    print(f"\n [CRITICAL ERROR] Unknown start stage: {start_from}")
    print(" Available stages:")
    for name, script in tasks:
        print(f"   - {name} | {script}")
    sys.exit(1)


def run_module_streaming(name, script_name):
    """Executes a script and streams unbuffered output for observability."""
    script_path = os.path.join(EXPERIMENT_DIR, script_name)

    print("\n" + "=" * 70)
    print(f" EXECUTING: {name}")
    print(f"SOURCE FILE: {script_name}")
    print("=" * 70 + "\n")

    if not os.path.exists(script_path):
        print(f" [CRITICAL ERROR] Script file not found: {script_path}")
        return False

    start_time = time.time()

    try:
        # sys.executable keeps everything in your current (venv)
        # '-u' forces unbuffered logs for real-time observability
        process = subprocess.Popen(
            [sys.executable, "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Stream lines to terminal as they are produced
        for line in process.stdout:
            print(f"  {line.strip()}")
            sys.stdout.flush()

        process.wait()

        if process.returncode == 0:
            elapsed = (time.time() - start_time) / 60
            print(f"\n [SUCCESS] {name} finalized in {elapsed:.2f} minutes.")
            return True
        else:
            print(f"\n [FAILED] {name} exited with error code: {process.returncode}")
            return False

    except Exception as e:
        print(f"[WARNING] [ORCHESTRATOR ERROR] Unexpected failure: {e}")
        return False


def main(start_from=None):
    print("\n" + "X" * 80)
    print("      PHD RESEARCH: R-PIPELINE REFERENCE ORCHESTRATOR")
    print("      STATUS: FROZEN CODEBASE | PHASE: REFERENCE ONTOLOGY BUILD")
    print("X" * 80)

    overall_start = time.time()

    selected_tasks = get_task_subset(R_PIPELINE_TASKS, start_from)

    if start_from:
        print(f"      RESTART MODE: STARTING FROM {start_from}")

    for name, script in selected_tasks:
        success = run_module_streaming(name, script)
        if not success:
            print(f"\n [PIPELINE TERMINATED] Failure in {name}. Reference integrity risk.")
            sys.exit(1)

    # Verify all final artefacts exist
    missing = [a for a in FINAL_ASSETS if not os.path.exists(a)]
    if missing:
        print(f"\n [PIPELINE TERMINATED] Final artefacts missing:")
        for a in missing:
            print(f"   - {a}")
        sys.exit(1)

    total_time = (time.time() - overall_start) / 60
    print("\n" + "#" * 40)
    print(f"# R-PIPELINE COMPLETE")
    print(f"# TOTAL EXECUTION TIME: {total_time:.2f} minutes")
    print(f"# FINAL ARTEFACTS:")
    for a in FINAL_ASSETS:
        print(f"#   - {a}")
    print("#" * 40)


if __name__ == "__main__":
    start_from = sys.argv[1] if len(sys.argv) > 1 else None
    main(start_from)
