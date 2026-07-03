import subprocess
import sys
import os
import time
import json
import shutil
import random

# --- Configuration & Paths ---
# CRITICAL: THIS VARIABLE MUST MATCH YOUR GOOGLE DRIVE SYNC LOCATION
# The project root is the folder *above* 'experiment' (i.e., 'conceptual_GraphRAG')
PROJECT_ROOT_PATH = r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG"

EXPERIMENT_DIR = os.path.join(PROJECT_ROOT_PATH, 'experiment')
DATA_DIR = os.path.join(PROJECT_ROOT_PATH, 'data')
OUTPUT_DIR = os.path.join(EXPERIMENT_DIR, 'output')
EVAL_DIR = os.path.join(EXPERIMENT_DIR, 'eval')

# --- Specific Input File for the R2 Orchestration (Updated to hotpotqa) ---
D2_SOURCE_PATH = os.path.join(DATA_DIR, 'D2_CLEAN_hotpotqa_test.jsonl')
# Required artifact path for Q1 and E1.1
D1_OUTPUT_PATH = os.path.join(DATA_DIR, 'D1_Test_file.jsonl')

# Define the sequence of pipeline stages (M, Q, E)
PIPELINE_STAGES = [
    # --- 1. M-Pipeline (Graph Indexing) ---
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

    # --- 2. Q-Pipeline (Signature Pre-Processing) ---
    {"name": "Q1_Domain_Router", "script": "Q1_domain_router.py", "pipeline": "Q"},
    {"name": "Q2_Intent_Detector", "script": "Q2_intent_detector.py", "pipeline": "Q"},
    {"name": "Q3_Signature_Extractor", "script": "Q3_Signature_Extractor.py", "pipeline": "Q"},

    # --- 3. Q-Pipeline (Retrieval & Answer Generation - Convergence) ---
    {"name": "Q4_Cluster_Router", "script": "Q4_cluster_router.py", "pipeline": "Q"},
    {"name": "Q5_Retrieval_Planner", "script": "Q5_retrieval_planner.py", "pipeline": "Q"},
    {"name": "Q6_Answer_Generator", "script": "Q6_answer_generator.py", "pipeline": "Q"},

    # --- 4. E-Pipeline (Evaluation) ---
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

def setup_data_stage():
    """
    Manual override of D-Pipeline: Extracts one record from the D2_CLEAN_hotpotqa_test.jsonl
    located in the Google Drive data folder.
    """
    print("\n" + "="*80)
    print(f"[D_SETUP] STARTING D2 ARTIFACT INTEGRATION (Source: hotpotqa)...")
    print(f"Source Path: {D2_SOURCE_PATH}")
    
    if not os.path.exists(D2_SOURCE_PATH):
        raise FileNotFoundError(f"CRITICAL ERROR: D2 source file not found at {D2_SOURCE_PATH}. Check your Google Drive sync and the 'PROJECT_ROOT_PATH' variable.")

    try:
        with open(D2_SOURCE_PATH, 'r', encoding='utf-8') as f_in:
            first_line = f_in.readline().strip()

        if not first_line:
            raise ValueError(f"D2 source file {D2_SOURCE_PATH} is empty.")
            
        record = json.loads(first_line)
        
        # We need to replicate the D1 output format (subset of fields)
        d1_input_data = {
            "id": record.get('id', 'N/A'),
            "question": record.get('question', 'N/A'),
            "documents": record.get('documents', []),
            "response": record.get('response', 'N/A'),
            "dataset_name": record.get('dataset_name', 'hotpotqa_test')
        }

        # 1. Write the single question record to the D1 required path
        with open(D1_OUTPUT_PATH, 'w', encoding='utf-8') as f_out:
            f_out.write(json.dumps(d1_input_data) + '\n')
            
        # 2. Write the corpus text required by M1_chunking.py 
        full_document_text = "\n\n".join(d1_input_data['documents'])
        corpus_path = os.path.join(DATA_DIR, 'ragbench_documents.txt')
        with open(corpus_path, 'w', encoding='utf-8') as f_corpus:
             f_corpus.write(full_document_text)

        print(f"[D_SETUP] SUCCESS. Record ID: {d1_input_data['id']}. Corpus generated.")

    except Exception as e:
        print(f"[D_SETUP] FATAL ERROR during data preparation: {e}")
        sys.exit(1)


def run_pipeline_stage(stage: dict):
    """Executes a single pipeline stage script using a subprocess."""
    # NOTE: The scripts are executed from the Project Root, not the experiment folder
    local_script_path = os.path.join(EXPERIMENT_DIR, stage['script'].replace('experiment.zip/', ''))

    print(f"\n{'='*80}")
    print(f"[{stage['pipeline']} - {stage['name']}] STARTING EXECUTION...")
    print(f"Executing: {sys.executable} {local_script_path}")
    print(f"CWD: {PROJECT_ROOT_PATH}")
    print(f"{'='*80}")

    try:
        result = subprocess.run(
            [sys.executable, local_script_path],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT_PATH, 
            check=True
        )
        print(f"[{stage['name']}] Standard Output (Snippet):\n{result.stdout[-500:]}")
        print(f"[{stage['name']}] SUCCESS.")

    except subprocess.CalledProcessError as e:
        print(f"\n{'!'*80}")
        print(f"[{stage['name']}] FATAL ERROR: Script returned non-zero exit code.")
        print(f"Standard Error:\n{e.stderr}")
        print(f"{'!'*80}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[{stage['name']}] CRITICAL ERROR: Script file not found at {local_script_path}.")
        sys.exit(1)


def run_full_pipeline():
    """The R2 master orchestrator function."""
    start_time = time.time()
    
    # Ensure all required directories exist (relative to Project Root)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT_PATH, 'output'), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT_PATH, 'eval'), exist_ok=True)
    
    print("\n\n" + "#" * 90)
    print("### R2 MASTER PIPELINE: STARTING HOTPOTQA ARTIFACT INTEGRATION FLOW ###")
    print(f"### Project Root: {PROJECT_ROOT_PATH}")
    print("#" * 90 + "\n")

    # --- 1. Custom Setup Stage (D-Pipeline Replacement) ---
    setup_data_stage()

    # --- 2. Sequential M, Q, E Execution ---
    for stage in PIPELINE_STAGES:
        run_pipeline_stage(stage)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print("\n\n" + "#" * 90)
    print("### R2 MASTER PIPELINE: EXECUTION COMPLETE ###")
    print(f"Total Stages Executed: {len(PIPELINE_STAGES) + 1} (Setup + M/Q/E)")
    print(f"Total Wall Time: {elapsed_time:.2f} seconds")
    print(f"Artifacts located relative to: {PROJECT_ROOT_PATH}")
    print("#" * 90)


if __name__ == "__main__":
    run_full_pipeline()