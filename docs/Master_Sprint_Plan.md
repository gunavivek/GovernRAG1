# Master Sprint Plan — GovRAG_Master build → TPS submission
*Created 2026-07-21. One task at a time, in order. Each task has a Definition of Done.
Working doc: `5_Manuscript/GovRAG_Master.md` (skeleton v1, extraction recipes at top).
Calendar anchors: QASC/QUAIC decision ~Jul 31 · TPS R2 submission Aug 15 · TPS decision Sept 20.*

## Sprint M — Build the Master (Jul 22–31, before the QASC gate)

| # | Date | Task | Sources | Definition of Done |
|---|---|---|---|---|
| M-1 | Jul 22 | §0.2 Proposal-contribution map + §0.3 program timeline | Proposal v3 §5, Email B text, Sprint_Log | Four contributions → delivered evidence → file path; every row auditable |
| M-2 | Jul 22–23 | Port Paper 1 §§1–2 → master ch 1–2 (program-level intro; related-work base) | GovernRAG_QUAIC_v10.2_FINAL | Chapters read as master text; citations intact; 2026-delta slot marked |
| M-2b | parallel (Claude) | 7C-1 prior-art delta (CogniGraph, Jain, Korosuke + any new) → ch 2 insert | 3_Positioning folder + fresh search | Delta paragraphs drafted with citations; single-operating-point vs frontier argument |
| M-3 | Jul 23–24 | Port Paper 1 §§3–7 → master ch 3 (framework), 4 (DSR), 5 (pilot+ablation) | Paper 1 v10.2 | Sourced chapters assembled; §5.5 bridge paragraph (n=10 limit → Part 2) drafted |
| M-4 | Jul 24 | **§3.9 one-page framework summary** (Scenario-1 linchpin) | ch 3 + dial supplement | Fits one page; standalone-readable; cites Paper 1 |
| M-5 | Jul 25 | Ch 6 scale-out prose (build-once/serve-many, hardening, cost economics) | 2_Design docs, PROJECT_STATUS, manifests | O(C_build+n·C_query) argument + $222 vs <$45 numbers, archive-cited |
| M-6 | Jul 26–27 | Ch 7 evaluation methodology assembly | Analysis plan, Subset_Selection_Validity, Analysis §7 | Pre-registration, selection+junk filter, metrics, dual-judge protocol — one coherent chapter |
| M-7 | Jul 27–28 | Ch 8 results assembly + ch 10 threats merge | Analysis_CrossRun §2–§8, Paper 1 §7.1 | All tables in, headline/supplement marks verified; threats merged Part1+Part2 |
| M-8 | Jul 29 | Ch 9 discussion (9.1 pass · 9.2 slope/band/cliff taxonomy · 9.3 H2 honesty) + ch 12 | Analysis §5, Paper 1 §8–9 | Deployment guidance explicit; no hallucination-reduction claim anywhere |
| M-9 | Jul 30 | Ch 11 + appendices assembly; full read-through; **master v1.0** | deviation log, manifests, evidence packs | Committed + pushed as v1.0; both extraction variants assemble cleanly on paper |
| M-10 | Jul 31 | **QASC GATE** — decision arrives → pick extraction recipe (S1 or S2) | QASC notification | Scenario recorded in master §0 + deviation-style note; Sprint E scoped |

## Sprint E — Extraction → TPS (Aug 1–15)

| # | Date | Task | Definition of Done |
|---|---|---|---|
| E-1 | Aug 1–3 | Assemble chosen recipe (S1 or S2) from master; TPS IEEE template | Complete draft in template, within page limit |
| E-2 | Aug 4–6 | Compression pass (results → headline only; supplement referenced); figures finalized | Reads as a paper, not an excerpt |
| E-3 | Aug 7–11 | Internal review → send to Dr. Xu; incorporate feedback | Dr. Xu comments in; revision complete |
| E-4 | Aug 12–14 | Final polish: abstract, threats, reproducibility statement, references | Submission-ready PDF |
| E-5 | Aug 15 | **SUBMIT to IEEE TPS R2** | EDAS/portal confirmation archived in evidence pack |

## Standing side-threads (do not block the sprint)
- Committee replies (Emails A/B) → 7C-5 venue lock; adjust E-track only if answers demand it.
- AAAI-FSS hedge (Aug 1) — only if committee confirms symposium counts AND a fitting
  symposium is identified by Jul 28; otherwise drop without regret.
- Optional run 4 (moderator prediction test) — only if M-sprint runs ahead of schedule.
- Tracker + Sprint_Log updated at every task completion (Claude, pre-authorized).

## Rules for this sprint (inherited)
Master is the only edited document; papers are extractions. Every number archive-cited.
New claims require evidence or the EXPLORATORY label. H2 stays refuted — reframe, never
oversell. One task at a time; a task is done when its DoD says so, not before.
