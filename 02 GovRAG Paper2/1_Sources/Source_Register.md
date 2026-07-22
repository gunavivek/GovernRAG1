# Paper 2 — Source Register
*The spine of the consolidated writing workspace. One row per master chapter: what it was
built from, where the snapshot copy sits, where the canonical lives, the public git
timestamp, and which sealed archive backs its numbers. Written 2026-07-22.*

**Rules.** Snapshots in `1_Sources\` are read-only conveniences — edit the CANONICAL, then
re-snapshot. Every number in the master must trace to a sealed archive (`results\run*`,
`index\*`) via this register; archives are append-only and never edited. GitHub =
gunavivek/GovernRAG1, branch `paper2-spectrum`, tags `run1-complete` / `run2-complete` /
`run3-complete`.

## Register (by master chapter)

| Master ch. | Content | Status | Source doc (snapshot in 1_Sources\ unless noted) | Canonical location | Evidence backing (sealed) |
|---|---|---|---|---|---|
| Front matter | Extraction recipes S1/S2, reading guide | FRESH | — (authored in master) | master itself | — |
| 1 Introduction | Framing; §1.3 one-page Part-1 substrate | FRESH — review | Contribution_Positioning_Note.md; Paper 1 (GovernRAG_QUAIC_v10.2_FINAL, in GovRAG\Paper\); Dissertation Proposal_v3.pdf | OneDrive 5_Manuscript; GovRAG\Paper; GovRAG root | — |
| 2 Related work & positioning | Four streams; three-position framing; unfilled slot | VERBATIM | Related_Work.md; Contribution_Positioning_Note.md; Prior_Art_Synthesis.md; prior-art library in 2_Prior_Art\ (CogniGraph, SITL PDFs + 3 Elicit reports) | OneDrive 5_Manuscript | — |
| 3 System & harness | Problem statement; build/serve refactor; §3.3 harness narrative incl. incidents | VERBATIM + FRESH §3.3 — review | Problem_Statement_Throughput.md; BuildServe_Refactor_Plan.md; (background: Governance_Spectrum_Design.md, Evaluation_Design.md) | OneDrive 2_Design | code in repo root + experiment\ (approved edits, .bak*) |
| 4 Methodology & pre-registration | Analysis plan; FULL deviation log; subset validity; metrics; evidence scoping | VERBATIM | Analysis_Plan_and_Stopping_Rule.md; Subset_Selection_Validity.md; Evaluation_Metrics_Definitions.md; Evidence_Scoping_Finding.md; Run2_Runbook.md | repo docs\ (+ OneDrive 2_Design mirror) — deviation log git-timestamped BEFORE execution; selection commit 54ef322 | data\ selections + provenance manifests |
| 5 Results | Run 1 full benchmark; runs 2–3; cross-run analysis; figures | VERBATIM | Full_Benchmark_Run1_Results.md; Analysis_CrossRun.md (v4); Run2_Manifest.yaml; Run3_Manifest.yaml; figures in 3_Figures\ | repo docs\ + OneDrive 6_Results | results\run1_delucionqa (+output_final_state), run1_rejudge, run2_hagrid, run3_expertqa — SHA256SUMS each; index\<corpus> |
| 6 Discussion | Cost/buy; frontier taxonomy; H2 honesty; 2026 positioning | FRESH — review | Analysis_CrossRun.md; Prior_Art_Synthesis.md; cost data in run manifests | as above | run archives (costs, counts) |
| 7 Reproducibility & threats | Model/repro protocol; §7.2 consolidated threats | VERBATIM + FRESH §7.2 — review | Model_and_Reproducibility_Protocol.md; Run2/Run3_API_Usage_Evidence_*.md | OneDrive 2_Design; repo docs\ | Run1/2/3_Evidence\ packs (screenshots + notes), OneDrive 6_Results |
| 8 Artifact inventory | What exists, where, hashes | ASSEMBLED | PROJECT_FILE_MAP.md (02 folder root) | 02 folder + repo docs\ | all archives + git tags |
| 9 Future work | Conformal wrapper; run-4 prediction test; KG paper | FRESH — review | Prior_Art_Synthesis.md (Tayebati note); Venue_Options.md | OneDrive 5_Manuscript; repo docs\ | — |

## Key cross-cutting numbers → where they come from

| Claim/number | Sealed source |
|---|---|
| Frontier slope/band/cliff; ontology-aligned share 98.2/47.2/25.8% | Analysis_CrossRun.md v4 ← results\run1_rejudge + run2_hagrid + run3_expertqa |
| G2 corrRef 75–78% vs naive 41–44%; falseRej 51→85% | same |
| H4 auditability 97.7–100% | same |
| H2 refuted (faithfulness ceiling ≥0.98) | same — never claim hallucination reduction |
| H1 judge-sensitivity (κ=0.681; Δacc −.018 vs −.065) | run1_delucionqa vs run1_rejudge (8,208 pairs both judges) |
| Costs (Run 1 ~$720 all-in; Runs 2+3 <$45) | run manifests + API usage evidence + AI Studio screenshots (6_Results\Run*_Evidence) |
| Selection anti-cherry-picking (4 tests; junk filter §2b) | Subset_Selection_Validity.md + commit 54ef322 + selection JSON manifests in data\ |

## Consolidated folder layout (after 2026-07-22 consolidation)

```
02 GovRAG Paper2\
  GovRAG_Paper2_Master.docx/.md   Source_Register.docx (this)   References.docx
  PROJECT_FILE_MAP.md             paper2_tracker.html
  1_Sources\    20 snapshot docs (each stamped with its canonical path)
  2_Prior_Art\  CogniGraph + SITL PDFs, 3 Elicit reports, → References.docx
  3_Figures\    Frontier_ThreeCorpora.png, Run1_Governance_Frontier.png,
                Supplement_Governance_Dial_Examples.pdf/.html
```
