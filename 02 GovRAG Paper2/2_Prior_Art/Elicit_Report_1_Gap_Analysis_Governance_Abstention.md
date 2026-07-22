**Primary (positioning + gap):**

Analyze the literature on governance and trustworthiness controls in retrieval-augmented generation. Has prior work proposed a tunable, multi-level governance mechanism — where progressively stricter, ontology- or knowledge-graph-derived authorization constraints trade answer coverage against faithfulness, provenance, and abstention? Compare any such graded-governance approaches to confidence-based selective prediction and conformal abstention, and identify the closest prior work and the specific open gap.

Short answer: prior work has built each of the three ingredients — RAG governance, ontology/KG-derived authorization, and calibrated abstention — but I did not find any paper that fuses them into a *tunable, multi-level* governance dial where progressively stricter ontology-derived constraints trade coverage against faithfulness/provenance in the way conformal abstention trades coverage against error. Below is the landscape and where the gap sits.

**Governance-aware RAG (closest in spirit, but not tiered).**
Jain et al.'s Governance-Aware Agentic RAG is the nearest neighbor: it introduces governance-sensitive reranking over an AI-policy corpus (legal status, jurisdiction, source authority) and routes low-evidence cases to an ABSTAIN / HUMAN REVIEW branch, with an extractive composer to preserve provenance. It answers only when the retrieved evidence is well-grounded and defers uncertain cases, and it uses an extractive evidence-based composer rather than unconstrained generation to preserve grounding.[^1] Governance here is used as a scoring signal plus a single answerable/abstain gate — not as a knob with multiple strictness levels.

Two other 2026 systems tighten the enterprise side. Venkatesan et al.'s Policy-Aware RAG on the Lakehouse enforces lineage-driven retrieval so that every retrieved chunk maps to a valid data contract [^2]. Singh et al.'s Korosuke goes furthest toward a tunable trade-off: a hierarchical security-aware embedding space that mathematically preserves access-control constraints during semantic search, paired with an adaptive re-ranking algorithm that explicitly optimizes a relevance–security trade-off.[^3] That is the paper whose *shape* matches the "tunable" framing most closely — but the dial is a scalar in a utility function, not a set of ontology-derived tiers with per-level faithfulness/coverage guarantees.

Chen & Taipalus (metadata + fine-grained RBAC on top of RAG), Bhatt et al. (participant-aware access control for Copilot Tuning), and Lee's ACL model for enterprise RAG all treat authorization as a hard binary filter — not a graded coverage/faithfulness lever.

**Ontology- and KG-derived authorization (the constraint substrate, pre-LLM).**
There is a mature line here that predates RAG. Knechtel & Hladik's RBAC-CH derives concrete permissions from DL reasoning over an OWL ontology; Valzelli et al. give a fine-grained access-control model for knowledge graphs via query transformation; Saripalle et al. use RDF/RDFS with RBAC. The most recent, and the closest to what your primary question implies, is Abdelrazek et al. for 6G knowledge-base agents: a hybrid RBAC + first-order-logic framework that enforces authorization at the SPO triple level and eliminates permission inheritance so agents only see metadata their functional lifecycle requires.[^4] This gives you the machinery to *define* graded constraints from an ontology, but it is not connected to a generative pipeline's coverage/faithfulness trade-off.

**Selective prediction and conformal abstention (the calibration substrate).**
The other side of your comparison is well-developed and mature.

- *Confidence-based selective prediction* — Xin et al.'s "Art of Abstention," Kamath et al. (domain shift), Chen et al.'s self-evaluation adaptation — treat abstention as a scalar confidence threshold learned or regularized per model.
- *Conformal abstention* — Abbasi-Yadkori et al. use self-consistency + conformal prediction to bound hallucination rate; Xu et al. add representation-geometry calibration; Kang et al.'s C-RAG is the first to certify an upper confidence bound on RAG generation risk with theoretical guarantees under test-distribution shift, and it proves RAG beats a bare LLM on that bound when retrieval quality is non-trivial.[^5]
- *Conformal RAG* — CONFLARE quantifies retrieval uncertainty with a conformal similarity threshold; Feng et al.'s Conformal-RAG gives sub-claim–level factuality guarantees via group-conditional coverage [^6].
- *Learned conformal thresholds* — Tayebati et al. are the most methodologically adjacent to your "tunable dial" framing: they argue static CP thresholds fail to adapt to task complexity and distribution shift, and use RL to learn adaptive abstention thresholds that jointly balance coverage and informativeness.[^7]

Crucially, in every one of these the dial is a *confidence* or *nonconformity* score. Authorization / governance information never enters the calibration.

