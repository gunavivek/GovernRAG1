#!/usr/bin/env python3
"""
B2_Serve.py  --  Sprint 2: serve-many over the build-once graph (design A).

Loads M5_Embedded_Graph.graphml ONCE (in Q3) and answers all questions against it
with NO rebuild, scoping each question to its OWN chunks (design A). Produces two
(query, context, response) tuples per question -- GovernRAG + Naive -- plus the
governance metrics the frozen code emits. trace_scorer.py then scores TRACe.

STAGE ORCHESTRATION (confirmed against frozen code):
  Q1 batch -> Q2 batch -> Q3 batch (design-A patched) -> Q4 PER-RECORD (needs
  record_id arg; SKIPPED if optional residual file absent) -> Q5 batch
  (process_file) -> Q6 batch (run_q6_synthesis).

RUN
  python B2_Serve.py --records ...\delucionqa_records.csv --sample 20
  python B2_Serve.py --records ...\delucionqa_records_912.csv --offset 25 --limit 25   # batch slice
"""
import argparse, csv, json, os, subprocess, sys, time
from pathlib import Path

STAGE_TIMINGS = []  # (stage, script, arg, seconds, ok) -- written to results/serve_stage_timings.jsonl

csv.field_size_limit(10_000_000)


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start


ROOT = find_root(Path(__file__).resolve().parent if (Path(__file__).resolve().parent / "output").exists() else Path.cwd())
EXP = ROOT / "experiment"
OUT = ROOT / "output"
RESULTS = ROOT / "results"; RESULTS.mkdir(exist_ok=True)

BASELINE_MODEL = "gemini-3.5-flash"

# (name, script, per_record?)
Q_STAGES = [
    ("Q1", "Q1_Gov_Intent_Gate_V2.py", False),
    ("Q2", "Q2_Gov_Signature_Extractor_V2.py", False),
    ("Q3", "Q3_Gov_Graph_Retrieval_Engine_V3.py", False),
    ("Q4", "Q4_Gov_Residual_Retrieval.py", True),   # per-record: needs record_id arg
    ("Q5", "Q5_Gov_Context_Router.py", False),
    ("Q6", "Q6_Gov_Answer_Generation.py", False),
]


