#!/usr/bin/env python3
"""
apply_q2_anchor_linking.py -- Option B: graph-grounded anchor linking in frozen Q2.

Makes `target_nodes` include the question's real entities by matching the question
against the design-A SCOPED node vocabulary (output/serve_scoped_vocab.json). Additive:
the frozen quote/capitalization/domain logic is unchanged; the capitalization path is
the fallback. Enabled ONLY when the vocab file exists (ablation = omit it).

Four edits, all in Q2:
  1) __init__: load scoped_vocab if present
  2) _distill_concepts: add `record_id` arg
  3) _distill_concepts: additive matching block before DOMAIN ANCHORING
  4) process(): pass record_id at the call site

Idempotent; makes a .bak; writes UTF-8 no-BOM.
RUN from repo root:  python apply_q2_anchor_linking.py
"""
import os, shutil, sys

Q2 = os.path.join("experiment", "Q2_Gov_Signature_Extractor_V2.py")

INIT_ANCHOR = '''              "General_Relation": ["name", "description"]
        }'''
INIT_NEW = '''              "General_Relation": ["name", "description"]
        }
        # --- Option B: graph-grounded anchor linking (design-A scoped) ---
        # Enabled iff the scoped-vocab artifact is present; else frozen behavior.
        self.scoped_vocab = None
        _sv = os.path.join("output", "serve_scoped_vocab.json")
        if os.path.exists(_sv):
            with open(_sv, encoding="utf-8") as _f:
                self.scoped_vocab = json.load(_f)   # {record_id: [node_name, ...]}
            print(f"[Q2] Anchor linking ON: scoped node vocab for {len(self.scoped_vocab)} questions")'''

SIG_ANCHOR = '''    def _distill_concepts(self, text: str, active_domains: List[str]) -> List[str]:'''
SIG_NEW = '''    def _distill_concepts(self, text: str, active_domains: List[str], record_id: str = None) -> List[str]:'''

DOM_ANCHOR = '''        # 4. DOMAIN ANCHORING'''
DOM_NEW = '''        # 3b. GRAPH-GROUNDED ANCHOR LINKING (design-A scoped) -- additive; fallback-safe.
        if self.scoped_vocab is not None and record_id is not None:
            q_lower = text.lower()
            for name in self.scoped_vocab.get(str(record_id), []):
                nl = str(name).lower().strip()
                if len(nl) >= 4 and re.search(r"\\b" + re.escape(nl) + r"\\b", q_lower):
                    if name not in concepts:
                        concepts.append(name)

        # 4. DOMAIN ANCHORING'''

CALL_ANCHOR = '''                target_nodes = self._distill_concepts(record["question"], active_domains)'''
CALL_NEW = '''                target_nodes = self._distill_concepts(
                    record["question"], active_domains, record_id=record.get("record_id"))'''


def main():
    if not os.path.exists(Q2):
        sys.exit(f"[FATAL] {Q2} not found -- run from the repo root.")
    src = open(Q2, encoding="utf-8").read()
    if "scoped_vocab" in src or "Anchor linking ON" in src:
        print("Already anchor-linked -- nothing to do."); return

    edits = [("__init__ vocab load", INIT_ANCHOR, INIT_NEW),
             ("_distill_concepts signature", SIG_ANCHOR, SIG_NEW),
             ("linking block", DOM_ANCHOR, DOM_NEW),
             ("process() call site", CALL_ANCHOR, CALL_NEW)]
    for label, anchor, _new in edits:
        if src.count(anchor) != 1:
            sys.exit(f"[FATAL] anchor for '{label}' matched {src.count(anchor)} times (need 1). "
                     f"NOT written -- paste me current Q2 and I'll adjust.")
    for _label, anchor, new in edits:
        src = src.replace(anchor, new, 1)

    shutil.copy2(Q2, Q2 + ".bak2")
    with open(Q2, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print(f"[OK] anchor-linking applied to {Q2} (4 edits). Backup: {Q2}.bak2")
    print("     verify: python -c \"import ast; ast.parse(open(r'%s',encoding='utf-8').read()); print('Q2 parses clean')\"" % Q2)


if __name__ == "__main__":
    main()
