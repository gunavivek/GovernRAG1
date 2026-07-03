import subprocess
import sys
import os
import time
import json
import random
import argparse

# --- Configuration & Paths ---
# CRITICAL: THIS VARIABLE MUST MATCH YOUR GOOGLE DRIVE SYNC LOCATION
PROJECT_ROOT_PATH = r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG"

EXPERIMENT_DIR = os.path.join(PROJECT_ROOT_PATH, 'experiment')
DATA_DIR = os.path.join(PROJECT_ROOT_PATH, 'data')

# --- Resiliency Configuration ---
MAX_RETRIES = 3
INITIAL_DELAY_SECONDS = 5
LLM_DEPENDENT_PIPELINES = ["M2", "M3.3", "M4", "M5", "Q2", "Q3", "Q6"]

# --- Specific Input File for the R3 Orchestration (hotpotqa) ---
D2_SOURCE_PATH = os.path.join(DATA_DIR, 'D2_CLEAN_hotpotqa_test.jsonl')
D1_OUTPUT_PATH = os.path.join(DATA_DIR, 'D1_Test_file.jsonl')

# Define the sequence of pipeline stages (M, Q, E)
PIPELINE_STAGES = [
    # --- 1. M-Pipeline (Graph Indexing) ---
    # NOTE: M1 is listed here for completeness, but typically skipped via command line argument.
    {"name": "M1_Chunking", "script": "M1_chunking.py", "pipeline": "M", "artifact": "M1_Text_Chunks.csv"},
    {"name": "M2_Extraction", "script": "M2_extraction.py", "pipeline": "M2", "artifact": "M2_Extracted_Triples.json"},
    {"name": "M3_Graph_Construction", "script": "M3_graph_construction.py", "pipeline": "M", "artifact": "M3_Knowledge_Graph.gml"},
    
    # --- Conditional Skip Stage for M3.5 (Skip if GML file exists) ---
    {"name": "M3.5_Ontology_Construction", "script": "M3.5_ontology_construction.py", "pipeline": "M", "artifact": "M3_5_Reference_Ontology.gml", "skippable": True},
    
    {"name": "M3.3_Concept_Augmentation", "script": "M3.3_concept_augmentation.py", "pipeline": "M3.3", "artifact": "M3_3_Augmented_Graph.gml"},
    {"name": "M4_Concept_Alignment", "script": "M4_concept_alignment.py", "pipeline": "M4", "artifact": "M4_Hybrid_Graph.gml"},
    {"name": "M5_Contextual_Embedding", "script": "M5_contextual_embedding.py", "pipeline": "M5", "artifact": "M5_Embedded_Graph.gml"},
    {"name": "M6_Graph_Clustering", "script": "M6_graph_clustering.py", "pipeline": "M", "artifact": "M6_Clustered_Graph.gml"},
    
    # Optional M-Pipeline Checks
    {"name": "M5.5_Embedding_Validation", "script": "M5.5_embedding_validation.py", "pipeline": "M_CHECK", "artifact": "M5_5_Full_Trace_Matrix.csv"},
    {"name": "M3.5_Visualization", "script": "M3.5_visualize.py", "pipeline": "M_CHECK", "artifact": "M3_5_Reference_Ontology_Viz.png"},

    # --- 2. Q-Pipeline (Signature Pre-Processing) ---
    {"name": "Q1_Domain_Router", "script": "Q1_domain_router.py", "pipeline": "Q", "artifact": "Q1_domain_router.jsonl"},
    {"name": "Q2_Intent_Detector", "script": "Q2_intent_detector.py", "pipeline": "Q2", "artifact": "Q2_intents.jsonl"},
    {"name": "Q3_Signature_Extractor", "script": "Q3_Signature_Extractor.py", "pipeline": "Q3", "artifact": "Q3_signatures.jsonl"},

    # --- 3. Q-Pipeline (Retrieval & Answer Generation - Convergence) ---
    {"name": "Q4_Cluster_Router", "script": "Q4_cluster_router.py", "pipeline": "Q", "artifact": "Q4_cluster_routing.jsonl"},
    {"name": "Q5_Retrieval_Planner", "script": "Q5_retrieval_planner.py", "pipeline": "Q", "artifact": "Q5_retrieval_plan.jsonl"},
    {"name": "Q6_Answer_Generator", "script": "Q6_answer_generator.py", "pipeline": "Q6", "artifact": "Q6_answers.jsonl"},

    # --- 4. E-Pipeline (Evaluation) ---
    {"name": "E1.1_Answer_Alignment", "script": "E1.1_answer_alignment.py", "pipeline": "E1", "artifact": "E1_1_answer_alignment.jsonl"},
    {"name": "E1.2_Type_Aware_Accuracy", "script": "E1.2_type_aware_accuracy.py", "pipeline": "E1", "artifact": "E1_2_type_aware_accuracy.jsonl"},
    {"name": "E2.0_Path_Variable_Generation", "script": "E2.0_path_variable_generation.py", "pipeline": "E2", "artifact": "E2_0_path_variables.jsonl"},
    {"name": "E2.1_Correlation_Analysis", "script": "E2.1_correlation_analysis.py", "pipeline": "E2", "artifact": "E2_1_correlation_analysis.jsonl"},
    {"name": "E1.3_Summary_Metrics", "script": "E1.3_summary_metrics.py", "pipeline": "E_FINAL", "artifact": "E1_3_summary.json"},
    {"name": "E2.2_Baseline_Comparison", "script": "E2.2_baseline_comparison.py", "pipeline": "E_FINAL", "artifact": "E2_2_comparison_summary.json"},
]

