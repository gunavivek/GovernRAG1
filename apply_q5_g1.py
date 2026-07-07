#!/usr/bin/env python3
"""
apply_q5_g1.py -- let Q5 skip the authorization filter when GOVRAG_LEVEL == "G1".

G1 (Cited) = no predicate authorization: keep ALL retrieved evidence. Q5 already keeps
everything when allowed_predicates is empty (its `else: keep all` branches), so we just
empty the set in G1 mode. DEFAULT (env unset or != G1) = unchanged. Idempotent; .bak.

RUN from repo root:  python apply_q5_g1.py
"""
import os, shutil, sys

Q5 = os.path.join("experiment", "Q5_Gov_Context_Router.py")
ANCHOR = ('        for profile in d5_contract.get("governance_profile", []):\n'
          '            preds = profile.get("rules", {}).get("relational_predicates", [])\n'
          '            allowed_predicates.update([p.lower() for p in preds])\n')
NEW = ANCHOR + ('        if os.getenv("GOVRAG_LEVEL", "G3") == "G1":\n'
                '            allowed_predicates = set()  # G1: no authorization filter -> keep all evidence\n')


def main():
    if not os.path.exists(Q5):
        sys.exit("[FATAL] %s not found -- run from the repo root." % Q5)
    src = open(Q5, encoding="utf-8").read()
    if "GOVRAG_LEVEL" in src:
        print("Already G1-toggle patched -- nothing to do."); return
    if src.count(ANCHOR) != 1:
        sys.exit("[FATAL] Q5 allowed-predicates anchor matched %d times (need 1). Not written." % src.count(ANCHOR))
    src = src.replace(ANCHOR, NEW, 1)
    shutil.copy2(Q5, Q5 + ".bakL")
    with open(Q5, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("[OK] Q5 G1 toggle added (default unchanged; G1 keeps all evidence). Backup: %s.bakL" % Q5)


if __name__ == "__main__":
    main()
