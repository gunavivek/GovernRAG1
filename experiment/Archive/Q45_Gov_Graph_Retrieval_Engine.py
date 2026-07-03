import json
import os
import networkx as nx
import numpy as np

GRAPH_PATH = "output/M5_Embedded_Graph.graphml"
INPUT_FILE = "output/Q3_signatures.jsonl"
OUTPUT_FILE = "output/Q45_retrieval_results.jsonl"

class GovernedRetrieverV3:
    def __init__(self, graph_path):
        print(f"--- [DEBUG] Initializing Q45_v3 (Resilient Mode) ---")
        self.G = nx.read_graphml(graph_path)

    def _extract_any_content(self, data):
        """Finds any string attribute that contains substantial text."""
        # Try common keys first
        for key in ['content', 'label', 'text', 'summary', 'description']:
            val = data.get(key)
            if val and len(str(val)) > 10:
                return str(val)
        # Fallback: check everything
        for val in data.values():
            if isinstance(val, str) and len(val) > 15:
                return val
        return str(data.get('label', ''))

    def _get_entry_point(self, concept, record_id):
        """Scans the entire graph for the Record ID as a substring in ANY field."""
        # 1. Look for the BIZBOK Concept first
        for n, d in self.G.nodes(data=True):
            if d.get('label', '').lower() == concept.lower():
                return n
        
        # 2. Deep Scan for Record ID substring (The Golden Thread Fallback)
        for n, d in self.G.nodes(data=True):
            for attr_val in d.values():
                if record_id in str(attr_val):
                    return n
        return None

    def process(self):
        with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
            
            for line in f_in:
                rec = json.loads(line)
                qid = rec['id']
                concept = rec['Q_layer'].get('concept', '')
                
                print(f"[DEBUG] Processing {qid} | Anchor: {concept}")
                
                anchor = self._get_entry_point(concept, qid)
                
                evidence = []
                if anchor:
                    # Collect from anchor and neighbors
                    nodes_to_check = [anchor] + list(self.G.neighbors(anchor))
                    for node_id in nodes_to_check:
                        data = self.G.nodes[node_id]
                        text = self._extract_any_content(data)
                        if text:
                            evidence.append({
                                "node": node_id,
                                "content": text,
                                "wa": 1.0 # Default weight for resilient mode
                            })
                
                rec["retrieved_evidence"] = evidence
                rec["governance_log"] = "Resilient Traversal" if anchor else "Anchor Not Found"
                
                f_out.write(json.dumps(rec, ensure_ascii=False) + '\n')
                print(f"  -> Found {len(evidence)} chunks.\n")

if __name__ == "__main__":
    GovernedRetrieverV3(GRAPH_PATH).process()