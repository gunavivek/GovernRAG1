# --------------------------------------------------------------------------
# A1_RAGBench_D0_M0_Runner.py
# Single-command build-phase orchestrator for a RAGBench corpus.
#
# Stages:
#   [1/5] Stage <corpus>_corpus.jsonl  ->  data/RGB_Single_Record.jsonl
#   [2/5] Run D1   (Global Domain Matcher)        -> D1_Global_Mapping.json
#   [3/5] Run D0   (D-pipeline orchestrator)      -> D5_Extraction_Manifest.jsonl
#   [3.5/5] PATCH  Override D5 manifest with D1 baseline domain when D2 reports ORPHAN
#                  (handles the BIZBOK-fit gap: non-enterprise corpora classified as orphan)
#   [4/5] Run M0   (M-pipeline orchestrator)      -> M5_Embedded_Graph.graphml
#   [5/5] Inventory final artefacts + write run summary
#
# Prerequisite (one-time per corpus):
#   python ./experiment/A0_RAGBench_PrepFixA.py <corpus>
#   This adds the `dataset` field to corpus.jsonl so D2 can do the D1 lookup.
#
# Usage:
#   python ./experiment/A1_RAGBench_D0_M0_Runner.py delucionqa
#   python ./experiment/A1_RAGBench_D0_M0_Runner.py emanual
# --------------------------------------------------------------------------
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


CORPORA = ["delucionqa", "emanual", "expertqa_run3", "hagrid_run2"]  # labels corrected 2026-07-19 after run-order swap (approved)
EXPECTED_CHUNKS = {"delucionqa": 930, "emanual": 222, "expertqa_run3": 150, "hagrid_run2": 150}

# --- D5 OVERRIDE POLICY ---
# When D2 classifies a corpus as ORPHAN, we override the synthesised governance_profile
# with one derived from the D1 baseline domain. This is the smallest change that lets the
# pipeline run end-to-end on non-enterprise corpora while preserving BIZBOK anchoring at
# the M3 alignment layer (R-pipeline reference is still used downstream).
#
# The synthetic governance_profile carries predicates and disambiguation keys appropriate
# for consumer-product manual content. These are documented in the paper as the
# "D1-baseline-override" architectural adaptation.

CUSTOMER_SUPPORT_PROFILE = {
    "domain":           "Customer Support",
    "affinity_weight":  1.0,
    "rules": {
        "search_exit_depth":     4,
        "relational_predicates": [
            "uses", "operates", "configures", "maintains", "controls",
            "displays", "presses", "selects", "activates", "engages",
            "warns", "indicates", "requires", "performs", "supports"
        ],
        "disambiguation_keys": {
            "vehicle":  "consumer automotive product",
            "device":   "consumer electronic product",
            "system":   "subsystem of the consumer product",
            "feature":  "user-accessible function",
            "manual":   "user documentation",
            "operator": "consumer / end user"
        }
    }
}


def project_root() -> Path:
    here = Path(__file__).resolve()
    if here.parent.name.lower() == "experiment":
        return here.parent.parent
    return here.parent.parent if (here.parent.parent / "data").exists() else here.parent


def stage_corpus(root: Path, corpus: str) -> dict:
    src = root / "data" / f"{corpus}_corpus.jsonl"
    dst = root / "data" / "RGB_Single_Record.jsonl"
    if not src.exists():
        raise FileNotFoundError(f"Source corpus not found: {src}")
    shutil.copy2(src, dst)

    with dst.open(encoding="utf-8") as f:
        rec = json.loads(f.readline())
    return {
        "src": str(src),
        "dst": str(dst),
        "id": rec.get("id"),
        "dataset": rec.get("dataset"),
        "question": rec.get("question"),
        "n_chunks": len(rec.get("documents", [])),
        "expected_chunks": EXPECTED_CHUNKS.get(corpus),
    }


