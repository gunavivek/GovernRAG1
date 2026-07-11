# CLAUDE.md — conceptual_GraphRAG (dissertation, Paper 2 evaluation phase)

> Reconstructed 2026-07-09 from git history, code, and results\ after the original session
> files were lost. Keep this file (and PROJECT_STATUS.md / RESEARCH_LOG.md) ON DISK and
> update them at the end of every working session — cloud-session files that aren't
> committed back to this folder do not survive.

## What this project is
GovernRAG: a governance-spectrum evaluation of a concept-graph RAG pipeline on DelucionQA
(RAGBench). A frozen Q-pipeline (Q1 intent gate → Q2 signature extractor → Q3 graph
retrieval → Q4 residual retrieval (optional) → Q5 context router → Q6 answer generation,
under `experiment\`) is served over a build-once embedded graph, and evaluated across
governance levels G0 (naive) … G4 (corroborated) plus two ontology-derived axes
(GOVRAG_ONTOLOGY conformance, GOVRAG_AFFINITY_MIN domain affinity, tau=0.35 default).

## Harness scripts (repo root) — run order
1. `B1_Build_Index.py` — build-once graph/index (done for delucionqa).
2. `serve_map_questions_to_chunks.py` — question→chunk scoping map (output\serve_question_chunk_map.jsonl, done).
3. `build_gold_map.py` — gold responses + answerability keyed by normalized question
   (results\gold_map.json: 912 entries; 848 answerable / 64 unanswerable, done Jul 7).
4. `dedup_records.py` — source delucionqa_records.csv (in C:\Users\gunav\Downloads\, 1826 rows
   = 2x duplication) → deduped benchmark CSV (912 unique questions).
5. `preflight_check.py` — read-only join/answerability/batch-math check; must say READY.
6. `B2_Serve.py` — serve a slice through the frozen pipeline (+ naive baseline).
   Supports `--offset/--limit` (batch slicing) and `--sample` (pilots).
7. `B4_Batch_Runner.py` — **full-run driver**: 37 batches of K=25, resumable via
   results\full_run\state.json; per batch runs B2 then per-config Q5+Q6 (generation only),
   appends to results\full_run\*_all.jsonl, merges to canonical paths at the end.
8. `B3_spectrum_axes.py` — pilot-scale config sweep WITH scoring (superseded for the full
   run by B4 + E3; still useful for small experiments).
9. `E3_Unified_Evaluation.py` — the single unified SCORER (no generation): frontier, triad,
   Constrained-F1, evidence reduction. Reads results\serve_results.jsonl + _spec_* caches.
10. `trace_scorer.py` — shared judging/normalization utilities (norm_q must stay in sync
    with preflight_check/dedup_records).

## Conventions
- Always run from repo root. Python on Windows; GEMINI_API_KEY in `.env`.
- Judge model: gemini-2.5-pro (stable independent); fast pass: gemini-2.5-flash --no-trace.
  Naive baseline model: gemini-3.5-flash (BASELINE_MODEL in B2_Serve.py).
- E2 P/N semantics: answerable → MATCH=SUCCESS; unanswerable → SAFE_SILENCE=SUCCESS,
  MATCH=FAILURE (parametric leakage).
- The 9 configs (G0_Naive, G1_Cited, G2_Grounded, G3_Strict, G4_Corrob, G2+OntNU,
  G2+OntConf, G2+Aff, G2+OntNU+Aff) are duplicated in B3_spectrum_axes.py,
  E3_Unified_Evaluation.py and B4_Batch_Runner.py — keep them in lockstep.
- output\Q5_*/Q6_* always reflect the LAST config run; canonical results live in results\.
- Patches to the frozen pipeline are applied by apply_q*.py scripts and are reversible
  (.bak files on disk). Pipeline changes pending review by Dr. Xu.

## Canonical documentation (read at session start)
OneDrive: `…\PhD\3 Dissertation\conceptual_GraphRAG\Documentation\GovRAG\Paper2\`
- `1_Planning\Sprint_Log.md` — the living handoff ("read this first to resume").
- `2_Design\Analysis_Plan_and_Stopping_Rule.md` — PRE-REGISTRATION (binding): judge locked
  gemini-2.5-pro, N≥3 runs, report-regardless, deviation log.
- `2_Design\Benchmark_Input_Provenance.md` — how delucionqa_records_912.csv is derived
  (dedup --key question --allow-divergent, keep-first).
- `2_Design\Frozen_Code_Changes.md` — audit record of every frozen-pipeline change
  (sets 5–6 held pending Dr. Xu before the full run).
- `4_Harness\` mirrors the repo-root harness scripts — keep the two in sync.

## Current status
See PROJECT_STATUS.md (verified 2026-07-09). Session history: RESEARCH_LOG.md.
