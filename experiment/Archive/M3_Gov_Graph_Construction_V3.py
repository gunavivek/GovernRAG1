# --------------------------------------------------------------------------
# MODULE 3: M3_Gov_Graph_Builder_V3.py
# ARCHITECTURE: Weighted Multi-Directed Graph (NetworkX MultiDiGraph)
# DISSERTATION GOAL: Preserves Poly-Ontological Edges & Weights
# --------------------------------------------------------------------------
import json
import networkx as nx
import os
import pandas as pd
from datetime import datetime

# --- 0. Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
INPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M2_Extracted_Triples.json')
OUTPUT_GRAPHML = os.path.join(PROJECT_ROOT, 'output', 'M3_Knowledge_Graph.graphml')
OUTPUT_STATS = os.path.join(PROJECT_ROOT, 'output', 'M3_Graph_Stats.csv')

def build_governed_graph():
    print("--- Starting M3_V3.0: Poly-Ontological Graph Construction ---")

    if not os.path.exists(INPUT_FILE):
        print(f"[CRITICAL] Input file missing: {INPUT_FILE}")
        return

    # 1. Load Extracted Triples
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        triples = json.load(f)

    # 2. Initialize Multi-Directed Graph
    # CRITICAL CHANGE: MultiDiGraph allows parallel edges (Same S-O, different Predicate/Domain)
    G = nx.MultiDiGraph()

    print(f"-> Ingesting {len(triples)} Semantic Triples...")

    edge_count = 0
    skipped_count = 0
    domain_counter = {}

    # 3. Graph Assembly Loop
    for item in triples:
        subj = str(item.get("subject", "")).strip()
        obj = str(item.get("object", "")).strip()
        pred = str(item.get("predicate", "")).strip()
        domain = item.get("domain", "Unknown")
        
        # Validation
        if not subj or not obj or not pred:
            skipped_count += 1
            continue

        # Add Nodes (NetworkX creates them if they don't exist)
        # We add a 'type' attribute to help visualization tools
        if subj not in G:
            G.add_node(subj, label=subj, type="Entity", created_at=datetime.now().strftime('%Y-%m-%d'))
        if obj not in G:
            G.add_node(obj, label=obj, type="Entity", created_at=datetime.now().strftime('%Y-%m-%d'))

        # Track Domain Stats
        domain_counter[domain] = domain_counter.get(domain, 0) + 1

        # Add Weighted Edge
        # We use the Domain + Predicate as the unique 'key' for the parallel edge
        # This ensures (Nets)-[is_a]->(Team) via Sports AND Media can coexist.
        G.add_edge(
            subj, 
            obj, 
            key=f"{domain}_{pred}", # Unique Edge ID
            predicate=pred,
            weight=float(item.get("weight", 0.1)), # $Wa Score from M1/M2
            domain=domain,
            provenance=item.get("extraction_mode", "STRICT"), # Strict vs Discovery
            record_id=item.get("record_id", "N/A"),
            chunk_id=item.get("chunk_id", "N/A")
        )
        edge_count += 1

    # 4. Topology Analytics (The "Results" Section)
    print("\n" + "="*40)
    print("M3 GRAPH TOPOLOGY METRICS")
    print("="*40)
    print(f"Total Unique Nodes: {G.number_of_nodes()}")
    print(f"Total Weighted Edges: {G.number_of_edges()}")
    
    # Identify Hubs (High Degree Centrality)
    # In a MultiGraph, degree sums all parallel edges, identifying true "Cross-Domain Concepts"
    degree_dict = dict(G.degree())
    sorted_degree = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)
    
    print("\n[TOP 5 AUTHORITY HUBS]")
    for entity, degree in sorted_degree[:5]:
        print(f"  > {entity}: {degree} connections")

    print("\n[DOMAIN DOMINANCE]")
    for dom, count in domain_counter.items():
        print(f"  > {dom}: {count} edges")

    # 5. Export
    # Export Stats to CSV
    stats_data = [{"Entity": k, "Degree": v} for k, v in sorted_degree]
    pd.DataFrame(stats_data).to_csv(OUTPUT_STATS, index=False)

    # Export GraphML (Best format for Gephi/Neo4j with rich attributes)
    nx.write_graphml(G, OUTPUT_GRAPHML)
    
    print("\n" + "="*40)
    print(f"[SUCCESS] Graph serialized to: {OUTPUT_GRAPHML}")
    print("M3 Complete.")

if __name__ == "__main__":
    build_governed_graph()