#!/usr/bin/env python3
"""
Z2_DECISION_TRACE.py
-----------------
Walks every runs/<run_id>/ folder and emits one row per record summarizing
which governance MECHANISMS activated. Useful when reviewers ask:
  "How often did the BIZBOK statistical anchor fire?"
  "How often did Q3.5 trigger recursive bridge expansion?"
  "How often did Q5 BLOCK the answer?"

Produces a per-run trace combining D-pipeline activations, Q3.5 audit results,
Q5 governance audit, and Q6 final mode.

Place at project root (sibling of A0_GovRAG_Runner.py, runs/, output/).

Usage:
    python Z2_DECISION_TRACE.py

Output:
    runs/Z2_DECISION_TRACE.csv
"""
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "runs"
OUT_FILE = RUNS_DIR / "Z2_DECISION_TRACE.csv"


def load_jsonl(path: Path) -> list:
    """Load a JSONL file into a list of dicts; tolerant of missing files."""
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def first_match(rows: list, key: str, val: str) -> dict:
    """Return the first row whose key matches val (case-insensitive, stripped)."""
    target = str(val).strip().lower()
    for r in rows:
        if str(r.get(key, "")).strip().lower() == target:
            return r
    return {}


def trace_run(run_dir: Path) -> dict:
    """Build one decision-trace row for a single run folder."""
    # 1. Identify the record_id from the manifest (most reliable source)
    rid = ""
    manifest_path = run_dir / "manifest" / "run_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        rid = manifest.get("record_id", "")

    # 2. D-pipeline decisions: read D5 manifest from this run's d/ snapshot
    d5_rows = load_jsonl(run_dir / "d" / "D5_Extraction_Manifest.jsonl")
    d5 = first_match(d5_rows, "record_id", rid)
    z_score = d5.get("z_score", None)
    profile = d5.get("governance_profile", []) or []
    n_domains = len(profile)
    # Heuristic: >1 domain in the manifest implies D3 affinity weighting fired
    d3_fired = n_domains > 1
    primary_domain = profile[0].get("domain", "") if profile else ""
    primary_wa = profile[0].get("affinity_weight", "") if profile else ""

    # 3. Q3.5 bridge-discovery audit
    q35_rows = load_jsonl(run_dir / "q" / "Q3_5_bridge_entities.jsonl")
    q35 = first_match(q35_rows, "record_id", rid)
    bridge_status = q35.get("status", "")
    bridge_count = len(q35.get("bridge_entities", []) or [])
    has_gap = q35.get("has_relational_gap", None)

    # 4. Q5 governance audit (gov_ratio, dropped triplets/chunks, predicate count)
    q5_rows = load_jsonl(run_dir / "q" / "Q5_routed_context.jsonl")
    q5 = first_match(q5_rows, "record_id", rid)
    gr = q5.get("gov_ratio", None)
    audit = q5.get("audit_metadata", {}) or {}
    triplets_dropped = audit.get("triplets_dropped", 0)
    chunks_dropped = audit.get("chunks_dropped", 0)
    n_predicates = len(audit.get("allowed_predicates_enforced", []) or [])
    contract_applied = audit.get("d5_contract_applied", None)

    # 5. Q6 final synthesis mode (SUCCESS_GENERATED vs BLOCKED_BY_Q5_AUDIT)
    q6_rows = load_jsonl(run_dir / "q" / "Q6_final_answers.jsonl")
    q6 = first_match(q6_rows, "record_id", rid)
    mode = q6.get("mode", "")
    triplet_count = (q6.get("metadata", {}) or {}).get("triplet_count", "")

    return {
        # Identity
        "Record_ID": rid.upper(),
        "Run_ID": run_dir.name,
        # D-pipeline
        "D2_Z_Score": z_score,
        "D3_Fired": d3_fired,
        "Active_Domains": n_domains,
        "Primary_Domain": primary_domain,
        "Primary_Wa": primary_wa,
        # Q3.5 bridge audit
        "Q3_5_Status": bridge_status,
        "Q3_5_Has_Gap": has_gap,
        "Q3_5_Bridge_Count": bridge_count,
        # Q5 audit
        "Q5_D5_Contract_Applied": contract_applied,
        "Q5_Gov_Ratio": gr,
        "Q5_Triplets_Dropped": triplets_dropped,
        "Q5_Chunks_Dropped": chunks_dropped,
        "Q5_Authorized_Predicates": n_predicates,
        # Q6 outcome
        "Q6_Mode": mode,
        "Q6_Triplet_Count": triplet_count,
    }


def main() -> None:
    if not RUNS_DIR.exists():
        print(f"[ERROR] {RUNS_DIR} not found.")
        return

    rows = []
    for run_dir in sorted(RUNS_DIR.iterdir()):
        if not run_dir.is_dir() or not run_dir.name.startswith("run_"):
            continue
        try:
            rows.append(trace_run(run_dir))
        except Exception as e:
            print(f"[WARN] Could not trace {run_dir.name}: {e}")

    if not rows:
        print("[WARN] No run folders found.")
        return

    fieldnames = list(rows[0].keys())
    with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Quick summary at the end for sanity checks
    blocked = sum(1 for r in rows if r["Q6_Mode"] == "BLOCKED_BY_Q5_AUDIT")
    bridge_required = sum(1 for r in rows if r["Q3_5_Status"] == "BRIDGE_REQUIRED")
    d3_fired = sum(1 for r in rows if r["D3_Fired"])

    print(f"[OK] Decision trace written: {OUT_FILE}")
    print(f"     Total runs traced: {len(rows)}")
    print(f"     Q5 BLOCKED:        {blocked} ({100*blocked/len(rows):.0f}%)")
    print(f"     Q3.5 BRIDGE_REQUIRED: {bridge_required} ({100*bridge_required/len(rows):.0f}%)")
    print(f"     D3 fired (>1 domain): {d3_fired} ({100*d3_fired/len(rows):.0f}%)")


if __name__ == "__main__":
    main()