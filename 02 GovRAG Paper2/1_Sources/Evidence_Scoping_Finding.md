> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\5_Manuscript\Evidence_Scoping_Finding.md — edit the canonical, then re-snapshot. See Source_Register.docx.

# Results — Ontology Axes on DelucionQA: Confirmed Diagnosis
*Paper 2, Results/Discussion. Updated 2026-07-07 with the confirmed empirical picture from the
20-record pilot + corpus-wide feature check. Pairs with Contribution_Positioning_Note.md and the
harness artifacts evidence_reduction.csv / affinity_tau_sweep.csv.*

## Target claim (approved wording) — a HYPOTHESIS, to be established on a corpus that can support it
> Reference-ontology conformance (BIZBOK `alignment_status`) and viewpoint-domain affinity (`wa_score`)
> operate as **evidence-scoping constraints**: they measurably reduce the admitted evidence set
> (mean *N* triplets/chunks dropped per record) without a detectable change in end-task answer accuracy
> or faithfulness. This suggests these ontology-derived signals primarily shape *which evidence is
> considered* rather than *what is ultimately answered*, with end-task effects expected under domain
> heterogeneity or adversarial evidence.

**Status: NOT established on DelucionQA.** The pilot shows *why* it cannot be tested here (below). Report
this as the hypothesis motivating the multi-domain / adversarial evaluation, not as a DelucionQA result.

## What DelucionQA actually shows (confirmed)
1. **The coverage cliff is chunk-level authorization — quantified.** Mean primary chunks kept: G1 = **32.9**,
   G2 = **3.55** (predicate filter drops ~29 chunks/record, ~89%). This is the 95%->20% coverage collapse.
   The triplet gate (G3/G4) is near-irrelevant: mean triplets kept ≈ **0.75**/record.
2. **Axis A (ontology conformance) is STARVED.** With <1 triplet/record retrieved, there is almost nothing
   to filter. Only `conformant` mode acted (`ontology_triplets_dropped` = 0.75, i.e. it removed the sole
   surviving triplet), with **no change** in accuracy/faithfulness — a technically-present but near-vacuous
   dissociation on a 0.75-triplet base. `not_unmapped` was inert (nothing Unmapped among survivors).
3. **Axis B (domain affinity) is DEGENERATE.** `wa_score` is the constant value **1.0 for all 5037 corpus
   chunks** (verified: `viewpoint_domain` = `Customer Support` for every chunk). Zero variance -> the filter
   drops nothing at *any* threshold. `affinity_tau_sweep.py`: global min=med=max=1.000; `affChk` = 0 at every τ.
   This is corpus-wide (all 5037 chunks), so the full 900+ run would not change it.

## Root cause (single structural fact)
DelucionQA is **single-domain and triplet-sparse**. Domain affinity requires multiple domains to be
non-trivial (single domain -> affinity ≡ 1.0); ontology conformance requires a populated triplet channel
(sparse retrieval -> nothing to filter). Neither axis is *wrong*; the corpus cannot exercise either.

## What to report / NOT report on this corpus
- **Report:** the chunk-authorization cliff (chkKept 32.9 -> 3.55) as the mechanism of the risk-coverage
  frontier; and the *negative characterization*: on single-domain, triplet-sparse data the two ontology-
  derived axes are un-exercisable (Axis A starved, Axis B degenerate).
- **Do NOT report:** an affinity τ choice or an affinity sensitivity curve for DelucionQA — there is no
  variance to threshold. Stating "we selected τ = X" here would be meaningless (or worse, look arbitrary).

## Caveats / framing (state them plainly)
- Frame Axis A's null as "no *detectable* end-task change at this power on a triplet-sparse corpus," not
  "conformance does not matter." Frame Axis B as "feature has zero variance on single-domain data," not
  "affinity does not matter."
- The generalization ("effects emerge under heterogeneity/adversarial evidence") is an explicit
  **hypothesis / future work**, supported by the diagnosis, not a demonstrated result.

## Why this is a contribution, not a failure
The instrumentation did not merely produce a null — it *explained* it: feature degeneracy (Axis B) and
triplet starvation (Axis A), both traceable to corpus composition. That is a precise, falsifiable account of
where these ontology-derived signals can and cannot pay off, and it is the concrete, evidence-backed
justification for a multi-domain, triplet-rich, adversarial corpus before the pre-registered 913 run.

## Verification trail
- `results/evidence_reduction.csv` — predTrp 0, ontTrp 0 (except OntConf 0.75), affChk 0; chkKept 32.9->3.55.
- `results/affinity_tau_sweep.csv` — global/survivor wa_score ≡ 1.000; affChk 0 at all τ.
- `output/M1_Governed_Chunks.csv` — n=5037; viewpoint_domain = {Customer Support: 5037}; wa_values = {1.0}.

---

## Update — bidirectional Q3 fix does not wake the axes (Pro judge, N=20, 2026-07-07)
The Q3 bidirectional-walk fix raised triplet yield 0.75 -> 2.70/record and roughly doubled governed
coverage (G2 20% -> 40%, accuracy 6% -> 33% on the Pro judge). It did NOT make the ontology axes
active: ontTrp = 0.05 (~1 triplet dropped total), affChk = 0. Under the Pro judge all axis variants
land at/below plain G2 (33%): OntNU/OntConf/OntNU+Aff = 28%, Aff = 22%. Because G2+Aff drops nothing
yet scores differently from G2, the sub-G2 differences are confirmed judge/generation noise at N=20.
Reading: more triplets != governance signal. Axis A needs ontology-conformance VARIATION (Unmapped/
Adaptive triplets in scope); Axis B needs MULTIPLE domains. Both remain corpus requirements, now
confirmed to persist after the retrieval fix. Faithfulness is saturated at 1.000 throughout.
