import json
import os
import pandas as pd
from typing import List, Dict

# --- Configuration & Paths ---
Q3_EVIDENCE_PATH = "output/Q3_retrieved_evidence.jsonl"
Q3_5_BRIDGE_PATH = "output/Q3_5_bridge_entities.jsonl"
M1_6_RESIDUAL_PATH = "output/M1_6_Residual_Chunks.csv" 
OUTPUT_FILE = "output/Q3_retrieved_evidence.jsonl" 

class GovResidualRetrieval:
    def __init__(self):
        if os.path.exists(M1_6_RESIDUAL_PATH):
            self.m1_6_df = pd.read_csv(M1_6_RESIDUAL_PATH, dtype={'record_id': str, 'chunk_id': str})
        else:
            raise FileNotFoundError(f"M1.6 residual chunks file not found at {M1_6_RESIDUAL_PATH}")

    def process_residual_audit(self, record_id: str):
        """
        PHD COMPONENT: Federated Residual Audit.
        Rescues descriptive context from the M1.6 Residual Pile to enrich symbolic findings.
        """
        evidence = self._load_jsonl(Q3_EVIDENCE_PATH, record_id, "record_id")
        bridge_data = self._load_jsonl(Q3_5_BRIDGE_PATH, record_id, "record_id")

        if not evidence or not bridge_data:
            raise ValueError(f"Q4 precursors missing for record_id={record_id}")

        # --- RECOVERY LOGIC (THE RESCUE) ---
        # If Q3.5 found no gap (Atomic), we use Q2's original target_nodes to ensure richness.
        anchors = bridge_data.get("bridge_entities", [])
        if not anchors:
            # Fallback to the original search warrant nodes
            anchors = evidence.get("q_signature", {}).get("target_nodes", [])
            print(f"[Q4] Atomic Path Detected. Using {len(anchors)} primary anchors for enrichment.")

        residual_context = []
        if self.m1_6_df is not None:
            # Epistemic Isolation: Filter by record_id
            target_chunks = self.m1_6_df[self.m1_6_df['record_id'] == str(record_id)]
            
            for _, row in target_chunks.iterrows():
                text = str(row['chunk_text'])
                
                # Metadata Extraction for Q5 provenance
                try:
                    meta = json.loads(row['disambiguation'])
                    shadow_domain = meta.get("shadow_domain", "General")
                except:
                    shadow_domain = "General"

                # Federated Search: Match anchors against unstructured text
                if any(str(anchor).lower() in text.lower() for anchor in anchors):
                    residual_context.append(f"[RESIDUAL_{row['chunk_id']} | DOMAIN: {shadow_domain}]: {text}")

        # Stateful Merge into the Evidence Packet
        evidence["residual_context"] = " ".join(residual_context)
        
        if "traversal_stats" not in evidence:
            evidence["traversal_stats"] = {}
        evidence["traversal_stats"]["residual_hits"] = len(residual_context)

        # Persistence: Stateful update
        self._update_evidence_file(evidence)
        print(f"[Q4] Residual Audit Complete. Found {len(residual_context)} fragments for {record_id}.")
        
        return {"status": "FEDERATED", "hits": len(residual_context)}

    def _update_evidence_file(self, updated_record: Dict):
        all_data = []
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data["record_id"] == updated_record["record_id"]:
                        all_data.append(updated_record)
                    else:
                        all_data.append(data)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for item in all_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

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
    engine = GovResidualRetrieval()
    engine.process_residual_audit(sys.argv[1])