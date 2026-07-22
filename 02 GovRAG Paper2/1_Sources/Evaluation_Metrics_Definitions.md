> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\5_Manuscript\Evaluation_Metrics_Definitions.md — edit the canonical, then re-snapshot. See Source_Register.docx.

# GovernRAG / Paper 2 — Evaluation Metrics Reference
*Single source of truth for every metric produced by E3_Unified_Evaluation.py (and B3_spectrum_axes.py).
Definitions, formulas, contextual meaning, and caveats. Use for the manuscript's Evaluation section.*

Notation: for a set of evaluation records, each record is scored under one **configuration** (a governance
setting) and belongs to one **answerability stratum**. Counts below are per-configuration unless noted.

---

## 1. What is being evaluated — the configurations (governance spectrum + axes)

The system is not one model but a **tunable governance dial**. Each configuration is one operating point.

- **G0 — Naive.** Ungoverned RAG baseline: the generation model answers from the raw retrieved context,
  no authorization. Reference point for "no governance."
- **G1 — Cited.** Any retrieved chunk is admitted with a provenance citation; no authorization filter.
- **G2 — Grounded.** Only evidence passing the Q5 predicate-authorization filter is admitted.
- **G3 — Strict.** Requires >= 1 authorized triplet to answer (the system's default gate).
- **G4 — Corroborated.** Requires >= 2 authorized triplets (strongest).
- **Ontology axes (applied on top of G2), the two ontology-derived governance dimensions:**
  - **Axis A — reference-ontology conformance** (`GOVRAG_ONTOLOGY`): `not_unmapped` drops triplets whose
    endpoints are Unmapped to the reference ontology; `conformant` keeps only Match/Adaptive endpoints.
  - **Axis B — domain affinity** (`GOVRAG_AFFINITY_MIN`): drops chunks whose M1 `wa_score` (viewpoint-domain
    affinity) is below a threshold tau.

Coverage falls and governance strictness rises as one moves G0 -> G4; the axes add orthogonal filtering.

---

## 2. Strata — answerability

Every record is labelled **answerable** or **unanswerable** from the gold benchmark (DelucionQA gold
`adherence_score`: answerable = the gold answer is supported by the provided context; unanswerable = it is not).
This is the DelucionQA generalization of E2's Positive/Negative (P/N) conditions.
- **Answerable (P):** correct behavior is to answer correctly.
- **Unanswerable (N):** correct behavior is to abstain (refuse).

Stratifying prevents a system from looking good by answering everything (inflating accuracy) or refusing
everything (inflating safety). Accuracy is judged on the answerable stratum; abstention quality on both.

---

## 3. Per-answer judgments (LLM-as-judge)

### 3.1 Verdict — MATCH / NO_MATCH / SAFE_SILENCE
The judge (a stable, independent LLM) compares the system answer to the gold answer after stripping
provenance markers (`[CHNK_...]`, `[RESIDUAL_...]`).
- **MATCH** — the answer contains the gold fact.
- **NO_MATCH** — the answer is factually wrong or hallucinated.
- **SAFE_SILENCE** — the answer explicitly refuses / abstains (e.g. "insufficient evidence", BLOCKED).
Meaning: separates *correct*, *wrong*, and *declined* — you cannot reduce governance quality to a single
right/wrong bit, because a refusal is neither correct nor a hallucination.

### 3.2 Condition grade (E2 semantics, retained)
Combines verdict with the stratum:
- Answerable: `SUCCESS` if MATCH, else `FAILURE_<verdict>`.
- Unanswerable: `SUCCESS_boundary` if SAFE_SILENCE; `FAILURE_leakage` if MATCH (answered something it
  shouldn't have — parametric leakage / hallucination); `FAILURE_badoutput` otherwise.
Meaning: the human-readable per-record verdict; the origin of the governance-accuracy metric (Sec 5.2).

### 3.3 Faithfulness — TRACe adherence
**TRACe** is the RAGBench evaluation framework (Relevance, Utilization, Completeness, **Adherence**).
We report **Adherence**: the fraction of the answer's claims that are grounded in the admitted context
(LLM-judged, per answered tuple). "Faithfulness" and "TRACe adherence" are the same column here.
- Range 0-1; 1.0 = every claim supported by context; low = ungrounded / hallucinated.
Caveat: computing it needs a second judge call per answer, hence the `--no-trace` fast-screen flag that
skips it. It is distinct from E2's per-record "verdict trace" printout (`--record N`).

---

## 4. Coverage and accuracy

Let `total` = records scored under a config; `answered` = records not refused;
`answerable_total` = answerable records; `adh_match` = answerable records judged MATCH.

- **Coverage** = answered / total. The answer rate; falls as governance tightens. Judge-independent.
- **Accuracy (adherent stratum)**, written `acc(adh)` = adh_match / answerable_total. Of the questions that
  *should* be answerable, the fraction answered correctly (a refused answerable counts against it).
- **Risk-coverage frontier** = the curve of accuracy (or risk = 1-accuracy) vs coverage across G0..G4.
  The core artifact: it shows how much answer coverage is traded for governance strictness. Prior fail-closed
  systems report a single point on this curve; we report the whole curve.

---

## 5. Governance metric triad (abstention quality)

Refusals are not uniformly good or bad; the triad separates them by stratum.

- **Refusal rate** = refused / total. How often the system declines (any reason). = 1 - coverage.
- **Correct-refusal rate** = (SAFE_SILENCE on unanswerable) / unanswerable_total. Of the questions that
  *should* be refused, the fraction correctly refused. Higher = better boundary maintenance.
- **False-rejection rate** = (refused on answerable) / answerable_total. Of the answerable questions, the
  fraction wrongly refused. Higher = more usable answers thrown away. This is the cost side of strictness,
  and the metric CogniGraph is nearly alone in reporting (its "49% false-rejection reduction").
Meaning: a governance layer is good if it raises correct-refusal without raising false-rejection.

---

## 6. Comparability metrics (vs CogniGraph)

- **token-F1** = SQuAD-style bag-of-tokens F1 between the (marker-stripped) system answer and the gold
  answer: with precision p = |common tokens| / |answer tokens|, recall r = |common| / |gold tokens|,
  `F1 = 2pr / (p+r)`. Averaged over answered answerable records. A content-overlap measure of answer quality.
- **Governance accuracy (GA)** = (records graded SUCCESS*) / total, i.e. correct-per-condition behavior
  (answerable answered correctly OR unanswerable correctly refused). The single-number "did it behave
  correctly under governance" rate.
- **Constrained-F1** = 0.5 * token-F1 + 0.5 * GA. Adopted from CogniGraph (Kumar 2026) as the direct
  comparability number: it fuses answer quality (token-F1) with governance correctness (GA) so a system
  cannot score well by being fluent while violating governance, or vice versa. We report it per config; a
  fail-closed system reports one value, we report Constrained-F1 across the whole spectrum.

---

## 7. Evidence-scoping metrics (what governance removed)

From Q5's per-record audit (`audit_metadata.evidence_reduction`), averaged per config. These explain
*mechanically* where coverage is lost, and support the "scopes evidence, not answers" analysis.

- **predTrp** (predicate_triplets_dropped) — triplets removed by predicate authorization (Q5 core filter).
- **ontTrp** (ontology_triplets_dropped) — triplets removed by Axis A (ontology conformance).
- **affChk** (affinity_chunks_dropped) — chunks removed by Axis B (domain affinity).
- **chkTot** (chunks_dropped_total) — total chunks dropped (Tier-1 + Tier-2 authorization).
- **trpKept** (triplets_kept) — triplets surviving into the answer prompt.
- **chkKept** (primary_chunks_kept) — primary chunks surviving into the answer prompt.
- **Governance ratio (GR)** — Q5's governed_text_len / total_evidence_len: the fraction of admitted
  evidence that is authorized/governed. 1.0 = fully governed context. Reported as a per-config mean.

---

## 8. Model protocol (validity guards)

- **Generation parity.** The G0 naive baseline uses the *same* generation model as the governed answer (Q6),
  so a naive-vs-governed difference reflects the *pipeline*, not a model swap. (E2's use of a different
  baseline model, gemma-3-4b-it, violated this; E3 fixes it.)
- **Judge independence.** The evaluation judge (default gemini-2.5-pro) differs from the generation model,
  so the judge is not grading its own outputs. A *stable* (non-preview) judge is used for reproducibility.
- **Determinism.** Generation and judging run at temperature 0; residual variation at small N is treated as
  noise (differences below ~1-2 records at N=20 are not interpreted).

---

## 9. One-line reading guide
Coverage + acc(adh) + the frontier = the core trade-off. The triad = abstention quality (correct- vs
false-refusal). token-F1 / GA / Constrained-F1 = comparability to CogniGraph. Evidence-reduction + GR =
the mechanism (what governance removed). Faithfulness = grounding of what was answered.
