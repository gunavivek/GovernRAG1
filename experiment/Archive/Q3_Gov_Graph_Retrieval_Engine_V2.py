import json
import os
import sys  # Added for CLI arguments
import networkx as nx
from typing import Dict, Any, List, Set

# --- Configuration & Paths ---
Q2_SIGNATURE_PATH = "output/Q2_signatures.jsonl"
M5_GRAPH_PATH = "output/M5_Embedded_graph.graphml"
OUTPUT_FILE = "output/Q3_retrieved_evidence.jsonl"

class GovGraphRetrievalEngineV3:
    def __init__(self):
        print(f"[INIT] Loading M5 Knowledge Graph: {M5_GRAPH_PATH}")
        if not os.path.exists(M5_GRAPH_PATH):
            raise FileNotFoundError(f"M5 GraphML file not found at {M5_GRAPH_PATH}")
        
        self.G = nx.read_graphml(M5_GRAPH_PATH)
        print(f"[INIT] Graph Loaded: {len(self.G.nodes)} nodes, {len(self.G.edges)} edges.")

    def _get_isolated_subgraph(self, record_id: str) -> tuple:
        """GATE 1: Namespace Isolation. Returns (subgraph, source_text)."""
        relevant_edges = []
        source_text = ""

        for u, v, k, data in self.G.edges(keys=True, data=True):
            edge_rid = data.get("record_id") or data.get("source_chunk_id")
            if str(edge_rid) == str(record_id):
                relevant_edges.append((u, v, k))
                if not source_text:
                    source_text = data.get("source_text", "Source text missing in graph metadata.")

        if not relevant_edges:
            return nx.MultiDiGraph(), ""

        return self.G.edge_subgraph(relevant_edges).copy(), source_text

    def _resolve_anchors(self, local_graph: nx.Graph, target_nodes: List[str]) -> List[str]:
        """GATE 2: Anchor Resolution with Noise Filtering."""
        anchors = []
        noise_words = {"which", "american", "were", "both", "are", "what", "is", "the", "did"}
        clean_targets = [t.lower() for t in target_nodes if t.lower() not in noise_words]

        for node_id in local_graph.nodes:
            for entity in clean_targets:
                if entity in node_id.lower() or node_id.lower() in entity:
                    anchors.append(node_id)
        
        return list(set(anchors))

    def _perform_governed_walk(self, local_graph: nx.Graph, anchors: List[str], 
                             predicates: List[str], k_hops: int) -> Set[tuple]:
        """GATE 3: Predicate-Bound Traversal (The Symbolic Skeleton)."""
        discovered_triples = set()
        current_layer = set(anchors)
        visited_nodes = set(anchors)

        for hop in range(k_hops):
            next_layer = set()
            for u in current_layer:
                edges_to_check = local_graph.out_edges(u, data=True) if local_graph.is_directed() else local_graph.edges(u, data=True)
                for _, v, data in edges_to_check:
                    p_label = data.get('predicate', 'related_to')
                    if not predicates or "general_traversal" in predicates or p_label in predicates:
                        discovered_triples.add((u, p_label, v))
                        if v not in visited_nodes:
                            next_layer.add(v)
            current_layer = next_layer
            visited_nodes.update(next_layer)
            if not current_layer: break
            
        return discovered_triples

    def process(self, filter_id: str = None):
        """
        Main Execution Loop. 
        If filter_id is provided, only that specific record is processed.
        """
        mode_label = f"SINGLE RECORD [{filter_id}]" if filter_id else "BATCH MODE"
        print(f"\n--- Q3 V3: Neuro-Symbolic Retrieval ({mode_label}) ---")
        
        with open(Q2_SIGNATURE_PATH, 'r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            
            count = 0
            for line in infile:
                record = json.loads(line)
                record_id = record["id"]
                
                # Logic Gate: Skip if filter_id is active and doesn't match
                if filter_id and str(record_id) != str(filter_id):
                    continue
                
                # 1. Isolate Graph and Retrieve Semantic Chunk (Text)
                local_g, semantic_chunk = self._get_isolated_subgraph(record_id)
                
                # 2. Resolve Anchors and Perform Symbolic Walk (Triplets)
                anchors = self._resolve_anchors(local_g, record["q_signature"]["target_nodes"])
                triples = self._perform_governed_walk(local_g, anchors, 
                                                    record["q_signature"]["required_predicates"], 
                                                    record["traversal_parameters"]["k_hops"])
                
                # 3. Package Dual-Grounded Evidence
                output_packet = {
                    "id": record_id,
                    "question": record["question"],
                    "semantic_chunk": semantic_chunk,
                    "symbolic_triplets": [{"s": t[0], "p": t[1], "o": t[2]} for t in triples],
                    "traversal_stats": {"hops": record["traversal_parameters"]["k_hops"], "count": len(triples)}
                }
                
                outfile.write(json.dumps(output_packet, ensure_ascii=False) + '\n')
                count += 1
                print(f"[RECORD FOUND] {record_id[:8]} | Triples: {len(triples)} | Text Length: {len(semantic_chunk)}")

        if count == 0 and filter_id:
            print(f"[⚠️ WARNING] Record ID {filter_id} was not found in {Q2_SIGNATURE_PATH}")
        else:
            print(f"\n[COMPLETE] Evidence saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    engine = GovGraphRetrievalEngineV3()
    
    # Check if a Record ID was passed as an argument
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    engine.process(filter_id=target_id)