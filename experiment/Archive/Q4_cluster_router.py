"""
Q4_cluster_router.py

Purpose:
    Given question signatures from Q3 and the clustered hybrid graph from M6,
    select:
      1) Seed nodes in the graph that best match the question, and
      2) Relevant communities (clusters) to route the query into.

Inputs:
    - output/Q3_signatures.jsonl      (from Q3_Signature_Extractor.py)
    - output/M6_Clustered_Graph.gml   (from document pipeline M4–M6)

Output:
    - output/Q4_cluster_routing.jsonl
"""

import json
import os
from typing import Dict, Any, List, Tuple
from collections import defaultdict

import numpy as np
import networkx as nx
from dotenv import load_dotenv
from google import genai  # Gemini embeddings

# -------------------------------------------------------------------
# 0. Configuration
# -------------------------------------------------------------------

load_dotenv()

Q3_INPUT_FILE = "output/Q3_signatures.jsonl"
GRAPH_PATH = "output/M6_Clustered_Graph.gml"
OUTPUT_FILE = "output/Q4_cluster_routing.jsonl"

# Embedding config – must match what you used in M5
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIM = 768  # standard for text-embedding-004

# Routing / scoring knobs
TOP_K_SEEDS = 10
TOP_K_COMMUNITIES = 3
MIN_HYBRID_SCORE = 0.4

W_LEXICAL = 0.4
W_VECTOR = 0.5
W_DOMAIN = 0.1


# -------------------------------------------------------------------
# 1. Utility: Loading data
# -------------------------------------------------------------------

def load_q3_signatures(path: str) -> List[Dict[str, Any]]:
    """Load all Q3 signature records from a JSONL file."""
    records: List[Dict[str, Any]] = []
    try:
        full_path = os.path.join(os.getcwd(), path)
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        print(f"[Q4][DEBUG] Loaded {len(records)} Q3 records from {path}")
    except FileNotFoundError:
        print(f"[Q4][ERROR] Q3 signatures file not found at {path}")
    except json.JSONDecodeError as e:
        print(f"[Q4][ERROR] JSON parsing error in {path}: {e}")
    return records


def load_hybrid_graph(path: str) -> nx.Graph:
    """Load the M6 clustered graph with embeddings and communities."""
    try:
        full_path = os.path.join(os.getcwd(), path)
        G = nx.read_gml(full_path)
        print(
            f"[Q4][DEBUG] Loaded graph from {path} "
            f"with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
        )
        return G
    except FileNotFoundError:
        print(f"[Q4][ERROR] Graph file not found at {path}")
    except Exception as e:
        print(f"[Q4][ERROR] Failed to load graph: {e}")
    return nx.Graph()


# -------------------------------------------------------------------
# 2. Embeddings (Gemini)
# -------------------------------------------------------------------

_gemini_client = None


def get_gemini_client() -> genai.Client:
    """Lazily initialize the Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set in environment/.env for Q4 embeddings."
            )
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def embed_text(text: str) -> np.ndarray:
    """
    Embed text using the same model as M5 (Gemini text-embedding-004).
    Returns a numpy vector; on failure returns a zero vector.
    """
    text = (text or "").strip()
    if not text:
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)

    try:
        client = get_gemini_client()
        resp = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[text],  # <-- matches M5
        )

        if getattr(resp, "embeddings", None):
            vec = np.array(resp.embeddings[0].values, dtype=np.float32)
        else:
            raise ValueError("No embeddings returned from Gemini API")

        return vec
    except Exception as e:
        print(f"[Q4][WARN] Embedding failed for text '{text[:40]}...': {e}")
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)


def cosine_sim(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors with basic safety checks."""
    if v1 is None or v2 is None:
        return 0.0
    if v1.size == 0 or v2.size == 0:
        return 0.0
    if v1.shape != v2.shape:
        return 0.0
    denom = (np.linalg.norm(v1) * np.linalg.norm(v2)) + 1e-8
    return float(np.dot(v1, v2) / denom)


