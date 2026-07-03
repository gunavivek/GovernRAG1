# --------------------------------------------------------------------------
# MODULE 2: M2_Gov_Extraction_V3.py
# ARCHITECTURE: Adaptive Weighted Extraction (Poly-Ontological + Discovery)
# DISSERTATION GOAL: Extract Weighted Triples & Identify Ontology Gaps
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
import time
import ast
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key: print("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-2.0-flash-lite"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Extracted_Triples.json")
DISCOVERY_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Discovery_Registry.json")

# --- 1. Schema Definition ---
OUTPUT_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    description="List of semantic triples.",
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

# --- 2. Adaptive Extraction Logic ---
def call_extraction(text: str, domain: str, predicates: list, definitions: dict, mode: str) -> list:
    """
    Executes extraction based on the mode:
    - 'STRICT': Enforces the predicate list perfectly.
    - 'DISCOVERY': Allows natural language verbs (for gap analysis).
    """
    if mode == "STRICT":
        constraint = f"STRICTLY usage ONLY these verbs: {predicates}. If a relationship exists but uses a different verb, IGNORE IT."
    else:
        constraint = "DISCOVERY MODE: The strict vocabulary failed. Extract relationships using natural language verbs that best describe the connection."

    prompt = f"""
    You are a Knowledge Engineer for the {domain} domain.
    TASK: Extract Subject-Predicate-Object triples.
    
    GOVERNANCE RULES:
    1. CONTEXT: {constraint}
    2. DEFINITIONS: Resolve entity ambiguity using: {definitions}.
    3. ATOMICITY: Subjects/Objects must be specific named entities.
    
    <TEXT>
    {text}
    </TEXT>
    """

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", 
                response_schema=OUTPUT_SCHEMA,
                temperature=0.1 # Deterministic
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        # print(f"   [Log] Extraction skip ({mode}): {e}")
        return []

# --- 3. Main Execution Loop ---
def run_m2_v3_adaptive():
    if not os.path.exists(INPUT_FILE):
        print(f"Missing Input: {INPUT_FILE}")
        return

    print(f"M2_V3.0: Starting Adaptive Weighted Extraction...")
    df = pd.read_csv(INPUT_FILE)
    
    all_triples = []
    discovery_registry = []
    
    # Metrics
    stats = {"strict_hits": 0, "discovery_hits": 0, "total_edges": 0}

    for index, row in df.iterrows():
        # Parse metadata
        try:
            preds = json.loads(row['predicates']) if isinstance(row['predicates'], str) else []
            defs = json.loads(row['disambiguation']) if isinstance(row['disambiguation'], str) else {}
        except:
            preds = []
            defs = {}

        # TIER 1: STRICT GOVERNANCE
        triples = call_extraction(row['chunk_text'], row['viewpoint_domain'], preds, defs, mode="STRICT")
        extraction_mode = "STRICT"
        
        # TIER 2: ADAPTIVE DISCOVERY (Safety Net)
        # We only trigger discovery if Strict failed AND the text is actually relevant (High Wa)
        # This prevents hallucinating on low-quality chunks.
        if not triples and row['wa_score'] > 0.35: 
            triples = call_extraction(row['chunk_text'], row['viewpoint_domain'], preds, defs, mode="DISCOVERY")
            extraction_mode = "DISCOVERY"

        # Processing Results
        if triples:
            if extraction_mode == "STRICT": stats["strict_hits"] += 1
            else: stats["discovery_hits"] += 1

            for t in triples:
                # STAPLE PROVENANCE & WEIGHTS
                t.update({
                    'record_id': row['record_id'],
                    'chunk_id': row['chunk_id'],
                    'domain': row['viewpoint_domain'],
                    'weight': row['wa_score'],          # <--- The dissertation Key
                    'extraction_mode': extraction_mode,
                    'granularity': row['granularity_level']
                })
                all_triples.append(t)

                # Feedback Loop: If Discovery Mode, log for D1 updates
                if extraction_mode == "DISCOVERY":
                    discovery_registry.append({
                        "domain": row['viewpoint_domain'],
                        "found_predicate": t['predicate'],
                        "context_snippet": row['chunk_text'][:100]
                    })
        
        # Simple progress log
        if index % 10 == 0: print(f"Processed {index} chunks...")

    # --- 4. Artifact Persistence ---
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_triples, f, indent=2)
        
    with open(DISCOVERY_FILE, 'w', encoding='utf-8') as f:
        json.dump(discovery_registry, f, indent=2)

    print("\n" + "="*50)
    print("M2_V3.0 COMPLETE (Adaptive Poly-Ontological)")
    print("="*50)
    print(f"Total Weighted Edges:   {len(all_triples)}")
    print(f"Strict Compliance:      {stats['strict_hits']} chunks")
    print(f"Discovery Fallback:     {stats['discovery_hits']} chunks")
    print(f"Ontology Gaps Found:    {len(discovery_registry)} (Saved to Registry)")
    print(f"Primary Artifact:       {OUTPUT_FILE}")

if __name__ == "__main__":
    run_m2_v3_adaptive()