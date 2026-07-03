# --------------------------------------------------------------------------
# MODULE 2: M2_Gov_Extraction_V4.py
# ARCHITECTURE: Adaptive Weighted Extraction + Dynamic Heuristic Interceptor
# UPGRADE: Removed all hardcoded domain logic. 100% Data-Driven.
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
import time
import re  # Required for Regex
import ast
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key: print("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-3-flash-preview"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Extracted_Triples.json")
DISCOVERY_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Discovery_Registry.json")

telemetry = {
        "api_calls": 0,
        "total_prompt_tokens": 0,
        "total_comp_tokens": 0,
        "total_time": 0.0
    }

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

# --- 2. Dynamic Heuristic Interceptor (THE FIX) ---
def heuristic_entity_rescue(text, record_id, domain, existing_triples):
    """
    Scavenges for Quoted Entities (Titles, Acts, Code Names) missed by LLM.
    PURELY DYNAMIC: Adapts to any domain by using the input 'domain' variable.
    """
    new_triples = []
    
    # 1. Regex for Quoted Strings (Structural Detection)
    # Catches: "Portraits and Prayers", "Income Tax Act", "Apollo 13"
    patterns = [r'"([^"]+)"', r"'([^']+)'"]
    
    for pat in patterns:
        matches = re.findall(pat, text)
        for entity in matches:
            # Noise Filter: Ignore tiny words (e.g., 'the') or huge blobs
            if len(entity) < 3 or len(entity) > 75: continue
            
            # Smart Filter: Check for capitalization. 
            # Entities usually have at least one Capital Letter (e.g. "The Raven" vs "the raven")
            # This reduces false positives like "a lot of people".
            if not any(char.isupper() for char in entity):
                continue

            # Deduplication: Don't add if LLM already found it
            if any(t['subject'] == entity or t['object'] == entity for t in existing_triples):
                continue

            # 2. Dynamic Typing (No Hardcoding)
            # We construct the Class Type from the Domain itself.
            # e.g., Domain="Taxation" -> Type="Taxation_Artifact"
            clean_domain = domain.replace(" ", "_")
            dynamic_type = f"{clean_domain}_Artifact"

            # 3. Create Weighted Triples
            # Triple A: Type Definition
            new_triples.append({
                "subject": entity,
                "predicate": "is_type_of",
                "object": dynamic_type, # Dynamic
                "extraction_mode": "HEURISTIC" 
            })
            
            # Triple B: Governance Anchor
            new_triples.append({
                "subject": entity,
                "predicate": "belongs_to_domain",
                "object": domain, # Dynamic
                "extraction_mode": "GOVERNANCE"
            })

    return existing_triples + new_triples

# --- 3. Adaptive Extraction Logic ---
def call_extraction(text: str, domain: str, predicates: list, definitions: dict, mode: str) -> list:
    if mode == "STRICT":
        constraint = f"STRICTLY usage ONLY these verbs: {predicates}. If a relationship exists but uses a different verb, IGNORE IT."
    else:
        constraint = "DISCOVERY MODE: The strict vocabulary failed. Extract relationships using natural language verbs."

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
        start_time = time.time() # Track network latency
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", 
                response_schema=OUTPUT_SCHEMA,
                temperature=0.1
            ),
        )
        # --- UPDATE TELEMETRY HERE ---
        telemetry['api_calls'] += 1
        telemetry['total_time'] += (time.time() - start_time)
        
        # Accessing token counts from the Gemini response metadata
        if response.usage_metadata:
            telemetry['total_prompt_tokens'] += response.usage_metadata.prompt_token_count
            telemetry['total_comp_tokens'] += response.usage_metadata.candidates_token_count

        return json.loads(response.text)
    except Exception as e:
        print(f"   [API Error - {mode}] {e}") # Let's see the errors!    
        return []

