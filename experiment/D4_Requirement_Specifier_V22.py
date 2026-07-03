import json
import os
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

# --- PhD Rigor Environment Setup ---
load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class D4RequirementSpecifierV22:
    """
    D4: Requirement Engineering Module (V22)
    Logic: Governed synthesis with document grounding and structured requirement-style packet generation
    Objective: Transform Discovery outputs into machine-executable Domain Control Packets.
    """
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # Paths for Persistence and Registries 
        self.pioneer_path = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Pioneer.json")
        self.discovered_path = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Discovered.json")
        self.d3_output_path = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Discovery.json")
        self.raw_data_path = os.path.join(PROJECT_ROOT, "data", "RGB_Single_Record.jsonl")
        
        self.pioneer_registry = self._load_json(self.pioneer_path)
        # Paper-freeze mode: start with an empty discovered registry for each run
        # to avoid cross-record contamination in controlled evaluation.
        #self.discovered_registry = self._load_json(self.discovered_path)
        self.discovered_registry = {}
        
        # Load raw text to ensure Disambiguation & Predicate Grounding 
        self.raw_records = {}
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                rid = rec.get("id")
                if rid is None or str(rid).strip() == "":
                    continue
                self.raw_records[str(rid).strip()] = rec
        
    def _load_json(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_discovered(self):
        """Append and persist the new spec to ensure future ontological consistency-Enterprise version.
        Persist the discovered governance packets for the current evaluation run-single run freeze version."""
        with open(self.discovered_path, 'w', encoding='utf-8') as f:
            json.dump(self.discovered_registry, f, indent=4)

    def generate_governed_specification(self, domain_name: str, d3_meta: Dict) -> Dict:
        """
        Synthesizes technical requirements using a 'Lookup-First' pattern.
        """
        # 1. Lookup-First Pattern: Check Pioneer Registry then Discovered 
        if domain_name in self.pioneer_registry:
            return self.pioneer_registry[domain_name]
        if domain_name in self.discovered_registry:
            return self.discovered_registry[domain_name]

        # 2. Contextual Grounding Retrieval 
        origin_id = d3_meta.get("origin_record")
        
        raw_rec = self.raw_records.get(origin_id, {})
        raw_context = raw_rec.get("context", "Context unavailable.")
        raw_text = " ".join(raw_context) if isinstance(raw_context, list) else str(raw_context)
        
        description = d3_meta.get("description", "")
        comp_question = d3_meta.get("competency_question", "")
        z_score = d3_meta.get("origin_z_score", 0.0)

        print(f"  [D4 V22] Engineering Policy for: {domain_name} (Grounded in Record {origin_id})")
        
        # Rigorous prompt for Governed Synthesis 
        prompt = f"""
        Role: Senior Business Architect responsible for domain governance and structured requirement design.
                
        TARGET DOMAIN: "{domain_name}"
        DOMAIN CONTEXT: {description}
        COMPETENCY QUESTION: "{comp_question}"
        STATISTICAL DISTANCE: {z_score} sigma.
        
        GROUNDING DATA (Raw Context): "{raw_text[:1200]}"
        
        TASK:
        Generate a 'Domain Control Packet' (Governance Packet) defining M-Pipeline (Extraction) 
        and Q-Pipeline (Query) operational rules for this business domain.
        
        REQUIREMENTS:
        1. RELATIONAL PREDICATES: 5 domain-relevant mandatory verbs evidenced in the text.
        2. SEARCH DEPTH: Integer (1-5). Use depth > 3 if Z-score > 5.0.
        3. DISAMBIGUATION: Define 3 potentially ambiguous terms from the source text that are important to this business domain.
        4. SUCCESS METRIC: Define standard benchmarks (e.g., Technical Precision).

        OUTPUT FORMAT (JSON ONLY):
        {{
            "relational_predicates": ["...", "...", "...", "...", "..."],
            "search_exit_depth": int,
            "disambiguation_keys": {{ "term": "definition" }},
            "success_metrics": {{ "primary": "...", "threshold": "..." }}
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a senior business architect and governance designer."},
                          {"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                temperature=0.0,
                seed=42
            )
            spec = json.loads(response.choices[0].message.content)
            
            # 3. Persistence and Registration
            # Fixed double brace issue by using standard dict construction
            self.discovered_registry[domain_name] = {
                "domain": domain_name,
                "provenance": {
                    "origin_record": origin_id,
                    "z_score_calibration": z_score,
                    "competency_anchor": comp_question
                },
                "governance_packet": spec
            }
            self._save_discovered()
            return self.discovered_registry[domain_name]
            
        except Exception as e:
            # Critical error logging for PhD audit trail
            print(f"  D4 API Error: {str(e)}")
            return None

    def run_requirement_pipeline(self):
        """Execute the engineering cycle for all newly discovered domains."""
        if not os.path.exists(self.d3_output_path):
            print("ERROR: D3 library (D3_Domain_Discovery.json) not found.")
            return

        with open(self.d3_output_path, 'r', encoding='utf-8') as f:
            d3_data = json.load(f)

        print("--- D4 V22: Engineering Governed Domain Policies ---")
        
        for domain, metadata in d3_data.items():
            self.generate_governed_specification(domain, metadata)

        print(f"\n--- D4 Complete. Master Governance Registry at: {self.discovered_path} ---")

if __name__ == "__main__":
    d4 = D4RequirementSpecifierV22()
    d4.run_requirement_pipeline()