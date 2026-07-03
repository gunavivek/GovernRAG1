#!/usr/bin/env python3
"""
Z3_Evidence_Append.py
---------------------
Appends one canonical, full-payload JSONL line per run to
output/All_GovRAG_Evidence.jsonl. This is the cumulative paper / dissertation
evidence archive — one line per run with:
  - Run identity (run_id, record_id, condition, timestamps)
  - The question and ground truth
  - Naive RAG answer + judge verdict + verdict outcome
  - GovRAG full payload:
      * answer text
      * mode (SUCCESS_GENERATED | BLOCKED_BY_Q5_AUDIT)
      * audited triplets (the symbolic facts that survived Q5)
      * audited primary chunks (Tier 1 evidence, post-audit)
      * audited residual chunks (Tier 2 evidence, post-audit)
      * gov_ratio
      * audit_metadata (chunk_decision_log, allowed_predicates, dropped counts)
      * full Q6 prompt as sent to the LLM
      * citations_present, triplet_count, etc.
  - Routing decisions (Path A/B, intent classes, k_hops, active domains)

APPEND-ONLY semantics: never overwrites or removes entries. Re-runs of the
same record add NEW lines. Use run_id timestamps to identify the latest
iteration per record_id.

Place at experiment/Z3_Evidence_Append.py.
Runs as the third stage of Z0 (after Z1, Z2; before Z4 so Z4 mirrors the
fresh evidence file to the dropzone).

Usage:
    python experiment/Z3_Evidence_Append.py

Output:
    output/All_GovRAG_Evidence.jsonl   (append-only, one JSONL line per run)
"""
import csv
import json
from datetime import datetime
from pathlib import Path

