# --------------------------------------------------------------------------
# MODULE R4: R4_Embed_Reference_Ontology_V2.py
# ARCHITECTURE: Enterprise Reference Data Caching (DAMA-DMBOK Pattern)
# PURPOSE: Embeds the static Reference Ontology for M-Pipeline AND 
#          calculates the Statistical Baseline for the D2 Gatekeeper.
# --------------------------------------------------------------------------
import os
import networkx as nx
import json
import time
import numpy as np  # <-- Added for D2 Math
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key: print("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)

EMBEDDING_MODEL = 'models/gemini-embedding-001'
EMBEDDING_DIM = 768 # Standardized for both R-Pipeline and D-Pipeline

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# INPUT: The Raw Governance Ontology
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'R_Reference_Ontology.gml')


# OUTPUT 1: The Cached Graph for the M-Pipeline
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'R_Embedded_Reference_Ontology.graphml')
# OUTPUT 2: The Statistical Baseline for the D-Pipeline
OUTPUT_BASELINE = os.path.join(PROJECT_ROOT, 'output', 'R_Statistical_Baseline.json')

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
        return [e.values for e in response.embeddings]
    except Exception as e:
        print(f"   [Error] Batch embedding failed: {e}")
        return [[0.0] * EMBEDDING_DIM for _ in texts]

# --- 2. Main Execution ---
def run_r1_caching():
    print("--- Starting R1: Reference Ontology Caching & Baseline Math ---")
    
    if not os.path.exists(INPUT_GRAPH):
        print(f"[CRITICAL] Missing Input Graph: {INPUT_GRAPH}")
        return

    print("Loading Raw Reference Ontology...")
    try:
        G = nx.read_gml(INPUT_GRAPH)
        if not isinstance(G, nx.MultiDiGraph):
            G = nx.MultiDiGraph(G)
        print(f"-> Loaded {G.number_of_nodes()} Reference Nodes.")
    except Exception as e:
        print(f"[ERROR] Could not parse GML file: {e}")
        return

    # Tracking variables for D2 Statistical Math
    all_vectors = []
    temp_domains = {}
    keyword_mapping = {}

    print("\nVectorizing Reference Concepts in Batches of 100...")
    nodes_list = list(G.nodes(data=True))
    batch_size = 100
    
    for i in range(0, len(nodes_list), batch_size):
        batch = nodes_list[i:i+batch_size]
        
        texts_to_embed = []
        for node, data in batch:
            defn = data.get('definition', 'Standard BIZBOK Concept')
            n_type = data.get('type', 'Reference')
            feature_text = f"Concept: {node} | Definition: {defn} | Governance Status: Reference | Type: {n_type}"
            texts_to_embed.append(feature_text)
            
        print(f" -> Calling API for nodes {i+1} to {min(i+batch_size, len(nodes_list))}...")
        vectors = embed_batch(texts_to_embed)
        
        # Process vectors for BOTH graph saving AND D2 math
        for j, (node, data) in enumerate(batch):
            vec = vectors[j]
            domain = data.get('industry_domain', 'Common')
            label = data.get('label', node)
            
            # 1. Attach to Graph Node (For M-Pipeline)
            G.nodes[node]['embedding'] = json.dumps(vec)
            G.nodes[node]['embedding_model'] = EMBEDDING_MODEL
            
            # 2. Store in trackers (For D-Pipeline)
            keyword_mapping[label.lower()] = domain
            if domain not in temp_domains: temp_domains[domain] = []
            temp_domains[domain].append(vec)
            all_vectors.append(vec)
            
        time.sleep(1.0) 

    # --- 3. Save Output 1: Embedded Graph ---
    print(f"\nSaving Cached Embedded Ontology to {OUTPUT_GRAPH}...")
    nx.write_graphml(G, OUTPUT_GRAPH)
    
    # --- 4. Calculate and Save Output 2: D2 Statistical Baseline ---
    print("Calculating Statistical Baseline for D2 Gatekeeper...")
    global_centroid = np.mean(all_vectors, axis=0)
    distances = [np.linalg.norm(v - global_centroid) for v in all_vectors]
    
    mu = float(np.mean(distances))
    sigma = float(np.std(distances)) if len(distances) > 1 else 0.05

    domain_centroids = {}
    for domain, vecs in temp_domains.items():
        domain_centroids[domain] = np.mean(vecs, axis=0).tolist()

    baseline_data = {
        "mu": mu,
        "sigma": sigma,
        "domain_centroids": domain_centroids,
        "keyword_mapping": keyword_mapping
    }

    with open(OUTPUT_BASELINE, 'w', encoding='utf-8') as f:
        json.dump(baseline_data, f, indent=4)

    print(f"-> Saved Statistical Baseline to {OUTPUT_BASELINE}")
    print(f"-> Architecture Metrics: Mu={mu:.4f}, Sigma={sigma:.4f}")
    
    print("\n" + "="*70)
    print("R4 COMPLETE. Enterprise Graph Cached AND Statistical Anchor Generated.")
    print("="*70)

if __name__ == "__main__":
    run_r1_caching()