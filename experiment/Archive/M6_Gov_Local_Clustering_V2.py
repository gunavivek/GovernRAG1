# --------------------------------------------------------------------------
# MODULE 6: GOVERNED LOCAL CLUSTERING (V2)
# GOAL: Cluster nodes within document boundaries to prevent semantic bleed,
#       while anchoring them to BIZBOK® standards for global context.
# --------------------------------------------------------------------------
import os
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

# --- 0. Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_Gov_Embedded_Graph.gml')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M6_Gov_Clustered_Graph.gml')

# Hyperparameters
CLUSTERS_PER_DOC = 3  # Target number of thematic communities per record

def run_governed_clustering():
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input graph not found: {INPUT_FILE}")
        return

    G = nx.read_gml(INPUT_FILE)
    print(f"--- Starting M6 V2: Clustering {G.number_of_nodes()} Nodes ---")

    # 1. Identify Independent Records (Source Contexts)
    # We use source_chunk_id or a similar attribute to isolate the 10 records
    nodes_by_record = {}
    reference_nodes = []

    for node, data in G.nodes(data=True):
        if data.get('node_type') == 'ReferenceConcept':
            reference_nodes.append(node)
        elif 'embedding' in data:
            # Use source_chunk_id or metadata as the isolation key
            record_id = data.get('source_chunk_id', 'Global_Context').split('_')[0] 
            if record_id not in nodes_by_record:
                nodes_by_record[record_id] = []
            nodes_by_record[record_id].append(node)

    print(f"Found {len(nodes_by_record)} independent records for isolation.")

    # 2. Local Clustering Logic (Per Document)
    total_communities = 0
    
    for record_id, node_ids in nodes_by_record.items():
        if len(node_ids) < CLUSTERS_PER_DOC:
            # Assign single community if too few nodes
            for nid in node_ids:
                G.nodes[nid]['community_id'] = f"{record_id}_COMM_0"
            continue

        # Extract vectors for the local document
        vectors = np.array([G.nodes[nid]['embedding'] for nid in node_ids])
        
        # Apply K-Means
        kmeans = KMeans(n_clusters=CLUSTERS_PER_DOC, random_state=42, n_init='auto')
        labels = kmeans.fit_predict(vectors)

        # 3. Anchor-Based Tagging (The "Global Bridge")
        # For each local cluster, find the most representative BIZBOK anchor
        for cluster_idx in range(CLUSTERS_PER_DOC):
            cluster_node_ids = [node_ids[i] for i, l in enumerate(labels) if l == cluster_idx]
            community_label = f"{record_id}_THEME_{cluster_idx}"
            
            # Identify the most frequent Reference Anchor linked to this cluster
            anchor_candidates = []
            for cnid in cluster_node_ids:
                G.nodes[cnid]['community_id'] = community_label
                # Check M4 alignment edges
                for neighbor in G.neighbors(cnid):
                    if G.nodes[neighbor].get('node_type') == 'ReferenceConcept':
                        anchor_candidates.append(neighbor)
            
            # Determine the "Global Context" label for this local cluster
            if anchor_candidates:
                top_anchor = Counter(anchor_candidates).most_common(1)[0][0]
                global_context = G.nodes[top_anchor].get('industry_domain', 'Common')
                # Tag the nodes with the global context derived from the anchor
                for cnid in cluster_node_ids:
                    G.nodes[cnid]['global_anchor_context'] = f"{global_context}:{top_anchor}"
            else:
                for cnid in cluster_node_ids:
                    G.nodes[cnid]['global_anchor_context'] = "Unanchored"

        total_communities += CLUSTERS_PER_DOC

    # 4. Save and Finalize
    nx.write_gml(G, OUTPUT_FILE)
    print(f"\n[SUCCESS] M6_V2 Complete.")
    print(f"Generated {total_communities} local communities across {len(nodes_by_record)} records.")
    print(f"Governed Clustered Graph saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_governed_clustering()