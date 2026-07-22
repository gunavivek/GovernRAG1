> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\2_Design\Governance_Spectrum_Design.md (git mirror: repo docs\ where present) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Governance Spectrum — design (one page, for Dr. Xu)

**Idea.** Instead of one governed mode, expose a **monotone spectrum** of answer policies from Naive
(no governance) to Corroborated (maximal governance). Each answer is tagged with a **governance score**;
the consumer picks the minimum level they will accept (a *governance contract*). Traceability and
auditability are preserved at every governed level — only *coverage* trades against *assurance*.
**Date:** 2026-07-06.

## The spectrum (a lattice of constraints — each level adds one)

| Level | Name | Evidence required to answer | Pipeline lever | Provenance / audit |
|---|---|---|---|---|
| **G0** | Naive | any retrieved text | bypass Q-pipeline (`naive_baseline`) | none |
| **G1** | Cited | ≥1 retrieved chunk, **citation required** | Q6 accepts any cited chunk; skip Q5 predicate filter | citation only |
| **G2** | Grounded | ≥1 **authorized** chunk (passes Q5 predicate filter) + citation | Q6 gate = authorized-chunk OR triplet | Q5 decision log + citation |
| **G3** | Strict *(current)* | ≥1 **authorized symbolic triplet** + citation | Q6 gate = triplet required | + symbolic triple |
| **G4** | Corroborated | ≥N triplets, or triplet **and** agreeing authorized chunk | Q6 gate = corroboration test | + cross-evidence |

Monotone: G0 ⊂ G1 ⊂ G2 ⊂ G3 ⊂ G4 in *constraints* ⇒ **coverage ↓, assurance ↑** as level rises.

## Orthogonal dials (tune within a level)
- **Retrieval depth** `k_hops` (Q1 intent hierarchy): 1 / 2 / 3 — breadth of the governed walk (recall, not authorization).
- **Predicate breadth** (Q5 allowed set): question-mapped subset ⊂ domain-scoped ⊂ full-ontology.
- **Citation granularity**: chunk-level vs sentence-span.
These move coverage/precision *without* changing the governance level's semantics — reported as secondary axes.

## The governance score (already partly emitted)
- **Continuous:** Q5 **Governance Ratio (GR)** ∈ [0,1] (primary_kept / (primary+residual_kept)) + evidence tier.
- **Discrete:** the highest level G0–G4 the answer satisfies.
- **Consumer contract:** "accept answers with level ≥ Gk" (or GR ≥ τ). The system already computes GR;
  the dial just exposes the *minimum tier accepted*.

## Invariant (the moat vs a scalar confidence knob)
Every governed level (G1–G4) carries **resolvable provenance (`[CHNK_*]` forensic key) + Q5 decision log**.
So the dial trades coverage for assurance while keeping **auditability at all levels** — a black-box
confidence threshold cannot. This interpretable/auditable graded governance is the novel core.

## Evaluation (the two money figures)
Run **5 levels × 913 questions × N≥3**, stratified by answerability, judge = gemini-2.5-pro (independent).
1. **Risk–coverage frontier:** faithfulness (TRACe Adherence / 1−hallucination) and adherent-stratum
   accuracy vs **coverage** (answer rate), one point per level. The knee is the practical operating point.
2. **Governance-score calibration:** governance level vs *empirical* faithfulness — must be **monotone**;
   overlay a **selective-prediction baseline** (confidence-threshold abstainer) to show the auditable dial
   matches/beats the frontier while adding provenance the baseline lacks.
Plus per level: coverage, hallucination rate, abstention correctness (non-adherent), provenance coverage, mean GR, cost/latency.

## Implementation (what it costs)
- G0, G3 exist. **G1/G2/G4 = one parameterized Q6 gate** (env `GOVRAG_LEVEL`), a single reviewable frozen
  diff exposing the level — not per-level rewrites. `k_hops` = one Q1 line. Scorer already stratifies; add
  a per-level loop + frontier plot.
- Frozen edits: Q6 gate (governance semantics) → **requires Dr. Xu sign-off**. Everything else harness.

## Novelty & risks (be honest)
- **Novel:** symbolic, ontology-derived, *auditable* graded governance with per-answer provenance and a
  consumer-selectable contract — distinct from scalar selective prediction / conformal / guardrails.
- **Trap 1 (tautology):** "stricter ⇒ more faithful" is partly by construction. The contribution is the
  *shape/knee* of the frontier, *score calibration*, and *auditability*, NOT monotonicity alone.
- **Trap 2 (generalizability):** one corpus (DelucionQA) is a workshop-strength result; ≥2 corpora
  (Emanual + a finance/legal set) needed for a strong main-track claim.
- **Trap 3 (baseline):** must compare to a confidence-threshold/conformal abstainer or reviewers call it
  "rediscovered risk–coverage."
- **Trap 4 (unanswerable power):** DelucionQA has only ~64 unsupported items; add Emanual for the abstention claim.

## Decisions for Dr. Xu
1. Adopt the **governance spectrum** as the headline contribution (vs STRICT-only as fallback)?
2. Approve the parameterized **Q6-gate** frozen diff (governance semantics change)?
3. Scope: **corpora** (DelucionQA only vs + Emanual + FinQA/CUAD) and **levels** (G0/G2/G3 minimal vs full G0–G4)?
