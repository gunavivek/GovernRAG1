import json
import os
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

# --- PhD Rigor Environment Setup ---
load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class D4RequirementSpecifier:
    """
    D4: Requirement Engineering Module
    Logic: Governed Synthesis (BIZBOK Standards + Document Context)
    Objective: Generate the Domain Control Packet for M and Q pipelines.
    """
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # Paths for the Registry System
        self.pioneer_path = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Pioneer.json")
        self.discovered_path = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Discovered.json")
        
        # Load existing specifications
        self.pioneer_registry = self._load_json(self.pioneer_path)
        self.discovered_registry = self._load_json(self.discovered_path)

    def _load_json(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_discovered(self):
        with open(self.discovered_path, 'w', encoding='utf-8') as f:
            json.dump(self.discovered_registry, f, indent=4)

    def generate_governed_specification(self, domain_name: str, parent_context: str, record_text: str) -> Dict:
        """
        Intersects BIZBOK standards with Document context.
        """
        # 1. Check Pioneer Registry (Static BIZBOK)
        if domain_name in self.pioneer_registry:
            print(f"  [D4 PIONEER] Applying existing BIZBOK standard for: {domain_name}")
            return self.pioneer_registry[domain_name]

        # 2. Check Discovered Registry (Previously synthesized)
        if domain_name in self.discovered_registry:
            return self.discovered_registry[domain_name]

        # 3. Dynamic Synthesis (New Vertical Discovery)
        print(f"  [D4 SYNTHESIS] Engineering requirements for NEW domain: {domain_name}")
        
        prompt = f"""
        Role: BIZBOK® Lead Architect & IEEE 1074 Compliance Officer.
        
        CONTEXT:
        Discovered Industry Vertical: "{domain_name}"
        Parent BIZBOK Category: "{parent_context}"
        Sample Data Record: "{record_text[:1000]}..."
        
        TASK:
        Perform 'Requirement Engineering' to define the operational parameters for this domain's Knowledge Graph cluster.
        
        GOVERNANCE REQUIREMENTS:
        1. RELATIONAL PREDICATES: Provide 5 high-fidelity verbs standard to this industry (Subject-Predicate-Object).
        2. SEARCH DEPTH: Assign a search hop limit (1-5) based on complexity (e.g. Facts=2, Policy=4).
        3. DISAMBIGUATION: Identify industry-specific meanings for ambiguous terms in the text.
        4. SUCCESS METRIC: Define the primary metric (e.g., 'Numerical Accuracy', 'Temporal Provenance', 'Legal Adherence').

        OUTPUT FORMAT (JSON ONLY):
        {{
            "relational_predicates": ["verb1", "verb2", "verb3", "verb4", "verb5"],
            "search_exit_depth": int,
            "disambiguation_keys": {{ "term": "definition" }},
            "success_metrics": {{ "primary": "...", "secondary": "..." }}
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a professional Business Architect."},
                          {"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            spec = json.loads(response.choices[0].message.content)
            
            # Store in Discovered Registry
            self.discovered_registry[domain_name] = {
                "domain": domain_name,
                "parent_context": parent_context,
                "specification_source": "D4_DYNAMIC_SYNTHESIS",
                "governance_packet": spec
            }
            self._save_discovered()
            return self.discovered_registry[domain_name]
            
        except Exception as e:
            print(f"  D4 API Error: {e}")
            return None

    def run_requirement_pipeline(self):
        D3_OUTPUT = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Recommendations.json")
        RAW_INPUT = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl") # Use 10 record version
        
        with open(D3_OUTPUT, 'r', encoding='utf-8') as f:
            d3_data = json.load(f)
        with open(RAW_INPUT, 'r', encoding='utf-8') as f:
            raw_data = {json.loads(line)['id']: json.loads(line) for line in f}

        print("--- D4 Requirement Engineering: Building Governance Packets ---")
        
        for domain, metadata in d3_data.items():
            # Get parent context and find a sample document that triggered this domain
            parent = metadata.get("parent_context", "common")
            
            # In D4, we only need to spec a domain ONCE. 
            # We use the first document associated with this domain as the contextual grounding.
            sample_text = "N/A - Pioneer Domain"
            # Find the first record in raw_data that D3 associated with this domain
            # (In a real run, D5 would pass this more elegantly, but here we process the cache)
            
            self.generate_governed_specification(domain, parent, sample_text)

        print(f"\n--- D4 Complete. Master Governance at: {self.discovered_path} ---")

if __name__ == "__main__":
    d4 = D4RequirementSpecifier()
    d4.run_requirement_pipeline()