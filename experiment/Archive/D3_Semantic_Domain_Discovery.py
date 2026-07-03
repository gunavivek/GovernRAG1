import json
import os
import time
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

# --- PhD Rigor Environment Setup ---
load_dotenv()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

class D3Discovery:
    """
    D3: Semantic Discovery & Ontological Regulator
    Function: Runtime Ontological Architect.
    Objective: Resolves ORPHAN records by engineering new BIZBOK verticals 
               and updating the central Mapping Registry.
    """
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL ERROR: OPENAI_API_KEY not found in .env file.")
        
        self.client = OpenAI(api_key=api_key)
        self.cache_path = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Recommendations.json")
        self.mapping_path = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=4)

    def discover_domain(self, record_text: str, d1_domain: str) -> Dict:
        """
        Governed Synthesis: Intersects IEEE 1074 requirements with Document Context.
        """
        prompt = f"""
        Role: BIZBOK® Lead Architect & Knowledge Engineer.
        Standard: IEEE 1074-2006 (Requirement-Driven Discovery).
        
        TOP-LEVEL CONTEXT (D1): "{d1_domain}"
        EXISTING DISCOVERED VERTICALS: {list(self.cache.keys()) if self.cache else "None"}
        
        RAW DATA RECORD: "{record_text[:1500]}"
        
        TASK:
        1. DECOMPOSE: Do NOT return "{d1_domain}". Break it into a specific BIZBOK Level-1 Industry Vertical (e.g., 'Professional Sports', 'Aerospace').
        2. RECURSIVE REUSE: If the record fits an 'EXISTING DISCOVERED VERTICAL' above, return that EXACT name.
        3. M-PIPELINE GUIDANCE: Define the 3 most important Entity Types to extract for this vertical.
        4. GROUNDING: Formulate a 'Competency Question' (CQ) this domain resolves for the Knowledge Graph.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "domain": "Vertical Name (Title Case)",
            "description": "Functional purpose.",
            "mapping_instruction": "Extraction focus.",
            "competency_question": "Logical anchor for Q-Pipeline."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a professional Business Architect specializing in Ontological Decomposition."},
                          {"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            data = json.loads(response.choices[0].message.content)
            data["domain"] = data["domain"].strip().title()
            return data
        except Exception as e:
            print(f"  D3 API Error: {e}")
            return None

    def run_discovery_pipeline(self):
        RAW_INPUT = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl")
        
        if not os.path.exists(self.mapping_path):
            print("CRITICAL: D2 Mapping file not found. Run D2 first.")
            return

        # 1. Load the Registry (The Golden Thread)
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            full_mapping = [json.loads(line) for line in f]
        
        # 2. Load Raw Text for Context
        with open(RAW_INPUT, 'r', encoding='utf-8') as f:
            raw_data = {json.loads(line)['id']: json.loads(line) for line in f}

        updated_mapping = []
        discovery_count = 0

        print(f"--- D3 Discovery: Resolving Registry Orphans ---")

        for entry in full_mapping:
            if entry["assigned_domain"] == "ORPHAN":
                record_id = entry["record_id"]
                # Retrieve text context (Question + Documents)
                record_text = raw_data[record_id].get("question", "") + " " + " ".join(raw_data[record_id].get("documents", []))
                
                # Perform Discovery
                # Note: In a production run, D1 context would be pulled from D2 audit log
                # Here we default to 'General Knowledge' for discovery grounding
                discovery = self.discover_domain(record_text, "General Knowledge")
                
                if discovery:
                    domain_name = discovery["domain"]
                    
                    # Update Mapping Registry (Stateful Resolution)
                    entry["assigned_domain"] = domain_name
                    entry["mapping_source"] = "D3_DISCOVERY"
                    
                    # Update Cache if it's a new vertical
                    if domain_name not in self.cache:
                        print(f"  [NEW DOMAIN] {domain_name} discovered for {record_id}")
                        self.cache[domain_name] = {
                            "description": discovery["description"],
                            "mapping_instruction": discovery["mapping_instruction"],
                            "competency_question": discovery["competency_question"]
                        }
                        self._save_cache()
                        discovery_count += 1
                    else:
                        print(f"  [RESOLVED] {record_id} mapped to existing {domain_name}")
            
            updated_mapping.append(entry)

        # 3. Persist the updated "Golden Thread"
        with open(self.mapping_path, 'w', encoding='utf-8') as f:
            for entry in updated_mapping:
                f.write(json.dumps(entry) + "\n")

        print(f"\n--- D3 Complete. {discovery_count} New Verticals Added. Registry Updated. ---")

if __name__ == "__main__":
    d3 = D3Discovery()
    d3.run_discovery_pipeline()