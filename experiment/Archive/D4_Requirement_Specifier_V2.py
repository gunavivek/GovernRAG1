import json
import os
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

# --- PhD Rigor Environment Setup ---
load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class D4RequirementSpecifierV2:
    """
    D4: Requirement Engineering Module (V2)
    Logic: Statistical Governance (BIZBOK + Z-Score Calibration)
    Objective: Generate high-fidelity Governance Packets for M and Q pipelines.
    """
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        self.pioneer_path = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Pioneer.json")
        self.discovered_path = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Discovered.json")
        self.d3_output_path = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Recommendations.json")
        
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

    def generate_governed_specification(self, domain_name: str, d3_meta: Dict) -> Dict:
        """
        Synthesizes IEEE 1074 requirements using D3 Discovery context.
        """
        # 1. Registry Check
        if domain_name in self.pioneer_registry:
            return self.pioneer_registry[domain_name]
        if domain_name in self.discovered_registry:
            return self.discovered_registry[domain_name]

        # 2. Extract Context from D3 (Critical for the 'Golden Thread')
        description = d3_meta.get("description", "")
        comp_question = d3_meta.get("competency_question", "")
        z_score = d3_meta.get("origin_z_score", 0.0) # Pulled from your D3_V2 update

        print(f"  [D4 V2] Engineering Policy for: {domain_name} (Z-Score: {z_score:.2f})")
        
        prompt = f"""
        Role: BIZBOK® Lead Architect.
        Standard: IEEE 1074-2006 (Governed Extraction Requirements).
        
        TARGET DOMAIN: "{domain_name}"
        DOMAIN CONTEXT: {description}
        COMPETENCY QUESTION: "{comp_question}"
        STATISTICAL DISTANCE: {z_score} sigma (Distance from BIZBOK Centroid).
        
        TASK:
        Generate a 'Governance Packet' that defines how the M-Pipeline (Extraction) 
        and Q-Pipeline (Query) must operate in this high-entropy domain.
        
        REQUIREMENTS:
        1. RELATIONAL PREDICATES: 5 Industry-standard verbs for Knowledge Graph Triples.
        2. SEARCH DEPTH: Assign an integer (1-5). Use depth > 3 if Z-score > 5.0.
        3. ENTITY CONSTRAINTS: Identify 3 unique entity types specific to this vertical.
        4. SUCCESS METRIC: Define the primary metric (e.g., 'Historical Fidelity', 'Technical Precision').

        OUTPUT FORMAT (JSON ONLY):
        {{
            "relational_predicates": ["...", "...", "...", "...", "..."],
            "search_exit_depth": int,
            "entity_constraints": ["...", "...", "..."],
            "success_metrics": {{ "primary": "...", "threshold": "..." }}
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a BIZBOK Governance Officer."},
                          {"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            spec = json.loads(response.choices[0].message.content)
            
            self.discovered_registry[domain_name] = {
                "domain": domain_name,
                "z_score_calibration": z_score,
                "governance_packet": spec,
                "competency_anchor": comp_question
            }
            self._save_discovered()
            return self.discovered_registry[domain_name]
            
        except Exception as e:
            print(f"  D4 API Error: {e}")
            return None

    def run_requirement_pipeline(self):
        if not os.path.exists(self.d3_output_path):
            print("ERROR: D3 recommendations not found. Run D3 first.")
            return

        with open(self.d3_output_path, 'r', encoding='utf-8') as f:
            d3_data = json.load(f)

        print("--- D4 V2: Engineering Statistical Governance Packets ---")
        
        for domain, metadata in d3_data.items():
            self.generate_governed_specification(domain, metadata)

        print(f"\n--- D4 Complete. Master Governance at: {self.discovered_path} ---")

if __name__ == "__main__":
    d4 = D4RequirementSpecifierV2()
    d4.run_requirement_pipeline()