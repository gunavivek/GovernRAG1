#!/usr/bin/env python3
"""
A0_GovRAG_Runner
Thin Experiment Runner: D00 -> D0 -> M0 -> Q0 -> E2 -> Z0

Purpose:
- Select exactly one RGB record via D00
- Run frozen D0 -> M0 -> Q0 -> E2 sequentially
- Stop on failure
- Capture logs, selected artifacts, and minimal paper metrics
- Preserve reproducible run manifests, stage snapshots, and JSONL batch index

Place this runner at the project root (same level as data/, output/, experiment/, runs/).

IMPORTANT:
1. Update D00_MODULE_PATH, D0_SCRIPT, M0_SCRIPT, Q0_SCRIPT, E2_SCRIPT to your actual filenames.
2. This runner assumes:
   - D00 is called by import (because current D00 is not CLI-parameterized)
   - D0 consumes the D00 output / prior D artifacts and can be run as a script
   - M0 consumes D outputs and can be run as a script
   - Q0 accepts record_id as a CLI argument
"""

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# -----------------------------------------------------------------------------
# PROJECT PATHS
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT_DIR = PROJECT_ROOT / "experiment"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
RUNS_DIR = PROJECT_ROOT / "runs"

# --- UPDATE THESE FOUR PATHS TO MATCH YOUR ACTUAL FILENAMES ---
D00_MODULE_PATH = EXPERIMENT_DIR / "D00_Data_Extractor.py"
D0_SCRIPT = EXPERIMENT_DIR / "D0_Gov_Domain_Orchestrator.py"
M0_SCRIPT = EXPERIMENT_DIR / "M0_Main_Extraction_Orchestrator.py"
Q0_SCRIPT = EXPERIMENT_DIR / "Q0_Gov_RAG_Orchestrator.py"
E2_SCRIPT = EXPERIMENT_DIR / "E2_Unified_Baseline_and_Eval.py"
# --------------------------------------------------------------

# D00 expected input/output
D00_INPUT_FILE = DATA_DIR / "en_refine.json"
D00_OUTPUT_FILE = DATA_DIR / "RGB_Single_Record.jsonl"

MASTER_SUMMARY = RUNS_DIR / "master_runs.csv"
RUN_INDEX_JSONL = RUNS_DIR / "run_index.jsonl"
SNAPSHOT_SCHEMA_VERSION = "1.0"

# Minimal paper-phase artifact capture
D_ARTIFACTS = [
    OUTPUT_DIR / "D5_Extraction_Manifest.jsonl",
]

M_ARTIFACTS = [
    OUTPUT_DIR / "M1_Governed_Chunks.csv",
    OUTPUT_DIR / "M1_6_Residual_Chunks.csv",
    OUTPUT_DIR / "M5_Embedded_Graph.graphml",
    OUTPUT_DIR / "M2_telemetry.json",
]

Q_ARTIFACTS = [
    OUTPUT_DIR / "Q1_intent_gate.jsonl",
    OUTPUT_DIR / "Q2_signatures.jsonl",
    OUTPUT_DIR / "Q3_retrieved_evidence.jsonl",
    OUTPUT_DIR / "Q3_5_bridge_entities.jsonl",
    OUTPUT_DIR / "Q5_routed_context.jsonl", 
    OUTPUT_DIR / "Q6_final_answers.jsonl", 
]

E_ARTIFACTS = [
    OUTPUT_DIR / "MASTER_EVALUATION_LOG.csv",
]

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def log_runner(message: str) -> None:
    print(message, flush=True)


