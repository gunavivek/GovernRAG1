> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\2_Design\Subset_Selection_Validity.md (git mirror: repo docs\ where present) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Subset Selection Validity — Runs 2–3 (ExpertQA, HAGRID)
*Updated 2026-07-20: executed Run-3 (drop-junk, 150 q) representativeness table added.*
*Updated 2026-07-19: HAGRID K=150 representativeness table added (run-order swap: HAGRID is now Run 2).*
*Methodological justification for reduced-corpus evaluation. Drafted 2026-07-18, before Run-2
execution. Source for the paper's Methods (corpus construction) and Limitations sections.
Pairs with: Analysis_Plan_and_Stopping_Rule.md (deviation entry 2026-07-12),
ragbench_select_and_prep.py (the deterministic selection rule), git commit 54ef322.*

## 1. Why not the full datasets (feasibility, quantified)
Generation and judging cost scale with question count; the **build** cost scales with corpus
size. Calibration from Run 1 (DelucionQA): 930-document build = $498.12; 912-question
serve+judge = $221.96. Extrapolation: ExpertQA full (7,403 documents, 2,027 unique questions)
≈ $3.5–4K build + ~$490 evaluation; HAGRID full (6,965 documents, 2,638 questions) similar.
Full-corpus replication across both datasets (~$8–10K) is infeasible for this project; the
reduced-corpus design reduces each run to ~$90–120 while preserving what runs 2–3 exist to
test (§3).

## 2. Why the selection is not cherry-picking (four tests)
The methodological line between legitimate subsetting and outcome-bending selection is
whether the selection could have been influenced by results. Four tests, all satisfied:

1. **Outcome-blindness.** The criterion is *document reuse* — a structural property of the
   benchmark (greedy full-cover: the K documents that jointly answer the most questions;
   a question is included iff ALL of its source documents are selected). No GovernRAG output
   for any ExpertQA/HAGRID question existed when the rule was fixed; selection cannot favor
   questions the system handles well because no one has ever observed the system on them.
2. **Pre-specification.** The rule and parameter (K = 60 documents) are recorded in the
   pre-registration's deviation log (dated 2026-07-12) and implemented in
   `ragbench_select_and_prep.py` before any run-2 generation.
3. **Public timestamp prior to execution.** Git commit `54ef322` (branch `paper2-spectrum`,
   github.com/gunavivek/GovernRAG1, pushed 2026-07-18) contains the selection script and the
   amended analysis plan; it provably precedes all Run-2/3 data.
4. **Mechanical reproducibility.** The selection is deterministic (fixed split concatenation
   order; first-occurrence question dedup; greedy ties broken by document hash). Any third
   party re-running the script obtains the identical record set; each selection emits a
   provenance manifest (`<subset>_<label>_selection.json`) with document hashes and counts.

Cherry-picking is post-hoc, outcome-driven, and invisible. This selection is prior,
structural, and public — the opposite on each axis.

## 2b. The junk-document filter is data cleaning, not selection (run 3, `--drop-junk`)

RAGBench's web-collected corpora contain scraping artifacts: HTTP error pages ("Access
Denied", "403 Forbidden", CAPTCHA interstitials) and sub-40-word stubs. The `--drop-junk`
filter excludes them before document selection. Five properties keep this on the data-
cleaning side of the line:

1. **Content-only, outcome-blind criterion.** A document is excluded iff its own text
   matches a FIXED, pre-registered marker list or falls under 40 words. No model output,
   no result, and no question property is consulted — the filter cannot "see" what it
   helps or hurts.
2. **Pre-registered before execution.** Markers and threshold are recorded in the
   deviation log (2026-07-19, GitHub-timestamped) and in `ragbench_select_and_prep.py`
   before any run-3 generation existed.
3. **Uniform application.** The same filter ran on every corpus from the moment it was
   introduced (HAGRID: 462 excluded; ExpertQA: 80 excluded) — never selectively invoked.
