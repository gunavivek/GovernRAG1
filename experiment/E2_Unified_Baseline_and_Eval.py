import os
import sys
import json
import argparse
import pandas as pd
from google import genai
from google.genai import types

# --- 1. ARGUMENT PARSING ---
parser = argparse.ArgumentParser(description="Generate Baseline and Evaluate DSR Pipeline.")
parser.add_argument('--numeric-id', type=int, required=True, help="Numeric ID of the record")
parser.add_argument('--flag', type=str, required=True, choices=['P', 'N', 'p', 'n'], help="Condition flag")
args = parser.parse_args()

numeric_id = args.numeric_id
flag = args.flag.upper()
target_record_id = f"rgb_{numeric_id}_{flag}".lower()

# --- 2. PATH SETUP ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

RAW_INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "en_refine.json") 
Q6_OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "Q6_final_answers.jsonl") 
MASTER_EVAL_LOG = os.path.join(PROJECT_ROOT, "output", "MASTER_EVALUATION_LOG.csv")

# --- 3. CONFIGURATION ---
BASELINE_MODEL = "gemma-3-4b-it"
JUDGE_MODEL = "gemini-3-flash-preview" 

api_key = os.getenv("GEMINI_API_KEY") 
client = genai.Client(api_key=api_key)

def generate_naive_rag(question, context):
    """Generates the Track 1 Baseline Answer."""
    print(f">> Generating Naive RAG Baseline ({BASELINE_MODEL})...")
    prompt = (
        f"Instructions: Answer the following question based ONLY on the context provided.\n\n"
        f"Context: {context}\n\n"
        f"Question: {question}"
    )
    try:
        response = client.models.generate_content(
            model=BASELINE_MODEL, contents=prompt, config=types.GenerateContentConfig(temperature=0.0)
        )
        return response.text.strip()
    except Exception as e:
        print(f"   [!] Baseline Generation Error: {e}")
        return f"ERROR: {str(e)}"

def evaluate_system(ground_truth, answer, sys_name):
    """Uses LLM-as-a-Judge to evaluate semantic alignment."""
    print(f">> Grading {sys_name} Output...")
    if not isinstance(answer, str) or answer.strip() == "":
        return "NO_MATCH"
        
    prompt = (
    "You are an academic evaluator grading an enterprise AI system.\n"
    "Compare the System Answer to the Ground Truth.\n\n"
    f"Ground Truth: {ground_truth}\n"
    f"System Answer: {answer}\n\n"
    "RULES:\n"
    "1. IGNORE provenance citation markers in the System Answer. "
    "Markers look like [CHNK_...], [CHNK_PRIMARY], [RESIDUAL_...], or similar bracketed tags. "
    "These are architectural metadata, not content. Mentally strip them before grading.\n"
    "2. If the System Answer (after stripping citation markers) contains the factual information in the Ground Truth, output exactly: MATCH\n"
    "3. If the System Answer is factually incorrect or hallucinates content unsupported by the Ground Truth, output exactly: NO_MATCH\n"
    "4. If the System Answer explicitly refuses to answer (e.g., 'Insufficient evidence', 'REJECTED', 'BLOCKED', 'NOT_FOUND'), output exactly: SAFE_SILENCE\n\n"
    "Output ONLY the single classification word."
    )
    
    try:
        response = client.models.generate_content(
            model=JUDGE_MODEL, contents=prompt, config=types.GenerateContentConfig(temperature=0.0) 
        )
        return response.text.strip().upper()
    except Exception as e:
        print(f"   [!] Eval Error: {e}")
        return "ERROR"

