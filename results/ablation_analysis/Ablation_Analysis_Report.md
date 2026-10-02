# Cross-Family Generation Ablation — Formal Analysis Report

Generated 2026-10-02T21:25:05Z · paired bootstrap B=10000, seed 20261002 · all numbers computed from sealed archives
(input SHA-256 list in analysis_report.json). Design, pins and the pre-stated decision rule:
deviation entry 2026-10-02, pushed to GitHub before execution (04e8865; selection pre-commit 974db57).

## 1. Coverage frontiers (fraction answered)

**DelucionQA (912, aligned)**

| Family | G0 | G1 | G2 | G3 | G4 |
|---|---|---|---|---|---|
| Gemini (campaign, gemini-3.5-flash) | 100.0% | 92.5% | 44.1% | 38.0% | 34.8% |
| GPT-4.1-mini-2025-04-14 (OpenAI) | 100.0% | 95.3% | 57.4% | 50.2% | 46.6% |
| Llama-3.3-70B-Instruct-Turbo (Together, FP8) | 100.0% | 95.6% | 54.9% | 47.3% | 44.3% |

**HAGRID (163)**

| Family | G0 | G1 | G2 | G3 | G4 |
|---|---|---|---|---|---|
| Gemini (campaign, gemini-3.5-flash) | 100.0% | 77.9% | 16.6% | 0.0% | 0.0% |
| GPT-4.1-mini-2025-04-14 (OpenAI) | 100.0% | 82.2% | 16.0% | 0.0% | 0.0% |
| Llama-3.3-70B-Instruct-Turbo (Together, FP8) | 100.0% | 82.8% | 17.2% | 0.0% | 0.0% |

**ExpertQA (150)**

| Family | G0 | G1 | G2 | G3 | G4 |
|---|---|---|---|---|---|
| Gemini (campaign, gemini-3.5-flash) | 100.0% | 58.7% | 32.7% | 0.0% | 0.0% |
| GPT-4.1-mini-2025-04-14 (OpenAI) | 100.0% | 74.0% | 42.0% | 0.0% | 0.0% |
| Llama-3.3-70B-Instruct-Turbo (Together, FP8) | 100.0% | 79.3% | 42.7% | 0.0% | 0.0% |

## 2. Pre-stated criteria — verdicts

| Criterion | GPT-4.1-mini | Llama-3.3-70B |
|---|---|---|
| (a) Coverage monotone non-increasing, every corpus | PASS | PASS |
| (b) G1->G2 cliff (DelucionQA) + HAGRID above-G1 collapse | PASS | PASS |
| (c) Correct-refusal: G2+ above naive on unanswerable stratum, CI excl. 0 | PASS | PASS |
| (d) Citation auditability at ceiling (>=0.99) | **BOUNDED: min 0.867** | PASS (1.000) |

Cliff magnitudes (DelucionQA G1->G2 coverage delta): GPT-4.1-mini -37.9 pp, CI95 [-41.2, -34.8]; Llama -40.7 pp, CI95 [-44.0, -37.5].

## 3. Findings

**F1 — Generation-step structural resilience.** Given identical admitted evidence (byte-identical
replayed prompts, T=0), both foreign families reproduce the governance dial's structure on all three
corpora: monotone coverage descent, the G1->G2 cliff on the aligned corpus, the HAGRID above-G1
collapse, and governed-over-naive correct refusal at G2+ with bootstrap CIs excluding zero.
Levels shift (both ablation families answer more than the campaign generator at governed tiers);
structure does not. This is the pre-stated resilience pattern.

**F2 — Bounded resilience: citation-identifier fabrication by GPT-4.1-mini (criterion d).**
On DelucionQA, GPT-4.1-mini fabricates citation identifiers that do not occur in its evidence
(e.g., hybrids of the bare CHNK_PRIMARY tag with invented numeric suffixes): 316 of 2371 distinct
cited markers unresolvable (resolvability 0.867; ExpertQA 0.982; HAGRID 1.000). Campaign Gemini:
0.997-1.000. Llama: 1.000 on all three corpora. Citation discipline is therefore the one
generation-side property observed to be family-dependent; the governance substrate (admission,
blocking, routing) is unaffected by construction. Reported as a bounded-resilience finding per the
pre-stated rule; deployment implication: a citation-id validity check at the serve boundary
(deterministic, no LLM) would close this gap for any family.

**F3 — G1 refusal behaviour note.** The campaign generator's G1 correct-refusal rate was already
statistically indistinguishable from naive (DelucionQA delta +1.6 pp, CI [-6.3, +9.4]); Llama shows a
small negative G1 delta (-12.5 pp, CI [-23.4, -1.6]). The pre-stated ordering criterion concerns
G2 and above, where all families pass; the G1 tier's refusal behaviour is reported for completeness.

**F4 — Judge-family sensitivity (job 7).** n=500 sealed campaign pairs re-judged by gpt-4.1-mini-2025-04-14:
raw agreement 80.4%, Cohen's kappa 0.606, bootstrap CI95 [0.539, 0.672]. Disagreement is almost
entirely one-directional (89 MATCH->NO_MATCH vs 9 NO_MATCH->MATCH): the cross-family judge is
systematically stricter, mirroring (in direction-reversed form) the campaign's within-family judge
succession (kappa 0.681, successor more lenient). Judges move severity, not structure.

## 4. Cost (evidence-chained)

OpenAI family generation: $3.14, reconciled token-exact against sealed per-call checkpoints
(4624 requests / 6558131 in / 395102 out). Gemini judging through Oct 1-2: $70.34 (provider report;
final Cost-table CSV capture pending per billing lag). Together export pending. Projected study
total ~$110-125 against the $250 cap. Generation cost of the swap was negligible; the measurement
instrument dominates.

*Prepared by the analysis stage (AB3_Ablation_Analysis.py); every figure regenerable from the*
*sealed archives named in analysis_report.json.*