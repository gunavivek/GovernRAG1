# --------------------------------------------------------------------------
# MODULE 5.5: GOVERNED QUANTITATIVE VALIDATION (V2)
# GOAL: Calculate APCS and Traceability Scores to validate Semantic Grounding.
# --------------------------------------------------------------------------
import os
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import json
from datetime import datetime

# --- 0. Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Input: The finalized, vectorized hybrid graph from M5 [cite: 7]
INPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_Gov_Embedded_Graph.gml')
# Outputs: Statistical reports and traceability matrices for dissertation evidence 
OUTPUT_APCS_JSON = os.path.join(PROJECT_ROOT, 'output', 'M5_5_APCS_Report.json')
OUTPUT_TRACE_CSV = os.path.join(PROJECT_ROOT, 'output', 'M5_5_Full_Trace_Matrix.csv')

def run_governed_audit():
    if not os.path.exists(INPUT_FILE):
        print(f"[CRITICAL ERROR] M5 Artifact missing: {INPUT_FILE}")
        return

    # Load the graph containing the high-dimensional vectors [cite: 7]
    G = nx.read_gml(INPUT_FILE)
    print(f"--- Starting M5.5 V2: Analyzing {G.number_of_nodes()} Nodes & {G.number_of_edges()} Edges ---")

    # 1. Extract Vectors and Metadata for Authority Stratification 
    nodes_list = []
    for node, data in G.nodes(data=True):
        if 'embedding' in data and data['embedding'] is not None:
            nodes_list.append({
                'id': node,
                'type': data.get('node_type', 'UnmappedConcept'),
                'domain': data.get('industry_domain', 'Unknown'),
                'vec': np.array(data['embedding']).reshape(1, -1)
            })
    
    if not nodes_list:
        print("[ERROR] No embedding data found in the graph nodes.")
        return

    df_nodes = pd.DataFrame(nodes_list)

    # 2. Relationship Similarity (The Traceability Matrix) 
    # This validates the "triangulation" between document facts and BIZBOK standards 
    trace_data = []
    for u, v, data in G.edges(data=True):
        rel = data.get('relationship')
        # We only audit the governance-specific alignment edges [cite: 7]
        if rel in ['IS_ALIGNED_WITH', 'ADAPTED_FROM']:
            try:
                vec_u = np.array(G.nodes[u]['embedding']).reshape(1, -1)
                vec_v = np.array(G.nodes[v]['embedding']).reshape(1, -1)
                
                # Math: Cosine Similarity calculation 
                sim = cosine_similarity(vec_u, vec_v)[0][0]
                
                trace_data.append({
                    'Source Concept': u,
                    'Source Type': G.nodes[u].get('node_type'),
                    'Reference Anchor': v,
                    'Relationship': rel,
                    'Similarity Score': round(float(sim), 4)
                })
            except KeyError:
                continue

    df_trace = pd.DataFrame(trace_data).sort_values(by='Similarity Score', ascending=False)
    df_trace.to_csv(OUTPUT_TRACE_CSV, index=False)

    # 3. APCS Calculation (By Node Type Group) 
    # Proves that ReferenceConcepts act as high-authority anchors 
    groups = ['ReferenceConcept', 'AdaptiveConcept', 'DocumentConcept', 'UnmappedConcept']
    apcs_results = {}

    for g in groups:
        group_vectors = df_nodes[df_nodes['type'] == g]['vec'].tolist()
        if len(group_vectors) > 1:
            X = np.vstack(group_vectors)
            sim_matrix = cosine_similarity(X)
            # Use upper triangle mean to find Average Pairwise Cosine Similarity 
            mask = np.triu_indices_from(sim_matrix, k=1)
            apcs_results[g] = round(float(np.mean(sim_matrix[mask])), 4)
        else:
            apcs_results[g] = "Insufficient Data"

    # 4. Final Dissertation Validation Report 
    mean_triangulation = df_trace['Similarity Score'].mean() if not df_trace.empty else 0
    
    report = {
        "metadata": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "validation_timestamp": datetime.now().isoformat(),
            "embedding_model": "text-embedding-004"
        },
        "apcs_scores_by_authority": apcs_results,
        "triangulation_metrics": {
            "mean_triangulation_similarity": round(float(mean_triangulation), 4),
            "edge_count_audited": len(df_trace)
        },
        "integrity_check": "PASS" if mean_triangulation > 0.70 else "FAIL"
    }

    with open(OUTPUT_APCS_JSON, 'w') as f:
        json.dump(report, f, indent=4)

    print(f"\n[SUCCESS] M5.5_V2 Quantitative Audit Complete.")
    print(f"Mean Triangulation Similarity: {report['triangulation_metrics']['mean_triangulation_similarity']}")
    print(f"Full Report: {OUTPUT_APCS_JSON}")
    print(f"Traceability Matrix: {OUTPUT_TRACE_CSV}")

if __name__ == "__main__":
    run_governed_audit()