import json
import os
from typing import Dict, Any

# --- Project Paths (Aligned with D5 and Project Root) ---
PROJECT_ROOT = os.getcwd()
D5_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl") 
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "Q1_domain_router.jsonl")

def load_governance_registry_v22(manifest_path: str) -> Dict[str, str]:
    """
    Reads the V22 Poly-Ontological Manifest (Extraction Manifest).
    Resolves the Primary Domain by selecting the entry with the highest 
    affinity_weight, ensuring Symmetric Alignment between M and Q pipelines.
    """
    registry = {}
    if not os.path.exists(manifest_path):
        print(f"[Q1][ERROR] D5 Manifest not found at {manifest_path}. Pipeline blocked.")
        return {}

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                contract = json.loads(line)
                rid = contract.get("record_id")
                profile = contract.get("governance_profile", [])

                if rid and profile:
                    # Select the domain with the highest affinity_weight (H1: Standardization)
                    primary_entry = sorted(
                        profile, 
                        key=lambda x: x.get('affinity_weight', 0), 
                        reverse=True
                    )[0]
                    registry[rid] = primary_entry["domain"]
        
        print(f"[Q1][DEBUG] Loaded {len(registry)} governed contracts from D5.")
        return registry
    except Exception as e:
        print(f"[Q1][ERROR] Handshake Registry Load Failed: {e}")
        return {}

def align_governed_record(raw_data: Dict[str, Any], registry: Dict[str, str]) -> Dict[str, Any]:
    """
    Executes the Governed Handshake. 
    Tags the record with its engineered domain for downstream Q45 depth control.
    """
    # HotpotQA / RAGBench often use 'id' or '_id'
    rid = raw_data.get("id") or raw_data.get("_id")
    
    # Retrieve the 'Golden Thread' domain
    governed_domain = registry.get(rid)
    
    if governed_domain:
        confidence = 1.0
        status = "Bound"
        notes = f"Symmetric Handshake Successful: Bound to '{governed_domain}' via D5 Manifest."
    else:
        # Fallback for out-of-manifest records (Discovery Path)
        governed_domain = "General"
        confidence = 0.4
        status = "Unbound"
        notes = f"Handshake Failed: ID {rid} missing from D5. Defaulting to General."

    # Augment Record with Governance Metadata
    raw_data["primary_domain"] = governed_domain
    raw_data["governance_status"] = status
    raw_data["domains"] = [{ "name": governed_domain, "confidence": confidence }]
    raw_data["routing_notes"] = notes
    
    return raw_data

def main():
    print("--- Q1_v2: Governed Domain Aligner (D5 V22 Handshake) ---")
    
    # 1. Load the Governance Laws
    registry = load_governance_registry_v22(D5_MANIFEST_PATH)
    if not registry:
        return

    # 2. Open Files and Process Stream
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    processed_count = 0
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                
                raw_record = json.loads(line)
                
                # Perform the Deterministic Handshake
                governed_record = align_governed_record(raw_record, registry)
                
                # Write to the Q-Pipeline stream
                outfile.write(json.dumps(governed_record, ensure_ascii=False) + '\n')
                processed_count += 1

                if processed_count % 100 == 0:
                    print(f"[Q1_v2] Processed {processed_count} records...")

        print(f"--- SUCCESS: {processed_count} records aligned to D5 Manifest ---")
        print(f"Output saved to: {OUTPUT_FILE}")

    except FileNotFoundError:
        print(f"[Q1][ERROR] Raw input file not found at {INPUT_FILE}.")
    except Exception as e:
        print(f"[Q1][FATAL] Pipeline Error: {e}")

if __name__ == "__main__":
    main()