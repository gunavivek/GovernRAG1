import json
import os
import pandas as pd
import nltk
from typing import Dict, Any
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

# --- Dependency Setup ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class E1ValidationEngine:
    def __init__(self, 
                 system_path="output/Q4_final_answers.jsonl", 
                 golden_path="data/hotpotqa_test.jsonl"):
        """
        Initializes the Evaluation Engine.
        Paths are relative to the 'conceptual_GraphRAG' root directory.
        """
        print(f"\n[DEBUG] Working Directory: {os.getcwd()}")
        self.system_results = self._load_jsonl(system_path)
        self.golden_key = self._load_jsonl(golden_path)
        self.r_scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

    def _load_jsonl(self, path: str) -> Dict[str, Any]:
        data = {}
        if not os.path.exists(path):
            print(f"[WARNING] File not found: {os.path.abspath(path)}")
            return data
        
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    # Extract unique ID (handling both 'id' and '_id')
                    uid = str(obj.get('id') or obj.get('_id'))
                    data[uid] = obj
                except json.JSONDecodeError:
                    continue
        print(f"[INFO] Loaded {len(data)} records from {path}")
        return data

    def calculate_metrics(self, actual: str, expected: str) -> Dict[str, float]:
        """Calculates Semantic Overlap (Metric A)."""
        if not actual or not expected:
            return {"bleu": 0.0, "rougeL": 0.0}
        
        # BLEU Score
        ref = [expected.lower().split()]
        cand = actual.lower().split()
        bleu = sentence_bleu(ref, cand, smoothing_function=SmoothingFunction().method1)
        
        # ROUGE-L Score
        rouge = self.r_scorer.score(expected, actual)['rougeL'].fmeasure
        
        return {"bleu": bleu, "rougeL": rouge}

    def execute_evaluation(self):
        if not self.golden_key:
            print("[ERROR] No Golden Truth data found. Evaluation aborted.")
            return

        print("\n" + "="*80)
        print("--- E1: EPISTEMIC VALIDATION (Actual vs. Expected) ---")
        print("="*80 + "\n")
        
        final_report = []
        summary = {"Correct": 0, "Hallucinated": 0, "Blocked_Correctly": 0, "Failed": 0}

        for uid, golden in self.golden_key.items():
            system = self.system_results.get(uid)
            if not system:
                continue

            # --- Map keys to Q4 Output Structure ---
            expected = golden.get('response', '').strip()
            # Q4 uses 'generated_answer' as seen in your code
            actual = system.get('generated_answer', '').strip()
            mode = system.get('mode', 'STANDARD')
            evidence_count = system.get('evidence_count', 0)

            # --- Comparison Console Print ---
            print(f"ID: {uid}")
            print(f"EXPECTED (Golden): {expected}")
            print(f"ACTUAL   (System): {actual}")
            
            # --- Categorization Logic ---
            if mode == "BLOCKED_BY_GOVERNANCE":
                status = "Blocked_Correctly"
                summary["Blocked_Correctly"] += 1
                scores = {"bleu": 0.0, "rougeL": 0.0}
            else:
                scores = self.calculate_metrics(actual, expected)
                
                # Rule: If answer exists but evidence_count was 0 (Governance Violation)
                if evidence_count == 0 and actual:
                    status = "Hallucinated"
                    summary["Hallucinated"] += 1
                elif scores['rougeL'] >= 0.3: # Pass threshold
                    status = "Correct"
                    summary["Correct"] += 1
                else:
                    status = "Failed"
                    summary["Failed"] += 1

            print(f"MODE: {mode} | ROUGE-L: {scores.get('rougeL', 0):.4f} | STATUS: {status}")
            print("-" * 60)

            final_report.append({
                "id": uid,
                "status": status,
                "rougeL": round(scores.get('rougeL', 0), 4),
                "mode": mode,
                "evidence_count": evidence_count
            })

        # --- Final Summary ---
        print("\n" + "="*30)
        print("FINAL E1 VALIDATION SUMMARY")
        print("="*30)
        for cat, count in summary.items():
            print(f"{cat.ljust(18)}: {count}")
        print("="*30 + "\n")

        # Save to CSV
        os.makedirs("eval", exist_ok=True)
        pd.DataFrame(final_report).to_csv("eval/E1_detailed_results.csv", index=False)
        print(f"Detailed results saved to: eval/E1_detailed_results.csv")

if __name__ == "__main__":
    engine = E1ValidationEngine()
    engine.execute_evaluation()