def load_module_from_path(module_name: str, module_path: Path):
    if not module_path.exists():
        raise FileNotFoundError(f"Module not found: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_copy(src: Path, dst_dir: Path) -> Optional[str]:
    if not src.exists():
        return None
    ensure_dir(dst_dir)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    return str(dst)


def remove_file_if_exists(path: Path) -> None:
    if path.exists() and path.is_file():
        path.unlink()


def unique_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    result = []
    for p in paths:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        result.append(p)
    return result


def clear_run_output_files(paths: list[Path]) -> None:
    for p in unique_paths(paths):
        remove_file_if_exists(p)


def load_jsonl_rows(path: Path) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    if not path.exists():
        return rows

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl_rows(path: Path, rows: list[Dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl_by_record(path: Path, record_id: str) -> Dict[str, Any]:
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            if str(data.get("record_id", "")).strip() == str(record_id).strip():
                return data

    return {}


def normalize_single_d00_row(path: Path, expected_record_id: str) -> Dict[str, Any]:
    rows = load_jsonl_rows(path)
    if not rows:
        return {}

    first_row = rows[0]
    log_runner(f"[RUNNER] D00 first-row keys: {sorted(first_row.keys())}")
    log_runner(f"[RUNNER] D00 first-row record_id: {first_row.get('record_id')}")
    log_runner(f"[RUNNER] D00 first-row id: {first_row.get('id')}")
    log_runner(f"[RUNNER] D00 row count: {len(rows)}")

    existing = read_jsonl_by_record(path, expected_record_id)
    if existing:
        return existing

    if len(rows) == 1 and not str(rows[0].get("record_id", "")).strip():
        rows[0]["record_id"] = expected_record_id
        write_jsonl_rows(path, rows)
        log_runner(f"[RUNNER] Injected missing record_id={expected_record_id} into D00 output")
        return rows[0]

    return {}


def governance_ratio_from_q3(q3_packet: Dict[str, Any]) -> float:
    g_len = len(q3_packet.get("semantic_chunk", "") or "")
    r_len = len(q3_packet.get("residual_context", "") or "")
    return g_len / (g_len + r_len) if (g_len + r_len) > 0 else 1.0


def has_citations(text: str) -> bool:
    return bool(re.search(r"\[(?:CHNK_[^\]]+|RESIDUAL_[^\]]+)\]", text or ""))


def append_master_summary(row: Dict[str, Any]) -> None:
    ensure_dir(RUNS_DIR)
    file_exists = MASTER_SUMMARY.exists()
    fieldnames = list(row.keys())

    with open(MASTER_SUMMARY, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_code_fingerprints() -> Dict[str, Any]:
    targets = {
        "a0_runner": Path(__file__).resolve(),
        "d00_module": D00_MODULE_PATH,
        "d0_script": D0_SCRIPT,
        "m0_script": M0_SCRIPT,
        "q0_script": Q0_SCRIPT,
        "e2_script": E2_SCRIPT,
    }
    return {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
        }
        for name, path in targets.items()
    }


def write_stage_snapshot(snapshot_dir: Path, stage_result: Dict[str, Any]) -> None:
    ensure_dir(snapshot_dir)
    write_json(snapshot_dir / f"{stage_result['stage']}_snapshot.json", stage_result)


def get_d00_output_candidates() -> list[Path]:
    candidates = [
        D00_OUTPUT_FILE,
        PROJECT_ROOT / D00_OUTPUT_FILE.name,
        Path.cwd() / D00_OUTPUT_FILE.name,
    ]
    return unique_paths(candidates)


def normalize_d00_output() -> Optional[Path]:
    expected = D00_OUTPUT_FILE

    if expected.exists():
        return expected

    for candidate in get_d00_output_candidates():
        if candidate == expected:
            continue
        if candidate.exists():
            ensure_dir(expected.parent)
            shutil.move(str(candidate), str(expected))
            return expected

    return None


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


# -----------------------------------------------------------------------------
# STAGE EXECUTION
# -----------------------------------------------------------------------------
def run_subprocess_stage(stage_name: str, cmd: list[str], cwd: Path, log_dir: Path) -> Dict[str, Any]:
    ensure_dir(log_dir)
    stdout_path = log_dir / f"{stage_name.lower()}_stdout.txt"
    stderr_path = log_dir / f"{stage_name.lower()}_stderr.txt"

    start_ts = datetime.utcnow().isoformat() + "Z"
    t0 = time.perf_counter()

    log_runner(f"[RUNNER] START {stage_name}: {' '.join(cmd)}")

    with open(stdout_path, "w", encoding="utf-8") as out, open(stderr_path, "w", encoding="utf-8") as err:
        process = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        try:
            assert process.stdout is not None
            for line in process.stdout:
                out.write(line)
                out.flush()
                print(f"[{stage_name}] {line}", end="", flush=True)

            return_code = process.wait()

        except KeyboardInterrupt:
            err.write("[A0] KeyboardInterrupt received. Terminating child process.\n")
            err.flush()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise

        finally:
            err.write("[A0] stderr redirected to stdout for live streaming.\n")
            err.flush()

    elapsed = time.perf_counter() - t0
    end_ts = datetime.utcnow().isoformat() + "Z"
    status = "SUCCESS" if return_code == 0 else "FAILED"

    log_runner(f"[RUNNER] END {stage_name}: status={status} runtime_seconds={round(elapsed, 3)}")

    return {
        "stage": stage_name,
        "status": status,
        "exit_code": return_code,
        "runtime_seconds": round(elapsed, 3),
        "started_at": start_ts,
        "ended_at": end_ts,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stderr_redirected_to_stdout": True,
        "cmd": cmd,
    }


def run_d00_stage(numeric_id: int, flag: str, log_dir: Path) -> Dict[str, Any]:
    """
    Calls current D00 by import because D00 is not CLI-parameterized.
    Also normalizes D00 output to the authoritative data path if needed.
    """
    ensure_dir(log_dir)
    stdout_path = log_dir / "d00_stdout.txt"
    stderr_path = log_dir / "d00_stderr.txt"

    start_ts = datetime.utcnow().isoformat() + "Z"
    t0 = time.perf_counter()
    expected_record_id = f"rgb_{numeric_id}_{flag}"

    log_runner(f"[RUNNER] START D00: import-call {D00_MODULE_PATH}")

    with open(stdout_path, "w", encoding="utf-8") as out, open(stderr_path, "w", encoding="utf-8") as err:
        tee_out = Tee(sys.stdout, out)
        tee_err = Tee(sys.stderr, err)

        with redirect_stdout(tee_out), redirect_stderr(tee_err):
            d00 = load_module_from_path("d00_module", D00_MODULE_PATH)
            d00.reset_pipeline_caches()
            d00.extract_record(
                str(D00_INPUT_FILE),
                str(D00_OUTPUT_FILE),
                numeric_id,
                flag,
            )

    elapsed = time.perf_counter() - t0
    end_ts = datetime.utcnow().isoformat() + "Z"

    for candidate in get_d00_output_candidates():
        log_runner(f"[RUNNER] D00 candidate path: {candidate} | exists={candidate.exists()}")

    normalized = normalize_d00_output()
    if normalized:
        log_runner(f"[RUNNER] D00 normalized/confirmed output: {normalized}")
    else:
        log_runner("[RUNNER] D00 output file not found in any candidate location")

    d00_packet = normalize_single_d00_row(D00_OUTPUT_FILE, expected_record_id)
    status = "SUCCESS" if d00_packet else "FAILED"
    exit_code = 0 if status == "SUCCESS" else 1

    log_runner(f"[RUNNER] END D00: status={status} runtime_seconds={round(elapsed, 3)}")

    return {
        "stage": "D00",
        "status": status,
        "exit_code": exit_code,
        "runtime_seconds": round(elapsed, 3),
        "started_at": start_ts,
        "ended_at": end_ts,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "cmd": ["import-call", str(D00_MODULE_PATH)],
        "expected_record_id": expected_record_id,
        "d00_output_path": str(D00_OUTPUT_FILE),
        "record_found": bool(d00_packet),
    }


# -----------------------------------------------------------------------------
# ARTIFACTS / METRICS
# -----------------------------------------------------------------------------
def capture_artifacts(artifact_paths: list[Path], dst_dir: Path) -> list[str]:
    copied = []
    for p in artifact_paths:
        copied_path = safe_copy(p, dst_dir)
        if copied_path:
            copied.append(copied_path)
    return copied


def parse_q_metrics(record_id: str, q_dir: Path) -> Dict[str, Any]:
    q1 = read_jsonl_by_record(q_dir / "Q1_intent_gate.jsonl", record_id)
    q2 = read_jsonl_by_record(q_dir / "Q2_signatures.jsonl", record_id)
    q3 = read_jsonl_by_record(q_dir / "Q3_retrieved_evidence.jsonl", record_id)
    q5 = read_jsonl_by_record(q_dir / "Q5_routed_context.jsonl", record_id)   # Q5 audit packet
    q6 = read_jsonl_by_record(q_dir / "Q6_final_answers.jsonl", record_id)    # Q6 final answer

    final_answer = q6.get("generated_answer", "")
    final_prompt = q6.get("final_prompt", "")

    return {
        "q_path": q1.get("complexity_path"),
        "q_primary_intent": q1.get("primary_intent"),
        "q_functional_intent": q1.get("justification", {}).get("target_functional_intent"),
        "q_triplet_count": q3.get("traversal_stats", {}).get(
            "count",
            q6.get("metadata", {}).get("triplet_count"),
        ),
        "q_residual_hits": q3.get("traversal_stats", {}).get("residual_hits", 0),
        "q_governance_ratio": q5.get("gov_ratio") if q5 else round(governance_ratio_from_q3(q3), 4),  # PREFER Q5's
        "q_mode": q6.get("mode"),
        "q_final_answer_present": bool(final_answer),
        "q_final_prompt_present": bool(final_prompt),
        "q_citations_present": has_citations(final_answer),
        "q_generated_answer": final_answer,
        # NEW: Q5 governance audit fields (paper-critical)
        "q_triplets_dropped": q5.get("audit_metadata", {}).get("triplets_dropped", 0),
        "q_chunks_dropped": q5.get("audit_metadata", {}).get("chunks_dropped", 0),
        "q_d5_contract_applied": q5.get("audit_metadata", {}).get("d5_contract_applied", False),
    }


# -----------------------------------------------------------------------------
# MAIN RUNNER
# -----------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Thin Experiment Runner: D00 -> D0 -> M0 -> Q0")
    parser.add_argument("--numeric-id", type=int, required=True, help="Numeric source ID, e.g. 12")
    parser.add_argument("--flag", choices=["P", "N"], required=True, help="'P' for positive, 'N' for negative")
    parser.add_argument("--label", choices=["positive", "negative"], default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    numeric_id = args.numeric_id
    flag = args.flag.upper()
    label = args.label or ("positive" if flag == "P" else "negative")
    record_id = f"rgb_{numeric_id}_{flag}"

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = args.run_id or f"run_{ts}_{record_id}_{label}"

    run_dir = RUNS_DIR / run_id
    manifest_dir = run_dir / "manifest"
    logs_dir = run_dir / "logs"
    d_dir = run_dir / "d"
    m_dir = run_dir / "m"
    q_dir = run_dir / "q"
    e_dir = run_dir / "e"
    snapshot_dir = run_dir / "snapshots"

    for p in [run_dir, manifest_dir, logs_dir, d_dir, m_dir, q_dir, e_dir, snapshot_dir]:
        ensure_dir(p)

    clear_run_output_files(
        get_d00_output_candidates() + D_ARTIFACTS + M_ARTIFACTS + Q_ARTIFACTS)
    # Note: E_ARTIFACTS deliberately excluded from clearing — MASTER_EVALUATION_LOG.csv
    # accumulates across runs via E2's merge-by-record logic.

    manifest: Dict[str, Any] = {
        "run_id": run_id,
        "record_id": record_id,
        "numeric_id": numeric_id,
        "flag": flag,
        "label": label,
        "project_root": str(PROJECT_ROOT),
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "code_fingerprints": build_code_fingerprints(),
        "started_at": datetime.utcnow().isoformat() + "Z",
        "stages": [],
        "artifact_dirs": {
            "d": str(d_dir),
            "m": str(m_dir),
            "q": str(q_dir),
            "e": str(e_dir),
        },
    }

    current_stage = "INIT"
    log_runner(f"[RUNNER] START run_id={run_id} record_id={record_id} label={label}")

    try:
        # ---- D00 ----
        current_stage = "D00"
        d00_result = run_d00_stage(numeric_id, flag, logs_dir)
        manifest["stages"].append(d00_result)
        write_stage_snapshot(snapshot_dir, d00_result)

        if d00_result["status"] != "SUCCESS":
            manifest["overall_status"] = "FAILED_AT_D00"
            manifest["current_stage"] = current_stage
            manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
            write_json(manifest_dir / "run_manifest.json", manifest)

            append_jsonl(
                RUN_INDEX_JSONL,
                {
                    "run_id": run_id,
                    "record_id": record_id,
                    "label": label,
                    "overall_status": "FAILED_AT_D00",
                    "current_stage": current_stage,
                    "manifest_path": str(manifest_dir / "run_manifest.json"),
                    "snapshot_dir": str(snapshot_dir),
                    "ended_at": manifest["ended_at"],
                },
            )
            raise SystemExit("D00 failed")

        d_copied_pre = capture_artifacts([D00_OUTPUT_FILE], d_dir)

        # ---- D0 ----
        current_stage = "D0"
        d0_cmd = [sys.executable, "-u", str(D0_SCRIPT)]
        d0_result = run_subprocess_stage("D0", d0_cmd, PROJECT_ROOT, logs_dir)
        manifest["stages"].append(d0_result)
        write_stage_snapshot(snapshot_dir, d0_result)

        if d0_result["status"] != "SUCCESS":
            manifest["overall_status"] = "FAILED_AT_D0"
            manifest["current_stage"] = current_stage
            manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
            write_json(manifest_dir / "run_manifest.json", manifest)

            append_jsonl(
                RUN_INDEX_JSONL,
                {
                    "run_id": run_id,
                    "record_id": record_id,
                    "label": label,
                    "overall_status": "FAILED_AT_D0",
                    "current_stage": current_stage,
                    "manifest_path": str(manifest_dir / "run_manifest.json"),
                    "snapshot_dir": str(snapshot_dir),
                    "ended_at": manifest["ended_at"],
                },
            )
            raise SystemExit("D0 failed")

        d_copied = d_copied_pre + capture_artifacts(D_ARTIFACTS, d_dir)

        # ---- M0 ----
        current_stage = "M0"
        m0_cmd = [sys.executable, "-u", str(M0_SCRIPT)]
        m0_result = run_subprocess_stage("M0", m0_cmd, PROJECT_ROOT, logs_dir)
        manifest["stages"].append(m0_result)
        write_stage_snapshot(snapshot_dir, m0_result)

        if m0_result["status"] != "SUCCESS":
            manifest["overall_status"] = "FAILED_AT_M0"
            manifest["current_stage"] = current_stage
            manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
            write_json(manifest_dir / "run_manifest.json", manifest)

            append_jsonl(
                RUN_INDEX_JSONL,
                {
                    "run_id": run_id,
                    "record_id": record_id,
                    "label": label,
                    "overall_status": "FAILED_AT_M0",
                    "current_stage": current_stage,
                    "manifest_path": str(manifest_dir / "run_manifest.json"),
                    "snapshot_dir": str(snapshot_dir),
                    "ended_at": manifest["ended_at"],
                },
            )
            raise SystemExit("M0 failed")

        m_copied = capture_artifacts(M_ARTIFACTS, m_dir)

        # ---- Q0 ----
        current_stage = "Q0"
        q0_cmd = [sys.executable, "-u", str(Q0_SCRIPT), record_id]
        q0_result = run_subprocess_stage("Q0", q0_cmd, PROJECT_ROOT, logs_dir)
        manifest["stages"].append(q0_result)
        write_stage_snapshot(snapshot_dir, q0_result)

        if q0_result["status"] != "SUCCESS":
            manifest["overall_status"] = "FAILED_AT_Q0"
            manifest["current_stage"] = current_stage
            manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
            write_json(manifest_dir / "run_manifest.json", manifest)

            append_jsonl(
                RUN_INDEX_JSONL,
                {
                    "run_id": run_id,
                    "record_id": record_id,
                    "label": label,
                    "overall_status": "FAILED_AT_Q0",
                    "current_stage": current_stage,
                    "manifest_path": str(manifest_dir / "run_manifest.json"),
                    "snapshot_dir": str(snapshot_dir),
                    "ended_at": manifest["ended_at"],
                },
            )
            raise SystemExit("Q0 failed")

        q_copied = capture_artifacts(Q_ARTIFACTS, q_dir)

# ---- E2 ----
        current_stage = "E2"
        
        # Pass the numeric-id and flag dynamically from the runner to your E2 script
        e2_cmd = [
            sys.executable, "-u", str(E2_SCRIPT), 
            "--numeric-id", str(numeric_id), 
            "--flag", flag
        ]
        
        e2_result = run_subprocess_stage("E2", e2_cmd, PROJECT_ROOT, logs_dir)
        manifest["stages"].append(e2_result)
        write_stage_snapshot(snapshot_dir, e2_result)

        if e2_result["status"] != "SUCCESS":
            manifest["overall_status"] = "FAILED_AT_E2"
            manifest["current_stage"] = current_stage
            manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
            write_json(manifest_dir / "run_manifest.json", manifest)

            append_jsonl(
                RUN_INDEX_JSONL,
                {
                    "run_id": run_id,
                    "record_id": record_id,
                    "label": label,
                    "overall_status": "FAILED_AT_E2",
                    "current_stage": current_stage,
                    "manifest_path": str(manifest_dir / "run_manifest.json"),
                    "snapshot_dir": str(snapshot_dir),
                    "ended_at": manifest["ended_at"],
                },
            )
            raise SystemExit("E2 failed")

        e_copied = capture_artifacts(E_ARTIFACTS, e_dir)
        
        # ---- Summarize ----
        q_metrics = parse_q_metrics(record_id, q_dir)

        if not q_metrics.get("q_final_answer_present"):
            manifest["overall_status"] = "FAILED_MISSING_Q_OUTPUT"
            manifest["current_stage"] = current_stage
            manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
            manifest["q_metrics"] = q_metrics
            write_json(manifest_dir / "run_manifest.json", manifest)

            append_jsonl(
                RUN_INDEX_JSONL,
                {
                    "run_id": run_id,
                    "record_id": record_id,
                    "label": label,
                    "overall_status": "FAILED_MISSING_Q_OUTPUT",
                    "current_stage": current_stage,
                    "manifest_path": str(manifest_dir / "run_manifest.json"),
                    "snapshot_dir": str(snapshot_dir),
                    "ended_at": manifest["ended_at"],
                },
            )
            raise SystemExit("Q0 produced no final answer for record")

        manifest["artifacts"] = {
            "d": d_copied,
            "m": m_copied,
            "q": q_copied,
            "e": e_copied,
        }
        manifest["q_metrics"] = q_metrics
        manifest["overall_status"] = "SUCCESS"
        manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"

        write_json(manifest_dir / "run_manifest.json", manifest)

        summary_row = {
            "run_id": run_id,
            "record_id": record_id,
            "label": label,
            "d00_status": d00_result["status"],
            "d0_status": d0_result["status"],
            "m0_status": m0_result["status"],
            "q0_status": q0_result["status"],
            "e2_status": e2_result["status"],
            "d_seconds": d00_result["runtime_seconds"] + d0_result["runtime_seconds"],
            "m_seconds": m0_result["runtime_seconds"],
            "q_seconds": q0_result["runtime_seconds"],
            "e_seconds": e2_result["runtime_seconds"],
            "d_artifact_dir": str(d_dir),
            "m_artifact_dir": str(m_dir),
            "q_artifact_dir": str(q_dir),
            "e_artifact_dir": str(e_dir),
            "q_path": q_metrics.get("q_path"),
            "q_primary_intent": q_metrics.get("q_primary_intent"),
            "q_functional_intent": q_metrics.get("q_functional_intent"),
            "q_triplet_count": q_metrics.get("q_triplet_count"),
            "q_residual_hits": q_metrics.get("q_residual_hits"),
            "q_governance_ratio": q_metrics.get("q_governance_ratio"),
            "q_mode": q_metrics.get("q_mode"),
            "q_final_answer_present": q_metrics.get("q_final_answer_present"),
            "q_final_prompt_present": q_metrics.get("q_final_prompt_present"),
            "q_citations_present": q_metrics.get("q_citations_present"),
            "q_triplets_dropped": q_metrics.get("q_triplets_dropped"),       
            "q_chunks_dropped": q_metrics.get("q_chunks_dropped"),           
            "q_d5_contract_applied": q_metrics.get("q_d5_contract_applied"), 
            "overall_status": "SUCCESS",
        }
        
        append_master_summary(summary_row)

        append_jsonl(
            RUN_INDEX_JSONL,
            {
                "run_id": run_id,
                "record_id": record_id,
                "label": label,
                "overall_status": "SUCCESS",
                "current_stage": "DONE",
                "manifest_path": str(manifest_dir / "run_manifest.json"),
                "snapshot_dir": str(snapshot_dir),
                "ended_at": manifest["ended_at"],
            },
        )

        # ---- Z0: Analysis Pipeline (non-blocking post-run) ----
        # Z0 runs AFTER manifest write + master_runs.csv append + run_index append,
        # so Z1/Z2/Z3/Z4 see fresh data including the current run.
        # Z0 orchestrates Z1 (Paper Analysis) -> Z2 (Decision Trace) -> Z3 (Evidence Append) -> Z4 (Dropzone Sync)
        z0_script = EXPERIMENT_DIR / "Z0_Analysis_Orchestrator.py"
        if z0_script.exists():
            current_stage = "Z0_Analysis"
            z0_cmd = [sys.executable, "-u", str(z0_script)]
            z0_result = run_subprocess_stage("Z0_Analysis", z0_cmd, PROJECT_ROOT, logs_dir)
            manifest["stages"].append(z0_result)
            write_stage_snapshot(snapshot_dir, z0_result)
            if z0_result["status"] != "SUCCESS":
                log_runner(f"[A0] WARN: Z0_Analysis had sub-stage failures (non-blocking)")
        else:
            log_runner(f"[A0] SKIP: Z0_Analysis_Orchestrator.py not found at {z0_script}")

        print(f"[RUNNER] SUCCESS: {run_id}")
        print(f"[RUNNER] Record:  {record_id}")
        print(f"[RUNNER] Run dir: {run_dir}")
        print(f"[RUNNER] Q mode:  {q_metrics.get('q_mode')}")
        print(f"[RUNNER] Answer present: {q_metrics.get('q_final_answer_present')}")

    except KeyboardInterrupt:
        manifest["overall_status"] = "CANCELLED_BY_USER"
        manifest["current_stage"] = current_stage
        manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
        write_json(manifest_dir / "run_manifest.json", manifest)

        append_jsonl(
            RUN_INDEX_JSONL,
            {
                "run_id": run_id,
                "record_id": record_id,
                "label": label,
                "overall_status": "CANCELLED_BY_USER",
                "current_stage": current_stage,
                "manifest_path": str(manifest_dir / "run_manifest.json"),
                "snapshot_dir": str(snapshot_dir),
                "ended_at": manifest["ended_at"],
            },
        )

        log_runner(f"[RUNNER] CANCELLED BY USER during {current_stage}")
        raise SystemExit(130)

    except SystemExit as e:
        log_runner(f"[RUNNER] STOPPED: {e}")
        raise

    except Exception as e:
        manifest["overall_status"] = "FAILED_WITH_EXCEPTION"
        manifest["current_stage"] = current_stage
        manifest["ended_at"] = datetime.utcnow().isoformat() + "Z"
        manifest["exception"] = str(e)
        manifest["exception_traceback"] = traceback.format_exc()
        write_json(manifest_dir / "run_manifest.json", manifest)

        append_jsonl(
            RUN_INDEX_JSONL,
            {
                "run_id": run_id,
                "record_id": record_id,
                "label": label,
                "overall_status": "FAILED_WITH_EXCEPTION",
                "current_stage": current_stage,
                "manifest_path": str(manifest_dir / "run_manifest.json"),
                "snapshot_dir": str(snapshot_dir),
                "ended_at": manifest["ended_at"],
            },
        )

        raise


if __name__ == "__main__":
    main()