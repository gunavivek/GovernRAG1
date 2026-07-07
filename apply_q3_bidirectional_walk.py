#!/usr/bin/env python3
"""
apply_q3_bidirectional_walk.py -- GENERIC correctness fix to Q3._perform_governed_walk.

The frozen walk follows out_edges only, so it discovers a governed triple ONLY when the query
entity is its SUBJECT. But a relation like (diesel_engine, requires, fuel_system) is exactly what
a question about "fuel system" needs -- and it is invisible to an out-only walk because the entity
is the OBJECT. This patch traverses IN + OUT edges for directed graphs while preserving each
triple's true subject->object orientation (provenance-safe). Predicate pruning, k_hops, anchors,
and the undirected-graph branch are unchanged. No dataset-specific logic. Idempotent. Backup .bakW.

RUN from repo root:  python apply_q3_bidirectional_walk.py
"""
import os, shutil, sys

Q3 = os.path.join("experiment", "Q3_Gov_Graph_Retrieval_Engine_V3.py")

ANCHOR = (
    "                # Support both directed and undirected traversal for robustness\n"
    "                edges = local_graph.out_edges(u, data=True) if local_graph.is_directed() else local_graph.edges(u, data=True)\n"
    "                for _, v, data in edges:\n"
    "                    p_label = data.get('predicate', 'related_to')\n"
    "                    # PhD Logic: Predicate Pruning\n"
    "                    if not predicates or any(p.lower() in p_label.lower() for p in predicates):\n"
    "                        discovered_triples.add((u, p_label, v))\n"
    "                        if v not in visited_nodes:\n"
    "                            next_layer.add(v)\n"
)
NEW = (
    "                # Bidirectional traversal (generic): a query entity may be the SUBJECT or the\n"
    "                # OBJECT of a governed relation; follow in+out edges, preserving true s->o direction.\n"
    "                if local_graph.is_directed():\n"
    "                    cand = [(u, v, data) for _, v, data in local_graph.out_edges(u, data=True)]\n"
    "                    cand += [(w, u, data) for w, _, data in local_graph.in_edges(u, data=True)]\n"
    "                else:\n"
    "                    cand = [(u, v, data) for _, v, data in local_graph.edges(u, data=True)]\n"
    "                for s_node, o_node, data in cand:\n"
    "                    p_label = data.get('predicate', 'related_to')\n"
    "                    # PhD Logic: Predicate Pruning (direction-agnostic reachability)\n"
    "                    if not predicates or any(p.lower() in p_label.lower() for p in predicates):\n"
    "                        discovered_triples.add((s_node, p_label, o_node))\n"
    "                        neighbor = o_node if s_node == u else s_node\n"
    "                        if neighbor not in visited_nodes:\n"
    "                            next_layer.add(neighbor)\n"
)

def main():
    if not os.path.exists(Q3):
        sys.exit("[FATAL] %s not found -- run from the repo root." % Q3)
    src = open(Q3, encoding="utf-8").read()
    if "Bidirectional traversal (generic)" in src or "in_edges(u, data=True)" in src:
        print("Already bidirectional-walk patched -- nothing to do."); return
    if src.count(ANCHOR) != 1:
        sys.exit("[FATAL] Q3 walk anchor matched %d times (need 1). Not written (is the live walk modified?)." % src.count(ANCHOR))
    src = src.replace(ANCHOR, NEW, 1)
    shutil.copy2(Q3, Q3 + ".bakW")
    with open(Q3, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("[OK] Q3 walk is now bidirectional (in+out, direction-preserving). Backup: %s.bakW" % Q3)

if __name__ == "__main__":
    main()
