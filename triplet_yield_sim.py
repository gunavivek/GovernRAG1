#!/usr/bin/env python3
"""
triplet_yield_sim.py -- READ-ONLY. Confirms the Q3 chokepoint is ANCHOR RESOLUTION and
quantifies the recoverable material, replicating the LIVE Q3 logic without changing anything:
  * live scoping: edges scoped by the question's chunk_ids (serve_chunk_filter) -- same as live Q3.
  * live anchors: substring match of q_signature target_nodes vs scoped node names (_resolve_anchors).
  * simulated walk: k-hop traversal from those anchors keeping required-predicate edges (== live yield).
  * ceiling: admissible (required-predicate) edges reachable if the walk seeded from ALL scoped nodes.
The gap between simulated-yield and ceiling IS the anchor-resolution loss.

Reads output/{M5_Embedded_Graph.graphml, Q3_retrieved_evidence.jsonl, serve_chunk_filter.json}.
Writes results/triplet_yield_sim.csv. Touches no pipeline code.
RUN from repo root:  python triplet_yield_sim.py
"""
import json, os, re, sys, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

def find_root(start):
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start

ROOT = find_root(Path.cwd()); OUT = ROOT / "output"; RES = ROOT / "results"; RES.mkdir(exist_ok=True)
NS = "{http://graphml.graphdrawing.org/xmlns}"

def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []

def edge_cid(attrs, key):
    for a in ("chunk_id", "source_chunk_id"):
        if attrs.get(a): return str(attrs[a])
    parts = str(attrs.get("forensic_key") or key or "").split("_")
    return parts[-2] if len(parts) >= 2 else ""

def matches(p_label, required):
    pl = str(p_label).lower()
    return (not required) or any(str(p).lower() in pl for p in required)

