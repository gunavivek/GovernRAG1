import os
import sys
import json
import pandas as pd
import time

# --- Environment Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- Modular Imports (Matched to Frozen Filenames) ---
try:
    from Q1_Gov_Intent_Gate_V2 import GovernedIntentGateV2
    from Q2_Gov_Signature_Extractor_V2 import GovernedSignatureExtractorV2
    from Q3_Gov_Graph_Retrieval_Engine_V3 import GovGraphRetrievalEngineV3
    from Q3_5_Gov_Bridge_Discovery import GovBridgeDiscovery
    from Q3_6_Gov_Signature_Expansion import GovSignatureExpansion
    from Q4_Gov_Residual_Retrieval import GovResidualRetrieval 
    from Q5_Gov_Context_Router import GovContextRouter    # Governed Router
    from Q6_Gov_Answer_Generation import generate_governed_answer # Final Synthesis
except ImportError as e:
    print(f"[CRITICAL] Architecture Linkage Error: {e}")
    sys.exit(1)

class GovRAG_Orchestrator_Final:
    def __init__(self, record_id: str):
        self.record_id = record_id
        self.q1_file = "output/Q1_intent_gate.jsonl"
        self.q2_file = "output/Q2_signatures.jsonl"
        self.q3_file = "output/Q3_retrieved_evidence.jsonl"
        self.q5_file = "output/Q5_routed_context.jsonl"
        self.intent_map = {"Extractive": "1", "Comparison": "2", "Inferential": "3"}

    def run(self):
        print(f"\n" + "="*80)
        print(f"   PHD RESEARCH: BA-GOVERNED FEDERATED PIPELINE [{self.record_id}]")
        print("="*80)

        # 1. INTENT & CONCEPT SIGNATURE (Q1 & Q2)
        # Bridges Natural Language to BA Predicates
        GovernedIntentGateV2().process() 
        strategy_code, comp_path, _ = self._resolve_execution_strategy()
        GovernedSignatureExtractorV2().process() 

        # 2. TIER 1: GOVERNED GRAPH RETRIEVAL (Q3 Pass 1)
        print(f"\n[Q3] Pass 1: Primary BA-Graph Walk ({strategy_code})...")
        q3_engine = GovGraphRetrievalEngineV3()
        q3_engine.process(filter_id=self.record_id) 

        # 3. RELATIONAL GAP REMEDIATION (Q3.5 Auditor)
        print(f"[Q3.5] Relational Gap Analysis...")
        bridge_results = GovBridgeDiscovery().process_record(self.record_id)

        # Path B only: recursive expansion if bridge is required
        if comp_path == "B" and bridge_results.get("status") == "BRIDGE_REQUIRED":
            GovSignatureExpansion().process_expansion(self.record_id)
            print(f"[Q3] Pass 2: Recursive BA-Graph Walk...")
            q3_engine.process(filter_id=self.record_id)

        # 4. TIER 2: FEDERATED RESIDUAL AUDIT (Q4)
        print("\n[Q4] Tier 2: Residual Retrieval - Auditing Federated Context...")
        residual_path = "output/M1_6_Residual_Chunks.csv"
        if os.path.exists(residual_path):
            GovResidualRetrieval().process_residual_audit(self.record_id)
        else:
            print(f"[Q4] SKIPPED: Residual source missing.")
        
        # 5. GOVERNED CONTEXT ROUTING (Q5)
        # This is the "Supreme Court" that audits Q3/Q4 against D5 Manifest
        final_evidence = self._load_jsonl_packet(self.q3_file, key="record_id")
        q2_context = self._load_jsonl_packet(self.q2_file, key="record_id")
        
        if not final_evidence:
            raise ValueError(f"Missing Q3 evidence for record_id={self.record_id}")

        # Meta-data Injection for the Router
        final_evidence["q_signature"] = q2_context.get("q_signature", {})
        final_evidence["justification"] = q2_context.get("justification", {})
        
        print(f"\n[Q5] Executing Governed Context Audit...")
        router = GovContextRouter()
        # Strictly audit chunks/triplets and calculate true Governance Ratio
        routed_evidence = router.route_governed_context(self.record_id, final_evidence)
        
        # Save routed evidence for audit trail
        with open(self.q5_file, "w", encoding="utf-8") as f_q5:
            f_q5.write(json.dumps(routed_evidence, ensure_ascii=False) + "\n")

        # 6. FEDERATED SYNTHESIS (Q6)
        gr_ratio = routed_evidence.get("gov_ratio", 1.0)
        print(f"\n[Q6] Hybrid Synthesis (Governance Ratio: {gr_ratio:.2f})")
        
        # Pass only the audited/routed evidence to the final narrator
        result = generate_governed_answer(routed_evidence)

        # Persist Q6 output for E2 / PAPER_ANALYSIS / dissertation audit
        q6_file = "output/Q6_final_answers.jsonl"
        with open(q6_file, "w", encoding="utf-8") as f_q6:
            f_q6.write(json.dumps(result, ensure_ascii=False) + "\n")

        # 7. FINAL REPORT
        self._display_final_report(result, strategy_code, comp_path, gr_ratio)

    def _calculate_governance_ratio(self, packet):
        """Deprecated: Logic moved to Q5 for higher precision auditing."""
        g_len = len(str(packet.get("symbolic_triplets", ""))) + len(str(packet.get("semantic_chunk", "")))
        r_len = len(str(packet.get("residual_context", "")))
        return g_len / (g_len + r_len) if (g_len + r_len) > 0 else 1.0

    def _resolve_execution_strategy(self):
        data = self._load_jsonl_packet(self.q1_file, key="record_id")
        path = data.get("complexity_path", "A")
        intent = data.get("primary_intent", "Extractive")
        return f"{path}{self.intent_map.get(intent, '1')}", path, intent

    def _load_jsonl_packet(self, file_path, key="record_id"):
        if not os.path.exists(file_path): return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if str(data.get(key)).strip() == str(self.record_id).strip(): 
                    return data
        return {}

    def _display_final_report(self, result, strategy, path, ratio):
        """The critical print block for Dissertation Result Capture."""
        print("\n" + "!"*25 + f" Q6 FINAL SYNTHESIS [{strategy}] " + "!"*25)
        
        mode = result.get("mode", "UNKNOWN")
        ans = result.get("generated_answer", "N/A")
        
        print(f"\nPROVENANCE-BOUNDED ANSWER:")
        print("-" * 80)
        print(ans)
        print("-" * 80)
            
        print(f"\nPHD AUDIT METRICS:")
        print(f" - Governance Ratio (GR): {ratio:.2f}")
        print(f" - Path Architecture:     {path}")
        print(f" - Triplet Grounding:     {result.get('metadata', {}).get('triplet_count', 0)} verified facts")
        print(f" - System Mode:           {mode}")
        print("!"*80 + "\n")

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        raise SystemExit("Usage: python Q0_Gov_RAG_Orchestrator.py <record_id>")
    
    target_record = sys.argv[1]
    orchestrator = GovRAG_Orchestrator_Final(target_record)
    orchestrator.run()