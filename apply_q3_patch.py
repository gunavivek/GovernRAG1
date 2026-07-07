#!/usr/bin/env python3
"""
apply_q3_patch.py -- apply the design-A chunk-scoping patch to Q3 safely.

Replaces two methods (_get_semantic_text_with_ids, _get_isolated_subgraph) with
design-A-aware versions. Idempotent; makes a .bak; writes UTF-8 no-BOM. If an
anchor doesn't match, it writes nothing and tells you.

RUN from repo root:  python apply_q3_patch.py
"""
import os, re, shutil, sys

Q3 = os.path.join("experiment", "Q3_Gov_Graph_Retrieval_Engine_V3.py")

NEW_SEM = '''    def _get_semantic_text_with_ids(self, record_id: str, chunk_ids=None) -> tuple:
        """Raw governed text chunks for Q5 (design-A aware: filter by chunk_ids if given)."""
        if self.m1_df is not None:
            if chunk_ids is not None:
                matches = self.m1_df[self.m1_df['chunk_id'].isin(set(map(str, chunk_ids)))]
            else:
                matches = self.m1_df[self.m1_df['record_id'] == str(record_id).strip()]
            if not matches.empty:
                cids = matches['chunk_id'].tolist()
                labeled_segments = [f"[{row['chunk_id']}]: {row['chunk_text']}" for _, row in matches.iterrows()]
                return " ".join(labeled_segments), cids
        raise ValueError(f"record_id {record_id} / chunks {chunk_ids} missing in M1 chunks")
'''

NEW_ISO = '''    def _get_isolated_subgraph(self, record_id: str) -> tuple:
        """Epistemic Isolation. Design-A: scope to the question's OWN chunk_ids
        (output/serve_chunk_filter.json) when present; else original record_id isolation."""
        import json as _json
        if not hasattr(self, "_chunk_filter"):
            self._chunk_filter = None
            _cf = os.path.join("output", "serve_chunk_filter.json")
            if os.path.exists(_cf):
                with open(_cf, encoding="utf-8") as _f:
                    self._chunk_filter = _json.load(_f)
                print(f"[Q3] Design-A serve mode: {len(self._chunk_filter)} question filters loaded")

        def _edge_cid(data, key):
            for a in ("chunk_id", "source_chunk_id"):
                if data.get(a):
                    return str(data[a])
            fk = str(data.get("forensic_key") or key or "")
            parts = fk.split("_")
            return parts[-2] if len(parts) >= 2 else ""

        if self._chunk_filter is not None and str(record_id) in self._chunk_filter:
            wanted = set(map(str, self._chunk_filter.get(str(record_id), [])))
            relevant_edges = [(u, v, k) for u, v, k, data in self.G.edges(keys=True, data=True)
                              if _edge_cid(data, k) in wanted]
            if not relevant_edges:
                raise ValueError(f"No edges for question {record_id} ({len(wanted)} chunk ids) -- _edge_cid attr wrong?")
            source_text, chunk_ids = self._get_semantic_text_with_ids(record_id, chunk_ids=wanted)
            return self.G.edge_subgraph(relevant_edges).copy(), source_text, chunk_ids

        relevant_edges = []
        for u, v, k, data in self.G.edges(keys=True, data=True):
            edge_rid = data.get("record_id") or data.get("source_chunk_id")
            if str(edge_rid) == str(record_id):
                relevant_edges.append((u, v, k))
        if not relevant_edges:
            raise ValueError(f"No graph data found in M5 for record_id={record_id}")
        source_text, chunk_ids = self._get_semantic_text_with_ids(record_id)
        return self.G.edge_subgraph(relevant_edges).copy(), source_text, chunk_ids
'''


def replace_method(src, name, new_body):
    pat = re.compile(r"(?ms)^    def " + re.escape(name) + r"\(.*?(?=^    def |\Z)")
    if not pat.search(src):
        return src, False
    return pat.sub(new_body + "\n", src, count=1), True


def main():
    if not os.path.exists(Q3):
        sys.exit(f"[FATAL] {Q3} not found — run from the repo root.")
    src = open(Q3, encoding="utf-8").read()
    if "_chunk_filter" in src and "chunk_ids=None" in src:
        print("Already patched — nothing to do."); return
    n = 0
    src, ok1 = replace_method(src, "_get_semantic_text_with_ids", NEW_SEM); n += ok1
    src, ok2 = replace_method(src, "_get_isolated_subgraph", NEW_ISO); n += ok2
    if n != 2:
        sys.exit(f"[FATAL] matched {n}/2 methods — NOT written. Paste me the current Q3 and I'll adjust "
                 f"(_get_semantic_text_with_ids ok={ok1}, _get_isolated_subgraph ok={ok2}).")
    shutil.copy2(Q3, Q3 + ".bak")
    with open(Q3, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print(f"[OK] patched {Q3} (2/2 methods). Backup: {Q3}.bak")
    print("     verify: python -c \"import ast; ast.parse(open(r'%s',encoding='utf-8').read()); print('Q3 parses clean')\"" % Q3)


if __name__ == "__main__":
    main()
