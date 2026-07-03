import pandas as pd
import json
import os
from typing import Dict, Any, List

# --- Configuration ---
DQA_INPUT_PATH = "eval/E0_ragbench_dqa_detail.csv"
FINAL_OUTPUT_PATH = "eval/E0_1_final_dataset_configs.json"

# --- Thresholds for Dataset Selection (Applying strict filtering) ---

# All thresholds are based on the population percentage (e.g., 'response_Populated_Pct')
THRESHOLDS = {
    # 1. HARD REQUIREMENTS (Must be near-perfect)
    'response_Populated_Pct': 98.0,  # Gold Answer (E1 base)
    'documents_Populated_Pct': 98.0, # Context Chunks (M-Pipeline base)
    
    # 2. HIGH-VALUE E2 VALIDATION REQUIREMENTS (All 8 high-value fields must be highly populated)
    'trulens_groundedness_Populated_Pct': 90.0,
    'ragas_faithfulness_Populated_Pct': 90.0,
    'gpt3_adherence_Populated_Pct': 90.0,
    'trulens_context_relevance_Populated_Pct': 90.0,
    'gpt3_context_relevance_Populated_Pct': 90.0,
    'utilization_score_Populated_Pct': 90.0,
    'gpt35_utilization_Populated_Pct': 90.0,
    'all_relevant_sentence_keys_Populated_Pct': 90.0, # Traceability Gold
}

# --- Data Selection Logic ---

def select_datasets_for_pipeline(input_path: str, thresholds: Dict[str, float]) -> List[Dict[str, str]]:
    """
    Consumes the DQA CSV and filters dataset configurations based on strict population thresholds 
    for all critical E-pipeline fields.
    """
    print(f"Loading DQA results from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print("Error: DQA input file not found. Please ensure E0_dqa.py ran successfully and the path is correct.")
        return []
    except pd.errors.EmptyDataError:
        print("Error: DQA input file is empty. Cannot perform filtering.")
        return []
    
    initial_count = len(df)
    
    # --- Step 1: Apply Filters ---
    
    # Ensure all required percentage columns exist before filtering
    required_cols = list(thresholds.keys())
    if not all(col in df.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in df.columns]
        print(f"Error: Missing critical columns in the DQA file: {missing_cols}")
        print("The E0 audit likely did not find these columns in any RAGBench subset.")
        return []

    print(f"Starting with {initial_count} configurations. Applying strict filters...")
    
    df_filtered = df.copy()
    notes = []
    
    # Apply filtering sequentially for full transparency
    for col, min_pct in thresholds.items():
        count_before = len(df_filtered)
        
        # Apply the filter: keep rows where the column's percentage is >= the minimum threshold
        df_filtered = df_filtered[df_filtered[col] >= min_pct]
        
        count_after = len(df_filtered)
        
        notes.append(f"  - Filtered by '{col}' ({min_pct}% minimum): Retained {count_after} configurations.")
        if count_after == 0:
             # Stop processing if no records remain
             print("Filter yields 0 results. Stopping.")
             break
    
    # --- Step 2: Format Output ---
    
    final_configs = []
    
    if len(df_filtered) > 0:
        for index, row in df_filtered.iterrows():
            # Example of splitting the full name: 'galileo-ai/ragbench:cuad/train'
            parts = row['Dataset/Split'].split(':')[-1].split('/')
            subset_name = parts[0]
            split_name = parts[1]
            
            final_configs.append({
                "subset": subset_name,
                "split": split_name,
                "total_records": int(row['Total Records'])
            })
            
    print("\n--- Filtering Summary ---")
    print("\n".join(notes))
    print(f"\nFinal Recommended Configurations: {len(final_configs)}.")
    
    return final_configs

# --- Execution ---
if __name__ == "__main__":
    
    # 1. Run the selection logic
    recommended_configs = select_datasets_for_pipeline(DQA_INPUT_PATH, THRESHOLDS)
    
    # 2. Save the final JSON configuration file
    if recommended_configs:
        os.makedirs(os.path.dirname(FINAL_OUTPUT_PATH), exist_ok=True)
        with open(FINAL_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(recommended_configs, f, indent=4)
        
        print("\n" + "="*50)
        print("[SUCCESS] Pipeline Configuration Selection Complete")
        print(f"Final M/Q/E pipeline config list saved to: {FINAL_OUTPUT_PATH}")
        print("This file contains the subset/split names that meet all 10 validation thresholds.")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("[WARNING] WARNING: No datasets met the minimum evaluation quality thresholds.")
        print("Consider lowering the E2 validation thresholds (e.g., 90% down to 80%) and re-running E0.1.")
        print("="*50)