def main():
    gml = OUT / "M5_Embedded_Graph.graphml"
    if not gml.exists(): sys.exit("[FATAL] %s missing." % gml)
    r = ET.parse(str(gml)).getroot()
    ekey = {k.get("id"): k.get("attr.name") for k in r.iter(NS + "key") if k.get("for") == "edge"}
    # edges grouped by chunk_id: (u, v, predicate)
    by_chunk = defaultdict(list)
    for e in r.iter(NS + "edge"):
        u, v = e.get("source"), e.get("target")
        attrs = {ekey.get(d.get("key"), d.get("key")): d.text for d in e.findall(NS + "data")}
        p = attrs.get("predicate") or "related_to"
        by_chunk[edge_cid(attrs, e.get("id"))].append((u, v, p))

    cf = OUT / "serve_chunk_filter.json"
    chunk_filter = json.load(open(cf, encoding="utf-8")) if cf.exists() else {}
    recs = load_jsonl(OUT / "Q3_retrieved_evidence.jsonl")
    if not recs: sys.exit("[FATAL] Q3 evidence missing -- run B2 first.")

    def walk(adj, seeds, required, k):
        seen_e = set(); layer = set(seeds); visited = set(seeds)
        for _ in range(max(1, k)):
            nxt = set()
            for u in layer:
                for v, p in adj.get(u, []):
                    if matches(p, required):
                        seen_e.add((u, p, v))
                        if v not in visited: nxt.add(v)
            layer = nxt; visited |= nxt
            if not layer: break
        return seen_e

    rows = [("record_id", "scoped_edges", "admissible", "live_anchors", "sim_triplets", "r1_anchors", "sim_r1_triplets", "ceiling_triplets")]
    agg = defaultdict(float); n = 0
    for rec in recs:
        rid = str(rec.get("record_id"))
        sig = rec.get("q_signature") or {}
        required = sig.get("required_predicates") or []
        targets = [str(t).lower() for t in (sig.get("target_nodes") or []) if len(str(t)) > 1]
        khops = int((rec.get("traversal_stats") or {}).get("hops") or 2)
        chunks = set(map(str, chunk_filter.get(rid, rec.get("contributing_chunks") or [])))
        scoped = [ed for c in chunks for ed in by_chunk.get(c, [])]
        nodes = set()
        adj = defaultdict(list)      # directed (out-edges), as the live walk uses
        biadj = defaultdict(list)    # bidirectional (in+out), the candidate walk fix
        for u, v, p in scoped:
            nodes.add(u); nodes.add(v)
            adj[u].append((v, p))
            biadj[u].append((v, p)); biadj[v].append((u, p))
        admissible = sum(1 for _, _, p in scoped if matches(p, required))
        # R0: live anchor logic (substring both directions)
        anchors = [nd for nd in nodes if any(e in nd.lower() or nd.lower() in e for e in targets)]
        sim = walk(adj, set(anchors), required, khops)
        # R1: token-overlap resolver (whole-word tokens, min length 4) -- the candidate FIX
        def toks(x): return set(w for w in re.findall(r"[a-z0-9]+", str(x).lower()) if len(w) >= 4)
        ttok = set().union(*[toks(t) for t in targets]) if targets else set()
        anchors_r1 = [nd for nd in nodes if toks(nd) & ttok]
        sim_r1 = walk(adj, set(anchors_r1), required, khops)
        sim_r2 = walk(biadj, set(anchors), required, khops)   # R2: bidirectional traversal, same anchors
        sim_r2b = walk(biadj, set(anchors_r1), required, khops)  # R2b: bidirectional + token-overlap anchors
        ceiling = walk(adj, nodes, required, khops)   # seed from ALL scoped nodes
        n += 1
        for k_, val in (("scoped", len(scoped)), ("admissible", admissible), ("anchors", len(anchors)),
                        ("anchors_r1", len(anchors_r1)), ("sim", len(sim)), ("sim_r1", len(sim_r1)),
                        ("sim_r2", len(sim_r2)), ("sim_r2b", len(sim_r2b)), ("ceiling", len(ceiling))):
            agg[k_] += val
        rows.append((rid, len(scoped), admissible, len(anchors), len(sim), len(anchors_r1), len(sim_r1), len(ceiling)))
    with open(RES / "triplet_yield_sim.csv", "w", encoding="utf-8") as f:
        for row in rows: f.write(",".join(map(str, row)) + "\n")

    m = {k: agg[k] / n for k in agg}
    print("=" * 70)
    print("Q3 YIELD SIMULATION (live logic replicated)   N=%d records" % n)
    print("=" * 70)
    print("  scoped edges (by chunk) ........ %.2f" % m["scoped"])
    print("  admissible (req-predicate) ..... %.2f   <- reachable ceiling of governed edges" % m["admissible"])
    print("  LIVE anchors resolved .......... %.2f   <- _resolve_anchors substring match" % m["anchors"])
    print("  simulated triplets (current) ... %.2f   <- should match your real ~0.75 yield" % m["sim"])
    print("  --- candidate FIX (token-overlap resolver) ---")
    print("  R1 anchors resolved ............ %.2f" % m["anchors_r1"])
    print("  R1 simulated triplets .......... %.2f   <- token-overlap resolver (same direction)" % m["sim_r1"])
    print("  R2 bidirectional (live anchors)  %.2f   <- walk follows in+out edges" % m["sim_r2"])
    print("  R2b bidirectional + token anchors %.2f  <- both fixes combined" % m["sim_r2b"])
    print("  ceiling triplets (all-node seed) %.2f   <- upper bound (loses query focus)" % m["ceiling"])
    print("-" * 70)
    loss = (1 - m["sim"] / m["ceiling"]) * 100 if m["ceiling"] else 0
    print("ANCHOR-RESOLUTION LOSS: current yield recovers %.0f%% of the reachable governed material;"
          % (100 * m["sim"] / m["ceiling"] if m["ceiling"] else 0))
    print("                        %.0f%% is lost purely because the walk cannot start from the right nodes." % loss)
    print("[sim] per-record -> results/triplet_yield_sim.csv")

if __name__ == "__main__":
    main()