# Script lives in experiment/; project root is one level up
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "runs"
OUTPUT_DIR = PROJECT_ROOT / "output"
EVIDENCE_FILE = OUTPUT_DIR / "All_GovRAG_Evidence.jsonl"
MASTER_EVAL = OUTPUT_DIR / "MASTER_EVALUATION_LOG.csv"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def find_latest_run() -> Path:
    """Find the most recent run_<id>_<...> folder by modification time."""
    if not RUNS_DIR.exists():
        return None
    candidates = [
        d for d in RUNS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("run_")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_jsonl_first(path: Path) -> dict:
    """Load the first JSONL record in a file as a dict; {} if missing."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    return {}


def load_jsonl_by_record(path: Path, record_id: str) -> dict:
    """Find the JSONL row matching record_id; falls back to first row."""
    if not path.exists():
        return {}
    target = str(record_id).strip().lower()
    first = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if first is None:
                first = data
            if str(data.get("record_id", "")).strip().lower() == target:
                return data
    return first or {}


def load_eval_row(record_id: str) -> dict:
    """Find the row for record_id in MASTER_EVALUATION_LOG.csv."""
    if not MASTER_EVAL.exists():
        return {}
    target = record_id.upper().strip()
    with open(MASTER_EVAL, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("Record_ID", "").upper().strip() == target:
                return row
    return {}


def extract_question_from_d5(d_dir: Path) -> str:
    """Pull the question text out of the D5 manifest captured for the run."""
    d5 = d_dir / "D5_Extraction_Manifest.jsonl"
    data = load_jsonl_first(d5)
    src = data.get("source_text", "")
    if "| Document:" in src:
        return src.split("| Document:", 1)[0].replace("Question:", "").strip()
    return src.replace("Question:", "").strip()


def has_provenance_citations(text: str) -> bool:
    """Match Q6's required citation pattern: [CHNK_...] or [RESIDUAL_...]."""
    if not text:
        return False
    return ("[CHNK_" in text) or ("[RESIDUAL_" in text)


# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
def build_evidence_record(run_dir: Path) -> dict:
    """Compose the full evidence payload for a single run folder."""
    # 1. Manifest — run identity
    manifest_path = run_dir / "manifest" / "run_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest missing in {run_dir}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    record_id = manifest.get("record_id", "")
    if not record_id:
        raise ValueError(f"no record_id in manifest at {run_dir}")

    # 2. Q5 audit packet
    q5 = load_jsonl_by_record(run_dir / "q" / "Q5_routed_context.jsonl", record_id)

    # 3. Q6 final answer
    q6 = load_jsonl_by_record(run_dir / "q" / "Q6_final_answers.jsonl", record_id)

    # 4. Q1 routing decisions
    q1 = load_jsonl_by_record(run_dir / "q" / "Q1_intent_gate.jsonl", record_id)

    # 5. E2 verdicts
    eval_row = load_eval_row(record_id)

    # 6. Question text
    question = extract_question_from_d5(run_dir / "d")

    # 7. Compose
    govrag_answer = q6.get("generated_answer", "")
    audit_meta = q5.get("audit_metadata", {}) or {}

    return {
        "schema_version": "1.0",
        "appended_at": datetime.utcnow().isoformat() + "Z",

        # Run identity
        "run_id": manifest.get("run_id"),
        "record_id": record_id.upper(),
        "condition": "Positive" if manifest.get("flag") == "P" else "Negative",
        "numeric_id": manifest.get("numeric_id"),
        "flag": manifest.get("flag"),
        "started_at": manifest.get("started_at"),
        "ended_at": manifest.get("ended_at"),

        # Question + ground truth
        "question": question,
        "ground_truth": eval_row.get("Ground_Truth", ""),

        # Naive RAG outcome
        "naive": {
            "answer": eval_row.get("Naive_Answer", ""),
            "judge_verdict": eval_row.get("Naive_Eval", ""),
            "outcome": eval_row.get("Naive_Verdict", ""),
        },

        # GovRAG full payload — the architectural-contribution evidence
        "govrag": {
            "answer": govrag_answer,
            "mode": q6.get("mode", ""),
            "judge_verdict": eval_row.get("GovRAG_Eval", ""),
            "outcome": eval_row.get("GovRAG_Verdict", ""),
            "final_prompt": q6.get("final_prompt", ""),

            # Audited evidence (post-Q5 filter)
            "audited_triplets": q5.get("symbolic_triplets", []),
            "audited_primary_chunk": q5.get("semantic_chunk", ""),
            "audited_residuals": q5.get("residual_context", []),

            # Governance metrics
            "gov_ratio": q5.get("gov_ratio", None),
            "audit_metadata": {
                "triplets_dropped": audit_meta.get("triplets_dropped", 0),
                "chunks_dropped": audit_meta.get("chunks_dropped", 0),
                "d5_contract_applied": audit_meta.get("d5_contract_applied", False),
                "allowed_predicates_enforced": audit_meta.get("allowed_predicates_enforced", []),
                "chunk_decision_log": audit_meta.get("chunk_decision_log", []),
            },

            # Provenance compliance
            "citations_present": has_provenance_citations(govrag_answer),
            "triplet_count": (q6.get("metadata", {}) or {}).get("triplet_count", 0),
            "chunks_used": (q6.get("metadata", {}) or {}).get("chunks_used", 0),
            "domains": (q6.get("metadata", {}) or {}).get("domains", []),
        },

        # Routing decisions (Path A/B etc.)
        "routing": {
            "complexity_path": q1.get("complexity_path", ""),
            "primary_intent": q1.get("primary_intent", ""),
            "functional_intent": (q1.get("justification", {}) or {}).get("target_functional_intent", ""),
            "active_domains": (q1.get("governed_context", {}) or {}).get("active_domains", []),
            "k_hops": (q1.get("traversal_parameters", {}) or {}).get("k_hops"),
            "recursive_expansion_enabled": (q1.get("traversal_parameters", {}) or {}).get("recursive_expansion", False),
        },
    }


def append_evidence(record: dict) -> None:
    """Append one record to the evidence file (creates if missing)."""
    EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def count_existing_lines() -> int:
    if not EVIDENCE_FILE.exists():
        return 0
    with open(EVIDENCE_FILE, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def main() -> None:
    print("--- Z3: Evidence Append ---")
    print(f"Target file: {EVIDENCE_FILE}")

    latest = find_latest_run()
    if not latest:
        print("[WARN] No run folders found in runs/. Nothing to append.")
        return

    print(f"Latest run:  {latest.name}")

    try:
        record = build_evidence_record(latest)
    except Exception as e:
        print(f"[ERROR] Could not build evidence record from {latest.name}: {e}")
        raise SystemExit(1)

    pre_count = count_existing_lines()
    append_evidence(record)
    post_count = count_existing_lines()

    # Summary for terminal
    rid = record["record_id"]
    cond = record["condition"]
    mode = record["govrag"]["mode"]
    gr = record["govrag"]["gov_ratio"]
    naive_outcome = record["naive"]["outcome"]
    gov_outcome = record["govrag"]["outcome"]

    print(f"\n--- Z3 Complete ---")
    print(f"   Appended: 1 line for {rid} ({cond})")
    print(f"   File total: {pre_count} -> {post_count} lines")
    print(f"   GovRAG mode:    {mode}")
    print(f"   GR:             {gr}")
    print(f"   Naive outcome:  {naive_outcome}")
    print(f"   GovRAG outcome: {gov_outcome}")


if __name__ == "__main__":
    main()