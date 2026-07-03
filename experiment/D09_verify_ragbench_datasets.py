"""
verify_ragbench_datasets.py
============================
Verification + schema-inspection script for the two single-document RAGBench
sub-corpora that are candidates for the GovRAG pivot away from RGB:

  1. DelucionQA  (Salesforce/DelucionQA)        — Jeep Grand Cherokee owner's manual
  2. Emanual     (RAGBench/emanual via subset)  — Samsung TV manual

Goals
-----
1. Confirm the datasets can be downloaded from Hugging Face Hub.
2. Inspect schema (column names, types, splits).
3. Report record counts and unique-question counts.
4. Validate fields needed for GovRAG pipeline: question, answer, context/source.
5. Show a small random sample so we can eyeball whether the data shape matches
   what the M / Q / E pipelines expect.
6. Optionally write the raw splits to JSONL so downstream M-pipeline code can
   read without re-hitting Hugging Face.

Usage
-----
    pip install datasets huggingface_hub                # one-time
    python verify_ragbench_datasets.py                  # verification only
    python verify_ragbench_datasets.py --export ./data  # also export JSONL

If you need a Hugging Face token (rare for these public datasets but harmless):
    export HUGGINGFACE_HUB_TOKEN=hf_xxx                 # Linux/Mac
    setx HUGGINGFACE_HUB_TOKEN hf_xxx                   # Windows (new shell)

Author: Vivek Gunasekaran
For: GovRAG dissertation pivot — committee response to Dr. Wang feedback
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------
# We deliberately list multiple candidate identifiers per dataset because
# Hugging Face dataset names sometimes shift between mirror repos. The script
# tries each candidate in order and stops on the first successful load.
DATASETS: Dict[str, Dict[str, Any]] = {
    "delucionqa": {
        "label": "DelucionQA (Jeep manual)",
        "candidates": [
            # (repo_id, config_or_subset, split)
            ("Salesforce/DelucionQA", None, None),       # primary
            ("rungalileo/ragbench", "delucionqa", None), # RAGBench mirror
        ],
        "expected_min_records": 100,
        "purpose": "Single-document manual QA — Jeep Grand Cherokee.",
    },
    "emanual": {
        "label": "Emanual (Samsung TV manual)",
        "candidates": [
            ("rungalileo/ragbench", "emanual", None),    # RAGBench primary
            ("emanual/emanual", None, None),             # fallback if it exists
        ],
        "expected_min_records": 100,
        "purpose": "Single-document manual QA — Samsung TV emanual.",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_print(*a, **k):
    print(*a, **k, flush=True)


def _try_import_datasets():
    try:
        from datasets import load_dataset, get_dataset_config_names  # noqa: F401
        return True
    except ImportError:
        _safe_print(
            "[FATAL] The 'datasets' library is not installed.\n"
            "        Install with:  pip install datasets huggingface_hub\n"
        )
        return False


def _attempt_load(repo_id: str, config: Optional[str], split: Optional[str]):
    """Try to load a dataset; return (ok, ds_or_dict, err)."""
    from datasets import load_dataset, get_dataset_config_names

    try:
        # If config not given but the repo has configs, list them so caller knows.
        if config is None:
            try:
                cfgs = get_dataset_config_names(repo_id)
                if cfgs:
                    _safe_print(f"      [info] {repo_id} configs available: {cfgs}")
            except Exception:
                pass

        ds = load_dataset(repo_id, config) if config else load_dataset(repo_id)
        if split and hasattr(ds, "keys") and split in ds:
            return True, ds[split], None
        return True, ds, None
    except Exception as e:
        return False, None, f"{type(e).__name__}: {e}"


def _summarise_split(name: str, ds_split) -> Dict[str, Any]:
    """Return a summary dict for a single split (column names, length, sample)."""
    cols = list(ds_split.column_names)
    n = len(ds_split)
    sample = ds_split[random.randrange(n)] if n else {}
    field_kinds = {}
    for c in cols:
        try:
            v = sample.get(c)
            field_kinds[c] = type(v).__name__ if v is not None else "None"
        except Exception:
            field_kinds[c] = "?"
    return {
        "split": name,
        "n_records": n,
        "columns": cols,
        "field_kinds": field_kinds,
        "sample_keys": list(sample.keys()),
    }


def _detect_qac_fields(columns: List[str]) -> Dict[str, Optional[str]]:
    """
    Heuristic mapping from the dataset columns to GovRAG expected roles:
    question, answer, context (single-doc passages or chunks), id.
    """
    columns_lower = {c.lower(): c for c in columns}

    def pick(*candidates: str) -> Optional[str]:
        for cand in candidates:
            if cand in columns_lower:
                return columns_lower[cand]
        return None

    return {
        "question":  pick("question", "query", "prompt", "input"),
        "answer":    pick("answer", "response", "ground_truth", "target", "output"),
        "context":   pick("context", "documents", "passages", "evidence", "source"),
        "id":        pick("id", "qid", "uid", "example_id"),
    }


def _print_section(title: str):
    bar = "=" * 78
    _safe_print(f"\n{bar}\n  {title}\n{bar}")


def _export_jsonl(ds_split, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in ds_split:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _safe_print(f"      [exported] {out_path}  ({len(ds_split)} records)")


# ---------------------------------------------------------------------------
# Per-dataset verification
# ---------------------------------------------------------------------------
def verify_one(key: str, spec: Dict[str, Any], export_dir: Optional[Path]) -> Dict[str, Any]:
    _print_section(f"{key.upper()} — {spec['label']}")
    _safe_print(f"  purpose: {spec['purpose']}")
    _safe_print(f"  candidates (tried in order):")
    for i, c in enumerate(spec["candidates"], 1):
        _safe_print(f"    {i}. repo={c[0]}  config={c[1]}  split={c[2]}")

    last_err = None
    loaded = None
    used = None
    for repo_id, config, split in spec["candidates"]:
        _safe_print(f"\n  → trying {repo_id} (config={config})")
        ok, ds_or_dict, err = _attempt_load(repo_id, config, split)
        if ok:
            loaded = ds_or_dict
            used = (repo_id, config, split)
            _safe_print(f"      [ok] loaded from {repo_id}")
            break
        else:
            _safe_print(f"      [fail] {err}")
            last_err = err

    if loaded is None:
        _safe_print(f"\n  ✗ All candidates failed for {key}.")
        _safe_print(f"    last error: {last_err}")
        return {"key": key, "status": "FAILED", "error": last_err}

    # Splits
    splits_summary: List[Dict[str, Any]] = []
    if hasattr(loaded, "keys"):  # DatasetDict
        for sp_name in loaded.keys():
            splits_summary.append(_summarise_split(sp_name, loaded[sp_name]))
    else:
        splits_summary.append(_summarise_split("default", loaded))

    total = sum(s["n_records"] for s in splits_summary)
    _safe_print(f"\n  total records across splits: {total}")
    if total < spec["expected_min_records"]:
        _safe_print(
            f"  [warn] Total {total} is below the expected minimum "
            f"{spec['expected_min_records']} — verify this is the right corpus."
        )

    # Print summary per split
    for s in splits_summary:
        _safe_print(f"\n  --- split: {s['split']} ---")
        _safe_print(f"      records   : {s['n_records']}")
        _safe_print(f"      columns   : {s['columns']}")
        _safe_print(f"      field kinds (from sample row):")
        for k, v in s["field_kinds"].items():
            _safe_print(f"        - {k}: {v}")

    # GovRAG field mapping (use first split's columns — assume consistent)
    cols = splits_summary[0]["columns"]
    govrag_map = _detect_qac_fields(cols)
    _safe_print(f"\n  GovRAG field role detection (heuristic):")
    for role, col in govrag_map.items():
        marker = "✓" if col else "✗ (NOT FOUND — review schema)"
        _safe_print(f"    {role:<10} -> {col!s:<22} {marker}")

    # Show one tiny sample (truncate context to keep terminal readable)
    if hasattr(loaded, "keys"):
        first_split_name = next(iter(loaded.keys()))
        sample_row = loaded[first_split_name][0]
    else:
        sample_row = loaded[0]
    _safe_print(f"\n  sample row (truncated):")
    for k, v in sample_row.items():
        s = repr(v)
        if len(s) > 220:
            s = s[:220] + "..."
        _safe_print(f"    {k}: {s}")

    # Export
    exported_files: List[str] = []
    if export_dir is not None:
        if hasattr(loaded, "keys"):
            for sp_name in loaded.keys():
                out = export_dir / f"{key}__{sp_name}.jsonl"
                _export_jsonl(loaded[sp_name], out)
                exported_files.append(str(out))
        else:
            out = export_dir / f"{key}__default.jsonl"
            _export_jsonl(loaded, out)
            exported_files.append(str(out))

    return {
        "key": key,
        "status": "OK",
        "used_repo": used[0],
        "used_config": used[1],
        "splits": splits_summary,
        "govrag_field_map": govrag_map,
        "exported": exported_files,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verify DelucionQA + Emanual datasets.")
    ap.add_argument("--export", type=str, default=None,
                    help="If given, export each split as JSONL into this directory.")
    ap.add_argument("--only", type=str, default=None,
                    help="Run for one dataset key only: 'delucionqa' or 'emanual'.")
    args = ap.parse_args(argv)

    if not _try_import_datasets():
        return 2

    random.seed(42)
    export_dir = Path(args.export) if args.export else None

    selected = list(DATASETS.keys())
    if args.only:
        if args.only not in DATASETS:
            _safe_print(f"[fatal] unknown --only value: {args.only}")
            return 2
        selected = [args.only]

    results = []
    for key in selected:
        try:
            r = verify_one(key, DATASETS[key], export_dir)
        except Exception as e:
            r = {"key": key, "status": "EXCEPTION", "error": f"{type(e).__name__}: {e}"}
        results.append(r)

    # Final report
    _print_section("FINAL VERIFICATION REPORT")
    for r in results:
        _safe_print(f"  {r['key']:<12} {r['status']}")
        if r.get("status") == "OK":
            _safe_print(f"      repo  : {r['used_repo']}  (config={r.get('used_config')})")
            for s in r["splits"]:
                _safe_print(f"      split : {s['split']:<12} n={s['n_records']}  cols={s['columns']}")
            roles = r["govrag_field_map"]
            missing = [k for k, v in roles.items() if v is None]
            if missing:
                _safe_print(f"      [warn] missing GovRAG roles: {missing}")
            else:
                _safe_print(f"      [ok] all GovRAG roles mapped: {roles}")
        else:
            _safe_print(f"      error : {r.get('error')}")

    ok_count = sum(1 for r in results if r["status"] == "OK")
    _safe_print(f"\n  → {ok_count}/{len(results)} datasets verified successfully.")
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
