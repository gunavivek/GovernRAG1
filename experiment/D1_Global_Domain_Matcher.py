import pandas as pd
import json
import os
from typing import Dict

# --- Ph.D. Rigor Configuration ---
# Anchoring all paths to the project root for dissertation portability [cite: 1]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

class D1Serializer:
    """
    D1: Global Ground Truth Serializer
    Purpose: One-time execution to establish the baseline "Control" variable[cite: 9].
    """
    
    def __init__(self, input_file: str, output_file: str):
        self.input_path = input_file
        self.output_path = output_file
        self.ground_truth_map: Dict[str, str] = {}

    def run_serialization(self):
        """
        Transformation Logic: Maps Dataset -> Domain with standardization[cite: 14].
        """
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Missing input layer: {self.input_path} [cite: 11]")

        print(f"--- D1 Execution: Processing {os.path.basename(self.input_path)} ---")
        
        # Load the RAGBench dataset description [cite: 11]
        # Data Model: dataset_id, global_baseline_domain [cite: 12, 13]
        df = pd.read_csv(self.input_path)
        
        for _, row in df.iterrows():
            # Extract and standardize text (lowercase, strip whitespace) [cite: 15]
            dataset_id = str(row['Dataset Name']).strip()
            domain_label = str(row['Domain']).strip().lower()
            
            self.ground_truth_map[dataset_id] = domain_label
            print(f"  [Serialized] {dataset_id} -> {domain_label}")

        self._save_artifact()

    def _save_artifact(self):
        """
        Storage: Persists the Experimental Baseline to JSON.
        """
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.ground_truth_map, f, indent=4)
        
        print(f"\n--- D1 Phase Complete ---")
        print(f"Experimental Baseline saved to: {self.output_path} [cite: 16]")

if __name__ == "__main__":
    # Define authoritative paths based on Technical Spec V3.1 [cite: 11, 16]
    INPUT_CSV = os.path.join(PROJECT_ROOT, "data", "RAGBench dataset description.csv")
    #INPUT_CSV = os.path.join(PROJECT_ROOT, "data", "RGB_Dataset_Negative_Rej.csv")
    OUTPUT_JSON = os.path.join(PROJECT_ROOT, "output", "D1_Global_Mapping.json")

    # Ph.D.-Level Execution
    try:
        serializer = D1Serializer(INPUT_CSV, OUTPUT_JSON)
        serializer.run_serialization()
    except Exception as e:
        print(f"D1 Execution Failure: {e}")