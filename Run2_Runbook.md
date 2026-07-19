# Run 2 Runbook — ExpertQA (and template for Run 3 — HAGRID)
*Created 2026-07-12. Execute top to bottom; do not skip. Each ☐ is checked before the next starts.*

**TERMINAL RULE (added 2026-07-19 after the wrong-tree M1 incident): every session starts with**
`& "C:\Users\gunav\repos\conceptual_GraphRAG\Start-GovRAG.ps1"`
**and you verify its three printed lines (repo folder · key prefix AIzaSyDhK for run 2 · venv python)
before typing anything else. CORPUS CHECKPOINT: the first M1 `View:` line must say
`Record EXPERTQA_CORPUS` — if it names any other corpus, Ctrl+C immediately.**

## Phase 0 — One-time protections (if not already done)
- ☐ `attrib +R "results\run1_delucionqa\*" /S` and `attrib +R "index\delucionqa\*" /S`
- ☐ Confirm `.gitignore` covers `.env` (`git check-ignore .env` → prints `.env`)
- ☐ Create API key **govrag-run2-expertqa** in AI Studio (same project → keeps Tier 3);
    put it in `.env`; record the key NAME in the run-2 manifest. Do not rotate mid-run.

## Phase 1 — Timestamp + commit (pre-registration attestation)
- ☐ The amended Analysis Plan (deviation entry dated 2026-07-12) is in
    `Documentation\GovRAG\Paper2\2_Design\` AND copied into the repo at `docs\`.
- ☐ `git add -A` → commit `"Run 2 prep: run-guard B4, selection script, amended analysis plan"`
    → `git push origin paper2-spectrum`  ← GitHub timestamp BEFORE any run-2 generation.

## Phase 2 — Corpus selection + prep (deterministic, no LLM calls)
- ☐ `python ragbench_select_and_prep.py --subset expertqa --label run2 --top-docs 60`
    → check the printed answerable/unanswerable mix (unanswerable MUST be > 0; expect a large
    N-stratum for ExpertQA). Outputs: `data\expertqa_run2_{corpus,questions}.jsonl`,
    `expertqa_run2_records.csv`, `expertqa_run2_selection.json`.
- ☐ `python build_gold_map.py --source data\expertqa_run2_questions.jsonl`
    → overwrites `results\gold_map.json` (working slot; delucionqa's is archived). 100% gold coverage expected.

## Phase 3 — Build the reduced graph (the ~$20–40 step)
- ☐ Run the D/M build chain on `data\expertqa_run2_corpus.jsonl` the same way the delucionqa
    build was done (A1 runner → B1_Build_Index snapshot to `index\expertqa_run2\`).
    ⚠ VERIFY TOGETHER FIRST: the A1/B1 invocation for a new corpus name — smoke it, then run.
- ☐ Confirm `index\expertqa_run2\` exists with a build manifest; `attrib +R` it.

## Phase 4 — Serve map + preflight (no LLM calls)
- ☐ `python serve_map_questions_to_chunks.py --records data\expertqa_run2_records.csv`
    → ~97%+ chunk coverage expected (substring mapping).
- ☐ `python preflight_check.py --records data\expertqa_run2_records.csv --k 25`
    → must print **READY** (100% gold join, 0 empty gold, unanswerable > 0). Record split line.

## Phase 5 — Generation (batched, resumable)
- ☐ Smoke: `python B4_Batch_Runner.py --records data\expertqa_run2_records.csv --k 25 --run-tag run2_expertqa --batches 0`
    → inspect batch 0 outputs/timing, then:
- ☐ Full:  `python B4_Batch_Runner.py --records data\expertqa_run2_records.csv --k 25 --run-tag run2_expertqa`
    (≈4–5 batches at ~100 questions; accumulators in `results\full_run_run2_expertqa\`;
    crash-safe: rerun the same command. On completion B4 auto-archives to `results\run2_expertqa\`.)

## Phase 6 — Scoring (parallel, checkpointed)
- ☐ `python E3_Parallel_Evaluation.py --judge-model gemini-2.5-pro --workers 12 --out-prefix E3_run2_expertqa`
    (resumable; rerun same command after any interrupt; outputs `results\E3_run2_expertqa_*.csv`.)
- ☐ Copy the two `E3_run2_expertqa_*.csv` files into `results\run2_expertqa\`.

## Phase 7 — Close the run (before ANYTHING else happens)
- ☐ Manifest: assemble `Run2_Manifest.yaml` (git commit, key name, per-key usage from AI Studio,
    daily spend, selection.json checksums, timing) → `results\run2_expertqa\` + OneDrive evidence pack.
- ☐ `SHA256SUMS.txt` over `results\run2_expertqa\`; copy to OneDrive evidence pack.
- ☐ `attrib +R "results\run2_expertqa\*" /S`
- ☐ `git add -A` → commit → `git tag run2-complete` → `git push origin paper2-spectrum --tags`
- ☐ Update Sprint_Log / PROJECT_STATUS / RESEARCH_LOG (Claude does this on request).
- ☐ Only now may Run 3 (HAGRID: same runbook, `--subset hagrid --label run3 --run-tag run3_hagrid`,
    key `govrag-run3-hagrid`) begin.

## Known open item to resolve at Phase 3
The A1→B1 build chain has only ever been invoked for delucionqa/emanual; its exact arguments for a
new corpus name must be verified before running (Claude will read the A1/B1 code and give the exact
command when Phase 3 is reached — do not guess).
