#!/usr/bin/env python3
"""
diagnose_refusals.py -- why does governed RAG refuse 19/20? (read-only; writes nothing)

Answers, with evidence, whether the 95% refusal is a serve-harness artifact
(under-authorized predicate universe) or a true property of GovernRAG.

Prints:
  [1] Authorized-predicate universe attached to the 20 served questions
      (from output/D5_Extraction_Manifest.jsonl governance_profile).
  [2] Predicate vocabulary the M5 GRAPH actually uses (edge 'predicate' attr, top 25).
  [3] OVERLAP: how many authorized predicates exist in the graph at all.  <-- smoking gun
  [4] Corpus manifest (index/delucionqa/D5_Extraction_Manifest.jsonl): row count +
      union of relational_predicates (what the build authorized).
  [5] Per failed question: Q2 mapped predicates, and of the edges IN its chunk scope,
      how many carry an authorized predicate.

RUN from repo root:  python diagnose_refusals.py
"""
import json, os, sys
from collections import Counter

OUT = "output"
INDEX = os.path.join("index", "delucionqa")


def load_jsonl(p):
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    return rows


def preds_from_profile(profile):
    if not isinstance(profile, dict):
        return []
    laws = profile.get("primary_laws", {}) if isinstance(profile.get("primary_laws"), dict) else {}
    return list(laws.get("relational_predicates", []) or profile.get("relational_predicates", []) or [])


def main():
    # [1] authorized universe attached at serve time
    staged = load_jsonl(os.path.join(OUT, "D5_Extraction_Manifest.jsonl"))
    auth = set()
    for r in staged:
        auth.update(preds_from_profile(r.get("governance_profile", {})))
    print("=" * 70)
    print("[1] AUTHORIZED PREDICATES attached to the served questions: %d" % len(auth))
    print("    ", sorted(auth)[:40])

    # [2] graph predicate vocabulary
    print("=" * 70)
    graph_preds = Counter()
    try:
        import networkx as nx
        g = nx.read_graphml(os.path.join(OUT, "M5_Embedded_Graph.graphml"))
        for _u, _v, d in g.edges(data=True):
            p = d.get("predicate")
            if p:
                graph_preds[str(p)] += 1
        print("[2] GRAPH predicate vocabulary: %d distinct over %d edges. Top 25:" %
              (len(graph_preds), sum(graph_preds.values())))
        for p, c in graph_preds.most_common(25):
            print("      %6d  %s" % (c, p))
    except Exception as e:
        print("[2] could not read graph: %s" % e)

    # [3] SMOKING GUN: overlap
    print("=" * 70)
    gset = set(graph_preds)
    inter = auth & gset
    print("[3] OVERLAP authorized ∩ graph = %d / %d authorized" % (len(inter), len(auth)))
    print("    present in graph :", sorted(inter))
    print("    authorized but ABSENT from graph:", sorted(auth - gset))
    if auth and not inter:
        print("    >>> VERDICT: zero overlap -> EVERY triple is unauthorized -> guaranteed refusal (harness artifact).")
    elif auth:
        covered = sum(graph_preds[p] for p in inter)
        print("    >>> authorized predicates cover %d/%d edges (%.1f%%) of the graph." %
              (covered, sum(graph_preds.values()), 100 * covered / max(sum(graph_preds.values()), 1)))

    # [4] corpus manifest the BUILD authorized
    print("=" * 70)
    corpus = load_jsonl(os.path.join(INDEX, "D5_Extraction_Manifest.jsonl"))
    cu = set()
    for r in corpus:
        cu.update(preds_from_profile(r.get("governance_profile", {})))
    print("[4] BUILD corpus manifest: %d rows; union of authorized predicates = %d" % (len(corpus), len(cu)))
    print("    ", sorted(cu)[:40])
    print("    corpus-union ∩ graph = %d (vs served-set ∩ graph = %d)" % (len(cu & gset), len(inter)))

    # [5] per-failed-question scope check
    print("=" * 70)
    cf = {}
    p = os.path.join(OUT, "serve_chunk_filter.json")
    if os.path.exists(p):
        cf = json.load(open(p, encoding="utf-8"))
    sigs = {str(r.get("record_id")): r for r in load_jsonl(os.path.join(OUT, "Q2_signatures.jsonl"))}

    def edge_cid(d, k):
        for a in ("chunk_id", "source_chunk_id"):
            if d.get(a):
                return str(d[a])
        parts = str(d.get("forensic_key") or k or "").split("_")
        return parts[-2] if len(parts) >= 2 else ""

    print("[5] per-question scope (first 5 served):")
    try:
        import networkx as nx
        for qid in list(cf)[:5]:
            wanted = set(map(str, cf.get(qid, [])))
            in_scope = auth_in_scope = 0
            for u, v, k, d in g.edges(keys=True, data=True):
                if edge_cid(d, k) in wanted:
                    in_scope += 1
                    if str(d.get("predicate")) in auth:
                        auth_in_scope += 1
            sig = sigs.get(qid, {})
            mp = sig.get("mapped_predicates") or sig.get("relational_predicates") or "?"
            print("    %s | chunks=%d edges_in_scope=%d authorized_edges_in_scope=%d | Q2_preds=%s"
                  % (qid, len(wanted), in_scope, auth_in_scope, mp))
    except Exception as e:
        print("    scope check skipped: %s" % e)

    print("=" * 70)
    print("READ: if [3] overlap is ~0 or authorized-set is tiny vs [4] corpus union,")
    print("      the fix is staging the RIGHT governance profile per question, not the")
    print("      governance logic. If [5] authorized_edges_in_scope=0 everywhere, same conclusion.")


if __name__ == "__main__":
    main()
