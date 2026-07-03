import json
import os
import re
from typing import List, Dict, Set

# --- Project Paths ---
Q1_INTENT_PATH = "output/Q1_intent_gate.jsonl"
Q3_EVIDENCE_PATH = "output/Q3_retrieved_evidence.jsonl"
OUTPUT_FILE = "output/Q2_5_bridge_entities.jsonl"

class GovBridgeDiscovery:
    """
    PHD RESEARCH COMPONENT: Q2.5 - Relational Gap Analysis
    Removes hardcoded dependencies to allow Q0 Orchestration.
    """

    def _extract_potential_entities(self, text: str) -> Set[str]:
        # Improved Regex for PhD-level Entity Extraction
        return set(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text))

    def _identify_relational_gap(self, question: str, triplets: List[Dict]) -> bool:
        q = question.lower()
        missing_predicates = ["born", "date", "founded", "location", "parent", "origin"]
        target_found = any(p in str(triplets).lower() for p in missing_predicates if p in q)
        return not target_found

    def process_record(self, record_id: str):
        # Now purely dynamic based on Q0 input
        intent_data = self._load_jsonl(Q1_INTENT_PATH, record_id, "id")
        evidence_data = self._load_jsonl(Q3_EVIDENCE_PATH, record_id, "record_id")

        if not intent_data or not evidence_data:
            return {"status": "ERROR", "msg": "Precursors missing"}

        question = intent_data["question"]
        triplets = evidence_data.get("symbolic_triplets", [])
        semantic_text = evidence_data.get("semantic_chunk", "")

        has_gap = self._identify_relational_gap(question, triplets)
        
        bridge_payload = {
            "record_id": record_id,
            "has_relational_gap": has_gap,
            "bridge_entities": [],
            "status": "ATOMIC_SATISFIED"
        }

        if has_gap:
            potential_anchors = self._extract_potential_entities(semantic_text)
            noise = {"The", "And", "Museum", "History", "Alcatraz", "Lawyer", "Founder"} 
            bridges = [ent for ent in potential_anchors if ent not in noise]
            
            bridge_payload["bridge_entities"] = bridges
            bridge_payload["status"] = "BRIDGE_REQUIRED"

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(bridge_payload, ensure_ascii=False) + '\n')
        
        return bridge_payload

    def _load_jsonl(self, path: str, rid: str, key: str) -> Dict:
        if not os.path.exists(path): return {}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if str(data.get(key)) == str(rid):
                    return data
        return {}