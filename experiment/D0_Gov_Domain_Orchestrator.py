import os
import sys
import subprocess
import time
import json
from datetime import datetime, timezone

# --- Environment Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

class GovDomainOrchestrator:
    """
    D0: Master Orchestrator for the Frozen D-Pipeline (Paper Evaluation Version)

    Purpose:
    Executes the evaluated D-pipeline only:
        D2 -> D3 -> D4 -> D5

    Notes:
    - D1 is treated as a separate initialization step that prepares the dataset-level baseline.
    - D45 is excluded from the frozen paper path because it depends on M2 outputs and
      functions as a downstream feedback/refinement module rather than a core D-pipeline stage.
    """
    def __init__(self):
        # --- EXACT FILENAME CONFIGURATION ---
        self.pipeline = [
            {"step": "D2",  "name": "Dynamic Statistical Gatekeeper", "file": "D2_Statistical_Domain_Ontological_Anchor_V3.py"}, 
            {"step": "D3",  "name": "Poly-Ontological Discovery",     "file": "D3_Multi_Domain_Discover_Score_V3.py"},
            {"step": "D4",  "name": "Requirement Specifier",          "file": "D4_Requirement_Specifier_V22.py"},
            {"step": "D5",  "name": "Extraction Manifest Orchestrator","file": "D5_Orchestrator_V22.py"}
        ]

    def _run_module(self, step_info: dict) -> bool:
        script_path = os.path.join(current_dir, step_info["file"])
        
        if not os.path.exists(script_path):
            print(f"[CRITICAL ERROR] Script missing or filename incorrect: {script_path}")
            return False

        print(f"\n[{step_info['step']}] Executing: {step_info['name']}...")
        try:
            # Subprocess guarantees absolute memory isolation. 
            # cwd=current_dir locks the execution context to the experiment folder.
            subprocess.run([sys.executable, script_path], check=True, cwd=current_dir)
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n[PIPELINE HALTED] {step_info['step']} failed with exit code {e.returncode}.")
            return False

    def run(self):
        print("\n" + "="*80)
        print("   PHD RESEARCH: AUTONOMOUS D-PIPELINE GOVERNANCE ORCHESTRATOR (D0) - FROZEN D-PIPELINE ORCHESTRATOR (PAPER EVALUATION VERSION)")
        print("="*80)
        print("   Prerequisite: Run D1 separately if D1_Global_Mapping.json needs refresh.")
        print("=" * 80)
        
        start_time = time.time()

        for module in self.pipeline:
            success = self._run_module(module)
            
            if not success:
                print("\n" + "!"*80)
                print(f"ORCHESTRATION FAILED. Fix errors in {module['step']} before continuing.")
                print("!"*80 + "\n")
                sys.exit(1)
                
            # Brief 1-second small pause to reduce file I/O race conditions across subprocess steps
            time.sleep(1) 

        end_time = time.time()
        print("\n" + "="*80)
        print(f"   D-PIPELINE COMPLETE. Total Execution Time: {(end_time - start_time):.2f} seconds.")
        print(f"   Golden Thread Manifest ready for M-Pipeline at: output/D5_Extraction_Manifest.jsonl")
        print("="*80 + "\n")

if __name__ == "__main__":
    orchestrator = GovDomainOrchestrator()
    orchestrator.run()