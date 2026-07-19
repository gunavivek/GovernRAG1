#!/usr/bin/env python3
"""
serve_map_questions_to_chunks.py  --  Sprint 2 enabler (design A), SUBSTRING method.

Maps each RAGBench question -> the pipeline chunk_ids of its own documents, so the
serve loop scopes retrieval per question (design A). M1 concatenated the docs and
re-chunked them (930 -> 5,037) with no source-doc boundary, so we match by VERBATIM
SUBSTRING CONTAINMENT: a chunk belongs to a document if the (whitespace-normalized)
chunk text is contained in the (normalized) document text. This is the corrected,
selective method (~38 chunks/question), not the earlier token-overlap one.

RUN LOCALLY (build is done — no Colab needed), from the repo root:
  python serve_map_questions_to_chunks.py --records "C:\\Users\\gunav\\Downloads\\delucionqa_records.csv"

INPUTS
  output/M1_Governed_Chunks.csv            (record_id, chunk_id, chunk_text)
  --records <delucionqa_records.csv>       (idx, question, n_docs, documents_joined)
OUTPUT
  output/serve_question_chunk_map.jsonl    one row/question: {idx, question, chunk_ids}
  + coverage report to stdout
"""
import argparse, csv, json, re, sys
from pathlib import Path

csv.field_size_limit(10_000_000)


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "output").exists():
            return p
    return start


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True, help="delucionqa_records.csv")
    ap.add_argument("--m1", default=None, help="M1_Governed_Chunks.csv (default output/M1_Governed_Chunks.csv)")
    ap.add_argument("--sep", default=" ||| ", help="documents_joined separator")
    ap.add_argument("--min-chars", type=int, default=40, help="ignore chunks shorter than this")
    args = ap.parse_args()

    root = find_root(Path.cwd())
    m1 = Path(args.m1) if args.m1 else root / "output" / "M1_Governed_Chunks.csv"
    if not m1.exists():
        sys.exit("[FATAL] M1 chunks not found: %s (run from the repo root or pass --m1)" % m1)

    # load chunks (normalized), drop tiny fragments that match everything
    chunks = []
    with open(m1, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = norm(row.get("chunk_text", ""))
            if len(t) >= args.min_chars:
                chunks.append((row.get("chunk_id"), t))
    print("chunks (>=%d chars): %d" % (args.min_chars, len(chunks)))

    cache = {}

    def chunks_for_doc(doc):
        # BIDIRECTIONAL containment (2026-07-19, approved): short corpora (e.g. HAGRID wiki
        # passages) yield M1 chunks LARGER than one document, so also match doc-inside-chunk;
        # windowed fallback catches partial boundary overlaps. Deviation-logged before serving.
        d = norm(doc)
        hits = [cid for cid, ct in chunks if ct in d or d in ct]
        if not hits:
            wins = [d[i:i + 120] for i in range(0, max(len(d) - 120, 1), 60)][:8]
            hits = [cid for cid, ct in chunks if any(w in ct for w in wins)]
        return hits

    out = root / "output" / "serve_question_chunk_map.jsonl"
    q_total = q_hit = doc_total = unmapped = 0
    per_q = []
    with open(args.records, encoding="utf-8") as f, out.open("w", encoding="utf-8") as w:
        for row in csv.DictReader(f):
            q_total += 1
            cids = set()
            for doc in [d for d in row.get("documents_joined", "").split(args.sep) if d.strip()]:
                doc_total += 1
                k = doc.strip()
                if k not in cache:
                    cache[k] = chunks_for_doc(doc)
                if cache[k]:
                    cids.update(cache[k])
                else:
                    unmapped += 1
            if cids:
                q_hit += 1
            per_q.append(len(cids))
            w.write(json.dumps({"idx": row.get("idx"), "question": row.get("question"),
                                "chunk_ids": sorted(cids)}) + "\n")

    avg = sum(per_q) / max(len(per_q), 1)
    print("\n===== COVERAGE =====")
    print("questions                       : %d" % q_total)
    print("questions with >=1 chunk mapped : %d (%.1f%%)" % (q_hit, 100 * q_hit / max(q_total, 1)))
    print("avg chunks per question         : %.1f" % avg)
    print("documents with NO chunk match   : %d/%d (%.1f%%)" % (unmapped, doc_total, 100 * unmapped / max(doc_total, 1)))
    print("map written -> %s" % out)
    print("[OK] design-A map ready" if q_hit / max(q_total, 1) >= 0.9
          else "[!] coverage <90% — check --min-chars / inputs")


if __name__ == "__main__":
    main()
