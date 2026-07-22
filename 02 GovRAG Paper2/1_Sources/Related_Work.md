> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\5_Manuscript\Related_Work.md — edit the canonical, then re-snapshot. See Source_Register.docx.

# Related Work (Paper 2 draft)

Our work sits at the intersection of four research streams — governance-aware retrieval-augmented
generation, ontology- and knowledge-graph-derived authorization, calibrated abstention, and
neuro-symbolic faithfulness verification. Each supplies one ingredient of a governed RAG system, but,
as we argue below, none combines them into a *tunable, multi-level, ontology-derived governance dial*
whose strictness drives the coverage–faithfulness trade-off. We organize the discussion around a simple
distinction that the neuro-symbolic literature itself draws: *where* the knowledge graph acts relative
to generation.

## Governance-aware and policy-aware RAG

A recent line of work adds governance signals to RAG retrieval and answer selection. Jain et al. (2026)
introduce Governance-Aware Agentic RAG, which reranks retrieved evidence by governance indicators
(legal status, jurisdiction, source authority) and routes low-evidence queries to an abstain-or-review
branch, using an extractive composer to preserve grounding. Venkatesan et al. (2026) enforce
lineage-driven retrieval so that every chunk maps to a valid data contract, and Singh et al. (2026,
*Korosuke*) learn a hierarchical, security-aware embedding space paired with an adaptive re-ranker that
optimizes an explicit relevance–security utility. Related enterprise systems (Chen and Taipalus; Bhatt
et al.; Lee) treat authorization as a hard binary access filter. Across this stream, governance is used
either as a *ranking feature* or as a *single answerable/abstain gate*; where a trade-off is exposed
(Korosuke), it is a scalar term in a utility function rather than a set of ontology-derived strictness
levels with per-level guarantees.

## Ontology- and knowledge-graph-derived authorization

A mature, largely pre-LLM literature derives access-control constraints from formal ontologies:
Knechtel and Hladik's RBAC-CH computes permissions by description-logic reasoning over OWL; Valzelli et
al. give fine-grained access control for knowledge graphs via query transformation; Saripalle et al.
use RDF/RDFS with RBAC. Most recently, Abdelrazek et al. (2026) enforce authorization at the
subject–predicate–object triple level for 6G knowledge-base agents, eliminating permission inheritance.
This stream provides the machinery to *define* graded, ontology-derived constraints, but it is not
connected to a generative pipeline's coverage or faithfulness behavior.

## Selective prediction and conformal abstention

A parallel and well-developed stream controls the risk–coverage trade-off with a *confidence* signal.
Selective prediction thresholds a learned or self-evaluated confidence score (Kamath et al., 2020; Chen
et al., 2023; Yang et al., 2023), and the abstention survey of Wen et al. (2024) catalogs the space.
Conformal methods convert any nonconformity score into distribution-free coverage or risk guarantees:
Quach et al. (2023) calibrate a stopping rule for open-ended generation; Kang et al. (2024, *C-RAG*)
certify an upper bound on RAG generation risk; Feng et al. (2025, *Conformal-RAG*) give sub-claim
factuality guarantees; and Tayebati et al. (2025) learn adaptive abstention thresholds by reinforcement
learning. Crucially, in every case the dial is a *confidence or nonconformity score* — authorization or
governance information never enters the calibration. These methods also, by themselves, carry no
answer-level provenance; attribution must come from an orthogonal component, and the field now regards a
risk–coverage curve reported *without* a paired attribution/faithfulness metric as incomplete (Schreieder
et al., 2025; Bohnet et al., 2022; Li et al., 2024).

## Neuro-symbolic faithfulness and verification

