> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\5_Manuscript\Contribution_Positioning_Note.md — edit the canonical, then re-snapshot. See Source_Register.docx.

# Contribution Positioning — Constrained-F1 Risk & Outcome-Contingent Framing
*Paper 2. Decide the headline metric AFTER the run; pre-committed phrasings below so the
framing is principled, not post-hoc rationalization. Pairs with Related_Work.md and
Prior_Art_Synthesis.md.*

## The risk (why the absolute number can hurt us)
CogniGraph (Kumar 2026) reports Constrained-F1 = 0.5·F1_token + 0.5·Governance-Accuracy = **0.756**
at a single fail-closed operating point on **MultiGov-30** (curated EU-AI-Act/GDPR/DORA/NIS2 reasoning,
30 items, multi-agent architecture). If our best-level Constrained-F1 on **DelucionQA / RAGBench**
(standard RAG QA, answerability-stratified, single-corpus authorization) lands well below 0.756, a
reviewer skims it as "worse than CogniGraph." That reading is category-confused (different benchmark
difficulty, different task, different architecture), but the burden is on us to neutralize it *up front*.

## The invariant claim (holds regardless of the number — never bury this)
Our contribution is **not** a higher Constrained-F1 than CogniGraph. It is:
1. **Position**: governance applied to the *evidence admitted to generation* (reference monitor / Q5),
   not to the model's *output* — the unoccupied third slot in the KG-before / KG-after / KG-as-gate
   taxonomy (SITL's own framing).
2. **Frontier**: the full per-level **risk–coverage curve**; CogniGraph and SITL each report a single
   operating point that is one point on our curve.
3. **False-rejection continuum**: CogniGraph reports one 49% false-rejection delta; we report the
   correct-answer false-rejection rate at *every* strictness level.
These three are outcome-independent. The absolute Constrained-F1 is a *comparability courtesy*, not the thesis.

## Decide the headline by outcome
Let CF1* = our best-level Constrained-F1; CF1_cg = 0.756 (theirs, different benchmark — not a target).

| Scenario | Trigger | Lead metric | Constrained-F1 role |
|---|---|---|---|
| **A — Competitive** | CF1* within ~0.05 of 0.756, or clearly strong in absolute terms | Constrained-F1 **parity** + frontier as the extra | Headline column; "parity at a point, superiority across the curve" |
| **B — Below but defensible** | CF1* materially < 0.756 but stable/interpretable across levels | **False-rejection-vs-coverage** + frontier shape | Secondary column, with benchmark-difficulty caveat |
| **C — Weak absolute** | CF1* low or noisy (small-N, judge variance) | **Three-position novelty** + false-rejection continuum | Appendix only, with explicit non-comparability statement |

Guardrail for all three: **never** write "we beat/outperform CogniGraph." Always "generalize / characterize /
locate their operating point on our frontier." A same-data head-to-head is not available (their code /
MultiGov-30 not runnable here; different pipeline position) — state this as a scoped limitation, not a gap.

## Pre-committed sentences (paste the matching block)

**Scenario A (competitive).**
> On DelucionQA our reference monitor attains Constrained-F1 comparable to the single-operating-point
> figure reported by CogniGraph (Kumar 2026), while additionally characterizing the full
> governance-strictness risk–coverage frontier — of which a fail-closed gate is one point. Governance
> quality is thus not traded against answer quality at a fixed setting but made *tunable*, with the
> operating point selectable to a target false-rejection budget.

**Scenario B (below but defensible).**
> We adopt CogniGraph's Constrained-F1 for comparability, but our central result is the
> false-rejection-vs-coverage frontier: across G0–G4 the correct-answer false-rejection rate moves
> continuously with authorization strictness, generalizing the single 49% false-rejection delta CogniGraph
> reports between two gate configurations. Absolute Constrained-F1 is not directly comparable across
> benchmarks — MultiGov-30 evaluates curated multi-agent regulatory reasoning (30 items); we evaluate
> evidence-admission governance on standard RAG QA with answerability stratification — so we report it as a
> secondary, within-system metric and base our claims on the *shape* of the frontier.

**Scenario C (weak absolute).**
> Our contribution is architectural and evaluative rather than a Constrained-F1 improvement: we place the
> symbolic gate on the evidence admitted to generation (the reference-monitor position), and we report the
> per-level risk–coverage and false-rejection frontier that prior fail-closed systems (CogniGraph, SITL)
> collapse to a single operating point. Because their architectures gate the *output* and their benchmarks
> are not runnable in our setting, we make no absolute Constrained-F1 comparison; we report it in Appendix X
> as a within-system diagnostic only.

## Reviewer-preemption line (use in all scenarios, Limitations or Eval-setup)
> We do not run CogniGraph or SITL as live baselines: they gate at a different pipeline position (post-
> generation output validation vs. our pre-admission evidence authorization), their code and MultiGov-30
> benchmark are not available to us, and our claim is to *characterize the frontier they each reduce to a
> single point*, not to exceed that point. Comparison is therefore at the metric level (shared Constrained-F1
> definition) rather than head-to-head on identical data.

## Operational rule
Report both metrics at every level in the results table (coverage, accuracy-on-adherent, faithfulness,
Constrained-F1, false-rejection). **Choose the headline only after seeing CF1*.** Pre-registering the three
phrasings above keeps the choice defensible rather than data-dredged: we are selecting emphasis, not the finding.
