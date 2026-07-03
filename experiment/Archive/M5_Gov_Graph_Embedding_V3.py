# --------------------------------------------------------------------------
# MODULE 5: M5_Gov_Graph_Embedding_V3.py
# ARCHITECTURE: Poly-Ontological Vectorization
# DISSERTATION GOAL: Embeds Governance Metadata & Weights into Vector Space
# --------------------------------------------------------------------------
import os
import networkx as nx
import numpy as np
import json
import time
from dotenv import load_dotenv
from google import genai

print("--- Starting M5_V3.0: Governed Graph Vectorization ---")

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key: print("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
EMBEDDING_MODEL = 'models/gemini-embedding-001' 
EMBEDDING_DIM = 768
RATE_LIMIT_DELAY = 1.0

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# INPUT: The Hybrid Graph from M4 (GraphML format)
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.graphml')
# OUTPUT: The Vectorized Graph
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M5_Embedded_Graph.graphml')

# --- 1. Embedding Wrapper ---
def get_embedding(text: str):
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[text]
        )
        # Return as list for JSON serialization compatibility
        return response.embeddings[0].values
    except Exception as e:
        print(f"   [Error] Embedding failed: {e}")
        return [0.0] * EMBEDDING_DIM

# --- 2. Main Execution ---
def run_m5_embedding():
    # 1. Load Graph
    if not os.path.exists(INPUT_GRAPH):
        print(f"[CRITICAL] Input Graph missing: {INPUT_GRAPH}")
        return

    print("Loading Hybrid Graph (MultiDiGraph)...")
    try:
        # Load as MultiDiGraph to preserve parallel edges
        G = nx.read_graphml(INPUT_GRAPH)
        print(f"-> Loaded {G.number_of_nodes()} Nodes, {G.number_of_edges()} Edges.")
    except Exception as e:
        print(f"[ERROR] Loading failed. Ensure M4 output is valid GraphML. {e}")
        return

    # 2. Embed Nodes (Concepts)
    print("\nVectorizing Nodes (with Governance Metadata)...")
    node_count = 0
    for node, data in G.nodes(data=True):
        # Construct Rich Feature String
        # We include the Definition (Semantic) and Status (Governance)
        defn = data.get('definition', data.get('generated_definition', ''))
        status = data.get('alignment_status', 'Unknown')
        n_type = data.get('type', 'Concept')
        
        feature_text = (
            f"Concept: {node} | "
            f"Definition: {defn} | "
            f"Governance Status: {status} | "
            f"Type: {n_type}"
        )
        
        vector = get_embedding(feature_text)
        
        # Serialize vector as JSON string to avoid GraphML parsing errors
        G.nodes[node]['embedding'] = json.dumps(vector)
        G.nodes[node]['embedding_model'] = EMBEDDING_MODEL
        
        node_count += 1
        if node_count % 50 == 0: print(f"   Embedded {node_count} nodes...")
        time.sleep(RATE_LIMIT_DELAY)

    # 3. Embed Edges (Relationships)
    print("\nVectorizing Edges (with Epistemic Weights)...")
    edge_count = 0
    
    # Iterate over Multi-Edges (u, v, key, data)
    for u, v, key, data in G.edges(keys=True, data=True):
        # Construct Weighted Feature String
        pred = data.get('predicate', 'related_to')
        dom = data.get('domain', 'General')
        weight = data.get('weight', 0.1)
        mode = data.get('provenance', 'STRICT')
        
        feature_text = (
            f"Source: {u} | "
            f"Relationship: {pred} | "
            f"Target: {v} | "
            f"Domain Context: {dom} | "
            f"Authority Weight: {weight} | "
            f"Extraction Mode: {mode}"
        )
        
        vector = get_embedding(feature_text)
        
        # Serialize
        G.edges[u, v, key]['embedding'] = json.dumps(vector)
        
        edge_count += 1
        if edge_count % 50 == 0: print(f"   Embedded {edge_count} edges...")
        time.sleep(RATE_LIMIT_DELAY)

    # 4. Persistence
    print(f"\nSaving Vectorized Graph to {OUTPUT_GRAPH}...")
    nx.write_graphml(G, OUTPUT_GRAPH)
    
    print("\n" + "="*50)
    print("M5_V3.0 COMPLETE. Graph Vectorized.")
    print(f"Nodes Embedded: {node_count}")
    print(f"Edges Embedded: {edge_count}")
    print("="*50)

if __name__ == "__main__":
    run_m5_embedding()