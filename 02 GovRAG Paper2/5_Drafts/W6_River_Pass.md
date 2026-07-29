# W6 River Pass — Report

*2026-07-29. Every section seam checked against the four Flow Map scope rules,
on the current shell (v1.0, all 34 references, NIST applied). No changes made —
each finding below is a PROPOSED edit awaiting Vivek's approval. Voice is NOT
part of this pass (separate task, per Vivek's ruling).*

## What was checked

Rule 1 (every passage feeds a map row; trims from branches, never §V) ·
Rule 2 (each number at full precision once, in its home section) ·
Rule 3 (branches visibly join and visibly leave) ·
Rule 4 (abstract, figures/tables, conclusion carry the main line standing alone).

## PASSED — seams that hold

- Abstract → §I → roadmap: the main line is stated, the headline set and both
  failed hypotheses are carried, forward pointers only. Rule 4 holds for the
  abstract and §VIII standing alone.
- §II: all three streams visibly join ("This paper's system occupies a third
  position"; the dial contrast; "has not been measured … precisely this study's
  contribution") and visibly leave (conformal wrapper named as future work).
  The new [3]/[4] sentence joins stream 1 with its contrast marked.
- §II → §III seam: reference-monitor concept [30] closes §II and opens §III.A.
- §III: 553 concepts and the level criteria are carried; both forward branch
  pointers are marked ("Section VI quantifies this economy"; "a finding
  reported in Section V").
- §IV: home precision respected (912/163/150 · 7.0/16.0/70.0% · 39.3/3.9/13.0 ·
  15.0/7.4/10.8 s/q · 462 junk · 23.9→30.0 vs 44.5).
- §V (the main current): every spine finding lands where the map says —
  F1→V.A/B, F2→V.B, F4→V.C, F3→V.D, F5→V.E, F6→V.F, F7→V.G — with home-precision
  numbers matching the Numbers Verification Ledger. NO trim candidates in §V.
- §VI/§VII/§VIII: economics set, CF1 span, κ scope, N=3 confound, and the
  one-line recap set all sit where the map assigns them. Future-work seeds each
  leave at their branch point and are collected once in §VIII.
- Cost figures consistent across altitude: "under $800" (abstract, §I) vs
  "roughly $765" (§VI home precision) — correct rounding direction.

## FINDINGS — proposed edits (approval required)

**RP-1 (§IV.D — missing instrument definition; the substantive catch).**
§V.E uses "governance accuracy" for its central F5 numbers (66.0% vs 55.3%;
82.7/75.9; 79.1/68.1) but §IV.D never defines the metric — it defines only
"accuracy on the answered stratum". A reviewer reaching V.E meets an
uninstrumented number. Proposed insertion in the §IV.D metric list, after
"accuracy on the answered stratum;":
  "governance accuracy, the fraction of all questions resolved correctly,
  where a correct refusal of an unanswerable question counts as a correct
  resolution;"
Grounding: locked Metric Formulas, GA = condition_grade SUCCESS / N (SUCCESS =
MATCH on answerable + credited SAFE_SILENCE on unanswerable).

**RP-2 (§VI.A — unhedged restatement of the exploratory F6).**
§V.F carefully labels ontology-fit "an observation, not a validated predictor";
§VI.A restates it flatly: "The aligned concept share, measured at build time,
indicates how far the dial can usefully turn." Overclaim risk at review.
Proposed: append " — an exploratory signal (Section V-F)".

**RP-3 (§VI.B — Rule-2 duplicate of §IV.D's precision).**
§VI.B repeats "signature extraction alone is 58–93% of stage time" — full
precision whose home is §IV.D. ("under 1%" for the monitor STAYS in VI.B: the
map's §VI row explicitly carries Q5<1%.) Proposed: "…dominated by the
pipeline's LLM calls (Section IV)."

**RP-4 (§II/§VI.C — acronym used before introduction).**
§VI.C says "post-generation validators such as CogniGraph and SITL", but §II
introduces the system only as "symbolic-in-the-loop engineering" — SITL is
never expanded. Proposed, in §II: "symbolic-in-the-loop (SITL) engineering
checks generated content against curated graphs [2]".

**RP-5 (§I ¶3 — third appearance of the study-size integers; recommend KEEP).**
1,225 / 11,025 / 8,208 appear in the abstract, §I ¶3, and §IV.C (home). Exact
integers cannot drift, and ¶3 needs them to set up contribution 2's dual-judge
protocol. Recommendation: keep as-is; note as the first trim candidate if
page-fit later demands one (it is a branch, not §V).

## Deferred re-checks (scheduled W6 work, not river faults)

- Rule 4 for figures/tables completes only after Fig. 1/Fig. 2 insertion —
  re-run the standalone check on both captions then.
- Two bracketed repo-citation placeholders in §IV.A and §VII.B resolve with the
  anonymised artifact package task.
- [33] swaps on the QASC decision.

## Disposition

RP-1..RP-4 await approval (RP-1 is the one with substance; 2–4 are one-line).
RP-5 needs no action. On approval: apply, re-run the bidirectional check,
snapshot v1.1 per the new versioning rule, commit.


## DISPOSITION UPDATE (2026-07-29)
RP-1..RP-4 approved and applied; bidirectional 34/34 clean. RP-5 under discussion. v1.1 on close.
