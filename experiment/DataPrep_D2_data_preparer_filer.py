import json
import os
import time
from datasets import load_dataset
from typing import List, Dict, Any
import numpy as np

# --- Configuration ---

# 1. Define the specific subsets and splits to process based on your E0.1 results.
# This list is based on your highest-quality eligible records.
DATASET_CONFIGS_TO_FILTER = [
    {"subset": "delucionqa", "split": "test"},
    {"subset": "expertqa", "split": "test"},
    {"subset": "finqa", "split": "test"},
    {"subset": "hagrid", "split": "test"},
    {"subset": "hotpotqa", "split": "test"},
    {"subset": "msmarco", "split": "test"},
]

# CRITICAL COLUMNS (All 10 must be non-empty for a record to be kept)
CRITICAL_COLUMNS = [
    "response", "documents", "trulens_groundedness", "ragas_faithfulness", 
    "trulens_context_relevance", "gpt3_adherence", "gpt3_context_relevance", 
    "utilization_score", "gpt35_utilization", "all_relevant_sentence_keys"
]

# 2. Define the Google Drive Output Path
# !!! CRITICAL: REPLACE THIS PLACEHOLDER WITH YOUR CORRECT LOCAL SYNC PATH !!!
# Example for Windows: r"G:\My Drive\conceptual_GraphRAG\Data"
# The program relies on the Google Drive desktop app syncing this local folder.
# --------------------------------------------------------------------------
ABSOLUTE_DRIVE_PATH = r"G:\My Drive\conceptual_GraphRAG\data" 
# --------------------------------------------------------------------------


# --- D2 Data Preparation Logic ---

def is_record_valid(record: Dict[str, Any], columns: List[str]) -> bool:
    """
    Checks if a single record has non-empty values for ALL critical columns.
    This implements the 10-column filter derived from the E0 audit.
    """
    for col in columns:
        value = record.get(col)
        
        # Check 1: Value is None (Python Null)
        if value is None:
            return False
            
        # Check 2: Value is NaN (Float Null)
        # Use np.isnan check only if the value is a float
        if isinstance(value, float) and np.isnan(value):
            return False

        # Check 3: Value is an empty string (or just whitespace)
        if isinstance(value, str) and value.strip() == '':
            return False
            
        # Check 4: Value is an empty list (Catches '[]' for key fields)
        if isinstance(value, list) and not value:
            return False
            
    return True

def process_and_filter_dataset(config: Dict[str, str], columns: List[str], output_dir: str):
    """
    Loads one dataset split, strictly filters records based on ALL critical columns, 
    and saves the clean output file directly to the specified directory.
    """
    subset_name = config['subset']
    split_name = config['split']
    
    full_name = f"galileo-ai/ragbench:{subset_name}/{split_name}"
    # Output file is named D2_CLEAN_subset_split.jsonl
    output_filename = f"D2_CLEAN_{subset_name}_{split_name}.jsonl"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"\n--- Starting Filter for: {full_name} ---")
    
    try:
        # Load the dataset using streaming for memory safety
        # This accesses the RAGBench data from Hugging Face
        ds_stream = load_dataset("galileo-ai/ragbench", subset_name, split=split_name, streaming=True)
        
        clean_records = []
        total_records = 0
        
        # 1. Iterate and Filter
        for record in ds_stream:
            total_records += 1
            # The record is only kept if it meets all 10 non-empty criteria
            if is_record_valid(record, columns):
                # The entire original record (all 30+ columns) is preserved
                clean_records.append(record)
        
        # 2. Save Clean Records
        if clean_records:
            os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                for record in clean_records:
                    # Write the full record to the Google Drive sync path
                    f.write(json.dumps(record) + '\n')
            
            print(f"[SUCCESS] Success: Saved {len(clean_records)} clean records (out of {total_records}) to {output_path}")
            print(f"   Syncing to Google Drive...")
        else:
            print(f"[WARNING] Warning: Found 0 records that meet all 10 non-empty criteria for {full_name}.")
            
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to process {full_name}. Check split name or connection. Error: {e}")


# --- Main Driver ---

def run_d2_preparer(configs: List[Dict[str, str]], drive_path: str):
    """Runs the preparer across all defined configurations."""
    start_time = time.time()
    
    # Check if the placeholder path was correctly updated
    if drive_path == r"C:\Users\YourUsername\Google Drive\conceptual_GraphRAG\Data":
        print("\n!!! FATAL: Please update the ABSOLUTE_DRIVE_PATH variable in the script with your correct path. !!!")
        return

    print("="*60)
    print("✨ D2: Data Preparation and Strict Filtering Start")
    print(f"Output Target: {drive_path}")
    print(f"Processing {len(configs)} configurations...")
    
    for config in configs:
        process_and_filter_dataset(config, CRITICAL_COLUMNS, drive_path)
        
    execution_time = time.time() - start_time
    print("\n" + "="*60)
    print("D2 Data Preparation Complete.")
    print(f"Total Execution Time: {execution_time:.2f} seconds")
    print("="*60)


if __name__ == "__main__":
    run_d2_preparer(DATASET_CONFIGS_TO_FILTER, ABSOLUTE_DRIVE_PATH)