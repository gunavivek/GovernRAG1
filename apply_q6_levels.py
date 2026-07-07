#!/usr/bin/env python3
"""
apply_q6_levels.py -- parameterize Q6's answer gate by GOVRAG_LEVEL (governance spectrum).

Replaces the single hard gate `if not triplets and not residual_chunks:` with a
level-parameterized gate. DEFAULT (env unset) = "G3" = EXACTLY the current behavior.
Idempotent; makes .bak; UTF-8 no-BOM.

RUN from repo root:  python apply_q6_levels.py
"""
import os, shutil, sys

Q6 = os.path.join("experiment", "Q6_Gov_Answer_Generation.py")
ANCHOR = "    if not triplets and not residual_chunks:\n"
NEW = '''    LEVEL = os.getenv("GOVRAG_LEVEL", "G3")   # governance spectrum; default G3 = current
    _nt = len(triplets); _hc = bool(str(text_chunk).strip()); _hr = bool(residual_chunks)
    if LEVEL == "G4":
        _allow = _nt >= 2
    elif LEVEL == "G2":
        _allow = _nt >= 1 or _hc or _hr
    elif LEVEL == "G1":
        _allow = _nt >= 1 or _hc or _hr
    else:
        _allow = _nt >= 1 or _hr
    if not _allow:
'''


def main():
    if not os.path.exists(Q6):
        sys.exit("[FATAL] %s not found -- run from the repo root." % Q6)
    src = open(Q6, encoding="utf-8").read()
    if "GOVRAG_LEVEL" in src:
        print("Already level-parameterized -- nothing to do."); return
    if src.count(ANCHOR) != 1:
        sys.exit("[FATAL] Q6 gate anchor matched %d times (need 1). Not written." % src.count(ANCHOR))
    src = src.replace(ANCHOR, NEW, 1)
    shutil.copy2(Q6, Q6 + ".bakL")
    with open(Q6, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("[OK] Q6 gate parameterized by GOVRAG_LEVEL (default G3 = unchanged). Backup: %s.bakL" % Q6)


if __name__ == "__main__":
    main()
