# Dissertation Defense — Session Handoff

> ## ⚡ CURRENT-STATE ADDENDUM (2026-08-23 close of day — read this FIRST, then the original below)
>
> **Canonical tracker now = `Defense_Project_Plan.md` in this folder** (16 phases D0–D15,
> 72 activities, decision log). The original handoff below (written 2026-08-16) predates it;
> where they differ, the plan wins. Progress: **30/72**. Cowork artifact `defense-tracker`
> mirrors it.
>
> **State:** D0 closed · D5 substantively complete (all chapters poured to
> `01 Master GovRAG\GovRAG_Master.md`; ch-2 depth gated on Dr. Xu) · **D6.1 DONE → draft now v0.3:
> `GovRAG_Dissertation_DRAFT_v0.3.docx`** (107 pp, committed; v0.2 → zz_Records by
> Vivek): §3.9 + §7.5/Table 7.2 POURED (master too) · Figures 3.1 & 8.1 INLINE with
> captions (3.2/3.3 still to source from 5_Drafts) · abbreviations in list form ·
> PC-table on FIXED layout (Word ignores width hints under autofit — lesson: explicit
> widths always need tblLayout fixed) · custom pandoc reference (template styles.xml
> breaks tables; decision log has the recipe). Committee walkthrough deck
> (`GovernRAG_Committee_Walkthrough_v1.pptx`, 11 slides + notes) and one-page
> `GovernRAG_Reading_Guide.docx` (v0.2 pagination) ready in the 03 folder. · **D1.2 DONE: 1:1 request
> SENT to Dr. Xu** (v6: MID-SEPTEMBER window intent → committee copy early Sept; QASC
> withdraw→arXiv question; title evolution) · **Dr. Wang: left UALR but committee-eligible
> (Talburt confirmed affiliation 2026-08-20); Vivek SENT him a high-level review request
> (his own wording, asking for 45–60 min THIS WEEK)** · Title Option B locked (Xu ratifies)
> · Mid-Sept consequence: read-through + D6.2 + §3.9 pour must close in ~10 days.
>
> **Folder layout (2026-08-22):** the 03 folder root holds only the live working set
> (plan · handoff · feedback ledger · glossary · draft v0.2 · reading guide ·
> walkthrough deck · D1_1/D10_2 outreach · GradSchool\). All closed records —
> D5_* proposals/reports, D0_Gap_Audit, P1_Backport_Checklist, D6_2 pour proposal,
> draft v0.1 — are in `zz_Records\`.
>
> **2026-08-22 additions:** `D6_Review_Feedback_Ledger.md` created — read-through
> comments land there and apply in BATCHES (Batch 1 open, empty so far; claim/number
> edits still get FROM→TO confirmation). `Defense_QA_Prep.md` (D12.1 IN PROGRESS): now A1–A8 (Vivek's read-through
> questions incl. counts discipline, frontier, faithfulness/predictor/provenance, M4
> alignment mechanism) + 15 anticipated committee questions + drill protocol.
> Ledger Batch 2 OPEN: §0.2 retitle APPROVED-pending ("Proposal commitments and
> their delivery — the defense spine", 3-occurrence sweep + glossary DR-4 row) ·
> landscape/broadside ruling pending (advice: portrait; decide at Table 8.2; confirm
> with Grad School via D1.3 forms item). Walkthrough deck now 13 slides (evidence-
> base backup + annotated slope/band/cliff discovery slide).
> No replies yet from Dr. Xu or Dr. Wang as of 2026-08-23 close.
>
> **In Vivek's court:** read-through of draft v0.2 (seam sentences aloud; comments → ledger) · replies from
> Dr. Xu (→ D1.3 capture list in `D1_1_Dr_Xu_Meeting_Request.md`) and Dr. Wang (prep in
> `D10_2_Dr_Wang_Review_Request.md`: draft v0.1 or ch-0 map as orientation) · personal
> texts for D6.2 (Acknowledgments, [Program Title], month/year, dept/college).
>
> **Session's next work item:** D6.2 the moment the read-through returns — real TOC/LoF/LoT,
> Tables 8.2/E.1, Figures 3.1–3.3/8.1, placeholders, §3.9 pour from TPS v1.8 shell, then
> re-run P3 (D6.3) + guidelines checklist (D6.4). §3.9 pour: DONE 2026-08-21. Build
> artifacts live in the cloud workspace (`build_source.md`, `custom_reference.docx`,
> PC-table width post-processor in the decision log) — if the container was reclaimed,
> rebuild per the decision-log recipe. Cautions on file: arXiv Paper 1 BEFORE Sept 20 could
> compromise TPS double-blind (raise at D1.3); if Wang meets before Xu, mention the chair
> is in the loop.


*Written 2026-08-16, at the close of the Paper-2 submission session. Purpose: start the
dissertation-defense work in a NEW session with full context. First actions in the new
session: (1) load the `govrag-operator` skill; (2) read this document end to end;
(3) confirm the standing rules below before any file is touched.*

---

## 1. Who and where

Candidate: **Vivek Gunasekaran** (UA Little Rock). Advisor: **Dr. Xiaowei Xu**.
Committee: **Dr. John Talburt** (PhD program head), **Dr. Wu**, **Dr. Wang**.
Proposal defended: **April 2025**. Fall semester starts end of August 2026.
Publication is **NOT** a graduation requirement at this university.
Graduate School gate for fall graduation: defense completed AND manuscript submitted
for format review by **December 1, 5 pm** (ualr.edu/gradschool/thesis-and-dissertation-information).
Program-level rules (announcement lead time, committee-copy lead, Graduate School
representative requirement) are **UNVERIFIED** — task D2 below.

## 2. The two papers

**Paper 1 — the conceptual pilot.** "GovernRAG: A Governance Manifest Architecture with
Reference Monitor Mediation for Auditable RAG" (v25). Introduces the architecture
(manifest, reference monitor, answer gate, governance dial), demonstrated on ten cases.
Status: submitted to QASC 2026; the venue went silent past its own notification date
(Jul 8); a status-inquiry email with an Aug 8 response deadline went unanswered; QASC
rescheduled its conference to Sept 25–27. **Withdrawal decision is OPEN (task D4).**
Fallback path decided earlier: withdraw → arXiv for timestamp/citability → IEEE Big Data
2026 workshops as peer-review venue. Paper 2 cites it as [33] "Anonymous authors …
under review"; the citation updates at TPS camera-ready per whatever is decided.
Files: `2_Prior_Art\GovernRAG A Governance Manifest Architecture...v25.pdf` +
`Supplementary_Material_A_B_C_D_E_v25.pdf`.

**Paper 2 — the benchmark evaluation.** "GovernRAG: Tunable Evidence Authorization for
Governed Retrieval-Augmented Generation." Submitted **IEEE TPS 2026, Research Track
Round 2, Submission #3778, Aug 15** (authors: Gunasekaran, Xu, Talburt; Vivek presenter).
Notification **Sept 20**; camera-ready **Sept 30**. Source: shell v1.8
(sha256 d695dcc740e4…); submitted PDF sha256 D3FA3434…BCF61, EasyChair stored copy
verified byte-identical. Dr. Xu signed off by email; confirmation forwarded to both
professors. Carries a three-sentence AI Disclosure (Claude / ChatGPT / Gemini named).

## 3. Asset inventory (device paths)

Root: `C:\Users\gunav\repos\conceptual_GraphRAG\`

| Asset | Path |
|---|---|
| Dissertation master document (completeness UNKNOWN — gap audit is task D0) | `02 GovRAG Paper2\` … `GovRAG_Master.docx` / `GovRAG_Paper2_Master.docx` (confirm which is canonical) |
| Proposal (April 2025) | `proposal.docx` — **Vivek to confirm exact path** |
| Dissertation ↔ Paper-2 mapping | `02 GovRAG Paper2\` … `Dissertation_to_Paper2_Mapping.docx` |
| Programme progression one-pager | `Programme_Progression_OnePager.docx` |
| Paper 2 shell v1.8 + Version_Log (hashes v1.0→v1.8) | `02 GovRAG Paper2\4_Submission\` |
| Submission PDF + record | `4_Submission\GovernRAG_Paper2_v1.8_SUBMISSION.pdf` |
| Locked instruments: Voice & Framing Guide v2, Flow Map, Manuscript Dictionary, Citation Use Table, Evaluation_Metrics_Definitions.md | `4_Submission\` and `1_Sources\` |
| Verification records: Citation_Verification_Ledger, W7_Numbers_Verification_Ledger_v1.8, Verify_v18_Numbers.py (138 checks; 3 accepted near-misses, author ruling 2026-08-13), T5 scrub report, T7 overlap check (CLEAN vs Paper 1), rebuttal reserve (axis variance) | `02 GovRAG Paper2\5_Drafts\` |
| Study diagrams (defense-deck raw material): one-page river v1/v2 (PDF+HTML), §II fishbone, §III canal works | `5_Drafts\` |
| Advisor deck (accuracy-verified digit-for-digit vs v1.8 minus the [4] fix) | Vivek's Google Slides + local pptx |
| Figures: Fig 1 architecture, Fig 2 frontier v2 + regeneration script | `02 GovRAG Paper2\3_Figures\` |
| Verified reference PDFs [1]–[4] (produce-the-source rule) | `02 GovRAG Paper2\2_Prior_Art\` |
| Sealed archives + frontier summaries (read-only, SHA-256 manifested) | `results\` (run1_delucionqa, run1 re-judge, run2_hagrid, run3_expertqa) |
| Frozen pipeline code | `experiment\`, B1–B5, E3P at repo root |
| Pre-registration + deviation log (public; latest entry e1ba89e) | `docs\Analysis_Plan_and_Stopping_Rule.md` + OneDrive mirror `Paper2\2_Design\` |
| Public artifact package [37] (74 files; expires 2027-06-30; auto-update OFF) | github.com/gunavivek/govrag-paper2-artifacts (private) → anonymous.4open.science/r/govrag-artifacts-26 |
| GAISS predatory-venue assessment (venue-decision record) | `5_Drafts\` + `4_Submission\Conference Venue\` |

**Headline numbers (all verified against sealed archives 2026-08-14):** corpora 912/163/150
(7.0/16.0/70.0% unanswerable); 1,225 q × 9 configs = 11,025 pairs, 8,208 dual-judged
(κ 0.681 jointly graded / 0.863 with refusals; 91.3% raw; 504/190); cRef 40.6–43.8 →
75.2–78.1% at G2; ExpertQA reversal GA 66.0 vs 55.3 (plain G2 64.7); faithfulness ≥0.98
both arms (H2 refuted); auditability 97.7–100% (H4 supported); cost ≈$765; monitor <1%
latency; ontology fit 98.2/47.2/25.8% (exploratory); 553-concept BIZBOK ontology.

## 4. Standing rules (carried over — confirm before work starts)

1. Sealed archives and `index/` are READ-ONLY; copies only; frozen `experiment/` +
   harness code changes require Vivek's approval, every time. New read-only analysis
   scripts are proposed before running.
2. Propose exact text → Vivek approves → pour. One task at a time.
3. Every git command set begins with the `cd` line; one command at a time; never chain
   past a failure.
4. Result-relevant changes get a deviation-log entry, pushed for public timestamp.
   No result, data, or sealed artifact is ever modified.
5. Numbers: symmetric precision; every number traces to a sealed archive or a dated
   verification record. Any edited document re-triggers a verification sweep.
6. New references enter only with the source document saved in `2_Prior_Art`
   (produce-the-source rule, adopted 2026-08-13).
7. Versioning: snapshot + Version_Log row with hash per major revision.
8. Voice: locked Voice & Framing Guide v2 (South Indian Engineering Professor register,
   curated markers, Indian-English caution list, GenAI ban list, rule zero: precision
   outranks style). Simple sentences in explanations.
9. No sycophancy; be objective; flag disagreements once, clearly, then respect rulings
   (recorded example: the three tabulated-rounding near-misses).
10. Manuscript PDFs, Paper-1 PDFs, and templates are NEVER committed to the public repo.
11. AI-use transparency: Paper 2 carries a disclosure; the dissertation's disclosure
    obligations are an OPEN question (D2) — same honesty standard applies.

## 5. The plan — sequential, dependency-listed (Vivek fills dates as tasks close)

| # | Task | Depends on | Owner | Date done |
|---|---|---|---|---|
| D0 | **Gap audit**: GovRAG master document vs April-2025 proposal commitments, chapter by chapter → work-list with effort estimates. Nothing is scheduled before this exists. | proposal path confirmed | Session + Vivek | |
| D1 | Dr. Xu ratifies: the plan, the defense window implied by D0's estimate, and the "papers under review" framing | D0 | Vivek | |
| D2 | Program coordinator query: announcement lead time, committee-copy lead, Grad School representative, dissertation AI-disclosure policy, format template | none — send early | Vivek | |
| D3 | Milestone wording pinned in writing with committee: "two venue-submitted papers satisfy the publication milestone" (or whatever the committee's answer is) | D1 | Vivek | |
| D4 | QASC resolution: formal withdrawal email; then the Paper-1 path decision (arXiv now vs hold for TPS outcome) | D1 | Vivek + session | |
| D5 | **Dissertation document sprint** per D0 work-list (proposal → Ch.1–2 base; Paper 1 → architecture chapter; Paper 2 → evaluation chapters; conclusions + contribution mapping) | D0, D1 | Session + Vivek | |
| D6 | Format pass per Grad School template + full verification sweep on the assembled document | D5, D2 | Session + Vivek | |
| D7 | Defense deck extracted from the document (advisor deck + river/canal/fishbone diagrams are ~70% of the raw material) | D5 | Session + Vivek | |
| D8 | Book the defense date + room with all committee members (as soon as D1 gives the window — do NOT wait for D5 to finish; the date disciplines the walkthroughs) | D1 | Vivek | |
| D9 | Committee copy delivered (document + deck), with the required lead per D2 | D6, D7, D8 | Vivek | |
| D10 | Individual walkthroughs: Dr. Xu first, then Dr. Wang, then Dr. Talburt (one round, time-boxed; briefing, not pre-agreement) | D9 | Vivek | |
| D11 | Incorporation pass: fold walkthrough feedback into document + deck; re-verify numbers if any changed | D10 | Session + Vivek | |
| D12 | Mastery drills + two mock defenses (session as hostile committee; diagonal questions) — runs in parallel with D10–D11 | D7 | Session + Vivek | |
| D13 | Logistics: defense announcement, forms, room/Zoom, tech check, printed river maps for the committee table | D8, D2 | Vivek | |
| D14 | **DEFENSE** | D11, D12, D13 | Vivek | |
| D15 | Post-defense: committee revisions → format-review submission (Dec 1 gate) → ProQuest upload | D14 | Vivek + session | |

External events that interleave (not dependencies, but calendar facts): **Sept 20** TPS
notification → if accepted, camera-ready by **Sept 30** (restore names, resolve [33]/[37]);
**Sept 25–27** QASC conference window.

## 6. Open questions (answer before or during D-tasks)

1. D2 set: announcement lead · committee-copy lead · Grad School rep · dissertation
   AI-disclosure policy · format template.
2. Milestone wording (D3) — never answered by the committee; pin it in writing.
3. QASC (D4): withdraw now? arXiv Paper 1 now or after TPS notification?
4. Which master document is canonical (GovRAG_Master vs GovRAG_Paper2_Master) and the
   proposal's exact path.
5. Defense date policy vs Sept 20: current recommendation is defend BEFORE the TPS
   notification (papers cleanly "under review"; avoids fresh-rejection optics), but the
   D0 estimate may force the date past it — decide with Dr. Xu at D1.

## 7. Scheduling email draft (D8 — dates blank)

> **Subject:** Dissertation defense scheduling — request for your availability
>
> Dear Dr. Xu, Dr. Talburt, Dr. Wu, and Dr. Wang,
>
> I am preparing to defend my dissertation, "GovernRAG: [final title]", this semester.
> Both venue papers are submitted: the architecture paper and the benchmark evaluation
> study (IEEE TPS 2026, Submission #3778, with Dr. Xu and Dr. Talburt as co-authors).
>
> May I request your availability in the week(s) of [WINDOW]? I will deliver the full
> dissertation document and the presentation to you at least [LEAD, per D2] before the
> date we fix, and I would like to offer each of you a brief individual walkthrough
> beforehand at your convenience.
>
> Thank you for your guidance through this work.
>
> Regards, Vivek G

## 8. Skills — which to use for the defense artifacts (recommended approach)

- **Every new-session start:** `govrag-operator` (it triggers on "dissertation defense")
  + this handoff. That pair replaces this session's memory.
- **D0 gap audit and all document reading:** `docx` skill (reading/extracting) and `pdf`
  skill (proposal and Paper-1 PDFs). Research-first rule: never open an output-format
  skill until the content work is done.
- **D5/D6 dissertation document:** `docx` skill for the build; Voice Guide v2 for prose;
  the verification-sweep pattern (a Verify_*.py against the sealed summaries) after any
  numbers are poured.
- **D7 deck:** `pptx` skill; `dataviz` skill BEFORE creating any new chart; reuse the
  manuscript figures and the study diagrams rather than redrawing.
- **D10–D12 critique and mocks:** `paper-reviewer` skill (mock committee, stress-tests,
  rebuttal drafting).
- **No new skill is required.** If the drill sessions prove repetitive, a small
  defense-drill skill can be created later with `skill-creator` — optional, not now.

## 9. What this session (the Paper-2 session) retains

TPS Submission #3778 follow-up stays HERE, not in the defense session: the Sept 20
notification, any rebuttal (reserve + five prepared Q&As are in 5_Drafts), camera-ready
(restore names, resolve [33] and [37], update Paper-1 citation), and the R11/R12
leftovers (calendar entries; syncing deck/fishbone/river maps to v1.8; housekeeping git
commit of accumulated 5_Drafts records).


## State at close, 2026-08-24 (night)
- Current reading copy: **v0.10** (111 pp, committed to 03 Dissertation Defense).
  Batch 6 APPLIED: §2.10 deleted; §8.3/§11.4 OKF claims corrected
  (demonstration-scoped, no "losslessly"/"vendor-neutral"); [81] Google Cloud OKF
  spec added (sole inline use §11.4); Table 0.1 PC4 evidence → §11.4. Master in
  01 Master GovRAG updated identically. Pagination UNCHANGED from v0.9 — reading
  guide valid as-is.
- Ledger: Batch 6 closed with full verification record. Open batch: EMPTY —
  next read-through comment starts Batch 7. Landscape ruling still pending
  (candidate: Table 2.1 header wraps).
- Q&A prep: A10 added (does GovernRAG emit OKF? — spoken answer).
- Vivek housekeeping: v0.7/v0.8/v0.9 → zz_Records; Lin + Shi PDFs into
  2_Prior_Art before committee copy; D6.2 personal texts; D2.4 PDFs; BOSS/Argos
  graduation application check; report Xu/Wang replies.
- Read-through position: Vivek was in ch 2 (§2.10 was the last comment); next
  session resumes reading v0.10 from ch 2 end / ch 3.

## State at close, 2026-08-25 (night)
- Current reading copy: **v0.11** (111 pp, committed). Batch 7 APPLIED (A1–A3,
  B1–B11, D-table; C1/C2 skipped per ruling). Pagination unchanged since v0.9 —
  reading guide valid.
- CITATION VERIFICATION COMPLETE for every inline occurrence in the document:
  ch 1–2 full audit (72 works, 104 claims) + ch 3–12 tail (14 keys incl. [35],
  [71]–[73], [81]) + ISO 42001 verified against Vivek's standard PDF + [37]
  verified real from his AI-SI 2025 IEEE PDF (initials fixed).
- New standing artifacts: Citation_Evidence_Map.md (42 rows, in 03 Dissertation
  Defense; ledger rule — map row updates travel with any citation-touching
  batch) · P1_Reference_and_RelatedWork_Patch.md (in 02 GovRAG Paper2; apply
  before any arXiv posting).
- Open batch: EMPTY (Batch 8 starts with next comment). Landscape ruling still
  pending.
- Vivek's next-session queue: (1) spot-check 5–8 Evidence Map rows against
  sources (audit-the-auditor); (2) confirm he can speak to the ~10 load-bearing
  comparators; (3) resume read-through — ch 2 needs only a voice/flow pass now,
  then ch 3 onward; (4) v0.9/v0.10 → zz_Records; (5) standing items (D6.2
  personal texts, D2.4 PDFs, BOSS/Argos check, Xu/Wang replies).
- Advice on record: citations no longer the blocker; remaining gates are D6.2
  front matter, guidelines checklist, and his read-through.

## State at close, 2026-08-26 (night)
- Row-by-row citation-support review of Citation_Evidence_Map_Review.docx in
  progress with Vivek. Rows 1 and 2 DONE, both ✓ (row 1: [29] McIntosh —
  confirmed against his PDF, contribution #3 + §4.5; row 2: six-key Observation-1
  sentence — all citations do their jobs post-B2 fix; noted the universal
  negatives are defended by Table 2.1/M-2b sweep, not by the citations).
- RESUME AT ROW 3 of Part 1 (ch 1–2, 30 rows total): "Gao et al.'s survey [16]
  organises RAG into Naive/Advanced/Modular…" — format per row: Claim /
  Paper's own words / Match assessment / suggested verdict.
- Open batch: EMPTY (his ✗/? verdicts become Batch 8 items).
- Everything else unchanged from 08-25 close (v0.11 current, verification
  complete, P1 patch + Evidence Map committed).

## State at close, 2026-08-28 (night)
- Current draft: **v0.15** (112 pp) — Figure 2.1 = workflow version (arabic
  p13), machine-reconciled against the map's RAG Phase column (PASS 81/81
  after adding [47]/[39] and recoding [71–73]→X, [75/78]→B).
- Batch 11 COLLECTING: Figure 2.1 → landscape/broadside section (plan + UALR
  page-number caveat logged; fallback = pre-rotated broadside image).
- PART 2 row review IN PROGRESS: Row 31 ✓ (R3.5/[7]; A27 added — LPG,
  two-pass build, 553). Row 32 PRESENTED, verdict pending — resume with a
  short recap of row 32 (§3.9 reference-monitor classical-sense, [3]/[38];
  witnesses = Q5 position in serve path + decision log; "within the serving
  pipeline" scope note re parametric channel), then row 33 (DSR positioning,
  Hevner [20]/Peffers [35]). 10 Part-2 rows remain after 32.
- Q&A prep now A1–A27. Review docx re-commit still pending (file open in
  Word). Housekeeping queue: v0.13/v0.14 → zz_Records.

## State at close, 2026-08-29 (night)
- PART 2 row review: rows 31–35 ✓ (31 R3.5/[7] · 32 §3.9 [3,38] incl. the
  "why not P4" placement question answered · 33 DSR [20,35] · 34 G–H [18] ·
  35 the full kernel table — all six keys given full per-key treatment after
  Vivek pressed on the shorthand; good procedure).
- RESUME AT ROW 36: the RAGBench refactor-plan sentence [15] (§6-area, dated
  plan → executed selection). Then 37–42: corpus selection [71–73], RAGBench
  roles ×2, metric families [15,49], OKF closer [81]. Seven rows remain.
- Q&A prep now A1–A30 (new: A28 DSRM mapping · A29 DP1–DP3 recitation ·
  A30 bounded-rationality aptness).
- Standing: Batch 11 collecting (Fig 2.1 landscape) awaiting Apply · review
  docx re-commit pending (open in Word) · v0.13/v0.14 → zz_Records ·
  current draft v0.15.

## 2026-08-29 close (Part I review day)

- Citation Evidence Map: ALL 42 ROWS VERIFIED (Part 2 rows 31-42 done; row 42
  OKF challenge resolved — artifact found at OneDrive Backup\Paper2\
  3_Positioning\OKF_Demo, conformance re-run PASS, copied to
  govrag-paper2-artifacts\OKF_Demo + 03 Dissertation Defense\OKF_Demo).
- Draft now v0.20 (112 pp). Batches 11-15 APPLIED same day: Fig 2.1 landscape
  page (9in) + rotated page number per Vivek's binding convention (binding
  along diagram top; number landscape bottom-right); badged Figure 3.1
  (C1/C2/C3, Fig31_Architecture_C123.png); SS3.2 two-pass clause + bounded
  vocabulary-agnostic claim; SS3.3 heading "+domain"; SS3.6 Xu-sign-off
  parenthetical REMOVED (Vivek lacks the 07-06/07-09 emails; ch11 cell
  sign-off-free; Appendix C verbatim log untouched — A36); SS3.9 retitled
  "Framework summary and trust model"; Tables 4.1/4.2 captioned.
- Build recipe now persisted: /home/claude/build_dissertation.py (pandoc +
  4-section layout + landscape header2 + 9in fig + fixed tables). Usage:
  python3 build_dissertation.py vNN.
- Q&A: A33-A35 (D/M/Q pipeline spoken explanations), A36 (sign-off), A37
  (kernel theory column).
- Git-commit tracker G1-G6 open in ledger (finalization-time, incl. sealed-
  archive mtime check G5).
- TOMORROW: Vivek reads PART II; Batch 16 opens on first comment. Also open:
  Reading Guide committed w/ p14 fix; Xu reconfirmation email = Vivek's call;
  D2.4 guidelines PDFs still pending (landscape number convention re-check).

## 2026-08-31 close (freeze + assembly day)

STATE: draft v0.31 (164 pp) committed. Review phase CLOSED (batches 6-21 all
applied; 36/36 incorporation audit PASS). D6.2 assembly COMPLETE except P3:
- Appendix B materialized (7 tables from sealed CSVs, hash-verified).
- SS8.5 + Figure 8.2 regenerated from sealed recomputation (Batch 21
  P3-finding: old G0-cov + G2/G4-acc intervals were mixed-definition drift;
  now successor judge, B=10k, seed 20260830, G3 included).
- Tables 5.1 (Paper 1 Table 3, 10/10 verified), 8.1, 8.2, 3.1 (authored — Z
  row flagged for Vivek), 3.2/3.3 captioned; Figures 3.2/3.3 DROPPED (never
  referenced). Appendix A incorporated (11 walkthroughs verbatim).
- TOC/LoF/LoT generated + page-verified (118 entries swept); old field-TOC
  placeholder removed. Landscape p36 = arabic 14, rotated number intact.
Bootstrap outputs in /home/claude: appb_bootstrap_run1.json, _runs23.json,
appb_fliptable.json, appb_sec85_final.json. Build: build_dissertation.py.

TOMORROW / PENDING:
1. P3 FULL VERIFICATION SWEEP (last document step), then D6.4 checklist.
2. Vivek personal texts: Acknowledgments, program title, department, college.
3. Vivek supply items: UALR Guidelines PDF (D2.4 — landscape number + dot
   leaders check), Lin [79]/Shi [80] PDFs, BOSS/Argos check, optional Xu
   reconfirmation email, v0.13-v0.30 -> zz_Records sweep.
4. Git finalization: tracker G1-G7 in ledger (incl. sealed-archive mtime
   check G5; billing screenshots G7).
5. D7 defense deck; D12 mock defenses (drill A1-A48).
6. Q&A prep at A48; evidence map complete (42/42).

---

## 2026-09-01 — Batch 23 complete → v0.33 (UALR conformance)

- All 6 UALR conformance findings applied; re-verification battery 16/16 PASS.
- v0.33: 171 pp; landscape = PDF 37 (arabic 14); arabic 1 = PDF 24 and now VISIBLE on ch-1 opener (23.2).
- Build script gained the styles.xml patch (first-line indent + NoIndent) — persisted in build_dissertation.py.
- Incident: plain-space sweep regex corrupted 7 body lines (incl. one Appendix C verbatim line); all repaired from sources of truth and verified. Em-space heredoc lesson recorded in ledger (again).
- Committed to device: 03 Dissertation Defense\GovRAG_Dissertation_DRAFT_v0.33.docx.
- Next: D6.4 submission checklist polish (optional dot-leaders), D7 defense deck, D12 mock defenses, G1–G8 git finalization. Vivek's items unchanged (cover-to-cover read; Table 3.1 Z-row; Lin/Shi PDFs; BOSS application; scheduling).

---

## 2026-09-05 — D7 defense deck v1 built

- GovRAG_Defense_Deck_v1.pptx: 39 slides (31 core incl. title/thank-you + 8 backups), 40-45 min target.
- Structure: 5 acts mapped to RQ1/RQ2/RQ3; PC1-PC4 spine slide; H1-H4 ledger with H2 REFUTED badge; figures 2.1/3.1/6.1/8.1/8.2 embedded; speaker notes on every slide.
- Numbers pipeline: deck_numbers.json extracted+asserted from build_source.md (45 values); build_deck.js reads JSON (never-retype honored); final sweep verified 30 headline values verbatim in source; hand-typed literals audited — $71.23/$170.77 spend-counter deltas REMOVED from backup B5 (not in dissertation; replaced with the document-carried $752.09-of-$999.00 capture of 2026-07-19).
- Visual QA: chip-invisibility on dark slides fixed (ice border); Fig 2.1 overlap fixed; validate.py PASS.
- Delivered to Vivek; device bridge offline at delivery time — NOT yet committed to 03 Dissertation Defense (pending desktop reconnect).
- Batch 24.1 (Acknowledgments 'Above all'→'I also') still queued, awaiting Apply.

---

## 2026-09-06 — Batch 24 APPLIED → v0.34; QASC accept + reviews integrated

- Paper 1 ACCEPTED at QASC 2026 (letter 2026-09-02; Springer LNEE; conf Sept 25-27; camera-ready + registration due Sept 7 — URGENT, Vivek's task).
- Paper 2 desk-rejected at TPS (no peer review); redirect per venue plan (Big Data 2026 workshops / AAAI-27 next).
- Publication NOT a graduation requirement (per Vivek).
- Batch 24 (24.1-24.8 + A50) applied; v0.34 built, battery effective 20/20; C2 scope verified against sealed archives (one Part-1 bridge record only).
- Deck v2 updated (slide 14 reviewer line; publication status on conclusion; chips centered; slide 5 native rebuild; backup divider + B9).
- Vivek's open items: QASC registration + camera-ready revision (reviews define it); combined Xu email (acceptance + scheduling); cover-to-cover read now on v0.34; Table 3.1 Z-row; BOSS application; walkthrough-deck refresh decision; Appendix D anonymity-note decision for next venue.

---

## 2026-09-06 (later) — Batch 25 APPLIED → v0.35: C2 demoted to mechanism

- Camera-ready Paper 1 drops C2 from contributions (keeps architecture); dissertation follows (Option B — no renumbering).
- v0.35: 172 pp, battery effective 18/18. Fig 3.1 C2 badge now outline-style.
- Deck v2 updated in step (slide 8 "Five contributions and one mechanism", C2 card, RQ1 conclusion line, Fig 3.1).
- sweep_lists.py persisted (em-space-safe, curly-quote-aware) — use for all future renumbering.
- A51 added. Vivek: camera-ready revision itself still his task (with Overleaf LNEE template), QASC registration deadline Sept 7.

---

## 2026-09-11 — Batch 26 APPLIED → v0.36: camera-ready alignment (the big renumber)

- Contributions now C1 Manifest / C2 Monitor / C3 Feasibility / C4 Frontier / C5 Fit; bridge = DP2 mechanism, "implemented, not exercised" (Q3.6 never ran — archive-verified).
- Serve path corrected (Q1→Q2→Q3→Q5→Q6, Q4 guard) — verified against frozen B2_Serve.py.
- §0.4 AI-use disclosure added (end of Preface — Claude's placement call, flag if wrong).
- Deck slide 14 factual error fixed (0/8 ablation); B10 case slide added (verbatim sealed evidence).
- v0.36: 174 pp; landscape 38; battery effective 24/24.
- OPEN: OneDrive tracker updates (device shell down); Vivek: send v0.36 to Xu/committee (this is now the consistent-with-published-record version), QASC talk Sept 25-27, defense scheduling.

---

## 2026-09-11 (later) — Batch 27 → v0.37 (disclosure to Appendix F); statuses per Vivek's 14-point reply

Queue order per Vivek: cover-to-cover read (tomorrow, of v0.37) → individual committee reviews (availability gathered there) → mock defenses AFTER doc+deck final. Grad application deprioritized. QASC untracked. Paper 2 venue TBD post-committee-review. Trackers parked. Pending HIS answers: Z-row confirmation; Lin/Shi + Elicit decision.

---

## 2026-09-12 — Prior-art item CLOSED

Verified in repo `02 GovRAG Paper2\2_Prior_Art` (device listing):
- Concept-based RAG models_ A high-accuracy fact retrieval approach_Lin_C_Y_and Jang_ J_S_R_2025.pdf (ref [79])
- Compressing long context for enhancing RAG with AMR-based concept distillation_Shi_K_2024.pdf (ref [80])
Lin/Shi item closed. Remaining Vivek-side: v0.38 cover-to-cover read; committee reviews;
optional Elicit delta-scan (Claude offered to run via web search). Claude-side: awaiting
read feedback; G1-G8 on hold; trackers parked.

---

## 2026-09-12 (close) — Committee outreach sent; read scheduled

- Vivek sent follow-up emails to Dr. Xu and Dr. Wang requesting individual review
  sessions (Xu first; deck = full defense deck v2, trimmed 17-slide live path:
  1-2-3-4-6-7-9-12-14-18-20-22-23-26-27-28-30-31; asks made verbally at slide 30).
- Document + Reading Guide go out only AFTER his cover-to-cover read — read of v0.38
  starts tomorrow (2026-09-13).
- Next Claude actions on his return: fold read notes into a batch (v0.39 if any);
  refresh D1_1/D10_2 meeting materials if asked; committee-session prep per member
  (Talburt ch 7/11/AppC; Wu ch 4/7; Wang ch 3/5/6); mocks after doc+deck final.

---

## 2026-09-14 (close) — Read session 1 done; Wang deck feedback incoming

- Vivek's v0.38 read produced A53-A58 (title/name/BA-vs-ontology/BIZBOK/bootstrap
  drills) + Batch 28 items. Bootstrap provenance verified end-to-end (script in
  Evidence\, reproduces sealed JSON exactly).
- Batch 28 status: APPROVED 28.1 (ref[7] license) · 28.2 (abstract name unpack) ·
  28.3 ("Why this anchor." §3.2, run-in label) · 28.4 (abstract expansion removal) ·
  28.5 (§12.1 C3-C4 fix) · 28.6 (Ack venue credit). AWAITING DECISION: 28.7 (dot
  leaders / right-aligned TOC numbers) · 28.8 (NoIndent first-line-indent BUG fix —
  recommended, explains the misalignment he saw) · 28.9 (spell out "10,000 bootstrap
  resamples").
- NEXT SESSION: Dr. Wang's deck feedback — "story is not so strong." Plan: hear the
  specifics, then restructure the deck narrative (candidate arc: problem→promise
  (PC spine)→build→price→prediction, one through-line = "governance as a priced dial";
  the QASC 15-slide talk's tight story frame is a proven donor). Deck edits under the
  same propose→approve→apply protocol.
- Read continues (he was in front matter/ch1 region); Xu session still to be scheduled.

---

# Session close — 2026-09-16 (Wang deck review → Deck v3)

## Workspace reset disclosure
Cloud workspace was wiped between sessions. Lost: build_source.md, build/sweep
scripts, ledger Batch 27/28 records, Q&A A53–A58 full texts (all post-Sep-10,
uncommitted). Recovered/reconstructed this session: ledger records rebuilt
(28.3's full locked wording is the one true loss — flagged for RE-APPROVAL);
A53–A58 reconstructed abridged in Defense_QA_Prep.md. New rule: ledger + Q&A
prep committed to device at EVERY session close. Batch 28 application will
state its method (source reconstruction vs direct docx edit) before running.

## Done this session
- Dr. Wang's six deck comments (W1–W6) processed: intake log
  D11_Wang_Deck_Review_Log.md (verbatim + verified facts + classification).
- Restructure proposal D11_Deck_v3_Restructure_Proposal.md approved (decisions
  D1 deck-only RQ recast · D2 rgb_5_N cold open · D3 HAGRID cliff on main path
  · D4 = batch item 28.10 · D5 build).
- **GovRAG_Defense_Deck_v3.pptx built, verified, committed to device** —
  47 slides (36 main + 11 backup). Full change record in the ledger's
  "Deck record — Wang review → Deck v3" section.
- Ledger: Batch 27/28 reconstructed + 28.10 added. Q&A: A59–A61 added
  (reasoning-model challenge; stage-4 "did you look"; RQ-vs-engineering).

## Next session
- Vivek reviews Deck v3 (content pass). Known polish item: promoted staircase
  slide (main-path p23) kept the plain backup layout — restyle on request.
  Optional visual nit: on the two-panel example slides the box tints follow
  the donor layout (red first box) — recolour on request.
- 28.3 full wording re-draft → Vivek re-approval.
- Batch 28 apply after his cover-to-cover read completes (28.7/28.8/28.9 still
  awaiting decision; 28.8 recommended).
- §1.4 RQ1–RQ3 deck/doc divergence question → raise with Dr. Xu.
- Committee sessions: Xu first; 17-slide live path needs re-selection for v3
  numbering once content is settled.

## Late addendum (same session, before close)
- Vivek supplied the QASC Paper-1 Fig. 1 screenshot; added as new main-path
  slide "THE PUBLISHED ARCHITECTURE" (after arch overview, before modules) —
  rebuilt as native vector shapes (screenshot too low-res to project); labels
  verbatim; ledger addendum recorded. Deck v3 now 48 slides (37 main + 11
  backup); committed to device. Offer open: swap in camera-ready original if
  he supplies the figure file.
- Vivek reviews deck v3 tomorrow → expect review comments next session.


# Session close — 2026-09-21 (v6 mid-review checkpoint)
Deck v6 delivered + committed (51 slides). Vivek's slide-by-slide review
paused AT SLIDE 10 ("ACT 1 · THE QUESTION"); DB-1–DB-11 applied, previews
approved through the gap slides. NEXT SESSION: resume review at slide 10;
remaining cohesion items parked: stakes-slide card whitespace tightening,
notesSlide1 cue touch-up, time-budget recheck (+1 FULL slide), rubric
re-grade at review end. Standing: 8-dimension rubric, per-slide preview
process, deck-only citation rule for the two public incidents. Batch 28
(document) unchanged: 28.1–28.6+28.10 approved (28.3 needs re-approval),
28.7/28.8/28.9 open.

# Session close — 2026-09-23 (review continues)
Applied today into v6 (recommitted to device): DB-12 OpenAI case-4 band on
Models 2/2 (deck-only citation; stakes slide unchanged after analysis) ·
DB-13 RQ framing kept, headlines softened ("The research question…";
commitments-only rejected with reasoning logged) · DB-14 gap-filled mapping
now rounded-elbow lanes · DB-15 question slide rebuilt as argument chain
(RQ → THEREFORE price → THEREFORE prediction). Review position: RESUME AT
SLIDE 11 (PC1–PC4 defense spine). Pending cohesion items unchanged + add:
notesSlide6 connective sync, A59 OpenAI addendum for Q&A prep.

# Checkpoint — 2026-09-24 (mid-review, DB-16 through DB-24)
Applied since last checkpoint: DB-16 stakes sources verified to primary depth
+ "prosecuted" wording corrected + Evidence memo committed · DB-16a
verify-on-demand links in notes · DB-17 RQ-vs-EQ definitional drill (A62
queued) · DB-18 Proposal §5 pointer + provenance note · DB-19 spine bridge
band + clean headline · DB-20 DP2 Q3.5/Q3.6 precision + Part-II relabel ·
DB-21 metrics instantiation wording (deck) + 28.12 proposed · DB-22 CF1
provenance (28.12 APPROVED, recorded in ledger) · DB-23 explicit
COMMITTED/EXTENDED/ADOPTED block on method slide (one XML corruption caught
by render check, restored from v5, redone validated) · DB-24 where-measured
cue (Part 2 only; Tables B.1–B.4). Review position: slides 1–12 done; RESUME
AT SLIDE 13 (published architecture). Batch stays OPEN until review completes;
final cohesion pass + battery + rubric re-grade then produce the Xu-ready v6.

## Session close 2026-09-25 — v8 shipped
Review completed through all slides (his confirmation). v8 = 52 slides, battery 27/27 (2 false negatives explained: title line-wrap, in-image caption). Cycle log: Deck_Batch_v7.md DB-48–DB-65. Document queue: 28.15 APPROVED, 28.16 CHECK queued ("affirmation" scan §7.4), 28.13/28.14 open (Fig 3.1 / Fig 6.1 doc-figure alignment), 28.9 recommended, 28.3 needs re-draft. Q&A drills pending merge: A59, A62–A65 + κ gloss + direct-to-Q + auditor-not-refuser. Scratchpad tree deck_v6/ = v8 state.
NEXT SESSION (his word, 2026-09-25 close): DOCUMENT REVIEW of v0.38. Start with the Batch 28 queue: apply approved items (28.1–28.2, 28.4–28.6, 28.10, 28.12, 28.15) on his "Apply"; run 28.16 check ("affirmation" scan, §7.4 + metric text); verify doc Figs 3.1/6.1 vs corrected deck images (28.13/28.14); decide 28.7/28.8/28.9; re-draft 28.3 for re-approval. Method note owed to him first: build_source.md was lost to container resets — state docx-direct editing vs source reconstruction before applying anything. Never touch Appendix C.

## Session close 2026-09-26 — Batch 28 applied, v0.39 shipped
v0.39.docx (175 pp) on device with all 14 items; v0.38 untouched as fallback; corrected Fig31 PNG in Figures\; deck v8 synced (DB-67). Full application record: ledger "Batch 28 — APPLIED".
NEXT SESSION (his word): Vivek reviews the DISSERTATION DOCUMENT (v0.39) again. Read-session protocol: his questions during review = predicted committee questions → capture as Q&A drills; findings → Batch 29 queue (one batch per cycle); apply-only on his "Apply". Also pending: Q&A drill merge (A59, A62–A65 + κ gloss, direct-to-Q, auditor-not-refuser) into Defense_QA_Prep at next checkpoint; committee scheduling heads-up to Talburt/Wu (he'll ask Dr. Xu first); Xu/Wang deck feedback → Batch 29 + deck v9.

## Session close 2026-09-29 — ablation run plan captured
Xu feedback X1–X6 logged; clarifications ruled; Defense_Action_Plan_Oct.md + Ablation_CrossFamily_Runplan.md committed. APPROVED: budget yes, TWO families (OpenAI mini-class + hosted Llama-class), mini-frontier design (DelucionQA n=300 seeded subset + HAGRID 163 + ExpertQA 150 × G0–G4, no variants), judge constant, $250 cap, run exactly per campaign discipline (probe → adapter approval → deviation push → quarantine → B4/E3P → sealed archives → billing captures). PRIORITY: ablation before ALL other tasks (Doodle/manuscript/deck v9 wait for the result per Vivek's sequencing). Keys provided at run time. NEXT SESSION: start checklist in the run plan.

## Session close 2026-09-30 — ablation design LOCKED (run plan v2, commit cddcff7)
Rulings today: swap scope = **Q6-only REPLAY** (Q2 NOT swapped; replay sealed `_spec_*.jsonl` prompts byte-identical to new family at T=0 → identical admitted evidence by construction; claim = generation-step resilience) · corpora upgraded to FULL 912+163+150 × G0–G4 = 6,125 pairs/family (subset design dropped) · judge-agreement add-on APPROVED (~500 sealed pairs, second judge family, ~$5–10). Ablation_CrossFamily_Runplan.md rewritten (v2) and committed; prior version = .bak (gitignored). Housekeeping: stale + stranded git lock/tmp files moved to `_to_delete/` at repo root (delete permission declined this session — Vivek empties it himself).
NEXT SESSION (execution, in order per run plan checklist): Vivek provides OpenAI key + hosted-Llama provider choice (Together/Groq) → verify all 15 spec files + SHA-256 → replay-adapter script presented as diff for approval (standalone file, no frozen code touched) → live model probes → deviation-log entry pushed to GitHub BEFORE first token → add-on sample script + seed commit → 20-q pilot per family → Family A full replay. Budget ≈$165 + $5–10 add-on, cap $250. Everything else (Doodle, manuscript §8.6/§10.2, deck v9, committee email) waits for the result per Vivek's sequencing.
