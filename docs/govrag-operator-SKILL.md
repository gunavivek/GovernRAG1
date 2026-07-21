---
name: govrag-operator
description: Operating manual for Vivek's GovernRAG PhD dissertation project (Paper 2, conceptual_GraphRAG repo). Use this at the START of any session that touches this project — before running pipelines, editing any code, analyzing results, writing the master-paper2 chapter or venue papers, or updating trackers. Trigger whenever the user mentions GovernRAG, GovRAG, Paper 2, the governance frontier, runs 1–3, sealed archives, the deviation log, B4/B5/E3P, DelucionQA/HAGRID/ExpertQA, the dissertation defense, or venue/submission planning — even casually. A session that starts without this context has previously cost days of rework; load it first.
---

# GovernRAG Operator

## What this project is
Vivek Gunasekaran's PhD dissertation (UA Little Rock; advisor Dr. Xiaowei Xu; committee
Dr. Talburt, Dr. Wu, Dr. Wang). GovernRAG is a governed concept-graph RAG framework:
answers must cite evidence, use only authorized sources, and refuse when evidence is
insufficient, with complete decision logs. Paper 1 (QASC 2026, submitted) introduced the
framework with a 10-question pilot. Paper 2 delivered the pre-registered, three-corpus
benchmark evaluation (DelucionQA 912 q · HAGRID 163 q · ExpertQA 150 q) of the governance
dial G0–G4. The campaign is COMPLETE and sealed; current work is analysis→manuscript→defense.

## First actions in any session
1. Read the sidebar artifact `paper2-tracker` (or `Paper2/1_Planning/Sprint_Log.md`) for
   current sprint state. Work ONE task at a time, top to bottom — Vivek's explicit preference.
2. Read `PROJECT_STATUS.md` and `RESEARCH_LOG.md` at the repo root; the LAST dated section
   supersedes earlier sections (they are append-only with corrections noted, not rewritten).
3. Any terminal work starts with the launcher:
   `& "C:\Users\gunav\repos\conceptual_GraphRAG\Start-GovRAG.ps1"` — verify its three printed
   lines (repo folder, key prefix AIzaSyDhK, venv python) before any command. Never assume a
   terminal is in the right folder; a wrong-tree run once wasted 3 hours of build.

## Standing rules (Vivek's, verbatim intent — do not relax)
- **Code changes require Vivek's approval — every time.** Frozen pipeline code
  (`experiment/`) AND harness code (B1–B5, E3P, serve/map/preflight scripts). Markdown/status
  docs are pre-authorized. Always create `.bak*` backups (gitignored) before edits, and
  grep the ENTIRE harness for any id/format/model string you change — a one-sided change
  once silently invalidated a full scoring run.
- **Deviation log before execution.** Any change to models, metrics, data, or procedure is
  entered in `docs/Analysis_Plan_and_Stopping_Rule.md` (+ OneDrive Paper2/2_Design mirror)
  and pushed to GitHub BEFORE the affected step runs. Commits are the public timestamps.
- **Two-tier artifacts.** `output/` and canonical `results/` filenames are transient working
  slots. Per-run archives (`results/run1_delucionqa/`, `run1_rejudge/`, `run2_hagrid/`,
  `run3_expertqa/`, `index/<corpus>/`) are append-only, SHA-256-manifested, read-only.
  Paper numbers come ONLY from archives. Never write into an archive; history only gains files.
  Before any new build: quarantine stale M-stage partials from `output/` (stale-resume hazard).
- **Paste one command at a time** in Vivek's terminal; never chain past a failure.
- Google models get withdrawn mid-study (it happened 4× in one day). Before any run: probe
  the exact model strings live. Current pins: build gemini-3.1-flash-lite · embeddings
  gemini-embedding-001 · serve/naive gemini-3.5-flash · judge gemini-3.1-pro-preview
  (a PREVIEW — assume mortal; dual-judge protocol exists for run 1).

