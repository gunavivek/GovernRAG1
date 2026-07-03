import json
import os
from typing import Dict, List

# --- Project Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_PATH = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")
D4_REGISTRY_PATH = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Discovered.json")
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl")
D5_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")

def run_d5_orchestration_v22():
    print("--- D5 V22: Orchestrating Poly-Ontological Extraction Contracts ---")
    
    # 1. Ingest Enriched D4 Governance Laws [cite: 24]
    with open(D4_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        d4_laws = json.load(f)
    
    # 2. Load Raw Data for context [cite: 22]
    with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
        raw_records = {json.loads(line)['id']: json.loads(line) for line in f}

    manifest_count = 0
    with open(D5_MANIFEST_PATH, 'w', encoding='utf-8') as f_out:
        # 3. Load the Poly-Ontological Mapping (The Golden Thread with Wa Scores) [cite: 20, 23]
        with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                record_entry = json.loads(line)
                rid = record_entry["record_id"]
                
                # Support both old single domain and new affinity map for backward compatibility
                affinities = record_entry.get("domain_affinities", {})
                
                # Construct Salience-Weighted Governance Profile
                governance_profile = []
                for domain_name, meta in affinities.items():
                    if domain_name in d4_laws:
                        law = d4_laws[domain_name]
                        governance_profile.append({
                            "domain": domain_name,
                            "affinity_weight": meta.get("wa", 1.0), # Injected Wa 
                            "rules": law["governance_packet"] # Relational Predicates, Depth, etc. [cite: 25]
                        })

                if governance_profile:
                    # Construct the Poly-Ontological Atomic Execution Contract [cite: 6, 32]
                    contract = {
                        "record_id": rid,
                        "z_score": record_entry.get("z_score", 0.0), # Provenance [cite: 15]
                        "governance_profile": governance_profile,
                        "source_text": raw_records[rid].get("question", "") + " " + 
                                      " ".join(raw_records[rid].get("context", []))
                    }
                    
                    f_out.write(json.dumps(contract) + "\n")
                    manifest_count += 1

    print(f"SUCCESS: {manifest_count} Poly-Ontological Contracts written to {D5_MANIFEST_PATH}")

if __name__ == "__main__":
    run_d5_orchestration_v22()