# -------------------------------------------------------------------
# 3. Scoring functions
# -------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    """Simple whitespace + lowercase tokenization."""
    return [t for t in (text or "").lower().split() if t]


def lexical_overlap_score(q_text: str, node_label: str) -> float:
    """
    Simple lexical similarity:
    - 1.0 for case-insensitive exact match
    - otherwise Jaccard-like token overlap in [0, 1]
    """
    q = (q_text or "").strip()
    n = (node_label or "").strip()
    if not q or not n:
        return 0.0

    if q.lower() == n.lower():
        return 1.0

    q_tokens = set(tokenize(q))
    n_tokens = set(tokenize(n))
    if not q_tokens or not n_tokens:
        return 0.0

    intersection = len(q_tokens & n_tokens)
    union = len(q_tokens | n_tokens)
    return intersection / union if union > 0 else 0.0


def get_node_label(node_id: str, data: Dict[str, Any]) -> str:
    """Best-effort to get a human-readable label for a node."""
    return (
        data.get("label")
        or data.get("name")
        or data.get("title")
        or str(node_id)
    )


def get_node_domain(data: Dict[str, Any]) -> str:
    """
    Extract domain field from node attributes if present.
    Align with M5, which uses 'industry_domain' in its embedding text.
    """
    dom = (
        data.get("domain")
        or data.get("primary_domain")
        or data.get("industry_domain")
    )
    return str(dom) if dom is not None else ""


def get_node_community(data: Dict[str, Any]) -> Any:
    """Extract community/cluster id from node attributes."""
    return (
        data.get("community_id")
        or data.get("cluster_id")
        or data.get("community")
        or None
    )


def get_node_embedding(data: Dict[str, Any]) -> np.ndarray:
    """Extract embedding as numpy array if present; otherwise 0-vector."""
    emb = data.get("embedding")
    if emb and isinstance(emb, (list, tuple)):
        try:
            return np.array(emb, dtype=np.float32)
        except Exception:
            return np.zeros(EMBEDDING_DIM, dtype=np.float32)
    return np.zeros(EMBEDDING_DIM, dtype=np.float32)


# -------------------------------------------------------------------
# 4. Seed selection & community aggregation
# -------------------------------------------------------------------