def run_unified_pipeline():
    print(f"======================================================")
    print(f" E2-PIPELINE: BASELINE GENERATION & FINAL EVALUATION")
    print(f" TARGET RECORD: {target_record_id.upper()}")
    print(f"======================================================")

    # --- STEP 1: READ RAW DATA ---
    print(f">> Fetching Raw Data from: {os.path.basename(RAW_INPUT_FILE)}...")
    try:
        with open(RAW_INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = [json.loads(line) for line in f if line.strip()]
            
            record = None
            for r in raw_data:
                # FIX 1: Match the exact integer 'id' field in the JSON to the numeric_id parameter
                if r.get('id') == numeric_id:
                    record = r
                    break
            
            if record is not None:
                question = record.get('query', 'UNKNOWN')
                
                # FIX 2: Handle nested answer lists (e.g. ["answer"] vs [["ans1", "ans2"]])
                ans_data = record.get('answer', 'UNKNOWN')
                if isinstance(ans_data, list) and len(ans_data) > 0:
                    if isinstance(ans_data[0], list):
                        ground_truth = str(ans_data[0][0]) # Pluck the first alias
                    else:
                        ground_truth = str(ans_data[0])
                else:
                    ground_truth = str(ans_data)
                
                # Fetch Positive or Negative context based on the flag
                context_key = 'positive' if flag == 'P' else 'negative'
                context_raw = record.get(context_key, [])
                
                context_str = ""
                if isinstance(context_raw, list):
                    for item in context_raw:
                        if isinstance(item, list) and len(item) == 2:
                            context_str += f"{item[1]} " 
                        else:
                            context_str += f"{item} "
                else:
                    context_str = str(context_raw)
                    
                context = context_str.strip()
                
            else:
                print(f"[FATAL] Target ID {numeric_id} not found in raw dataset.")
                sys.exit(1)
    except Exception as e:
        print(f"[FATAL] Could not read raw dataset: {e}")
        sys.exit(1)

    # --- STEP 2: GENERATE BASELINE ---
    naive_answer = generate_naive_rag(question, context)

    # --- STEP 3: FETCH GOV-RAG OUTPUT ---
    print(f">> Fetching Gov-RAG Output from Q6 logs...")
    gov_answer = "NOT_FOUND"
    if os.path.exists(Q6_OUTPUT_FILE):
        with open(Q6_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    q6_data = json.loads(line)
                    if q6_data.get('record_id', '').lower() == target_record_id.lower():
                        gov_answer = q6_data.get('generated_answer', 'NOT_FOUND') 
                except:
                    continue

    # --- STEP 4: EVALUATE BOTH ---
    naive_eval = evaluate_system(ground_truth, naive_answer, "Naive RAG")
    gov_eval = evaluate_system(ground_truth, gov_answer, "Gov-RAG")

    def grade_pipeline(eval_result, condition_flag):
        if condition_flag == 'P':
            return "SUCCESS (Accurate Retrieval)" if eval_result == "MATCH" else f"FAILURE ({eval_result})"
        else:
            if eval_result == "SAFE_SILENCE":
                return "SUCCESS (Boundary Maintained)"
            elif eval_result == "MATCH":
                return "FAILURE (Parametric Leakage / Hallucination)"
            else:
                return "FAILURE (Contextual Bleeding / Bad Output)"

    naive_status = grade_pipeline(naive_eval, flag)
    gov_status = grade_pipeline(gov_eval, flag)

    # --- NEW: VISUAL MANUAL VERIFICATION TRACE ---
    print(f"\n======================================================")
    print(f" MANUAL VERIFICATION TRACE FOR {target_record_id.upper()}")
    print(f" Condition: {'Negative (Expect Safe Silence)' if flag == 'N' else 'Positive (Expect Match)'}")
    print(f"======================================================")
    print(f" [Q] QUESTION:")
    print(f"     {question}")
    print(f"------------------------------------------------------")
    print(f" [A] GROUND TRUTH FACT:")
    print(f"     {ground_truth}")
    print(f"------------------------------------------------------")
    print(f" [1] TRACK 1: NAIVE RAG")
    print(f"     System Output: {naive_answer}")
    print(f"     LLM Judge:     {naive_eval}")
    print(f"     Verdict:       {naive_status}")
    print(f"------------------------------------------------------")
    print(f" [2] TRACK 2: GOV-RAG")
    print(f"     System Output: {gov_answer}")
    print(f"     LLM Judge:     {gov_eval}")
    print(f"     Verdict:       {gov_status}")
    print(f"======================================================\n")

    # --- STEP 5: SAVE TO MASTER LOG ---
    eval_record = {
        "Record_ID": target_record_id.upper(),
        "Condition": "Positive" if flag == 'P' else "Negative",
        "Ground_Truth": ground_truth,
        "Naive_Answer": naive_answer,
        "Naive_Eval": naive_eval,
        "Naive_Verdict": naive_status,
        "GovRAG_Answer": gov_answer,
        "GovRAG_Eval": gov_eval,
        "GovRAG_Verdict": gov_status
    }
    
    df_new = pd.DataFrame([eval_record])
    if os.path.exists(MASTER_EVAL_LOG):
        df_existing = pd.read_csv(MASTER_EVAL_LOG)
        df_existing = df_existing[df_existing['Record_ID'].str.lower() != target_record_id] 
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_final = df_new

    df_final.to_csv(MASTER_EVAL_LOG, index=False, encoding='utf-8-sig')
    print(f"   [Master Log Updated]: {MASTER_EVAL_LOG}")

if __name__ == "__main__":
    run_unified_pipeline()