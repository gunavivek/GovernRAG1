# --------------------------------------------------------------------------
# MODULE R1: R1_Embed_Reference_Ontology.py
# ARCHITECTURE: Enterprise Reference Data Caching (DAMA-DMBOK Pattern)
# PURPOSE: Embeds the static Reference Ontology once to optimize the M-Pipeline
# --------------------------------------------------------------------------
import os
import networkx as nx
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key: print("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)

EMBEDDING_MODEL = 'models/gemini-embedding-001'
# NOTE: Set this to 768 or 3072 depending on your architectural choice for M5
EMBEDDING_DIM = 768 

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# INPUT: The Raw Governance Ontology
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'R_Reference_Ontology_Governance.gml')
# OUTPUT: The Cached/Embedded Ontology (Saved as GraphML for downstream compatibility)
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'R_Embedded_Reference_Ontology.graphml')

# --- 1. Batch Embedding Function ---
def embed_batch(texts: list):
    """Sends up to 100 texts in a single API call to bypass massive loop delays."""
    if not texts: return []
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
        )
        # Extract the vector arrays from the response
        return [e.values for e in response.embeddings]
    except Exception as e:
        print(f"   [Error] Batch embedding failed: {e}")
        return [[0.0] * EMBEDDING_DIM for _ in texts]

# --- 2. Main Execution ---
def run_r1_caching():
    print("--- Starting R1: Reference Ontology Caching ---")
    
    if not os.path.exists(INPUT_GRAPH):
        print(f"[CRITICAL] Missing Input Graph: {INPUT_GRAPH}")
        return

    # 1. Load the Raw Reference Graph
    print("Loading Raw Reference Ontology...")
    try:
        G = nx.read_gml(INPUT_GRAPH)
        # Ensure it is a MultiDiGraph to match the M-Pipeline topology
        if not isinstance(G, nx.MultiDiGraph):
            G = nx.MultiDiGraph(G)
        print(f"-> Loaded {G.number_of_nodes()} Reference Nodes.")
    except Exception as e:
        print(f"[ERROR] Could not parse GML file: {e}")
        return

    # 2. Batch Processing Loop
    print("\nVectorizing Reference Concepts in Batches of 100...")
    nodes_list = list(G.nodes(data=True))
    batch_size = 100
    
    for i in range(0, len(nodes_list), batch_size):
        batch = nodes_list[i:i+batch_size]
        
        # Prepare the semantic strings for the batch
        texts_to_embed = []
        for node, data in batch:
            defn = data.get('definition', 'Standard BIZBOK Concept')
            n_type = data.get('type', 'Reference')
            
            # This string format must match how M5 embeds its nodes!
            feature_text = f"Concept: {node} | Definition: {defn} | Governance Status: Reference | Type: {n_type}"
            texts_to_embed.append(feature_text)
            
        print(f" -> Calling API for nodes {i+1} to {min(i+batch_size, len(nodes_list))}...")
        
        # Execute the single batch API call
        vectors = embed_batch(texts_to_embed)
        
        # Suture the vectors back onto the graph nodes
        for j, (node, data) in enumerate(batch):
            G.nodes[node]['embedding'] = json.dumps(vectors[j])
            G.nodes[node]['embedding_model'] = EMBEDDING_MODEL
            
        # Respect API rate limits between batches
        time.sleep(1.0) 

    # 3. Persistence
    print(f"\nSaving Cached Embedded Ontology to {OUTPUT_GRAPH}...")
    nx.write_graphml(G, OUTPUT_GRAPH)
    
    print("\n" + "="*60)
    print("R1 COMPLETE. Enterprise Ontology Cached Successfully.")
    print("="*60)

if __name__ == "__main__":
    run_r1_caching()