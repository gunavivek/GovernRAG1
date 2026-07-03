import json
import os

# --- Project Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_PATH = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")
D4_REGISTRY_PATH = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Discovered.json")
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl")
D5_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")

def run_d5_orchestration():
    print("--- D5 Orchestration: Constructing Governed Extraction Manifest ---")
    
    # 1. Load the D4 Governance Laws
    with open(D4_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        d4_laws = json.load(f)
    
    # 2. Load the Record-to-Domain Mapping (The Golden Thread)
    record_to_domain = {}
    with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            record_to_domain[entry["record_id"]] = entry["assigned_domain"]
            
    # 3. Load Raw Data for context
    with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
        raw_records = {json.loads(line)['id']: json.loads(line) for line in f}

    manifest_count = 0
    with open(D5_MANIFEST_PATH, 'w', encoding='utf-8') as f_out:
        for record_id, domain in record_to_domain.items():
            if domain in d4_laws:
                packet = d4_laws[domain]["governance_packet"]
                
                # Construct the Atomic Execution Contract
                contract = {
                    "record_id": record_id,
                    "domain": domain,
                    "governance_constraints": {
                        "predicates": packet["relational_predicates"],
                        "depth": packet["search_exit_depth"],
                        "glossary": packet["disambiguation_keys"]
                    },
                    "source_text": raw_records[record_id].get("question", "") + " " + 
                                  " ".join(raw_records[record_id].get("documents", []))
                }
                
                f_out.write(json.dumps(contract) + "\n")
                manifest_count += 1

    print(f"SUCCESS: {manifest_count} Governed Contracts written to {D5_MANIFEST_PATH}")

if __name__ == "__main__":
    run_d5_orchestration()