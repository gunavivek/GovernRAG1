"""
D03_Derive_Views_From_Parent.py
===============================
Stage 2 of the data-prep pipeline.

Reads the parent JSONL produced by D02 and derives the two views the
downstream pipelines actually consume:

    <corpus>_corpus.jsonl     -- 1 record with all UNIQUE chunks (feeds A1 / D0 / M0)
    <corpus>_questions.jsonl  -- 1 record per UNIQUE question id, INCLUDING
                                 the 'documents' field (its 3 retrieved chunks)
                                 so the join to corpus is verifiable.

After deriving both views, runs an integrity check:
    [A] every chunk referenced by any question is present in corpus
    [B] no orphan chunks in corpus (every corpus chunk is referenced by ≥1 question)
    [C] every question has exactly 3 documents
    [D] every question id is unique in questions.jsonl

If any check fails, the report shows specifically what.

Usage:
    python D03_Derive_Views_From_Parent.py --in_dir ./data --out_dir ./data
    python D03_Derive_Views_From_Parent.py --only delucionqa
"""

import argparse
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path


CORPORA = ["delucionqa", "emanual"]


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def load_parent(parent_path: Path):
    rows = []
    with parent_path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def derive_corpus(parent_rows, corpus: str, out_path: Path) -> tuple[int, set]:
    """Single record with all unique chunks. Returns (n_unique, hashes)."""
    seen_hashes, unique_chunks = OrderedDict(), []
    for row in parent_rows:
        docs = row.get("documents") or []
        if not isinstance(docs, list):
            continue
        for chunk in docs:
            if not isinstance(chunk, str) or not chunk.strip():
                continue
            h = sha1(chunk)
            if h in seen_hashes:
                continue
            seen_hashes[h] = chunk
            unique_chunks.append(chunk)

    record = {
        "id":        f"{corpus.upper()}_CORPUS",
        "question":  "CORPUS_INIT",
        "documents": unique_chunks,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(unique_chunks), set(seen_hashes.keys())


def derive_questions(parent_rows, out_path: Path) -> int:
    """One record per unique question id (dedup the 2× system-response duplication)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for row in parent_rows:
            rid = row.get("id")
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def integrity_check(corpus_hashes: set, questions_path: Path):
    """Run checks A/B/C/D on the derived views."""
    print(f"\n  [INTEGRITY CHECK] {questions_path.name}")

    # Re-load questions
    questions = []
    with questions_path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    n_q = len(questions)

    # [D] uniqueness of question ids
    id_counts = Counter(q.get("id") for q in questions)
    dup_ids = {k: v for k, v in id_counts.items() if v > 1}
    print(f"  [D] unique question ids                      : "
          f"{len(id_counts)} / {n_q}  -> {'PASS' if len(id_counts) == n_q else 'FAIL'}")
    if dup_ids:
        print(f"      duplicates : {list(dup_ids.items())[:3]}")

    # [C] each question has exactly 3 documents
    doc_count_dist = Counter(len(q.get("documents", []) or []) for q in questions)
    n_with_3 = doc_count_dist.get(3, 0)
    print(f"  [C] questions with exactly 3 documents       : "
          f"{n_with_3} / {n_q}  -> {'PASS' if n_with_3 == n_q else 'FAIL'}")
    if n_with_3 != n_q:
        print(f"      doc-count distribution : {dict(doc_count_dist)}")

    # [A] every question chunk hash exists in corpus
    referenced_hashes = set()
    questions_with_missing = []
    for q in questions:
        docs = q.get("documents") or []
        for d in docs:
            if isinstance(d, str):
                referenced_hashes.add(sha1(d))
        # also check this question's chunks
        missing_for_q = [
            sha1(d) for d in docs
            if isinstance(d, str) and sha1(d) not in corpus_hashes
        ]
        if missing_for_q:
            questions_with_missing.append((q.get("id"), missing_for_q))

    missing = referenced_hashes - corpus_hashes
    print(f"  [A] referenced chunks present in corpus      : "
          f"{len(referenced_hashes) - len(missing)} / {len(referenced_hashes)}  "
          f"-> {'PASS' if not missing else 'FAIL'}")
    if missing:
        print(f"      {len(missing)} chunks referenced by questions but NOT in corpus")
        for qid, hs in questions_with_missing[:3]:
            print(f"      e.g. question id={qid!r} missing hashes {hs[:2]}")

    # [B] no orphan chunks in corpus
    orphans = corpus_hashes - referenced_hashes
    print(f"  [B] corpus chunks referenced by ≥1 question  : "
          f"{len(corpus_hashes) - len(orphans)} / {len(corpus_hashes)}  "
          f"-> {'PASS' if not orphans else 'WARN'}")
    if orphans:
        print(f"      {len(orphans)} corpus chunks not referenced by any question")
        print(f"      (this is informational, not a failure)")

    overall = (len(id_counts) == n_q) and (n_with_3 == n_q) and (not missing)
    return overall


def process(corpus: str, in_dir: Path, out_dir: Path) -> bool:
    print(f"\n{'=' * 78}\n  {corpus.upper()}\n{'=' * 78}")
    parent_path = in_dir / f"{corpus}_parent.jsonl"
    if not parent_path.exists():
        print(f"[FATAL] Parent file not found: {parent_path}")
        print(f"        Run D02_RAGBench_Parent_Extractor.py first.")
        return False

    parent_rows = load_parent(parent_path)
    print(f"  loaded parent : {len(parent_rows)} rows")

    corpus_path    = out_dir / f"{corpus}_corpus.jsonl"
    questions_path = out_dir / f"{corpus}_questions.jsonl"

    n_chunks, chunk_hashes = derive_corpus(parent_rows, corpus, corpus_path)
    print(f"  -> {corpus_path}  ({n_chunks} unique chunks)")

    n_questions = derive_questions(parent_rows, questions_path)
    print(f"  -> {questions_path}  ({n_questions} unique questions)")

    return integrity_check(chunk_hashes, questions_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 2: parent JSONL -> corpus + questions views.")
    ap.add_argument("--in_dir",  type=str, default="./data")
    ap.add_argument("--out_dir", type=str, default="./data")
    ap.add_argument("--only",    type=str, default=None, choices=CORPORA)
    args = ap.parse_args()

    in_dir, out_dir = Path(args.in_dir), Path(args.out_dir)
    keys = [args.only] if args.only else CORPORA

    all_pass = True
    for corpus in keys:
        if not process(corpus, in_dir, out_dir):
            all_pass = False

    print(f"\n{'=' * 78}")
    print(f"  OVERALL: {'ALL CHECKS PASSED' if all_pass else 'ONE OR MORE CHECKS FAILED'}")
    print(f"{'=' * 78}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
