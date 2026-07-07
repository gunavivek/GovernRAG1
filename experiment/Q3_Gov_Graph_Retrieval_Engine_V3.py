import json
import os
import sys
import pandas as pd
import networkx as nx
from typing import Dict, Any, List, Set

# --- Configuration & Paths ---
M5_GRAPH_PATH = os.path.join("output", "M5_Embedded_Graph.graphml")
M1_CHUNKS_PATH = os.path.join("output", "M1_Governed_Chunks.csv")
OUTPUT_FILE = os.path.join("output", "Q3_retrieved_evidence.jsonl")

class GovGraphRetrievalEngineV3:
    def __init__(self):
        print(f"[INIT] Loading M5 Knowledge Graph: {M5_GRAPH_PATH}")
        if not os.path.exists(M5_GRAPH_PATH):
            raise FileNotFoundError(f"M5 GraphML file not found at {M5_GRAPH_PATH}")
        
        self.G = nx.read_graphml(M5_GRAPH_PATH)
        print(f"[INIT] Graph Loaded: {len(self.G.nodes)} nodes, {len(self.G.edges)} edges.")

        # PhD Governance: Lexical Noise Filter (Categorized for Explainability)
        self.noise_words = {
            "what", "which", "who", "how", "where", "when", "why", "whose", "whom",
            "the", "a", "an", "this", "that", "these", "those", "it", "they", 
            "their", "them", "he", "she", "we", "you", "his", "her",
            "is", "are", "was", "were", "be", "been", "being", "do", "did", 
            "does", "can", "could", "will", "would", "shall", "should", "may", "might", "must",
            "of", "at", "by", "for", "with", "about", "against", "between", "into", "through"
        }

        if os.path.exists(M1_CHUNKS_PATH):
            self.m1_df = pd.read_csv(M1_CHUNKS_PATH, dtype={'record_id': str, 'chunk_id': str})
        else:
            raise FileNotFoundError(f"M1 chunks file not found at {M1_CHUNKS_PATH}")

    def _resolve_anchors(self, local_graph: nx.Graph, target_nodes: List[str]) -> List[str]:
        """Maps Q2 signature targets to M5 node identifiers, excluding Governed Noise."""
        anchors = []
        clean_targets = [
            str(t).lower() for t in target_nodes 
            if str(t).lower() not in self.noise_words and len(str(t)) > 1
        ]
        
        for node_id in local_graph.nodes:
            node_id_lower = node_id.lower()
            for entity in clean_targets:
                # PhD Logic: Symbolic Anchor Match (Exact or Substring)
                if entity in node_id_lower or node_id_lower in entity:
                    anchors.append(node_id)
        return list(set(anchors))

    def _get_semantic_text_with_ids(self, record_id: str, chunk_ids=None) -> tuple:
        """Raw governed text chunks for Q5 (design-A aware: filter by chunk_ids if given)."""
        if self.m1_df is not None:
            if chunk_ids is not None:
                matches = self.m1_df[self.m1_df['chunk_id'].isin(set(map(str, chunk_ids)))]
            else:
                matches = self.m1_df[self.m1_df['record_id'] == str(record_id).strip()]
            if not matches.empty:
                cids = matches['chunk_id'].tolist()
                labeled_segments = [f"[{row['chunk_id']}]: {row['chunk_text']}" for _, row in matches.iterrows()]
                return " ".join(labeled_segments), cids
        raise ValueError(f"record_id {record_id} / chunks {chunk_ids} missing in M1 chunks")

    def _get_isolated_subgraph(self, record_id: str) -> tuple:
        """Epistemic Isolation. Design-A: scope to the question's OWN chunk_ids
        (output/serve_chunk_filter.json) when present; else original record_id isolation."""
        import json as _json
        if not hasattr(self, "_chunk_filter"):
            self._chunk_filter = None
            _cf = os.path.join("output", "serve_chunk_filter.json")
            if os.path.exists(_cf):
                with open(_cf, encoding="utf-8") as _f:
                    self._chunk_filter = _json.load(_f)
                print(f"[Q3] Design-A serve mode: {len(self._chunk_filter)} question filters loaded")

        def _edge_cid(data, key):
            for a in ("chunk_id", "source_chunk_id"):
                if data.get(a):
                    return str(data[a])
            fk = str(data.get("forensic_key") or key or "")
            parts = fk.split("_")
            return parts[-2] if len(parts) >= 2 else ""

        if self._chunk_filter is not None and str(record_id) in self._chunk_filter:
            wanted = set(map(str, self._chunk_filter.get(str(record_id), [])))
            relevant_edges = [(u, v, k) for u, v, k, data in self.G.edges(keys=True, data=True)
                              if _edge_cid(data, k) in wanted]
            if not relevant_edges:
                raise ValueError(f"No edges for question {record_id} ({len(wanted)} chunk ids) -- _edge_cid attr wrong?")
            source_text, chunk_ids = self._get_semantic_text_with_ids(record_id, chunk_ids=wanted)
            return self.G.edge_subgraph(relevant_edges).copy(), source_text, chunk_ids

        relevant_edges = []
        for u, v, k, data in self.G.edges(keys=True, data=True):
            edge_rid = data.get("record_id") or data.get("source_chunk_id")
            if str(edge_rid) == str(record_id):
                relevant_edges.append((u, v, k))
        if not relevant_edges:
            raise ValueError(f"No graph data found in M5 for record_id={record_id}")
        source_text, chunk_ids = self._get_semantic_text_with_ids(record_id)
        return self.G.edge_subgraph(relevant_edges).copy(), source_text, chunk_ids

    def _perform_governed_walk(self, local_graph: nx.Graph, anchors: List[str], 
                               predicates: List[str], k_hops: int) -> Set[tuple]:
        """
        Executes symbolic k-hop traversal.
        Constraint: Only follows predicates authorized by the Q2 Search Warrant.
        """
        discovered_triples = set()
        current_layer = set(anchors)
        visited_nodes = set(anchors)
        
        for hop in range(k_hops):
            next_layer = set()
            for u in current_layer:
                # Bidirectional traversal (generic): a query entity may be the SUBJECT or the
                # OBJECT of a governed relation; follow in+out edges, preserving true s->o direction.
                if local_graph.is_directed():
                    cand = [(u, v, data) for _, v, data in local_graph.out_edges(u, data=True)]
                    cand += [(w, u, data) for w, _, data in local_graph.in_edges(u, data=True)]
                else:
                    cand = [(u, v, data) for _, v, data in local_graph.edges(u, data=True)]
                for s_node, o_node, data in cand:
                    p_label = data.get('predicate', 'related_to')
                    # PhD Logic: Predicate Pruning (direction-agnostic reachability)
                    if not predicates or any(p.lower() in p_label.lower() for p in predicates):
                        discovered_triples.add((s_node, p_label, o_node))
                        neighbor = o_node if s_node == u else s_node
                        if neighbor not in visited_nodes:
                            next_layer.add(neighbor)
            current_layer = next_layer
            visited_nodes.update(next_layer)
            if not current_layer: break
        return discovered_triples

    def process(self, filter_id: str = None, signature_path: str = "output/Q2_signatures.jsonl"):
        print("--- Q3 V3: Governed Graph Engine (Frozen DSR State) ---")

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as _:
            pass       
        
        if not os.path.exists(signature_path):
            print(f"[ERROR] Signature file not found: {signature_path}")
            raise SystemExit(1)

        with open(signature_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                if not line.strip(): continue
                record = json.loads(line)
                # UNIFIED NAMESPACE: Strictly use record_id
                record_id = record.get("record_id")
                
                if filter_id and str(record_id) != str(filter_id):
                    continue
                
                # 1. Epistemic Isolation (Subgraph Extraction)
                local_g, semantic_chunk, chunk_ids = self._get_isolated_subgraph(record_id)
                
                # 2. Anchor Resolution
                anchors = self._resolve_anchors(local_g, record["q_signature"]["target_nodes"])
                print(f"[Q3] Record {record_id[:8]} | Anchors found: {len(anchors)}")

                # 3. Governed Walk
                triples = self._perform_governed_walk(
                    local_g, 
                    anchors, 
                    record["q_signature"]["required_predicates"], 
                    record["traversal_parameters"]["k_hops"]
                )
                
                new_triplets = []
                for t in triples:
                    trip = {"s": t[0], "p": t[1], "o": t[2]}
                    s_data = self.G.nodes[t[0]] if self.G.has_node(t[0]) else {}
                    o_data = self.G.nodes[t[2]] if self.G.has_node(t[2]) else {}
                    trip["s_align"] = s_data.get("alignment_status", "Unknown")
                    trip["o_align"] = o_data.get("alignment_status", "Unknown")
                    new_triplets.append(trip)
                
                # 4. Persistence
                self._update_output_file(record_id, chunk_ids, semantic_chunk, new_triplets, record)

    def _update_output_file(self, record_id, chunk_ids, semantic_chunk, new_triplets, record):
        """Additive update that preserves the record_id key."""
        existing_data = {}
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    existing_data[data["record_id"]] = data

        # Overwrite or Create
        existing_data[record_id] = {
            "record_id": record_id,
            "contributing_chunks": chunk_ids,
            "question": record["question"],
            "semantic_chunk": semantic_chunk,
            "symbolic_triplets": new_triplets,
            "q_signature": record.get("q_signature"), # Carry signature for Q5 audit
            "justification": record.get("justification"), # Carry justification
            "traversal_stats": {
                "hops": record["traversal_parameters"]["k_hops"], 
                "count": len(new_triplets)
            }
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            for rid in existing_data:
                outfile.write(json.dumps(existing_data[rid], ensure_ascii=False) + '\n')
        
        print(f"[SUCCESS] {record_id[:8]} | Triples Extracted: {len(new_triplets)}")

if __name__ == "__main__":
    engine = GovGraphRetrievalEngineV3()
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    engine.process(filter_id=target_id)