#!/usr/bin/env python3
"""
triplet_starvation_diag.py -- READ-ONLY. Explains WHY Q3 retrieves ~0.75 triplets/record on
DelucionQA: is it (a) corpus/build sparsity (few governed edges exist for these chunks), or
(b) a Q3-parameter/attribute throttle (predicate-attr mismatch, required-predicate mismatch, or
anchor resolution)? Reproduces Q3's funnel without running or changing anything.

Q3 funnel (from frozen Q3_Gov_Graph_Retrieval_Engine_V3.py):
  scope subgraph  ->  anchors (q_signature target_nodes)  ->  k-hop walk keeping edges whose
  predicate (data.get('predicate','related_to')) matches a required predicate  ->  triples.

Reads output/{M5_Embedded_Graph.graphml, Q3_retrieved_evidence.jsonl, serve_chunk_filter.json}.
Writes results/triplet_starvation_diag.csv. Touches no pipeline code.
RUN from repo root:  python triplet_starvation_diag.py
"""
import csv, json, os, sys, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

def find_root(start):
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start

ROOT = find_root(Path.cwd()); OUT = ROOT / "output"; RES = ROOT / "results"; RES.mkdir(exist_ok=True)
NS = "{http://graphml.graphdrawing.org/xmlns}"
GML = OUT / "M5_Embedded_Graph.graphml"
Q3 = OUT / "Q3_retrieved_evidence.jsonl"

def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []

def main():
    if not GML.exists():
        sys.exit("[FATAL] %s missing." % GML)
    t = ET.parse(str(GML)); r = t.getroot()
    ekey = {k.get("id"): k.get("attr.name") for k in r.iter(NS + "key") if k.get("for") == "edge"}

    # index edges: by chunk_id and by record_id, capturing (u, v, predicate)
    edges_by_chunk = defaultdict(list)
    edges_by_rid = defaultdict(list)
    tot_edges = 0; with_pred = 0
    pred_vocab = Counter(); rel_vocab = Counter()
    node_ids = set(n.get("id") for n in r.iter(NS + "node"))
    for e in r.iter(NS + "edge"):
        tot_edges += 1
        u, v = e.get("source"), e.get("target")
        attrs = {ekey.get(d.get("key"), d.get("key")): d.text for d in e.findall(NS + "data")}
        pred = attrs.get("predicate")
        if pred: with_pred += 1; pred_vocab[pred] += 1
        rel_vocab[attrs.get("relationship")] += 1
        p_label = pred if pred else "related_to"
        cid = attrs.get("chunk_id"); rid = attrs.get("record_id")
        rec = (u, v, p_label)
        if cid: edges_by_chunk[cid].append(rec)
        if rid: edges_by_rid[rid].append(rec)

    print("=" * 74)
    print("GRAPH  nodes=%d  edges=%d  edges_with_'predicate'=%d (%.0f%%)"
          % (len(node_ids), tot_edges, with_pred, 100 * with_pred / tot_edges if tot_edges else 0))
    print("  top predicate values :", pred_vocab.most_common(10))
    print("  top relationship vals :", rel_vocab.most_common(6))
    print("=" * 74)

    recs = load_jsonl(Q3)
    if not recs:
        sys.exit("[FATAL] %s missing -- run B2/Q3 first." % Q3)

    def matches(p_label, required):
        pl = str(p_label).lower()
        return (not required) or any(str(p).lower() in pl for p in required)

    rows = [("record_id", "contrib_chunks", "scoped_edges", "edges_w_predicate",
             "edges_match_required", "target_nodes", "anchors_in_scope", "triplets_extracted")]
    agg = Counter(); n = 0
    for rec in recs:
        rid = rec.get("record_id")
        sig = rec.get("q_signature") or {}
        required = sig.get("required_predicates") or []
        targets = sig.get("target_nodes") or []
        chunks = rec.get("contributing_chunks") or []
        extracted = len(rec.get("symbolic_triplets") or [])
        # design-A serve scopes by chunk_id; frozen Q3 walk isolates by record_id -- report BOTH
        scoped_chunk = []
        for c in chunks:
            scoped_chunk += edges_by_chunk.get(c, [])
        scoped_rid = edges_by_rid.get(rid, [])
        # the frozen walk uses record_id scoping, so that is the "effective" material
        scoped = scoped_rid if scoped_rid else scoped_chunk
        nodes_in_scope = set()
        for u, v, p in scoped:
            nodes_in_scope.add(u); nodes_in_scope.add(v)
        ew_pred = sum(1 for _, _, p in scoped if p != "related_to")
        ematch = sum(1 for _, _, p in scoped if matches(p, required))
        anchors_in = sum(1 for tn in targets if tn in nodes_in_scope)
        n += 1
        agg["scoped_chunk"] += len(scoped_chunk); agg["scoped_rid"] += len(scoped_rid)
        agg["scoped"] += len(scoped); agg["ew_pred"] += ew_pred; agg["ematch"] += ematch
        agg["targets"] += len(targets); agg["anchors"] += anchors_in; agg["extracted"] += extracted
        rows.append((rid, len(chunks), len(scoped), ew_pred, ematch, len(targets), anchors_in, extracted))
    with open(RES / "triplet_starvation_diag.csv", "w", encoding="utf-8") as f:
        for row in rows:
            f.write(",".join(map(str, row)) + "\n")

    m = {k: agg[k] / n for k in agg} if n else {}
    print("PER-RECORD FUNNEL (mean over %d records)" % n)
    print("  scoped edges by CHUNK id ..... %.2f   (design-A serve scoping)" % m.get("scoped_chunk", 0))
    print("  scoped edges by RECORD id .... %.2f   <- what the FROZEN Q3 walk actually isolates" % m.get("scoped_rid", 0))
    print("  contributing_chunks .......... %.2f" % (sum(len(r.get('contributing_chunks') or []) for r in recs) / n))
    print("  scoped edges ................. %.2f   <- graph material available to the walk" % m.get("scoped", 0))
    print("  ... with a real 'predicate' .. %.2f   (rest default to 'related_to')" % m.get("ew_pred", 0))
    print("  ... matching required preds .. %.2f   <- edges the walk is ALLOWED to keep" % m.get("ematch", 0))
    print("  target_nodes (intended) ...... %.2f" % m.get("targets", 0))
    print("  anchors present in scope ..... %.2f   <- walk can only start from these" % m.get("anchors", 0))
    print("  triplets EXTRACTED ........... %.2f" % m.get("extracted", 0))
    print("-" * 74)
    # verdict heuristic
    sc, ewp, em, an = m.get("scoped", 0), m.get("ew_pred", 0), m.get("ematch", 0), m.get("anchors", 0)
    sc_chunk, sc_rid = m.get("scoped_chunk", 0), m.get("scoped_rid", 0)
    if sc_rid < 1 and sc_chunk >= 1:
        v = "SCOPING MISMATCH: material exists by chunk_id (%.1f) but Q3 isolates by record_id (%.1f=empty) -> design-A serve/graph key mismatch. (Fixable in Q3 scoping, not corpus.)" % (sc_chunk, sc_rid)
    elif sc < 1:
        v = "CORPUS/BUILD SPARSE: almost no governed edges scoped to these chunks (M3.3 produced few triples)."
    elif ewp < 1:
        v = "ATTRIBUTE THROTTLE: scoped edges lack a 'predicate' attr -> walk defaults to 'related_to' -> required-predicate filter starves it. (Fixable in M-build/Q3, not corpus.)"
    elif em < 1:
        v = "PREDICATE THROTTLE: scoped predicated edges exist but none match required_predicates -> the Q2 required-predicate set is too strict / mismatched vocab. (Fixable Q2/Q3 param.)"
    elif an < 1:
        v = "ANCHOR THROTTLE: edges + matching predicates exist but no target_node anchors resolve in scope -> anchor resolution is the bottleneck."
    else:
        v = "WALK/K-HOPS: material, predicates, and anchors are present -> low yield is traversal depth (k_hops) or graph shape."
    print("VERDICT:", v)
    print("[diag] per-record -> results/triplet_starvation_diag.csv")

if __name__ == "__main__":
    main()