def setup_data_stage():
    """
    MODIFIED: Extracts ONLY the first document from the documents list for M1 input.
    """
    print("\n" + "="*80)
    print(f"[D_SETUP] STARTING D2 ARTIFACT INTEGRATION (Source: hotpotqa)...")
    
    if not os.path.exists(D2_SOURCE_PATH):
        raise FileNotFoundError(f"CRITICAL ERROR: D2 source file not found at {D2_SOURCE_PATH}.")

    try:
        with open(D2_SOURCE_PATH, 'r', encoding='utf-8') as f_in:
            first_line = f_in.readline().strip()

        if not first_line:
            raise ValueError(f"D2 source file {D2_SOURCE_PATH} is empty.")
            
        record = json.loads(first_line)
        
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
        document_list = d1_input_data.get('documents', [])
        
        # --- CRITICAL MODIFICATION: Single Document Logic ---
        if document_list and len(document_list) > 0:
            full_document_text = document_list[0]
            print("[D_SETUP] Document source limited to FIRST DOCUMENT only.")
        else:
            full_document_text = ""
            print("[D_SETUP] WARNING: Document list is empty. M1 will process empty text.")
        # --- END MODIFICATION ---

        corpus_path = os.path.join(DATA_DIR, 'ragbench_documents.txt')
        with open(corpus_path, 'w', encoding='utf-8') as f_corpus:
             f_corpus.write(full_document_text)

        print(f"[D_SETUP] SUCCESS. Record ID: {d1_input_data['id']}. Single document corpus generated.")

    except Exception as e:
        print(f"[D_SETUP] FATAL ERROR during data preparation: {e}")
        sys.exit(1)

def calculate_delay(retry_count: int) -> float:
    """Calculates exponential backoff delay with jitter."""
    # Delay = initial * (2^retry) + jitter
    base_delay = INITIAL_DELAY_SECONDS * (2 ** retry_count)
    jitter = random.uniform(0, 1.0)
    return base_delay + jitter

