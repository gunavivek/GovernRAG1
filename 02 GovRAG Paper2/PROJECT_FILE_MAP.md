# GovRAG Paper 2 — Complete File Map (crash-recovery inventory)
*Written 2026-07-22. If a session or the app crashes: open a new session, mention
"GovernRAG Paper 2" (the govrag-operator skill loads project context automatically),
and point Claude at this file. Everything below is on YOUR disk or GitHub — nothing
essential lives only inside a chat session.*

## 1. THE ACTIVE WORKSPACE (write the paper from here) — consolidated 2026-07-22
`C:\Users\gunav\repos\conceptual_GraphRAG\02 GovRAG Paper2\`
- **GovRAG_Paper2_Master.docx** — THE document (46 pp; read/mark up here)
- GovRAG_Paper2_Master.md — same content, Claude's editing source
- **Source_Register.docx** — the spine: chapter → source → canonical → sealed evidence
- **References.docx** — working bibliography (31 IEEE-numbered entries, ⚠ = verify at extraction)
- PROJECT_FILE_MAP.md — this file · paper2_tracker.html — offline tracker copy
- `1_Sources\` — 20 snapshot docs (each stamped with canonical path; edit canonical, re-snapshot)
- `2_Prior_Art\` — CogniGraph + SITL PDFs, 3 Elicit reports (citation library)
- `3_Figures\` — Frontier_ThreeCorpora.png · Run1_Governance_Frontier.png · Supplement pdf/html

## 2. PARKED (ignore until a Paper1+2 merge is needed — Scenario 2 only)
`C:\Users\gunav\repos\conceptual_GraphRAG\01 Master GovRAG\`
- GovRAG_Master.docx/.md (combined-master shell), Master_Sprint_Plan.docx/.md

## 3. SEALED EVIDENCE (read-only; every paper number traces here; NEVER edit)
Repo `results\`:
- run1_delucionqa\ (47 files + SHA256SUMS + output_final_state\, 83 files)
- run1_rejudge\ (successor-judge re-judge of all 8,208 pairs + SHA256SUMS)
- run2_hagrid\ (23 files + SHA256SUMS) · run3_expertqa\ (+ SHA256SUMS)
- Working-slot leftovers (E3_run*_*.csv/jsonl, *.bad_join evidence) — transient tier
Repo `index\`: delucionqa\, hagrid_run2\, expertqa_run3\ (build snapshots + manifests)
  (+ index\_to_delete_hagrid_run2_contaminated and repo _quarantine\ — safe to delete by hand)
Repo `data\`: delucionqa_records_912.csv · hagrid_run2_* · expertqa_run3_* (selections +
  manifests with doc hashes) · parquet\ (RAGBench sources) · superseded expertqa_run2_*

## 4. GIT-TRACKED MIRRORS + TIMESTAMPS
Repo `docs\`: Analysis_Plan_and_Stopping_Rule.md (pre-registration + FULL deviation log) ·
Analysis_CrossRun.md (v4) · Subset_Selection_Validity.md · Run2/Run3_Manifest.yaml ·
Run2/Run3_API_Usage_Evidence_*.md · Venue_Options.md · Frontier png · Supplement html/pdf ·
GovRAG_Master.md · Master_Sprint_Plan.md · govrag-operator-SKILL.md
**GitHub: github.com/gunavivek/GovernRAG1 · branch paper2-spectrum · tags run1-complete,
run2-complete, run3-complete** — the public timestamp chain; everything above is pushed.

## 5. CODE (frozen pipeline + harness; edits need Vivek's approval, .bak* backups exist)
Repo root: B1_Build_Index.py · B2_Serve.py · B4_Batch_Runner.py · B5_Build_Runner.py ·
E3_Parallel_Evaluation.py · trace_scorer.py · serve_map_questions_to_chunks.py ·
preflight_check.py · build_gold_map.py · ragbench_select_and_prep.py · Start-GovRAG.ps1
(ALWAYS run the launcher first in any terminal) · .env (API key — keep private)
Repo `experiment\`: frozen D/M/Q/R pipeline (session edits, all approved+logged: M1, M2,
M3.3_HARDENED, M4_PARALLEL, M5_HARDENED added; Q3 empty-evidence; A1 labels)
Repo `runs\` + `logs\`: stage logs, A1 summaries, terminal transcripts, showcase_examples.json

## 6. ONEDRIVE Paper2 TREE (documentation home; auto-synced to cloud)
`...\3 Dissertation\conceptual_GraphRAG\Documentation\GovRAG\Paper2\`
- 1_Planning\: Sprint_Log.md (full history) · Master_Sprint_Plan.md · govrag-operator-SKILL.md
- 2_Design\: deviation log mirror · Subset_Selection_Validity.md · Run2_Runbook.md ·
  Problem_Statement_Throughput.md · BuildServe_Refactor_Plan.md · Model_and_Reproducibility_Protocol.md
- 3_Positioning\: Venue_Options.md · OKF SPEC/positioning/OKF_Demo\
- 4_Harness\: script mirrors of §5
- 5_Manuscript\: Related_Work.md · Prior_Art_Synthesis.md · Contribution_Positioning_Note.md ·
  Evaluation_Metrics_Definitions.md · Evidence_Scoping_Finding.md · Supplement (html+pdf) ·
  Run1_Advisor_OnePager/Brief · Prior Art Literature Review\ (Elicit reports + CogniGraph/SITL)
- 6_Results\: Analysis_CrossRun.md · Full_Benchmark_Run1_Results.md · Run1_Evidence\ ·
  Run2_Evidence\ (8 screenshots + note + manifest) · Run3_Evidence\ (3 screenshots + note + manifest)

## 7. PAPER 1 (for Scenario-2 merge or citation only)
`...\Documentation\GovRAG\Paper\GovernRAG_QUAIC_v10.2_FINAL.docx/.pdf` (+ manuscript_v10.1.md)
`...\Documentation\GovRAG\Dissertation Proposal_v3.pdf` (approved proposal)

## 8. COWORK-APP ITEMS (app-local; disk backups noted)
- Sidebar artifact `paper2-tracker` → offline copy: this folder's paper2_tracker.html
- Sidebar artifact `governance-dial-showcase` → disk copies: Supplement html/pdf (docs\ + 5_Manuscript\)
- Installed skill `govrag-operator` → disk copies: docs\ + 1_Planning\ SKILL.md

## 9. CURRENT STATE + NEXT STEP (as of 2026-07-22)
Campaign complete & sealed. Paper-2 master assembled (46 pp). NEXT: Vivek reviews fresh
chapters 1, 3.3, 6, 7.2, 9 → revisions → v1.0 (Jul 30) → QASC gate (Jul 31) → TPS extraction
→ SUBMIT Aug 15 (notify Sept 20). Committee replies pending (requirements + Dr. Wang status).
