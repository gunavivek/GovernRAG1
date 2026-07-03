import json
import os
import sys
import numpy as np
from typing import Dict, List
from openai import OpenAI
from google import genai
from dotenv import load_dotenv

# --- PhD Rigor Setup ---
load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class D3MultiDiscoveryV22:
    def __init__(self):
        # 1. Identity & Client Setup
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key: raise ValueError("CRITICAL: OPENAI_API_KEY missing.")
        self.client = OpenAI(api_key=api_key)

        # 2. Path Management (Core Functionality)
        self.cache_path = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Discovery.json")
        self.mapping_path = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")
        self.raw_data_path = os.path.join(PROJECT_ROOT, "data", "RGB_Single_Record.jsonl")
        #self.raw_data_path = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl")
        
        # 3. Memory Initialization (Recursive Reuse)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_embedding(self, text: str):
        """Generates 3072-dim vector for Semantic Affinity (Wa) calculation."""
        res = genai_client.models.embed_content(model='gemini-embedding-001', contents=text)
        return np.array(res.embeddings[0].values)

    def discover_poly_ontological(self, text: str, record_id: str) -> List[Dict]:
        """Core D3 Discovery: Synthesizes BIZBOK Industry Verticals."""
        prompt = f"""
        Role: BIZBOK® Lead Architect. Standard: IEEE 1074-2006.
        EXISTING VERTICALS: {list(self.cache.keys())}
        
        DATA: "{text[:1500]}"
        
        TASK:
        1. DECOMPOSE: Identify 1-3 specific BIZBOK Level-1 Industry Verticals.
        2. RECURSIVE REUSE: If a vertical exists in the list above, use that EXACT name.
        3. OUTPUT JSON: {{"domains": [{{"name": "...", "description": "...", "mapping_instruction": "...", "competency_question": "..."}}]}}
        """
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a professional Ontologist."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content).get("domains", [])

    def run_discovery_pipeline(self):
        print(f"--- D3_V22: Executing Weighted Poly-Ontological Discovery ---")
        
        # 1. Load Registry & Raw Data
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            full_mapping = [json.loads(line) for line in f]
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            raw_data = {json.loads(line)['id']: json.loads(line) for line in f}

        updated_mapping = []
        record_vec_cache = {}

        for entry in full_mapping:
            if entry.get("assigned_domain") == "ORPHAN" or "domain_affinities" not in entry:
                rid = entry["record_id"]
                # --- CRITICAL FIX: Gracefully handle both Strings and Lists ---
                raw_context = raw_data[rid].get("context", "")
                context_str = " ".join(raw_context) if isinstance(raw_context, list) else str(raw_context)
                text = raw_data[rid].get("question", "") + " " + context_str
                # text = raw_data[rid].get("question", "") + " " + " ".join(raw_data[rid].get("context", []))
                
                # Perform Discovery
                discovered_list = self.discover_poly_ontological(text, rid)
                
                # Calculate Affinity Weights (Wa)
                r_vec = self.get_embedding(text)
                affinities = {}
                raw_sims = []
                
                for d in discovered_list:
                    d_name = d['name'].title()
                    # Recursive Cache Update
                    if d_name not in self.cache:
                        # --- SCALABLE FIX: Stamp the domain with its origin data ---
                        d['origin_record'] = rid
                        d['origin_z_score'] = entry.get("z_score", 0.0)
                        self.cache[d_name] = d
                    
                    # Math: Cosine Similarity for Wa
                    d_vec = self.get_embedding(f"{d_name} {d['description']}")
                    sim = np.dot(r_vec, d_vec) / (np.linalg.norm(r_vec) * np.linalg.norm(d_vec))
                    raw_sims.append((d_name, sim))

                # Normalize Wa
                total_sim = sum(s[1] for s in raw_sims)
                for name, sim in raw_sims:
                    affinities[name] = {"wa": round(float(sim/total_sim), 4)}

                # Update Registry (The Golden Thread Persistence)
                entry["domain_affinities"] = affinities
                entry["assigned_domains"] = list(affinities.keys())
                entry["mapping_source"] = "D3_V22_SALIENT_WEIGHTED"
                entry.pop("assigned_domain", None) # Clean up old orphan tag

            updated_mapping.append(entry)

        # 2. Final Atomic Persistence
        with open(self.mapping_path, 'w', encoding='utf-8') as f:
            for entry in updated_mapping: f.write(json.dumps(entry) + "\n")
            
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=4)

        print(f"--- D3 Complete. Registry and Discovery Library Updated. ---")

if __name__ == "__main__":
    D3MultiDiscoveryV22().run_discovery_pipeline()