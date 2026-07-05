# --------------------------------------------------------------------------
# MODULE 5 (HARDENED): transient-aware retry/backoff (503 + 429 + timeout),
# UTF-8-safe prints, and incremental checkpoint/resume so a crash mid-embedding
# continues instead of restarting. Embedding logic + feature text are UNCHANGED
# (output-neutral). Drop-in replacement for M5_Gov_Graph_Embedding_V4.py
# --------------------------------------------------------------------------
import os
import networkx as nx
import json
import time
import sys
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dotenv import load_dotenv
from google import genai
from google.genai import types

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

print("--- Starting M5_V4.0 (HARDENED): Cache-Aware Graph Vectorization ---")

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
CHECKPOINT_EVERY_BATCHES = 10   # save the graph every N embedding batches

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.graphml')
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M5_Embedded_Graph.graphml')

TRANSIENT = ("503", "unavailable", "429", "resource_exhausted", "500",
             "internal", "deadline", "timeout", "high demand")

def _is_transient(e):
    return any(t in str(e).lower() for t in TRANSIENT)


def get_embeddings_batch(texts: list):
    """Embed up to 100 texts per call; retry transient errors with backoff."""
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
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
            )
            response = future.result(timeout=REQUEST_TIMEOUT_SECONDS)
            if not getattr(response, "embeddings", None):
                raise ValueError("Empty embedding response.")
            return [e.values for e in response.embeddings]
        except Exception as e:
            last_error = e
            if attempt >= MAX_TRANSPORT_ATTEMPTS:
                raise RuntimeError(f"M5 embedding failed after {attempt} attempts: {e}") from e
            wait = min(90, 2 ** attempt) + random.uniform(0, 2) if _is_transient(e) else 2
            print(f"   [retry {attempt}/{MAX_TRANSPORT_ATTEMPTS}] embedding batch: "
                  f"{str(e)[:60]}... waiting {wait:.0f}s")
            time.sleep(wait)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)


def run_m5_embedding():
    if not os.path.exists(INPUT_GRAPH):
        sys.exit(f"[CRITICAL] Input Graph missing: {INPUT_GRAPH}")

    # RESUME: if a partial embedded graph exists, continue from it (the cache
    # check below then skips whatever is already embedded).
    if os.path.exists(OUTPUT_GRAPH):
        print(f"-> Resuming from partial {OUTPUT_GRAPH}")
        G = nx.read_graphml(OUTPUT_GRAPH)
    else:
        print("Loading Hybrid Graph (fresh)...")
        G = nx.read_graphml(INPUT_GRAPH)
    print(f"-> Loaded {G.number_of_nodes()} Nodes, {G.number_of_edges()} Edges.")

    batch_size = 100

    # 2. Embed Nodes
    print("\nVectorizing Nodes...")
    nodes_to_embed = []
    for node, data in G.nodes(data=True):
        if 'embedding' in data:
            continue
        feature_text = (f"Concept: {node} | Definition: {data.get('definition', data.get('generated_definition',''))} | "
                        f"Governance Status: {data.get('alignment_status','Unknown')} | Type: {data.get('type','Concept')}")
        nodes_to_embed.append((node, feature_text))
    print(f" -> {len(nodes_to_embed)} nodes to embed (skipped {G.number_of_nodes()-len(nodes_to_embed)} cached).")

    for bi, i in enumerate(range(0, len(nodes_to_embed), batch_size)):
        batch = nodes_to_embed[i:i + batch_size]
        vectors = get_embeddings_batch([t for _, t in batch])
        for j, (node, _) in enumerate(batch):
            G.nodes[node]['embedding'] = json.dumps(vectors[j])
            G.nodes[node]['embedding_model'] = EMBEDDING_MODEL
        print(f"   node batch {i+1}-{min(i+batch_size, len(nodes_to_embed))} done")
        if (bi + 1) % CHECKPOINT_EVERY_BATCHES == 0:
            nx.write_graphml(G, OUTPUT_GRAPH); print("      [checkpoint] nodes saved")
        time.sleep(RATE_LIMIT_DELAY)

    nx.write_graphml(G, OUTPUT_GRAPH)  # checkpoint before edges

    # 3. Embed Edges
    print("\nVectorizing Edges...")
    edges_to_embed = []
    for u, v, key, data in G.edges(keys=True, data=True):
        if 'embedding' in data:
            continue
        feature_text = (f"Source: {u} | Relationship: {data.get('predicate','related_to')} | Target: {v} | "
                        f"Domain Context: {data.get('domain','General')} | Authority Weight: {data.get('weight',0.1)} | "
                        f"Extraction Mode: {data.get('provenance','STRICT')}")
        edges_to_embed.append((u, v, key, feature_text))
    print(f" -> {len(edges_to_embed)} edges to embed.")

    for bi, i in enumerate(range(0, len(edges_to_embed), batch_size)):
        batch = edges_to_embed[i:i + batch_size]
        vectors = get_embeddings_batch([t for *_, t in batch])
        for j, (u, v, key, _) in enumerate(batch):
            G.edges[u, v, key]['embedding'] = json.dumps(vectors[j])
        print(f"   edge batch {i+1}-{min(i+batch_size, len(edges_to_embed))} done")
        if (bi + 1) % CHECKPOINT_EVERY_BATCHES == 0:
            nx.write_graphml(G, OUTPUT_GRAPH); print("      [checkpoint] edges saved")
        time.sleep(RATE_LIMIT_DELAY)

    nx.write_graphml(G, OUTPUT_GRAPH)
    print("\n" + "=" * 50)
    print("M5_V4.0 COMPLETE. Graph Vectorized.")
    print(f"Output: {OUTPUT_GRAPH}")
    print("=" * 50)


if __name__ == "__main__":
    run_m5_embedding()
