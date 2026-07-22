> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\2_Design\Evaluation_Design.md (git mirror: repo docs\ where present) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Paper 2 — Evaluation Design (superiority-at-parity framing)

*Derived from Paper 1 (Future Work + DO5/SAFE_SILENCE), the dissertation proposal §4.4/§5,
the frozen Q/E code, and the 2026-07 serve-many results. Supersedes the earlier
"parity + governance superiority" framing with a sharper, reviewer-proof claim.*
**Updated:** 2026-07-06.

---

## 1. The claim (superiority-at-parity)

> **In regulated / enterprise RAG, symbolic governance derived from the R/D/M pipelines makes
> GovernRAG *superior* to naive RAG on trustworthiness — it abstains on unsupported queries and
> grounds every answer in authorized provenance, reducing hallucination — *at parity* answer
> quality on answerable queries.**

Two axes, asymmetric on purpose:
- **Trustworthiness axis → SUPERIORITY.** Faithfulness (non-hallucination), correct abstention on
  unanswerable queries, and audit-grade provenance/authorization that naive RAG structurally lacks.
- **Answer-quality axis → PARITY.** On *answerable* queries GovernRAG answers about as accurately as
  naive (it does not sacrifice utility). Paper 1's ablation already showed governance adds
  *properties*, not raw accuracy — so quality is a parity claim, not a quality-win claim.

**Do NOT claim** superiority on QA accuracy. Governance can only hold or lower raw coverage; a headline
"governed beats naive on accuracy" contradicts Paper 1's ablation and invites desk-reject.

---

## 2. What "superiority" means — and the trap it must survive

**Superiority is selectivity, not refusal volume.** A system that refuses everything has perfect
faithfulness and zero utility — trivially "safe," scientifically worthless. The contribution is that
GovernRAG **answers the answerable AND refuses the unanswerable** — the *right* refusals. This is the
selective-prediction / risk–coverage framing ("know what you don't know"; SQuAD 2.0 unanswerables;
abstention QA). Your frozen E2 already encodes the test: Positive expects MATCH, Negative expects
SAFE_SILENCE.

**Consequences for interpretation (guardrails against reviewer attacks):**
- A high *overall* refusal rate is **not** a result on its own — it must be decomposed by answerability.
- Refusing *answerable* questions = **recall loss** (broken retrieval masquerading as safety), NOT
  superiority. Retrieval quality (answering the answerable) is therefore **load-bearing** for the claim.
- The utility floor must stay visible: report answer-rate and accuracy on the answerable stratum next to
  the safety metrics, always.

---

## 3. Determining answerability (independent of GovernRAG — never circular)

Every question is labelled **answerable** or **unanswerable** *before* either system runs, by a source
independent of GovernRAG. Priority order:

1. **Native benchmark label (preferred).** RAGBench per-example annotations / the E2 Positive–Negative
   flag: Positive = gold answer supported by the provided context; Negative = adversarial/unsupported.
   DelucionQA's faithfulness/answerability signal likewise. *(Requires pulling the native answerability
   field from source — the same fix as the empty-`gold` bug.)*
2. **Gold-derived.** Gold is a real fact → answerable; gold is an explicit "cannot be determined / not in
   context" → unanswerable.
3. **Independent NLI/entailment (fallback).** Judge (≠ generation model, temp 0): does the gold answer
   follow from the provided context? Disclosed as a derived label with its own error rate.

**Freeze the labels**; report per-stratum. This stratification *is* the superiority test.

---

## 4. Hypotheses

- **H1 (quality parity).** On the *answerable* stratum, GovernRAG and naive RAG are statistically
  equivalent on answer accuracy and on TRACe Relevance/Utilization/Completeness (equivalence bound, not
  "higher is better").
- **H2 (faithfulness superiority).** Across all queries, GovernRAG's hallucination rate < naive's;
  equivalently TRACe **Adherence** governed ≥ naive.
- **H3 (selective abstention).** On the *unanswerable* stratum, GovernRAG's correct-abstention rate ≫
  naive's; naive exhibits parametric leakage / contextual bleeding (Paper 1 DO5 at scale). Governed
  abstention on the *answerable* stratum stays low (selectivity, not blanket refusal).
- **H4 (auditability by construction).** GovernRAG emits provenance-resolvable citations, an authorization
  decision log, and a governance ratio for ~100% of outputs; naive has no analogue.

