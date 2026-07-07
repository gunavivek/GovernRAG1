#!/usr/bin/env python3
"""
build_scoped_vocab.py  --  Option-B enabler (read-only on the graph; writes one JSON).

Produces the per-question, design-A SCOPED node vocabulary that Q2 uses for
graph-grounded anchor linking:

    output/serve_scoped_vocab.json  =  { record_id : [node_name, ...] }

where node_name ranges over the endpoints of the edges that belong to THAT
question's own chunks (same scoping Q3 already uses). Q2 then adds any of these
names that the question actually mentions to `target_nodes`. Q3's existing
_resolve_anchors restricts anchors to the scoped subgraph, so nothing out of
governance scope can leak in.

ABLATION: don't run this (or delete the output) -> Q2 falls back to the frozen
capitalization heuristic, byte-for-byte.

RUN (after B2 has staged serve_chunk_filter.json), from repo root:
    python build_scoped_vocab.py
"""
import json, os, sys
from collections import defaultdict

OUT = "output"
GRAPH = os.path.join(OUT, "M5_Embedded_Graph.graphml")
FILTER = os.path.join(OUT, "serve_chunk_filter.json")
VOCAB = os.path.join(OUT, "serve_scoped_vocab.json")


def edge_cid(data, key):
    for a in ("chunk_id", "source_chunk_id"):
        if data.get(a):
            return str(data[a])
    parts = str(data.get("forensic_key") or key or "").split("_")
    return parts[-2] if len(parts) >= 2 else ""


def main():
    if not os.path.exists(FILTER):
        sys.exit("[FATAL] %s missing -- run B2 staging first (writes serve_chunk_filter.json)." % FILTER)
    if not os.path.exists(GRAPH):
        sys.exit("[FATAL] %s missing." % GRAPH)

    cf = json.load(open(FILTER, encoding="utf-8"))            # {record_id: [chunk_id, ...]}
    import networkx as nx
    g = nx.read_graphml(GRAPH)

    # one pass over edges: chunk_id -> set(endpoint node names)
    chunk_nodes = defaultdict(set)
    for u, v, k, d in g.edges(keys=True, data=True):
        cid = edge_cid(d, k)
        if cid:
            chunk_nodes[cid].add(str(u))
            chunk_nodes[cid].add(str(v))

    vocab, sizes = {}, []
    for rid, cids in cf.items():
        names = set()
        for c in cids:
            names |= chunk_nodes.get(str(c), set())
        vocab[rid] = sorted(names)
        sizes.append(len(names))

    json.dump(vocab, open(VOCAB, "w", encoding="utf-8"), ensure_ascii=False)
    avg = sum(sizes) / max(len(sizes), 1)
    print("[OK] wrote %s : %d questions, avg %.1f scoped node names/question (min %d, max %d)"
          % (VOCAB, len(vocab), avg, min(sizes or [0]), max(sizes or [0])))


if __name__ == "__main__":
    main()
