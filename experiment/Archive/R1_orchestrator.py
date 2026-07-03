import subprocess
import sys
import os
import time

# --- Configuration ---
# The root path is relative to where this orchestrator script is executed.
# Assuming this script is in the same directory as all other .py files.
EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the sequence of pipeline stages
PIPELINE_STAGES = [
    # --- 1. D-Pipeline (Data Acquisition) ---
    {"name": "D1_Data_Feed", "script": "D1_Data_feed_from_HF.py", "pipeline": "D"},

    # --- 2. M-Pipeline (Graph Indexing) ---
    {"name": "M1_Chunking", "script": "M1_chunking.py", "pipeline": "M"},
    {"name": "M2_Extraction", "script": "M2_extraction.py", "pipeline": "M"},
    {"name": "M3_Graph_Construction", "script": "M3_graph_construction.py", "pipeline": "M"},
    {"name": "M3.5_Ontology_Construction", "script": "M3.5_ontology_construction.py", "pipeline": "M"},
    {"name": "M3.3_Concept_Augmentation", "script": "M3.3_concept_augmentation.py", "pipeline": "M"},
    {"name": "M4_Concept_Alignment", "script": "M4_concept_alignment.py", "pipeline": "M"},
    {"name": "M5_Contextual_Embedding", "script": "M5_contextual_embedding.py", "pipeline": "M"},
    {"name": "M6_Graph_Clustering", "script": "M6_graph_clustering.py", "pipeline": "M"},
    # Optional M-Pipeline Checks
    {"name": "M5.5_Embedding_Validation", "script": "M5.5_embedding_validation.py", "pipeline": "M_CHECK"},
    {"name": "M3.5_Visualization", "script": "M3.5_visualize.py", "pipeline": "M_CHECK"},

    # --- 3. Q-Pipeline (Signature Pre-Processing) ---
    {"name": "Q1_Domain_Router", "script": "Q1_domain_router.py", "pipeline": "Q"},
    {"name": "Q2_Intent_Detector", "script": "Q2_intent_detector.py", "pipeline": "Q"},
    {"name": "Q3_Signature_Extractor", "script": "Q3_Signature_Extractor.py", "pipeline": "Q"},

    # --- 4. Q-Pipeline (Retrieval & Answer Generation - Convergence) ---
    # Dependencies Q4, Q5 on M6 artifact
    {"name": "Q4_Cluster_Router", "script": "Q4_cluster_router.py", "pipeline": "Q"},
    {"name": "Q5_Retrieval_Planner", "script": "Q5_retrieval_planner.py", "pipeline": "Q"},
    {"name": "Q6_Answer_Generator", "script": "Q6_answer_generator.py", "pipeline": "Q"},

    # --- 5. E-Pipeline (Evaluation) ---
    # E1 Track (Answer Quality)
    {"name": "E1.1_Answer_Alignment", "script": "E1.1_answer_alignment.py", "pipeline": "E1"},
    {"name": "E1.2_Type_Aware_Accuracy", "script": "E1.2_type_aware_accuracy.py", "pipeline": "E1"},

    # E2 Track (Causal Analysis)
    {"name": "E2.0_Path_Variable_Generation", "script": "E2.0_path_variable_generation.py", "pipeline": "E2"},
    {"name": "E2.1_Correlation_Analysis", "script": "E2.1_correlation_analysis.py", "pipeline": "E2"},

    # Final Summaries
    {"name": "E1.3_Summary_Metrics", "script": "E1.3_summary_metrics.py", "pipeline": "E_FINAL"},
    {"name": "E2.2_Baseline_Comparison", "script": "E2.2_baseline_comparison.py", "pipeline": "E_FINAL"},
]

def run_pipeline_stage(stage: dict):
    """Executes a single pipeline stage script using a subprocess."""
    script_path = os.path.join(EXPERIMENT_DIR, stage['script'])
    
    print(f"\n{'='*80}")
    print(f"[{stage['pipeline']} - {stage['name']}] STARTING EXECUTION...")
    print(f"Executing: {sys.executable} {script_path}")
    print(f"{'='*80}")

    try:
        # Use sys.executable to ensure the correct Python environment is used
        # check=True raises an exception if the script returns a non-zero exit code
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=EXPERIMENT_DIR, # Set current working directory to experiment folder
            check=True
        )
        print(f"[{stage['name']}] Output:\n{result.stdout}")
        print(f"[{stage['name']}] SUCCESS.")

    except subprocess.CalledProcessError as e:
        print(f"\n{'!'*80}")
        print(f"[{stage['name']}] FATAL ERROR: Script returned non-zero exit code.")
        print(f"Standard Output:\n{e.stdout}")
        print(f"Standard Error:\n{e.stderr}")
        print(f"{'!'*80}")
        # Terminate the master pipeline on failure
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[{stage['name']}] CRITICAL ERROR: Script file not found at {script_path}.")
        sys.exit(1)


def run_full_pipeline():
    """The master orchestrator function."""
    start_time = time.time()
    
    # 1. Check for directory setup
    if not os.path.exists(os.path.join(EXPERIMENT_DIR, 'data')) or not os.path.exists(os.path.join(EXPERIMENT_DIR, 'output')):
        print("MASTER PIPELINE: Creating required 'data' and 'output' directories...")
        os.makedirs(os.path.join(EXPERIMENT_DIR, 'data'), exist_ok=True)
        os.makedirs(os.path.join(EXPERIMENT_DIR, 'output'), exist_ok=True)
        os.makedirs(os.path.join(EXPERIMENT_DIR, 'eval'), exist_ok=True)

    print("\n\n" + "#" * 90)
    print("### MASTER PIPELINE: STARTING END-TO-END RAG PROTOTYPE EXECUTION ###")
    print(f"### Execution Environment: {sys.executable}")
    print("#" * 90 + "\n")

    for stage in PIPELINE_STAGES:
        run_pipeline_stage(stage)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print("\n\n" + "#" * 90)
    print("### MASTER PIPELINE: EXECUTION COMPLETE ###")
    print(f"Total Stages Executed: {len(PIPELINE_STAGES)}")
    print(f"Total Wall Time: {elapsed_time:.2f} seconds")
    print(f"All artifacts saved relative to: {EXPERIMENT_DIR}")
    print("#" * 90)


if __name__ == "__main__":
    run_full_pipeline()