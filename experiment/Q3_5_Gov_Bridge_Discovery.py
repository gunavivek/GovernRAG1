import json
import os
import re
from typing import List, Dict, Set

# --- Project Paths ---
Q1_INTENT_PATH = "output/Q1_intent_gate.jsonl"
Q2_SIGNATURE_PATH = "output/Q2_signatures.jsonl"
Q3_EVIDENCE_PATH = "output/Q3_retrieved_evidence.jsonl"
OUTPUT_FILE = "output/Q3_5_bridge_entities.jsonl"

class GovBridgeDiscovery:
    """
    PHD RESEARCH COMPONENT: Q3.5 - Relational Gap Analysis (The Auditor)
    Detects if the Symbolic Walk (Q3) satisfied the BA Governance requirements.
    """

    def _extract_potential_entities(self, text: str) -> Set[str]:
        """Distills candidate entities from text for Bridge Discovery."""
        # PhD Logic: Regex targets proper nouns which likely represent BA Information Concepts
        return set(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text))

    def _identify_relational_gap(self, record: Dict, triplets: List[Dict]) -> bool:
        """
        Audits retrieved triplets against the BA Domain laws.
        Returns True if a required conceptual relationship is missing.
        """
        # Retrieve the required predicates defined in the Q1/Q2 signature
        signature = record.get("q_signature", {})
        required = signature.get("required_predicates", [])
        
        if not required:
            return False # No specific relational requirement, assume atomic success
            
        found_predicates = [t.get("p", "").lower() for t in triplets]
        
        # Gap exists if any required BA predicate is missing from the Graph Walk
        for req in required:
            if not any(req.lower() in fp for fp in found_predicates):
                return True
        return False

    def process_record(self, record_id: str) -> Dict:
        """Entry point for Q0 Orchestrator to decide on Recursive Pass."""
        print(f"--- Q3.5: Relational Gap Audit for [{record_id}] ---")
        
        # FIXED: Both lookups now use the unified 'record_id' key
        intent_data = self._load_jsonl(Q2_SIGNATURE_PATH, record_id, "record_id")
        evidence_data = self._load_jsonl(Q3_EVIDENCE_PATH, record_id, "record_id")

        if not intent_data or not evidence_data:
            raise ValueError(f"Precursors missing for Gap Analysis: record_id={record_id}")

        triplets = evidence_data.get("symbolic_triplets", [])
        semantic_text = evidence_data.get("semantic_chunk", "")

        # Perform the Audit
        has_gap = self._identify_relational_gap(intent_data, triplets)
        
        bridge_payload = {
            "record_id": record_id,
            "has_relational_gap": has_gap,
            "bridge_entities": [],
            "status": "ATOMIC_SATISFIED"
        }

        if has_gap:
            # ADAPTIVE ENRICHMENT: Identify bridge entities for the next hop
            potential_anchors = self._extract_potential_entities(semantic_text)
            
            # Dissertation filter: Remove noise/document terms to isolate BA Concepts
            noise = {"Document", "Page", "Section", "Table", "Figure", "Source", "Match", "Final"} 
            bridges = [ent for ent in potential_anchors if ent not in noise and len(ent) > 2]
            
            bridge_payload["bridge_entities"] = bridges
            bridge_payload["status"] = "BRIDGE_REQUIRED"
            print(f"[Q3.5] Relational Gap Detected. Identified {len(bridges)} candidate bridges.")
        else:
            print(f"[Q3.5] Audit Passed: Symbolic evidence satisfies BA constraints.")

        # Write the audit result to the output file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(bridge_payload, ensure_ascii=False) + '\n')
        
        return bridge_payload

    def _load_jsonl(self, path: str, rid: str, key: str) -> Dict:
        if not os.path.exists(path): return {}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                # Robust comparison with string stripping
                if str(data.get(key)).strip() == str(rid).strip():
                    return data
        return {}

if __name__ == "__main__":
    import sys
    discovery = GovBridgeDiscovery()
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not target_id:
        raise SystemExit("record_id argument required")
    discovery.process_record(target_id)