# --- 4. Main Execution Loop ---
def run_m2_v3_adaptive():
    if not os.path.exists(INPUT_FILE):
        print(f"Missing Input: {INPUT_FILE}")
        return

    print(f"M2_V4.0: Adaptive Extraction + Dynamic Heuristic...")
    df = pd.read_csv(INPUT_FILE)
    
    all_triples = []
    discovery_registry = []
    
    stats = {"strict_hits": 0, "discovery_hits": 0, "heuristic_hits": 0, "total_edges": 0}

    for index, row in df.iterrows():
        try:
            preds = json.loads(row['predicates']) if isinstance(row['predicates'], str) else []
            defs = json.loads(row['disambiguation']) if isinstance(row['disambiguation'], str) else {}
        except:
            preds = []
            defs = {}

        # TIER 1: STRICT GOVERNANCE
        triples = call_extraction(row['chunk_text'], row['viewpoint_domain'], preds, defs, mode="STRICT")
        extraction_mode = "STRICT"
        
        # TIER 2: ADAPTIVE DISCOVERY (Logic Fix: Run if result is sparse)
        if (not triples or len(triples) < 2) and row['wa_score'] > 0.35: 
            discovery_triples = call_extraction(row['chunk_text'], row['viewpoint_domain'], preds, defs, mode="DISCOVERY")
            if discovery_triples:
                triples.extend(discovery_triples)
                extraction_mode = "HYBRID" 

        # --- TIER 3: DYNAMIC HEURISTIC INTERCEPTOR ---
        # Pass the dynamic 'viewpoint_domain' to the function
        count_before = len(triples)
        triples = heuristic_entity_rescue(
            row['chunk_text'], 
            row['record_id'], 
            row['viewpoint_domain'], # <--- Passes "Taxation", "Literary", etc.
            triples
        )
        count_after = len(triples)
        
        if count_after > count_before:
            stats["heuristic_hits"] += (count_after - count_before)

        # Processing Results
        if triples:
            if extraction_mode == "STRICT": stats["strict_hits"] += 1
            elif extraction_mode == "DISCOVERY": stats["discovery_hits"] += 1

            for t in triples:
                t.update({
                    'record_id': row['record_id'],
                    'chunk_id': row['chunk_id'],
                    'domain': row['viewpoint_domain'],
                    'weight': row['wa_score'],
                    'extraction_mode': t.get('extraction_mode', extraction_mode),
                    'granularity': row['granularity_level']
                })
                all_triples.append(t)

                if t.get('extraction_mode') == "DISCOVERY":
                    discovery_registry.append({
                        "domain": row['viewpoint_domain'],
                        "found_predicate": t['predicate'],
                        "context_snippet": row['chunk_text'][:100]
                    })
        
        #if index % 10 == 0: print(f"Processed {index} chunks...")
        found_count = len(triples)
        print(f"[{index+1}/{len(df)}] Processed {row['chunk_id']} | Mode: {extraction_mode} | Triples Found: {found_count}")

    # --- 5. Artifact Persistence ---
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_triples, f, indent=2)
        
    with open(DISCOVERY_FILE, 'w', encoding='utf-8') as f:
        json.dump(discovery_registry, f, indent=2)

    print("\n" + "="*60)
    print("M2_V4.0 COMPLETE: TELEMETRY & EXTRACTION REPORT")
    print("="*60)
    print(f"Total API Calls Made:    {telemetry['api_calls']}")
    print(f"Total API Network Time:  {telemetry['total_time']:.2f} seconds")
    print(f"Total Prompt Tokens:     {telemetry['total_prompt_tokens']:,}")
    print(f"Total Completion Tokens: {telemetry['total_comp_tokens']:,}")
    print("-" * 60)
    print(f"Total Weighted Edges:    {len(all_triples)}")
    print(f"Strict Mode Hits:        {stats['strict_hits']} chunks")
    print(f"Hybrid/Discovery Hits:   {stats['discovery_hits']} chunks")
    print(f"Heuristic Rescues:       {stats['heuristic_hits']} (Quoted Artifacts Saved)")
    print(f"Primary Artifact:        {OUTPUT_FILE}")

if __name__ == "__main__":
    run_m2_v3_adaptive()