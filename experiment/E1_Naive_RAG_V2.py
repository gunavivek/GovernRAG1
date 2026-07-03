import os
import json
import time
import pandas as pd
from google import genai
from google.genai import types

# --- 1. PATH SETUP ---
BASE_PATH = r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG"
# Use the same manifest you used for Q1
INPUT_FILE = os.path.join(BASE_PATH, "output", "D5_Extraction_Manifest.jsonl")
OUTPUT_FILE = os.path.join(BASE_PATH, "output", "NAIVE_RAG_BASELINE_RESULTS.csv")

# --- 2. CONFIGURATION ---
MODEL_ID = "gemma-3-4b-it" # Use the SAME model as Q5
#MODEL_ID = "gemini-3-flash-preview" # Alternative model
api_key = os.getenv("GEMINI_API_KEY") 
client = genai.Client(api_key=api_key)

def run_naive_baseline_comparison():
    print(f"--- Starting Baseline Track: Naive RAG with {MODEL_ID} ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Could not find {INPUT_FILE}")
        return

    results = []

    # --- 3. EXECUTION LOOP ---
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for index, line in enumerate(f):
            data = json.loads(line)
            record_id = data.get('record_id')
            
            # Extract question and the RAW text (unstructured context)
            source_text = data.get("source_text", "")
            # Split to get just the Question and the Document content
            parts = source_text.split("| Document:")
            question = parts[0].replace("Question:", "").strip()
            document_context = parts[1].strip() if len(parts) > 1 else source_text

            print(f"[{index+1}] Naive Baseline Processing: {record_id}")
            
            # THE NAIVE PROMPT (No Governance, No Triples, No Rules)
            prompt = (
                f"Instructions: Answer the following question based ONLY on the context provided.\n\n"
                f"Context: {document_context}\n\n"
                f"Question: {question}"
            )
            
            try:
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.0)
                )
                naive_answer = response.text.strip()
            except Exception as e:
                naive_answer = f"ERROR: {str(e)}"
            
            # --- ---- Print output to the terminal ---
            print(f"  -> Question: {question}")
            print(f"  -> Naive Answer: {naive_answer}\n")
            # -----------------------------------------

            results.append({
                "Record_ID": record_id,
                "Question": question,
                "Naive_Answer": naive_answer
            })
            
            time.sleep(2.0) # Respect API limits

    # --- 4. SAVE RESULTS ---
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n[SUCCESS] Baseline results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_naive_baseline_comparison()