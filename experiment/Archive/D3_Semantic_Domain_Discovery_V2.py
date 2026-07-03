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

class D3DiscoveryV2:
    """
    D3: Statistical Semantic Discovery & Ontological Regulator
    Function: Runtime Ontological Architect.
    Objective: Resolves ORPHAN records by engineering new BIZBOK verticals.
    V2 Update: Integrates D2_V2 Z-Scores to calibrate discovery resolution.
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

    def discover_domain(self, record_text: str, d1_domain: str, z_score: float) -> Dict:
        """
        Governed Synthesis: Uses Z-Score to determine ontological distance.
        """
        # PhD Calibration: Higher Z-scores indicate a need for more granular decomposition
        entropy_level = "EXTREME" if z_score > 8.0 else "MODERATE"
        
        prompt = f"""
        Role: BIZBOK® Lead Architect & Knowledge Engineer.
        Standard: IEEE 1074-2006 (Requirement-Driven Discovery).
        
        STATISTICAL CONTEXT: 
        - Semantic Distance (Z-Score): {z_score:.2f}
        - Ontological Entropy: {entropy_level}
        - Top-Level Domain (D1): "{d1_domain}"
        
        EXISTING DISCOVERED VERTICALS: {list(self.cache.keys()) if self.cache else "None"}
        
        RAW DATA RECORD: "{record_text[:1800]}"
        
        TASK:
        1. DECOMPOSE: Break the content into a specific BIZBOK Level-1 Industry Vertical.
        2. ENTROPY ADJUSTMENT: Since the Z-score is {z_score:.2f}, ensure the domain name is highly specific.
        3. RECURSIVE REUSE: If the record fits an 'EXISTING DISCOVERED VERTICAL' above, reuse that EXACT name.
        4. GROUNDING: Formulate a 'Competency Question' (CQ) for the M-Pipeline Knowledge Graph.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "domain": "Vertical Name (Title Case)",
            "description": "Functional purpose.",
            "mapping_instruction": "Extraction focus based on entropy.",
            "competency_question": "Logical anchor for Q-Pipeline.",
            "statistical_provenance": "Validated against Z-score {z_score}"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": f"You are a Business Architect resolving semantic orphans with Z-score {z_score}."},
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
            print("CRITICAL: D2_V2 Mapping file not found. Ensure D2_V2 execution is complete.")
            return

        # 1. Load the Mapping Registry (Now includes Z-scores from D2_V2)
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            full_mapping = [json.loads(line) for line in f]
        
        # 2. Load Raw Text for Context
        if not os.path.exists(RAW_INPUT):
            print(f"CRITICAL: {RAW_INPUT} missing.")
            return
            
        with open(RAW_INPUT, 'r', encoding='utf-8') as f:
            raw_data = {}
            for line in f:
                item = json.loads(line)
                raw_data[item['id']] = item

        updated_mapping = []
        discovery_count = 0

        print(f"--- D3_V2 Discovery: Resolving Statistical Orphans ---")

        for entry in full_mapping:
            if entry["assigned_domain"] == "ORPHAN":
                record_id = entry["record_id"]
                z_val = entry.get("z_score", 0.0)
                
                # Context Retrieval
                record = raw_data.get(record_id, {})
                context_str = record.get("question", "") + " " + " ".join(record.get("context", []))
                
                # Perform Discovery with Z-score weighting
                discovery = self.discover_domain(context_str, "General Knowledge", z_val)
                
                if discovery:
                    domain_name = discovery["domain"]
                    entry["assigned_domain"] = domain_name
                    entry["mapping_source"] = "D3_STATISTICAL_DISCOVERY"
                    
                    # Store discovery logic in cache
                    if domain_name not in self.cache:
                        print(f"  [NEW DOMAIN] {domain_name} (Z={z_val:.2f})")
                        self.cache[domain_name] = {
                            "description": discovery["description"],
                            "mapping_instruction": discovery["mapping_instruction"],
                            "competency_question": discovery["competency_question"],
                            "origin_z_score": z_val
                        }
                        self._save_cache()
                        discovery_count += 1
                    else:
                        print(f"  [RESOLVED] {record_id} -> {domain_name} (Cluster Member)")
            
            updated_mapping.append(entry)

        # 3. Persist the updated "Golden Thread"
        with open(self.mapping_path, 'w', encoding='utf-8') as f:
            for entry in updated_mapping:
                f.write(json.dumps(entry) + "\n")

        print(f"\n--- D3 Complete. {discovery_count} New Verticals Synthesized. Registry Updated. ---")

if __name__ == "__main__":
    d3 = D3DiscoveryV2()
    d3.run_discovery_pipeline()