import json
import os
import numpy as np
from google import genai
from dotenv import load_dotenv
from typing import Dict, List, Tuple

# --- 0. Setup and Configuration ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Parity with D2/D3 Pipelines 
EMBEDDING_MODEL = 'gemini-embedding-001'
EMBEDDING_DIM = 768

# Project Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D4_PATH = os.path.join(PROJECT_ROOT, "output", "D4_Registry_Discovered.json")
M2_DISCOVERY_PATH = os.path.join(PROJECT_ROOT, "output", "M2_discovered_concepts.json")
D45_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "D45_Dispatcher_Report.json")

class D45StatisticalDispatcher:
    def __init__(self):
        self.d4_baseline = self._load_json(D4_PATH)
        self.m2_discoveries = self._load_json(M2_DISCOVERY_PATH)
        self.domain_stats = {}

    def _load_json(self, path: str):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_embedding(self, text: str) -> np.ndarray:
        """Generates native 3072-dim vector using Gemini gemini-embedding-001."""
        result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
        return np.array(result.embeddings[0].values)

    def calculate_domain_baseline(self):
        """Calculates Mu and Sigma for existing D4 predicates."""
        print("--- D45: Establishing Semantic Baselines from D4 ---")
        for domain, data in self.d4_baseline.items():
            predicates = data.get("governance_packet", {}).get("relational_predicates", [])
            if not predicates: continue

            # Fixed: Call get_embedding as a class method
            vectors = [self.get_embedding(p) for p in predicates]
            centroid = np.mean(vectors, axis=0)
            
            # Calculate distances of members from centroid to find Sigma
            distances = [np.linalg.norm(v - centroid) for v in vectors]
            mu = np.mean(distances)
            sigma = np.std(distances) if len(distances) > 1 else 0.05 # Fallback for low density
            
            self.domain_stats[domain] = {
                "centroid": centroid,
                "mu": mu,
                "sigma": sigma
            }
            print(f" [Baseline] {domain}: Mu={mu:.4f}, Sigma={sigma:.4f}")

    def triage_discoveries(self):
        """Performs Z-Score triage on M2 discoveries."""
        report = []
        print("\n--- D45: Performing Statistical Triage on M2 Discovery ---")

        for discovery in self.m2_discoveries:
            suggested_verb = discovery.get("suggested_predicate")
            context = discovery.get("context", "")
            record_id = discovery.get("record_id")
            
            # Use LLM to identify the likely parent domain for triage
            # For PhD rigor, we triage against the most similar domain centroid
            verb_vec = self.get_embedding(suggested_verb)
            
            best_domain = None
            min_z_score = float('inf')

            for domain, stats in self.domain_stats.items():
                distance = np.linalg.norm(verb_vec - stats["centroid"])
                z_score = (distance - stats["mu"]) / stats["sigma"] if stats["sigma"] > 0 else distance
                
                if z_score < min_z_score:
                    min_z_score = z_score
                    best_domain = domain

            # Dispatch Logic based on Z-Score [cite: 33, 35]
            action = "REJECT_NOISE"
            if min_z_score < 1.0:
                action = "GLOSSARY_PATCH"  # Enrichment (Nouns)
            elif 1.0 <= min_z_score < 2.5:
                action = "PREDICATE_PROMOTION" # Expansion (Verbs)
            elif 2.5 <= min_z_score < 3.5:
                action = "AWAITING_HITL_RATIFICATION" # Innovation
            
            report.append({
                "record_id": record_id,
                "suggested_predicate": suggested_verb,
                "assigned_domain": best_domain,
                "z_score": round(float(min_z_score), 4),
                "action": action,
                "context_sample": context[:200]
            })
            print(f" [Triage] {suggested_verb} -> {best_domain} (Z={min_z_score:.2f}) -> {action}")

        self._save_report(report)

    def _save_report(self, report):
        with open(D45_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4)
        print(f"\n--- D45 Complete: Report saved to {D45_OUTPUT_PATH} ---")

if __name__ == "__main__":
    dispatcher = D45StatisticalDispatcher()
    dispatcher.calculate_domain_baseline()
    dispatcher.triage_discoveries()