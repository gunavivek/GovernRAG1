import json
import os
import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- 0. Setup and Configuration ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini high-performance model configuration
EMBEDDING_MODEL = 'models/gemini-embedding-001' 
EMBEDDING_DIM = 768  # Standardized to match R4
RATE_LIMIT_DELAY = 0  # Optimized for text-embedding-001 throughput

# Project Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

class StatsTracker:
    def __init__(self):
        self.input_records = 0
        self.output_records = 0
        self.graph_searches = 0
        self.embedding_ops = 0
        self.orphans = 0
        self.matches_tier1 = 0
        self.matches_tier2 = 0
        self.matches_d1 = 0

    def print_summary(self):
        shift_rate = (self.orphans / self.input_records * 100) if self.input_records > 0 else 0
        alignment_rate = (self.matches_d1 / self.input_records * 100) if self.input_records > 0 else 0
        
        print("\n" + "="*50)
        print("D2_V3 EXECUTION STATISTICS: STATISTICAL ANCHOR INITIATED")
        print("="*50)
        print(f"Total Input Records:     {self.input_records}")
        print(f"Total Output Records:    {self.output_records}")
        print(f"Graph Search Ops:        {self.graph_searches} (Tier 1)")
        print(f"Z-Score Operations:      {self.embedding_ops} (Tier 2)")
        print("-" * 30)
        print(f"Tier 1 Matches (GML):    {self.matches_tier1}")
        print(f"Tier 2 Matches (Z-Score): {self.matches_tier2}")
        print(f"ORPHAN (Z > 2.5):        {self.orphans}")
        print("-" * 30)
        print(f"D1 ground truth Match:   {self.matches_d1}")
        print(f"Architectural Shift Rate: {shift_rate:.2f}%")
        print(f"D1 vs D2 Alignment Rate: {alignment_rate:.2f}%")
        print("="*50 + "\n")

class D2StatisticalDomainOntologicalAnchor:
    def __init__(self, baseline_path: str, cache_path: str, global_mapping_path: str):
        # 1. Load Static Math instantly from R4 (Replaces the slow GML load)
        with open(baseline_path, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
            
        self.mu = baseline["mu"]
        self.sigma = baseline["sigma"]
        self.domain_centroids = {k: np.array(v) for k, v in baseline["domain_centroids"].items()}
        self.keyword_mapping = baseline["keyword_mapping"]
        
        # 2. Load other artifacts for architectural parity
        self.d3_cache = self._load_json(cache_path)
        self.global_map = self._load_json(global_mapping_path)
        self.stats = StatsTracker()
        
        print(f"--- D2_V3: Static Baseline Loaded (Mu: {self.mu:.4f}, Sigma: {self.sigma:.4f}) ---")

    def _load_json(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_embedding(self, text: str) -> np.ndarray:
        """Standardized embedding via Gemini text-embedding-001."""
        time.sleep(RATE_LIMIT_DELAY)
        result = client.models.embed_content(
            model=EMBEDDING_MODEL, 
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
        )
        return np.array(result.embeddings[0].values)

    def _tier1_structural_match(self, content: str) -> Optional[str]:
        """Priority keyword match against BIZBOK node labels loaded from Baseline."""
        for label, domain in self.keyword_mapping.items():
            if label in content:
                return domain
        return None

    def validate_record(self, record: dict) -> Tuple[dict, dict]:
        self.stats.input_records += 1
        content = f"{record.get('context', '')} {record.get('question', '')}"
        record_id = record.get('id')
        if record_id is None or str(record_id).strip() == "":
            raise ValueError("[D2] Missing required source id in input record")
        record_id = str(record_id).strip()
        dataset_name = str(record.get('dataset', 'UNKNOWN_DATASET')).strip()
        d1_baseline = self.global_map.get(dataset_name, "general knowledge")

        mapping_source = "BIZBOK_IDENTITY"
        
        # Tier 1: Structural Match
        self.stats.graph_searches += 1
        matched_domain = self._tier1_structural_match(content.lower())
        z_score = 0.0
        reasoning = "Tier 1: Identity Match via R3.5 GML" if matched_domain else ""
        
        if matched_domain: 
            self.stats.matches_tier1 += 1

        # Tier 2: Adaptive Semantic Reconciliation (Z-Score Triage)
        if not matched_domain:
            self.stats.embedding_ops += 1
            record_vec = self.get_embedding(content)
            
            best_domain = None
            min_z = float('inf')

            # Calculate distance to known Domain Centroids
            for domain, centroid in self.domain_centroids.items():
                distance = np.linalg.norm(record_vec - centroid)
                current_z = (distance - self.mu) / self.sigma
                
                if current_z < min_z:
                    min_z = current_z
                    best_domain = domain

            # Statistical Gate: Z < 2.5 (High Confidence Proximity)
            if min_z < 2.5:
                matched_domain = best_domain
                z_score = min_z
                mapping_source = "BIZBOK_STATISTICAL"
                reasoning = f"Tier 2: Statistical Anchor (Z={z_score:.2f})"
                self.stats.matches_tier2 += 1
            else:
                # Tier 3: Statistical Orphan Trigger
                self.stats.orphans += 1
                matched_domain = "ORPHAN"
                z_score = min_z
                mapping_source = "ORPHAN"
                reasoning = f"Tier 3: Semantic Outlier (Z={z_score:.2f}) -> D3 Discovery"

        # Track D1 Comparison for Metrics
        if matched_domain.lower() == d1_baseline.lower():
            self.stats.matches_d1 += 1

        self.stats.output_records += 1
        
        # Audit log for D9 Provenance
        result = {
            "record_id": record_id,
            "d1_ground_truth": d1_baseline,
            "d2_validated_domain": matched_domain,
            "z_score": round(float(z_score), 4),
            "reasoning_path": reasoning,
            "architectural_shift": 1.0 if d1_baseline != matched_domain else 0.0
        }

        # The Golden Thread Mapping Entry
        mapping = {
            "record_id": record_id,
            "assigned_domain": matched_domain,
            "mapping_source": mapping_source,
            "z_score": round(float(z_score), 4)
        }

        return result, mapping


if __name__ == "__main__":
    # Ingress Artifacts
    BASELINE_PATH = os.path.join(PROJECT_ROOT, "output", "R_Statistical_Baseline.json")
    CACHE_PATH = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Recommendations.json")
    D1_MAP_PATH = os.path.join(PROJECT_ROOT, "output", "D1_Global_Mapping.json")
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "RGB_Single_Record.jsonl")
    
    # Egress Artifacts
    AUDIT_FILE = os.path.join(PROJECT_ROOT, "output", "D2_Document_Domain.jsonl")
    MAPPING_FILE = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")

    if not os.path.exists(BASELINE_PATH):
        print("CRITICAL: Static Baseline not found. Please run R4 first.")
        exit()

    anchor = D2StatisticalDomainOntologicalAnchor(BASELINE_PATH, CACHE_PATH, D1_MAP_PATH)
    
    print(f"--- D2_V3: Statistical Domain Ontological Anchor Execution ---")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(AUDIT_FILE, 'w', encoding='utf-8') as audit_out, \
         open(MAPPING_FILE, 'w', encoding='utf-8') as mapping_out:
        
        for line in infile:
            if line.strip():
                record_data = json.loads(line)
                audit_result, mapping_entry = anchor.validate_record(record_data)
                audit_out.write(json.dumps(audit_result) + "\n")
                mapping_out.write(json.dumps(mapping_entry) + "\n")
    
    anchor.stats.print_summary()