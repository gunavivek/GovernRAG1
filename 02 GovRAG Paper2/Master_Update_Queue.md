# Master Update Queue
*Rule (agreed 2026-07-23): Claude drafts proposed master edits here with exact text.
Nothing is applied to GovRAG_Paper2_Master.docx/.md until Vivek says "update".
Applied items move to the log at the bottom with the date.*

## POLICY (locked 2026-07-23, supersedes earlier direction)
**The master is the program record: it keeps the Paper 1 → Paper 2 continuity framing
UNCHANGED.** All standalone reframing (no Paper-1 references, standalone cost model,
fresh system section) applies ONLY to the venue manuscript (4_Submission\ IEEE shell).
Paper 1's experiment was complete as a demonstration; benchmark-scale evaluation was cut
short by the per-record rebuild runtime (~3 h/question) — the venue paper states this as
the rejected design alternative, without naming Paper 1.

## PENDING — awaiting "update"
(none — U2–U4 applied 2026-07-25, see APPLIED LOG)

## APPLIED 2026-07-25 (Vivek's "update master items U2–U4")
- **U2 — Constrained-F1 outcome decision (Scenario B) — UNBLOCKED 2026-07-23.** Append a
  dated block to the §2.x positioning note: "Outcome decision (2026-07-23): Scenario B
  selected (below but defensible). Consistent-judge CF1* (governed best): 0.668
  (DelucionQA, G1, rejudge) / 0.646 (HAGRID, G1) / 0.566 (ExpertQA, G2+OntNU) vs
  CogniGraph 0.756 (different benchmark, not comparable); ExpertQA reversal noted
  (governed 0.566 > naive 0.502)."
- **U3 — Pair-count phrase standardisation.** Replace "11,025 judged answer-pairs across
  all passes" (master §1.2 and anywhere else) with the locked phrase: "11,025 judged
  pairs, of which 8,208 were additionally re-judged by a second judge."
- **U4 — Judge-policy note.** Add one sentence to master ch.4 (methods): primary results
  use the single successor judge for all runs; run 1's initial scoring is retained as an
  inter-judge robustness study (agreed 2026-07-23; matches Paper2_Spine v1.0).

## SPINE UPDATE LOG (Paper2_Spine.docx — frozen; edits only on Vivek's "update spine")
- APPLIED 2026-07-24 (batch, Vivek's "update spine"): S1 claim rewrite with F5 promoted +
  "ontology-derived reference monitor" phrasing · S2 "reference ontology" standard term,
  BIZBOK named as its instance in §5 · S3 F1 baseline safe-silence definitional guard ·
  S4 F1 G2-selection clause ("strictest level at which all three corpora still answer") ·
  S5 ExpertQA stratum corrected: evaluated set 70% unanswerable (105/150); 55% = full
  corpus, labelled as such. Spine is now v1.2.
- APPLIED 2026-07-25 (batch 2, Vivek's "update spine" — spine now v2.0): S6–S36 + N1–N5,
  the full topic-by-topic review (Topics 1–15). Includes: F2 localisation evidence; F3
  rebuilt (measured vs by-construction, auditor capability, G1 nearly-free operating
  point); F4 ceiling cause + leniency caveat + reframe; F5 cross-run refuse-all
  containment + stratum scoping + axis-variant guard; F6 chance/mechanism/confound guards
  + axes negative characterisation; F7 same-family + run-1-only + per-config flip
  analysis; F8 unit economics + all-in cost scoping; ledger rebuilt (both H1 estimators,
  graded H3, parametric leakage); §4 models/scoping/taxonomy/junk-filter/commit-id/
  empty-evidence; §5 exact level semantics + Q5/Q6 split + axis definitions; §6 CF1
  within-system scale + reviewer-preemption + terminology; NEW §7 Limitations minimum;
  Annex A → pointer to Dissertation_to_Paper2_Mapping.docx (kept as-is, per Vivek).
  Historical detail of individual S-items:
  S6 (T3): F2 localisation evidence — by-construction sentence + monitor drop counts (0.0 at G1 → 35.9 avg chunks/question at G2+, DelucionQA); numbers line gains drop counts.
  S7 (T4a): F3 auditor-capability sentence (reconstruct admit/drop/rule/citation from logs alone, without re-running).
  S8 (T4b): F3 reword — measured citation-resolvability (97.7–100% of governed answers) separated from by-construction Q5 decision logging (refusals included).
  S9 (T5a): F4 ceiling cause — gold-context benchmarks leave no hallucination headroom (halluc-on-answered 1.2–2.2%).
  S10 (T5b): F4 pre-registered leniency caveat (TRACe-adherence on short cited answers; discriminant check future work) + ceiling observed under both judges.
  S11 (T5c): F4 closing reframe — governance's measured value lies in refusal quality (F1) and auditability (F3).
  LEDGER NOTE (applies at ledger topic): H1 retains BOTH point deltas (Δ=.034/.080 master notation) and paired-bootstrap CIs (−.018/−.065); use whichever suits the outlet (Vivek 2026-07-24).

## TECHNICAL PROGRAM QUEUE
- T1 — Root-cause analysis: <2.3% unresolved citations on DelucionQA (from Spine Topic 4c).
  Method: query run1 sealed audit metadata for non-resolving citation keys; classify failure
  mode. Spine §7 discloses the gap until resolved.
- T2 — Per-question latency (from Spine Topic 9d): pre-registered ("per-question $ and
  seconds") but not found in any sealed summary. Extract from run logs/timestamps if
  present; otherwise record non-collection as a dated deviation-log entry + limitation.

## CANCELLED / REVERTED
- **U1 — §1.1 softening.** Applied 2026-07-23, REVERTED same day at Vivek's direction
  (master keeps continuity). .md restored on disk; on-disk .docx was never modified
  (Word file lock blocked the write); cloud copies restored and verified.

## VENUE-PAPER GUIDANCE (moved out of master queue — lives in the IEEE shell spec)
- Standalone cost model text (drafted 2026-07-23): per-question rebuild presented as the
  rejected design alternative; T = D·C_build + n·C_query; no Paper-1 reference.
- §1.3-equivalent system summary written fresh; Paper 1 cited once in §II as under review.

## APPLIED LOG
- 2026-07-25 · U2 (Scenario-B decision block appended to §2.x positioning note), U3
  (pair-count phrase standardised), U4 (judge-policy note added after ch.4 heading) —
  applied to BOTH GovRAG_Paper2_Master.md and .docx; verified anchors unique; docx via
  tracked paragraph insertion, TOC unaffected.
- 2026-07-23 · U1 applied and reverted same day (see CANCELLED / REVERTED).

## Review state (ch. 1, 3.3, 6, 7.2, 9)
- Ch. 1 — reviewed; stands AS ORIGINALLY WRITTEN (continuity retained). §1.2 C4 at
  one-sentence depth confirmed; §1.3 confirmed. Vivek's cut-off comment "3)" still open.
- Ch. 2 — CF1 positioning note reviewed; U2 finalised, pending "update".
- §3.3, Ch. 6, §7.2, Ch. 9 — awaiting Vivek's comments.
