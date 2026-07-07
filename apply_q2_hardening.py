#!/usr/bin/env python3
"""
apply_q2_hardening.py -- make Q2's predicate mapping tolerant of malformed LLM JSON.

PROBLEM (serve-many blocker): Q2._map_predicates_dynamically does
    clean_res = response.text.strip().replace("```json","").replace("```","")
    return json.loads(clean_res)          # any bad response -> raise -> whole batch dies
On flash-lite a single truncated response (e.g. "[") aborts all questions.

FIX (output-neutral on the happy path; matches the code's OWN Rule 2
"if no clear match, return an empty list []"):
  - retry up to 3x (recovers transient truncations at temp 0),
  - salvage the first JSON array with a regex if the raw text is wrapped/truncated,
  - degrade to [] instead of crashing.
No governance semantics change: valid JSON parses identically to before.

Idempotent; makes a .bak; writes UTF-8 no-BOM.
RUN from repo root:  python apply_q2_hardening.py
"""
import os, re, shutil, sys

Q2 = os.path.join("experiment", "Q2_Gov_Signature_Extractor_V2.py")

NEW_BLOCK = '''        import time as _time
        last_err = None
        for _attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=mapping_prompt,
                    config=types.GenerateContentConfig(temperature=0.0)  # Zero temp for DSR reproducibility
                )
                clean_res = (response.text or "").strip().replace("```json", "").replace("```", "").strip()
                try:
                    val = json.loads(clean_res)
                except json.JSONDecodeError:
                    m = re.search(r"\\[.*\\]", clean_res, re.DOTALL)  # salvage a JSON array if wrapped/truncated
                    if not m:
                        raise
                    val = json.loads(m.group(0))
                return val if isinstance(val, list) else []
            except Exception as e:
                last_err = e
                _time.sleep(2 * (_attempt + 1))
        print(f"[Q2][WARN] predicate mapping degraded to [] (Rule 2) after 3 tries: {last_err}")
        return []
'''

# match from the `try:` down to the RuntimeError re-raise, inclusive
PAT = re.compile(
    r"        try:\n"
    r"            response = client\.models\.generate_content\(.*?"
    r'            raise RuntimeError\(f"Dynamic Mapping Failure: \{e\}"\) from e\n',
    re.DOTALL,
)


def main():
    if not os.path.exists(Q2):
        sys.exit(f"[FATAL] {Q2} not found -- run from the repo root.")
    src = open(Q2, encoding="utf-8").read()
    if "degraded to [] (Rule 2)" in src:
        print("Already hardened -- nothing to do."); return
    new, n = PAT.subn(NEW_BLOCK, src, count=1)
    if n != 1:
        sys.exit("[FATAL] could not locate the Q2 try/except mapping block (matched %d). "
                 "Paste me lines 82-93 of Q2 and I'll adjust the pattern." % n)
    shutil.copy2(Q2, Q2 + ".bak")
    with open(Q2, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    print(f"[OK] hardened {Q2} (1 block). Backup: {Q2}.bak")
    print("     verify: python -c \"import ast; ast.parse(open(r'%s',encoding='utf-8').read()); print('Q2 parses clean')\"" % Q2)


if __name__ == "__main__":
    main()
