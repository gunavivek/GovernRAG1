**Methods comparison:**

Synthesize and compare methods for controlling the coverage–faithfulness (risk–coverage) tradeoff in RAG and LLM question answering: selective prediction, conformal prediction, answer abstention, and guardrail / policy-constrained generation. Which of these provide auditable, per-answer provenance alongside the abstention decision, and how is the tradeoff typically evaluated (which metrics and benchmarks)?

The four families sit on a spectrum from *heuristic-but-flexible* to *statistically guaranteed-but-narrow*, and they answer different questions about the risk–coverage curve. A brief comparison, then the provenance and evaluation parts.

## The four families

**Selective prediction (SP).** Learn a confidence signal — model softmax, a trained calibrator, self-evaluation prompts, or auxiliary uncertainty heads — and threshold it to decide whether to answer or abstain. The classic Kamath et al. formulation showed that raw softmax is overconfident under domain shift, and a calibrator trained on out-of-domain errors lifts coverage from 48% to 56% at 80% accuracy on SQuAD-plus-five-domain mixtures [^1]. Later variants tune the *signal* — parameter-efficient adaptation with self-evaluation prompts [^2], dedicated uncertainty-aware decoding heads [^3], or black-box embedding classifiers that don't touch the LLM at inference [^4]. SP is cheap and general but its guarantees are only as good as the calibrator on the deployment distribution; recent work shows entropy alone is not enough for safe SP in LLMs.

**Conformal prediction (CP).** A distribution-free wrapper that converts any nonconformity score into either a *prediction set* with a marginal coverage guarantee $$1-\alpha$$, or, in more recent variants, a *risk-controlled* abstention threshold [^5]. For MCQA it produces small sets that almost always contain the correct option [^6]. Conformal Language Modeling generalises this to open-ended generation by calibrating a *stopping rule* over sampled candidates and proving the returned set contains at least one acceptable answer with high probability, with sentence-level "not-a-hallucination" guarantees inside it [^7]. API-only variants use sample-frequency + semantic-similarity nonconformity scores instead of logits [^8]. The key limitation is the exchangeability assumption — Geissler et al. show it can silently break in RAG when the retriever mixes distributions, and propose diagnostic metrics for when guarantees actually hold [^9].

**Answer abstention.** The umbrella that SP and CP feed into, but also including refusal-tuned decoding, self-consistency dispersion, and post-abstention re-attempt loops [^10]. Two developments matter for RAG:
- *Risk-controlled refusal that fuses multiple evidence signals.* UniCR combines sequence likelihoods, self-consistency dispersion, retrieval compatibility, and verifier feedback into a calibrated probability and enforces a user-specified error budget with conformal risk control [^11].
- *Cascaded abstention for RAG.* BalanceRAG jointly calibrates two thresholds — an LLM-only branch and a RAG fallback — so the system can answer from parametric knowledge, escalate to retrieval, or abstain, with a certified system-level error rate [^12]. COIN goes the other direction, calibrating a single threshold that filters *one* generated answer per question under a user-specified false-discovery-rate constraint via Clopper–Pearson bounds [^13].

**Guardrails / policy-constrained generation.** A distinct family: instead of thresholding correctness, guardrails classify inputs and outputs against a *policy* (safety, access control, jurisdictional rules) and block, rewrite, or refuse. GuardAgent compiles a natural-language safety spec into executable guardrail code that deterministically checks agent actions, reaching 98% / 83% guardrail accuracy on healthcare and web-agent benchmarks [^14]. This is coverage–faithfulness control only in an indirect sense — the abstention decision is driven by policy match, not by prediction confidence. Recent work highlights a specific failure mode called the *deliberation-to-enforcement gap*, where the guardrail's rationale and its final label diverge [^15], which is why SP/CP and guardrails are best viewed as complementary rather than substitutes.

## Auditable per-answer provenance alongside the abstention decision

This is where the families sharply differ.

