# --------------------------------------------------------------------------
# MODULE 0: M0_Main_Extraction_Orchestrator.py
# ARCHITECTURE: Streaming Executive Process Controller
# DISSERTATION PHASE: Empirical Extraction (Frozen Codebase)
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
FINAL_ASSET = os.path.join(PROJECT_ROOT, "output", "M5_Embedded_Graph.graphml")

# --- 1. THE TASK MANIFEST (Frozen & Sequenced) ---
M_PIPELINE_TASKS = [
    ("M1: Governed Chunking", "M1_Gov_Chunking_V5.py"),
    ("M1.5: Data Lineage Audit", "M1_5_Gov_Chunking_Audit.py"),
    ("M2: Async Triple Extraction", "M2_Gov_Extraction_v4_Async.py"),
    ("M3: Graph Construction", "M3_Gov_Graph_Construction_V4.py"),
    ("M3.3: Concept Augmentation", "M3.3_Gov_Concept_Augmentation_V3.py"),
    ("M4: Ontological Alignment", "M4_Gov_Concept_Alignment_V3.py"),
    ("M5: 768-Dim Vectorization", "M5_Gov_Graph_Embedding_V4.py")
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
    
    print("\n" + "="*70)
    print(f" EXECUTING: {name}")
    print(f"SOURCE FILE: {script_name}")
    print("="*70 + "\n")
    
    if not os.path.exists(script_path):
        print(f" [CRITICAL ERROR] Script file not found: {script_path}")
        return False

    start_time = time.time()
    
    try:
        # sys.executable keeps everything in your current (venv)
        # '-u' forces unbuffered logs so M2 progress is real-time
        process = subprocess.Popen(
            [sys.executable, "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
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
    print("\n" + "X"*80)
    print("      PHD RESEARCH: M-PIPELINE MAIN EXTRACTION ORCHESTRATOR")
    print("      STATUS: FROZEN CODEBASE | PHASE: EMPIRICAL EXTRACTION")
    print("X"*80)

    overall_start = time.time()
    
    selected_tasks = get_task_subset(M_PIPELINE_TASKS, start_from)

    if start_from:
        print(f"      RESTART MODE: STARTING FROM {start_from}")

    for name, script in selected_tasks:
        success = run_module_streaming(name, script)
        if not success:
            print(f"\n [PIPELINE TERMINATED] Failure in {name}. Data integrity risk.")
            sys.exit(1)

    if not os.path.exists(FINAL_ASSET):
        print(f"\n [PIPELINE TERMINATED] Final artifact missing: {FINAL_ASSET}")
        sys.exit(1)

    total_time = (time.time() - overall_start) / 60
    print("\n" + "#"*40)
    print(f"# M-PIPELINE COMPLETE")
    print(f"# TOTAL EXECUTION TIME: {total_time:.2f} minutes")
    print(f"# FINAL KNOWLEDGE ASSET: {FINAL_ASSET}")
    print("#"*40)

if __name__ == "__main__":
    start_from = sys.argv[1] if len(sys.argv) > 1 else None
    main(start_from)