# --------------------------------------------------------------------------
# MODULE 5.5: Embedding Validation (TRACEABILITY MATRIX CALCULATION)
# FIX: Corrected vector extraction and DataFrame structure to prevent the 
#      'too many values to unpack' error.
# --------------------------------------------------------------------------
import os
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
from dotenv import load_dotenv

print("--- Starting Module 5.5: Traceability Matrix Calculation ---")

# --- 0. Setup ---
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

INPUT_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_Embedded_Graph.gml')
OUTPUT_APCS_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_5_APCS_Matrix.csv')
OUTPUT_TRACE_MATRIX_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_5_Full_Trace_Matrix.csv')


# --- 1. Load Data and Extract Vectors (CRITICAL FIX HERE) ---
def extract_vectors(G):
    """Extracts node data and vector matrix from the embedded graph."""
    nodes_data = []
    
    for node_id, data in G.nodes(data=True):
        
        # Only process nodes that actually contain the embedding attribute (M5 output)
        if 'embedding' in data and data['embedding'] is not None:
            
            # Store metadata
            nodes_data.append({
                'Node ID': node_id,
                'Type': data.get('node_type', 'Unknown'),
                'Domain': data.get('industry_domain', 'Unknown'),
                'Base Concept': data.get('base_concept_name', node_id.split(':')[-1]),
                # Store the vector itself as a list/array attribute in the DataFrame
                'Embedding': np.array(data['embedding'])
            })
            
    # X (the matrix) will be derived from the 'Embedding' column of the DataFrame
    df_nodes = pd.DataFrame(nodes_data)
    
    # Check if df_nodes is empty to prevent failure later
    if df_nodes.empty:
        return df_nodes, np.array([]) 

    # Extract the NumPy array matrix (X) from the 'Embedding' column
    X = np.stack(df_nodes['Embedding'].values)
    
    return df_nodes, X


# --- 2. APCS Matrix Calculation ---
def calculate_apcs_matrix(df_nodes, X):
    """Calculates the Average Pairwise Cosine Similarity (APCS) matrix."""
    groups = ['ReferenceConcept', 'AdaptiveConcept', 'DocumentConcept']
    similarity_matrix = {g: {} for g in groups}
    
    for type_a in groups:
        # Filter vectors based on Type
        vectors_a = X[df_nodes['Type'] == type_a]
        
        for type_b in groups:
            vectors_b = X[df_nodes['Type'] == type_b]
            
            if len(vectors_a) == 0 or len(vectors_b) == 0:
                similarity_matrix[type_a][type_b] = np.nan
                continue
            
            pairwise_sim = cosine_similarity(vectors_a, vectors_b)
            apcs = np.mean(pairwise_sim)
            similarity_matrix[type_a][type_b] = apcs
            
    df_matrix = pd.DataFrame(similarity_matrix).T
    df_matrix.columns = [c.replace('Concept', '') for c in df_matrix.columns]
    df_matrix.index = [c.replace('Concept', '') for c in df_matrix.index]
    
    return df_matrix.map(lambda x: f"{x:.4f}" if pd.notna(x) else 'N/A')


# --- 3. Full Traceability Matrix Calculation ---
def calculate_full_trace_matrix(G, df_nodes):
    """
    Calculates the similarity scores required by the user's custom matrix structure.
    """
    
    # Create a mapping dictionary for easy vector lookup {Node ID: Vector}
    # This map now uses the 'Embedding' column from the DataFrame
    vector_map = {row['Node ID']: row['Embedding'] for index, row in df_nodes.iterrows()}
    
    scores_list = []
    
    # Iterate over all M4 linking edges (IS_ALIGNED_WITH / ADAPTED_FROM)
    for u, v, data in G.edges(data=True):
        relationship = data.get('relationship')
        if relationship not in ['IS_ALIGNED_WITH', 'ADAPTED_FROM']:
            continue
            
        source_id = u
        anchor_id = v
        
        source_row = df_nodes[df_nodes['Node ID'] == source_id].iloc[0]
        
        source_vector = vector_map.get(source_id)
        anchor_vector = vector_map.get(anchor_id)
        
        # Ensure both vectors exist (non-None and non-zero vectors from M5)
        if source_vector is not None and anchor_vector is not None and np.any(source_vector) and np.any(anchor_vector):
            
            sim_score = cosine_similarity(source_vector.reshape(1, -1), anchor_vector.reshape(1, -1))[0][0]
            
            # --- Populate the required columns based on Source Type ---
            source_type = source_row['Type']
            
            scores_list.append({
                'Source Concept Name': source_id,
                'Source Type': source_type,
                'Reference Anchor Name': anchor_id,
                'Source_Anchor_Similarity': sim_score,
                
                # Document-Adaptive similarity (Only defined if source is Document)
                'Document_Adaptive_Similarity': sim_score if source_type == 'DocumentConcept' else np.nan, 
                # Adaptive-Reference similarity (Only defined if source is Adaptive)
                'Adaptive_Reference_Similarity': sim_score if source_type == 'AdaptiveConcept' else np.nan, 
            })
        
    df_results = pd.DataFrame(scores_list)
    
    # --- FIX: Guarantee Column Existence (The solution to KeyError) ---
    required_cols = ['Document_Adaptive_Similarity', 'Adaptive_Reference_Similarity', 'Source_Anchor_Similarity']
    for col in required_cols:
        if col not in df_results.columns:
            # Initialize missing column with NaN
            df_results[col] = np.nan 
    # --- END FIX ---

    # FINAL CLEANUP: Format the numerical scores
    for col in ['Document_Adaptive_Similarity', 'Adaptive_Reference_Similarity', 'Source_Anchor_Similarity']:
        df_results[col] = df_results[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else '')
        
    # The sort key is the Source_Anchor_Similarity score
    return df_results.sort_values(by='Source_Anchor_Similarity', ascending=False, key=lambda x: pd.to_numeric(x.str.replace('N/A', '-1')))


# --- 4. Main Execution and Artifact Saving ---
if __name__ == "__main__":
    
    try:
        G = nx.read_gml(INPUT_GRAPH_FILE)
        df_nodes, X = extract_vectors(G)
    except Exception as e:
        print(f"\n[ERROR] Initialization failed. Error: {e}")
        exit()

    if X.size == 0:
        print("WARNING: No embeddings found. Cannot perform validation.")
        exit()

    # --- Task A: Calculate and Save APCS Matrix ---
    df_apcs_matrix = calculate_apcs_matrix(df_nodes, X)
    df_apcs_matrix.to_csv(OUTPUT_APCS_FILE, float_format='%.4f')
    print(f"\n[SUCCESS] APCS Matrix saved to: {OUTPUT_APCS_FILE}")

    # --- Task B: Calculate and Save Full Traceability Matrix ---
    df_full_trace_matrix = calculate_full_trace_matrix(G, df_nodes)
    df_full_trace_matrix.to_csv(OUTPUT_TRACE_MATRIX_FILE, index=False)
    print(f"[SUCCESS] Full Traceability Matrix saved to: {OUTPUT_TRACE_MATRIX_FILE}")

    print("\nModule 5.5 (Calculation) successfully completed.")