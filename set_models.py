#!/usr/bin/env python3
"""
set_models.py -- set the serve-side LLM model in one place (quality-first).

Changes THREE model references to --model (default gemini-3-pro):
  experiment/Q6_Gov_Answer_Generation.py   MODEL_ID       (governed generation)
  experiment/Q2_Gov_Signature_Extractor_V2.py  MODEL_ID   (predicate mapping)
  B2_Serve.py                              BASELINE_MODEL  (naive baseline)

Q6 and the naive baseline MUST match (generation parity) -- this keeps them locked
together. Idempotent; per-file .bak (.bakm); prints old -> new.

RUN from repo root:  python set_models.py                 # -> gemini-3-pro
                     python set_models.py --model gemini-3.5-flash
"""
import argparse, os, re, shutil, sys

TARGETS = [
    (os.path.join("experiment", "Q6_Gov_Answer_Generation.py"), r'MODEL_ID\s*=\s*"([^"]*)"', 'MODEL_ID = "%s"'),
    (os.path.join("experiment", "Q2_Gov_Signature_Extractor_V2.py"), r'MODEL_ID\s*=\s*"([^"]*)"', 'MODEL_ID = "%s"'),
    ("B2_Serve.py", r'BASELINE_MODEL\s*=\s*"([^"]*)"', 'BASELINE_MODEL = "%s"'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-3-pro")
    args = ap.parse_args()

    changed = 0
    for path, pat, repl in TARGETS:
        if not os.path.exists(path):
            print(f"[WARN] {path} not found -- skipping"); continue
        src = open(path, encoding="utf-8").read()
        m = re.search(pat, src)
        if not m:
            print(f"[WARN] no model line found in {path} -- skipping"); continue
        old = m.group(1)
        if old == args.model:
            print(f"[skip] {path}: already {old}"); continue
        new_src = re.sub(pat, repl % args.model, src, count=1)
        shutil.copy2(path, path + ".bakm")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_src)
        print(f"[OK]   {path}: {old} -> {args.model}  (backup {path}.bakm)")
        changed += 1
    print(f"[done] {changed} file(s) updated to model '{args.model}'.")
    print("       Q6 == naive baseline (parity) is preserved.")


if __name__ == "__main__":
    main()
