import pandas as pd
import json
import os
from typing import Dict, Any, List
import numpy as np

# --- Configuration ---
# INPUTS:
E1_SUMMARY_PATH = "eval/E1_3_summary.json"     # Aggregated metrics for YOUR system
E21_INPUT_PATH = "eval/E2_1_correlation_analysis.jsonl" # Used to derive system success rates

# NOTE: Baseline data must be generated externally by running a Vector RAG model 
# (or simplified GraphRAG) on the same dataset and metrics. We simulate this.
BASELINE_SUMMARY_PATH = "data/Baseline_RAG_Summary.json"

# OUTPUT: The final comparison table
E2_OUTPUT_PATH = "eval/E2_2_comparison_summary.json"

# List of the 10 critical metrics we must compare (used for final structure)
CRITICAL_METRICS = [
    'mean_em', 'mean_f1', 'entity_accuracy', 'numeric_accuracy',
    'trulens_groundedness', 'ragas_faithfulness', 'trulens_context_relevance',
    'utilization_score', 'gpt3_adherence', 'gpt35_utilization'
]

# --- 1. Utility Functions ---

def load_json_data(path: str) -> Dict[str, Any]:
    """Load a JSON file (used for E1.3 and Baseline summaries)."""
    if not os.path.exists(path):
        print(f"Error: Required file not found at {path}. Returning empty dictionary.")
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
        return {}

def calculate_success_rate(e21_path: str, metric_column: str) -> Dict[str, float]:
    """
    Calculates the average success rate for a given binary flag (e.g., high_groundedness_flag).
    Since E2.1 is per-record, we aggregate here to get the global mean percentage.
    """
    try:
        df = pd.read_json(e21_path, lines=True)
        if df.empty or metric_column not in df.columns:
            return {'Global': 0.0}
        
        # Calculate global mean (which is the success percentage for a 0/1 flag)
        global_rate = df[metric_column].mean()
        
        # Calculate mean grouped by intent
        intent_rates = df.groupby('intent')[metric_column].mean().to_dict()
        
        # Convert means to percentages and return
        results = {k: round(v * 100, 2) for k, v in intent_rates.items()}
        results['Global'] = round(global_rate * 100, 2)
        
        return results
        
    except Exception as e:
        print(f"Error calculating success rate from {e21_path}: {e}")
        return {'Global': 0.0}


# --- 2. Main Comparison Logic ---

def run_e2_2_comparison(e1_path: str, e21_path: str, baseline_path: str, output_path: str):
    """
    Compares Your System (GraphRAG) vs. Baseline RAG and reports performance deltas.
    """
    print("--- Starting E2.2 Baseline Comparison ---")

    # 1. Load Aggregated Data
    your_summary = load_json_data(e1_path)
    baseline_summary = load_json_data(baseline_path)

    if not your_summary or not baseline_summary:
        print("Aborting E2.2: Missing Your System Summary or Baseline Summary data.")
        return

    # 2. Calculate Success Rates for Per-Record Flags (E2.1 Output)
    # This proves the efficacy of the E2.0 causal variables.
    your_groundedness_success_rate = calculate_success_rate(e21_path, 'high_groundedness_flag')
    
    # NOTE: You would typically need baseline E2.1 data here too, but we focus on your system's output
    # to show the performance driven by the structural usage.

    # 3. Create Comparison Structure (The Report)
    comparison_report = {
        'metadata': {
            'system_name': 'Concept-Enhanced GraphRAG',
            'baseline_name': 'Vanilla Vector RAG',
            'total_records': your_summary.get('Global_Summary', {}).get('total_records', 0)
        },
        'Global_Metrics': {},
        'Grouped_Deltas_by_Intent': {},
        'Groundedness_Success_Rate': your_groundedness_success_rate
    }

    # 4. Global Metric Comparison
    your_global = your_summary.get('Global_Summary', {})
    baseline_global = baseline_summary.get('Global_Summary', {})

    for metric in CRITICAL_METRICS:
        your_score = your_global.get(metric)
        baseline_score = baseline_global.get(metric)
        
        # Skip if either value is missing (NaN/None)
        if your_score is None or baseline_score is None:
            comparison_report['Global_Metrics'][metric] = {'yours': your_score, 'baseline': baseline_score, 'delta': None}
            continue

        # Calculate Delta: GraphRAG - Baseline
        delta = round(your_score - baseline_score, 4)
        
        comparison_report['Global_Metrics'][metric] = {
            'yours': your_score,
            'baseline': baseline_score,
            'delta': delta,
            'improvement_flag': 'POSITIVE' if delta > 0 else ('NEGATIVE' if delta < 0 else 'NEUTRAL')
        }

    # 5. Grouped Comparison by Intent
    your_grouped = your_summary.get('Grouped_Summaries', {}).get('intent', {})
    baseline_grouped = baseline_summary.get('Grouped_Summaries', {}).get('intent', {})

    for intent, your_scores in your_grouped.items():
        baseline_scores = baseline_grouped.get(intent, {})
        intent_deltas = {'count': your_scores.get('count', 0)}
        
        for metric in CRITICAL_METRICS:
            y_score = your_scores.get(metric)
            b_score = baseline_scores.get(metric)
            
            if y_score is not None and b_score is not None:
                delta = round(y_score - b_score, 4)
                intent_deltas[f'delta_{metric}'] = delta

        comparison_report['Grouped_Deltas_by_Intent'][intent] = intent_deltas

    # 6. Save Final Report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        # Use allow_nan=True if necessary, though pandas usually handles floats well
        json.dump(comparison_report, f, indent=4) 

    print(f"E2.2 Baseline Comparison Complete. Final report saved to: {output_path}")

