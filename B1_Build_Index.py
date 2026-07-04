#!/usr/bin/env python3
"""
B1_Build_Index.py  --  Sprint 1 (Paper 2): build-once + persist + measure.

WHAT THIS DOES
  The frozen pipeline writes every build artefact into a single-slot `output/`,
  and the next build overwrites it. This wrapper turns that into a reusable,
  per-dataset INDEX so a corpus is built ONCE and served MANY times (Sprint 2).

  For one corpus it:
    1. (optionally) runs the existing A1 build runner (D1 -> D0 -> D5 patch -> M0)
       while polling peak RAM of the whole process tree (psutil);
    2. snapshots the resulting `output/` into  index/<dataset>/ ;
    3. reads the M5 graph and records node/edge counts + file sizes;
    4. writes  index/<dataset>/build_manifest.json  with the Sprint-1 metrics
       (n_records, C_build seconds, peak RAM MB, graph size).

  It does NOT modify any frozen pipeline script. Serving (Sprint 2) will just
  copy index/<dataset>/ back into output/ once, then loop questions.

WHERE TO PUT IT
  Drop this file in your live project ROOT (the folder that contains `data/`,
  `output/`, and `experiment/`). It auto-locates the root by walking up to find
  `data/` and `output/`.

PREREQUISITES (on your machine)
  pip install psutil networkx
  (your usual Gemini API key / env must be set, exactly as for a normal A1 run)

USAGE
  # build + persist + measure in one shot (recommended):
  python B1_Build_Index.py delucionqa

  # if you prefer to run A1 yourself first, then just snapshot+measure output/:
  python A1_RAGBench_D0_M0_Runner.py delucionqa
  python B1_Build_Index.py delucionqa --skip-build

  # point at A1 explicitly if auto-locate fails:
  python B1_Build_Index.py finqa --a1 experiment/A1_RAGBench_D0_M0_Runner.py
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def find_root(start: Path) -> Path:
    """Walk up from `start` until a dir has both data/ and output/."""
    for parent in [start, *start.parents]:
        if (parent / "data").exists() and (parent / "output").exists():
            return parent
    # fall back: make output/ next to data/ if only data/ exists
    for parent in [start, *start.parents]:
        if (parent / "data").exists():
            (parent / "output").mkdir(exist_ok=True)
            return parent
    sys.exit("[FATAL] Could not locate project root (no data/ + output/ found above this script).")


def locate_a1(root: Path, override: str | None) -> Path | None:
    if override:
        p = Path(override)
        return p if p.is_absolute() else (root / p)
    for cand in [
        root / "A1_RAGBench_D0_M0_Runner.py",
        root / "experiment" / "A1_RAGBench_D0_M0_Runner.py",
        Path(__file__).resolve().parent / "A1_RAGBench_D0_M0_Runner.py",
    ]:
        if cand.exists():
            return cand
    return None


def count_records(corpus_jsonl: Path) -> int:
    n = 0
    with corpus_jsonl.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def run_build_with_ram(a1_path: Path, corpus: str, root: Path, log_path: Path) -> dict:
    """Run A1 as a subprocess; poll peak RSS of the process tree (psutil)."""
    import psutil

    log_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, "-u", str(a1_path), corpus],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    p = psutil.Process(proc.pid)
    peak_rss = 0

    def sample():
        nonlocal peak_rss
        try:
            procs = [p] + p.children(recursive=True)
            total = 0
            for q in procs:
                try:
                    total += q.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            peak_rss = max(peak_rss, total)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    with log_path.open("w", encoding="utf-8") as log_f:
        last = 0.0
        for line in proc.stdout:
            log_f.write(line)
            log_f.flush()
            print(f"  {line.rstrip()}", flush=True)
            now = time.perf_counter()
            if now - last > 0.5:
                sample()
                last = now
        rc = proc.wait()
        sample()

    elapsed = time.perf_counter() - t0
    return {
        "status": "SUCCESS" if rc == 0 else "FAILED",
        "exit_code": rc,
        "build_seconds": round(elapsed, 1),
        "build_minutes": round(elapsed / 60, 2),
        "peak_ram_mb": round(peak_rss / (1024 * 1024), 1),
        "log": str(log_path),
    }


def graph_stats(graphml: Path) -> dict:
    if not graphml.exists():
        return {"exists": False}
    out = {"exists": True, "graphml_bytes": graphml.stat().st_size}
    try:
        import networkx as nx
        g = nx.read_graphml(graphml)
        out["nodes"] = g.number_of_nodes()
        out["edges"] = g.number_of_edges()
        rids = set()
        for _, _, d in g.edges(data=True):
            if "record_id" in d:
                rids.add(d["record_id"])
        if rids:
            out["distinct_record_ids_on_edges"] = len(rids)
    except Exception as e:
        out["graph_read_error"] = str(e)
    return out


def snapshot_output(output_dir: Path, index_dir: Path) -> list[dict]:
    if index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for item in sorted(output_dir.rglob("*")):
        if item.is_file():
            rel = item.relative_to(output_dir)
            dst = index_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst)
            manifest.append({"file": str(rel), "bytes": item.stat().st_size})
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="Build-once + persist + measure one corpus index.")
    ap.add_argument("corpus", help="corpus name, e.g. delucionqa | emanual | finqa | cuad | techqa")
    ap.add_argument("--skip-build", action="store_true",
                    help="do not run A1; just snapshot+measure the current output/")
    ap.add_argument("--a1", default=None, help="explicit path to A1_RAGBench_D0_M0_Runner.py")
    args = ap.parse_args()
    corpus = args.corpus.lower()

    root = find_root(Path(__file__).resolve().parent)
    output_dir = root / "output"
    corpus_jsonl = root / "data" / f"{corpus}_corpus.jsonl"

    print("X" * 70)
    print(f"  B1 BUILD-ONCE INDEX :: corpus = {corpus}")
    print(f"  project_root : {root}")
    print("X" * 70)

    if not corpus_jsonl.exists():
        print(f"[FATAL] staged corpus not found: {corpus_jsonl}")
        print(f"        stage it first with A0_RAGBench_PerQuestion_Stager.py")
        return 2
    n_records = count_records(corpus_jsonl)
    print(f"  records in corpus: {n_records}")

    summary = {
        "corpus": corpus,
        "n_records": n_records,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "skip_build": args.skip_build,
    }

    if args.skip_build:
        print("\n[1/3] --skip-build: using existing output/ (no A1 run)")
        summary["build"] = {"status": "SKIPPED", "note": "measured existing output/"}
    else:
        a1 = locate_a1(root, args.a1)
        if not a1:
            print("[FATAL] Could not find A1_RAGBench_D0_M0_Runner.py. Pass --a1 <path>,")
            print("        or run A1 yourself and re-run this with --skip-build.")
            return 2
        print(f"\n[1/3] Building via A1: {a1}")
        try:
            import psutil  # noqa: F401
        except ImportError:
            print("[FATAL] psutil not installed. Run: pip install psutil")
            return 2
        runs_dir = root / "runs" / f"B1_{corpus}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        build = run_build_with_ram(a1, corpus, root, runs_dir / "build.log")
        summary["build"] = build
        if build["status"] != "SUCCESS":
            print(f"\n[FATAL] A1 build FAILED (exit {build['exit_code']}). See {build['log']}")
            return 1

    print("\n[2/3] Reading graph stats")
    gstats = graph_stats(output_dir / "M5_Embedded_Graph.graphml")
    summary["graph"] = gstats
    if not gstats.get("exists"):
        print("   [WARN] M5_Embedded_Graph.graphml not found in output/ — index may be incomplete.")

    print("\n[3/3] Snapshotting output/ -> index/<dataset>/")
    index_dir = root / "index" / corpus
    files = snapshot_output(output_dir, index_dir)
    summary["index_dir"] = str(index_dir)
    summary["index_files"] = files
    summary["index_total_bytes"] = sum(f["bytes"] for f in files)
    summary["ended_at"] = datetime.utcnow().isoformat() + "Z"

    (index_dir / "build_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    # ---- Sprint 1 metrics block ----
    b = summary.get("build", {})
    print("\n" + "#" * 70)
    print(f"  SPRINT 1 METRICS :: {corpus}")
    print("#" * 70)
    print(f"  records (n)        : {n_records}")
    if "build_minutes" in b:
        print(f"  C_build (wall)     : {b['build_minutes']} min  ({b['build_seconds']} s)")
        print(f"  peak RAM           : {b['peak_ram_mb']} MB")
    print(f"  graph nodes        : {gstats.get('nodes', 'n/a')}")
    print(f"  graph edges        : {gstats.get('edges', 'n/a')}")
    print(f"  distinct record_ids on edges : {gstats.get('distinct_record_ids_on_edges', 'n/a')}")
    print(f"  graphml size       : {round(gstats.get('graphml_bytes', 0)/1024, 1)} KB")
    print(f"  index total size   : {round(summary['index_total_bytes']/1024, 1)} KB  ({len(files)} files)")
    print(f"  persisted to       : {index_dir}")
    print(f"  manifest           : {index_dir / 'build_manifest.json'}")
    print("#" * 70)
    print("\n  -> Report C_build, peak RAM, nodes/edges back for the Sprint-1 log.")
    print("  -> Sprint 2 will restore this index and serve all questions with NO rebuild.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
