#!/usr/bin/env python3
"""
diagnose_anchors.py -- why does Q3 find 0 anchors? (read-only; writes nothing)

v1 mis-read governance_profile (it's a LIST of domain views, per M1). This version
reads it correctly and, more importantly, tests the REAL suspect from the Q3 log:
anchor resolution. It introspects the Q1/Q2/Q3 outputs (so we learn the exact field
names) and, for a few refused questions, checks whether Q2's target concepts exist
as graph nodes AT ALL, and whether they fall inside the design-A scoped subgraph.

RUN from repo root:  python diagnose_anchors.py
"""
import glob, json, os, sys
from collections import Counter

OUT = "output"
INDEX = os.path.join("index", "delucionqa")


def load_jsonl(p):
    rows = []
    if p and os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def first_out(*pats):
    for pat in pats:
        hits = sorted(glob.glob(os.path.join(OUT, pat)))
        if hits:
            return hits[0]
    return None


def profile_predicates(profile):
    """governance_profile is a LIST of {domain, affinity_weight, rules:{relational_predicates}}."""
    preds = set()
    if isinstance(profile, list):
        for view in profile:
            if isinstance(view, dict):
                preds.update((view.get("rules") or {}).get("relational_predicates", []) or [])
    elif isinstance(profile, dict):
        preds.update((profile.get("primary_laws") or {}).get("relational_predicates", []) or [])
        preds.update(profile.get("relational_predicates", []) or [])
    return preds


def dump_first(label, path):
    rows = load_jsonl(path)
    print("-" * 70)
    print("[%s] %s  (%d records)" % (label, path or "NOT FOUND", len(rows)))
    if rows:
        r0 = rows[0]
        print("     keys:", list(r0.keys()))
        s = json.dumps(r0, ensure_ascii=False)
        print("     first:", s[:900] + (" ...[truncated]" if len(s) > 900 else ""))
    return rows


def find_strings(obj, out):
    """recursively collect all string leaves (candidate anchor/concept names)."""
    if isinstance(obj, str):
        if obj.strip():
            out.add(obj.strip())
    elif isinstance(obj, list):
        for x in obj:
            find_strings(x, out)
    elif isinstance(obj, dict):
        for x in obj.values():
            find_strings(x, out)


def main():
    # --- correct authorized-predicate universe ---
    staged = load_jsonl(os.path.join(OUT, "D5_Extraction_Manifest.jsonl"))
    corpus = load_jsonl(os.path.join(INDEX, "D5_Extraction_Manifest.jsonl"))
    auth = set()
    for r in staged:
        auth |= profile_predicates(r.get("governance_profile"))
    corp = set()
    for r in corpus:
        corp |= profile_predicates(r.get("governance_profile"))
    print("=" * 70)
    print("[A] authorized predicates (served, corrected) : %d  %s" % (len(auth), sorted(auth)[:30]))
    print("[A] authorized predicates (build corpus union): %d  %s" % (len(corp), sorted(corp)[:30]))

    # --- graph ---
    import networkx as nx
    g = nx.read_graphml(os.path.join(OUT, "M5_Embedded_Graph.graphml"))
    node_ids = set(map(str, g.nodes()))
    node_labels = set()
    for n, d in g.nodes(data=True):
        for a in ("label", "name", "concept", "text"):
            if d.get(a):
                node_labels.add(str(d[a]))
    all_node_str = node_ids | node_labels
    all_node_lc = {s.lower() for s in all_node_str}
    print("=" * 70)
    print("[B] graph: %d nodes, %d edges. sample node ids: %s" %
          (g.number_of_nodes(), g.number_of_edges(), list(node_ids)[:8]))
    print("    sample node labels:", list(node_labels)[:8])

    # --- introspect Q-stage outputs (learn field names) ---
    print("=" * 70)
    q1 = dump_first("Q1", first_out("Q1_*intent*.jsonl", "Q1_*.jsonl"))
    q2 = dump_first("Q2", first_out("Q2_*sig*.jsonl", "Q2_*.jsonl"))
    q3 = dump_first("Q3", first_out("Q3_retrieved_evidence.jsonl", "Q3_*evidence*.jsonl"))
    q6 = load_jsonl(first_out("Q6_final_answers.jsonl"))

    # which q_ids refused
    def is_refusal(rec):
        a = (rec.get("generated_answer") or "") + (rec.get("mode") or "")
        return "Boundary" in a or "blocked" in a.lower() or str(rec.get("mode", "")).startswith("BLOCKED")
    refused = [str(r.get("record_id")) for r in q6 if is_refusal(r)]
    answered = [str(r.get("record_id")) for r in q6 if not is_refusal(r)]
    print("=" * 70)
    print("[C] Q6: %d refused, %d answered. answered ids: %s" % (len(refused), len(answered), answered[:5]))

    # --- scope map ---
    cf = {}
    p = os.path.join(OUT, "serve_chunk_filter.json")
    if os.path.exists(p):
        cf = json.load(open(p, encoding="utf-8"))

    def edge_cid(d, k):
        for a in ("chunk_id", "source_chunk_id"):
            if d.get(a):
                return str(d[a])
        parts = str(d.get("forensic_key") or k or "").split("_")
        return parts[-2] if len(parts) >= 2 else ""

    q3_by_id = {str(r.get("record_id")): r for r in q3}

    def scoped_nodes(qid):
        wanted = set(map(str, cf.get(qid, [])))
        ns = set()
        for u, v, k, d in g.edges(keys=True, data=True):
            if edge_cid(d, k) in wanted:
                ns.add(str(u)); ns.add(str(v))
        return ns, wanted

    # --- the key test: do Q2 concepts exist as nodes, and are they in scope? ---
    print("=" * 70)
    print("[D] ANCHOR EXISTENCE for up to 4 refused questions:")
    sample = (refused or list(cf))[:4]
    for qid in sample:
        rec = q3_by_id.get(qid, {})
        # collect candidate concept strings from the q_signature / whole record
        cand = set()
        find_strings(rec.get("q_signature", rec), cand)
        # keep plausible concept tokens (short-ish, not huge text blobs)
        cand = {c for c in cand if 1 <= len(c) <= 60 and not c.startswith("CHNK_")}
        ns, wanted = scoped_nodes(qid)
        exist_global = [c for c in cand if c in all_node_str or c.lower() in all_node_lc]
        exist_scope = [c for c in cand if c in ns]
        # substring fallback (concept appears within some node label)
        sub_global = [c for c in cand if any(c.lower() in s for s in all_node_lc)]
        print("    %s | chunks=%d scoped_nodes=%d | concepts=%d exact_global=%d in_scope=%d substr_global=%d"
              % (qid, len(wanted), len(ns), len(cand), len(exist_global), len(exist_scope), len(sub_global)))
        print("        concepts sample:", sorted(cand)[:8])
        print("        matched globally:", exist_global[:8] or sub_global[:8])
    print("=" * 70)
    print("READ: if concepts exist_global>0 but in_scope=0 -> scoping too narrow (anchors")
    print("      live outside the question's own chunk edges). If exact_global=0 but")
    print("      substr_global>0 -> matcher needs normalization/fuzzy. If both 0 -> Q2")
    print("      concepts are nothing like node names (Q1/Q2 concept extraction mismatch).")


if __name__ == "__main__":
    main()
