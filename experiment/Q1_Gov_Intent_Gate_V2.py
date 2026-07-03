import json
import os
from typing import Dict, Any, List

# --- Project Paths ---
D5_MANIFEST_PATH = "output/D5_Extraction_Manifest.jsonl"
OUTPUT_FILE = "output/Q1_intent_gate.jsonl"

class GovernedIntentGateV2:
    def __init__(self):
        self.doc_boundary = "| Document:" 
        
        # PHD DESIGN COMPONENT: Strategic Intent Hierarchy
        # Maps Semantic Intent to Traversal Depth (k-hops) for Search Optimization
        self.intent_hierarchy = {"Inferential": 3, "Comparison": 2, "Extractive": 1}

        # PHD DESIGN COMPONENT: Functional Categories
        # Maps Natural Language cues to Business Architecture (BA) Predicate Families
        self.functional_categories = {
            "Temporal": ["end", "start", "when", "date", "time", "year", "opened", "closed", "finish", "conclude"],
            "Spatial": ["where", "location", "place", "city", "country", "based", "situated", "headquartered"],
            "Identity": ["who", "name", "founder", "author", "creator", "directed", "built", "by"],
            "Quantity": ["how many", "how much", "count", "amount", "total", "number of", "price", "cost", "worth", "for how much"]
        }

    def _resolve_functional_intent(self, question: str) -> str:
        """Identifies the high-level functional category for Q2 Signature selection."""
        q = question.lower()
        for category, keywords in self.functional_categories.items():
            if any(word in q for word in keywords):
                return category
        return "General_Relation"

    def _detect_complexity_path(self, question: str) -> str:
        """
        PHD COMPONENT: Execution Strategy Selection.
        Path A (Atomic): Direct lookup for high-efficiency extraction.
        Path B (Relational): Triggers Q3.5 Bridge Discovery for multi-hop graph walks.
        """
        q = question.lower()
        relational_markers = [
            "'s", "of the", "who is the", "whose", "born on", 
            "founded by", "created by", "opening of", "impact on",
            "relationship between", "associated with"
        ]
        return "B" if any(marker in q for marker in relational_markers) else "A"

    def _decompose_intents(self, question: str) -> List[str]:
        """Maps inquiry to Intent Classes for k-hop scaling."""
        q = question.lower()
        found = ["Extractive"]
        comp_triggers = ["both", "compare", "difference", "versus", "between",
                       "earlier", "later", "more", "most", "than"]
        if any(w in q for w in comp_triggers):
            found.append("Comparison")
        inferential_triggers = ["why", "reason", "because", "consider", "consequence"]
        if any(w in q for w in inferential_triggers):
            found.append("Inferential")
        return list(set(found))

    def process(self):
        print("--- Q1 V2: Governed Intent Gate (Frozen DSR State) ---")
        
        if not os.path.exists(D5_MANIFEST_PATH):
            print(f"[FATAL] Missing input: {D5_MANIFEST_PATH}")
            raise SystemExit(1)

        count = 0
        with open(D5_MANIFEST_PATH, 'r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                if not line.strip(): continue
                data = json.loads(line)
                
                # 1. Epistemic Isolation: Extract the specific research question
                raw_source = data.get("source_text", "")
                clean_question = raw_source.split(self.doc_boundary)[0].replace("Question:", "").strip()
                
                if data.get("record_id") is None:
                    raise ValueError("Missing record_id in input manifest row")
                if not clean_question:
                    raise ValueError(f"Empty question extracted for record_id={data.get('record_id')}")

                # 2. HYBRID ARCHITECTURAL INHERITANCE (The 90% Competitive Affinity Rule)
                # Strategy: If the gap between domains is < 10%, we authorize both to prevent recall loss.
                profiles = data.get("governance_profile", [])
                if not profiles:
                    active_profiles = [{"domain": "General", "rules": {}}]
                else:
                    # Select domains within the competitive threshold: affinity >= (max_affinity * 0.9)
                    top_affinity = max(p.get('affinity_weight', 0) for p in profiles)
                    threshold = top_affinity * 0.90 
                    active_profiles = [p for p in profiles if p.get('affinity_weight', 0) >= threshold]
                
                enforced_domains = [p.get("domain") for p in active_profiles]
                
                # Merge Predicates from all authorized domains for the Q2 Search Warrant
                merged_rules = {"relational_predicates": [], "disambiguation_keys": {}}
                for p in active_profiles:
                    rules = p.get("rules", {})
                    merged_rules["relational_predicates"].extend(rules.get("relational_predicates", []))
                    merged_rules["disambiguation_keys"].update(rules.get("disambiguation_keys", {}))
                
                merged_rules["relational_predicates"] = list(set(merged_rules["relational_predicates"]))

                # 3. BA Structural & Functional Analysis
                complexity_path = self._detect_complexity_path(clean_question)
                all_intents = self._decompose_intents(clean_question)
                target_functional_intent = self._resolve_functional_intent(clean_question)
                
                # Resolve Primary Intent Class to determine Graph Hop Depth
                primary_intent = max(all_intents, key=lambda x: self.intent_hierarchy[x])
                
                # 4. Generate Positioned Justification (The Audit Trail)
                justification = {
                    "logic": f"Hybrid Domains {enforced_domains} | Intent [{primary_intent}] | Path [{complexity_path}]",
                    "domain_focus": enforced_domains, 
                    "recursive_flag": "ENABLED" if complexity_path == "B" else "DISABLED",
                    "target_functional_intent": target_functional_intent 
                }

                # 5. Build Unified Packet (UNIFIED NAMESPACE)
                q1_packet = {
                    "record_id": data.get("record_id"),
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
                        "active_domains": enforced_domains,
                        "primary_laws": merged_rules, 
                        "functional_intent": target_functional_intent
                    }
                }
                
                outfile.write(json.dumps(q1_packet, ensure_ascii=False) + '\n')
                count += 1
        
        print(f"--- SUCCESS: {count} Concept-Aware Intent Packets generated ---")

if __name__ == "__main__":
    GovernedIntentGateV2().process()