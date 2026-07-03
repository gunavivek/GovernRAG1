# --------------------------------------------------------------------------
# MODULE 5: Contextual Embedding (Graph Vectors)
# FINAL FIX: Corrects object access and keyword arguments for modern Google SDK.
# --------------------------------------------------------------------------
import os
import networkx as nx
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types # Keep types for robustness, though not directly used in embed_content

print("--- Starting Module 5: Contextual Embedding Generation ---")

# --- 0. Setup and Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = 'text-embedding-004' 
EMBEDDING_DIM = 768 # Standard dimension for text-embedding-004

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

INPUT_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.gml')
OUTPUT_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_Embedded_Graph.gml')


# --- 1. Core Embedding Function (CRITICAL FIX APPLIED) ---
def get_embedding(client: genai.Client, text: str) -> np.ndarray:
    """Calls Gemini's embedding model with corrected parameters and parsing."""
    if not text.strip():
        # Use np.zeros for clean fallback
        return np.zeros(EMBEDDING_DIM, dtype=np.float32) 
        
    try:
        # FIX 1: Use `contents=` (plural) for the standard Python SDK
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, 
            contents=[text] 
        )
        
        # FIX 2: Access the vector using attribute indexing (response.embeddings[0].values)
        if getattr(response, "embeddings", None):
             values = response.embeddings[0].values
        else:
             raise ValueError("No valid embedding array returned from API object.")
             
        return np.array(values, dtype=np.float32)
        
    except Exception as e:
        # If this still fails, the graph will be filled with zero vectors.
        print(f"  [CRITICAL API FAILURE] Embedding failed for text: {text[:50]}... Error: {e}")
        return np.zeros(EMBEDDING_DIM, dtype=np.float32) 


# --- 2. Main Embedding Logic ---
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("\n[SETUP ERROR] GEMINI_API_KEY not found. Cannot run embedding.")
        exit()

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Load the M4 Hybrid Graph
    try:
        G = nx.read_gml(INPUT_GRAPH_FILE)
    except FileNotFoundError:
        print(f"\n[ERROR] Input graph not found: {INPUT_GRAPH_FILE}. Please run M4_concept_alignment.py first.")
        exit()
    
    print(f"Loaded Hybrid Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
    
    # --- 3. Embed Nodes (Concepts) ---
    print("\n--- Embedding Concepts (Nodes) ---")
    
    for node_id, data in G.nodes(data=True):
        embedding_text = (
            f"Node Type: {data.get('node_type', 'Concept')}; "
            f"Domain: {data.get('industry_domain', 'Document')}; "
            f"Concept: {data.get('base_concept_name', node_id)}; "
            f"Definition: {data.get('definition', 'N/A')}"
        )
        
        vector = get_embedding(client, embedding_text)
        G.nodes[node_id]['embedding'] = vector.tolist()
        G.nodes[node_id]['embedding_model'] = EMBEDDING_MODEL

    
    # --- 4. Embed Edges (Relationships) ---
    print("\n--- Embedding Relationships (Edges) ---")
    
    for u, v, data in G.edges(data=True):
        embedding_text = (
            f"Relationship: {data.get('relationship')}. "
            f"Source Concept: {u}. Target Concept: {v}."
        )
        
        vector = get_embedding(client, embedding_text)
        G.edges[u, v]['embedding'] = vector.tolist()
        G.edges[u, v]['embedding_model'] = EMBEDDING_MODEL
        
    print(f"\nEmbedding complete. Nodes embedded: {G.number_of_nodes()}. Edges embedded: {G.number_of_edges()}.")

    # --- 5. Save the Embedded Graph ---
    try:
        output_dir = os.path.join(PROJECT_ROOT, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        nx.write_gml(G, OUTPUT_GRAPH_FILE)
        print(f"\n[SUCCESS] Module 5 successfully completed!")
        print(f"Embedded Graph saved to: {OUTPUT_GRAPH_FILE}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save graph. Reason: {e}")