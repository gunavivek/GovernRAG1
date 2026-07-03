#!/usr/bin/env python3
"""
ABL2_Verdict_Grader.py
======================
Compares v8 baseline outputs (preserved in analysis_dropzone/) against
the Q5-ablated outputs (produced in ablation_dropzone/<rid>/output/ by ABL1)
and grades each case heuristically. Produces the §6.2 comparison artefacts.

Does NOT touch frozen code or Code-Freeze/output/. File-reader only.

INPUTS (read-only):
  analysis_dropzone/run_*/e/MASTER_EVALUATION_LOG.csv   (v8 verdicts)
  ablation_dropzone/<record_id>/output/Q6_final_answers.jsonl

OUTPUTS:
  ablation_dropzone/ABLATION_COMPARISON.csv
  ablation_dropzone/ABLATION_REPORT.md

USAGE
-----
  python ./Ablation/ABL2_Verdict_Grader.py
"""

import os
import sys
import json
import csv
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GOVRAG_ROOT = SCRIPT_DIR.parent
ANALYSIS_DROPZONE = GOVRAG_ROOT / "analysis_dropzone"
ABLATION_DROPZONE = GOVRAG_ROOT / "ablation_dropzone"

GROUND_TRUTH = {
    "rgb_3_P":   ("defensive coordinator",   "Sport / Bio"),
    "rgb_3_N":   ("defensive coordinator",   "Sport / Bio"),
    "rgb_5_P":   ("EVO Entertainment Group", "M&A / Entertainment"),
    "rgb_5_N":   ("EVO Entertainment Group", "M&A / Entertainment"),
    "rgb_12_P":  ("$68.7 billion",           "Tech Acquisition"),
    "rgb_12_N":  ("$68.7 billion",           "Tech Acquisition"),
    "rgb_48_P":  ("Elon Musk",               "Twitter / Musk"),
    "rgb_48_N":  ("Elon Musk",               "Twitter / Musk"),
    "rgb_104_P": ("ColdQuanta",              "Quantum / M&A"),
    "rgb_104_N": ("ColdQuanta",              "Quantum / M&A"),
}


def normalize(s):
    return re.sub(r"[^\w\s]", "", (s or "").lower()).strip()


def grade_ablation_answer(record_id, ablation_record, condition):
    answer = ablation_record.get("generated_answer", "")
    mode = ablation_record.get("mode", "")
    truth, _domain = GROUND_TRUTH.get(record_id, ("", ""))

    norm_answer = normalize(answer)
    norm_truth = normalize(truth)

    refused = ("governance boundary" in norm_answer or
               "evidence insufficient" in norm_answer or
               "response blocked" in norm_answer or
               mode == "BLOCKED_BY_Q5_AUDIT")

    has_citation = bool(re.search(r"\[(?:CHNK_[^\]]+|RESIDUAL_[^\]]+)\]", answer))
    truth_in_answer = norm_truth in norm_answer if norm_truth else False

    if refused:
        if condition == "P":
            return ("FAILURE (Over-Strict Refusal)", "Refused on positive evidence")
        return ("SUCCESS (Boundary Maintained)", "Refused on negative evidence")

    if truth_in_answer and has_citation:
        if condition == "P":
            return ("SUCCESS (Accurate Retrieval)", "Truth-matched + cited")
        return ("FAILURE (Parametric Leakage)", "Truth-matched on N-condition with citations")

    if truth_in_answer and not has_citation:
        return ("UNCLEAR (Human Review)", "Truth-matched without citation — check manually")

    if not truth_in_answer:
        return ("FAILURE (Contextual Bleeding)", "Wrong content from retrieved chunks")

    return ("UNCLEAR (Human Review)", "Heuristic could not assign")


