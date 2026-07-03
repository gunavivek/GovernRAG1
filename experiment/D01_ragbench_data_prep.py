"""
ragbench_data_prep.py
=====================
One-shot data-prep pipeline for the GovRAG RAGBench pivot.

Takes the DelucionQA and Emanual subsets of galileo-ai/ragbench from
Hugging Face and produces M-pipeline-ready inputs:

  <out_dir>/<dataset>/chunks.jsonl        unique passages with stable chunk_ids
  <out_dir>/<dataset>/questions.jsonl     questions + TRACe gold scores
  <out_dir>/<dataset>/pilot.jsonl         stratified 10-question pilot subset
  <out_dir>/<dataset>/profile.json        corpus statistics

Stable chunk_ids are SHA-1(text)[:12], so re-running the script on a future
release of the dataset yields identical chunk_ids for unchanged passages —
this is the lineage anchor M1.5 needs.

Pilot stratification draws 10 questions across:
  • 5 from the well-supported quartile  (high adherence_score)
  • 3 from the partially-supported half  (mid adherence_score)
  • 2 from the poorly-supported quartile (low adherence_score)

This gives the runtime-estimation pilot a realistic mix of "easy" and
"hallucination-prone" cases — same difficulty distribution as the full sweep.

Usage
-----
    pip install datasets huggingface_hub
    python ragbench_data_prep.py --out ./data
    python ragbench_data_prep.py --out ./data --only delucionqa
    python ragbench_data_prep.py --out ./data --pilot_size 20

Author: Vivek Gunasekaran
For: GovRAG dissertation pivot — Epic 2 implementation prep
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ============================================================================
# Dataset registry (mirrors verify_ragbench_datasets.py)
# ============================================================================
DATASETS: Dict[str, Dict[str, Any]] = {
    "delucionqa": {
        "label":       "DelucionQA (Jeep manual)",
        "candidates":  [
            ("galileo-ai/ragbench", "delucionqa", None),
            ("rungalileo/ragbench", "delucionqa", None),
            ("Salesforce/DelucionQA", None, None),
        ],
        "expected_chunks":   1046,
        "expected_questions": 913,
    },
    "emanual": {
        "label":       "Emanual (Samsung TV manual)",
        "candidates":  [
            ("galileo-ai/ragbench", "emanual", None),
            ("rungalileo/ragbench", "emanual", None),
        ],
        "expected_chunks":   261,
        "expected_questions": 659,
    },
}

# Heuristic field-name detection (RAGBench uses these; original DelucionQA differs)
FIELD_CANDIDATES = {
    "question":   ["question", "query", "prompt", "input"],
    "response":   ["response", "answer", "ground_truth", "target", "output"],
    "documents":  ["documents", "context", "passages", "evidence"],
    "qid":        ["id", "qid", "uid", "example_id"],
    # TRACe gold scores
    "adherence":     ["adherence_score"],
    "relevance":     ["relevance_score"],
    "utilization":   ["utilization_score"],
    "completeness":  ["completeness_score"],
    # Sentence-level annotations (used to compute fine-grained quality)
    "supporting_keys":   ["supporting_sentence_keys", "all_supporting_sentence_keys"],
    "unsupported_keys":  ["unsupported_response_sentence_keys"],
    "relevant_keys":     ["all_relevant_sentence_keys"],
    "utilized_keys":     ["all_utilized_sentence_keys"],
}


# ============================================================================
# Helpers
# ============================================================================
def _log(*a, **k):
    print(*a, **k, flush=True)


def _try_import_datasets() -> bool:
    try:
        from datasets import load_dataset, get_dataset_config_names  # noqa: F401
        return True
    except ImportError:
        _log(
            "[FATAL] The 'datasets' library is not installed.\n"
            "        Install with:  pip install datasets huggingface_hub\n"
        )
        return False


def _attempt_load(repo_id: str, config: Optional[str]):
    """Try to load a dataset; return (DatasetDict_or_None, error_str_or_None)."""
    from datasets import load_dataset
    try:
        ds = load_dataset(repo_id, config) if config else load_dataset(repo_id)
        return ds, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _detect_fields(columns: List[str]) -> Dict[str, Optional[str]]:
    cols_lower = {c.lower(): c for c in columns}
    out: Dict[str, Optional[str]] = {}
    for role, candidates in FIELD_CANDIDATES.items():
        out[role] = next((cols_lower[c] for c in candidates if c in cols_lower), None)
    return out


def _chunk_id(text: str) -> str:
    """Stable chunk identifier — SHA-1 of the passage text, truncated to 12 hex."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _coerce_documents_field(v: Any) -> List[str]:
    """RAGBench's documents field is sometimes a list[str], sometimes a list[dict]."""
    if v is None:
        return []
    if isinstance(v, list):
        out: List[str] = []
        for item in v:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                # try common keys
                for k in ("text", "content", "passage", "document"):
                    if k in item and isinstance(item[k], str):
                        out.append(item[k])
                        break
        return out
    if isinstance(v, str):
        return [v]
    return []


