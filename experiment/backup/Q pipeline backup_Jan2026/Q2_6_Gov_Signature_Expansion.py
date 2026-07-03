import json
import os
from typing import Dict, List

# --- Project Paths ---
Q1_INTENT_PATH = "output/Q1_intent_gate.jsonl"
Q2_5_BRIDGE_PATH = "output/Q2_5_bridge_entities.jsonl"
OUTPUT_FILE = "output/Q2_signatures.jsonl"

class GovSignatureExpansion:
    """
    PHD RESEARCH COMPONENT: Q2.6 - Dynamic Signature Expansion
    Objective: Orchestrates a recursive search signature without hardcoded values.
    """

    def process_expansion(self, record_id: str):
        print(f"--- Q2.6: Dynamic Signature Expansion for [{record_id}] ---")

        # 1. Load context from previous stages
        intent_data = self._load_jsonl(Q1_INTENT_PATH, record_id, "id")
        bridge_data = self._load_jsonl(Q2_5_BRIDGE_PATH, record_id, "record_id")

        if not intent_data or not bridge_data:
            return {"status": "ERROR", "msg": "Context precursors missing"}

        if bridge_data.get("status") != "BRIDGE_REQUIRED":
            return {"status": "SKIPPED"}

        # 2. DYNAMIC MAPPING: PREDICATE DERIVATION
        # Instead of hardcoding, we derive search predicates from the Q1 question
        # and the 'relational_predicates' allowed by the Governance Profile.
        original_question = intent_data.get("question", "").lower()
        governed_predicates = intent_data.get("governed_context", {}).get("primary_laws", {}).get("relational_predicates", [])
        
        # Heuristic: Match keywords in question to governed predicates
        # If no match, we use the original governed list as the search scope
        search_predicates = [p for p in governed_predicates if p in original_question]
        if not search_predicates:
            search_predicates = governed_predicates

        # 3. DYNAMIC MAPPING: ANCHOR SELECTION
        # We preserve the domain from Q1 to ensure we stay within the governed silo
        active_domain = intent_data.get("governed_context", {}).get("active_domains", ["General"])[0]
        
        # We take the top entities discovered in Q2.5 as the new targets
        bridge_nodes = bridge_data.get("bridge_entities", [])

        # 4. CONSTRUCT EXPANDED PACKET
        # We update the original packet to maintain the audit trail for the PhD
        expanded_signature = {
            "primary_anchor": active_domain,
            "target_nodes": bridge_nodes,
            "required_predicates": search_predicates,
            "is_recursive_pass": True,
            "expansion_source": "Q2.5_Bridge"
        }

        # Update the main data object
        intent_data["q_signature"] = expanded_signature
        intent_data["traversal_parameters"]["k_hops"] += 1 # Increment depth for the hop
        intent_data["justification"]["logic"] += f" | Dynamically expanded via {len(bridge_nodes)} bridge nodes."

        # 5. PERSISTENCE
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(intent_data, ensure_ascii=False) + '\n')

        return {"status": "EXPANDED", "node_count": len(bridge_nodes)}

    def _load_jsonl(self, path: str, rid: str, key: str) -> Dict:
        if not os.path.exists(path): return {}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if str(data.get(key)) == str(rid):
                    return data
        return {}

if __name__ == "__main__":
    # Designed to be called by Q0
    pass