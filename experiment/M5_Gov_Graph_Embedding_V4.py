# --------------------------------------------------------------------------
# MODULE 5: M5_Gov_Graph_Embedding_V4.py
# ARCHITECTURE: Poly-Ontological Vectorization (CACHE-AWARE & BATCHED)
# DISSERTATION GOAL: Embeds Governance Metadata & Weights into Vector Space
# --------------------------------------------------------------------------
import os
import networkx as nx
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dotenv import load_dotenv
from google import genai
from google.genai import types

print("--- Starting M5_V4.0: Cache-Aware Graph Vectorization ---")

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
EMBEDDING_MODEL = 'models/gemini-embedding-001' 
EMBEDDING_DIM = 768
RATE_LIMIT_DELAY = 5.0
REQUEST_TIMEOUT_SECONDS = 300
MAX_TRANSPORT_ATTEMPTS = 10

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# INPUT: The Hybrid Graph from M4 (GraphML format)
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.graphml')
# OUTPUT: The Vectorized Graph
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M5_Embedded_Graph.graphml')

# --- 1. Batch Embedding Wrapper ---
def get_embeddings_batch(texts: list):
    """Sends up to 100 texts in a single API call with bounded timeout/retry."""
    if not texts:
        return []

    last_error = None

    for attempt in range(1, MAX_TRANSPORT_ATTEMPTS + 1):
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                client.models.embed_content,
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
            )
            response = future.result(timeout=REQUEST_TIMEOUT_SECONDS)

            if not getattr(response, "embeddings", None):
                raise ValueError("Empty embedding response.")

            return [e.values for e in response.embeddings]

        except FuturesTimeoutError as e:
            last_error = TimeoutError(
                f"Embedding batch timed out after {REQUEST_TIMEOUT_SECONDS}s"
            )

        except Exception as e:
            last_error = e
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = 60
                if attempt == MAX_TRANSPORT_ATTEMPTS:
                    raise RuntimeError(
                        f"M5 embedding failed after {attempt} attempts: {e}"
                    ) from e
                print(
                    f"   [API Throttled] Quota hit. Pausing for {wait_time}s "
                    f"(Retry {attempt}/{MAX_TRANSPORT_ATTEMPTS})..."
                )
                time.sleep(wait_time)
                continue

        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        if attempt == MAX_TRANSPORT_ATTEMPTS:
            raise RuntimeError(
                f"M5 embedding failed after {attempt} attempts: {last_error}"
            ) from last_error

        time.sleep(2)

# --- 2. Main Execution ---
def run_m5_embedding():
    # 1. Load Graph
    if not os.path.exists(INPUT_GRAPH):
        sys.exit(f"[CRITICAL] Input Graph missing: {INPUT_GRAPH}")

    if os.path.exists(OUTPUT_GRAPH):
        os.remove(OUTPUT_GRAPH)

    print("Loading Hybrid Graph (MultiDiGraph)...")
    try:
        # Load as MultiDiGraph to preserve parallel edges
        G = nx.read_graphml(INPUT_GRAPH)
        print(f"-> Loaded {G.number_of_nodes()} Nodes, {G.number_of_edges()} Edges.")
    except Exception as e:
        sys.exit(f"[CRITICAL] Loading failed. Ensure M4 output is valid GraphML. {e}")

    # 2. Embed Nodes (Concepts)
    print("\nVectorizing Nodes (with Governance Metadata)...")
    nodes_to_embed = []
    
    for node, data in G.nodes(data=True):
        # THE GOVERNANCE CACHE CHECK
        if 'embedding' in data: 
            continue # SKIP! This is a pre-embedded Reference Node
            
        defn = data.get('definition', data.get('generated_definition', ''))
        status = data.get('alignment_status', 'Unknown')
        n_type = data.get('type', 'Concept')
        
        feature_text = (
            f"Concept: {node} | "
            f"Definition: {defn} | "
            f"Governance Status: {status} | "
            f"Type: {n_type}"
        )
        nodes_to_embed.append((node, feature_text))

    skipped_count = G.number_of_nodes() - len(nodes_to_embed)
    print(f" -> Found {len(nodes_to_embed)} new nodes to embed (Skipped {skipped_count} cached reference nodes).")
    
    node_count = len(nodes_to_embed)
    batch_size = 100
    for i in range(0, len(nodes_to_embed), batch_size):
        batch = nodes_to_embed[i:i+batch_size]
        texts = [item[1] for item in batch]
        
        vectors = get_embeddings_batch(texts)
        
        for j, (node, _) in enumerate(batch):
            G.nodes[node]['embedding'] = json.dumps(vectors[j])
            G.nodes[node]['embedding_model'] = EMBEDDING_MODEL
            
        print(f"   Processed node batch {i+1} to {min(i+batch_size, len(nodes_to_embed))}...")
        time.sleep(RATE_LIMIT_DELAY)

    # 3. Embed Edges (Relationships)
    print("\nVectorizing Edges (with Epistemic Weights)...")
    edges_to_embed = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        if 'embedding' in data: continue 
        
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
        edges_to_embed.append((u, v, key, feature_text))

    print(f" -> Found {len(edges_to_embed)} new edges to embed.")
    edge_count = len(edges_to_embed)

    for i in range(0, len(edges_to_embed), batch_size):
        batch = edges_to_embed[i:i+batch_size]
        texts = [item[3] for item in batch]
        
        vectors = get_embeddings_batch(texts)
        
        for j, (u, v, key, _) in enumerate(batch):
            G.edges[u, v, key]['embedding'] = json.dumps(vectors[j])
            
        print(f"   Processed edge batch {i+1} to {min(i+batch_size, len(edges_to_embed))}...")
        time.sleep(RATE_LIMIT_DELAY)

    # 4. Persistence
    print(f"\nSaving Vectorized Graph to {OUTPUT_GRAPH}...")
    nx.write_graphml(G, OUTPUT_GRAPH)
    
    print("\n" + "="*50)
    print("M5_V4.0 COMPLETE. Graph Vectorized in record time.")
    print(f"Nodes Embedded: {node_count}")
    print(f"Edges Embedded: {edge_count}")
    print("="*50)

if __name__ == "__main__":
    run_m5_embedding()