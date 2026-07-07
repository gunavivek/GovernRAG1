#!/usr/bin/env python3
"""
apply_q3_ontology_tag.py -- Axis A (part 1): make Q3 tag each emitted triplet with the
reference-ontology alignment_status of its subject and object nodes (from the M5 graph
that Q3 already has loaded as self.G). This is PURELY ADDITIVE: it attaches two new keys
(s_align, o_align) to each triplet dict and changes NOTHING about which triplets are kept.
Q5's Axis-A filter (apply_q5_axes.py) reads these tags only when GOVRAG_ONTOLOGY is set.

Default pipeline behaviour is unchanged. Idempotent. Backup: .bakO

RUN from repo root:  python Paper2/4_Harness/apply_q3_ontology_tag.py
"""
import os, shutil, sys

Q3 = os.path.join("experiment", "Q3_Gov_Graph_Retrieval_Engine_V3.py")
ANCHOR = '                new_triplets = [{"s": t[0], "p": t[1], "o": t[2]} for t in triples]\n'
NEW = (
    '                new_triplets = []\n'
    '                for t in triples:\n'
    '                    trip = {"s": t[0], "p": t[1], "o": t[2]}\n'
    '                    s_data = self.G.nodes[t[0]] if self.G.has_node(t[0]) else {}\n'
    '                    o_data = self.G.nodes[t[2]] if self.G.has_node(t[2]) else {}\n'
    '                    trip["s_align"] = s_data.get("alignment_status", "Unknown")\n'
    '                    trip["o_align"] = o_data.get("alignment_status", "Unknown")\n'
    '                    new_triplets.append(trip)\n'
)

def main():
    if not os.path.exists(Q3):
        sys.exit("[FATAL] %s not found -- run from the repo root." % Q3)
    src = open(Q3, encoding="utf-8").read()
    if "s_align" in src:
        print("Already ontology-tag patched -- nothing to do."); return
    if src.count(ANCHOR) != 1:
        sys.exit("[FATAL] Q3 triplet-build anchor matched %d times (need 1). Not written." % src.count(ANCHOR))
    src = src.replace(ANCHOR, NEW, 1)
    shutil.copy2(Q3, Q3 + ".bakO")
    with open(Q3, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("[OK] Q3 now tags triplets with s_align/o_align (additive; behaviour unchanged). Backup: %s.bakO" % Q3)

if __name__ == "__main__":
    main()