def _safe_get_float(row: Dict[str, Any], col: Optional[str]) -> Optional[float]:
    if col is None or col not in row:
        return None
    v = row[col]
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# ============================================================================
# Per-dataset prep
# ============================================================================
def prep_one(key: str, spec: Dict[str, Any], out_dir: Path,
             pilot_size: int = 10, seed: int = 42) -> Dict[str, Any]:
    _log("=" * 78)
    _log(f"  {key.upper()}  ·  {spec['label']}")
    _log("=" * 78)

    # ---- 1. Load --------------------------------------------------------
    loaded = None
    used_repo = used_cfg = None
    last_err = None
    for repo_id, cfg, _split in spec["candidates"]:
        _log(f"  → load attempt: repo={repo_id} config={cfg}")
        ds, err = _attempt_load(repo_id, cfg)
        if ds is not None:
            loaded = ds
            used_repo, used_cfg = repo_id, cfg
            _log(f"      [ok] loaded from {repo_id}")
            break
        _log(f"      [fail] {err}")
        last_err = err
    if loaded is None:
        _log(f"  ✗ Could not load {key}: {last_err}")
        return {"status": "FAILED", "error": last_err}

    # ---- 2. Iterate over all splits, collect rows -----------------------
    if hasattr(loaded, "keys"):
        all_splits = list(loaded.keys())
    else:
        all_splits = ["default"]
        loaded = {"default": loaded}

    # detect fields from first non-empty split
    sample_split = next(s for s in all_splits if len(loaded[s]) > 0)
    fields = _detect_fields(loaded[sample_split].column_names)
    _log(f"\n  Detected fields:")
    for role, col in fields.items():
        marker = "✓" if col else "—"
        _log(f"    {marker} {role:<18} -> {col}")

    if fields["question"] is None or fields["documents"] is None:
        return {"status": "FAILED",
                "error": f"required fields missing: question={fields['question']} documents={fields['documents']}"}

    # ---- 3. Extract chunks (deduplicated) and questions -----------------
    chunks_by_id: Dict[str, Dict[str, Any]] = {}
    questions: List[Dict[str, Any]] = []
    rows_processed = 0
    rows_skipped = 0

    for split_name in all_splits:
        ds_split = loaded[split_name]
        for i, row in enumerate(ds_split):
            rows_processed += 1
            q_text = row.get(fields["question"]) if fields["question"] else None
            if not q_text or not isinstance(q_text, str):
                rows_skipped += 1
                continue

            doc_texts = _coerce_documents_field(row.get(fields["documents"])) \
                        if fields["documents"] else []

            chunk_ids: List[str] = []
            for txt in doc_texts:
                if not isinstance(txt, str) or not txt.strip():
                    continue
                cid = _chunk_id(txt)
                if cid not in chunks_by_id:
                    chunks_by_id[cid] = {
                        "chunk_id":  cid,
                        "text":      txt,
                        "n_chars":   len(txt),
                        "n_words":   len(txt.split()),
                        "first_seen_split":   split_name,
                        "first_seen_row_idx": i,
                    }
                chunk_ids.append(cid)

            qid_raw = row.get(fields["qid"]) if fields["qid"] else None
            qid = str(qid_raw) if qid_raw is not None else f"{key}__{split_name}__{i}"

            q_record = {
                "qid":          qid,
                "split":        split_name,
                "question":     q_text,
                "response":     row.get(fields["response"]) if fields["response"] else None,
                "chunk_ids":    chunk_ids,
                # TRACe gold scores (None where absent)
                "trace_adherence":    _safe_get_float(row, fields["adherence"]),
                "trace_relevance":    _safe_get_float(row, fields["relevance"]),
                "trace_utilization":  _safe_get_float(row, fields["utilization"]),
                "trace_completeness": _safe_get_float(row, fields["completeness"]),
                # sentence-level annotations (raw, kept for downstream Q5 alignment)
                "supporting_keys":  row.get(fields["supporting_keys"])  if fields["supporting_keys"]  else None,
                "unsupported_keys": row.get(fields["unsupported_keys"]) if fields["unsupported_keys"] else None,
                "relevant_keys":    row.get(fields["relevant_keys"])    if fields["relevant_keys"]    else None,
                "utilized_keys":    row.get(fields["utilized_keys"])    if fields["utilized_keys"]    else None,
            }
            questions.append(q_record)

    _log(f"\n  rows processed: {rows_processed}  · skipped: {rows_skipped}")
    _log(f"  unique chunks  : {len(chunks_by_id)}  (expected ~{spec['expected_chunks']})")
    _log(f"  questions      : {len(questions)}      (expected ~{spec['expected_questions']})")

    # ---- 4. Profile statistics ------------------------------------------
    chunks_per_q = [len(q["chunk_ids"]) for q in questions]
    q_lens_words = [len(q["question"].split()) for q in questions]
    chunk_word_lens = [c["n_words"] for c in chunks_by_id.values()]
    adherence_present = [q["trace_adherence"] for q in questions if q["trace_adherence"] is not None]

    profile = {
        "dataset": key,
        "loaded_from": {"repo": used_repo, "config": used_cfg},
        "splits_available": all_splits,
        "totals": {
            "unique_chunks":   len(chunks_by_id),
            "questions":       len(questions),
            "chunk_word_count_total": sum(chunk_word_lens),
        },
        "chunks_per_question": {
            "min": min(chunks_per_q) if chunks_per_q else 0,
            "median": sorted(chunks_per_q)[len(chunks_per_q)//2] if chunks_per_q else 0,
            "max": max(chunks_per_q) if chunks_per_q else 0,
            "mean": (sum(chunks_per_q)/len(chunks_per_q)) if chunks_per_q else 0,
        },
        "question_word_length": {
            "min": min(q_lens_words) if q_lens_words else 0,
            "median": sorted(q_lens_words)[len(q_lens_words)//2] if q_lens_words else 0,
            "max": max(q_lens_words) if q_lens_words else 0,
        },
        "chunk_word_length": {
            "min": min(chunk_word_lens) if chunk_word_lens else 0,
            "median": sorted(chunk_word_lens)[len(chunk_word_lens)//2] if chunk_word_lens else 0,
            "max": max(chunk_word_lens) if chunk_word_lens else 0,
            "mean": (sum(chunk_word_lens)/len(chunk_word_lens)) if chunk_word_lens else 0,
        },
        "adherence_coverage": {
            "n_with_score": len(adherence_present),
            "n_without_score": len(questions) - len(adherence_present),
            "min": min(adherence_present) if adherence_present else None,
            "median": sorted(adherence_present)[len(adherence_present)//2] if adherence_present else None,
            "max": max(adherence_present) if adherence_present else None,
        },
        "field_mapping": fields,
    }

    # ---- 5. Pilot subset (stratified by adherence_score) ----------------
    rng = random.Random(seed)
    pilot: List[Dict[str, Any]] = []
    if adherence_present:
        scored = [q for q in questions if q["trace_adherence"] is not None]
        scored.sort(key=lambda q: q["trace_adherence"])
        n = len(scored)
        # quartiles
        q1 = scored[: n // 4]
        q2_3 = scored[n // 4 : 3 * n // 4]
        q4 = scored[3 * n // 4 :]
        n_well = max(1, pilot_size // 2)
        n_mid  = max(1, pilot_size * 3 // 10)
        n_poor = pilot_size - n_well - n_mid
        well_supported = rng.sample(q4, k=min(n_well, len(q4)))
        partial_supp   = rng.sample(q2_3, k=min(n_mid, len(q2_3)))
        poor_supp      = rng.sample(q1, k=min(n_poor, len(q1)))
        pilot = well_supported + partial_supp + poor_supp
    else:
        pilot = rng.sample(questions, k=min(pilot_size, len(questions)))
    _log(f"  pilot subset   : {len(pilot)} questions (stratified by adherence)")

    # ---- 6. Write outputs -----------------------------------------------
    ds_out = out_dir / key
    ds_out.mkdir(parents=True, exist_ok=True)

    chunks_path = ds_out / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as f:
        # sorted by chunk_id for deterministic output
        for cid in sorted(chunks_by_id.keys()):
            f.write(json.dumps(chunks_by_id[cid], ensure_ascii=False) + "\n")

    questions_path = ds_out / "questions.jsonl"
    with questions_path.open("w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    pilot_path = ds_out / "pilot.jsonl"
    with pilot_path.open("w", encoding="utf-8") as f:
        for q in pilot:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    profile_path = ds_out / "profile.json"
    with profile_path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    _log(f"\n  outputs:")
    _log(f"    {chunks_path}    ({len(chunks_by_id)} chunks)")
    _log(f"    {questions_path} ({len(questions)} questions)")
    _log(f"    {pilot_path}     ({len(pilot)} pilot questions)")
    _log(f"    {profile_path}")

    return {
        "status": "OK",
        "dataset": key,
        "n_chunks": len(chunks_by_id),
        "n_questions": len(questions),
        "n_pilot": len(pilot),
        "out_dir": str(ds_out),
    }


# ============================================================================
# Main
# ============================================================================
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="GovRAG · RAGBench data prep pipeline.")
    ap.add_argument("--out", type=str, default="./data",
                    help="Output directory (will be created). Default ./data")
    ap.add_argument("--only", type=str, default=None, choices=list(DATASETS.keys()),
                    help="Run on a single dataset.")
    ap.add_argument("--pilot_size", type=int, default=10,
                    help="Number of questions in pilot subset (default 10).")
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for reproducible pilot selection.")
    args = ap.parse_args(argv)

    if not _try_import_datasets():
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = [args.only] if args.only else list(DATASETS.keys())

    results = []
    for key in selected:
        try:
            r = prep_one(key, DATASETS[key], out_dir,
                         pilot_size=args.pilot_size, seed=args.seed)
        except Exception as e:
            r = {"status": "EXCEPTION", "dataset": key,
                 "error": f"{type(e).__name__}: {e}"}
        results.append(r)

    _log("\n" + "=" * 78)
    _log("  FINAL")
    _log("=" * 78)
    for r in results:
        if r.get("status") == "OK":
            _log(f"  {r['dataset']:<12} OK   chunks={r['n_chunks']:5d}  "
                 f"questions={r['n_questions']:5d}  pilot={r['n_pilot']:3d}  "
                 f"out={r['out_dir']}")
        else:
            _log(f"  {r.get('dataset','?'):<12} {r['status']}  {r.get('error','')}")

    ok = sum(1 for r in results if r.get("status") == "OK")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
