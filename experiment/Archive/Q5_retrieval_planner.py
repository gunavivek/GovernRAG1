# --------------------------------------------------------------------------
# Q5: Retrieval Planner
# Purpose:
#   Given Q4 cluster routing output and the clustered hybrid graph (M6),
#   build a small, ranked set of retrieval contexts (chunks + graph evidence)
#   for each question.
#
# Inputs:
#   - output/Q4_cluster_routing.jsonl  (from Q4_cluster_router.py)
#   - output/M6_Clustered_Graph.gml    (from M6 clustering)
#
# Output:
#   - output/Q5_retrieval_plan.jsonl
# --------------------------------------------------------------------------

import json
import os
from typing import Dict, Any, List, Optional, Set

import networkx as nx

# --- 0. Paths & basic config ------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

Q4_INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "Q4_cluster_routing.jsonl")
GRAPH_PATH = os.path.join(PROJECT_ROOT, "output", "M6_Clustered_Graph.gml")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "Q5_retrieval_plan.jsonl")

# How many communities / contexts we keep per question
MAX_COMMUNITIES = 3
MAX_CONTEXTS = 3
MAX_EDGE_SUMMARIES = 15


# --- 1. Utility: load JSONL & graph ----------------------------------------


def load_q4_records(path: str) -> List[Dict[str, Any]]:
    """Load Q4 cluster routing records from JSONL."""
    records: List[Dict[str, Any]] = []
    full_path = os.path.join(os.getcwd(), path) if not os.path.isabs(path) else path

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        print(f"[Q5][DEBUG] Loaded {len(records)} Q4 records from {full_path}")
    except FileNotFoundError:
        print(f"[Q5][ERROR] Q4 routing file not found at {full_path}")
    except json.JSONDecodeError as e:
        print(f"[Q5][ERROR] JSON parsing error in {full_path}: {e}")

    return records


def load_clustered_graph(path: str) -> nx.Graph:
    """Load M6 clustered graph."""
    full_path = os.path.join(os.getcwd(), path) if not os.path.isabs(path) else path
    try:
        G = nx.read_gml(full_path)
        print(
            f"[Q5][DEBUG] Loaded graph from {full_path} "
            f"with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
        )
        return G
    except FileNotFoundError:
        print(f"[Q5][ERROR] Graph file not found at {full_path}")
    except Exception as e:
        print(f"[Q5][ERROR] Failed to load graph: {e}")
    return nx.Graph()


# --- 2. Helpers to inspect node properties ---------------------------------


def get_node_type(data: Dict[str, Any]) -> str:
    """Return normalized node_type."""
    nt = data.get("node_type") or data.get("type") or ""
    return str(nt)


def get_node_community(data: Dict[str, Any]) -> Optional[str]:
    """Return community/cluster id if present."""
    cid = (
        data.get("community_id")
        or data.get("cluster_id")
        or data.get("community")
        or None
    )
    return str(cid) if cid is not None else None


