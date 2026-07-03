# --------------------------------------------------------------------------
# MODULE 1: M1_Gov_Chunking_V3.py
# ARCHITECTURE: Poly-Ontological Layering (Salience-Gated)
# DISSERTATION HYPOTHESIS 3: Interoperability via Multi-Pass Ingestion
# --------------------------------------------------------------------------
import pandas as pd
import json
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key: sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-2.0-flash-lite"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MANIFEST = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Layered_Chunks.csv")

# TUNABLE PARAMETER: Salience Threshold for Layering
# Domains within 0.20 of the primary Wa are considered "Active Views"
SALIENCE_THRESHOLD = 0.20 

def single_domain_partitioner(evidence_text: str, specific_domain_rule: dict, z_score: float) -> list:
    """
    Partitions text using a SINGLE ontological lens (Viewpoint).
    Integrates V2.3 Z-Score Triage with V2.5 Adaptive Density.
    """
    domain_name = specific_domain_rule['domain']
    rules = specific_domain_rule['rules']
    
    # --- GOVERNANCE CONTROLS ---
    target_pockets = rules.get("search_exit_depth", 4)
    predicates = rules.get("relational_predicates", [])
    disambiguation = rules.get("disambiguation_keys", {})
    
    # --- ADAPTIVE CEILING (V2.5 Upgrade) ---
    # Prevents forcing tiny texts into 4 chunks (Improvement over V2.3)
    if len(evidence_text) < 400: 
        target_pockets = 1
        density_instruction = "Treat this as a single atomic unit."
    else:
        density_instruction = f"Create NO MORE THAN {target_pockets} pockets."

    # --- Z-SCORE TRIAGE (Retained from V2.3) ---
    if z_score >= 2.5:
        mode = "EXPLORATORY DISCOVERY (High Novelty)"
        instruction = "The text contains novel concepts. Capture broader context around the predicates."
    else:
        mode = "STRICT GOVERNANCE (Standard BIZBOK)"
        instruction = "Adhere strictly to the predicates. Do not infer relationships outside the vocabulary."

    prompt = f"""
    You are a Data Architect strictly representing the {domain_name} Industry.
    OPERATIONAL MODE: {mode}
    
    TASK: Partition the <EVIDENCE_TEXT> into 'Knowledge Pockets'.
    
    STRICT ONTOLOGICAL VIEW:
    1. LENS: Focus ONLY on concepts relevant to {domain_name}.
    2. INSTRUCTION: {instruction}
    3. DEFINITIONS: Use these keys to define boundaries: {disambiguation}.
    4. ANCHORS: Cut text where these predicates conclude: {predicates}.
    5. LIMIT: {density_instruction}
    
    <EVIDENCE_TEXT>
    {evidence_text}
    </EVIDENCE_TEXT>
    
    OUTPUT: JSON Array of strings. Raw text only.
    """
    try:
        response = client.models.generate_content(
            model=LLM_MODEL, 
            contents=[prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1),
        )
        return json.loads(response.text)
    except:
        return [evidence_text]

def run_m1_v3_layering():
    if not os.path.exists(INPUT_MANIFEST): sys.exit("Manifest missing.")
    
    final_chunks = []
    print(f"M1_V3.0: Initializing Poly-Ontological Layering (Threshold={SALIENCE_THRESHOLD})...")

    with open(INPUT_MANIFEST, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            contract = json.loads(line)
            rid = contract["record_id"]
            z_score = contract.get("z_score", 0.0)
            
            # 1. Forensic Stripping (Retained from V2.3)
            text = contract["source_text"]
            evidence = text.split(" | Document: ", 1)[1] if " | Document: " in text else text

            # 2. Identify "Compatible" Domains for Layering
            sorted_domains = sorted(contract["governance_profile"], key=lambda x: x['affinity_weight'], reverse=True)
            primary_wa = sorted_domains[0]['affinity_weight']
            
            # Dissertation Logic: Layering is gated by Salience Threshold
            active_views = [d for d in sorted_domains if (primary_wa - d['affinity_weight']) <= SALIENCE_THRESHOLD]

            # 3. LAYERED EXECUTION LOOP (The V3.0 Delta)
            for view in active_views:
                domain_name = view['domain']
                wa = view['affinity_weight']
                
                # Execute Partitioning for this specific View
                pockets = single_domain_partitioner(evidence, view, z_score)
                
                # Staple Metadata & Generate View-Specific IDs
                for j, pocket_text in enumerate(pockets):
                    # Clean domain name for ID (e.g., "Higher Education" -> "HIGHER_ED")
                    safe_dom = domain_name.upper().replace(" ", "_").replace("&", "AND")[:15]
                    
                    final_chunks.append({
                        "record_id": rid,
                        # UNIQUE ID for graph separation:
                        "chunk_id": f"CHNK_{rid[-4:]}_{safe_dom}_{j:02d}",
                        "viewpoint_domain": domain_name,
                        "chunk_text": pocket_text,
                        "wa_score": wa,
                        "z_score": z_score,
                        # Staple the SPECIFIC rules used for this cut:
                        "predicates": json.dumps(view["rules"].get("relational_predicates", [])),
                        "disambiguation": json.dumps(view["rules"].get("disambiguation_keys", {})),
                        "depth_limit": view["rules"].get("search_exit_depth", 4)
                    })
                
                print(f"Record {rid} | Layer: {domain_name} (Wa:{wa}) | Chunks: {len(pockets)}")

    # Export Layered Artifact
    pd.DataFrame(final_chunks).to_csv(OUTPUT_FILE, index=False)
    print("\n" + "="*60)
    print(f"M1_V3.0 COMPLETE. Layered Artifact Saved: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    run_m1_v3_layering()