## File map
- Repo (git, GitHub gunavivek/GovernRAG1, branch paper2-spectrum):
  `C:\Users\gunav\repos\conceptual_GraphRAG\` — code, `docs/` (deviation log, analysis,
  manifests, figures, supplement), `data/` (selections), archives under `results/` + `index/`.
- OneDrive Paper2: `...\3 Dissertation\conceptual_GraphRAG\Documentation\GovRAG\Paper2\`
  — 1_Planning (Sprint_Log) · 2_Design (deviation log mirror, validity doc, runbook) ·
  3_Positioning (Venue_Options, OKF) · 4_Harness (script mirrors) · 5_Manuscript (supplement,
  master-paper2) · 6_Results (Analysis_CrossRun, evidence packs RunN_Evidence with
  screenshots + manifests).
- Key docs: `Subset_Selection_Validity.md` (anti-cherry-picking, 4 tests + §2b junk filter),
  `Analysis_CrossRun.md` (all cross-run numbers), `Supplement_Governance_Dial_Examples.*`
  (11 worked examples), `Frontier_ThreeCorpora.png` (headline figure).

## Campaign results (sealed; cite from archives)
Frontier shape tracks ontology-aligned concept share — slope (DelucionQA, 98.2%) → band
(ExpertQA, 47.2%) → cliff (HAGRID, 25.8%); EXPLORATORY, not pre-registered. Stable across
corpora: G2-tier correct refusal 75–78% (vs 41–44% naive); auditability 97.7–100% (H4
supported everywhere); faithfulness at ceiling (H2 refuted — do NOT claim hallucination
reduction). ExpertQA: governance beats naive 65% vs 55% GA (refuse-all=70% caveat). H1
parity judge-scoped: Δ −.018 [−.050,+.014] original judge vs −.065 [−.090,−.041] successor
(κ=0.681). Costs: run 1 ~$720 all-in; runs 2+3 <$45 combined.

## Writing workflow: master-paper2 (chapter-first)
Write the dissertation Study-2 chapter FIRST; venue papers are EXTRACTIONS from it.
Every section is marked CORE (goes into venue extractions) or EXT (dissertation-only:
Paper-1 continuity, proposal-contribution mapping, extended lit review, full deviation log).
The Framework section exists at TWO depths: a 1-page summary (CORE-S1) and the full
architecture (CORE-S2/EXT). Results tables are marked headline vs supplement to enable
page-limit compression. Map the proposal's four committed contributions (BA-aligned RAG
framework · concept mapping · TRACe enterprise metrics · adoption pathway) to delivered
evidence explicitly — that mapping IS the defense narrative.

## Publication scenario decision tree
- Primary venue: IEEE TPS 2026 (Round 2 submit Aug 15, notify Sept 20). Fallbacks: IEEE
  Big Data 2026 workshops (Oct→Nov), AAAI-27 workshops. Paper A (KG-framed) → ESWC/ICKG 2027.
  Full map: `3_Positioning/Venue_Options.md`.
- **Scenario 1 — QASC accepts Paper 1:** Paper 2 goes standalone to TPS using the 1-page
  framework summary (CORE-S1), CITING Paper 1; published text may not be reused.
- **Scenario 2 — QASC rejects Paper 1:** a combined framework+evaluation paper becomes
  possible (CORE-S2 promotes the full framework section; results compress per the
  headline/supplement marking); Paper 1's unpublished text is then freely reusable.
- **Timing gate:** if QASC's decision arrives after Aug 15, submit TPS in Scenario-1 form
  regardless, citing Paper 1 as "under review". Scenario 2 only activates if BOTH reject.
- Pending committee answers (emails sent 2026-07-21): grandfathering of the two-paper
  requirement (Vivek entered Jan 2021, requirement added ~2022/23); venue types that satisfy
  the milestone; acceptance-letter vs published; Dr. Wang's committee status. Do not lock
  the venue plan until these arrive.

## Known hazards (each cost real time once)
Stale-resume: M3.3/M4/M5 resume from any leftover `output/` file regardless of corpus —
clean the slot first, verify node counts against the fresh M3 graph. Wrong-folder terminals:
launcher first, always. Model withdrawal: probe before spend; log + repoint with approval.
Judge changes shift accuracy LEVELS but not frontier STRUCTURE — restate comparisons under
one judge. E3P/trace_scorer parse quirks: new judges may wrap JSON in lists. Empty-evidence
questions (all chunks yield zero triples) are a legitimate governed state, not an error.
