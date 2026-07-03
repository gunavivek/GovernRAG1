import json
import re
from typing import Dict, List, Optional
from tqdm import tqdm
import os
import string

# --- Configuration ---
# INPUTS:
Q2_INTENTS_PATH = "output/Q2_intents.jsonl"             # Source for intent (Single record expected)
E1_INPUT_PATH = "eval/E1_1_answer_alignment.jsonl"      # Canonical output from E1.1 (Single record expected)

# OUTPUT:
E1_OUTPUT_PATH = "eval/E1_2_type_aware_accuracy.jsonl"
NUMERIC_TOLERANCE = 0.01

# --- Data Loading Utility (Adjusted for single record read) ---

def load_single_record(path: str) -> Optional[dict]:
    """Loads the first (and only expected) record from a JSONL file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line:
                return json.loads(first_line)
    except FileNotFoundError:
        print(f"Error: Required input file not found at {path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
    return None

def load_jsonl_to_map(path: str, key_field: str = 'id') -> Dict[str, dict]:
    """Utility to load a full JSONL file into a map for lookup (used for Q2 here)."""
    # NOTE: We keep this utility as Q2 might contain more than one record if 
    # the Q-pipeline runs multiple records before E1.2 is triggered.
    data_map = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line.strip())
                if key_field in record:
                    data_map[record[key_field]] = record
    except Exception as e:
        # Catchall for file/decoding errors
        return {}
    return data_map


# --- Metric Calculation Functions (Unchanged) ---
# [Entity Match, Numeric Extraction, Numeric Match functions omitted for brevity, 
#  but they remain the same as the last working version.]

def compute_entity_match(gold_normalized: str, pred_normalized: str) -> Optional[int]:
    """ Refined entity match heuristic """
    gold_tokens = gold_normalized.split()
    if not gold_tokens:
        return None
    generic_words = {'the', 'a', 'an', 'is', 'was', 'in', 'of', 'for', 'it', 
                     'name', 'named', 'and', 'or', 'to', 'from', 'called',
                     'new', 'system', 'process', 'architecture', 'concept', 
                     'component', 'structure', 'implementation', 'migration', 
                     'pillar', 'experience', 'digital', 'transformation', 
                     'efficiency', 'operational', 'cloudnative'}
    key_tokens = [t for t in gold_tokens if t not in generic_words and len(t) > 2]
    key_token = max(key_tokens, key=len, default="") if key_tokens else max(gold_tokens, key=len, default="")
    if not key_token:
        return None
    return 1 if key_token in pred_normalized else 0

def extract_numbers_and_percentages(text: str) -> List[float]:
    """ Extracts numbers and percentages (as decimals) from a string. """
    numbers = []
    cleaned_text = text.replace(',', '')
    matches = re.findall(r'(\d[\d\.]*)(?:\.\d+)?\s*(%?)', cleaned_text)
    for value, unit in matches:
        try:
            num = float(value)
            numbers.append(num / 100.0 if unit == '%' else num)
        except ValueError:
            continue
    return numbers

def compute_numeric_match(gold_answer: str, pred_answer: str, tolerance: float) -> Optional[int]:
    """ Computes numeric match based on extracted numbers within tolerance. """
    gold_numbers = extract_numbers_and_percentages(gold_answer)
    pred_numbers = extract_numbers_and_percentages(pred_answer)
    if not gold_numbers:
        return None
        
    all_matched = True
    for g_num in gold_numbers:
        is_matched = False
        for p_num in pred_numbers:
            if abs(g_num - p_num) <= tolerance * abs(g_num) or (g_num == 0 and abs(p_num) <= tolerance):
                is_matched = True
                break
        if not is_matched:
            all_matched = False
            break
            
    return 1 if all_matched else 0


# --- Main E1.2 Runner (Modified for Direct Read) ---

def run_e1_2_type_aware_accuracy():
    """
    Directly reads the single record from E1.1 and the Q2 intent file, 
    merges data in memory, and performs type-aware accuracy calculation.
    """
    
    print("--- Starting E1.2 Direct Read and Calculation ---")
    
    # --- Step 1: Load E1.1 Record and Q2 Intents ---
    
    e1_record = load_single_record(E1_INPUT_PATH)
    if not e1_record:
        print(f"Error: E1.1 input not found or empty at {E1_INPUT_PATH}. Skipping E1.2.")
        return
        
    record_id = e1_record.get('id')
    
    # Load Q2 intents for the current record (assumes Q2 file has one matching record)
    q2_map = load_jsonl_to_map(Q2_INTENTS_PATH)
    q2_record = q2_map.get(record_id)

    if not q2_record:
        print(f"Warning: Intent for ID {record_id} not found in Q2 output. Cannot perform type-aware gating.")
        e1_record['intent'] = 'unknown'
        e1_record['answer_type'] = 'unknown'
    else:
        # Merge necessary Q2 fields directly into the E1.1 record
        e1_record['intent'] = q2_record.get('intent', 'unknown').lower()
        e1_record['answer_type'] = q2_record.get('answer_type', 'unknown').lower()
        e1_record['q2_notes'] = q2_record.get('q2_notes', 'N/A')

    # --- Step 2: Calculate Type-Aware Metrics ---
    
    os.makedirs(os.path.dirname(E1_OUTPUT_PATH), exist_ok=True)
    
    # Initialize E1.2 specific fields
    e1_record['entity_match'] = -1       
    e1_record['numeric_match'] = -1      
    e1_record['e1_2_notes'] = ""

    # Gating fields
    intent = e1_record.get('intent', 'unknown') 
    gold_normalized = e1_record.get('gold_normalized', '')
    pred_normalized = e1_record.get('pred_normalized', '')
    gold_answer = e1_record.get('response', '')        
    generated_answer = e1_record.get('generated_answer', '')

    notes = []

    # 1. Entity Match Check (Gated by Extractive/Factoid Intent)
    if 'extractive' in intent or 'factoid' in intent:
        entity_score = compute_entity_match(gold_normalized, pred_normalized)
        if entity_score is not None:
            e1_record['entity_match'] = entity_score
            notes.append(f"Entity check ran (Score: {entity_score}).")

    # 2. Numeric Match Check (Gated by Quantitative Intent)
    if 'quantitative' in intent or 'calculation' in intent:
        numeric_score = compute_numeric_match(gold_answer, generated_answer, NUMERIC_TOLERANCE)
        if numeric_score is not None:
            e1_record['numeric_match'] = numeric_score
            notes.append(f"Numeric check ran (Score: {numeric_score}).")
    
    e1_record['e1_2_notes'] = " | ".join(notes)

    # --- Step 3: Accumulate Results ---
    
    print(f"Saving result for ID: {record_id} to {E1_OUTPUT_PATH}...")
    # Open in 'a' (append) mode to accumulate results across runs
    with open(E1_OUTPUT_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(e1_record) + '\n')
        
    print(f"E1.2 Complete.")


# --- Pipeline Execution ---
if __name__ == "__main__":
    
    # --- Setup Dummy Files for Testing ---
    os.makedirs('output', exist_ok=True)
    os.makedirs('eval', exist_ok=True)

    # 1. Q2 Intent Output (Source)
    q2_data = {"id": "test record_id 1", "intent": "Extractive", "answer_type": "extractive", "q2_notes": "Predicted by LLM classifier."}
    with open(Q2_INTENTS_PATH, 'w', encoding='utf-8') as f:
         f.write(json.dumps(q2_data) + '\n')
         
    # 2. E1.1 Answer Alignment Output (Base Input)
    e1_1_data = {"id": "test record_id 1", "generated_answer": "Apollo", "response": "The new cloud-native architecture is named Apollo.", "gold_normalized": "new cloudnative architecture is named apollo", "pred_normalized": "apollo", "exact_match": 0, "f1_token_overlap": 0.2857142857142857}
    with open(E1_INPUT_PATH, 'w', encoding='utf-8') as f:
         f.write(json.dumps(e1_1_data) + '\n')
         
    # Run the E1.2 module
    run_e1_2_type_aware_accuracy()