# --------------------------------------------------------------------------
# MODULE 3: Knowledge Graph Construction (M3_V2)
# STRATEGY: Immediate Node Attribution & Provenance Anchoring
# GOAL: Resolve CH-001 (Metadata Vacuum) by stapling IDs to Nodes at birth.
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
import networkx as nx
from datetime import datetime

print("--- Starting Module 3: Provenance-Aware Graph Construction (V2) ---")

# --- 0. Setup Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
INPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M2_Extracted_Triples.json')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_Gov_Knowledge_Graph.gml')
OUTPUT_EDGES_CSV = os.path.join(PROJECT_ROOT, 'output', 'M3_Graph_Edges.csv')

def build_governed_graph():
    """Constructs a NetworkX graph ensuring every Node and Edge carries metadata."""
    
    # 1. Load Extracted Triples
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            triples_list = json.load(f)
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to load M2 artifact: {e}")
        return False

    # 2. Initialize Directed Graph
    G = nx.DiGraph()
    edge_data_list = []

    print(f"Processing {len(triples_list)} triples...")

    # 3. Populate with Metadata Persistence
    for triple in triples_list:
        subject = str(triple.get('subject', 'Unknown')).strip()
        predicate = str(triple.get('predicate', 'related_to')).strip()
        object_ = str(triple.get('object', 'Unknown')).strip()
        source_id = triple.get('source_chunk_id', 'Unknown_Source')

        # --- CORRECTIVE ACTION: IMMEDIATE NODE ATTRIBUTION ---
        # Instead of letting add_edge create blank nodes, we initialize them with metadata
        for node_name in [subject, object_]:
            if node_name not in G:
                G.add_node(
                    node_name, 
                    source_chunk_id=source_id, 
                    node_type="InitialConcept",
                    created_at=datetime.now().strftime('%Y-%m-%d')
                )
            else:
                # If node exists, we append the source ID if it's from a different chunk
                current_sources = G.nodes[node_name].get('source_chunk_id', "")
                if source_id not in current_sources:
                    G.nodes[node_name]['source_chunk_id'] = f"{current_sources}; {source_id}"

        # --- ADD RELATIONSHIP (EDGE) ---
        G.add_edge(
            subject, 
            object_, 
            relationship=predicate, 
            source_chunk_id=source_id,
            domain=triple.get('domain', 'General'),
            confidence=triple.get('confidence_score', 0)
        )
        
        edge_data_list.append({
            'source': subject, 'target': object_, 
            'relationship': predicate, 'source_chunk_id': source_id
        })

    # 4. Persistence
    nx.write_gml(G, OUTPUT_FILE)
    pd.DataFrame(edge_data_list).to_csv(OUTPUT_EDGES_CSV, index=False)
    
    print(f"\n[SUCCESS] M3_V2 Complete.")
    print(f"Total Nodes: {G.number_of_nodes()} (All attributed with source_chunk_id)")
    print(f"Total Edges: {G.number_of_edges()}")
    return True

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    build_governed_graph()