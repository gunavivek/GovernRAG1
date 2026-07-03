import json
import os
import uuid
import networkx as nx
import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from google import genai
from dotenv import load_dotenv

# --- 0. Setup and Configuration ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini high-performance model configuration [cite: 318]
EMBEDDING_MODEL = 'gemini-embedding-001' 
EMBEDDING_DIM = 3072 
RATE_LIMIT_DELAY = 0  # Optimized for text-embedding-001 throughput
#RATE_LIMIT_DELAY = 1  # Optimized for text-embedding-001 throughput

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
        print("D2_V2 EXECUTION STATISTICS: STATISTICAL ANCHOR INITIATED")
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
    def __init__(self, gml_path: str, cache_path: str, global_mapping_path: str):
        # Load authoritative BIZBOK R3.5 GML [cite: 24, 46]
        self.gml_graph = self._load_gml(gml_path)
        self.d3_cache = self._load_json(cache_path)
        self.global_map = self._load_json(global_mapping_path)
        self.stats = StatsTracker()
        
        # Statistical Baselines
        self.mu = 0.0
        self.sigma = 0.05  # Fallback variance
        self.domain_centroids = {}
        
        self._initialize_statistical_baseline()

    def _load_gml(self, path: str) -> nx.Graph:
        return nx.read_gml(path) if os.path.exists(path) else nx.Graph()

    def _load_json(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_embedding(self, text: str) -> np.ndarray:
        """Standardized 3072-dim embedding via Gemini text-embedding-001."""
        time.sleep(RATE_LIMIT_DELAY) # Respect optimized throughput
        result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
        return np.array(result.embeddings[0].values)

    def _initialize_statistical_baseline(self):
        """Calculates global Mu and Sigma from BIZBOK GML to ground Z-score logic."""
        print("--- D2_V2: Initializing Statistical Baseline from R-GML ---")
        all_vectors = []
        temp_domains = {}

        # Process nodes based on Industry Domain attributes [cite: 42]
        for node, data in self.gml_graph.nodes(data=True):
            domain = data.get('industry_domain', 'Common')
            label = data.get('label', node)
            vec = self.get_embedding(label)
            
            if domain not in temp_domains: temp_domains[domain] = []
            temp_domains[domain].append(vec)
            all_vectors.append(vec)

        # Global statistical anchors
        global_centroid = np.mean(all_vectors, axis=0)
        distances = [np.linalg.norm(v - global_centroid) for v in all_vectors]
        self.mu = np.mean(distances)
        self.sigma = np.std(distances) if len(distances) > 1 else 0.05

        # Domain-specific centroids
        for domain, vectors in temp_domains.items():
            self.domain_centroids[domain] = np.mean(vectors, axis=0)
        
        print(f" [Initial] Baseline Sigma established: {self.sigma:.4f}")

    def validate_record(self, record: dict) -> Tuple[dict, dict]:
        self.stats.input_records += 1
        content = f"{record.get('context', '')} {record.get('question', '')}"
        record_id = record.get('id', str(uuid.uuid4()))
        dataset_name = record.get('dataset', 'hotpotqa')
        d1_baseline = self.global_map.get(dataset_name, "general knowledge")

        mapping_source = "BIZBOK_IDENTITY"
        
        # Tier 1: Structural Match (BIZBOK GML Exact Keyword) [cite: 372]
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
                # Tier 3: Statistical Orphan Trigger [cite: 374]
                self.stats.orphans += 1
                matched_domain = "ORPHAN"
                z_score = min_z
                mapping_source = "ORPHAN"
                reasoning = f"Tier 3: Semantic Outlier (Z={z_score:.2f}) -> D3 Discovery"

        # Track D1 Comparison for Metrics [cite: 375]
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

    def _tier1_structural_match(self, content: str) -> Optional[str]:
        """Priority keyword match against BIZBOK node labels[cite: 378]."""
        for node, data in self.gml_graph.nodes(data=True):
            label = data.get('label', node).lower()
            if label in content:
                return data.get('industry_domain', label)
        return None

if __name__ == "__main__":
    # Ingress Artifacts
    GML_PATH = os.path.join(PROJECT_ROOT, "output", "R_Reference_Ontology_Governance.gml")
    CACHE_PATH = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Recommendations.json")
    D1_MAP_PATH = os.path.join(PROJECT_ROOT, "output", "D1_Global_Mapping.json")
    #INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl")
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "RGB_Single_Record.jsonl")
    
    # Egress Artifacts [cite: 382, 385]
    AUDIT_FILE = os.path.join(PROJECT_ROOT, "output", "D2_Document_Domain.jsonl")
    MAPPING_FILE = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")

    anchor = D2StatisticalDomainOntologicalAnchor(GML_PATH, CACHE_PATH, D1_MAP_PATH)
    
    print(f"--- D2_V2: Statistical Domain Ontological Anchor Execution ---")
    
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