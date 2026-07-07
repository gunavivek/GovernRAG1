#!/usr/bin/env python3
"""
spectrum_diag.py -- READ-ONLY. Reports the two ontology-derived signals so you can pick
sensible settings BEFORE running the axis sweep:
  * alignment_status distribution over M5 graph nodes  (Axis A: GOVRAG_ONTOLOGY)
  * wa_score distribution over M1 chunks               (Axis B: GOVRAG_AFFINITY_MIN)
It writes nothing and touches no pipeline code.

RUN from repo root:  python Paper2/4_Harness/spectrum_diag.py
"""
import csv, os, statistics as st, sys, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

def find_root(start):
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start

ROOT = find_root(Path.cwd()); OUT = ROOT / "output"
GML = OUT / "M5_Embedded_Graph.graphml"; M1 = OUT / "M1_Governed_Chunks.csv"
NS = "{http://graphml.graphdrawing.org/xmlns}"

print("== Axis A: reference-ontology conformance (M5 node alignment_status) ==")
if GML.exists():
    r = ET.parse(str(GML)).getroot()
    kid = next((k.get("id") for k in r.iter(NS + "key")
                if k.get("attr.name") == "alignment_status" and k.get("for") == "node"), None)
    c = Counter()
    for n in r.iter(NS + "node"):
        v = "<none>"
        for d in n.findall(NS + "data"):
            if d.get("key") == kid:
                v = d.text
        c[v] += 1
    tot = sum(c.values())
    print("  nodes=%d  key=%s" % (tot, kid))
    for k, v in c.most_common():
        print("    %-18s %5d  (%4.1f%%)" % (k, v, 100 * v / tot))
    tagged = tot - c.get("<none>", 0)
    print("  -> GOVRAG_ONTOLOGY=not_unmapped keeps Match/Adaptive/none, drops Unmapped")
    print("  -> GOVRAG_ONTOLOGY=conformant  keeps ONLY Match/Adaptive (%d nodes = %.1f%%)"
          % (c.get("Match", 0) + c.get("Adaptive", 0),
             100 * (c.get("Match", 0) + c.get("Adaptive", 0)) / tot))
else:
    print("  [missing] %s -- run the build (M5) first." % GML)

print("\n== Axis B: domain affinity (M1 wa_score) ==")
if M1.exists():
    csv.field_size_limit(10_000_000)
    xs = []
    for row in csv.DictReader(open(M1, encoding="utf-8")):
        try: xs.append(float(row["wa_score"]))
        except (TypeError, ValueError, KeyError): pass
    xs.sort()
    if xs:
        q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
        print("  n=%d  min=%.3f  p25=%.3f  median=%.3f  p75=%.3f  max=%.3f  mean=%.3f"
              % (len(xs), xs[0], q(.25), q(.5), q(.75), xs[-1], st.mean(xs)))
        for tau in (q(.25), q(.5), q(.75)):
            keep = sum(1 for x in xs if x >= tau)
            print("    GOVRAG_AFFINITY_MIN=%.3f keeps %d/%d chunks (%.0f%%)"
                  % (tau, keep, len(xs), 100 * keep / len(xs)))
    else:
        print("  [empty] no wa_score values parsed.")
else:
    print("  [missing] %s" % M1)
