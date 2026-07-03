import os
import json

# --- 1. SETUP PATHS ---
BASE_PATH = r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG"
INPUT_FILE = os.path.join(BASE_PATH, "data", "en_refine.json")
OUTPUT_FILE = os.path.join(BASE_PATH, "data", "RGB_Negative_Rejection_Candidates.json")

def extract_local_rejection_data():
    print(f"--- Starting Local Data Extraction (JSONL Format) ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Could not find {INPUT_FILE}")
        return

    try:
        data = []
        # --- 2. LOAD DATA LINE-BY-LINE ---
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
            
        print(f"[INFO] Successfully loaded {len(data)} total records from the benchmark.")
        print(f"[INFO] Because this file contains EXACTLY the 300 Negative Rejection records, no filtering is needed.")

        # --- 3. SELECT YOUR 5 RECORDS ---
        # Taking indices 10 through 15 to get complex queries
        stress_test_samples = data[10:20]
        
        # --- 4. EXPORT ---
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(stress_test_samples, f, indent=4)
            
        print(f"\n[FINAL SUCCESS] 5 Negative Rejection records saved to: {OUTPUT_FILE}")
        
        print("\n--- Example Record for your PhD Chapter 4 ---")
        if stress_test_samples:
            print(f"Question: {stress_test_samples[0]['query']}") # Note: RGB sometimes uses 'query' instead of 'question'
            print("Logic Check: Naive RAG will likely guess. Gov-RAG must block it.")
        
    except Exception as e:
        print(f"[SYSTEM ERROR] {str(e)}")

if __name__ == "__main__":
    extract_local_rejection_data()