def run_pipeline_stage_with_retry(stage: dict):
    """Executes a pipeline stage with exponential backoff for LLM-dependent stages."""
    
    # --- Conditional Skip Logic (M3.5) ---
    if stage.get('skippable'):
        output_file_path = os.path.join(PROJECT_ROOT_PATH, 'output', stage['artifact'])
        if os.path.exists(output_file_path):
            print(f"\n[SKIP] Stage {stage['name']} skipped. Output artifact {stage['artifact']} already exists.")
            return

    is_llm_stage = stage['pipeline'] in LLM_DEPENDENT_PIPELINES
    max_attempts = MAX_RETRIES if is_llm_stage else 1
    
    local_script_name = stage['script']
    local_script_path = os.path.join(EXPERIMENT_DIR, local_script_name)

    for attempt in range(max_attempts):
        print(f"\n{'='*80}")
        if is_llm_stage:
            print(f"[{stage['pipeline']} - {stage['name']}] STARTING EXECUTION (Attempt {attempt + 1}/{max_attempts})...")
        else:
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
            print(f"[{stage['name']}] SUCCESS (After {attempt + 1} attempts).")
            print(f"[{stage['name']}] Standard Output (Snippet):\n{result.stdout[-500:]}")
            return # Success, exit the retry loop

        except subprocess.CalledProcessError as e:
            # This catches non-zero exit codes
            print(f"\n{'!'*80}")
            print(f"[{stage['name']}] ERROR: Script returned non-zero exit code.")
            
            if is_llm_stage:
                print("[TRANSIENT ERROR] Assuming API/Rate Limit failure for retry.")
            else:
                 print("[CRITICAL FAILURE] Aborting pipeline due to unexpected non-LLM error.")
                 sys.exit(1)

            if not is_llm_stage or attempt == max_attempts - 1:
                print(f"[CRITICAL FAILURE] Aborting pipeline for stage: {stage['name']}.")
                sys.exit(1)
            
            # Exponential Backoff Logic
            delay = calculate_delay(attempt)
            print(f"[RETRY] Waiting {delay:.2f} seconds before retry...")
            time.sleep(delay)
            # Continue loop for retry

        except FileNotFoundError:
            print(f"\n[CRITICAL ERROR] Script file not found at {local_script_path}.")
            sys.exit(1)

def run_full_pipeline(start_stage_name=None):
    """The R3 master orchestrator function."""
    start_time = time.time()
    
    # Ensure all required directories exist (relative to Project Root)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT_PATH, 'output'), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT_PATH, 'eval'), exist_ok=True)
    
    print("\n\n" + "#" * 90)
    print("### R3 MASTER PIPELINE: STARTING FINAL RESILIENT EXECUTION ###")
    print(f"### Project Root: {PROJECT_ROOT_PATH}")
    print("#" * 90 + "\n")

    # --- 1. Custom Setup Stage (D-Pipeline Replacement) ---
    setup_data_stage()

    # --- 2. Sequential M, Q, E Execution ---
    start_index = 0
    if start_stage_name:
        try:
            stage_names = [stage['name'] for stage in PIPELINE_STAGES]
            start_index = stage_names.index(start_stage_name)
            print(f"\n[ORCHESTRATOR] STARTING FROM SPECIFIED STAGE: {start_stage_name}")
        except ValueError:
            print(f"\n[CRITICAL ERROR] Invalid start stage name '{start_stage_name}'. Starting from the beginning.")

    for stage in PIPELINE_STAGES[start_index:]:
        run_pipeline_stage_with_retry(stage)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print("\n\n" + "#" * 90)
    print("### R3 MASTER PIPELINE: EXECUTION COMPLETE ###")
    print(f"Total Stages Executed: {len(PIPELINE_STAGES[start_index:]) + 1} (Setup + M/Q/E)")
    print(f"Total Wall Time: {elapsed_time:.2f} seconds")
    print(f"Artifacts located relative to: {PROJECT_ROOT_PATH}")
    print("#" * 90)


if __name__ == "__main__":
    # Use argparse to safely handle command line arguments
    parser = argparse.ArgumentParser(description="Master Pipeline Orchestrator for RAG Prototype.")
    parser.add_argument('start_stage', nargs='?', default=None, help="Optional stage name to start execution from (e.g., M2_Extraction).")
    args = parser.parse_args()
    
    run_full_pipeline(args.start_stage)