def get_source_chunk_id(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract a chunk identifier from node attributes.
    If not present, returns None (we'll fall back to a single-chunk mode).
    """
    cid = data.get("source_chunk_id") or data.get("chunk_id")
    return str(cid) if cid is not None else None


def summarize_edge(u: str, v: str, data: Dict[str, Any]) -> str:
    """Produce a human-readable mini-summary of an edge."""
    rel = data.get("relationship") or data.get("type") or "RELATED_TO"
    reason = data.get("mapping_justification") or data.get("mapping_reason") or ""
    if reason:
        return f"{u} {rel} {v} (reason: {reason})"
    return f"{u} {rel} {v}"


# --- 3. Core: build retrieval contexts for one question --------------------


def select_top_communities(q_record: Dict[str, Any]) -> List[str]:
    """
    Pick the top communities from Q4 candidate_communities,
    or derive them from seed_nodes if needed.
    """
    communities_cfg: List[Dict[str, Any]] = q_record.get("candidate_communities") or []
    if communities_cfg:
        # Sort by community_weight descending, then max_similarity
        communities_cfg.sort(
            key=lambda c: (c.get("community_weight", 0.0), c.get("max_similarity", 0.0)),
            reverse=True,
        )
        return [
            c.get("community_id")
            for c in communities_cfg[:MAX_COMMUNITIES]
            if c.get("community_id")
        ]

    # Fallback: derive from seeds
    seeds: List[Dict[str, Any]] = q_record.get("seed_nodes") or []
    seen: List[str] = []
    for s in seeds:
        cid = s.get("community_id")
        if cid and cid not in seen:
            seen.append(cid)
        if len(seen) >= MAX_COMMUNITIES:
            break
    return seen


def build_working_node_set(
    G: nx.Graph, community_ids: List[str]
) -> List[str]:
    """Return list of node_ids that belong to any of the selected communities."""
    if not community_ids:
        return []

    selected_nodes: List[str] = []
    for node_id, data in G.nodes(data=True):
        cid = get_node_community(data)
        if cid in community_ids:
            selected_nodes.append(node_id)

    return selected_nodes


def group_nodes_by_chunk(
    G: nx.Graph, node_ids: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Group nodes into pseudo-chunks.
    If no explicit chunk id is available, we collapse everything
    into a single logical chunk 'chunk_0'.
    Returns:
      {chunk_id: { 'concept_nodes': set(), 'reference_nodes': set(), 'edge_summaries': [] }}
    """
    groups: Dict[str, Dict[str, Any]] = {}

    # First pass: assign nodes to chunks
    for node_id in node_ids:
        data = G.nodes[node_id]
        node_type = get_node_type(data)
        chunk_id = get_source_chunk_id(data) or "chunk_0"

        if chunk_id not in groups:
            groups[chunk_id] = {
                "concept_nodes": set(),  # DocumentConcept / AdaptiveConcept
                "reference_nodes": set(),  # Reference concepts or ontology
                "edge_summaries": [],
            }

        if node_type in ("DocumentConcept", "AdaptiveConcept"):
            groups[chunk_id]["concept_nodes"].add(node_id)
        else:
            # Heuristic: treat others as reference/ontology nodes
            groups[chunk_id]["reference_nodes"].add(node_id)

    # Second pass: capture edge summaries between groups' nodes
    for chunk_id, bucket in groups.items():
        local_nodes: Set[str] = bucket["concept_nodes"] | bucket["reference_nodes"]
        summaries: List[str] = []

        for u, v, edata in G.edges(data=True):
            if u in local_nodes and v in local_nodes:
                summaries.append(summarize_edge(str(u), str(v), edata))
                if len(summaries) >= MAX_EDGE_SUMMARIES:
                    break

        bucket["edge_summaries"] = summaries

    return groups


def score_chunk(
    chunk_id: str,
    chunk_data: Dict[str, Any],
    q_record: Dict[str, Any],
) -> float:
    """
    Assign a simple score to a chunk.
    For this prototype:
      - Score = max seed similarity for any node in this chunk (if known).
    """
    seeds: List[Dict[str, Any]] = q_record.get("seed_nodes") or []
    if not seeds:
        return 0.0

    concept_nodes: Set[str] = chunk_data["concept_nodes"]
    if not concept_nodes:
        return 0.0

    max_sim = 0.0
    for s in seeds:
        node_id = s.get("node_id")
        sim = float(s.get("similarity", 0.0))
        if node_id in concept_nodes and sim > max_sim:
            max_sim = sim

    return max_sim


def build_retrieval_contexts_for_question(
    G: nx.Graph,
    q_record: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Main function: for a given question record, build up to MAX_CONTEXTS
    retrieval contexts (chunk + graph evidence).
    """
    # 1) Pick focus communities
    community_ids = select_top_communities(q_record)
    if not community_ids:
        # No communities/seeds: fall back to a single context that just wraps the document text
        print(
            f"[Q5][WARN] No communities or seeds for id={q_record.get('id')}. "
            "Falling back to single full-document context."
        )
        ctx = {
            "context_id": "ctx_fallback",
            "community_ids": [],
            "chunk_id": "chunk_0",
            "document_id": q_record.get("dataset_name") or "doc_0",
            "score": 0.0,
            "concept_nodes": [],
            "reference_nodes": [],
            "edge_summaries": [],
            "chunk_text": q_record.get("documents") or "",
        }
        return [ctx]

    # 2) Build working node set from graph
    working_nodes = build_working_node_set(G, community_ids)
    if not working_nodes:
        print(
            f"[Q5][WARN] No graph nodes found for communities {community_ids}. "
            "Falling back to single full-document context."
        )
        ctx = {
            "context_id": "ctx_fallback",
            "community_ids": community_ids,
            "chunk_id": "chunk_0",
            "document_id": q_record.get("dataset_name") or "doc_0",
            "score": 0.0,
            "concept_nodes": [],
            "reference_nodes": [],
            "edge_summaries": [],
            "chunk_text": q_record.get("documents") or "",
        }
        return [ctx]

    # 3) Group nodes into pseudo-chunks
    chunk_groups = group_nodes_by_chunk(G, working_nodes)

    # 4) Score chunks
    scored_chunks: List[Dict[str, Any]] = []
    for chunk_id, bucket in chunk_groups.items():
        score = score_chunk(chunk_id, bucket, q_record)
        scored_chunks.append(
            {
                "chunk_id": chunk_id,
                "score": score,
                "concept_nodes": sorted(bucket["concept_nodes"]),
                "reference_nodes": sorted(bucket["reference_nodes"]),
                "edge_summaries": bucket["edge_summaries"],
            }
        )

    # 5) Sort and take top-K
    scored_chunks.sort(key=lambda c: c["score"], reverse=True)
    top_chunks = scored_chunks[:MAX_CONTEXTS] if scored_chunks else []

    # 6) Build final retrieval_contexts payload
    retrieval_contexts: List[Dict[str, Any]] = []
    doc_id = q_record.get("dataset_name") or "doc_0"
    full_text = q_record.get("documents") or ""

    for idx, ch in enumerate(top_chunks):
        ctx = {
            "context_id": f"ctx_{idx+1}",
            "community_ids": community_ids,
            "chunk_id": ch["chunk_id"],
            "document_id": doc_id,
            "score": ch["score"],
            "concept_nodes": ch["concept_nodes"],
            "reference_nodes": ch["reference_nodes"],
            "edge_summaries": ch["edge_summaries"],
            # For now, prototype uses full document text as chunk_text
            # because we have not yet externalized fine-grained chunking.
            "chunk_text": full_text,
        }
        retrieval_contexts.append(ctx)

    # If something went wrong and we ended with no contexts, fallback
    if not retrieval_contexts:
        retrieval_contexts.append(
            {
                "context_id": "ctx_fallback",
                "community_ids": community_ids,
                "chunk_id": "chunk_0",
                "document_id": doc_id,
                "score": 0.0,
                "concept_nodes": [],
                "reference_nodes": [],
                "edge_summaries": [],
                "chunk_text": full_text,
            }
        )

    return retrieval_contexts


# --- 4. Main driver --------------------------------------------------------


def run_q5(
    q4_path: str = Q4_INPUT_FILE,
    graph_path: str = GRAPH_PATH,
    out_path: str = OUTPUT_FILE,
) -> None:
    """Main driver for Q5 Retrieval Planner."""
    print("[Q5] Starting Q5 Retrieval Planner...")

    q4_records = load_q4_records(q4_path)
    if not q4_records:
        print("[Q5][ERROR] No Q4 records found. Aborting Q5.")
        return

    G = load_clustered_graph(graph_path)
    if G.number_of_nodes() == 0:
        print("[Q5][ERROR] Graph is empty or failed to load. Aborting Q5.")
        return

    out_dir = os.path.dirname(out_path)
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)

    count = 0
    with open(out_path, "w", encoding="utf-8") as outfile:
        for rec in q4_records:
            qid = rec.get("id", rec.get("question_id", f"Q{count+1}"))

            retrieval_contexts = build_retrieval_contexts_for_question(G, rec)

            out_rec = rec.copy()
            out_rec["retrieval_contexts"] = retrieval_contexts
            out_rec["q5_notes"] = (
                "Contexts selected from graph communities using seed-aligned chunks."
            )

            outfile.write(json.dumps(out_rec) + "\n")
            count += 1

            if count % 10 == 0:
                print(f"[Q5][INFO] Processed {count} questions...")

    print(f"[Q5] Completed. Wrote {count} records to: {out_path}")


if __name__ == "__main__":
    run_q5()