import json
import re
from typing import Dict, List, Tuple
from collections import Counter
import string
from tqdm import tqdm
import os

# --- Configuration ---
Q6_ANSWERS_PATH = "output/Q6_answers.jsonl"         # Assumed path for Q-pipeline output (single record)
D1_GROUND_TRUTH_PATH = "data/D1_test_file.jsonl" # Specified path for static gold answers
E1_OUTPUT_PATH = "eval/E1_1_answer_alignment.jsonl" # Canonical output for E1.1

# --- 1. Answer Normalization and Metric Functions (Core QA Logic) ---

def normalize_answer(s: str) -> str:
    """
    Normalizes text by lowercasing, removing articles, punctuation, and extra whitespace.
    """
    def remove_articles(text):
        # Removes 'a', 'an', 'the' at word boundaries
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))

def get_tokens(s: str) -> List[str]:
    """Tokenizes normalized string for F1 calculation."""
    if not s:
        return []
    return normalize_answer(s).split()

def compute_f1(a_gold: str, a_pred: str) -> float:
    """Computes F1 token overlap score."""
    gold_toks = get_tokens(a_gold)
    pred_toks = get_tokens(a_pred)
    
    # Calculate common tokens using Counters
    common = Counter(gold_toks) & Counter(pred_toks)
    num_common = sum(common.values())
    
    # Edge case: If both are empty, F1 is 1.0 (Exact Match)
    if len(gold_toks) == 0 or len(pred_toks) == 0:
        return float(gold_toks == pred_toks)
    
    precision = num_common / len(pred_toks)
    recall = num_common / len(gold_toks)
    
    if precision + recall == 0:
        return 0.0
        
    return 2 * (precision * recall) / (precision + recall)

def compute_exact_match(a_gold: str, a_pred: str) -> int:
    """Computes Exact Match score (binary)."""
    return int(normalize_answer(a_gold) == normalize_answer(a_pred))

# --- 2. Data Loading and Lookup ---

def load_d1_lookup_map(path: str) -> Dict[str, dict]:
    """Loads D1 file into an in-memory dictionary for fast ID lookup."""
    d1_map = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line.strip())
                if 'id' in record and 'response' in record:
                    d1_map[record['id']] = record
    except FileNotFoundError:
        print(f"Error: Required D1 file not found at {path}. Cannot run evaluation.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
        return {}
    return d1_map

# --- 3. Main Evaluation Function ---

# Load D1 map once outside the main run loop for efficiency
D1_MAP = load_d1_lookup_map(D1_GROUND_TRUTH_PATH)

def run_e1_1_alignment_for_record(q6_path: str, output_path: str):
    """
    Executes E1.1 evaluation for a single record from Q6 output, fetches gold
    answer using ID lookup, and appends results to the output file.
    """
    if not D1_MAP:
        print("D1 map is empty. Exiting E1.1.")
        return

    # --- Step 1: Load Q6 Output (Single Record) ---
    try:
        # Assuming Q6_answers.jsonl contains the single latest record
        with open(q6_path, 'r', encoding='utf-8') as f:
            # We assume the file is small or contains only the most recent record
            q6_records = [json.loads(line.strip()) for line in f]
            if not q6_records:
                print(f"No records found in Q6 output file: {q6_path}. Skipping.")
                return
            record = q6_records[0] # Process the first (and only expected) record
    except FileNotFoundError:
        print(f"Error: Q6 output file not found at {q6_path}. Skipping E1.1.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in Q6 output file: {e}. Skipping E1.1.")
        return
    
    record_id = record.get('id')
    print(f"\n--- Starting E1.1 for ID: {record_id} ---")

    # --- Step 2: Fetch Gold Answer (Direct Lookup) ---
    gold_record = D1_MAP.get(record_id)
    
    if not gold_record:
        print(f"Warning: Record ID {record_id} not found in D1 map. Cannot evaluate. Skipping.")
        return
        
    # Merge essential D1 fields into the record for output/traceability
    record['question'] = gold_record.get('question', record.get('question'))
    record['response'] = gold_record.get('response', '') # Gold Answer
    record['dataset_name'] = gold_record.get('dataset_name', record.get('dataset_name'))

    gold_answer = record['response']
    generated_answer = record.get('generated_answer', '')
    
    if not generated_answer or not gold_answer:
        print(f"Skipping record {record_id}: Missing generated or gold answer.")
        return

    # --- Step 3: Compute Metrics ---
    
    # Normalize answers for downstream use (E1.2)
    pred_normalized = normalize_answer(generated_answer)
    gold_normalized = normalize_answer(gold_answer)
    
    exact_match = compute_exact_match(gold_answer, generated_answer)
    f1_score = compute_f1(gold_answer, generated_answer)
    
    # Append calculated scores and normalized answers
    result = {
        **record,
        "pred_normalized": pred_normalized, 
        "gold_normalized": gold_normalized, 
        "exact_match": exact_match,
        "f1_token_overlap": f1_score
    }

    # --- Step 4: Accumulate Results ---
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Open in 'a' (append) mode to accumulate results across runs
    try:
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result) + '\n')
        print(f"Successfully evaluated and appended scores for ID: {record_id}")
    except Exception as e:
        print(f"Error writing to output file for ID {record_id}: {e}")

# --- Execution Example ---
if __name__ == "__main__":
    
    # 1. Setup Dummy Data for the Test Run
    # Create the required directory structure
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    os.makedirs('eval', exist_ok=True)

    # D1 Test File (Gold Truth)
    d1_records = [
        {"id": "test record_id 1", "question": "What is the new architecture?", "response": "Apollo", "dataset_name": "IT_train"},
        {"id": "test record_id 2", "question": "What is the key number?", "response": "15%", "dataset_name": "Finance"},
    ]
    with open(D1_GROUND_TRUTH_PATH, 'w', encoding='utf-8') as f:
        for record in d1_records:
            f.write(json.dumps(record) + '\n')
            
    # Q6 Test File (Simulate 1st Run Output)
    q6_run1 = {"id": "test record_id 1", "generated_answer": "Apollo", "retrieval_contexts": ["..."], "answer_type": "extractive"}
    with open(Q6_ANSWERS_PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(q6_run1) + '\n')
            
    # 2. Run E1.1 for the first record
    print("--- Running E1.1 (Run 1: EM=1, F1=1) ---")
    run_e1_1_alignment_for_record(Q6_ANSWERS_PATH, E1_OUTPUT_PATH)

    # 3. Simulate 2nd Run (Q-pipeline output changes)
    q6_run2 = {"id": "test record_id 2", "generated_answer": "fifteen percent.", "retrieval_contexts": ["..."], "answer_type": "quantitative"}
    with open(Q6_ANSWERS_PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(q6_run2) + '\n')

    # 4. Run E1.1 for the second record (Appends to the same file)
    print("\n--- Running E1.1 (Run 2: EM=0, F1~0.8) ---")
    run_e1_1_alignment_for_record(Q6_ANSWERS_PATH, E1_OUTPUT_PATH)
    
    print("\n--- E1.1 Execution Complete ---")
    print(f"All results accumulated in: {E1_OUTPUT_PATH}")