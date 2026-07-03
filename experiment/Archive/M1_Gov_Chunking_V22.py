# --------------------------------------------------------------------------
# MODULE 1: Forensic Governed Partitioning (M1_V2.2.1)
# GOAL: Strip Inquiry Context and Partition Evidence using D5.jsonl
# --------------------------------------------------------------------------
import pandas as pd
import json
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup and Environment ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    sys.exit("[CRITICAL ERROR] API Key not found in .env.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-2.0-flash-lite"

# UPDATED: Corrected path to .jsonl as per your manifest format
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MANIFEST = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")

def domain_contextual_partitioner(text: str, profile: list, z_score: float) -> list:
    """Slices the 'Document' portion while ignoring the 'Question' section."""
    
    # 1. Forensic Stripping: Isolate Document Evidence 
    # Source text format: "Question: ... | Document: ..."
    if " | Document: " in text:
        parts = text.split(" | Document: ", 1)
        inquiry_context = parts[0]
        evidence_text = parts[1]
    else:
        inquiry_context = "General Discovery"
        evidence_text = text

    # 2. Map Weighted Governance Profile [cite: 8, 12, 24]
    primary_gov = max(profile, key=lambda x: x['affinity_weight'])
    rules = primary_gov["rules"]
    depth = rules.get("search_exit_depth", 4) # [cite: 18]

    prompt = f"""
    You are a Strategic Data Architect. 
    INQUIRY CONTEXT: {inquiry_context}
    TASK: Partition the <EVIDENCE_TEXT> into exactly {depth} semantic 'Knowledge Pockets'.
    
    GOVERNANCE CONSTRAINTS:
    - Primary Domain: {primary_gov['domain']}
    - Mandatory Verbs: {rules.get('relational_predicates', [])}
    - Disambiguation: {rules.get('disambiguation_keys', {})}
    
    CRITICAL: Output ONLY a JSON array of strings containing the RAW LITERAL evidence text.
    Do not include the inquiry question in the results.
    
    <EVIDENCE_TEXT>
    {evidence_text}
    </EVIDENCE_TEXT>
    """
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL, 
            contents=[prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f" [ERROR] Partitioning failed: {e}")
        return [evidence_text]

def run_m1_v221():
    if not os.path.exists(INPUT_MANIFEST):
        sys.exit(f"[CRITICAL ERROR] Manifest missing at: {INPUT_MANIFEST}")

    final_chunks = []
    with open(INPUT_MANIFEST, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            contract = json.loads(line)
            rid = contract["record_id"]
            z_score = contract.get("z_score", 0.0) # [cite: 6, 7]
            profile = contract["governance_profile"] # 
            
            pockets = domain_contextual_partitioner(contract["source_text"], profile, z_score)
            
            # Map back to primary gov for metadata persistence [cite: 21, 25]
            primary_gov = max(profile, key=lambda x: x['affinity_weight'])
            
            for j, pocket_text in enumerate(pockets):
                final_chunks.append({
                    "record_id": rid,
                    "chunk_id": f"CHNK_{i:04d}_{j:02d}",
                    "domain": primary_gov["domain"],
                    "chunk_text": pocket_text,
                    "wa_score": primary_gov["affinity_weight"], # [cite: 12]
                    "z_score": z_score, # [cite: 6]
                    "predicates": json.dumps(primary_gov["rules"].get("relational_predicates", [])), # [cite: 17]
                    "depth_limit": primary_gov["rules"].get("search_exit_depth", 4) # [cite: 18]
                })
            print(f"Processed Record {i+1} | {rid} | Chunks: {len(pockets)}")

    # Export Artifact for M2 Extraction 
    pd.DataFrame(final_chunks).to_csv(OUTPUT_FILE, index=False)
    print("\n" + "="*50 + "\nM1_V2.2.1: FORENSIC INGESTION COMPLETE\n" + "="*50)

if __name__ == "__main__":
    run_m1_v221()