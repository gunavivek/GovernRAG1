import pandas as pd
import os
import json
import numpy as np
import time
from datasets import load_dataset
from typing import List, Dict, Any

# --- Configuration ---

# 1. Define the 12 complete subset names
SUBSET_NAMES = [
    "covidqa", 
    "cuad", 
    "delucionqa",
    "emanual", 
    "expertqa", 
    "finqa", 
    "hagrid", 
    "hotpotqa", 
    "msmarco",
    "pubmedqa",
    "tatqa",
    "techqa" 
] # Total of 12 unique subsets

# 2. Define the standard splits
SPLIT_NAMES = ["train", "test", "validation"]

# 3. Dynamic Generation (Creates 36 configurations efficiently)
DATASET_CONFIGS = [
    {"name": subset, "split": split}
    for subset in SUBSET_NAMES
    for split in SPLIT_NAMES
] # Total configurations: 12 * 3 = 36

# CRITICAL COLUMNS needed to validate M-Pipeline and Q-Pipeline
CRITICAL_COLUMNS = [
    "response",                      # Gold Answer (E1/E2.1 base)
    "documents",                     # Context Chunks (M-Pipeline Sanity check)
    "trulens_groundedness",          # Grounding (M-Pipeline Indexing Quality)
    "ragas_faithfulness",            # Faithfulness (M-Pipeline Indexing Quality)
    "trulens_context_relevance",     # Context Quality (Q-Pipeline Routing)
    "all_relevant_sentence_keys",    # Recall/Traceability (M-Pipeline Chunking)
    "utilization_score",             # Utilization (Q-Pipeline Retrieval Cleanliness)
]

# --- DQA Logic ---

def run_dqa_audit(configs: List[Dict[str, str]], columns: List[str]) -> pd.DataFrame:
    """
    Loads datasets in streaming mode, audits critical columns for population, 
    and returns a summary DataFrame.
    """
    audit_results = []
    
    print("Starting E0: RAGBench Data Quality Audit...")
    
    for config in configs:
        dataset_name = config['name']
        split_name = config['split']
        full_name = f"galileo-ai/ragbench:{dataset_name}/{split_name}"
        
        print(f"\nProcessing: {full_name}")
        
        total_records = 0
        populated_counts = {}
        
        try:
            # 1. Load Data using streaming=True (HIGHLY memory-efficient)
            ds_stream = load_dataset("galileo-ai/ragbench", dataset_name, split=split_name, streaming=True)
            
            # 2. Iterate through the dataset record-by-record
            for i, record in enumerate(ds_stream):
                total_records += 1
                
                # --- Dynamic Column Discovery ---
                # On the first record, identify ALL columns present in this split
                if i == 0:
                    all_cols_in_split = list(record.keys())
                    # Initialize counters for all found columns
                    # We only initialize counters for columns found in this specific split
                    populated_counts = {col: 0 for col in all_cols_in_split}
                
                # --- Population Check ---
                for col in populated_counts.keys():
                    value = record.get(col)
                    
                    # Check 1: Value is None (Python Null)
                    if value is None:
                        continue
                        
                    # Check 2: Value is NaN (Pandas/Float Null)
                    # We use np.isnan(value) check only if the value is a float
                    if isinstance(value, float) and np.isnan(value):
                        continue

                    # Check 3: Value is an empty string
                    if isinstance(value, str) and value.strip() == '':
                        continue
                        
                    # Check 4: Value is an empty list (Catches '[]')
                    if isinstance(value, list) and not value:
                        continue
                        
                    # If the value passes all emptiness checks, it is counted as 'populated'
                    populated_counts[col] += 1
                        
            # 3. Finalize Auditing Metrics
            missing_stats = {'Dataset/Split': full_name, 'Total Records': total_records}
            
            for col in populated_counts.keys():
                if total_records > 0:
                    # Calculate percentage of populated values
                    populated_percent = (populated_counts[col] / total_records) * 100
                    missing_stats[f'{col}_Populated_Pct'] = round(populated_percent, 2)
                    missing_stats[f'{col}_Missing_Count'] = total_records - populated_counts[col]
                else:
                    missing_stats[f'{col}_Populated_Pct'] = 0.0
                    missing_stats[f'{col}_Missing_Count'] = 0
                    
            audit_results.append(missing_stats)
            
        except Exception as e:
            error_message = str(e)
            if 'Does not have a split' in error_message:
                 print(f"Skipping {full_name}: Split does not exist for this subset.")
            elif '404 Client Error' in error_message:
                 print(f"Skipping {full_name}: Subset not found or split is inaccessible.")
            else:
                 print(f"Failed to load or process {full_name}. Error: {e}")
            
            audit_results.append({'Dataset/Split': full_name, 'Total Records': 0, 'Error': error_message})

    return pd.DataFrame(audit_results)

# --- Execution ---
if __name__ == "__main__":
    start_time = time.time() # Start timer

    # Ensure the 'eval' directory exists for output
    os.makedirs('eval', exist_ok=True)
    
    # Run the audit
    df_audit_results = run_dqa_audit(DATASET_CONFIGS, CRITICAL_COLUMNS)
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time

    # --- Print and Save Outputs ---
    
    # 1. Save Detailed Audit CSV
    output_csv_path = "eval/E0_ragbench_dqa_detail.csv"
    df_audit_results.to_csv(output_csv_path, index=False)
    
    print("\n" + "="*50)
    print("✨ E0 DQA Audit Complete")
    print(f"Total Execution Time: {execution_time:.2f} seconds")
    print(f"Results for all {len(DATASET_CONFIGS)} configurations saved to {output_csv_path}")
    print("="*50)
    
    # Optional: Display a filtered view of the critical columns
    print("\n--- Summary of Critical Column Population (%) ---")
    
    # Identify which critical columns were successfully found in at least one split
    filtered_cols = [col for col in df_audit_results.columns if any(c in col for c in CRITICAL_COLUMNS) and 'Populated_Pct' in col]
    
    display_cols = ['Dataset/Split', 'Total Records'] + filtered_cols
    print(df_audit_results[display_cols].fillna('N/A'))