Knowledge-graph-grounded RAG uses the graph in two ways. As a *pre-generation retriever*, GraphRAG and
constrained-decoding methods (Li et al., 2025, *DoG*; Ma et al., 2026, *C2RAG*) keep generation on
well-formed KG chains to improve recall and grounding. As a *post-generation verifier*, the graph checks
the output: HalluGraph (Noël et al., 2025) scores Entity Grounding and Relation Preservation against
source passages as an audit trail; CogniGraph (Kumar, 2026) places a SemanticSHACL gate that performs
OWL-aware three-layer validation — framework fidelity, scope boundary, and cross-reference integrity —
"post-generation, semantically" on every agent output, evaluated with a joint Constrained-F1 metric; and
SITL (Nadimuthu et al., 2026) repositions the KG "at the end of the pipeline as a formal verification
layer" that "automatically validates or rejects stochastic neural output." These systems demonstrate that
symbolic conformance can gate generation, but each applies a *single, fail-closed* gate to the *output*,
reports a *single operating point*, and does not expose strictness as a tunable parameter.

## The gap and our position

Two observations follow. First, the ingredients exist separately — governance-aware retrieval,
ontology-derived authorization, calibrated abstention, and symbolic verification — but no prior system
uses *graded, ontology-derived authorization strictness as the abstention substrate itself*, driving a
coverage–faithfulness frontier the way conformal methods drive coverage against confidence. Second, the
neuro-symbolic distinction between using the KG *before* generation (as context) and *after* generation
(as verification) leaves a third position unoccupied: using the KG as an **authorization gate on the
evidence admitted to generation**. GovernRAG occupies exactly this slot. Its reference monitor governs
what evidence the model may condition on — filtering by authorized predicates, reference-ontology
conformance, and domain affinity — at a strictness that is *tunable across a spectrum of levels*, and it
reports the full per-level risk–coverage frontier that governance-aware RAG omits and that conformal RAG
computes over confidence rather than authorization. Where CogniGraph and SITL place one fail-closed
symbolic gate on the model's output, GovernRAG places a tunable, ontology-derived reference monitor on
the evidence admitted to generation. We adopt CogniGraph's Constrained-F1 for comparability and, unlike
the governance-aware RAG stream, pair every operating point with a faithfulness/attribution measure.

## References
(to be formatted to venue style)

Abdelrazek et al. (2026). Dynamic Authorization for Knowledge-Base Agents in 6G.
Bohnet et al. (2022). Attributed Question Answering. arXiv.
Chen et al. (2023). Adaptation with Self-Evaluation to Improve Selective Prediction in LLMs. EMNLP.
Feng et al. (2025). Response Quality Assessment for RAG via Conditional Conformal Factuality. SIGIR.
Jain et al. (2026). Governance-Aware Agentic RAG with Evidence Abstention. ICAISET.
Kamath et al. (2020). Selective Question Answering under Domain Shift. ACL.
Kang et al. (2024). C-RAG: Certified Generation Risks for RAG. ICML.
Kumar (2026). CogniGraph: Governed Graph-of-Agents … Semantic SHACL Validation and Constrained F1. SSRN 6837300.
Li et al. (2024). AttributionBench. ACL.
Li et al. (2025). Decoding on Graphs (DoG). ACL.
Ma et al. (2026). Toward Robust GraphRAG (C2RAG).
Nadimuthu, Das, Soni, Sheth (2026). Symbolic-in-the-Loop (SITL). IEEE Internet Computing.
Noël et al. (2025). HalluGraph. arXiv.
Quach et al. (2023). Conformal Language Modeling. ICLR.
Schreieder et al. (2025). Attribution, Citation, and Quotation: A Survey. arXiv.
Singh et al. (2026). Korosuke. IEEE SCEECS.
Tayebati et al. (2025). Learning Conformal Abstention Policies. arXiv.
Venkatesan et al. (2026). Policy-Aware RAG on the Lakehouse.
Wen et al. (2024). The Art of Refusal: A Survey of Abstention in LLMs. arXiv.
Yang et al. (2023). Uncertainty-aware Language Modeling for Selective QA. arXiv.
