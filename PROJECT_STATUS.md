# PROJECT_STATUS.md — verified 2026-07-09

> Reconstructed from git log, scripts, and results\ after the previous session's status
> files were lost (they were never written to this folder). Every claim below was checked
> against the actual artifacts on disk on 2026-07-09.
>
> CANONICAL DOCUMENTATION lives in OneDrive:
> `…\PhD\3 Dissertation\conceptual_GraphRAG\Documentation\GovRAG\Paper2\`
> — living handoff: `1_Planning\Sprint_Log.md`; pre-registration:
> `2_Design\Analysis_Plan_and_Stopping_Rule.md`; benchmark derivation:
> `2_Design\Benchmark_Input_Provenance.md` (2026-07-08, the last thing the lost
> session wrote); frozen-pipeline audit trail: `2_Design\Frozen_Code_Changes.md`.

## Git
- HEAD: `2e56a4a` "E3 unified evaluator" (2026-07-07), on `1253fea` Q-pipeline corrections
  + eval harness (Q2 graph-grounded anchors; Q3 ontology-tag + bidirectional walk; Q5
  governance levels + ontology/affinity axes + evidence log; Q6 G-level gate).
- B2 --offset patch, B4_Batch_Runner.py, and these three .md files added 2026-07-09 (uncommitted).
- Working tree carries many older modified files (eval\, experiment\Archive\, config\) —
  pre-existing churn, not part of the current change.

## Completed (verified on disk)
- Build phase: index + embedded graph (runs\B1_delucionqa_20260703_231113), serve map
  output\serve_question_chunk_map.jsonl (Jul 5), gold map results\gold_map.json (Jul 7;
  912 questions: 848 P / 64 N).
- 20-record Pro-judge pilot: results\serve_results.jsonl (20 records), all 9 config caches
  (results\_spec_*.jsonl + _red), E3 scored (results\E3_master_eval_log.csv,
  E3_frontier_summary.csv). Headline pilot numbers (N=20): G0 coverage 100% / C-F1 0.62;
  G2_Grounded coverage 40%, correct-refusal 61%, C-F1 0.39; best governed C-F1
  G2+OntNU+Aff 0.42; evidence reduction ~29.4 chunks dropped/record at G2+ vs 0 at G1.
- Full-run prep tooling: preflight_check.py (K-batch math), dedup_records.py
  (1826 = 913x2 duplication analysis; dedup by question → 912 unique).

## NOT done yet (the immediate work)
1. ~~Produce data\delucionqa_records_912.csv~~ **DONE 2026-07-09.** The lost session's file
   was found in OneDrive `…\3 Dissertation\conceptual_GraphRAG\data\` (written 07-08 19:41),
   verified byte-identical to an independent re-derivation via the pre-registered command
   ({2:911, 4:1}; divergent group = "what does the vehicle security system do?"), and
   committed to `data\delucionqa_records_912.csv` in the repo.
2. ~~preflight READY~~ **DONE 2026-07-09.** 912 rows, 100% gold join, 0 empty gold,
   848 P / 64 N, all 912 idx resolve to non-empty serve-map chunk scopes. Split
   composition (methods appendix): train 729 / validation 91 / test 92 (informational —
   no train/test leakage, see provenance doc).
3. ~~The 37-batch run~~ **DONE 2026-07-09/10 (RUN 1 COMPLETE).** Generation: 37/37 batches,
   ~8.6 h, zero failures. Scoring: E3 sequential with Pro judge (~24 h; slow = API latency,
   fixed for future runs by E3_Parallel_Evaluation.py). QA: 8,208 pairs, 0 ERROR verdicts.
   Results archived as results\E3_run1_*.csv. Headline: H1 parity SUPPORTED at G1 only
   (−3.4 pp); H2 faithfulness superiority NOT supported (ceiling ~0.99 everywhere);
   H3 partial (corrRef 33→83% monotone, but falseRej 54–64% at G2+ = coverage-cost
   finding); H4 supported (97.7–99.9% provenance). Full analysis:
   Paper2\6_Results\Full_Benchmark_Run1_Results.md. Task #33 run 1 CLOSED.
4. **← CURRENT: task #38 + replication decision.** Draft results section from run 1;
   decide with Dr. Xu: full N≥3 replications (via B4 into separate full_run dirs + E3P
   --out-prefix) vs bootstrap CIs + subset replication (cheaper; deviation memo drafted on
   request). Original launch command for reference:
   `python B4_Batch_Runner.py --records "data\delucionqa_records_912.csv" --k 25 --run-e3`
   Resumable: rerun the same command after any crash; state in results\full_run\state.json.
4. E3 unified scoring at N=912 (auto with --run-e3), then results → dissertation tables.

## Pre-registration constraints (Analysis_Plan_and_Stopping_Rule.md — binding)
- Judge LOCKED = gemini-2.5-pro (deviation-logged 2026-07-06; flash mis-scores MATCH cases).
  Generation parity pair: Q6 == naive == gemini-3.5-flash. Any change must be deviation-logged.
- Report-regardless: the pre-registered run's results ARE the paper. No result-driven tuning.
- N ≥ 3 independent runs (temp-0 nondeterminism, M4 self-agreement ~90%/75%) — report
  mean ± sd. Budget: the 37-batch serve may need repetition, not just one pass.
- GATE: change sets 5–6 (ontology axes, Q3 bidirectional walk) are HELD PENDING DR. XU
  SIGN-OFF before the full (912) run per Frozen_Code_Changes.md.

## Artifact management policy (adopted 2026-07-11; applies to every run)
Two tiers. TIER 1 — working slots, transient, NEVER cited: `output\` (serve slot) and the
canonical `results\` filenames that B4/E3 write (overwritten by each run). TIER 2 —
per-run archives, append-only, the ONLY source for paper numbers:
- `index\<dataset>\` — one build per corpus (graph, embeddings, build manifest); never overwritten.
- `results\run1_delucionqa\` (archived 2026-07-11), `results\run2_expertqa\`,
  `results\run3_hagrid\` — each run's serve results, _spec_* caches, E3 outputs,
  timing_log/state, run manifest, pip freeze; plus git tag (runN-complete) and an OneDrive
  evidence pack of the small files.
CITATION RULE: a number may enter the paper/dissertation only from a Tier-2 folder + its
manifest. END-OF-RUN CHECKLIST: copy canonical outputs -> runN_<dataset>\; write manifest;
git tag + push; evidence pack to OneDrive; only then may the next run start.

## Known discrepancies / cautions
- The previous session's batch driver was never saved; B4_Batch_Runner.py (2026-07-09) is
  its reconstruction. B2_Serve.py gained --offset the same day.
- The UPDATED preflight_check.py (uniqueness + split composition, --split) lived only in
  Paper2\4_Harness\; synced into the repo 2026-07-09. Keep repo ↔ 4_Harness mirror in sync.
- B3_spectrum_axes.py still works but double-judges; for the full run use B4 + E3 only.
- Cost/scale: Sprint-1 build alone cost ≈ $500; full run = 912 x (Q1..Q6 + naive) + 8
  configs x Q5/Q6 + E3 judging 912 x 9 with Pro — estimate before launching, and remember N≥3.


---

# STATUS AS OF 2026-07-20 — EVALUATION CAMPAIGN COMPLETE

**All three pre-registered runs executed, scored, sealed, and tagged.** Numbers may enter
the paper only from Tier-2 archives (rule unchanged).

| Run | Corpus | N | Archive (Tier 2) | Tag | Judge |
|---|---|---|---|---|---|
| 1 | DelucionQA (full) | 912 | results/run1_delucionqa/ | run1-complete | 2.5-pro; RE-JUDGED under 3.1-pro-preview → results/run1_rejudge/ |
| 2 | HAGRID K=150 drop-junk | 163 | results/run2_hagrid/ | run2-complete | 3.1-pro-preview |
| 3 | ExpertQA K=150 drop-junk | 150 | results/run3_expertqa/ | run3-complete | 3.1-pro-preview |

CORRECTIONS to earlier sections of this file (kept above for provenance):
- Judge lock: gemini-2.5-pro was WITHDRAWN by Google 2026-07-19; locked successor =
  gemini-3.1-pro-preview (deviation-logged; dual-judge robustness on run 1: κ=0.681).
- Build models: gemini-3-flash-preview (run 1) → gemini-3.1-flash-lite (runs 2–3), forced
  by degradation/withdrawal; disclosed per manifest.
- N≥3 repeats: superseded 2026-07-12 by cross-corpus design + bootstrap CIs (deviation log).
- Archive names: run2 = results/run2_hagrid/, run3 = results/run3_expertqa/ (run order
  swapped 2026-07-19; the "run2_expertqa / run3_hagrid" names above are obsolete).
- Change sets 5–6 gate: signed off (relayed 2026-07-09) before run 1.

HEADLINE (consistent judge; details in docs/Analysis_CrossRun.md + Frontier_ThreeCorpora.png):
frontier shape slope/band/cliff tracks ontology-aligned share (98.2% / 47.2% / 25.8%);
G2-tier corrRef stable at ~75–78% on all corpora while its false-rejection price varies
(51→85%); H4 auditability supported everywhere (97.7–100% resolvable citations); H2 refuted
everywhere (faithfulness ceiling); H1 parity in-ontology only, judge-sensitive (Δ .034 vs
.080; CIs in Analysis §8). Total runs-2+3 marginal cost < $45 (vs ~$720 run-1 all-in).

CURRENT SPRINT: 7C (positioning + venue decision with Dr. Xu) then 8 (manuscript).
Tracker: paper2-tracker artifact + Paper2/1_Planning/Sprint_Log.md.
