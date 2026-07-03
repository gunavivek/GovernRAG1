# --------------------------------------------------------------------------
# MODULE 5: Governed Contextual Embedding (M5_V2)
# GOAL: Convert the Hybrid Knowledge Graph into a Vectorized Semantic Space.
# STRATEGY: Grounded Feature Engineering using BIZBOK Metadata.
# OUTPUT: M5_Gov_Embedded_Graph.gml
# --------------------------------------------------------------------------
import os
import networkx as nx
import numpy as np
import time
from dotenv import load_dotenv
from google import genai

# --- 0. Setup and Configuration ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
EMBEDDING_MODEL = 'text-embedding-004' # Gemini high-performance model [cite: 31]
EMBEDDING_DIM = 768 
RATE_LIMIT_DELAY = 1  # Optimized for text-embedding-004 throughput

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Input: The triangulation-ready hybrid graph [cite: 31]
INPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M4_Gov_Hybrid_Graph.gml')
# Output: The persistent, vectorized graph artifact [cite: 31]
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_Gov_Embedded_Graph.gml')

def get_governed_vector(text: str) -> list:
    """Invokes Gemini Embedding API with structural fallback."""
    if not text.strip():
        return np.zeros(EMBEDDING_DIM).tolist()
    try:
        # Standard Python SDK call for content embedding [cite: 31]
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[text]
        )
        return response.embeddings[0].values
    except Exception as e:
        # PHD RIGOR: Maintain process integrity via zero-vector fallback
        print(f"  [EMBEDDING ERROR] Fallback to zero-vector for: {text[:30]}... Error: {e}")
        return np.zeros(EMBEDDING_DIM).tolist()

if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        exit(f"[CRITICAL ERROR] M4 Graph missing: {INPUT_FILE}")

    G = nx.read_gml(INPUT_FILE)
    print(f"--- Starting M5_V2: Contextual Embedding for {G.number_of_nodes()} Nodes & {G.number_of_edges()} Edges ---")

    # --- 1. Vectorize Nodes (Architectural Concepts) ---
    print("\nVectorizing Concept Nodes...")
    for node_id, data in G.nodes(data=True):
        # FEATURE ENGINEERING: Anchoring vector to the Governed Hierarchy [cite: 29, 34]
        # Includes: Node Type, Industry Domain, Label, and synthesized definition
        feature_string = (
            f"Node Type: {data.get('node_type', 'DocumentConcept')}; "
            f"Domain: {data.get('industry_domain', 'General')}; "
            f"Concept: {node_id}; "
            f"Definition: {data.get('generated_definition', data.get('definition', 'N/A'))}"
        )
        
        vector = get_governed_vector(feature_string)
        G.nodes[node_id]['embedding'] = vector # Saved as a list of floats [cite: 31]
        G.nodes[node_id]['embedding_model'] = EMBEDDING_MODEL
        time.sleep(RATE_LIMIT_DELAY)

    # --- 2. Vectorize Edges (Governed Relationships) ---
    print("\nVectorizing Relationship Edges...")
    for u, v, data in G.edges(data=True):
        # FEATURE ENGINEERING: Capturing relational semantics between source and target 
        feature_string = f"Relationship: {data.get('relationship')}; Source: {u}; Target: {v}"
        
        vector = get_governed_vector(feature_string)
        G.edges[u, v]['embedding'] = vector
        G.edges[u, v]['embedding_model'] = EMBEDDING_MODEL
        time.sleep(RATE_LIMIT_DELAY)

    # --- 3. Final Persistence ---
    # Saving in .gml to preserve structural binding and "Golden Thread" traceability [cite: 31]
    nx.write_gml(G, OUTPUT_FILE)
    print(f"\n[SUCCESS] M5_V2 Complete. Governed Embedded Graph saved: {OUTPUT_FILE}")