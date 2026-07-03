import json
import os
import uuid
import networkx as nx
from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer, util

# --- PhD Rigor Configuration ---
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
        print("D2 EXECUTION STATISTICS: REGISTRY INITIATED")
        print("="*50)
        print(f"Total Input Records:     {self.input_records}")
        print(f"Total Output Records:    {self.output_records}")
        print(f"Graph Search Ops:        {self.graph_searches} (Tier 1)")
        print(f"Embedding Operations:    {self.embedding_ops} (Tier 2)")
        print("-" * 30)
        print(f"Tier 1 Matches (GML):    {self.matches_tier1}")
        print(f"Tier 2 Matches (Cache):  {self.matches_tier2}")
        print(f"ORPHAN Flagged:          {self.orphans}")
        print("-" * 30)
        print(f"D1 ground truth Match:   {self.matches_d1}")
        print(f"Architectural Shift Rate: {shift_rate:.2f}%")
        print(f"D1 vs D2 Alignment Rate: {alignment_rate:.2f}%")
        print("="*50 + "\n")

class D2Validator:
    def __init__(self, gml_path: str, cache_path: str, global_mapping_path: str):
        self.gml_graph = self._load_gml(gml_path)
        self.d3_cache = self._load_json(cache_path)
        self.global_map = self._load_json(global_mapping_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.stats = StatsTracker()

    def _load_gml(self, path: str) -> nx.Graph:
        return nx.read_gml(path) if os.path.exists(path) else nx.Graph()

    def _load_json(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def validate_record(self, record: dict) -> Tuple[dict, dict]:
        """
        Validates record and returns:
        1. result: The internal D2 audit log.
        2. mapping: The dynamic entry for the D2_D3_Record_Domain_Mapping.
        """
        self.stats.input_records += 1
        content = f"{record.get('context', '')} {record.get('question', '')}".lower()
        record_id = record.get('id', str(uuid.uuid4()))
        dataset_name = record.get('dataset', 'hotpotqa')
        d1_baseline = self.global_map.get(dataset_name, "general knowledge")

        mapping_source = "BIZBOK"
        
        # Tier 1: Structural Match (BIZBOK GML)
        self.stats.graph_searches += 1
        matched_domain = self._tier1_structural_match(content)
        reasoning = "Matched via R3.5 GML" if matched_domain else ""
        if matched_domain: 
            self.stats.matches_tier1 += 1

        # Tier 2: Semantic Match (D3 Recommendations Cache)
        if not matched_domain:
            self.stats.embedding_ops += 1
            matched_domain, score = self._tier2_semantic_search(content)
            if matched_domain:
                self.stats.matches_tier2 += 1
                mapping_source = "CACHE"
                reasoning = f"Matched via D3 Cache (Sim: {score:.2f})"

        # Tier 3: Discovery Trigger (ORPHAN)
        if not matched_domain:
            self.stats.orphans += 1
            matched_domain = "ORPHAN"
            mapping_source = "ORPHAN"
            reasoning = "No anchor found; triggered D3 Discovery"

        # Track D1 Comparison for Metrics
        if matched_domain.lower() == d1_baseline.lower():
            self.stats.matches_d1 += 1

        self.stats.output_records += 1
        
        # Audit Log Entry
        result = {
            "record_id": record_id,
            "d1_ground_truth": d1_baseline,
            "d2_validated_domain": matched_domain,
            "reasoning_path": reasoning,
            "architectural_shift": 1.0 if d1_baseline != matched_domain else 0.0
        }

        # Dynamic Mapping Entry (The Golden Thread)
        mapping = {
            "record_id": record_id,
            "assigned_domain": matched_domain,
            "mapping_source": mapping_source
        }

        return result, mapping

    def _tier1_structural_match(self, content: str) -> Optional[str]:
        for node, data in self.gml_graph.nodes(data=True):
            label = data.get('label', node).lower()
            if label in content:
                # Return the industry domain if specified, else the node label
                return data.get('industry_domain', label)
        return None

    def _tier2_semantic_search(self, content: str) -> Tuple[Optional[str], float]:
        if not self.d3_cache: return None, 0.0
        learned_domains = list(self.d3_cache.keys())
        content_emb = self.model.encode(content, convert_to_tensor=True)
        domain_embs = self.model.encode(learned_domains, convert_to_tensor=True)
        cosine_scores = util.cos_sim(content_emb, domain_embs)[0]
        max_score, idx = cosine_scores.max().item(), cosine_scores.argmax().item()
        return (learned_domains[idx], max_score) if max_score >= 0.85 else (None, 0.0)

if __name__ == "__main__":
    # File Paths
    GML_PATH = os.path.join(PROJECT_ROOT, "output", "R_Reference_Ontology_Governance.gml")
    CACHE_PATH = os.path.join(PROJECT_ROOT, "output", "D3_Domain_Recommendations.json")
    D1_MAP_PATH = os.path.join(PROJECT_ROOT, "output", "D1_Global_Mapping.json")
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "hotpotqa_test.jsonl")
    
    # OUTPUTS
    AUDIT_FILE = os.path.join(PROJECT_ROOT, "output", "D2_Document_Domain.jsonl")
    MAPPING_FILE = os.path.join(PROJECT_ROOT, "output", "D2_D3_Record_Domain_Mapping.jsonl")

    validator = D2Validator(GML_PATH, CACHE_PATH, D1_MAP_PATH)
    
    print(f"--- D2: Initializing Governance Validation & Mapping ---")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(AUDIT_FILE, 'w', encoding='utf-8') as audit_out, \
         open(MAPPING_FILE, 'w', encoding='utf-8') as mapping_out:
        
        for line in infile:
            if line.strip():
                record_data = json.loads(line)
                audit_result, mapping_entry = validator.validate_record(record_data)
                
                # Write to the Audit Log
                audit_out.write(json.dumps(audit_result) + "\n")
                
                # Write to the Dynamic Mapping Registry
                mapping_out.write(json.dumps(mapping_entry) + "\n")
    
    validator.stats.print_summary()