- **Selective prediction, by itself, provides no provenance.** It emits a score and a keep/abstain flag. Any attribution has to come from an orthogonal component (retrieval logs, post-hoc citation).
- **Conformal prediction** provides an *auditable statistical* trail — the calibration set, the nonconformity score, and the $$\alpha$$ level are recorded per decision, and CLM even certifies which sub-spans of a generation are individually supported [^7]. Conformal-RAG extends this to RAG by giving group-conditional coverage guarantees on *sub-claims* using signals internal to the RAG pipeline, retaining up to 60% more high-quality sub-claims than off-the-shelf CP applied to the LLM output [^16]. That is per-answer, per-claim provenance with a probabilistic guarantee attached.
- **Purpose-built RAG hallucination detectors** are the strongest form of source-linked provenance. HalluGraph aligns knowledge graphs extracted from context, query, and response and emits decomposed *Entity Grounding* and *Relation Preservation* scores that trace every asserted entity and relation back to a source passage — explicitly framed as an audit trail for legal RAG [^17]. Geissler et al.'s attention-based factuality classifier flags inconsistent answers with up to 77% detection accuracy and stamps confidence per generation [^9].
- **Guardrails** provide *policy* provenance (which rule fired, why the input was blocked) but usually not *content* provenance; recent reasoning-based guardrails try to close this by requiring the decision to be entailed by a policy-grounded rationale [^15].
- Orthogonally, the **attributed-QA literature** — Bohnet et al.'s Attributed QA formulation [^18], AutoAIS-style automatic evaluators [^19], and AttributionBench [^20] — provides the evaluation machinery for "is this answer's citation actually supported?", which is what any provenance-carrying abstention system needs to be judged against. A recent survey of 134 papers taxonomises this evidence-based-generation space and catalogues 300 evaluation metrics across seven dimensions [^21].

So the auditable-provenance-plus-abstention combination in practice comes from **CP applied at the sub-claim level** (Conformal-RAG, CLM), or from **hallucination detectors that natively link back to source passages** (HalluGraph, factuality-classifier RAG). SP and generic guardrails give an abstention decision but no answer-level evidence trail.

## How the tradeoff is evaluated

Two things get reported: aggregate risk–coverage behaviour, and coverage at a fixed target risk.

**Metrics**
- *Risk–coverage curves and area-under-them* — AURC and area under the accuracy-coverage curve (AUACC) are the workhorses; e.g. Chen et al. report AUACC 91.23% → 92.63% on CoQA [^2], and Varshney et al. report AUC-of-risk-coverage gains of 8–10% over max-prob on MNLI [^22].
- *Coverage at fixed accuracy / fixed risk* — Kamath et al.'s "% answered at 80% accuracy" is the canonical form [^1]; UniCR reports coverage at fixed risk plus AURC [^11].
- *AUROC of the abstention classifier* — treats it as a binary "will this be wrong?" detector.
- *Empirical coverage vs nominal $$1-\alpha$$* and *set size* — the CP-specific pair; a valid method must attain nominal coverage while shrinking sets.
- *False discovery rate control* — COIN reports FDR at user-specified level plus retention rate [^13].
- *Attribution / faithfulness scores on the non-abstained answers* — AutoAIS, AttributionBench macro-F1, entity-grounding / relation-preservation AUC in HalluGraph [^17][^20]. Without these, a "high coverage" number can hide unfaithful answers.

**Benchmarks**
- *Short-form / extractive QA*: SQuAD and its OOD extensions (NewsQA, TriviaQA, HotpotQA, SearchQA, NaturalQuestions) as in Kamath et al.'s selective-QA-under-domain-shift setup [^1]; CoQA for conversational QA [^2]; TruthfulQA for generative selective QA [^3].
- *MCQA*: MMLU and MedQA-style datasets are the standard CP testbeds [^6].
- *Open-ended / long-form RAG*: TriviaQA, Natural Questions, and PopQA appear in BalanceRAG [^12]; the biography-generation FActScore setup and radiology-report generation are used in CLM and UniCR-style work [^7][^11].
- *Attribution*: Attributed QA on Natural Questions [^18], AttributionBench (a compilation of prior attribution datasets, where even fine-tuned GPT-3.5 tops out around 80% macro-F1) [^20], and the New-Bing-style curated tests in AutoAIS [^19].
- *Guardrails*: policy-specific benchmarks like EICU-AC (healthcare access control) and Mind2Web-SC (web-agent safety policies) [^14], plus prompt- and response-harmfulness detection sets used by ConsisGuard [^15].

