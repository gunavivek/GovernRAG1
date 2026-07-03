import json
import os
import re
from typing import Dict, Any

# --- Configuration & Paths ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if "experiment" in PROJECT_ROOT:
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

D5_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
Q3_EVIDENCE_PATH = os.path.join(PROJECT_ROOT, "output", "Q3_retrieved_evidence.jsonl")
Q5_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "Q5_routed_context.jsonl")

class GovContextRouter:
    """
    PHD COMPONENT: Q5 - The Governed Synthesis Router (The Supreme Court)
    Evaluates empirical evidence (M-Pipeline/Q-Pipeline) against 
    the original D5 Governance Laws. Drops unauthorized triplets and chunks.
    """
    def __init__(self):
        self.d5_laws = self._load_d5_manifest()

    def _load_d5_manifest(self) -> Dict[str, Any]:
        """Loads the Golden Thread architectural contracts."""
        manifest = {}
        if os.path.exists(D5_MANIFEST_PATH):
            with open(D5_MANIFEST_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        manifest[data['record_id']] = data
        return manifest

    def route_governed_context(self, record_id: str, evidence_packet: dict) -> dict:
        """Audits both triplets AND chunks, calculating the true Governance Ratio (GR)."""
        print(f"\n--- Q5: Governed Context Routing for [{record_id}] ---")
        
        d5_contract = self.d5_laws.get(record_id, {})
        if not d5_contract:
            print(f"  [WARNING] No D5 Governance Contract found for {record_id}.")
        
        # 1. Extract Authorized Predicates from D5
        allowed_predicates = set()
        for profile in d5_contract.get("governance_profile", []):
            preds = profile.get("rules", {}).get("relational_predicates", [])
            allowed_predicates.update([p.lower() for p in preds])

        # 2. AUDIT TRIPLETS (Strict Negative Constraint)
        raw_triplets = evidence_packet.get("symbolic_triplets", [])
        governed_triplets = []
        
        if allowed_predicates:
            for t in raw_triplets:
                pred = str(t.get("p", "")).lower()
                # If the extracted predicate is legally authorized, keep it
                if any(auth_p in pred for auth_p in allowed_predicates):
                    governed_triplets.append(t)
        else:
            governed_triplets = raw_triplets

        dropped_triplets = len(raw_triplets) - len(governed_triplets)

        # 3. AUDIT CHUNKS (Un-stitching Q3's string to evaluate M1's boundaries)
        chunk_audit_log = []
        
        # --- Audit Tier 2 (Residuals) ---
        raw_residual = evidence_packet.get("residual_context", [])
        if isinstance(raw_residual, str):
            raw_residual = [raw_residual] if raw_residual.strip() else []
            
        governed_residual_chunks = []
        if allowed_predicates:
            for i, chunk in enumerate(raw_residual):
                found_preds = [p for p in allowed_predicates if p in str(chunk).lower()]
                if found_preds:
                    governed_residual_chunks.append(chunk)
                    chunk_audit_log.append({"tier": 2, "index": i, "action": "KEPT", "reason": f"Predicates: {found_preds}"})
                else:
                    chunk_audit_log.append({"tier": 2, "index": i, "action": "DROPPED", "reason": "No authorized predicates"})
        else:
            governed_residual_chunks = raw_residual

        # --- Audit Tier 1 (Primary Semantic Chunk) ---
        raw_primary_str = str(evidence_packet.get("semantic_chunk", ""))
        governed_primary_chunks = []
        
        # Regex to un-stitch the massive string back into individual M1 chunks by their [CHNK_] tags
        primary_pieces = re.findall(r"(\[CHNK_[^\]]+\]:?\s*.*?)(?=\[CHNK_|$)", raw_primary_str, flags=re.DOTALL)
        
        if allowed_predicates and primary_pieces:
            for i, piece in enumerate(primary_pieces):
                found_preds = [p for p in allowed_predicates if p in str(piece).lower()]
                if found_preds:
                    governed_primary_chunks.append(piece.strip())
                    chunk_audit_log.append({"tier": 1, "index": i, "action": "KEPT", "reason": f"Predicates: {found_preds}"})
                else:
                    chunk_audit_log.append({"tier": 1, "index": i, "action": "DROPPED", "reason": "No authorized predicates"})
        else:
            governed_primary_chunks = primary_pieces

        # Re-assemble only the surviving Tier 1 chunks
        filtered_semantic_chunk = "\n".join(governed_primary_chunks)

        dropped_chunks = (len(primary_pieces) - len(governed_primary_chunks)) + (len(raw_residual) - len(governed_residual_chunks))

        # 4. CALCULATE TRUE GOVERNANCE RATIO (GR)
        governed_text_len = len(str(governed_triplets)) + len(filtered_semantic_chunk)
        residual_text_len = len(str(governed_residual_chunks))
        
        total_evidence_len = governed_text_len + residual_text_len
        gr_ratio = (governed_text_len / total_evidence_len) if total_evidence_len > 0 else 1.0

        print(f"  [Audit] Triplets: Kept {len(governed_triplets)}, Dropped {dropped_triplets}")
        print(f"  [Audit] Chunks:   Dropped {dropped_chunks} unauthorized chunks (Tier 1 & Tier 2).")
        print(f"  [Audit] Calculated Governance Ratio: {gr_ratio:.2f}")

        # 5. ASSEMBLE FINAL ROUTED PACKET FOR Q6
        routed_packet = evidence_packet.copy()
        routed_packet["symbolic_triplets"] = governed_triplets # Strictly Overwritten
        routed_packet["semantic_chunk"] = filtered_semantic_chunk # Strictly Overwritten
        routed_packet["residual_context"] = governed_residual_chunks # Strictly Overwritten
        routed_packet["gov_ratio"] = round(gr_ratio, 4)
        
        # Crucial payload for PhD Explainability
        routed_packet["audit_metadata"] = {
            "d5_contract_applied": True if d5_contract else False,
            "allowed_predicates_enforced": list(allowed_predicates),
            "triplets_dropped": dropped_triplets,
            "chunks_dropped": dropped_chunks,
            "chunk_decision_log": chunk_audit_log 
        }

        return routed_packet

    def process_file(self):
        """Processes all evidence sequentially (Standalone Execution)."""
        if not os.path.exists(Q3_EVIDENCE_PATH):
            raise FileNotFoundError(f"Missing Q3 evidence at {Q3_EVIDENCE_PATH}")
            
        routed_results = []
        with open(Q3_EVIDENCE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                evidence = json.loads(line)
                rid = evidence.get("record_id")
                
                routed_packet = self.route_governed_context(rid, evidence)
                routed_results.append(routed_packet)
                
        with open(Q5_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            for res in routed_results:
                f.write(json.dumps(res, ensure_ascii=False) + '\n')
        
        print(f"--- Q5 Complete. Routed {len(routed_results)} packets to {Q5_OUTPUT_PATH} ---")

if __name__ == "__main__":
    router = GovContextRouter()
    router.process_file()