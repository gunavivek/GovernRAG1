import pandas as pd
import json
from typing import Dict, Any, List
import os
import numpy as np

# --- Configuration ---
# INPUT: The canonical output from the E1.2 module
E1_INPUT_PATH = "eval/E1_2_type_aware_accuracy.jsonl"
# OUTPUT: The comprehensive JSON summary (Required for analysis)
E1_SUMMARY_JSON_PATH = "eval/E1_3_summary.json"

# Columns to be aggregated (metrics calculated in E1.1 and E1.2)
METRIC_COLUMNS = [
    'exact_match', 
    'f1_token_overlap', 
    'entity_match', 
    'numeric_match'
]

# Dimensions for aggregation (grouping keys)
GROUPING_DIMENSIONS = [
    'intent', 
    'answer_type', 
    'dataset_name', 
    'primary_domain'
]

# --- 1. Aggregation and Summarization Function ---

def calculate_summaries(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates overall and grouped mean metrics, treating -1 (Not Applicable) as NaN.
    """
    summary = {}
    
    # Clean dataframe: Convert -1 (Not Applicable) to NaN (pandas' missing value) 
    # for correct averaging, ensuring metrics are only averaged over applicable questions.
    df_cleaned = df.copy()
    for col in METRIC_COLUMNS:
        df_cleaned[col] = df_cleaned[col].replace(-1, np.nan)

    # --- Global Summary ---
    
    # Calculate means, rounded to 4 decimal places for reporting
    global_metrics = df_cleaned[METRIC_COLUMNS].mean().round(4).to_dict()
    
    summary['Global_Summary'] = {
        'total_records': len(df),
        'mean_em': global_metrics.get('exact_match'),
        'mean_f1': global_metrics.get('f1_token_overlap'),
        # E1.2 metrics are often referred to as 'accuracy'
        'entity_accuracy': global_metrics.get('entity_match'),
        'numeric_accuracy': global_metrics.get('numeric_match'),
    }

    # --- Grouped Summaries ---
    
    summary['Grouped_Summaries'] = {}
    
    for dimension in GROUPING_DIMENSIONS:
        if dimension in df_cleaned.columns and df_cleaned[dimension].nunique() > 0:
            
            # Drop rows where the grouping column value is missing/NaN
            df_grouped = df_cleaned.dropna(subset=[dimension])
            
            # Calculate mean metrics for each group within the dimension
            group_summary = df_grouped.groupby(dimension)[METRIC_COLUMNS].mean().round(4)
            
            # Get the count of applicable records for each group
            group_counts = df_grouped.groupby(dimension).size().to_dict()
            
            dimension_results = {}
            
            for group_name, row in group_summary.iterrows():
                dimension_results[str(group_name)] = {
                    'count': group_counts.get(group_name, 0),
                    'mean_em': row.get('exact_match'),
                    'mean_f1': row.get('f1_token_overlap'),
                    'entity_accuracy': row.get('entity_match'),
                    'numeric_accuracy': row.get('numeric_match'),
                }
                
            summary['Grouped_Summaries'][dimension] = dimension_results
        
    return summary


# --- 2. Main E1.3 Runner ---

def run_e1_3_summary_metrics(input_path: str, json_path: str):
    """
    Loads E1.2 output, calculates summary metrics, and saves the results in JSON format.
    """
    print(f"Loading E1.2 data from {input_path}...")
    try:
        # Load the JSONL file directly into a pandas DataFrame
        df = pd.read_json(input_path, lines=True)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}. Please ensure E1.2 has run.")
        return
    except pd.errors.EmptyDataError:
        print("Error: Input file is empty. Cannot generate summary metrics.")
        return
    except ValueError as e:
        print(f"Error reading JSONL file: {e}. Check file formatting.")
        return
        
    if df.empty:
        print("Input DataFrame is empty. Cannot generate summary metrics.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    print(f"Calculating global and grouped summary metrics for {len(df)} records...")
    
    # Calculate the summaries
    summary_data = calculate_summaries(df)

    # --- Save JSON Output ---
    
    # Save JSON (Nested structure for programmatic access)
    with open(json_path, 'w', encoding='utf-8') as f:
        # Use json.dump with indent for readability
        json.dump(summary_data, f, indent=4)
    print(f"Summary metrics saved to JSON: {json_path}")
    
    print("E1.3 Summary Metrics Complete.")

# --- Execution Example ---
if __name__ == "__main__":
    
    # --- Setup Dummy E1.2 Input File ---
    os.makedirs('eval', exist_ok=True)
    
    # Simulate a dataset with two intents and two domains
    dummy_e1_2_data = [
        # Record 1: Extractive (Correct Entity) - IT Domain
        {"id": "001", "intent": "extractive", "dataset_name": "DS1", "primary_domain": "IT", 
         "exact_match": 0, "f1_token_overlap": 0.9, "entity_match": 1, "numeric_match": -1},
        # Record 2: Extractive (Wrong Entity) - IT Domain
        {"id": "002", "intent": "extractive", "dataset_name": "DS1", "primary_domain": "IT", 
         "exact_match": 0, "f1_token_overlap": 0.5, "entity_match": 0, "numeric_match": -1},
        # Record 3: Quantitative (Correct Number) - Finance Domain
        {"id": "003", "intent": "quantitative", "dataset_name": "DS2", "primary_domain": "Finance", 
         "exact_match": 0, "f1_token_overlap": 0.7, "entity_match": -1, "numeric_match": 1},
        # Record 4: Quantitative (Wrong Number) - Finance Domain
        {"id": "004", "intent": "quantitative", "dataset_name": "DS2", "primary_domain": "Finance", 
         "exact_match": 0, "f1_token_overlap": 0.6, "entity_match": -1, "numeric_match": 0},
        # Record 5: Summarization (Skipped in E1.2, only affects EM/F1 global average) - IT Domain
        {"id": "005", "intent": "summarization", "dataset_name": "DS1", "primary_domain": "IT", 
         "exact_match": 0, "f1_token_overlap": 0.8, "entity_match": -1, "numeric_match": -1},
    ]
    
    DUMMY_E1_2_PATH = "eval/E1_2_type_aware_accuracy_dummy.jsonl"
    with open(DUMMY_E1_2_PATH, 'w', encoding='utf-8') as f:
        for record in dummy_e1_2_data:
            f.write(json.dumps(record) + '\n')
            
    # Run the E1.3 module using the dummy path
    print("--- Running E1.3 Summary Metrics ---")
    run_e1_3_summary_metrics(DUMMY_E1_2_PATH, E1_SUMMARY_JSON_PATH)