**Where the two traditions meet — and don't.**
The two lines run in parallel and rarely touch. Governance-aware and policy-aware RAG use ontology/metadata/lineage constraints as *hard filters* or as *ranking features*, then decide abstention via a coarse "evidence sufficient?" gate. Selective-prediction and conformal-abstention work provides the calibrated coverage-vs-risk knob, but its risk axis is model confidence or factuality — not the *authorization strictness* of the retrieved evidence. Korosuke's relevance-security utility (BKGq0OKw) and Jain et al.'s governance-sensitive reranker (wdDr0k0g) are the two closest attempts to make authorization a continuous lever, but neither exposes an ontology-derived, multi-level authorization ladder, and neither gives per-level statistical guarantees on faithfulness/coverage the way conformal RAG does on factuality.

**Closest prior work** (in decreasing order of overlap with your framing):
1. **Korosuke (Singh et al., 2026)** — closest on the "tunable trade-off" shape; hierarchical security embeddings + adaptive re-ranker with a relevance-security utility. Missing: ontology-derived authorization tiers, provenance/faithfulness guarantees per tier.
2. **Governance-Aware Agentic RAG (Jain et al., 2026)** — closest on "governance + abstention"; extractive composer, evidence abstention, governance-indicator reranker. Missing: tunable multi-level dial, KG/ontology constraint substrate, statistical guarantees.
3. **C-RAG (Kang et al., 2024) + Conformal-RAG (Feng et al., 2025)** — closest on "principled coverage-vs-risk knob." Missing: the risk axis is factuality/generation risk, not authorization strictness.
4. **Dynamic Authorization for KB Agents in 6G (Abdelrazek et al., 2026)** — closest on "ontology-derived triple-level authorization." Missing: any connection to generation-time coverage/faithfulness trade-off.

**The specific open gap.**
I did not find a system that (a) derives a *lattice* of authorization constraints from a KG/ontology (e.g., class-hierarchy-, predicate-, or triple-level filters à la RBAC-CH or Abdelrazek), (b) exposes strictness as a *tunable multi-level parameter* rather than a binary access decision or a scalar utility weight, and (c) gives per-level, empirically calibrated guarantees on the resulting *faithfulness / provenance / abstention rate*, in the way C-RAG or Tayebati et al. give per-α guarantees on generation risk. In particular, no paper I retrieved treats ontology-derived authorization as the *nonconformity substrate itself* — i.e., driving the abstention/coverage curve with governance strictness rather than with confidence. That composition — graded ontology-authorization as a conformal-style dial over RAG faithfulness — is the unclaimed intersection.

Two secondary gaps worth flagging: none of the governance-aware RAG papers report a per-strictness *faithfulness-vs-coverage curve* (the field default is a single operating point), and none evaluate whether stricter authorization actually improves attributability, as opposed to only reducing leakage. Both are natural evaluation contributions if you build in this space.

Caveats: this is one search pass focused on RAG, ontology/KG authorization, selective prediction, and conformal abstention; adjacent literatures I did not deeply mine — differential-privacy-tuned RAG, guardrail-policy DSLs, deliberative KG reasoning with proof carriers — could contain closer prior art, and there is likely 2026 preprint activity I did not surface.

[^1]: Jain et al., 2026. Governance-Aware Agentic Retrieval-Augmented Generation with Evidence Abstention for Reliable AI Policy Question Answering. 2026 International Conference on Artificial Intelligence, Systems, and Emerging Technologies (ICAISET).

[^2]: Venkatesan et al., 2026. Policy-Aware RAG on the Lakehouse: Lineage-Driven Retrieval Over Apache Iceberg on S3 to Reduce Hallucination and Cost. Computing and Communication Workshop and Conference.

[^3]: Singh et al., 2026. Korosuke: A Principled Framework for Security-Preserving Contextual Retrieval in Enterprise Knowledge Systems. 2026 IEEE International Students' Conference on Electrical, Electronics and Computer Science (SCEECS).

[^4]: Abdelrazek et al., 2026. Dynamic Authorization for Knowledge-Base Agents in 6G.

[^5]: Kang et al., 2024. C-RAG: Certified Generation Risks for Retrieval-Augmented Language Models. International Conference on Machine Learning.

[^6]: Feng et al., 2025. Response Quality Assessment for Retrieval-Augmented Generation via Conditional Conformal Factuality. Annual International ACM SIGIR Conference on Research and Development in Information Retrieval.

[^7]: Tayebati et al., 2025. Learning Conformal Abstention Policies for Adaptive Risk Management in Large Language and Vision-Language Models. arXiv.org.