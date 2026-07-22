> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\6_Results\Analysis_CrossRun.md (git mirror: repo docs\Analysis_CrossRun.md) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Cross-Run Analysis — Runs 1–3 (DRAFT v1, 2026-07-20)

*v4 (2026-07-20): Run-1 paired bootstrap CIs added (§8).*
*v3 (2026-07-20): H4 complete for runs 2–3 (100.0%/100.0%).*
*v2 (2026-07-20 midday): Run-1 re-judge complete; judge-agreement section added; H1 row revised.*
*Sources: sealed archives `results/run1_delucionqa/` (tag `run1-complete`), `results/run2_hagrid/`
(`run2-complete`), `results/run3_expertqa/` (`run3-complete`). Every number below traces to an
`E3_*_frontier_summary.csv` in a hashed archive or to the sealed index snapshots.
PENDING: bootstrap CIs for runs 2–3 (probe-N; wide intervals expected).*

## 1. The three corpora

| | Run 1 — DelucionQA | Run 2 — HAGRID | Run 3 — ExpertQA |
|---|---|---|---|
| Content | Jeep owner-manual QA (customer support) | Wiki passages, factoid QA | Long-form expert QA |
| Questions (N) | 912 (full benchmark) | 163 (K=150 reuse selection) | 150 (K=150, `--drop-junk`) |
| Answerable / Unanswerable | 93% / 7% | 84% / 16% | 30% / 70% |
| Role | Full-coverage anchor | Parity probe (P-heavy) | Abstention probe (N-heavy) |
| Chunks scoped per question | ~36 | ~3.9 | ~13 |
| Concept nodes (M3 stage) | 3,781 | 298 | 703 |
| **Ontology-aligned share (M4, measured)** | **98.2%** (3,713/3,781; 68 unmapped) | **25.8%** (77/298; 219 low-conf + 2 unmapped) | **47.2%** (332/703; 366 low-conf + 5 unmapped) |
| Build model | gemini-3-flash-preview | gemini-3.1-flash-lite | gemini-3.1-flash-lite |
| Judge | gemini-2.5-pro (re-judge under 3.1-pro-preview pending) | gemini-3.1-pro-preview | gemini-3.1-pro-preview |

## 2. Three-corpus governance frontier (key configs)

Coverage / accuracy-on-answered / faithfulness / correct-refusal / false-rejection:

| Config | DelucionQA (912) | HAGRID (163) | ExpertQA (150) |
|---|---|---|---|
| G0 Naive | 100% / 68% / .99 / 33% / 0% | 100% / 86% / 1.00 / 42% / 0% | 100% / 82% / .99 / 44% / 0% |
| G1 Cited | 93% / 64% / .98 / 42% / 5% | 78% / 72% / 1.00 / 46% / 18% | 59% / 69% / 1.00 / 50% / 20% |
| G2 Grounded | 44% / 18% / .99 / 78% / 54% | 17% / 13% / 1.00 / 77% / 85% | 33% / 40% / 1.00 / 75% / 51% |
| G2+OntNU | 45% / 20% / .99 / 75% / 54% | 16% / 14% / 1.00 / 81% / 85% | 33% / 44% / 1.00 / 75% / 49% |
| G3 Strict | 38% / 15% / .99 / 78% / 61% | 0% / — / — / 100% / 100% | 0% / — / — / 100% / 100% |
| G4 Corrob | 35% / 14% / .98 / 83% / 64% | 0% / — / — / 100% / 100% | 0% / — / — / 100% / 100% |

**Shape summary: slope (DelucionQA) → band (ExpertQA) → cliff (HAGRID).** On the in-ontology
corpus the dial degrades gracefully through G4; on the partially-aligned corpus a genuine
intermediate band survives at the G2 tier and the dial dies at G3; on the out-of-ontology
corpus everything above G1 collapses (G2 barely holds 17%, G3+ refuse everything).

## 3. Hypothesis verdicts per corpus