The practical picture is that most serious RAG deployments now stack these: a CP or CP-plus-risk-control layer sets an *answer* threshold with a formal guarantee, a hallucination detector produces the *per-claim* audit trail, and a guardrail layer handles orthogonal policy constraints. The evaluation almost always pairs a risk–coverage curve with an attribution/faithfulness metric — reporting either alone is now considered incomplete.

[^1]: Kamath et al., 2020. Selective Question Answering under Domain Shift. Annual Meeting of the Association for Computational Linguistics.

[^2]: Chen et al., 2023. Adaptation with Self-Evaluation to Improve Selective Prediction in LLMs. Conference on Empirical Methods in Natural Language Processing.

[^3]: Yang et al., 2023. Uncertainty-aware Language Modeling for Selective Question Answering. arXiv.org.

[^4]: Schönwälder et al., 2025. Abstention is all you need. International Conference on Data Science and Advanced Analytics.

[^5]: Campos et al., 2024. Conformal Prediction for Natural Language Processing: A Survey. Transactions of the Association for Computational Linguistics.

[^6]: Kumar et al., 2023. Conformal Prediction with Large Language Models for Multi-Choice Question Answering. arXiv.org.

[^7]: Quach et al., 2023. Conformal Language Modeling. International Conference on Learning Representations.

[^8]: Su et al., 2024. API Is Enough: Conformal Prediction for Large Language Models Without Logit-Access. Conference on Empirical Methods in Natural Language Processing.

[^9]: Geissler et al., 2026. Towards Dependable Retrieval-Augmented Generation Using Factual Confidence Prediction.

[^10]: Wen et al., 2024. The Art of Refusal: A Survey of Abstention in Large Language Models. arXiv.org.

[^11]: Oehri et al., 2025. Trusted Uncertainty in Large Language Models: A Unified Framework for Confidence Calibration and Risk-Controlled Refusal. arXiv.org.

[^12]: Jia et al., 2026. BalanceRAG: Joint Risk Calibration for Cascaded Retrieval-Augmented Generation.

[^13]: Wang et al., 2025. COIN: Uncertainty-Guarding Selective Question Answering for Foundation Models with Provable Risk Guarantees. arXiv.org.

[^14]: Xiang et al., 2024. GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning. arXiv.org.

[^15]: Wang et al., 2026. ConsisGuard: Aligning Safety Deliberation with Policy Enforcement in LLM Guardrails.

[^16]: Feng et al., 2025. Response Quality Assessment for Retrieval-Augmented Generation via Conditional Conformal Factuality. Annual International ACM SIGIR Conference on Research and Development in Information Retrieval.

[^17]: Noël et al., 2025. HalluGraph: Auditable Hallucination Detection for Legal RAG Systems via Knowledge Graph Alignment. arXiv.org.

[^18]: Bohnet et al., 2022. Attributed Question Answering: Evaluation and Modeling for Attributed Large Language Models. arXiv.org.

[^19]: Yue et al., 2023. Automatic Evaluation of Attribution by Large Language Models. Conference on Empirical Methods in Natural Language Processing.

[^20]: Li et al., 2024. AttributionBench: How Hard is Automatic Attribution Evaluation?. Annual Meeting of the Association for Computational Linguistics.

[^21]: Schreieder et al., 2025. Attribution, Citation, and Quotation: A Survey of Evidence-based Text Generation with Large Language Models. arXiv.org.

[^22]: Varshney et al., 2020. It's better to say "I can't answer" than answering incorrectly: Towards Safety critical NLP systems. arXiv.org.