def select_seed_nodes_for_question(
    G: nx.Graph,
    q_record: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    For a single question, score all nodes and select top-K seeds based on
    hybrid lexical+embedding+domain score.
    """
    q_layer = q_record.get("Q_layer", {}) or {}
    q_concept = q_layer.get("concept") or ""
    q_attribute = q_layer.get("attribute") or ""
    q_domain = (q_record.get("primary_domain") or "").lower()

    # Build primary query string (concept + optional attribute)
    if q_attribute:
        query_text = f"{q_attribute} of {q_concept}".strip()
    else:
        query_text = q_concept

    if not query_text:
        # Fallback: use question text itself
        query_text = q_record.get("question_text") or ""

    q_vec = embed_text(query_text)

    seed_candidates: List[Tuple[str, float, Dict[str, Any]]] = []

    for node_id, data in G.nodes(data=True):
        label = get_node_label(node_id, data)
        node_domain = get_node_domain(data).lower()
        node_emb = get_node_embedding(data)

        # Lexical similarity between query and node label
        lex_score = lexical_overlap_score(query_text, label)

        # Embedding similarity
        vec_sim = cosine_sim(q_vec, node_emb)

        # Domain preference
        domain_flag = 1.0 if q_domain and (q_domain == node_domain) else 0.0

        hybrid_score = (
            W_LEXICAL * lex_score
            + W_VECTOR * vec_sim
            + W_DOMAIN * domain_flag
        )

        if hybrid_score < MIN_HYBRID_SCORE:
            continue

        seed_candidates.append((node_id, hybrid_score, data))

    # Sort by hybrid score descending
    seed_candidates.sort(key=lambda x: x[1], reverse=True)

    # Take top-K seeds
    seeds: List[Dict[str, Any]] = []
    for rank, (node_id, score, data) in enumerate(
        seed_candidates[:TOP_K_SEEDS], start=1
    ):
        label = get_node_label(node_id, data)
        node_type = data.get("node_type", "UNKNOWN")  # <-- FIXED KEY
        community_id = get_node_community(data)

        # Simple match_source heuristic
        lex_score = lexical_overlap_score(query_text, label)
        if lex_score >= 0.95:
            match_source = "lexical_exact"
        elif lex_score > 0.0:
            match_source = "lexical_fuzzy"
        else:
            match_source = "embedding"

        # For now, we treat this as concept-based match
        match_field = "concept"

        seeds.append(
            {
                "node_id": str(node_id),
                "node_label": label,
                "node_type": node_type,
                "community_id": community_id,
                "match_source": match_source,
                "match_field": match_field,
                "similarity": round(float(score), 4),
                "rank": rank,
            }
        )

    return seeds


def aggregate_communities_from_seeds(
    seeds: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Aggregate seed nodes into candidate communities with simple statistics.
    Only seeds that have a non-null community_id (from M6) contribute.
    """
    if not seeds:
        return []

    stats = defaultdict(lambda: {"scores": [], "count": 0})

    for seed in seeds:
        community_id = seed.get("community_id")
        if community_id is None:
            continue
        score = seed.get("similarity", 0.0)
        stats[community_id]["scores"].append(score)
        stats[community_id]["count"] += 1

    communities: List[Dict[str, Any]] = []
    for cid, info in stats.items():
        scores = info["scores"]
        seed_count = info["count"]
        max_sim = max(scores) if scores else 0.0
        avg_sim = sum(scores) / len(scores) if scores else 0.0

        # Simple community weight: count * max_similarity
        community_weight = seed_count * max_sim

        communities.append(
            {
                "community_id": cid,
                "seed_count": seed_count,
                "max_similarity": round(float(max_sim), 4),
                "avg_similarity": round(float(avg_sim), 4),
                "community_weight": round(float(community_weight), 4),
            }
        )

    # Sort by weight desc and keep top-K
    communities.sort(
        key=lambda c: (c["community_weight"], c["max_similarity"]), reverse=True
    )
    return communities[:TOP_K_COMMUNITIES]


# -------------------------------------------------------------------
# 5. Main driver
# -------------------------------------------------------------------

def run_q4(
    q3_path: str = Q3_INPUT_FILE,
    graph_path: str = GRAPH_PATH,
    out_path: str = OUTPUT_FILE,
) -> None:
    print("[Q4] Starting Q4 Cluster & Seed Router...")

    q3_records = load_q3_signatures(q3_path)
    if not q3_records:
        print("[Q4][ERROR] No Q3 records found. Aborting Q4.")
        return

    G = load_hybrid_graph(graph_path)
    if G.number_of_nodes() == 0:
        print("[Q4][ERROR] Graph is empty or failed to load. Aborting Q4.")
        return

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)

    count = 0
    with open(out_path, "w", encoding="utf-8") as outfile:
        for rec in q3_records:
            qid = rec.get("id", rec.get("question_id", f"Q{count+1}"))

            seeds = select_seed_nodes_for_question(G, rec)
            communities = aggregate_communities_from_seeds(seeds)

            out_rec = rec.copy()
            out_rec["seed_nodes"] = seeds
            out_rec["candidate_communities"] = communities

            if not seeds:
                out_rec["q4_notes"] = (
                    "No seeds above threshold; downstream should fallback to "
                    "broader retrieval."
                )
            else:
                out_rec["q4_notes"] = (
                    "Seeds and communities selected via hybrid lexical+embedding routing."
                )

            outfile.write(json.dumps(out_rec) + "\n")
            count += 1

            if count % 10 == 0:
                print(f"[Q4][INFO] Processed {count} questions...")

    print(f"[Q4] Completed. Wrote {count} records to: {out_path}")


if __name__ == "__main__":
    run_q4()