#!/usr/bin/env python3
"""
PAPER_ANALYSIS.py
-----------------
Joins runs/master_runs.csv (A0 governance metrics) with output/MASTER_EVALUATION_LOG.csv
(E2 NaiveRAG-vs-GovRAG verdicts) on Record_ID. Pulls the question text from each run's
captured D5_Extraction_Manifest.jsonl. Produces ONE row per (record, condition) that
becomes the spine of the paper's §6 results table.

Place at project root (sibling of A0_GovRAG_Runner.py, runs/, output/).
Run after one or more A0 runs have completed and E2 has populated MASTER_EVALUATION_LOG.csv.

Usage:
    python PAPER_ANALYSIS.py

Output:
    runs/PAPER_ANALYSIS.csv
"""
import csv
import json
from pathlib import Path

# Project layout (override here if your runner sits elsewhere)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "runs"
OUTPUT_DIR = PROJECT_ROOT / "output"

MASTER_RUNS = RUNS_DIR / "master_runs.csv"
MASTER_EVAL = OUTPUT_DIR / "MASTER_EVALUATION_LOG.csv"
PAPER_ANALYSIS = RUNS_DIR / "Z1_PAPER_ANALYSIS.csv"


def extract_question_from_d5(d_dir: Path) -> str:
    """Pull the question text out of the D5 manifest captured for this run."""
    d5 = d_dir / "D5_Extraction_Manifest.jsonl"
    if not d5.exists():
        return ""
    with open(d5, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            src = data.get("source_text", "")
            if "| Document:" in src:
                return src.split("| Document:", 1)[0].replace("Question:", "").strip()
            return src.replace("Question:", "").strip()
    return ""


def load_eval_log() -> dict:
    """Index MASTER_EVALUATION_LOG.csv by Record_ID (uppercased for stable join)."""
    if not MASTER_EVAL.exists():
        return {}
    eval_map = {}
    with open(MASTER_EVAL, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            eval_map[row["Record_ID"].upper().strip()] = row
    return eval_map


def main() -> None:
    if not MASTER_RUNS.exists():
        print(f"[ERROR] {MASTER_RUNS} not found. Run A0 at least once first.")
        return

    eval_map = load_eval_log()
    if not eval_map:
        print(f"[WARN] {MASTER_EVAL} not found or empty. Output will lack NaiveRAG/GovRAG verdicts.")

    rows_out = []
    with open(MASTER_RUNS, "r", encoding="utf-8") as f:
        for run in csv.DictReader(f):
            rid = run.get("record_id", "").upper().strip()
            eval_row = eval_map.get(rid, {})

            d_dir = Path(run.get("d_artifact_dir", ""))
            question = extract_question_from_d5(d_dir) if d_dir.exists() else ""

            rows_out.append({
                # Identity
                "Record_ID": rid,
                "Run_ID": run.get("run_id", ""),
                "Condition": eval_row.get("Condition", run.get("label", "")),
                # Question + ground truth
                "Question": question,
                "Ground_Truth": eval_row.get("Ground_Truth", ""),
                # Routing decisions
                "Path": run.get("q_path", ""),
                "Primary_Intent": run.get("q_primary_intent", ""),
                "Functional_Intent": run.get("q_functional_intent", ""),
                # NaiveRAG outcome
                "NaiveRAG_Answer": eval_row.get("Naive_Answer", ""),
                "NaiveRAG_Eval": eval_row.get("Naive_Eval", ""),
                "NaiveRAG_Verdict": eval_row.get("Naive_Verdict", ""),
                # GovRAG outcome
                "GovRAG_Answer": eval_row.get("GovRAG_Answer", ""),
                "GovRAG_Eval": eval_row.get("GovRAG_Eval", ""),
                "GovRAG_Verdict": eval_row.get("GovRAG_Verdict", ""),
                "Q_Mode": run.get("q_mode", ""),
                # Governance metrics (from Q5 audit, surfaced by A0)
                "Governance_Ratio": run.get("q_governance_ratio", ""),
                "Triplets_Dropped": run.get("q_triplets_dropped", ""),
                "Chunks_Dropped": run.get("q_chunks_dropped", ""),
                "D5_Contract_Applied": run.get("q_d5_contract_applied", ""),
                "Citations_Present": run.get("q_citations_present", ""),
                # Retrieval volume
                "Triplet_Count": run.get("q_triplet_count", ""),
                "Residual_Hits": run.get("q_residual_hits", ""),
                # Run-level
                "Overall_Status": run.get("overall_status", ""),
                "Q_Seconds": run.get("q_seconds", ""),
                "M_Seconds": run.get("m_seconds", ""),
            })

    if not rows_out:
        print("[WARN] No rows in master_runs.csv to analyze.")
        return

    fieldnames = list(rows_out[0].keys())
    PAPER_ANALYSIS.parent.mkdir(parents=True, exist_ok=True)
    with open(PAPER_ANALYSIS, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"[OK] Wrote {len(rows_out)} rows to {PAPER_ANALYSIS}")
    print(f"     Columns: {', '.join(fieldnames)}")


if __name__ == "__main__":
    main()