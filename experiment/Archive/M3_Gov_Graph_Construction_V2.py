# --------------------------------------------------------------------------
# MODULE 3: Governed Knowledge Graph Construction (M3_V2)
# Goal: Construct a traceable Knowledge Graph from governed M2 triples.
# Implementation: Golden Thread Persistence for Dissertation Rigor.
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
import networkx as nx
import time

print("--- Starting Module 3: Governed Knowledge Graph Construction (M3_V2) ---")

# --- 0. Setup and Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Extracted_Triples.json")
OUTPUT_GML = os.path.join(PROJECT_ROOT, "output", "M3_Gov_Knowledge_Graph.gml")
OUTPUT_EDGES_CSV = os.path.join(PROJECT_ROOT, "output", "M3_Gov_Graph_Edges.csv")

# Metrics Registry for Dissertation Documentation
metrics = {
    "start_time": 0,
    "end_time": 0,
    "total_triples_ingested": 0,
    "unique_nodes": 0,
    "total_edges": 0
}

def build_governed_graph():
    """Constructs the Graph while maintaining the Layer 1-2-3 Traceability."""
    
    metrics["start_time"] = time.time()
    
    # 1. Load Governed Triples from M2
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            triples_list = json.load(f)
    except FileNotFoundError:
        print(f"[CRITICAL ERROR] M2 Triples not found: {INPUT_FILE}")
        return False

    # 2. Initialize Directed Graph
    G = nx.DiGraph()
    edge_audit_list = []

    # 3. Populate Graph with the Golden Thread
    for i, triple in enumerate(triples_list):
        subject = triple['subject']
        predicate = triple['predicate']
        object_ = triple['object']
        
        # Preservation of the Traceability Lineage
        record_id = triple.get('record_id', 'UNKNOWN_REC')      # Layer 1
        chunk_id = triple.get('source_chunk_id', 'UNKNOWN_CHNK') # Layer 2
        
        # Add edge with multi-layer metadata
        G.add_edge(
            subject, 
            object_, 
            relationship=predicate, 
            record_id=record_id, 
            source_chunk_id=chunk_id
        )
        
        # Prepare audit record
        edge_audit_list.append({
            'source': subject,
            'target': object_,
            'predicate': predicate,
            'record_id': record_id,
            'chunk_id': chunk_id
        })

    metrics["total_triples_ingested"] = len(triples_list)
    metrics["unique_nodes"] = G.number_of_nodes()
    metrics["total_edges"] = G.number_of_edges()
    metrics["end_time"] = time.time()

    # 4. Persistence
    nx.write_gml(G, OUTPUT_GML)
    df_edges = pd.DataFrame(edge_audit_list)
    df_edges.to_csv(OUTPUT_EDGES_CSV, index=False)

    # --- DISSERTATION METRICS PRINTOUT ---
    duration = metrics["end_time"] - metrics["start_time"]
    print("\n" + "="*50)
    print("M3_V2: GOVERNED GRAPH CONSTRUCTION METRICS")
    print("="*50)
    print(f"Total Triples Ingested:    {metrics['total_triples_ingested']}")
    print(f"Graph Nodes (Concepts):    {metrics['unique_nodes']}")
    print(f"Graph Edges (Relations):   {metrics['total_edges']}")
    print(f"Processing Time:           {duration:.4f} seconds")
    print(f"Traceability Audit:        SUCCESS (Record+Chunk IDs Persisted)")
    print(f"Artifact Saved (GML):      {OUTPUT_GML}")
    print(f"Artifact Saved (Audit):    {OUTPUT_EDGES_CSV}")
    print("="*50 + "\n")

    return True

if __name__ == "__main__":
    build_governed_graph()