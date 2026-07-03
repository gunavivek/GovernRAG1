import json
import os
import re
import pandas as pd
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import string
import numpy as np

# --- Configuration ---
# INPUTS:
E20_INPUT_PATH = "eval/E2_0_path_variables.jsonl"    # Causal Variables (Graph Usage Counts)
E1_INPUT_PATH = "eval/E1_2_type_aware_accuracy.jsonl" # Source for Gold Answer, etc.
# NOTE: This path is a placeholder. In a real system, you would load the full 
# RAGBench data for the eligible subset/split (e.g., cuads/test) here.
RAGBENCH_METRICS_PATH = "data/RAGBench_Metrics_Source.jsonl" 

# OUTPUT: The final dataset ready for correlation (Input for E2.2 Baseline)
E2_OUTPUT_PATH = "eval/E2_1_correlation_analysis.jsonl" 

# --- Thresholds ---
GROUNDEDNESS_THRESHOLD = 0.90 # Score > 0.90 indicates high grounding

# List of the 8 high-value RAGBench float metrics needed for correlation
RAGBENCH_FLOAT_METRICS = [
    "trulens_groundedness", "ragas_faithfulness", "gpt3_adherence",
    "trulens_context_relevance", "gpt3_context_relevance",
    "utilization_score", "gpt35_utilization"
]

# --- 1. Utility Functions ---

def normalize_text(s: str) -> str:
    """Standard normalization: lowercases, removes punctuation/whitespace."""
    if not s: return ""
    s = s.lower()
    s = ''.join(ch for ch in s if ch not in string.punctuation)
    return ' '.join(s.split())

def load_jsonl_to_df(path: str) -> pd.DataFrame:
    """Helper to load JSONL files into a Pandas DataFrame."""
    if not os.path.exists(path):
        print(f"Warning: Input file not found at {path}.")
        return pd.DataFrame()
    return pd.read_json(path, lines=True)

# --- 2. Flag Calculation Functions ---

def check_chunk_contains_gold(gold_answer: str, documents: List[str]) -> int:
    """
    Calculates the chunk recall flag: Did the gold answer text appear in the retrieved context?
    """
    if not documents or not gold_answer:
        return 0
    
    gold_normalized = normalize_text(gold_answer)
    
    # Check if the normalized gold answer text is a substring of any retrieved document/chunk
    for doc_text in documents:
        doc_normalized = normalize_text(doc_text)
        if gold_normalized and gold_normalized in doc_normalized:
            return 1 # Success
            
    return 0

def check_high_groundedness(score: Optional[float]) -> int:
    """
    Generates a success flag based on the trulens_groundedness metric.
    """
    if score is None or pd.isna(score):
        return 0
    return 1 if score >= GROUNDEDNESS_THRESHOLD else 0


# --- 3. Main Runner ---

def run_e2_1_correlation(e20_path: str, e1_path: str, ragbench_path: str, output_path: str):
    """
    Loads Causal Variables (E2.0), Effect Variables (RAGBench Metrics), and Gold Truth (E1),
    merges them, calculates success flags, and prepares the final correlation dataset.
    """
    print("--- Starting E2.1 Correlation Analysis ---")

    # 1. Load Data Sources
    df_e20 = load_jsonl_to_df(e20_path).set_index('id') # Causal Variables (Graph Usage)
    df_e1 = load_jsonl_to_df(e1_path).set_index('id')[['response']] # Gold Answer (Needed for chunk check)

    # SIMULATION: Load RAGBench data (Effect Variables + Traceability)
    # In a real pipeline, this would load the filtered, validated RAGBench parquet file.
    try:
        # Load the core fields (including the context text)
        df_rb = load_jsonl_to_df(ragbench_path).set_index('id')[RAGBENCH_FLOAT_METRICS + ['documents', 'all_relevant_sentence_keys']]
    except Exception:
        print(f"ERROR: Could not load RAGBench data from {ragbench_path}. Creating dummy DataFrame.")
        # Create a dummy DataFrame with NaN values to allow the pipeline to continue
        dummy_data = {col: np.nan for col in RAGBENCH_FLOAT_METRICS}
        dummy_data['documents'] = [[]]
        dummy_data['all_relevant_sentence_keys'] = [[]]
        df_rb = pd.DataFrame(dummy_data, index=df_e20.index)

    # 2. Merge DataFrames
    # We use inner join to ensure only records that completed E2.0 and have RAGBench metrics are analyzed
    df_merged = df_e20.join([df_e1, df_rb], how='inner').reset_index()
    df_merged = df_merged.rename(columns={'index': 'id'})
    
    if df_merged.empty:
        print("ERROR: Merged DataFrame is empty. Check inputs and IDs.")
        return

    print(f"Analyzing {len(df_merged)} records for correlation.")

    # 3. Calculate Success/Recall Flags (The Output Metrics)

    # A. Groundedness Success Flag (E2.1 Flag 1)
    df_merged['high_groundedness_flag'] = df_merged['trulens_groundedness'].apply(check_high_groundedness)

    # B. Chunk Recall Flag (E2.1 Flag 2)
    # This requires zipping the gold answer text and the retrieved document text
    df_merged['chunk_contains_gold'] = df_merged.apply(
        lambda row: check_chunk_contains_gold(
            row['response'], 
            row['documents']
        ), axis=1
    )

    # 4. Save Final Correlation Dataset
    # Drop verbose columns (like full document text) before saving
    cols_to_drop = ['response', 'documents']
    df_final = df_merged.drop(columns=[col for col in cols_to_drop if col in df_merged.columns])
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_json(output_path, orient='records', lines=True)

    print(f"E2.1 Correlation Analysis Complete. Results saved to {output_path}")