4. **Fully disclosed and reproducible.** Every excluded document's hash is published in
   the selection manifest (`junk_doc_hashes`); any third party can re-run the filter and
   obtain the identical exclusion set.
5. **Conservative direction of effect.** Machine-unusable evidence is precisely where a
   governance layer looks best (correct refusal) and a naive baseline looks worst
   (hallucination over garbage). Removing junk therefore removes cases FAVORABLE to the
   evaluated artifact — the filter biases against our hypotheses, not toward them.

An "Access Denied" page is not a hard document; it is a collection defect. Excluding it
is the corpus-level analogue of the question dedup already applied in Run 1, and the
representativeness table (§4) is recomputed on the post-filter selection.

**Paper-ready sentence (Methods):**
> Documents matching a pre-registered list of scraping-artifact markers (HTTP error
> pages, CAPTCHA interstitials) or shorter than 40 words were excluded before selection;
> exclusion hashes ship in each selection manifest, the filter is uniform across corpora,
> and its effect is conservative for our hypotheses, since unusable evidence is where
> governed abstention would otherwise be rewarded.

## 3. Claim scoping (what runs 2–3 do and do not assert)
Run 1 evaluated the **complete** DelucionQA benchmark (all 912 unique questions); the
paper's headline quantitative claims rest on that full-coverage run. Runs 2–3 are
**cross-corpus generalization probes**: they test whether the *qualitative shape* of the
governance frontier — the monotone coverage/abstention dial, the faithfulness ceiling, the
localization of coverage cost at the authorization step — reproduces on different corpora,
including a far richer unanswerable stratum (ExpertQA: 55% unanswerable vs. DelucionQA's 7%).
They are not population estimates of full-ExpertQA/HAGRID performance, and the paper does
not present them as such. Pattern replication imposes weaker representativeness demands than
parameter estimation; the claim is scoped to "questions answerable from the selected corpus."

## 4. Representativeness characterization (selection vs. population)
Even outcome-blind selection can yield an unrepresentative subset. For each selection we
publish a comparison of the selected questions against the full subset population on
observables available *independently of our system* (RAGBench gold annotations).

**Run 2 — ExpertQA, K=150 (computed 2026-07-18, selection of 176 of 2,027):**

| Observable | Selected (176) | Population (2,027) |
|---|---|---|
| Answerable share | 23.9% | 44.5% |
| Question length (words, mean) | 17.7 | 19.0 |
| Gold answer length (words, mean) | 135.5 | 154.0 |
| Gold relevance (mean) | 0.3 | 0.3 |
| Gold utilization (mean) | 0.2 | 0.2 |
| Gold completeness (mean) | 0.7 | 0.6 |
| Documents per question (mean) | 1.1 | 3.7 |
| Split mix (train/val/test) | 144/20/12 | 1621/203/203 |

READ: the selection matches the population on question length, gold-answer length, and all
three gold quality annotations — no evidence of systematically easier questions. Two
divergences, both structural and disclosed: (a) **answerability skew** (23.9% vs 44.5%
answerable) — ExpertQA's most-reused documents attract unanswerable expert questions;
(b) **docs-per-question** (1.1 vs 3.7) — full-cover selection inherently favors
few-document questions.

**Run 3 — ExpertQA, K=150 with `--drop-junk` (EXECUTED selection, computed 2026-07-20;
150 of 2,027; 80 error-page/stub documents excluded before selection; supersedes the
2026-07-18 pre-filter table above, retained for provenance):**

| Observable | Selected (150) | Population (2,027) |
|---|---|---|
| Answerable share | 30.0% | 44.5% |
| Question length (words, mean) | 17.5 | 19.0 |
| Gold answer length (words, mean) | 142.7 | 154.0 |
| Gold relevance (mean) | 0.4 | 0.3 |
| Gold utilization (mean) | 0.3 | 0.2 |
| Gold completeness (mean) | 0.7 | 0.6 |
| Documents per question (mean) | 1.0 | 3.7 |
| Split mix (train/val/test) | 122/19/9 | 1,621/203/203 |

READ: the junk filter moved the selection CLOSER to the population than the pre-filter
version on answerability (30.0% vs the earlier 23.9%; population 44.5%) and gold-answer
length (142.7 vs 135.5; population 154.0), with the gold quality annotations at or above
population — no evidence of an easier subset. The two structural divergences (N-heavy skew,
docs-per-question 1.0) are unchanged in kind, disclosed, and constitute the abstention-probe
design role (§ Complementary-strata).

**Run 2 — HAGRID, K=150 with `--drop-junk` (computed 2026-07-19, selection of 163 of 2,638;
462 error-page/stub documents excluded before selection per the pre-registered junk filter):**

| Observable | Selected (163) | Population (2,638) |
|---|---|---|
| Answerable share | 84.0% | 85.5% |
| Question length (words, mean) | 6.9 | 6.9 |
| Gold answer length (words, mean) | 23.1 | 36.4 |
| Gold relevance (mean) | 0.3 | 0.3 |
| Gold utilization (mean) | 0.3 | 0.2 |
| Gold completeness (mean) | 0.9 | 0.8 |
| Documents per question (mean) | 1.0 | 2.7 |
| Split mix (train/val/test) | 107/4/52 | 1,846/76/716 |

READ: the HAGRID selection mirrors its population on answerability (84.0% vs 85.5%), question
length (identical), and all three gold quality annotations — the parity-probe role holds. Two
divergences, both structural and disclosed: (a) shorter gold answers (23.1 vs 36.4 words) —
most-reused wiki passages attract factoid-style questions; (b) documents-per-question 1.0 vs
2.7 — the same full-cover artifact as ExpertQA, inherent to any bounded-build selection.

**Complementary-strata design (K-sweep evidence, both corpora):** the skew is turned into a
design feature. ExpertQA selections are N-heavy at every K (17–26% answerable, K=60..300)
→ ExpertQA serves as the **abstention probe** (134 unanswerable at K=150, 2.1× Run 1's
entire N-stratum). HAGRID selections mirror their population exactly (84% vs 85% answerable
at every K) → HAGRID serves as the **answerable/parity probe** (141 answerable at K=150).
Together the two corpora stress both halves of the frontier harder than either balanced
subset could.

**Reuse economics at K=150:** 1.17 (ExpertQA) / 1.11 (HAGRID) questions per built document,
vs 0.27 / 0.38 for the full corpora — a ~3–4× improvement in build cost per evaluated
question; marginal ratio ≈ 1.0 q/doc through K=150 and collapsing beyond (K=300 adds 35
questions for 150 documents), justifying K=150 as the knee of the curve.

## 5. Pre-committed text for the paper

**Methods (corpus construction):**
> For each additional corpus we construct a reduced benchmark by an outcome-blind structural
> rule: the K = 60 documents maximizing fully-covered questions under greedy set cover, and
> every question whose complete document set is contained in the selection. The rule, its
> implementation, and the amended analysis plan were committed publicly (repository commit
> 54ef322) before any generation on these corpora; the selection is deterministic and ships
> with a provenance manifest. Full-corpus evaluation is cost-infeasible at the build stage
> (§ cost analysis); Run 1 provides full-benchmark coverage on DelucionQA.

**Limitations:**
> Runs 2–3 evaluate reduced corpora selected by document reuse. The selection is structural,
> outcome-blind, deterministic, and timestamped prior to execution, and we characterize the
> selected questions against the full-subset population on system-independent observables;
> nevertheless, claims for these corpora are scoped to questions answerable from the selected
> documents, and the runs serve as generalization probes of the frontier's shape rather than
> population estimates.

## 6. Reviewer-preemption note
If asked "why not random question sampling instead?": random questions reference documents
outside any affordable build — a question is only evaluable if its documents are built. The
unit of affordability is the document set; selecting documents (and taking all their
questions) is the only sampling scheme compatible with a bounded build, and reuse-maximizing
selection is the variant that maximizes evidence per dollar without reference to outcomes.