def load_baseline_verdicts():
    csvs = sorted(ANALYSIS_DROPZONE.glob("run_*/e/MASTER_EVALUATION_LOG.csv"), reverse=True)
    if not csvs:
        return {}
    latest = csvs[0]
    print(f"[INFO] v8 baseline verdicts read from {latest.relative_to(GOVRAG_ROOT)}")
    verdicts = {}
    with open(latest, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = row["Record_ID"].strip().lower()
            verdicts[rid] = {
                "naive_verdict": row["Naive_Verdict"],
                "naive_answer": row["Naive_Answer"],
                "govrag_verdict_v8": row["GovRAG_Verdict"],
                "govrag_answer_v8": row["GovRAG_Answer"],
            }
    return verdicts


def main():
    print("=" * 80)
    print("  ABL2: Ablation Verdict Grader")
    print("=" * 80)

    if not ABLATION_DROPZONE.exists():
        print(f"[FATAL] No ablation_dropzone/ at {ABLATION_DROPZONE}. Run ABL1 first.")
        sys.exit(1)

    baseline = load_baseline_verdicts()
    rows = []

    for record_id in sorted(GROUND_TRUTH.keys()):
        condition = record_id.split("_")[-1]
        ablation_q6 = ABLATION_DROPZONE / record_id / "output" / "Q6_final_answers.jsonl"
        if not ablation_q6.exists():
            print(f"[WARN] No ablation output for {record_id} at {ablation_q6.relative_to(GOVRAG_ROOT)}")
            continue
        with open(ablation_q6, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    ablation = json.loads(line)
                    break

        verdict, reason = grade_ablation_answer(record_id, ablation, condition)
        bkey = record_id.lower()
        baseline_row = baseline.get(bkey, {})

        rows.append({
            "record_id": record_id,
            "condition": condition,
            "ground_truth": GROUND_TRUTH[record_id][0],
            "naive_verdict": baseline_row.get("naive_verdict", "?"),
            "govrag_v8_verdict": baseline_row.get("govrag_verdict_v8", "?"),
            "govrag_ablated_verdict": verdict,
            "govrag_ablated_reason": reason,
            "govrag_ablated_answer": (ablation.get("generated_answer", "") or "")[:300],
        })

    if not rows:
        print("[FATAL] No ablated cases found. Did ABL1 complete successfully?")
        sys.exit(1)

    csv_path = ABLATION_DROPZONE / "ABLATION_COMPARISON.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[OK] Wrote {csv_path.relative_to(GOVRAG_ROOT)}")

    md_path = ABLATION_DROPZONE / "ABLATION_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Q5 Ablation Report — v8 Baseline vs Q5-Disabled\n\n")
        f.write("**Ablation pipeline:** `Q5_Gov_Context_Router_Ablated.GovContextRouterAblated`\n")
        f.write("**DP3 (predicate enforcement) disabled.** All upstream artifacts "
                "(D5, M5, Q3) held constant via re-staging from `analysis_dropzone/`.\n")
        f.write("**Frozen Q6 invoked unchanged** on the ablated Q5 output.\n")
        f.write("**Code-Freeze/output/ was not modified** by the ablation pipeline.\n\n")

        f.write("## Comparison table\n\n")
        f.write("| Case | Naive | GovRAG v8 | GovRAG (Q5 ablated) | Heuristic verdict |\n")
        f.write("|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['record_id']} | {r['naive_verdict']} | "
                    f"{r['govrag_v8_verdict']} | {r['govrag_ablated_verdict']} | "
                    f"{r['govrag_ablated_reason']} |\n")

        v8_wins = sum(1 for r in rows if r['condition'] == 'N'
                      and 'Boundary Maintained' in r['govrag_v8_verdict'])
        abl_wins = sum(1 for r in rows if r['condition'] == 'N'
                       and 'Boundary Maintained' in r['govrag_ablated_verdict'])
        f.write(f"\n## Architectural-win count on negative-condition cases (n=5)\n\n")
        f.write(f"- **v8 baseline:** {v8_wins}/5\n")
        f.write(f"- **Q5-ablated:** {abl_wins}/5\n")
        f.write(f"- **Delta:** {v8_wins - abl_wins} architectural-win cases flip when DP3 disabled.\n\n")

        f.write("## Ablated answers (for manual review)\n\n")
        for r in rows:
            f.write(f"### {r['record_id']} ({r['condition']}-condition)\n")
            f.write(f"- **Ground truth:** `{r['ground_truth']}`\n")
            f.write(f"- **Ablated answer:** {r['govrag_ablated_answer']}\n")
            f.write(f"- **Heuristic verdict:** {r['govrag_ablated_verdict']} — {r['govrag_ablated_reason']}\n\n")

    print(f"[OK] Wrote {md_path.relative_to(GOVRAG_ROOT)}")
    print()
    print("Console summary:")
    print("-" * 80)
    for r in rows:
        flip = " <-- FLIP" if r['govrag_v8_verdict'] != r['govrag_ablated_verdict'] else ""
        print(f"  {r['record_id']:12s}  v8: {r['govrag_v8_verdict']:42s}  "
              f"abl: {r['govrag_ablated_verdict']:40s}{flip}")
    print()
    print("Next: hand-check any UNCLEAR rows, then send ABLATION_REPORT.md back to Claude.")


if __name__ == "__main__":
    main()
