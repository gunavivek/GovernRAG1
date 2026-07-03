# --------------------------------------------------------------------------
# MODULE 2: Adaptive Governed Extraction (M2_V2.2)
# VERSION: 2.2 (Circular Loopback & Tiered Discovery)
# GOAL: Rebuildable forensic extraction with zero-loss record retention.
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
import time
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
LLM_MODEL = "gemini-2.0-flash-lite" 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Extracted_Triples.json")
DISCOVERY_FILE = os.path.join(PROJECT_ROOT, "output", "M2_discovered_concepts.json")

# --- 1. Schema Definition (Strict Type Enforcement) ---
OUTPUT_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "subject": types.Schema(type=types.Type.STRING),
            "predicate": types.Schema(type=types.Type.STRING),
            "object": types.Schema(type=types.Type.STRING),
        },
        required=["subject", "predicate", "object"],
    )
)

# --- 2. Tiered Extraction Logic ---
def call_extraction(text, domain, predicates, glossary, mode="Governed"):
    """
    Tiered logic: 
    'Governed' mode uses strict manifest. 
    'Discovery' mode uses natural language predicates to prevent data loss.
    """
    if mode == "Governed":
        instruction = f"STRICT: ONLY use these predicates: {predicates}. Discard if no match."
    else:
        instruction = "DISCOVERY: If no governed predicate fits, use natural language verbs to capture the relationship."

    system_instruction = f"""
    You are a Business Architecture Extraction Agent for the {domain} domain.
    TASK: Extract Subject-Predicate-Object triples.
    CONSTRAINT: {instruction}
    GLOSSARY: Use these standard labels where applicable: {glossary}.
    """
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[text],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=OUTPUT_SCHEMA,
                temperature=0.1
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"  [CRITICAL ERROR] Extraction failed in {mode} mode: {e}")
        return []

# --- 3. Main Execution (The Atomic Ingestion Pattern) ---
if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] M1 Artifact not found at {INPUT_FILE}")
        exit(1)

    df_chunks = pd.read_csv(INPUT_FILE)
    all_triples = []
    discovery_registry = []
    
    print(f"--- M2_V2.2: Starting Adaptive Extraction Loop ---")

    for idx, row in df_chunks.iterrows():
        # TIER 1: Attempt Governed Extraction
        triples = call_extraction(row['chunk_text'], row['domain'], row['predicates'], row['glossary'], mode="Governed")
        
        # TIER 2: Failure Recovery (Discovery Mode)
        if not triples:
            print(f"  [!] Record {row['record_id']}: No Governed Triples. Triggering Discovery Mode.")
            triples = call_extraction(row['chunk_text'], row['domain'], row['predicates'], row['glossary'], mode="Discovery")
            mode_tag = "DiscoveryConcept"
        else:
            mode_tag = "GovernedConcept"

        # PROVENANCE STAPLING: Binding the Golden Thread
        for t in triples:
            t.update({
                'record_id': row['record_id'],
                'source_chunk_id': row['chunk_id'],
                'domain': row['domain'],
                'node_type': mode_tag,
                'extraction_mode': "Strict" if mode_tag == "GovernedConcept" else "Relaxed"
            })
            all_triples.append(t)
            
            # Populate DISCOVERY REGISTRY for D1 Feedback Loop
            if mode_tag == "DiscoveryConcept":
                discovery_registry.append({
                    "record_id": row['record_id'],
                    "suggested_predicate": t['predicate'],
                    "subject_sample": t['subject'],
                    "object_sample": t['object'],
                    "context": row['chunk_text'][:200]
                })
        
        time.sleep(1.0) # Rate limit mitigation

    # --- 4. Artifact Persistence ---
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_triples, f, indent=2)
    
    with open(DISCOVERY_FILE, 'w') as f:
        json.dump(discovery_registry, f, indent=2)

    print(f"\n[SUCCESS] M2_V2.2 Completed.")
    print(f"-> Total Triples: {len(all_triples)}")
    print(f"-> Discovery Candidates: {len(discovery_registry)} (Review for D1 Promotion)")