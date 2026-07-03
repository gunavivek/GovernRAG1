import os
import sys
import json
import pandas as pd

# --- Environment Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- Modular Imports ---
try:
    from Q1_Gov_Intent_Gate import GovernedIntentGate
    from Q2_Gov_Signature_Extractor import GovernedSignatureExtractor
    from Q2_5_Gov_Bridge_Discovery import GovBridgeDiscovery
    from Q2_6_Gov_Signature_Expansion import GovSignatureExpansion
    from Q3_Gov_Graph_Retrieval_Engine_V3 import GovGraphRetrievalEngineV3
    from Q4_Gov_Answer_Generation import generate_neuro_symbolic_answer
except ImportError as e:
    print(f"[CRITICAL] Architecture Linkage Error: {e}")
    sys.exit(1)

class GovRAG_Hybrid_Pipeline:
    def __init__(self, record_id: str):
        self.record_id = record_id
        self.q1_file = "output/Q1_intent_gate.jsonl"
        self.q2_file = "output/Q2_signatures.jsonl"
        self.q3_file = "output/Q3_retrieved_evidence.jsonl"
        self.residual_file = "output/M1_6_Residual_Chunks.csv"
        self.intent_map = {"Extractive": "1", "Comparison": "2", "Inferential": "3"}

    def run(self):
        print(f"\n" + "="*80)
        print(f"   PHD RESEARCH: HYBRID FEDERATED PIPELINE [{self.record_id}]")
        print("="*80)

        # 1. INTENT & SIGNATURE
        GovernedIntentGate().process() 
        strategy_code, comp_path, _ = self._resolve_execution_strategy()
        GovernedSignatureExtractor().process() 

        # 2. TIER 1: GOVERNED GRAPH RETRIEVAL
        print(f"\n[STEP 3] Tier 1: Executing {strategy_code} Governed Graph Walk...")
        q3 = GovGraphRetrievalEngineV3()
        q3.process(filter_id=self.record_id) 

        # 3. RELATIONAL BRIDGE (Triggered on Path B)
        if comp_path == "B":
            bridge_results = GovBridgeDiscovery().process_record(self.record_id)
            if bridge_results.get("status") == "BRIDGE_REQUIRED":
                GovSignatureExpansion().process_expansion(self.record_id)
                # Re-run Q3 with expanded signature
                q3.process(
                    filter_id=self.record_id, 
                    signature_path="output/Q2_6_expanded_signatures.jsonl"
                )

        # 4. TIER 2: RESIDUAL RETRIEVAL (Federated Logic)
        print("\n[STEP 3.7] Tier 2: Residual Retrieval - Auditing Orphaned Text...")
        governed_packet = self._load_jsonl_packet(self.q3_file)
        residual_text = self._fetch_residual_context()

        # 5. HYBRID SYNTHESIS & METRICS
        federated_packet = self._build_federated_packet(governed_packet, residual_text)
        
        print(f"\n[STEP 4] Q4: Hybrid Synthesis (Ratio: {federated_packet['gov_ratio']:.2f})")
        result = generate_neuro_symbolic_answer(federated_packet)

        self._display_final_report(result, strategy_code, comp_path, federated_packet['gov_ratio'])

    def _fetch_residual_context(self) -> str:
        """Standard Federated Search: Finds keyword hits in the Tier 2 scrap pile."""
        if not os.path.exists(self.residual_file):
            return ""
        
        try:
            df = pd.read_csv(self.residual_file)
            res_rows = df[df['record_id'] == self.record_id]
            if res_rows.empty:
                return ""
            
            # Use Q2 signatures to find relevant text in the residual pile
            q2_data = self._load_jsonl_packet(self.q2_file, key="id")
            targets = q2_data.get("q_signature", {}).get("target_nodes", [])
            
            hits = []
            for _, row in res_rows.iterrows():
                chunk = str(row['chunk_text'])
                if any(t.lower() in chunk.lower() for t in targets):
                    hits.append(chunk)
            
            return " ".join(hits)
        except Exception as e:
            print(f"[WARN] Residual fetch failed: {e}")
            return ""

    def _build_federated_packet(self, gov_packet, residual_text):
        """Combines T1 and T2 data and calculates the Governance Ratio."""
        g_chunks = gov_packet.get("semantic_chunk", "")
        
        # Tag the data for Q4 Synthesis
        combined_context = f"### [GOVERNED CONTEXT]\n{g_chunks}\n\n"
        if residual_text:
            combined_context += f"### [RESIDUAL CONTEXT (TIER 2)]\n{residual_text}"

        # Calculate Governance Ratio (Character-based)
        g_len = len(g_chunks)
        r_len = len(residual_text)
        ratio = g_len / (g_len + r_len) if (g_len + r_len) > 0 else 1.0

        new_packet = gov_packet.copy()
        new_packet["semantic_chunk"] = combined_context
        new_packet["gov_ratio"] = ratio
        return new_packet

    def _display_final_report(self, result, strategy, path, ratio):
        print("\n" + "!"*25 + f" HYBRID RESPONSE [{strategy}] " + "!"*25)
        if result.get("mode") == "GENERATED":
            print(f"ANSWER:   {result['generated_answer']}")
            print(f"\nGOVERNANCE METRICS:")
            print(f" - Governance Ratio: {ratio:.2f}")
            print(f" - Strategy Path:    {path}")
            print(f" - Tier 2 Status:    {'ACTIVE' if ratio < 1.0 else 'INACTIVE'}")
        else:
            print(f"REASON: {result.get('generated_answer') or result.get('error')}")
        print("!"*75 + "\n")

    def _resolve_execution_strategy(self):
        data = self._load_jsonl_packet(self.q1_file, key="id")
        path = data.get("complexity_path", "A")
        intent = data.get("primary_intent", "Extractive")
        return f"{path}{self.intent_map.get(intent, '1')}", path, intent

    def _load_jsonl_packet(self, file_path, key="record_id"):
        if not os.path.exists(file_path): return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if str(data.get(key)) == str(self.record_id):
                    return data
        return {}

if __name__ == "__main__":
    MY_RECORD_ID = "5ae28b76554299495565daa8"
    pipeline = GovRAG_Hybrid_Pipeline(MY_RECORD_ID)
    pipeline.run()