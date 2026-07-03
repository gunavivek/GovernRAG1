import json
import os
import numpy as np
import time
from typing import Dict, List
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- PhD Rigor Setup ---
load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_DIM = 768  # MUST match R4 and D2!
RATE_LIMIT_DELAY = 0 # Optimized for text-embedding-001

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
        
        # 3. Memory Initialization (Recursive Reuse in Enterprise Domain Discovery)
        #self.cache = self._load_cache()
        
        # 3. Memory Initialization
        # Paper-freeze mode: start with an empty in-memory cache for every run
        # to prevent cross-record contamination and order-dependent discovery.
        self.cache = {}

    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def get_embedding(self, text: str):
        """Generates 768-dim vector for Semantic Affinity (Wa) calculation."""
        time.sleep(RATE_LIMIT_DELAY)
        res = genai_client.models.embed_content(
            model='models/gemini-embedding-001', 
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
        )
        return np.array(res.embeddings[0].values)

    def discover_poly_ontological(self, text: str, record_id: str) -> List[Dict]:
        """Core D3 Discovery: Synthesizes BIZBOK Industry Verticals."""
        prompt = f"""
        Role: BIZBOK® Lead Architect.
        EXISTING VERTICALS: []
        
        DATA: "{text[:1500]}"
        
        TASK:
        1. DECOMPOSE: Identify 1-3 specific BIZBOK Level-1 Industry Verticals.
        2. RECURSIVE REUSE: If a vertical exists in the list above, use that EXACT name.
        3. OUTPUT JSON: {{"domains": [{{"name": "...", "description": "...", "mapping_instruction": "...", "competency_question": "..."}}]}}
        4. CANONICALIZE: Prefer broad, reusable industry vertical names. Do not return near-duplicate synonyms.
        5. If two candidate labels overlap strongly, choose only one canonical label.
        6. Return domains ordered from most salient to least salient.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a professional Ontologist."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
                seed=42
            )
            return json.loads(response.choices[0].message.content).get("domains", [])
        except Exception as e:
            print(f"D3 LLM Generation Error: {e}")
            return []

    def run_discovery_pipeline(self):
        print(f"--- D3_V22: Executing Weighted Poly-Ontological Discovery (Embedded Math) ---")
        
        if not os.path.exists(self.mapping_path):
            print(f"ERROR: Mapping file missing at {self.mapping_path}")
            return
            
        # 1. Load Registry & Raw Data
        full_mapping = []
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    full_mapping.append(json.loads(line))
                    
        raw_data = {}
        if os.path.exists(self.raw_data_path):
            with open(self.raw_data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        raw_id = record.get('id', record.get('_id'))
                        if raw_id is None or str(raw_id).strip() == "":
                            continue
                        raw_data[str(raw_id).strip()] = record

        updated_mapping = []

        for entry in full_mapping:
            rid = str(entry["record_id"]).strip()
            # Only process if it's an ORPHAN or missing affinities
            assigned_domain = str(entry.get("assigned_domain", "")).strip().upper()
            if assigned_domain == "ORPHAN" or "domain_affinities" not in entry:
            
                if rid not in raw_data:
                    print(f"WARNING: Raw data for {rid} not found. Skipping.")
                    updated_mapping.append(entry)
                    continue
                    
                # Extract robust text
                raw_context = raw_data[rid].get("context", "")
                context_str = " ".join(raw_context) if isinstance(raw_context, list) else str(raw_context)
                text = raw_data[rid].get("question", "") + " " + context_str
                
                print(f" [D3] Synthesizing and Scoring Domains for: {rid}")
                
                # 1. Discover Domains via LLM
                discovered_list = self.discover_poly_ontological(text, rid)
                if not discovered_list:
                    updated_mapping.append(entry)
                    continue
                
                # 2. Calculate Affinity Weights (Wa)
                r_vec = self.get_embedding(text)
                affinities = {}
                raw_sims = []
                
                for d in discovered_list:
                    d_name = d['name'].title()
                    
                    # Recursive Cache Update
                    if d_name not in self.cache:
                        d['origin_record'] = rid
                        d['origin_z_score'] = entry.get("z_score", 0.0)
                        self.cache[d_name] = d
                    
                    # Math: Cosine Similarity for Wa
                    d_vec = self.get_embedding(f"{d_name} {d['description']}")
                    sim = np.dot(r_vec, d_vec) / (np.linalg.norm(r_vec) * np.linalg.norm(d_vec))
                    
                    # Ensure no negative affinities
                    sim = max(0.0, float(sim))
                    raw_sims.append((d_name, sim))

                # Normalize Wa (Weight of Affinity)
                total_sim = sum(s[1] for s in raw_sims)
                if total_sim > 0:
                    for name, sim in raw_sims:
                        affinities[name] = {"wa": round(float(sim/total_sim), 4)}
                else:
                    for name, _ in raw_sims:
                        affinities[name] = {"wa": round(1.0 / len(raw_sims), 4)}

                # Update Registry (The Golden Thread Persistence)
                entry["domain_affinities"] = affinities
                entry["assigned_domains"] = list(affinities.keys())
                entry["mapping_source"] = "D3_V22_SALIENT_WEIGHTED"
                entry.pop("assigned_domain", None) # Clean up old orphan tag

            updated_mapping.append(entry)

        # 2. Final Atomic Persistence
        with open(self.mapping_path, 'w', encoding='utf-8') as f:
            for entry in updated_mapping: 
                f.write(json.dumps(entry) + "\n")
            
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=4)

        print(f"--- D3 Complete. Registry and Discovery Library Updated. ---")

if __name__ == "__main__":
    D3MultiDiscoveryV22().run_discovery_pipeline()