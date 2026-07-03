import os
import sys
import json

# --- Environment Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- Modular Imports ---
try:
    from Q1_Gov_Intent_Gate import GovernedIntentGate
    from experiment.Q2_Gov_Signature_Extractor_V2 import GovernedSignatureExtractor
    from experiment.Q3_5_Gov_Bridge_Discovery import GovBridgeDiscovery
    from experiment.Q3_6_Gov_Signature_Expansion import GovSignatureExpansion
    from Q3_Gov_Graph_Retrieval_Engine_V3 import GovGraphRetrievalEngineV3
    from experiment.Q5_Gov_Answer_Generation import generate_neuro_symbolic_answer
except ImportError as e:
    print(f"[CRITICAL] Architecture Linkage Error: {e}")
    sys.exit(1)

class GovRAG_Pipeline:
    def __init__(self, record_id: str):
        self.record_id = record_id
        self.q1_file = "output/Q1_intent_gate.jsonl"
        self.q3_file = "output/Q3_retrieved_evidence.jsonl"
        self.intent_map = {"Extractive": "1", "Comparison": "2", "Inferential": "3"}

    def run(self):
        print(f"\n" + "="*80)
        print(f"   PHD RESEARCH PIPELINE: EXECUTING RECORD [{self.record_id}]")
        print("="*80)

        # -----------------------------------------------------------------
        # PHASE Q1: GOVERNANCE INTENT GATE
        # -----------------------------------------------------------------
        print("\n[STEP 1] Q1: Intent Gate - Classifying Complexity...")
        GovernedIntentGate().process() 

        # Resolve Strategy Code (e.g., A1, B1, B23)
        strategy_code, comp_path, intent_class = self._resolve_execution_strategy()
        print(f">>> DETECTED INTENT CLASS: {intent_class}")
        print(f">>> EXECUTION STRATEGY  : {strategy_code}")

        # -----------------------------------------------------------------
        # PHASE Q2: SIGNATURE EXTRACTION (Primary Pass)
        # -----------------------------------------------------------------
        print("\n[STEP 2] Q2: Signature Extractor - Mapping Primary Anchors...")
        GovernedSignatureExtractor().process() 

        # -----------------------------------------------------------------
        # PHASE Q3: GRAPH RETRIEVAL ENGINE (Primary Pass)
        # -----------------------------------------------------------------
        print(f"\n[STEP 3] Q3: Graph Engine - Executing {strategy_code} Primary Walk...")
        q3 = GovGraphRetrievalEngineV3()
        q3.process(filter_id=self.record_id) 

        # -----------------------------------------------------------------
        # PHASE Q2.5 & Q2.6: THE RELATIONAL BRIDGE (Triggered on Path B)
        # -----------------------------------------------------------------
        if comp_path == "B":
            print(f"\n[STEP 3.5] Q2.5: Bridge Discovery - Analyzing Gaps for {strategy_code}...")
            bridge_results = GovBridgeDiscovery().process_record(self.record_id)
            
            if bridge_results.get("status") == "BRIDGE_REQUIRED":
                print(f">>> Relational Gap Confirmed. Found Bridge Nodes: {bridge_results['bridge_entities']}")
                
                print("\n[STEP 3.6] Q2.6: Signature Expansion - Re-anchoring Graph Walk...")
                expansion_result = GovSignatureExpansion().process_expansion(self.record_id)
                
                if expansion_result.get("status") == "EXPANDED":
                    print("\n[STEP 3.RECURSIVE] Q3: Re-running with EXPANDED signatures...")
                    # CHANGE: Point to the output of Q2.6, NOT the default Q2_signatures.jsonl
                    q3.process(
                        filter_id=self.record_id, 
                        signature_path="output/Q2_6_expanded_signatures.jsonl" 
                    )
            else:
                print(">>> Path B indicated, but local evidence was sufficient. Skipping expansion.")

        # -----------------------------------------------------------------
        # PHASE Q4: NEURO-SYMBOLIC SYNTHESIS
        # -----------------------------------------------------------------
        print("\n[STEP 4] Q4: Synthesis - Generating Grounded Answer...")
        evidence_packet = self._load_packet(self.q3_file)
        
        if evidence_packet:
            result = generate_neuro_symbolic_answer(evidence_packet)
            
            # --- FINAL OUTPUT DISPLAY ---
            print("\n" + "!"*25 + f" GOVERNED RESPONSE [{strategy_code}] " + "!"*25)
            if result.get("mode") == "GENERATED":
                print(f"QUESTION: {result['question']}")
                print(f"ANSWER:   {result['generated_answer']}")
                print(f"\nAUDIT TRAIL:")
                print(f" - Path Type:      {comp_path}")
                print(f" - Strategy:       {strategy_code}")
                print(f" - Triplets Used:  {result['triplet_count']}")
            else:
                print(f"STATUS: {result.get('mode')}")
                print(f"REASON: {result.get('generated_answer') or result.get('error')}")
            print("!"*75 + "\n")
        else:
            print(f"[FATAL] Evidence packet missing for record {self.record_id}.")

    def _resolve_execution_strategy(self):
        """Maps Q1 results to strategy codes (A1, B1, B23, etc)."""
        if not os.path.exists(self.q1_file):
            return "A1", "A", "Extractive"
        
        with open(self.q1_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if str(data.get("id")) == str(self.record_id):
                    path = data.get("complexity_path", "A")
                    intent = data.get("primary_intent", "Extractive")
                    # Map intent list to numbers if necessary, or just use primary
                    intent_num = self.intent_map.get(intent, "1")
                    return f"{path}{intent_num}", path, intent
        return "A1", "A", "Extractive"

    def _load_packet(self, file_path):
        if not os.path.exists(file_path): return None
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if str(data.get("record_id")) == str(self.record_id):
                    return data
        return None

if __name__ == "__main__":
    # Target Record: John Morgan (Multi-hop)
    MY_RECORD_ID = "5ae76c625542997ec272763e"
    
    pipeline = GovRAG_Pipeline(MY_RECORD_ID)
    pipeline.run()