# --- Execution Example ---
if __name__ == "__main__":
    
    # --- SIMULATE INPUT FILES ---
    os.makedirs('data', exist_ok=True)
    os.makedirs('eval', exist_ok=True)

    # 1. Simulate E1.3 Summary (Your System: GraphRAG)
    your_summary_data = {
        "Global_Summary": {
            "total_records": 5000, "mean_f1": 0.78, "entity_accuracy": 0.85, 
            "trulens_groundedness": 0.92, "ragas_faithfulness": 0.90,
            "trulens_context_relevance": 0.88, "utilization_score": 0.65,
            # Add placeholders for all 10 critical metrics used in CRITICAL_METRICS list
            "mean_em": 0.1, "numeric_accuracy": 0.75, "gpt3_adherence": 0.91,
            "gpt3_context_relevance": 0.85, "gpt35_utilization": 0.70
        },
        "Grouped_Summaries": {
            "intent": {
                "extractive": {"count": 2000, "mean_f1": 0.82, "entity_accuracy": 0.91, 
                               "trulens_groundedness": 0.95, "numeric_accuracy": None},
                "quantitative": {"count": 1000, "mean_f1": 0.70, "entity_accuracy": None, 
                                 "trulens_groundedness": 0.88, "numeric_accuracy": 0.85},
            }
        }
    }
    with open(E1_SUMMARY_PATH, 'w') as f: json.dump(your_summary_data, f, indent=4)

    # 2. Simulate Baseline Summary (Vector RAG)
    baseline_summary_data = {
        "Global_Summary": {
            "total_records": 5000, "mean_f1": 0.74, "entity_accuracy": 0.75, 
            "trulens_groundedness": 0.80, "ragas_faithfulness": 0.82,
            "trulens_context_relevance": 0.75, "utilization_score": 0.55,
            "mean_em": 0.08, "numeric_accuracy": 0.60, "gpt3_adherence": 0.81,
            "gpt3_context_relevance": 0.75, "gpt35_utilization": 0.60
        },
        "Grouped_Summaries": {
            "intent": {
                "extractive": {"count": 2000, "mean_f1": 0.75, "entity_accuracy": 0.80, 
                               "trulens_groundedness": 0.85, "numeric_accuracy": None},
                "quantitative": {"count": 1000, "mean_f1": 0.68, "entity_accuracy": None, 
                                 "trulens_groundedness": 0.75, "numeric_accuracy": 0.70},
            }
        }
    }
    with open(BASELINE_SUMMARY_PATH, 'w') as f: json.dump(baseline_summary_data, f, indent=4)

    # 3. Simulate E2.1 Input (High Groundedness Success Rate for Your System)
    # This is a highly simplified simulation just to pass the function call:
    e21_dummy_data = [] # In real life, this would be thousands of lines
    with open(E21_INPUT_PATH, 'w') as f:
         # Write some minimal data to ensure the file exists and is readable
         f.write(json.dumps({"id": "dummy_1", "high_groundedness_flag": 1, "intent": "extractive"}) + '\n')
         f.write(json.dumps({"id": "dummy_2", "high_groundedness_flag": 0, "intent": "extractive"}) + '\n')
         f.write(json.dumps({"id": "dummy_3", "high_groundedness_flag": 1, "intent": "quantitative"}) + '\n')
    
    # 4. Run E2.2 Comparison
    run_e2_2_comparison(E1_SUMMARY_PATH, E21_INPUT_PATH, BASELINE_SUMMARY_PATH, E2_OUTPUT_PATH)