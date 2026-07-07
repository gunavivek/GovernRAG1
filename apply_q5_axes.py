#!/usr/bin/env python3
"""
apply_q5_axes.py -- add two ONTOLOGY-DERIVED governance axes to Q5's reference monitor,
each env-gated and DEFAULT-OFF (frozen behaviour preserved unless the env var is set):

  Axis A  GOVRAG_ONTOLOGY  in {all(default), not_unmapped, conformant}
          Filters the (already predicate-authorized) triplets by reference-ontology
          conformance using the s_align/o_align tags Q3 attaches (apply_q3_ontology_tag.py):
            all           -> no ontology filter (default)
            not_unmapped  -> drop triplets whose subject OR object is 'Unmapped*'
            conformant    -> keep only triplets whose subject AND object are Match/Adaptive
  Axis B  GOVRAG_AFFINITY_MIN  float (default 0 = off)
          Drops Tier-1 primary chunks whose M1 wa_score < threshold (domain affinity).

Composes with GOVRAG_LEVEL (predicate authorization). Idempotent. Backup: .bakA

RUN from repo root:  python Paper2/4_Harness/apply_q5_axes.py
"""
import os, shutil, sys

Q5 = os.path.join("experiment", "Q5_Gov_Context_Router.py")

LOADER_ANCHOR = 'Q5_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "Q5_routed_context.jsonl")\n'
LOADER_NEW = LOADER_ANCHOR + (
    '\n'
    'import csv as _csv\n'
    'import glob as _glob\n'
    '_WA_CACHE = None\n'
    'def _load_wa_scores():\n'
    '    """chunk_id -> wa_score from M1_Governed_Chunks.csv (Axis B: domain affinity)."""\n'
    '    global _WA_CACHE\n'
    '    if _WA_CACHE is not None:\n'
    '        return _WA_CACHE\n'
    '    _WA_CACHE = {}\n'
    '    _cands = [os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")]\n'
    '    _cands += sorted(_glob.glob(os.path.join(PROJECT_ROOT, "index", "*", "M1_Governed_Chunks.csv")))\n'
    '    _cands += sorted(_glob.glob(os.path.join(PROJECT_ROOT, "index", "**", "M1_Governed_Chunks.csv"), recursive=True))\n'
    '    _path = next((c for c in _cands if os.path.exists(c)), None)\n'
    '    if _path:\n'
    '        _csv.field_size_limit(10_000_000)\n'
    '        with open(_path, encoding="utf-8") as _f:\n'
    '            for _row in _csv.DictReader(_f):\n'
    '                try:\n'
    '                    _WA_CACHE[_row.get("chunk_id") or ""] = float(_row.get("wa_score"))\n'
    '                except (TypeError, ValueError):\n'
    '                    pass\n'
    '        print("  [Axis B] wa_scores loaded from %s (%d chunks)" % (_path, len(_WA_CACHE)))\n'
    '    else:\n'
    '        print("  [Axis B][WARN] no M1_Governed_Chunks.csv found; affinity filter is a no-op")\n'
    '    return _WA_CACHE\n'
)

ONT_ANCHOR = '        dropped_triplets = len(raw_triplets) - len(governed_triplets)\n'
ONT_NEW = (
    '        # --- Axis A: reference-ontology conformance (env GOVRAG_ONTOLOGY; default all=off) ---\n'
    '        _ont = os.getenv("GOVRAG_ONTOLOGY", "all").lower()\n'
    '        if _ont in ("conformant", "not_unmapped"):\n'
    '            def _conf(v):\n'
    '                v = str(v or "Unknown").lower()\n'
    '                if _ont == "not_unmapped":\n'
    '                    return "unmapped" not in v\n'
    '                return v in ("match", "adaptive")\n'
    '            _before = len(governed_triplets)\n'
    '            governed_triplets = [t for t in governed_triplets\n'
    '                                 if _conf(t.get("s_align")) and _conf(t.get("o_align"))]\n'
    '            print(f"  [Axis A] ontology=%s dropped %d non-conformant triplets"\n'
    '                  % (_ont, _before - len(governed_triplets)))\n'
    '\n'
    + ONT_ANCHOR
)

AFF_ANCHOR = '        filtered_semantic_chunk = "\\n".join(governed_primary_chunks)\n'
AFF_NEW = (
    '        # --- Axis B: domain-affinity gate (env GOVRAG_AFFINITY_MIN; default 0=off) ---\n'
    '        _amin = float(os.getenv("GOVRAG_AFFINITY_MIN", "0") or 0)\n'
    '        if _amin > 0:\n'
    '            _wa = _load_wa_scores()\n'
    '            _kept = []\n'
    '            for _piece in governed_primary_chunks:\n'
    '                _m = re.search(r"\\[(CHNK_[^\\]]+)\\]", _piece)\n'
    '                _sc = _wa.get(_m.group(1)) if _m else None\n'
    '                if _sc is None or _sc >= _amin:\n'
    '                    _kept.append(_piece)\n'
    '            print(f"  [Axis B] affinity>=%.3f dropped %d low-affinity chunks"\n'
    '                  % (_amin, len(governed_primary_chunks) - len(_kept)))\n'
    '            governed_primary_chunks = _kept\n'
    '\n'
    + AFF_ANCHOR
)

def main():
    if not os.path.exists(Q5):
        sys.exit("[FATAL] %s not found -- run from the repo root." % Q5)
    src = open(Q5, encoding="utf-8").read()
    if "GOVRAG_ONTOLOGY" in src or "GOVRAG_AFFINITY_MIN" in src:
        print("Already axes-patched -- nothing to do."); return
    for name, anc in (("loader", LOADER_ANCHOR), ("ontology", ONT_ANCHOR), ("affinity", AFF_ANCHOR)):
        if src.count(anc) != 1:
            sys.exit("[FATAL] Q5 %s anchor matched %d times (need 1). Not written." % (name, src.count(anc)))
    src = src.replace(LOADER_ANCHOR, LOADER_NEW, 1)
    src = src.replace(ONT_ANCHOR, ONT_NEW, 1)
    src = src.replace(AFF_ANCHOR, AFF_NEW, 1)
    shutil.copy2(Q5, Q5 + ".bakA")
    with open(Q5, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("[OK] Q5 axes added: GOVRAG_ONTOLOGY (Axis A) + GOVRAG_AFFINITY_MIN (Axis B); default off. Backup: %s.bakA" % Q5)

if __name__ == "__main__":
    main()