# --- Execution Example ---
if __name__ == "__main__":
    
    # 1. Setup Dummy Files
    os.makedirs('output', exist_ok=True)
    os.makedirs('eval', exist_ok=True)

    # Dummy E2.0 Path Variables (Causal Vars)
    e20_dummy = [
        {"id": "A001", "used_adaptive_concepts": 3, "num_communities_used": 1, "seeds_aligned_to_q3_concept": 1},
        {"id": "A002", "used_adaptive_concepts": 0, "num_communities_used": 3, "seeds_aligned_to_q3_concept": 0},
        {"id": "A003", "used_adaptive_concepts": 5, "num_communities_used": 1, "seeds_aligned_to_q3_concept": 1},
    ]
    with open(E20_INPUT_PATH, 'w') as f:
        for rec in e20_dummy: f.write(json.dumps(rec) + '\n')

    # Dummy E1 Input (Gold Answer for Chunk Check)
    e1_dummy = [
        {"id": "A001", "response": "The name is Apollo.", "documents": ["The name is Apollo.", "other text"]},
        {"id": "A002", "response": "The answer is 15%.", "documents": ["This text contains 15%."]},
        {"id": "A003", "response": "The answer is 15%.", "documents": ["This text contains 15%."]},
    ]
    with open(E1_INPUT_PATH, 'w') as f:
        for rec in e1_dummy: f.write(json.dumps({"id": rec["id"], "response": rec["response"]}) + '\n')
    
    # Dummy RAGBench Metrics/Context (Effect Vars)
    rb_dummy = [
        {"id": "A001", "trulens_groundedness": 0.95, "trulens_context_relevance": 0.9, "documents": ["The name is Apollo, dubbed Apollo Architecture."], "all_relevant_sentence_keys": ["s1"]},
        {"id": "A002", "trulens_groundedness": 0.80, "trulens_context_relevance": 0.5, "documents": ["The target is 15.0%. Context is clean."], "all_relevant_sentence_keys": ["s2", "s3"]},
        {"id": "A003", "trulens_groundedness": 0.99, "trulens_context_relevance": 0.99, "documents": ["The target is 15.0%. Context is clean."], "all_relevant_sentence_keys": ["s2", "s3"]},
    ]
    # Simulate saving ALL the necessary fields, including the 8 high-value floats
    # Note: Using the documents field from RAGBench is more accurate for the chunk check
    rb_final_dummy = []
    for rec in rb_dummy:
        # Add placeholder floats for the other 6 high-value metrics
        rec.update({
            "ragas_faithfulness": 0.8, "gpt3_adherence": 0.9,
            "gpt3_context_relevance": 0.8, "utilization_score": 0.7, 
            "gpt35_utilization": 0.8,
        })
        rb_final_dummy.append(rec)

    with open(RAGBENCH_METRICS_PATH, 'w') as f:
        for rec in rb_final_dummy: f.write(json.dumps(rec) + '\n')


    # Run E2.1
    run_e2_1_correlation(E20_INPUT_PATH, E1_INPUT_PATH, RAGBENCH_METRICS_PATH, E2_OUTPUT_PATH)
    
    print("\n--- E2.1 Simulation Complete ---")
    print("Final output contains Causal Variables and Effect Variables merged together.")