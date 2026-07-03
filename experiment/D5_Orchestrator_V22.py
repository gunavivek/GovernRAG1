import json
import os
from typing import Dict, List, Any

# --- Project Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_PATH = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")
D4_REGISTRY_PATH = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Discovered.json")
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "RGB_Single_Record.jsonl")
D5_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")

def flatten_evidence(item: Dict[str, Any]) -> str:
    """
    Universal Evidence Extractor (Schema-Agnostic).
    Parses data based purely on its structural shape (String, Flat List, Nested List)
    rather than relying on hardcoded dataset definitions.
    """
    # 1. Identify the payload regardless of the specific key name
    payload = item.get("context") or item.get("documents") or item.get("text") or item.get("passage")
    
    if not payload:
        return ""

    # 2. Structural Pattern Matching
    
    # Shape A: Pure String
    if isinstance(payload, str):
        return payload.strip()
        
    # Shape B: List Structures
    if isinstance(payload, list):
        if not payload: return ""
        
        # Peek at the first element to determine nesting depth
        first_element = payload[0]
        
        # Sub-Shape B1: Flat List of Strings ["Sentence 1", "Sentence 2"]
        if isinstance(first_element, str):
            return " ".join([str(p).strip() for p in payload if isinstance(p, str)])
            
        # Sub-Shape B2: Nested Lists (e.g., [["Title", ["Sentence 1", "Sentence 2"]]])
        if isinstance(first_element, list):
            extracted_text = []
            for block in payload:
                if isinstance(block, list) and len(block) >= 2:
                    content = block[1] 
                    if isinstance(content, list):
                        extracted_text.extend([str(c) for c in content if isinstance(c, str)])
                    elif isinstance(content, str):
                        extracted_text.append(content)
            return " ".join(extracted_text)
            
        # Sub-Shape B3: List of Dictionaries (e.g., [{"text": "sentence"}])
        if isinstance(first_element, dict):
             extracted_text = []
             for block in payload:
                 text_val = block.get("text") or block.get("content") or block.get("paragraph")
                 if text_val and isinstance(text_val, str):
                     extracted_text.append(text_val)
             return " ".join(extracted_text)

    # 3. Fallback for completely unexpected structures
    return str(payload)

def run_d5_orchestration_v22():
    print("--- D5 V22: Orchestrating Poly-Ontological Extraction Contracts (Unicode Fixed) ---")
    
    # 1. Ingest Enriched D4 Governance Laws
    if not os.path.exists(D4_REGISTRY_PATH):
        print(f"CRITICAL ERROR: D4 Registry not found at {D4_REGISTRY_PATH}")
        return
        
    with open(D4_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        d4_laws = json.load(f)
    
    # 2. Load Raw Data
    raw_lookup = {}
    if os.path.exists(RAW_DATA_PATH):
        print(f"Ingesting raw evidence from {RAW_DATA_PATH}...")
        with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                
                rid = item.get('id', item.get('_id'))
                if rid is None or str(rid).strip() == "":
                    continue
                rid = str(rid).strip()
                question = item.get("question", "")
                
                # Extract Evidence
                full_doc_text = flatten_evidence(item)
                
                if not full_doc_text:
                    full_doc_text = "EMPTY_DOCUMENT_ERROR"
                
                # CHANGE 1: Label changed from 'Context' to 'Document'
                raw_lookup[rid] = f"Question: {question} | Document: {full_doc_text}"
    else:
        print(f"CRITICAL ERROR: Raw data not found at {RAW_DATA_PATH}")
        return

    manifest_count = 0
    with open(D5_MANIFEST_PATH, 'w', encoding='utf-8') as f_out:
        # 3. Load the Poly-Ontological Mapping
        if not os.path.exists(MAPPING_PATH):
            print(f"CRITICAL ERROR: Mapping file not found at {MAPPING_PATH}")
            return

        with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                record_entry = json.loads(line)
                rid = str(record_entry["record_id"]).strip()
                
                affinities = record_entry.get("domain_affinities", {})
                
                governance_profile = []
                for domain_name, meta in affinities.items():
                    if domain_name in d4_laws:
                        law = d4_laws[domain_name]
                        governance_profile.append({
                            "domain": domain_name,
                            "affinity_weight": meta.get("wa", 1.0),
                            "rules": law["governance_packet"]
                        })

                if governance_profile:
                    contract = {
                        "record_id": rid,
                        "z_score": record_entry.get("z_score", 0.0), 
                        "governance_profile": governance_profile,
                        "source_text": raw_lookup.get(rid, "EVIDENCE_NOT_FOUND_IN_LOOKUP") 
                    }
                    
                    # CHANGE 2: ensure_ascii=False forces actual characters (Léo instead of L\u00e9o)
                    f_out.write(json.dumps(contract, ensure_ascii=False) + "\n")
                    manifest_count += 1

    print(f"SUCCESS: {manifest_count} Atomic Contracts written to {D5_MANIFEST_PATH}")

if __name__ == "__main__":
    run_d5_orchestration_v22()