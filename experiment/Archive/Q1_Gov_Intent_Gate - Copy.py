import json
import os
from typing import Dict, Any, List

# --- Project Paths ---
D5_MANIFEST_PATH = "output/D5_Extraction_Manifest.jsonl"
OUTPUT_FILE = "output/Q1_intent_gate.jsonl"

class GovernedIntentGate:
    def __init__(self):
        self.doc_boundary = "| Document:" 
        # PhD Logic: Semantic Complexity Hierarchy mapped to Traversal Depth
        self.intent_hierarchy = {"Inferential": 3, "Comparison": 2, "Extractive": 1}

    def _detect_domain_overlap(self, question: str, profiles: List[Dict]) -> List[str]:
        """Identifies if the question spans multiple BA Domain ontologies (M5)."""
        q = question.lower()
        active_domains = []
        for p in profiles:
            # Matches question keywords against BA relational predicates
            predicates = p.get("rules", {}).get("relational_predicates", [])
            if any(pred.lower() in q for pred in predicates):
                active_domains.append(p.get("domain"))
        return list(set(active_domains))

    def _detect_complexity_path(self, question: str) -> str:
        """
        Structural Complexity Analysis for Dissertation Evaluation.
        Path A: Atomic (Single BA concept lookup)
        Path B: Relational (Cross-concept bridging required - triggers Q3.5 loop)
        """
        q = question.lower()
        
        # B-Path Triggers: Markers indicating relational dependencies between entities
        relational_markers = [
            "'s", "of the", "who is the", "whose", "born on", 
            "founded by", "created by", "opening of", "impact on",
            "relationship between", "associated with"
        ]
        
        if any(marker in q for marker in relational_markers):
            return "B"  
        return "A"      

    def _decompose_intents(self, question: str, overlapped_domains: List[str]) -> List[str]:
        """Maps inquiry to Semantic Intent Classes for k-hop scaling."""
        q = question.lower()
        found = ["Extractive"]
        
        comp_triggers = ["both", "compare", "difference", "versus", "between", 
                         "earlier", "later", "more", "most", "than"]
        
        if len(overlapped_domains) > 1 or any(w in q for w in comp_triggers):
            found.append("Comparison")
        
        if any(w in q for w in ["why", "how", "reason", "because", "consider", "consequence"]):
            found.append("Inferential")
            
        return list(set(found))

    def process(self):
        print("--- Q1: Governed Intent Gate (BA Domain Strategy Mode) ---")
        
        if not os.path.exists(D5_MANIFEST_PATH):
            print(f"[FATAL] Missing input: {D5_MANIFEST_PATH}")
            return

        count = 0
        with open(D5_MANIFEST_PATH, 'r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                if not line.strip(): continue
                data = json.loads(line)
                
                # 1. Epistemic Isolation: Extract clean inquiry from manifest
                raw_source = data.get("source_text", "")
                clean_question = raw_source.split(self.doc_boundary)[0].replace("Question:", "").strip()
                
                # 2. BA Structural & Semantic Analysis
                profiles = data.get("governance_profile", [])
                
                # Path Detection (A vs B)
                complexity_path = self._detect_complexity_path(clean_question)
                
                # Domain & Intent Class Detection
                overlapped_domains = self._detect_domain_overlap(clean_question, profiles)
                all_intents = self._decompose_intents(clean_question, overlapped_domains)
                
                # 3. Decision Logic: Resolve Primary Strategy
                primary_intent = max(all_intents, key=lambda x: self.intent_hierarchy[x])
                primary_profile = max(profiles, key=lambda x: x.get('affinity_weight', 0)) if profiles else {}
                
                # 4. Generate Positioned Justification (Audit Trail for Dissertation)
                justification = {
                    "logic": f"Primary intent [{primary_intent}] on Complexity Path [{complexity_path}].",
                    "domain_focus": overlapped_domains if overlapped_domains else [primary_profile.get("domain")],
                    "recursive_flag": "ENABLED" if complexity_path == "B" else "DISABLED"
                }

                # 5. Build Unified Packet
                q1_packet = {
                    "id": data.get("record_id"),
                    "question": clean_question,
                    "primary_intent": primary_intent,
                    "complexity_path": complexity_path,
                    "justification": justification,
                    "traversal_parameters": {
                        "k_hops": self.intent_hierarchy[primary_intent],
                        "recursive_expansion": complexity_path == "B",
                        "ba_triangulate": primary_intent == "Comparison"
                    },
                    "governed_context": {
                        "active_domains": justification["domain_focus"],
                        "primary_laws": primary_profile.get("rules", {})
                    }
                }
                
                outfile.write(json.dumps(q1_packet, ensure_ascii=False) + '\n')
                count += 1
        
        print(f"--- SUCCESS: {count} BA-Intent Packets generated (Path B logic enabled) ---")

if __name__ == "__main__":
    GovernedIntentGate().process()