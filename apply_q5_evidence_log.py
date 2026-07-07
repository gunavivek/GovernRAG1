#!/usr/bin/env python3
"""
apply_q5_evidence_log.py -- instrument Q5 to record the EVIDENCE-SET REDUCTION each governance
setting produces, so the "scopes evidence, not answers" claim has numbers behind it. Adds an
"evidence_reduction" block to each record's audit_metadata (flows to output/Q5_routed_context.jsonl):
  predicate_triplets_dropped, ontology_triplets_dropped (Axis A), affinity_chunks_dropped (Axis B),
  chunks_dropped_total, triplets_kept, primary_chunks_kept, + the active level/ontology/affinity.

PRE-REQ: apply_q5_axes.py already applied (needs the Axis-A/Axis-B blocks). Additive only;
changes no filtering behaviour. Idempotent. Backup: .bakE
RUN from repo root:  python apply_q5_evidence_log.py
"""
import os, shutil, sys

Q5 = os.path.join("experiment", "Q5_Gov_Context_Router.py")

INIT_ANCHOR = "        governed_triplets = []\n"
INIT_NEW = INIT_ANCHOR + "        _ont_dropped = 0\n        _aff_dropped = 0\n"

ONTCAP_ANCHOR = (
    '            print(f"  [Axis A] ontology=%s dropped %d non-conformant triplets"\n'
    '                  % (_ont, _before - len(governed_triplets)))\n'
)
ONTCAP_NEW = (
    '            _ont_dropped = _before - len(governed_triplets)\n'
    '            print(f"  [Axis A] ontology=%s dropped %d non-conformant triplets"\n'
    '                  % (_ont, _ont_dropped))\n'
)

AFFCAP_ANCHOR = (
    '            print(f"  [Axis B] affinity>=%.3f dropped %d low-affinity chunks"\n'
    '                  % (_amin, len(governed_primary_chunks) - len(_kept)))\n'
    '            governed_primary_chunks = _kept\n'
)
AFFCAP_NEW = (
    '            _aff_dropped = len(governed_primary_chunks) - len(_kept)\n'
    '            print(f"  [Axis B] affinity>=%.3f dropped %d low-affinity chunks"\n'
    '                  % (_amin, _aff_dropped))\n'
    '            governed_primary_chunks = _kept\n'
)

META_ANCHOR = '            "chunk_decision_log": chunk_audit_log \n'
META_NEW = (
    '            "chunk_decision_log": chunk_audit_log,\n'
    '            "evidence_reduction": {\n'
    '                "level": os.getenv("GOVRAG_LEVEL", "G3"),\n'
    '                "ontology_mode": os.getenv("GOVRAG_ONTOLOGY", "all"),\n'
    '                "affinity_min": float(os.getenv("GOVRAG_AFFINITY_MIN", "0") or 0),\n'
    '                "predicate_triplets_dropped": dropped_triplets - _ont_dropped,\n'
    '                "ontology_triplets_dropped": _ont_dropped,\n'
    '                "affinity_chunks_dropped": _aff_dropped,\n'
    '                "chunks_dropped_total": dropped_chunks,\n'
    '                "triplets_kept": len(governed_triplets),\n'
    '                "primary_chunks_kept": len(governed_primary_chunks),\n'
    '            },\n'
)

def main():
    if not os.path.exists(Q5):
        sys.exit("[FATAL] %s not found -- run from the repo root." % Q5)
    src = open(Q5, encoding="utf-8").read()
    if "GOVRAG_ONTOLOGY" not in src:
        sys.exit("[FATAL] apply_q5_axes.py must be applied first (no Axis blocks found).")
    if "evidence_reduction" in src:
        print("Already evidence-log patched -- nothing to do."); return
    for name, anc in (("init", INIT_ANCHOR), ("ontcap", ONTCAP_ANCHOR),
                      ("affcap", AFFCAP_ANCHOR), ("meta", META_ANCHOR)):
        if src.count(anc) != 1:
            sys.exit("[FATAL] Q5 %s anchor matched %d times (need 1). Not written." % (name, src.count(anc)))
    src = src.replace(INIT_ANCHOR, INIT_NEW, 1)
    src = src.replace(ONTCAP_ANCHOR, ONTCAP_NEW, 1)
    src = src.replace(AFFCAP_ANCHOR, AFFCAP_NEW, 1)
    src = src.replace(META_ANCHOR, META_NEW, 1)
    shutil.copy2(Q5, Q5 + ".bakE")
    with open(Q5, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("[OK] Q5 evidence-reduction logger added (audit_metadata.evidence_reduction). Backup: %s.bakE" % Q5)

if __name__ == "__main__":
    main()