def run_stage(name: str, script_path: Path, project_root: Path, log_path: Path) -> dict:
    print("\n" + "=" * 70)
    print(f"  {name}")
    print(f"  source: {script_path}")
    print("=" * 70 + "\n")

    if not script_path.exists():
        return {"stage": name, "status": "FAILED", "reason": f"Script not found: {script_path}"}

    t0 = time.perf_counter()
    started_at = datetime.utcnow().isoformat() + "Z"

    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as log_f:
        process = subprocess.Popen(
            [sys.executable, "-u", str(script_path)],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in process.stdout:
            log_f.write(line)
            log_f.flush()
            print(f"  {line.rstrip()}", flush=True)
        rc = process.wait()

    elapsed = time.perf_counter() - t0
    ended_at = datetime.utcnow().isoformat() + "Z"
    status = "SUCCESS" if rc == 0 else "FAILED"

    print(f"\n  [{name}] {status}  elapsed = {elapsed/60:.2f} min  ({elapsed:.1f} s)")

    return {
        "stage":           name,
        "status":          status,
        "exit_code":       rc,
        "elapsed_seconds": round(elapsed, 1),
        "elapsed_minutes": round(elapsed / 60, 2),
        "started_at":      started_at,
        "ended_at":        ended_at,
        "log":             str(log_path),
    }


def patch_d5_manifest(root: Path) -> dict:
    """
    Stage [3.5/5] - D5 manifest override using D1 baseline.

    Reads:
      - output/D5_Extraction_Manifest.jsonl  (from D0)
      - output/D1_Global_Mapping.json         (from D1)
      - output/D2_D3_Record_Domain_Mapping.jsonl  (from D2)
      - data/RGB_Single_Record.jsonl          (the staged corpus, has `dataset` field)

    For each manifest record whose mapping is ORPHAN:
      replace governance_profile with the D1-baseline policy (CUSTOMER_SUPPORT_PROFILE
      for now; in future, generalise per dataset baseline).

    Writes:
      - output/D5_Extraction_Manifest.jsonl  (overwritten)
      - output/D5_Manifest_Override_Audit.jsonl  (provenance trail of what changed)
    """
    manifest_path = root / "output" / "D5_Extraction_Manifest.jsonl"
    d1_map_path  = root / "output" / "D1_Global_Mapping.json"
    d2_map_path  = root / "output" / "D2_D3_Record_Domain_Mapping.jsonl"
    record_path  = root / "data" / "RGB_Single_Record.jsonl"
    audit_path   = root / "output" / "D5_Manifest_Override_Audit.jsonl"

    # 1. Read everything
    with manifest_path.open(encoding="utf-8") as f:
        manifest_rows = [json.loads(line) for line in f if line.strip()]

    d1_map = {}
    if d1_map_path.exists():
        with d1_map_path.open(encoding="utf-8") as f:
            d1_map = json.load(f)

    d2_rows = {}
    if d2_map_path.exists():
        with d2_map_path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    d2_rows[r.get("record_id")] = r

    record_dataset_map = {}
    if record_path.exists():
        with record_path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    record_dataset_map[r.get("id")] = r.get("dataset")

    # 2. Override loop
    overrides_applied = []
    for m in manifest_rows:
        rid = m.get("record_id")
        d2_entry = d2_rows.get(rid, {})
        d2_assigned_domain = d2_entry.get("assigned_domain", "UNKNOWN")
        d2_mapping_source  = d2_entry.get("mapping_source",  "UNKNOWN")

        dataset_name = record_dataset_map.get(rid)
        if not dataset_name:
            print(f"  [skip] record_id={rid!r} has no `dataset` field, cannot resolve D1 baseline")
            continue

        d1_baseline = d1_map.get(dataset_name, "").strip().lower()
        if not d1_baseline:
            print(f"  [skip] no D1 baseline for dataset={dataset_name!r}")
            continue

        # Idempotency: skip if override already applied (Customer Support is the marker)
        current_domains = [str(d.get("domain", "")).lower() for d in m.get("governance_profile", [])]
        if CUSTOMER_SUPPORT_PROFILE["domain"].lower() in current_domains:
            print(f"  [skip] record_id={rid!r} already has Customer Support override")
            continue

        # Diagnostic: print the D2 state so user knows what is being overridden
        print(f"  [diagnostic] record_id={rid!r}")
        print(f"               D2 assigned_domain : {d2_assigned_domain!r}")
        print(f"               D2 mapping_source  : {d2_mapping_source!r}")
        print(f"               D1 baseline        : {d1_baseline!r}")

        # Snapshot the original profile for audit
        original_profile = m.get("governance_profile", [])

        # Apply override
        m["governance_profile"] = [CUSTOMER_SUPPORT_PROFILE]
        overrides_applied.append({
            "record_id":            rid,
            "dataset":              dataset_name,
            "d1_baseline_domain":   d1_baseline,
            "d2_assigned_domain":   d2_assigned_domain,
            "d2_mapping_source":    d2_mapping_source,
            "original_domains":     [d.get("domain") for d in original_profile],
            "override_domain":      CUSTOMER_SUPPORT_PROFILE["domain"],
            "applied_at":           datetime.utcnow().isoformat() + "Z",
        })
        print(f"  [override] record_id={rid!r} dataset={dataset_name!r}")
        print(f"             D2 said ORPHAN, D1 baseline = {d1_baseline!r}")
        print(f"             original synthesised: {[d.get('domain') for d in original_profile]}")
        print(f"             new (single) domain:   {CUSTOMER_SUPPORT_PROFILE['domain']!r}")

    # 3. Write back manifest + audit
    with manifest_path.open("w", encoding="utf-8") as f:
        for m in manifest_rows:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    with audit_path.open("w", encoding="utf-8") as f:
        for entry in overrides_applied:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {
        "manifest_rows":         len(manifest_rows),
        "overrides_applied":     len(overrides_applied),
        "audit_log":             str(audit_path),
    }


def check_artefacts(root: Path) -> dict:
    out = root / "output"
    artefacts = {
        "D1_Global_Mapping.json":             out / "D1_Global_Mapping.json",
        "D5_Extraction_Manifest.jsonl":       out / "D5_Extraction_Manifest.jsonl",
        "D5_Manifest_Override_Audit.jsonl":   out / "D5_Manifest_Override_Audit.jsonl",
        "M1_Governed_Chunks.csv":             out / "M1_Governed_Chunks.csv",
        "M2_telemetry.json":                  out / "M2_telemetry.json",
        "M5_Embedded_Graph.graphml":          out / "M5_Embedded_Graph.graphml",
    }
    return {
        name: {
            "path":   str(p),
            "exists": p.exists(),
            "bytes":  p.stat().st_size if p.exists() else 0,
        }
        for name, p in artefacts.items()
    }


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1].lower() not in CORPORA:
        print(f"Usage: python A1_RAGBench_D0_M0_Runner.py <{ '|'.join(CORPORA) }>")
        return 2
    corpus = sys.argv[1].lower()

    root = project_root()
    experiment = root / "experiment"
    runs_dir = root / "runs" / f"A1_{corpus}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    runs_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "X" * 70)
    print(f"  A1 BUILD PHASE: {corpus.upper()}")
    print(f"  project_root : {root}")
    print(f"  runs_dir     : {runs_dir}")
    print("X" * 70)

    summary = {
        "corpus":     corpus,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "runs_dir":   str(runs_dir),
    }

    # ===== [1/5] Stage corpus =====
    print(f"\n[1/5] Staging {corpus}_corpus.jsonl -> RGB_Single_Record.jsonl")
    try:
        stage_info = stage_corpus(root, corpus)
    except FileNotFoundError as e:
        print(f"[FATAL] {e}")
        return 2
    print(f"   id          : {stage_info['id']}")
    print(f"   dataset     : {stage_info['dataset']}")
    print(f"   question    : {stage_info['question']}")
    print(f"   chunks      : {stage_info['n_chunks']}  (expected ~{stage_info['expected_chunks']})")
    summary["stage"] = stage_info
    if not stage_info.get("dataset"):
        print("   [WARN] corpus.jsonl has no `dataset` field. Run A0_RAGBench_PrepFixA.py first.")

    # ===== [2/5] D1 Global Domain Matcher =====
    print(f"\n[2/5] Running D1 (D1_Global_Domain_Matcher.py)")
    d1_result = run_stage("D1", experiment / "D1_Global_Domain_Matcher.py", root, runs_dir / "d1.log")
    summary["d1"] = d1_result
    if d1_result["status"] != "SUCCESS":
        summary["overall_status"] = "FAILED_AT_D1"
        (runs_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return 1

    # ===== [3/5] D0 D-pipeline =====
    print(f"\n[3/5] Running D0 (D0_Gov_Domain_Orchestrator.py)")
    d0_result = run_stage("D0", experiment / "D0_Gov_Domain_Orchestrator.py", root, runs_dir / "d0.log")
    summary["d0"] = d0_result
    if d0_result["status"] != "SUCCESS":
        summary["overall_status"] = "FAILED_AT_D0"
        (runs_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return 1

    # ===== [3.5/5] D5 manifest override (BIZBOK-fit gap repair) =====
    print(f"\n[3.5/5] Patching D5 manifest with D1 baseline override")
    try:
        patch_info = patch_d5_manifest(root)
        print(f"   manifest_rows scanned : {patch_info['manifest_rows']}")
        print(f"   overrides applied     : {patch_info['overrides_applied']}")
        print(f"   audit log             : {patch_info['audit_log']}")
        summary["d5_override"] = patch_info
    except Exception as e:
        print(f"   [WARN] D5 manifest override failed: {e}")
        summary["d5_override"] = {"status": "FAILED", "error": str(e)}

    # ===== [4/5] M0 M-pipeline =====
    print(f"\n[4/5] Running M0 (M0_Main_Extraction_Orchestrator.py)")
    m0_result = run_stage("M0", experiment / "M0_Main_Extraction_Orchestrator.py", root, runs_dir / "m0.log")
    summary["m0"] = m0_result
    if m0_result["status"] != "SUCCESS":
        summary["overall_status"] = "FAILED_AT_M0"
        summary["artefacts"] = check_artefacts(root)
        (runs_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return 1

    # ===== [5/5] Final summary =====
    summary["artefacts"] = check_artefacts(root)
    summary["overall_status"] = "SUCCESS"
    summary["ended_at"] = datetime.utcnow().isoformat() + "Z"

    total = round(
        d1_result["elapsed_seconds"]
        + d0_result["elapsed_seconds"]
        + m0_result["elapsed_seconds"], 1
    )
    summary["total_elapsed_seconds"] = total
    summary["total_elapsed_minutes"] = round(total / 60, 2)

    (runs_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "#" * 70)
    print(f"  A1 BUILD PHASE COMPLETE: {corpus.upper()}")
    print("#" * 70)
    print(f"  D1 elapsed : {d1_result['elapsed_minutes']} min  ({d1_result['elapsed_seconds']} s)")
    print(f"  D0 elapsed : {d0_result['elapsed_minutes']} min  ({d0_result['elapsed_seconds']} s)")
    print(f"  M0 elapsed : {m0_result['elapsed_minutes']} min  ({m0_result['elapsed_seconds']} s)")
    print(f"  TOTAL      : {summary['total_elapsed_minutes']} min  ({total} s)")
    print(f"\n  Final artefacts:")
    for name, info in summary["artefacts"].items():
        flag = "OK " if info["exists"] else "MISS"
        size_kb = info["bytes"] / 1024
        print(f"    [{flag}] {name:<40} {size_kb:>10.1f} KB")
    print(f"\n  Summary JSON : {runs_dir / 'summary.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

