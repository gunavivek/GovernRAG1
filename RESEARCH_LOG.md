# RESEARCH_LOG.md

> Reconstructed 2026-07-09 from git history and file timestamps after the original log was
> lost with the previous cloud session. Entries before 2026-07-09 are inferred, not verbatim.
> Append a dated entry at the end of every working session.

## 2026-07-03 (inferred from git)
- Initial commit `36b2e58`: dissertation codebase, Paper 1 frozen state.
- A1/B1 delucionqa runs started (runs\A1_delucionqa_20260703_231114, B1_..._231113).

## 2026-07-04 – 07-05 (inferred from git)
- Sprint 1 hardening: M3.3 retry/backoff/checkpoint; B1 build harness (`dcb1f0a`);
  M4+M5 hardening (`ae83641`); parallel M4 + equivalence checker (`fd267a3`).
- Serve map built (output\serve_question_chunk_map.jsonl, Jul 5).

## 2026-07-07 (inferred from git + results timestamps)
- `1253fea`: Q-pipeline corrections + eval harness. Q2 graph-grounded anchors, Q3
  ontology-tag + bidirectional walk, Q5 governance levels/axes/evidence log, Q6 G-level
  gate. Validated on 20-record Pro-judge pilot (G2 coverage/accuracy 20/6 → 40/33).
  Reversible (.bak on disk). Pending review by Dr. Xu.
- gold_map.json built (912 questions, 848 P / 64 N).
- Diagnostics along the way: affinity tau sweep, triplet starvation/yield sims,
  spectrum pilot + axes runs (results\ timestamps Jul 7–8).
- `2e56a4a`: E3_Unified_Evaluation.py — unified scorer (frontier + triad + Constrained-F1
  + evidence reduction); E3 run on the 20-record pilot caches.

## 2026-07-08 (inferred from file mtimes)
- Full-run preparation: preflight_check.py (join coverage + K-batch math) and
  dedup_records.py (1826 rows = 2x duplication; safety check for divergent duplicate
  groups; --write to produce the deduped benchmark CSV).

## 2026-07-09 (this session, verified)
- Previous Cowork session lost; CLAUDE.md / PROJECT_STATUS.md / RESEARCH_LOG.md were found
  to have never reached the local disk. State re-verified from code, git, and results\.
- Confirmed 912 = unique normalized questions (gold_map), K=25 → 37 batches
  (offsets 0,25,…,900; last batch 12 records).
- Found the batch driver missing; B2_Serve.py had no --offset. Fixes made:
  - B2_Serve.py: added --offset (batch slicing; --sample path unchanged). Slicing unit-tested.
  - B4_Batch_Runner.py: new resumable 37-batch driver — per batch B2 serve → 8 governed
    configs Q5+Q6 (generation only, no double-judging) → append to results\full_run\ →
    checkpoint state.json; final merge (dedup by record id) into the canonical paths E3
    reads; optional --run-e3. Batch math + merge logic unit-tested.
- Status files recreated (this file, CLAUDE.md, PROJECT_STATUS.md).
- Paper2 documentation folder (OneDrive) recovered and reviewed: Sprint_Log.md (Jul 6),
  Analysis_Plan_and_Stopping_Rule.md (pre-registration + deviation log),
  Frozen_Code_Changes.md (change sets 1–6), Spectrum_Pilot_Results.md (N=20),
  Benchmark_Input_Provenance.md (Jul 8 — the 912-record derivation: dedup --key question
  --allow-divergent, keep-first; {2:911, 4:1}; 848 P / 64 N). Corrections applied:
  pre-registered dedup command adopted; updated preflight_check.py (split composition)
  synced from Paper2\4_Harness into the repo; B4 + patched B2 mirrored back to 4_Harness.
- CONSTRAINTS from pre-registration: judge locked gemini-2.5-pro; N≥3 runs; change sets
  5–6 held pending Dr. Xu sign-off before the full run.
- NEXT: (Dr. Xu sign-off) → dedup (pre-registered cmd) → preflight → launch
  `python B4_Batch_Runner.py --records "data\delucionqa_records_912.csv" --k 25 --run-e3`

## 2026-07-09 (later, verified) — LAUNCH CLEARED
- Dr. Xu SIGNED OFF on change sets 5–6 (relayed by Vivek). Full-run gate open.
- `delucionqa_records_912.csv` located (OneDrive `…\conceptual_GraphRAG\data\`, written by
  the lost 07-08 session at 19:41). VERIFIED: byte-identical (md5, EOL-normalized) to an
  independent re-derivation via the pre-registered dedup command; preflight READY (912 rows,
  100% gold join, 0 empty gold, 848 P / 64 N, 37 batches); all 912 idx resolve to non-empty
  serve-map chunk scopes. Split composition recorded: train 729 / val 91 / test 92.
- File committed to repo `data\delucionqa_records_912.csv`. Run launched from Vivek's
  terminal: `python B4_Batch_Runner.py --records "data\delucionqa_records_912.csv" --k 25 --run-e3`
  (pre-registration: judge gemini-2.5-pro; N≥3 runs; report-regardless).

## 2026-07-09/10 — RUN 1 COMPLETE (task #33)
- Generation: 37/37 batches in ~8.6 h, 19.1 ± 1.9 min/batch, ZERO failed stages
  (timing_log.csv). Merge: 912 records in serve_results + all 8 config caches.
- Scoring: E3 sequential, Pro judge; ~24 h wall-clock due to API latency variance
  (overnight ~2.5 min/record; account already Tier 3 at 11/2000 RPM peak → bottleneck was
  sequential latency, NOT quota). Mitigation built + approved: E3_Parallel_Evaluation.py
  (workers + per-pair checkpoint + retry/backoff; mock-tested; for ALL future scoring).
- QA: 8,208/8,208 pairs, 0 ERROR verdicts, strata 848/64, 3 rows missing TRACe (noise).
- RESULTS (full table + H1–H4: Paper2\6_Results\Full_Benchmark_Run1_Results.md):
  H1 parity at G1 ONLY (−3.4 pp acc, +0.005 F1); H2 NOT supported (faith ceiling 0.98–0.99
  all configs); H3 partial (corrRef 33→42→75–83% monotone, leakage 17→5–8%, BUT falseRej
  54–64% at G2+ → pre-registered coverage-cost finding); H4 supported (97.7–99.9% cited).
  Key numbers: G1 93% cov / 64.4% acc; G2 44% / 18.2%; evidence reduction 35.9 chunks
  dropped/record at G2+ with flat accuracy (dissociation confirmed at N=912).
- Run-1 outputs archived: results\E3_run1_master_eval_log.csv, E3_run1_frontier_summary.csv.
- NEXT (#38): results section draft; replication decision (N≥3 vs bootstrap memo) w/ Dr. Xu.