| | DelucionQA | HAGRID | ExpertQA | Overall |
|---|---|---|---|---|
| **H1 quality parity @ G1** (±0.05 bound, answered-stratum accuracy) | **Judge-sensitive**: supported under original locked judge (Δ=.034); Δ=.080 under successor judge | Not supported (Δ=.138) | Not supported (Δ=.133) | Near-parity only in-ontology, within a judge-dependent 3–8-pt band; off-ontology the G1 cost is real (~13 pts) |
| **H2 faithfulness superiority** | Refuted (tie at ceiling: .98 vs .99) | Refuted (tie: 1.00 vs 1.00) | Refuted (tie: 1.00 vs .99) | **Consistently refuted** — gold-context benchmarks leave no hallucination headroom; contribution reframed (see §5) |
| **H3 selective abstention** | Supported w/ coverage cost (corrRef 33→83%, falseRej ≤64%) | Partial — cost extreme (falseRej 85–100% at G2+) | **Strongest support** (corrRef 75% vs naive 44%; GA 65% vs 55%) | Monotone dial replicates on all three; the *price* varies with ontology fit |
| **H4 auditability** | Supported (97.7–99.9% resolvable citations) | **Supported (100.0%**, 206/206 answers cited) | **Supported (100.0%**, 238/238 answers cited) | The one hypothesis with an unqualified cross-corpus verdict: full provenance + complete decision logs in every run |

Notable regularity: **correct-refusal at the G2 tier is ~75–78% on all three corpora** while
its cost (false rejection) varies 51→85% — the gate's *benefit* is stable, its *price* is
corpus-dependent.

## 4. Exploratory finding: ontology coverage moderates the frontier shape

NOT pre-registered; presented as observational. The share of a corpus's concept vocabulary
that M4 can align to the governance ontology (BIZBOK) orders the corpora exactly as the
frontier shape does:

| Corpus | Aligned share | G2-tier coverage | Shape |
|---|---|---|---|
| DelucionQA | 98.2% | 44% | slope (dial usable through G4) |
| ExpertQA | 47.2% | 33% | band (dial usable through G2 tier) |
| HAGRID | 25.8% | 17% | cliff (dial unusable above G1) |

Mechanism is legible in the pipeline: authorization (G2+) derives from the D5 domain policy;
when the ontology cannot name a corpus's concepts, authorized-predicate sets thin out or
empty, and the gates refuse. Interpretation for practice: **measure ontology-corpus fit
(M4 aligned share) before deploying aggressive governance tiers — it predicts the coverage
price.** Proposed confirmatory follow-up: strongly in-ontology corpora (FinQA, CUAD) —
future work.

## 5. Contribution framing (post-evidence, for the manuscript)
1. **Governed abstention with a dial:** monotone corrRef gains on every corpus; on the
   N-heavy corpus governance *beats* naive on overall grade (65% vs 55%) — the first
   configuration where the governed system wins the headline metric. Caveat stated:
   refuse-all attains GA=70% on that stratum mix by construction; the claim rests on the
   corrRef/falseRej tradeoff, not GA alone.
2. **Auditability ~for free at G1:** near-parity coverage with full provenance and decision
   logs on the in-ontology corpus (falseRej 5%).
3. **Frontier characterization + the fit variable (exploratory):** the slope/band/cliff
   taxonomy and the aligned-share ordering.
4. **NOT claimed:** hallucination reduction (H2 ceiling), population estimates for
   runs 2–3 (probe scope), confirmatory status for §4.

## 6. Caveats carried into the paper
- Run-1 numbers above were judged by gemini-2.5-pro (withdrawn by Google 2026-07-19);
  runs 2–3 by gemini-3.1-pro-preview. The Run-1 re-judge under the new judge (in progress)
  provides the judge-agreement analysis; all cross-run comparisons will be restated under
  the single consistent judge, with the original preserved.
- accuracy-on-answered is conditional on each config's own answered subset (selection
  effects at low coverage: G2+ accuracies describe few, hard-filtered answers).
