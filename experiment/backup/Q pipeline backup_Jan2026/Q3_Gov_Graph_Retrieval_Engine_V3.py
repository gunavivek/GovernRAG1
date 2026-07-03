import json
import os
import sys
import pandas as pd
import networkx as nx
from typing import Dict, Any, List, Set

# --- Configuration & Paths ---
M5_GRAPH_PATH = os.path.join("output", "M5_Embedded_graph.graphml")
M1_CHUNKS_PATH = os.path.join("output", "M1_Governed_Chunks.csv")
OUTPUT_FILE = os.path.join("output", "Q3_retrieved_evidence.jsonl")

class GovGraphRetrievalEngineV3:
    def __init__(self):
        print(f"[INIT] Loading M5 Knowledge Graph: {M5_GRAPH_PATH}")
        if not os.path.exists(M5_GRAPH_PATH):
            raise FileNotFoundError(f"M5 GraphML file not found at {M5_GRAPH_PATH}")
        
        self.G = nx.read_graphml(M5_GRAPH_PATH)
        print(f"[INIT] Graph Loaded: {len(self.G.nodes)} nodes, {len(self.G.edges)} edges.")

        if os.path.exists(M1_CHUNKS_PATH):
            self.m1_df = pd.read_csv(M1_CHUNKS_PATH, dtype={'record_id': str, 'chunk_id': str})
        else:
            self.m1_df = None

    def _get_semantic_text_with_ids(self, record_id: str) -> tuple:
        if self.m1_df is not None:
            target = str(record_id).strip()
            matches = self.m1_df[self.m1_df['record_id'] == target]
            if not matches.empty:
                chunk_ids = matches['chunk_id'].tolist()
                labeled_segments = [f"[{row['chunk_id']}]: {row['chunk_text']}" for _, row in matches.iterrows()]
                return " ".join(labeled_segments), chunk_ids
        return f"CRITICAL: ID {record_id} missing in M1.", []

    def _get_isolated_subgraph(self, record_id: str) -> tuple:
        relevant_edges = []
        for u, v, k, data in self.G.edges(keys=True, data=True):
            edge_rid = data.get("record_id") or data.get("source_chunk_id")
            if str(edge_rid) == str(record_id):
                relevant_edges.append((u, v, k))
        if not relevant_edges:
            return nx.MultiDiGraph(), "No graph data found.", []
        source_text, chunk_ids = self._get_semantic_text_with_ids(record_id)
        return self.G.edge_subgraph(relevant_edges).copy(), source_text, chunk_ids

    def _resolve_anchors(self, local_graph: nx.Graph, target_nodes: List[str]) -> List[str]:
        anchors = []
        noise_words = {"which", "american", "were", "both", "are", "what", "is", "the", "did"}
        clean_targets = [str(t).lower() for t in target_nodes if str(t).lower() not in noise_words]
        for node_id in local_graph.nodes:
            for entity in clean_targets:
                if entity in node_id.lower() or node_id.lower() in entity:
                    anchors.append(node_id)
        return list(set(anchors))

    def _perform_governed_walk(self, local_graph: nx.Graph, anchors: List[str], 
                               predicates: List[str], k_hops: int) -> Set[tuple]:
        discovered_triples = set()
        current_layer = set(anchors)
        visited_nodes = set(anchors)
        for hop in range(k_hops):
            next_layer = set()
            for u in current_layer:
                edges = local_graph.out_edges(u, data=True) if local_graph.is_directed() else local_graph.edges(u, data=True)
                for _, v, data in edges:
                    p_label = data.get('predicate', 'related_to')
                    if not predicates or any(p in p_label for p in predicates):
                        discovered_triples.add((u, p_label, v))
                        if v not in visited_nodes: next_layer.add(v)
            current_layer = next_layer
            visited_nodes.update(next_layer)
            if not current_layer: break
        return discovered_triples

    def process(self, filter_id: str = None, signature_path: str = "output/Q2_signatures.jsonl"):
        """
        PhD Logic: signature_path allows the Orchestrator to switch between 
        Primary (Q2) and Recursive (Q2.6) signatures.
        """
        mode_label = "RECURSIVE PASS" if "2.6" in signature_path else "PRIMARY PASS"
        print(f"\n[STEP 3] Q3: Graph Engine ({mode_label}) using {signature_path}")
        
        if not os.path.exists(signature_path):
            print(f"[ERROR] Signature file not found: {signature_path}")
            return

        with open(signature_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                record = json.loads(line)
                record_id = record.get("id") or record.get("record_id")
                
                if filter_id and str(record_id) != str(filter_id):
                    continue
                
                # 1. Traversal logic
                local_g, semantic_chunk, chunk_ids = self._get_isolated_subgraph(record_id)
                anchors = self._resolve_anchors(local_g, record["q_signature"]["target_nodes"])
                triples = self._perform_governed_walk(local_g, anchors, 
                                                    record["q_signature"]["required_predicates"], 
                                                    record["traversal_parameters"]["k_hops"])
                
                new_triplets = [{"s": t[0], "p": t[1], "o": t[2]} for t in triples]

                # 2. STATEFUL MERGE: Don't overwrite evidence if this is Pass 2
                self._update_output_file(record_id, chunk_ids, semantic_chunk, new_triplets, record)

    def _update_output_file(self, record_id, chunk_ids, semantic_chunk, new_triplets, record):
        """Append or Update existing evidence to prevent data loss across hops."""
        existing_data = {}
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    existing_data[data["record_id"]] = data

        if record_id in existing_data:
            # Merge logic for Recursive Pass
            existing_data[record_id]["symbolic_triplets"].extend(new_triplets)
            # Remove duplicates
            existing_data[record_id]["symbolic_triplets"] = [dict(t) for t in {tuple(d.items()) for d in existing_data[record_id]["symbolic_triplets"]}]
            existing_data[record_id]["traversal_stats"]["recursive_success"] = len(new_triplets) > 0
        else:
            # Fresh entry for Primary Pass
            existing_data[record_id] = {
                "record_id": record_id,
                "contributing_chunks": chunk_ids,
                "question": record["question"],
                "semantic_chunk": semantic_chunk,
                "symbolic_triplets": new_triplets,
                "traversal_stats": {"hops": record["traversal_parameters"]["k_hops"], "count": len(new_triplets)}
            }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            for rid in existing_data:
                outfile.write(json.dumps(existing_data[rid], ensure_ascii=False) + '\n')
        
        print(f"[SUCCESS] {record_id[:8]} | Total Triples: {len(existing_data[record_id]['symbolic_triplets'])}")

if __name__ == "__main__":
    engine = GovGraphRetrievalEngineV3()
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    engine.process(filter_id=target_id)