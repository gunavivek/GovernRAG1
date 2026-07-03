# --------------------------------------------------------------------------
# MODULE 2: Governed Relationship Extraction (M2_V2.1)
# STRATEGY: Atomic Ingestion & Provenance Stapling
# GOAL: Create metadata-rich triples to feed the M3 Provenance-Aware Graph.
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
import time
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup and Configuration ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
LLM_MODEL = "gemini-2.0-flash-lite" 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Extracted_Triples.json")

# --- 1. Output Schema Definition ---
OUTPUT_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    description="List of knowledge triples mapped to the governed schema.",
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

# --- 2. Extraction Function ---
def governed_extraction(text: str, domain: str, predicates: str, glossary: str):
    system_instruction = f"""
    You are a Governed Extraction Agent specializing in the {domain} domain.
    TASK: Extract Subject-Predicate-Object (S-P-O) triples from the text.
    
    STRICT CONSTRAINTS:
    1. ALLOWED PREDICATES: {predicates}. ONLY use verbs from this list.
    2. GLOSSARY: Use these standard labels for entities: {glossary}.
    3. If a relationship is ambiguous, DISCARD it.
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
        print(f"  [ERROR] LLM Failure: {e}")
        return []

# --- 3. Main Execution (Atomic Ingestion Pattern) ---
if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input missing: {INPUT_FILE}")
        exit(1)

    df_chunks = pd.read_csv(INPUT_FILE)
    all_governed_triples = []
    
    print(f"--- M2_V2.1: Extracting from {len(df_chunks)} atomic chunks ---")
    start_time = time.time()

    for idx, row in df_chunks.iterrows():
        print(f"Processing Chunk: {row['chunk_id']}")
        
        # LLM Extraction
        triples = governed_extraction(
            row['chunk_text'], 
            row['domain'], 
            row['predicates'], 
            row['glossary']
        )
        
        # PROVENANCE STAPLING: The Golden Thread
        # We ensure every triple carries its specific origin metadata
        for triple in triples:
            triple['record_id'] = row['record_id']
            triple['source_chunk_id'] = row['chunk_id']
            triple['domain'] = row['domain']
            triple['confidence_score'] = 90 # Initial extraction confidence
            all_governed_triples.append(triple)
        
        time.sleep(1.0) # Rate limit management

    # Save Layer 3 Artifact
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_governed_triples, f, indent=2)

    print(f"\n[SUCCESS] M2_V2.1 Complete. {len(all_governed_triples)} triples saved.")