def load_questions(records_csv, serve_map, limit=None, sample=None, seed=13, offset=0):
    chunkmap = {}
    with open(serve_map, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                chunkmap[str(d.get("idx"))] = d.get("chunk_ids", [])
    rows = list(csv.DictReader(open(records_csv, encoding="utf-8")))
    if sample:
        import random
        random.seed(seed)
        rows = random.sample(rows, min(sample, len(rows)))
    else:
        if offset:
            rows = rows[offset:]
        if limit:
            rows = rows[:limit]
    qs = []
    for i, row in enumerate(rows):
        idx = str(row.get("idx", i))
        qs.append({
            "q_id": "delucionqa_q%05d" % int(idx),
            "idx": idx,
            "question": row.get("question", ""),
            "gold": row.get("gold", row.get("response", "")),
            "docs": row.get("documents_joined", ""),
            "chunk_ids": chunkmap.get(idx, []),
        })
    return qs


def stage_pipeline_inputs(qs):
    gov_profile = None
    cm = ROOT / "index" / "delucionqa" / "D5_Extraction_Manifest.jsonl"
    if cm.exists():
        for line in cm.open(encoding="utf-8"):
            if line.strip():
                gov_profile = json.loads(line).get("governance_profile")
                break
    manifest = OUT / "D5_Extraction_Manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as f:
        for q in qs:
            row = {
                "record_id": q["q_id"],
                "source_text": "Question: %s | Document: %s" % (q["question"], q["docs"][:4000]),
            }
            if gov_profile is not None:
                row["governance_profile"] = gov_profile
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (OUT / "serve_chunk_filter.json").write_text(
        json.dumps({q["q_id"]: q["chunk_ids"] for q in qs}), encoding="utf-8")
    gp = "attached" if gov_profile else "MISSING (check index/delucionqa/)"
    print("[stage] %d questions staged; corpus governance profile: %s" % (len(qs), gp))


def run_stage(name, script, arg=None):
    p = EXP / script
    if not p.exists():
        print("[WARN] %s: %s not found (adjust Q_STAGES)" % (name, p)); return False
    cmd = [sys.executable, "-u", str(p)] + ([arg] if arg else [])
    t0 = time.perf_counter()
    ok = subprocess.run(cmd, cwd=str(ROOT)).returncode == 0
    STAGE_TIMINGS.append({"stage": name, "script": script, "arg": arg,
                          "seconds": round(time.perf_counter() - t0, 3), "ok": ok})
    return ok


def run_governed_pipeline(qs):
    for name, script, per_record in Q_STAGES:
        if per_record:
            if name == "Q4" and not (OUT / "M1_6_Residual_Chunks.csv").exists():
                print("[run] Q4 SKIPPED (optional Tier-2 residuals; output/M1_6_Residual_Chunks.csv absent)")
                continue
            print("[run] %s per-record x%d" % (name, len(qs)))
            for q in qs:
                if not run_stage(name, script, arg=q["q_id"]):
                    print("[WARN] %s failed for %s (continuing)" % (name, q["q_id"]))
        else:
            print("[run] %s (batch)" % name)
            if not run_stage(name, script):
                print("[FATAL] governed pipeline stopped at %s" % name); return False
    return True


def naive_baseline(question, context):
    """Returns (answer, latency_seconds, usage_dict) -- per-question naive cost/latency (metric #7)."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = "Instructions: Answer the question based ONLY on the context.\n\nContext: %s\n\nQuestion: %s" % (context, question)
    t0 = time.perf_counter()
    try:
        r = client.models.generate_content(model=BASELINE_MODEL, contents=prompt,
                                            config=types.GenerateContentConfig(temperature=0.0))
        dt = round(time.perf_counter() - t0, 3)
        usage = {}
        try:
            u = r.usage_metadata
            usage = {"prompt_tokens": u.prompt_token_count, "output_tokens": u.candidates_token_count}
        except Exception:
            pass
        return r.text.strip(), dt, usage
    except Exception as e:
        return "ERROR: %s" % e, round(time.perf_counter() - t0, 3), {}


def assemble(qs):
    q6 = {}
    q6f = OUT / "Q6_final_answers.jsonl"
    if q6f.exists():
        for line in q6f.open(encoding="utf-8"):
            if line.strip():
                d = json.loads(line)
                q6[str(d.get("record_id"))] = d
    out = RESULTS / "serve_results.jsonl"
    n = 0
    with out.open("w", encoding="utf-8") as f:
        for q in qs:
            g = q6.get(q["q_id"], {})
            gov_answer = g.get("generated_answer", "")
            gov_mode = g.get("mode", "")
            gov_context = g.get("final_prompt", "") or q["docs"]
            has_cite = ("[CHNK_" in gov_answer) or ("[RESIDUAL_" in gov_answer)
            rowout = {
                "idx": q["idx"],
                "question": q["question"],
                "gold": q["gold"],
                "governed": {
                    "answer": gov_answer,
                    "mode": gov_mode,
                    "context": gov_context,
                    "refused": gov_mode.startswith("BLOCKED"),
                    "has_citation": has_cite,
                    "governance_ratio": g.get("governance_ratio"),
                },
                "naive": {},
            }
            n_ans, n_lat, n_use = naive_baseline(q["question"], q["docs"])
            rowout["naive"] = {"answer": n_ans, "context": q["docs"],
                               "latency_s": n_lat, "usage": n_use}
            f.write(json.dumps(rowout, ensure_ascii=False) + "\n")
            n += 1
    refused = sum(1 for q in qs if q6.get(q["q_id"], {}).get("mode", "").startswith("BLOCKED"))
    print("[assemble] wrote %d rows -> %s  (governed refusals: %d/%d)" % (n, out, refused, n))
    return out


def build_scoped_vocab():
    """Option B: produce output/serve_scoped_vocab.json for Q2 anchor linking."""
    script = ROOT / "build_scoped_vocab.py"
    if not script.exists():
        print("[WARN] build_scoped_vocab.py not found at repo root; skipping anchor linking"); return
    print("[run] build_scoped_vocab (Option B anchor linking)")
    subprocess.run([sys.executable, "-u", str(script)], cwd=str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--map", default=str(OUT / "serve_question_chunk_map.jsonl"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--offset", type=int, default=0, help="skip the first N records (batch slicing; ignored with --sample)")
    ap.add_argument("--sample", type=int, default=None, help="serve N RANDOM questions")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--no-linking", action="store_true",
                    help="ablation: skip graph-grounded anchor linking (Q2 reverts to frozen heuristic)")
    args = ap.parse_args()

    qs = load_questions(args.records, args.map, limit=args.limit, sample=args.sample, seed=args.seed, offset=args.offset)
    print("[B2] serving %d questions from %s" % (len(qs), OUT / "M5_Embedded_Graph.graphml"))
    stage_pipeline_inputs(qs)
    if args.no_linking:
        vf = OUT / "serve_scoped_vocab.json"
        if vf.exists():
            vf.unlink()  # ensure Q2 reverts to frozen heuristic for the ablation
        print("[B2] anchor linking DISABLED (--no-linking): frozen Q2 heuristic")
    else:
        build_scoped_vocab()
    if not run_governed_pipeline(qs):
        sys.exit(1)
    out = assemble(qs)
    # execution log: per-stage wall time for this serve slice (metric #7 amortized-latency source)
    with (RESULTS / "serve_stage_timings.jsonl").open("w", encoding="utf-8") as f:
        f.write(json.dumps({"offset": args.offset, "n_records": len(qs),
                            "stages": STAGE_TIMINGS}, ensure_ascii=False) + "\n")
    print("[B2] stage timings -> results/serve_stage_timings.jsonl")
    print("\n[B2] done. Next: python trace_scorer.py --results %s --judge-model gemini-2.5-flash" % out)


if __name__ == "__main__":
    main()