---

## 5. Metric suite (stratified: answerable vs unanswerable)

**A. Faithfulness / hallucination (headline superiority).**
- TRACe **Adherence** (boolean: all response sentences grounded in context) — governed vs naive.
- **Hallucination rate** = answered-but-unsupported / answered. Compute on **answered** tuples only
  (a refusal is not an unfaithful answer — exclude refusals from Adherence, unlike the first buggy pass).

**B. Selective prediction (the "right refusals" story).**
- **Risk–coverage:** accuracy vs answer-rate as the abstention threshold varies; report coverage at fixed
  risk and the area under the risk–coverage curve. Naive (no abstention) is a single point.
- **Abstention correctness:** on unanswerable, % correctly refused (governed vs naive); on answerable,
  % wrongly refused (recall loss — keep low).

**C. Answer quality on the answerable stratum (parity).**
- Correctness (MATCH / NO_MATCH judge, independent) and TRACe Relevance/Utilization/Completeness,
  governed vs naive, with an equivalence bound.

**D. Governance-native (naive ≈ 0 by construction).**
- Governance Ratio distribution (Q5 primary_kept / (primary_kept + residual_kept)).
- Provenance/citation coverage (% outputs with source-resolvable `[CHNK_*]`/`[RESIDUAL_*]`).
- Decision-log completeness, contract fidelity, evidence-binding correctness (Paper 1 FW#4).

**E. Cost + latency** — per-question $ and seconds, governed vs naive (substantiates "at bounded cost").

---

## 6. Projecting the pipelines into the contribution (DSR)

Not a system paper — a **design-knowledge** paper. The R/D/M/Q/E pipelines instantiate design principles;
the contribution is the validated principle, framed in the Gregor & Hevner **improvement** quadrant
(problem maturity high: RAG hallucination under regulation is a known problem; solution maturity low: no
corpus-derived symbolic-governance artifact validated at scale).

| Pipeline | DSR artifact | Contribution |
|---|---|---|
| **R / D / M** | constructs (governance manifest, authorized predicate, forensic provenance key) + model | method to build a **governed symbolic substrate** from an enterprise corpus |
| **Q** | method (reference monitor, tiered evidence, provenance-cited synthesis, boundary refusal) | **governed serving** that abstains and cites by construction |
| **E** | evaluation instrument | the dual-axis, stratified **selective-trustworthiness** evaluation |
| **Whole** | instantiation (GovernRAG) + design principles DP1–DP3 | evidence that **corpus-derived symbolic governance → selective, auditable trustworthiness** |

**Novelty by positioning (avoid "first-to"):**
- vs **naive RAG** — adds symbolic authorization, selective abstention, and an audit trail.
- vs **post-hoc guardrails / policy filters** — governance is *derived from the corpus* (R/D/M),
  provenance-native and predicate-authorized, not a bolted-on keyword/rule layer.
- vs **GraphRAG** — the KG is used for *authorization/governance*, not retrieval recall: a different
  purpose for the graph.

**The rolled-up result triad (what the reader takes away):**
1. **Governance coverage** — provenance ~100%, authorization enforced (artifact property).
2. **Selective behavior** — answers the answerable, abstains on the unanswerable (risk–coverage curve).
3. **Faithfulness superiority at answer-quality parity** — governed Adherence ≥ naive; accuracy at parity
   where answers are warranted.

Together these are the knowledge claim: *symbolic, corpus-derived governance produces selective,
auditable trustworthiness that ungoverned RAG structurally cannot — without sacrificing answer quality
where an answer is warranted.*

---

## 7. TRACe — exact specification (RAGBench, arXiv:2407.11005)

Context docs `D = {d_1..d_n}`; `R_i` = relevant sentences in `d_i`; `U_i` = utilized sentences; `Len()` =
sentence length. Per example, aggregated over docs.
- **Relevance** = `Σ Len(R_i) / Σ Len(d_i)` — fraction of retrieved context that is relevant.
- **Utilization** = `Σ Len(U_i) / Σ Len(d_i)` — fraction actually used by the response.
- **Completeness** = `Len(R_i ∩ U_i) / Len(R_i)` — fraction of relevant content utilized.
- **Adherence** = boolean per example: are ALL response sentences grounded in context? (this is the
  anti-hallucination metric, and the one where GovernRAG should win). **Score only on answered tuples.**

**Scorer:** RAGBench's fine-tuned **DeBERTa-v3-Large** span evaluator (local, ~free, no self-preference)
is primary; its benchmarking beats LLM judges (RAGAS/TruLens). LLM-judge (independent model, temp 0) is
the fallback. RAGBench gold TRACe labels are the reference/validation point, not a substitute for scoring
our own outputs.

---

## 8. Study design

- **Corpora:** DelucionQA + Emanual (Paper 1 named these); FinQA/CUAD later for breadth. All must carry a
  usable **answerability label** (Section 3).
- **Systems:** GovernRAG vs naive RAG baseline — **identical generation model, identical base context, no
  governance contract** (Paper 1's baseline definition). Served on the prebuilt graph, **design A**
  per-question chunk scoping.
- **Generation model (parity pair):** Q6 == naive baseline == same model (currently `gemini-3.5-flash`,
  GA/stable; pin the exact version for the final run). Q2 predicate-mapping same model. **Judge ≠
  generation** (independence): `gemini-2.5-flash` or the DeBERTa evaluator.
- **Scale:** 20 (smoke) → 465 → full; **N≥3 runs, report mean ± sd** (temp-0 nondeterminism finding).
- **Ablations:** governance on/off; anchor-linking on/off (`--no-linking`); design A vs B (secondary).

---

## 9. Methods — draft prose (lift + adapt)

**Setup.** We evaluate GovernRAG against a naive RAG baseline (identical generation model, identical base
context, no governance contract) on RAGBench DelucionQA and Emanual. The governed knowledge graph is built
once per corpus and served across all questions without rebuild; each question is scoped to its own
document chunks (design A), reconstructed by substring alignment. Each question yields two
(query, context, response) tuples — governed and naive — labelled *answerable* or *unanswerable* by an
independent source (native benchmark annotation; NLI-entailment fallback), fixed before serving.

**Metrics (dual-axis, stratified).** *Trustworthiness:* TRACe Adherence and hallucination rate (on
answered tuples); correct-abstention rate on the unanswerable stratum; a risk–coverage analysis of
selective prediction; and governance-native measures (Governance Ratio, provenance coverage, decision-log
completeness) for which the baseline has no analogue. *Answer quality:* correctness and TRACe
Relevance/Utilization/Completeness on the answerable stratum, with a statistical equivalence bound.
TRACe is scored with RAGBench's fine-tuned span evaluator (no self-preference); the correctness judge is
an independent model.

**Hypotheses.** H1 quality parity (answerable stratum); H2 faithfulness superiority (Adherence /
hallucination); H3 selective abstention (correct refusal on unanswerable, low refusal on answerable);
H4 auditability by construction.

**Reproducibility.** N≥3 runs; mean ± sd (temp-0 nondeterminism). Model versions, decoding params,
prompt-template hashes, per-run cost/latency in released run manifests.

**Threats to validity.** (a) *Circularity* — answerability is labelled independently of GovernRAG, never
by its refusals. (b) *Refuse-everything* — we report selectivity (answerable answer-rate) beside safety, so
blanket refusal cannot masquerade as success. (c) *Mapping* — question→chunk alignment is reconstructed by
substring (~97%), disclosed and bounded. (d) *Design A* scopes to gold documents; open-corpus design B is a
harder, separately reported condition. (e) *Judge* — independent model / DeBERTa; report judge-swap
sensitivity on a subset. (f) *Reference gold, not human gold* — DelucionQA's `response` is RAGBench's
faithfulness-annotated *reference answer* (GPT-3.5-generated), not a human gold answer. On the
non-adherent stratum the reference is itself unsupported (a hallucination), so **answer-match vs the
reference is computed ONLY on the adherent stratum** (where the reference is grounded); faithfulness
(TRACe Adherence) and abstention metrics run across **all** strata. Answerability = gold `adherence_score`.

---

## 10. Open items for Dr. Xu
1. Endorse **superiority-at-parity** (faithfulness/abstention superiority + answer-quality parity) as the
   Paper 2 claim, replacing the softer "parity + governance properties" framing.
2. Confirm the **answerability source** per corpus (native label vs NLI-derived) and the equivalence bound
   for H1.
3. Confirm the **selective-prediction (risk–coverage)** analysis as a first-class result, not an appendix.
