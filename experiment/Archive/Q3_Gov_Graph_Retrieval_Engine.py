import json
import os
import networkx as nx
from typing import Dict, Any, List, Set

# --- Project Paths ---
Q2_SIGNATURE_PATH = "output/Q2_signatures.jsonl"
M5_GRAPH_PATH = "output/M5_Embedded_graph.graphml"
OUTPUT_FILE = "output/Q3_retrieved_evidence.jsonl"

class GovGraphRetrievalEngine:
    def __init__(self):
        print(f"[INIT] Loading M5 Knowledge Graph: {M5_GRAPH_PATH}")
        if not os.path.exists(M5_GRAPH_PATH):
            raise FileNotFoundError(f"M5 GraphML file not found at {M5_GRAPH_PATH}")
        
        self.G = nx.read_graphml(M5_GRAPH_PATH)
        print(f"[INIT] Graph Loaded: {len(self.G.nodes)} nodes, {len(self.G.edges)} edges.")
        self._debug_graph_attributes()

    def _debug_graph_attributes(self):
        """Prints sample node attributes to verify the isolation key."""
        if not self.G.nodes:
            print("[DEBUG] Graph is empty!")
            return
        
        sample_node = list(self.G.nodes(data=True))[0]
        print(f"\n[DEBUG] Sample Node ID: {sample_node[0]}")
        print(f"[DEBUG] Available Attributes: {list(sample_node[1].keys())}")
        if 'source_record_id' in sample_node[1]:
            print(f"[DEBUG] source_record_id Type: {type(sample_node[1]['source_record_id'])}")
        else:
            print("[CRITICAL] 'source_record_id' NOT FOUND in node attributes. Update Gate 1 logic.")

    def _get_isolated_subgraph(self, record_id: str) -> nx.Graph:
        """Gate 1: Namespace Isolation."""
        # Convert record_id if necessary (e.g., to int) to match GraphML type
        local_nodes = [n for n, d in self.G.nodes(data=True) 
                       if str(d.get("source_record_id")) == str(record_id)]
        
        print(f"[DEBUG] Found {len(local_nodes)} nodes for ID: {record_id}")
        return self.G.subgraph(local_nodes).copy()

    def _resolve_anchors(self, local_graph: nx.Graph, target_nodes: List[str]) -> List[str]:
        """Gate 2: Anchor Resolution."""
        anchors = []
        for node_id in local_graph.nodes:
            for entity in target_nodes:
                if entity.lower() in node_id.lower() or node_id.lower() in entity.lower():
                    anchors.append(node_id)
        
        print(f"[DEBUG] Signature Entities: {target_nodes} -> Matched Anchors: {list(set(anchors))}")
        return list(set(anchors))

    def _perform_governed_walk(self, local_graph: nx.Graph, anchors: List[str], 
                             predicates: List[str], k_hops: int) -> Set[tuple]:
        """Gate 3: Predicate-Bound Traversal."""
        discovered_triples = set()
        current_layer = set(anchors)
        visited_nodes = set(anchors)

        print(f"[DEBUG] Starting {k_hops}-hop walk with predicates: {predicates}")

        for hop in range(k_hops):
            next_layer = set()
            for u in current_layer:
                # Use out_edges for directed graphs, edges for undirected
                edges_to_check = local_graph.out_edges(u, data=True) if local_graph.is_directed() else local_graph.edges(u, data=True)
                
                for _, v, data in edges_to_check:
                    p_label = data.get('predicate', 'related_to')
                    
                    # Logic: If predicates is empty or "general_traversal", we allow all
                    is_allowed = not predicates or "general_traversal" in predicates or p_label in predicates
                    
                    if is_allowed:
                        discovered_triples.add((u, p_label, v))
                        if v not in visited_nodes:
                            next_layer.add(v)
            
            print(f"  - Hop {hop+1}: Found {len(next_layer)} new nodes.")
            current_layer = next_layer
            visited_nodes.update(next_layer)
            if not current_layer: break
            
        return discovered_triples

    def process(self):
        print("\n--- Q3: Governed Graph Retrieval Engine (Debug Mode) ---")
        
        with open(Q2_SIGNATURE_PATH, 'r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                record = json.loads(line)
                record_id = record["id"]
                sig = record["q_signature"]
                params = record["traversal_parameters"]
                
                print(f"\n[RECORD] {record_id[:8]} | Q: {record['question'][:50]}...")
                
                # 1. Isolation
                local_g = self._get_isolated_subgraph(record_id)
                if not local_g.nodes:
                    print(f"  [SKIP] No nodes in namespace for {record_id}")
                    continue
                
                # 2. Anchors
                anchors = self._resolve_anchors(local_g, sig["target_nodes"])
                if not anchors:
                    print(f"  [SKIP] No anchors found in local subgraph.")
                    continue
                
                # 3. Walk
                triples = self._perform_governed_walk(
                    local_g, 
                    anchors, 
                    sig["required_predicates"], 
                    params["k_hops"]
                )
                
                evidence = [{"s": t[0], "p": t[1], "o": t[2]} for t in triples]
                
                output_packet = {
                    "id": record_id,
                    "question": record["question"],
                    "ideal_chunk": {
                        "anchors_found": anchors,
                        "evidence_triples": evidence,
                        "traversal_stats": {"hops": params["k_hops"], "triple_count": len(evidence)}
                    }
                }
                
                outfile.write(json.dumps(output_packet, ensure_ascii=False) + '\n')
                print(f"  [SUCCESS] Extracted {len(evidence)} triples.")

if __name__ == "__main__":
    engine = GovGraphRetrievalEngine()
    engine.process()