- Build-model difference run 1 vs 2–3 (forced deprecations, deviation-logged): affects
  generalization breadth, not within-run validity.
- Runs 2–3 are reduced-corpus probes (anti-cherry-picking defense: Subset_Selection_Validity.md).


## 7. Judge robustness — Run-1 dual-judge analysis (7A-2, complete)

Run 1's full 8,208 pairs were re-judged with the successor judge (gemini-3.1-pro-preview)
after Google withdrew the pre-registered judge (gemini-2.5-pro). Original judging preserved
untouched (post-re-judge hash verification: 47/47); re-judge sealed as `results/run1_rejudge/`.

| Statistic | Value |
|---|---|
| Pairs compared | 8,208 (100%) |
| Raw verdict agreement (incl. refusal classifications) | 91.3% |
| Agreement on judged pairs (MATCH/NO_MATCH both) | 84.1% (n=4,365) |
| Cohen's κ (judged pairs) | **0.681** (substantial) |
| MATCH rate | 0.506 (original) → 0.578 (successor) |
| Flip asymmetry | 504 NO→MATCH vs 190 MATCH→NO — successor is systematically more lenient |
| Where leniency lands | Verbose configs: G0 (+161/−8), G1 (+147/−26); sparse G2+ configs ≈ symmetric |

Consequences: (a) frontier STRUCTURE is judge-invariant — coverage, refusal, false-rejection
identical by construction; accuracy orderings and the monotone corrRef dial preserved;
(b) absolute accuracy LEVELS are judge-dependent (+8–17 pts under the successor);
(c) H1's ±.05 absolute bound is therefore judge-sensitive on Run 1 (Δ .034 → .080) — the
paper reports both judges and scopes the parity claim accordingly; (d) all cross-run
comparisons in this document's §2–§4 remain valid and are restated under the single
consistent judge below.

**Run-1 headline numbers under the consistent judge (gemini-3.1-pro-preview):**
G0 100%/86%/1.00; G1 93%/78%/1.00 (falseRej 5%); G2 44%/19%; G3 38%/16%; G4 35%/14%;
corrRef 41→83%. Cross-corpus under ONE judge: naive acc 86/86/82, G1 acc 78/72/69 —
level-comparable at last.


## 8. Statistical inference — Run-1 paired bootstrap (7A-4, B=10,000, seed 20260720)

Metric definitions for this section: coverage = judged-answer share; accuracy-on-answered =
MATCH / (MATCH+NO_MATCH); corrRef = refusal share of the unanswerable stratum. Records
resampled with replacement; both arms evaluated on the identical resample (paired).

**Per-config 95% CIs (consistent judge, gemini-3.1-pro-preview):**
G0 cov [.924,.956], acc [.843,.888], corrRef [.286,.529] · G1 cov [.907,.942], acc
[.772,.827], corrRef [.297,.547] · G2 cov [.408,.473], acc [.368,.465], corrRef
[.673,.881] · G4 cov [.317,.378], acc [.338,.446], corrRef [.730,.918].

**H1 — paired Δ accuracy (G1 − naive), both judges:**

| Judge | Δ | 95% CI | Verdict vs ±.05 bound |
|---|---|---|---|
| Original (2.5-pro, pre-registered) | −.018 | [−.050, +.014] | Within bound (at its edge); includes 0 → parity supported |
| Successor (3.1-pro-preview) | −.065 | [−.090, −.041] | Excludes 0 → real cost, bounded ≤ ~.09; straddles bound |

**H3 — paired Δ corrRef (G2 − naive), successor judge:** +.250 to +.500 (95% CI; excludes 0)
— the abstention gain is judge-robust and inferentially solid.

Paper sentence: G1 attains accuracy parity within the pre-specified bound under the
pre-registered judge; under the successor judge a small real cost appears (4–9 points,
95% CI). The abstention gain is large and robust under either judge. Runs 2–3 CIs to be
added (probe N ⇒ wide intervals; reported for completeness, not for headline claims).
