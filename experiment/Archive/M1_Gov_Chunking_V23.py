# --------------------------------------------------------------------------
# MODULE 1: M1_Gov_Chunking_V23.py
# DISSERTATION HYPOTHESIS 1: Concept-Enhanced Ingestion
# GOAL: Transform ICD Manifest into Governed Semantic Pockets
# --------------------------------------------------------------------------
import pandas as pd
import json
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Dissertation Environment Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.exit("[CRITICAL DISSERTATION ERROR] API Key missing. Governance Layer offline.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-2.0-flash-lite"

# Paths aligned to your project structure
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MANIFEST = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")

def governance_driven_partitioner(text: str, profile: list, z_score: float, record_id: str) -> list:
    """
    Implements the 'Concept-Enhanced' Logic defined in the ICD.
    Maps D5 metadata directly to partitioning constraints.
    """
    
    # --- ICD KEY 3 (Context): Forensic Stripping ---
    # Proposal p.3: Eliminate Inquiry Bias. We only chunk the Document.
    if " | Document: " in text:
        evidence_text = text.split(" | Document: ", 1)[1]
    else:
        evidence_text = text # Fallback for pure document records

    # --- ICD KEY 1 (Control): Salience Steering via Affinity Weight ---
    # We select the domain with the highest Wa to rule this session.
    primary_gov = max(profile, key=lambda x: x['affinity_weight'])
    rules = primary_gov["rules"]
    domain_name = primary_gov["domain"]

    # --- ICD KEY 1 (Control): Statistical Triage via Z-Score ---
    # Proposal p.3: Dynamic handling of enterprise data.
    if z_score >= 2.5:
        mode = "EXPLORATORY DISCOVERY (High Novelty)"
        instruction = "The text contains novel concepts. Capture broader context around the predicates."
    else:
        mode = "STRICT GOVERNANCE (Standard BIZBOK)"
        instruction = "Adhere strictly to the predicates. Do not infer relationships outside the vocabulary."

    # --- ICD KEY 1 (Control): Deterministic Density via Search Exit Depth ---
    # Proposal p.14: Complexity Control.
    target_pockets = rules.get("search_exit_depth", 4)

    # --- ICD KEY 1 (Control): Semantic Anchors via Relational Predicates ---
    # Proposal p.5: Concept-Enhanced extraction foundation.
    predicates = rules.get("relational_predicates", [])

    # --- ICD KEY 2 (Context): Node Integrity via Disambiguation ---
    # Proposal p.5: Hallucination Reduction (Graph Aliasing).
    disambiguation = rules.get("disambiguation_keys", {})

    # --- The "Work Order" Prompt ---
    prompt = f"""
    You are a Strategic Data Architect for the {domain_name} Industry.
    OPERATIONAL MODE: {mode}
    
    TASK: Partition the <EVIDENCE_TEXT> into exactly {target_pockets} semantic 'Knowledge Pockets'.
    
    GOVERNANCE INSTRUCTIONS (D5 Contract):
    1. {instruction}
    2. SEMANTIC ANCHORS: Cut the text where these specific relationships conclude: {predicates}.
    3. AMBIGUITY SHIELD: Ensure these terms retain their specific definition: {disambiguation}.
    
    CRITICAL OUTPUT RULES:
    - Return exactly {target_pockets} text segments.
    - CONTENT MUST BE RAW LITERAL STRINGS from the evidence. Do not summarize.
    - Do not include the user question.
    - Format: JSON Array of strings.
    
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
        print(f" [ERROR] Partitioning failed for Record {record_id}: {e}")
        # Fallback: Return the whole text as 1 chunk (Preserves data, fails gracefully)
        return [evidence_text]

def run_m1_v23():
    if not os.path.exists(INPUT_MANIFEST):
        sys.exit(f"[CRITICAL] Manifest not found at {INPUT_MANIFEST}")

    final_chunks = []
    print(f"M1_V2.3: Initializing Concept-Enhanced Ingestion from {INPUT_MANIFEST}...")

    with open(INPUT_MANIFEST, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            contract = json.loads(line)
            
            # --- ICD KEY 3 (Traceability): Record ID ---
            rid = contract["record_id"]
            z_score = contract.get("z_score", 0.0)
            
            # Execute Governed Partitioning
            pockets = governance_driven_partitioner(
                contract["source_text"], 
                contract["governance_profile"], 
                z_score,
                rid
            )
            
            # Metadata Stapling (Persisting the "Golden Thread" for M9 Auditor)
            primary_gov = max(contract["governance_profile"], key=lambda x: x['affinity_weight'])
            
            for j, pocket_text in enumerate(pockets):
                final_chunks.append({
                    "record_id": rid,                          # Traceability
                    "chunk_id": f"CHNK_{rid[-4:]}_{j:02d}",    # Unique Semantic ID
                    "domain": primary_gov["domain"],           # Context
                    "chunk_text": pocket_text,                 # The Evidence
                    "wa_score": primary_gov["affinity_weight"],# Salience
                    "z_score": z_score,                        # Entropy
                    "predicates": json.dumps(primary_gov["rules"].get("relational_predicates", [])),
                    "disambiguation": json.dumps(primary_gov["rules"].get("disambiguation_keys", {})),
                    "depth_limit": primary_gov["rules"].get("search_exit_depth", 4)
                })
            
            print(f"Record {rid} | {primary_gov['domain']} | Mode: {'Discovery' if z_score>=2.5 else 'Governance'} | Chunks: {len(pockets)}")

    # Export Artifact
    df = pd.DataFrame(final_chunks)
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "="*60)
    print(f"M1_V2.3 COMPLETE: Generated {len(final_chunks)} Governed Semantic Pockets.")
    print(f"Artifact Saved: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    run_m1_v23()