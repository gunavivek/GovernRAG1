import os
import pandas as pd
import time
from google import genai
from google.genai import types

# --- 1. ABSOLUTE PATH SETUP ---
BASE_PATH = r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG"
INPUT_FILE = os.path.join(BASE_PATH, "data", "Concept Gov RAG_Results_Jan2026.csv")
OUTPUT_FILE = os.path.join(BASE_PATH, "output", "Naive_RAG_Results.csv")

# --- 2. CONFIGURATION ---
# Using the specific versioned model name often resolves 404s in v1beta/v1 mismatches
MODEL_ID = "gemini-3-flash-preview"
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def run_naive_rag_baseline():
    print(f"--- Starting Baseline Track: Naive RAG ---")
    
    # Validation of file existence
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] File not found at {INPUT_FILE}")
        return

    # Load with encoding fix
    try:
        df = pd.read_csv(INPUT_FILE, encoding='ISO-8859-1')
    except:
        df = pd.read_csv(INPUT_FILE, encoding='cp1252')

    baseline_answers = []
    
    # 3. DETERMINISTIC EXECUTION (Auditability Anchor)
    for index, row in df.iterrows():
        question = row['Question']
        document = row['Document']
        record_id = row['Record ID']
        
        print(f"[{index+1}/10] Baseline Processing: {record_id}")
        
        # Standard Naive RAG Prompt
        prompt = f"Context: {document}\n\nQuestion: {question}\n\nAnswer using only the context provided."
        
        try:
            # temperature=0.0 is your PhD "Consistency" requirement
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            baseline_answers.append(response.text.strip())
        except Exception as e:
            print(f"Error on {record_id}: {e}")
            baseline_answers.append(f"[ERROR_GENERATING]: {e}")
            
        time.sleep(1.0) # Rate limit safety

    # 4. CAPTURE & EXPORT
    df['Baseline_Flash_Answer'] = baseline_answers
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n[FINAL SUCCESS] Baseline results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_naive_rag_baseline()