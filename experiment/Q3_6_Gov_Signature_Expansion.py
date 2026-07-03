import json
import os
from typing import Dict, List

# --- Project Paths ---
Q1_INTENT_PATH = "output/Q1_intent_gate.jsonl"
Q3_5_BRIDGE_PATH = "output/Q3_5_bridge_entities.jsonl"
OUTPUT_FILE = "output/Q2_signatures.jsonl" # Stateful Overwrite for Q3 Re-entry

class GovSignatureExpansion:
    """
    PHD RESEARCH COMPONENT: Q3.6 - Dynamic Signature Expansion
    Orchestrates recursive signatures based on discovered bridge concepts.
    """

    def process_expansion(self, record_id: str) -> Dict:
        print(f"--- Q3.6: Dynamic Signature Expansion for [{record_id}] ---")

        # 1. Load context from Auditor (Q3.5) and Gate (Q1)
        intent_data = self._load_jsonl(Q1_INTENT_PATH, record_id, "record_id")
        bridge_data = self._load_jsonl(Q3_5_BRIDGE_PATH, record_id, "record_id")

        if not intent_data or not bridge_data:
          raise ValueError(f"Context precursors missing for record_id={record_id}")

        # 2. AUDIT CHECK: Only proceed if Q3.5 flagged a Relational Gap
        if bridge_data.get("status") != "BRIDGE_REQUIRED":
            print(f"[Q3.6] Audit satisfied for {record_id}. Skipping expansion.")
            return {"status": "SKIPPED"}

        # 3. DYNAMIC PREDICATE DERIVATION (Governed)
        # We ensure the expansion honors the Hybrid Domains defined in Q1
        governed_context = intent_data.get("governed_context", {})
        active_domains = governed_context.get("active_domains", ["General"])
        
        # Inherit the full merged predicate list from the Hybrid Q1 gate
        # This ensures we don't lose the 'win' or 'compete' predicates in the 2nd hop
        search_predicates = governed_context.get("primary_laws", {}).get("relational_predicates", [])

        # 4. DYNAMIC ANCHOR SELECTION
        # Use entities discovered in the first walk (e.g. "Riyadh", "Real Madrid") as new anchors
        bridge_nodes = bridge_data.get("bridge_entities", [])

        # 5. CONSTRUCT EXPANDED PACKET
        expanded_signature = {
            "primary_anchor": active_domains[0] if active_domains else "General",
            "active_domains": active_domains, # Preserving Hybrid State
            "target_nodes": bridge_nodes,
            "required_predicates": search_predicates,
            "is_recursive_pass": True,
            "expansion_source": "Q3.5_Bridge_Analysis"
        }

        # 6. STATE PRESERVATION (The PhD Audit Trail)
        intent_data["q_signature"] = expanded_signature
        
        # Increment hop depth (k-hop scaling)
        original_hops = intent_data["traversal_parameters"].get("k_hops", 1)
        intent_data["traversal_parameters"]["k_hops"] = original_hops + 1
        
        intent_data["justification"]["logic"] += f" | RECURSIVE: Expanded via {len(bridge_nodes)} bridge nodes."

        # 7. PERSISTENCE: Re-write to Q2 Signatures for Q3's next pass
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(intent_data, ensure_ascii=False) + '\n')

        print(f"[Q3.6] Signature expanded. New k_hops: {intent_data['traversal_parameters']['k_hops']}")
        return {"status": "EXPANDED", "node_count": len(bridge_nodes)}

    def _load_jsonl(self, path: str, rid: str, key: str) -> Dict:
        if not os.path.exists(path): return {}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if str(data.get(key)).strip() == str(rid).strip():
                    return data
        return {}

if __name__ == "__main__":
    import sys
    if len(sys.argv) <= 1:
        raise SystemExit("record_id argument required")
    GovSignatureExpansion().process_expansion(sys.argv[1])