# GovRAG Paper 2 — Master Document
**The Governance Frontier of Retrieval-Augmented Generation: A Pre-Registered
Three-Corpus Evaluation of Tunable, Ontology-Derived Governance**

Vivek Gunasekaran · University of Arkansas at Little Rock
Working master, v1.0-draft (assembled 2026-07-22) · Sources: sealed archives
(git tags run1/2/3-complete) and committed design documents; every number traces to a
SHA-256-manifested archive.

**Extraction recipes:** *TPS paper (Scenario 1)* = ch 1, 2 (compressed), 3.1, 4, 5 (headline
tables), 6, 7, 9 · *Combined paper (Scenario 2)* = add Part-1 framework summary at full §1.3
depth · *KG paper (2027)* = ch 4.2, 5.6, 6.2 + confirmatory run · *Defense* = ch 1, 5, 6, 8.

---

## 1. Introduction

### 1.1 The question Paper 1 could not answer
GovernRAG (Part 1 of this program) established that a retrieval-augmented generation
architecture can produce cited, policy-authorized answers with complete decision logs: a
per-record governance contract anchored on an enterprise reference vocabulary (the
Governance Manifest), predicate-validated retrieval under that contract, and
reference-monitor mediation of the generation context. The demonstration held on ten cases
— but its execution model rebuilt the knowledge graph for every question (~3 hours each),
capping evaluation at demonstration scale. The architecture's central promise therefore
remained unpriced: **evaluated at benchmark scale, what does governance actually cost, and
what does it buy?**

### 1.2 What this paper contributes
This paper answers that question with a pre-registered, report-regardless evaluation across
three RAGBench corpora (1,225 questions; 11,025 judged answer-pairs across all passes),
made feasible by a build-once/serve-many re-engineering of the execution layer that froze
every governance decision of Part 1. Contributions:

**C4 — Feasible governed evaluation.** An execution-layer refactoring reducing evaluation
cost from O(n·C_build) to O(C_build + n·C_query), with a hardened orchestration harness;
the full DelucionQA benchmark (912 questions × 9 configurations) ran for $222, and two
additional corpora for under $45 combined.

**C5 — The governance frontier.** The first per-level characterization of governance
strictness in RAG: coverage, accuracy, faithfulness, the abstention triad (refusal /
correct-refusal / false-rejection), provenance resolvability, and cost, measured at five
governance levels and three ontology/affinity axis variants, on three corpora, under a
dual-judge robustness protocol. Prior governance-aware RAG systems report single operating
points; this work reports the curve.

**C6 — Ontology-fit as a deployment predictor (exploratory).** The fraction of a corpus's
extracted concepts alignable to the governance ontology (98.2% / 47.2% / 25.8% across our
corpora) orders the frontier's shape — slope, band, cliff — giving practitioners a
measurable pre-deployment predictor of what strict governance will cost on their corpus.

### 1.3 The Part-1 substrate in one page
Five pipelines and an audit layer, connected by typed flows. **R** builds the global
enterprise reference ontology (BIZBOK-derived, 553 concepts). **D** anchors each corpus to
governance domains and composes the per-record Governance Manifest (D5) — the contract
carrying authorized predicates and attribute targets forward through every stage. **M**
builds the per-corpus concept graph under the manifest's predicate budget: LLM chunking
(M1), triple extraction (M2), graph construction (M3), concept augmentation (M3.3),
ontology alignment (M4 — each concept classified Match/Adaptive/Unmapped against the
reference), embedding (M5). **Q** resolves each question under contract: intent gate (Q1),
signature extraction (Q2), governed graph retrieval (Q3), residuals (Q4), the Reference
Monitor (Q5) that admits or drops evidence with logged reasons, and cited synthesis (Q6)
that answers or refuses. **The governance dial** parameterizes Q5/Q6 only — G0 ungoverned
baseline, G1 Cited, G2 Grounded (authorized predicates), G3 Strict, G4 Corroborated, plus
ontology-conformance and domain-affinity axes — so per-level differences isolate the
governance mechanism itself. Retrieval, graph, and models are identical across levels.
(Full architecture: Paper 1 v10.2 §4; supplementary module glossary therein.)


---

## 2. Related work and positioning

*Assembled from Related_Work.md (2026-07-07) and Prior_Art_Synthesis.md (full-text reads of CogniGraph and SITL).*

## Related Work (Paper 2 draft)

Our work sits at the intersection of four research streams — governance-aware retrieval-augmented
generation, ontology- and knowledge-graph-derived authorization, calibrated abstention, and
neuro-symbolic faithfulness verification. Each supplies one ingredient of a governed RAG system, but,
as we argue below, none combines them into a *tunable, multi-level, ontology-derived governance dial*
whose strictness drives the coverage–faithfulness trade-off. We organize the discussion around a simple
distinction that the neuro-symbolic literature itself draws: *where* the knowledge graph acts relative
to generation.

### Governance-aware and policy-aware RAG

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

### Ontology- and knowledge-graph-derived authorization

A mature, largely pre-LLM literature derives access-control constraints from formal ontologies:
Knechtel and Hladik's RBAC-CH computes permissions by description-logic reasoning over OWL; Valzelli et
al. give fine-grained access control for knowledge graphs via query transformation; Saripalle et al.
use RDF/RDFS with RBAC. Most recently, Abdelrazek et al. (2026) enforce authorization at the
subject–predicate–object triple level for 6G knowledge-base agents, eliminating permission inheritance.
This stream provides the machinery to *define* graded, ontology-derived constraints, but it is not
connected to a generative pipeline's coverage or faithfulness behavior.

### Selective prediction and conformal abstention

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

### Neuro-symbolic faithfulness and verification

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

### The gap and our position

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

### References
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

### 2.x Contribution positioning note (verbatim)

### Contribution Positioning — Constrained-F1 Risk & Outcome-Contingent Framing
*Paper 2. Decide the headline metric AFTER the run; pre-committed phrasings below so the
framing is principled, not post-hoc rationalization. Pairs with Related_Work.md and
Prior_Art_Synthesis.md.*

#### The risk (why the absolute number can hurt us)
CogniGraph (Kumar 2026) reports Constrained-F1 = 0.5·F1_token + 0.5·Governance-Accuracy = **0.756**
at a single fail-closed operating point on **MultiGov-30** (curated EU-AI-Act/GDPR/DORA/NIS2 reasoning,
30 items, multi-agent architecture). If our best-level Constrained-F1 on **DelucionQA / RAGBench**
(standard RAG QA, answerability-stratified, single-corpus authorization) lands well below 0.756, a
reviewer skims it as "worse than CogniGraph." That reading is category-confused (different benchmark
difficulty, different task, different architecture), but the burden is on us to neutralize it *up front*.

#### The invariant claim (holds regardless of the number — never bury this)
Our contribution is **not** a higher Constrained-F1 than CogniGraph. It is:
1. **Position**: governance applied to the *evidence admitted to generation* (reference monitor / Q5),
   not to the model's *output* — the unoccupied third slot in the KG-before / KG-after / KG-as-gate
   taxonomy (SITL's own framing).
2. **Frontier**: the full per-level **risk–coverage curve**; CogniGraph and SITL each report a single
   operating point that is one point on our curve.
3. **False-rejection continuum**: CogniGraph reports one 49% false-rejection delta; we report the
   correct-answer false-rejection rate at *every* strictness level.
These three are outcome-independent. The absolute Constrained-F1 is a *comparability courtesy*, not the thesis.

#### Decide the headline by outcome
Let CF1* = our best-level Constrained-F1; CF1_cg = 0.756 (theirs, different benchmark — not a target).

| Scenario | Trigger | Lead metric | Constrained-F1 role |
|---|---|---|---|
| **A — Competitive** | CF1* within ~0.05 of 0.756, or clearly strong in absolute terms | Constrained-F1 **parity** + frontier as the extra | Headline column; "parity at a point, superiority across the curve" |
| **B — Below but defensible** | CF1* materially < 0.756 but stable/interpretable across levels | **False-rejection-vs-coverage** + frontier shape | Secondary column, with benchmark-difficulty caveat |
| **C — Weak absolute** | CF1* low or noisy (small-N, judge variance) | **Three-position novelty** + false-rejection continuum | Appendix only, with explicit non-comparability statement |

Guardrail for all three: **never** write "we beat/outperform CogniGraph." Always "generalize / characterize /
locate their operating point on our frontier." A same-data head-to-head is not available (their code /
MultiGov-30 not runnable here; different pipeline position) — state this as a scoped limitation, not a gap.

#### Pre-committed sentences (paste the matching block)

**Scenario A (competitive).**
> On DelucionQA our reference monitor attains Constrained-F1 comparable to the single-operating-point
> figure reported by CogniGraph (Kumar 2026), while additionally characterizing the full
> governance-strictness risk–coverage frontier — of which a fail-closed gate is one point. Governance
> quality is thus not traded against answer quality at a fixed setting but made *tunable*, with the
> operating point selectable to a target false-rejection budget.

**Scenario B (below but defensible).**
> We adopt CogniGraph's Constrained-F1 for comparability, but our central result is the
> false-rejection-vs-coverage frontier: across G0–G4 the correct-answer false-rejection rate moves
> continuously with authorization strictness, generalizing the single 49% false-rejection delta CogniGraph
> reports between two gate configurations. Absolute Constrained-F1 is not directly comparable across
> benchmarks — MultiGov-30 evaluates curated multi-agent regulatory reasoning (30 items); we evaluate
> evidence-admission governance on standard RAG QA with answerability stratification — so we report it as a
> secondary, within-system metric and base our claims on the *shape* of the frontier.

**Scenario C (weak absolute).**
> Our contribution is architectural and evaluative rather than a Constrained-F1 improvement: we place the
> symbolic gate on the evidence admitted to generation (the reference-monitor position), and we report the
> per-level risk–coverage and false-rejection frontier that prior fail-closed systems (CogniGraph, SITL)
> collapse to a single operating point. Because their architectures gate the *output* and their benchmarks
> are not runnable in our setting, we make no absolute Constrained-F1 comparison; we report it in Appendix X
> as a within-system diagnostic only.

#### Reviewer-preemption line (use in all scenarios, Limitations or Eval-setup)
> We do not run CogniGraph or SITL as live baselines: they gate at a different pipeline position (post-
> generation output validation vs. our pre-admission evidence authorization), their code and MultiGov-30
> benchmark are not available to us, and our claim is to *characterize the frontier they each reduce to a
> single point*, not to exceed that point. Comparison is therefore at the metric level (shared Constrained-F1
> definition) rather than head-to-head on identical data.

#### Operational rule
Report both metrics at every level in the results table (coverage, accuracy-on-adherent, faithfulness,
Constrained-F1, false-rejection). **Choose the headline only after seeing CF1*.** Pre-registering the three
phrasings above keeps the choice defensible rather than data-dredged: we are selecting emphasis, not the finding.

---

## 3. Making governed evaluation feasible: build-once / serve-many

### 3.1 The throughput problem (verbatim design record)

### Problem Statement — Throughput Bottleneck in Per-Query Knowledge-Artifact Materialization

#### Abstract framing
Evaluating GovernRAG requires, for each (document, question) trial, (i) constructing a governance-bounded knowledge artifact — the D-pipeline **Governance Manifest** and the M-pipeline **knowledge graph** — and then (ii) resolving the query against it (Q + E pipelines) and scoring it. In the current evaluation harness the artifact is **re-materialized for every trial and then discarded**, so the achievable sample size *n* is bounded by

> **T_total = n · (C_build + C_query)**, with **C_build ≈ 3 h ≫ C_query**.

With C_build dominating, n ≈ 10 already costs ~30 h and n > a few dozen is infeasible. This prevents statistically meaningful evaluation (no confidence intervals, no power), which is the central empirical gap between the Level-1 existence proof (Paper 1) and the quantitative study the dissertation proposal requires.

#### The underlying problem
The harness **conflates offline index construction (ingestion) with online query serving (retrieval)** and keeps **no persistent, reusable index**. Concretely, a *corpus-level* artifact (graph + manifest) is rebuilt at *query-level* granularity.

The required property is **build–query separation with index reuse** (a.k.a. offline-indexing / online-serving, build-once / query-many): construct the per-corpus artifact once and amortize it over many queries.

#### Formal cost model
- **Current:** `T = n · (C_build + C_query)` → **O(n · C_build)** since C_build ≫ C_query.
- **Target:** `T = D · C_build + n · C_query`, where **D = number of distinct corpora** (often 1, since records are slices of one parent corpus) → **O(C_build + n · C_query)**.
- Because the query phase is stateless and embarrassingly parallel, the serve term reduces further to **n · C_query / P** for parallelism P.

Net effect: *n* becomes bounded by data availability, not by build time — enabling n > 1000.

#### Sub-problems to solve
1. **Artifact persistence & addressability** — materialize the graph + manifest once and key them by corpus/record id (a read-only "index").
2. **Query-time serving without rebuild** — the Q-pipeline loads (not rebuilds) the index; load-once-in-memory or database-backed.
3. **Build determinism / reusability** — the index must be a valid, fixed artifact to reuse across all trials (LLM-based extraction must be pinned, or the index treated as a one-time frozen build).
4. **(Optional) incremental materialization** — append new documents without a full rebuild (relevant only if corpora evolve).

#### Why this is an *execution-model* problem, not an architecture problem
Code inspection shows the pipelines already support the amortized pattern:
- `M3/M5` build a NetworkX **MultiDiGraph** whose forensic edge keys embed `record_id` → one graph holds many records.
- `D5` emits **per-record manifests** in a single multi-record JSONL.
- `Q3` already does `nx.read_graphml(global_graph)` and **prunes by `record_id`** (`filter_id`) at query time.

So a single global graph + manifest store can serve arbitrarily many queries by record-id filtering. The bottleneck is the *runner* (`A0_GovRAG_Runner`: one record per run into single-slot `output/`, then overwrite), not the pipeline logic.

#### Relevant concepts / search terms (for prior art and solutions)
- "offline indexing vs online retrieval", "ingestion–retrieval decoupling" (RAG/IR systems)
- "index construction amortization", "build-once query-many", "amortized preprocessing"
- "materialized index / view reuse", "incremental materialization" (databases)
- "computation memoization / caching of intermediate artifacts" (pipeline/workflow systems)
- "knowledge-graph persistence & indexed subgraph query" (graph databases: Neo4j, Memgraph, KùzuDB)
- "vector/graph index persistence and reload" (FAISS/Chroma serialize; NetworkX `read/write_graphml`)
- experiment design: "shared fixture reuse across trials", "stateful test corpus"

#### One-line statement (for a methods section)
*GovernRAG's evaluation throughput is bounded by per-query re-materialization of a corpus-level knowledge artifact; we remove this bound by separating one-time offline index construction from stateless online query serving with a persisted, record-addressable index, reducing total cost from O(n·C_build) to O(C_build + n·C_query) and enabling statistically powered evaluation (n ≫ 10³).*

### 3.2 The refactoring plan as executed (verbatim design record)

### Build–Serve Refactor Plan — Unbounding *n* for the RAGBench Evaluation

**Goal:** move from n ≈ 10 (per-query rebuild) to n ≫ 1000 by building the GovernRAG index once per corpus and serving all questions against it. Corpus choice: **enterprise-like RAGBench subsets** (FinQA, CUAD, TechQA), which fit the BIZBOK anchoring and avoid the orphan-patch.

---

#### 1. What the code actually does today (inspection findings)
| Component | Behaviour | Implication |
|---|---|---|
| `A0_GovRAG_Runner.py` | Orchestrates D00→D0→M0→Q0→E2→Z0 for **one record per run**, writing to single-slot `output/` | Build is coupled to a single query and overwritten each run |
| `M3 / M5` | Build a NetworkX **MultiDiGraph**; persist `output/M5_Embedded_Graph.graphml`; edge keys carry `record_id` | **Graph is already multi-record** |
| `D5` | Per-record manifests in one `D5_Extraction_Manifest.jsonl` | **Manifest store is already multi-record** |
| `Q3` (`Q3_..._Retrieval_Engine`) | `nx.read_graphml(M5_Embedded_Graph.graphml)` then **prunes by `record_id`** (`filter_id`) | **Per-record serving from a global graph already works** — but it re-reads the graphml on every instantiation |
| `Q0` | Loads + runs Q1..Q6 for a given `record_id` (no rebuild) | Serve path is already load-based |

**Conclusion:** the expensive D+M build is corpus-capable; the harness simply runs it per record and discards it. The refactor is an **orchestration + persistence** change, not a pipeline rewrite.

---

#### 2. Target design — two phases

##### Phase 1 — BUILD (once per dataset/corpus)
1. Stage the **full parent corpus** as a multi-record JSONL (every slice/document as a record), instead of one-record-per-question.
2. Run `D0` → `M0` **once** → produces one multi-record `D5_Extraction_Manifest.jsonl` + one global `M5_Embedded_Graph` covering all records.
3. Persist as a **read-only, keyed index**:
   ```
   index/<dataset>/
       D5_Extraction_Manifest.jsonl
       M1_Governed_Chunks.csv
       M5_Embedded_Graph.graphml      (or load into a graph DB — §4)
       build_manifest.json            (corpus id, record count, model, hash, timestamp)
   ```
   → **C_build paid once per dataset**, never per question.

##### Phase 2 — SERVE (per question; looped + parallel)
1. Load the index **once** (a long-lived graph object or a DB connection), reused across all questions.
2. For each question: `Q0(record_id)` + `E2` (Naive baseline) + **TRACe scoring** → answer, citations, governance log, metrics.
3. Write results to `results/<dataset>/...`; **parallelize** across questions (they are independent).
   → **C_query in minutes (or seconds), n unbounded.**

---

#### 3. Concrete, minimal-risk changes
1. **New stager** (adapt `A0_RAGBench_PerQuestion_Stager`): emit the full parent corpus as multi-record, not per-question.
2. **New build runner** (adapt `A1_RAGBench_D0_M0_Runner`): run D0→M0 once over the full corpus; write to `index/<dataset>/` (keyed, not single-slot `output/`).
3. **Refactor Q3 + Q5 to read the index path and load the graph ONCE** (a service object created before the question loop), instead of re-reading `output/M5_Embedded_Graph.graphml` per question. Keep the existing `record_id` filtering as-is.
4. **New serve runner**: `for q in questions: Q0(record_id_of(q)) + E2 + eval`, reading from `index/<dataset>/`, writing to `results/<dataset>/`. Add a worker pool for parallelism.
5. **Add the TRACe metric step** (the missing harness) in the eval — Relevance, Utilization, Completeness, Adherence — wired to RAGBench gold annotations + the generated answer/context.

These touch the *runners and the Q3/Q5 I/O*, not the governance logic (D/M/Q internals stay frozen).

---

#### 4. Storage decision — GraphML vs Graph database
**Recommendation: do (A) first for the immediate win; adopt (B) when the corpus graph outgrows RAM or you want incremental/concurrent builds.**

**(A) Keep GraphML, load-once-serve-many (fastest, ~1–2 days).**
- Refactor Q3 to load the global graph a single time into a reused object; the question loop never reloads.
- Removes *both* the rebuild and the per-query graphml reload.
- Works well if one enterprise-subset graph fits in RAM (verify by profiling — §6).

**(B) Embedded / server graph database (for scale, incremental, concurrency).**
- Persist the graph in a DB; `Q3` queries by `record_id` via an **indexed** lookup (no whole-graph load), supports concurrent question serving and incremental corpus updates.
- **KùzuDB** — embedded (no server), Cypher, columnar, fast, has vector indexes; ideal for a single-researcher reproducible pipeline. Lowest ops overhead.
- **Neo4j** — industry standard, great tooling/Browser, vector index in v5; heavier (server) but well-documented.
- **Memgraph** — in-memory, very fast, Cypher; good if the graph fits in RAM but you want DB semantics.
- The M5 graph also carries embeddings, so a DB with a **vector index** (Neo4j 5 / Kùzu) can unify symbolic + dense retrieval and remove the separate FAISS/embedding step.

**Practical path:** GraphML load-once now → if the FinQA/CUAD graph is too big for RAM or you want to keep appending corpora, port the persisted graph to **KùzuDB** (least friction) and have Q3 issue a record-scoped Cypher query.

---

#### 5. Throughput math
| Setup | n = 1000 | Notes |
|---|---|---|
| Current (rebuild per query) | ~3,000 h | infeasible |
| GraphML load-once, serial serve | C_build (hrs, once) + 1000·C_query | if C_query ≈ 1–2 min → ~1 day |
| + parallel serve (P=8) | C_build + 1000·C_query/8 | hours |
| Graph DB, record-scoped query | C_build + 1000·(indexed query) | no whole-graph RAM load; concurrent |

---

#### 6. Risks / things to verify before committing
- **Governance granularity:** decide whether each parent-corpus *document* is a `record` (per-document manifests inside a shared graph — preserves the governance story) or the whole corpus is one record (simpler, weaker governance claim). This choice should match Paper 2's claim ("governance at parity").
- **Build determinism:** M2 triple extraction is LLM-based. To *reuse* the index legitimately, either pin model/temperature/seed, or treat the build as a **frozen one-time artifact** for the study (acceptable, and you already froze the code).
- **Memory profile:** build the index on one enterprise subset first and measure graph size + RAM before choosing GraphML-in-memory vs DB.
- **BIZBOK orphan-patch:** with enterprise subsets, D2 should anchor without heavy patching — confirm the orphan rate drops vs the manuals.
- **Record↔question linkage:** confirm how RAGBench `record_id` maps questions to parent-corpus slices (quick check of `*_parent.jsonl` / `*_questions.jsonl`).

---

#### 7. Recommended next steps (in order)
1. **Confirm data structure** — inspect `*_parent.jsonl` vs `*_questions.jsonl` to lock the record↔question key.
2. **Build the index once on one enterprise subset** (start with FinQA) → measure C_build, graph size, RAM.
3. **Implement Q3/Q5 load-once + a serial serve loop + TRACe scoring** → measure C_query on ~50 questions.
4. **Parallelize the serve loop**, scale to n ≫ 1000.
5. **Decide GraphML-in-memory vs KùzuDB/Neo4j** based on the measured graph size and whether you want incremental corpora.

This unbounds *n* without changing the governance architecture — exactly the unlock needed to turn Paper 1's existence proof into Paper 2's statistically powered evaluation.

### 3.3 The hardened harness (narrative)

The refactoring produced a harness whose components each answer a failure mode observed
during the campaign: **B1** snapshots a completed build to an immutable per-corpus index
with a build manifest; **B2** serves question slices against the loaded graph with
per-question chunk scoping (design A); **B4** batches serving under a run-tag guard that
refuses cross-dataset mixing and auto-archives per-run accumulators; **B5** orchestrates
the frozen build stages with corpus and API-key guards, live streamed output, a stall
watchdog (stdout + file-growth + process-tree CPU), bounded retries, and stage checkpoints;
**E3P** scores answer-pairs in parallel with per-pair checkpointing, bounded HTTP timeouts,
and worker-failure isolation. Three campaign incidents materially shaped this design and
are reported as methodology evidence rather than hidden: a stale-resume contamination
(downstream build stages silently resuming a previous corpus's partial outputs — caught
from topology counts in live logs, quarantined, and rebuilt; the working slot is now
cleaned before every build), a scorer id-join defect introduced by a provenance fix (caught
by cross-checking scoring output against serve archives; two invalidated scoring passes are
retained as *.bad_join evidence), and repeated mid-study model withdrawals by the provider
(§7). The harness's economics: Run 1 = $221.96 serve+judge on a $498 build; Runs 2–3
combined < $45 end-to-end (reduced-corpus selection, §4.2).

---

## 4. Evaluation design

### 4.1 Pre-registration and deviation policy (the analysis plan, verbatim, incl. full deviation log)

### Paper 2 — Analysis Plan & Stopping Rule (pre-registration)

**Author:** Vivek  **Date committed:** 2026-07-06
**Purpose:** lock the run and the reporting *before* seeing results, to protect against
scope creep and result-driven tuning. This is a commitment, not a plan to revisit.

---

#### The commitment (verbatim)

> *"I run the full benchmark once, N≥3, stratified by answerability, on the frozen pipeline
> (anchor fix included). I report faithfulness, abstention correctness, provenance coverage,
> and answerable-stratum accuracy — whatever they are — and that is the paper."*

**Report-regardless clause.** The results of the pre-registered run are the paper, whether
they support, partially support, or refute the hypotheses. A refuting or mixed result is a
valid Design-Science contribution (an evaluated artifact with characterized boundary
conditions) and will be reported as such — not tuned away.

---

#### Frozen design (locked — no further changes)

- **Pipeline:** R/D/M build (done, `index/delucionqa/`) + frozen Q1–Q6 + Q5 reference monitor.
- **Only permitted edits already applied & reviewed:** Q2 (anchor-linking + JSON hardening),
  Q3 (design-A scoping), model lines. Recorded in `Frozen_Code_Changes.md`.
- **Generation model (parity pair):** Q6 == naive baseline == `gemini-3.5-flash` (GA; pin exact
  version at run time). Q2 same. **Judge ≠ generation** (`gemini-2.5-flash` or DeBERTa).
- **Serving:** build-once/serve-many, design-A per-question chunk scoping, anchor-linking ON.
- **No more pipeline tuning to raise answer rate.** Out of scope for this paper.

---

#### Strata (independent of GovernRAG — fixed before the run)

Each question labelled **answerable** / **unanswerable** from an independent source:
native benchmark answerability field (preferred) → gold-derived → NLI-entailment fallback.
Labels frozen before serving; never defined by GovernRAG's own refusals.

---

#### Metrics (exact) — reported per stratum + overall

1. **Faithfulness (headline).** TRACe **Adherence** (answered tuples only) and **hallucination
   rate** = answered-but-unsupported / answered. Governed vs naive.
2. **Abstention correctness.** Unanswerable stratum: % correctly refused (governed vs naive).
   Answerable stratum: % wrongly refused (recall loss — kept visible, not hidden).
3. **Provenance coverage.** % governed outputs with source-resolvable `[CHNK_*]`/`[RESIDUAL_*]`.
4. **Answerable-stratum accuracy (parity).** Correctness (MATCH/NO_MATCH judge) + TRACe
   Relevance/Utilization/Completeness, governed vs naive, with a stated equivalence bound.
5. **Selective prediction.** Risk–coverage curve (confidence proxy = Q5 governance ratio /
   kept-triplet count); governed = curve, naive = single point.
6. **Governance-native (context).** Governance Ratio distribution; decision-log completeness
   (Q5 audit / Z2–Z3). Naive ≈ 0 by construction.
7. **Cost + latency.** Per-question $ and seconds, governed vs naive.

#### Hypotheses & decision rules (set now)

- **H1 (quality parity, answerable stratum):** supported if governed vs naive difference on
  accuracy + R/U/C falls within the pre-set equivalence bound (state bound before run, e.g. ±0.05).
- **H2 (faithfulness superiority):** supported if governed Adherence ≥ naive and governed
  hallucination rate < naive (report effect size + N≥3 variance).
- **H3 (selective abstention):** supported if correct-abstention(unanswerable) ≫ naive AND
  wrong-refusal(answerable) is low. If wrong-refusal is high → reported as the coverage-cost finding.
- **H4 (auditability):** supported if provenance + decision-log coverage ≈ 100% for governed.

---

#### Scale & runs

- **N ≥ 3** independent runs (temp-0 nondeterminism); report **mean ± sd**.
- Scale: 20 (smoke, done) → validate ruler on ~50–100 → **full benchmark once**.
- Corpora: DelucionQA first (built); Emanual next if time permits; FinQA/CUAD = future work.

---

#### Measurement layer to finish BEFORE the pre-registered run (bounded; not design changes)

1. Fix `gold` loading + pull native **answerability** label from source data.
2. Stratified reporting in `trace_scorer` (answerable/unanswerable split).
3. Adherence scored on answered tuples only.
4. Risk–coverage from existing signals; per-run cost/latency logging.

These build the *ruler*; none alters governance logic. When (1)–(4) pass a sanity check on
~50 questions (naive accuracy is non-zero and plausible), the ruler is trusted and the
pre-registered full run proceeds.

---

#### Deviation policy

Any change after this point (pipeline, metric, stratum, model) is **logged with date + reason**
in this file before it is made. Silent changes are not permitted. If a deviation is required to
fix a *measurement* bug, that is allowed and logged; a deviation to improve *results* is not.

#### Deviation log
- **2026-07-06 — Gold + answerability source (measurement fix).** The served CSV had no gold/answerability
  columns (empty-`gold` bug). Gold answer + answerability label (`adherence_score`) now joined from
  RAGBench `delucionqa_questions.jsonl` by question (100% coverage). `build_gold_map.py` + `trace_scorer` join.
- **2026-07-06 — Judge model gemini-2.5-flash → gemini-2.5-pro (measurement fix).** Flash mis-scored
  "answer contains the gold fact" cases as NO_MATCH (e.g. the ABS answer). Pro judge is correct and still
  independent of the gemini-3.5-flash generator. Pro is the locked judge for the pre-registered run.
- **2026-07-06 — N corrected 1826 → 913 (data-artifact fix).** Records CSV duplicated each question ×2;
  effective unique N = 913. Full run dedups to 913.
- **2026-07-06 — Governance-level parameter added to Q6 + Q5 (new experimental axis, PILOT).**
  `GOVRAG_LEVEL` (G0–G4) parameterizes the Q6 answer gate and a Q5 filter toggle (G1). DEFAULT unset =
  G3 = exactly prior behavior (verified). This ADDS an experimental variable (governance spectrum),
  it does NOT tune the STRICT result. Reversible (`.bakL`, patchers `apply_q6_levels.py`/`apply_q5_g1.py`).
  Pilot on 20 Q to see the frontier; production use pending Dr. Xu sign-off (governance semantics).
- **2026-07-09 — N corrected 913 → 912 (data-artifact fix).** Actual unique-question count of the
  records export is 912 ({2:911, 4:1} duplication; one question appears 4× with divergent context,
  first occurrence kept). Frozen benchmark input: `data/delucionqa_records_912.csv`
  (see `Benchmark_Input_Provenance.md`). Change sets 5–6 signed off by Dr. Xu (relayed 2026-07-09);
  full run executed 2026-07-09/10 (RUN 1, results in `6_Results/Full_Benchmark_Run1_Results.md`).
- **2026-07-12 — REPLICATION DESIGN AMENDED (cost-motivated; decided BEFORE runs 2–3 execute).**
  Original commitment: N≥3 full-benchmark repeats on DelucionQA (mean ± sd). Amended to:
  (a) cross-corpus generalization — runs 2–3 on two additional RAGBench subsets selected by
  document-reuse (per discussion with Dr. Wang): **ExpertQA** and **HAGRID**, top-50/60 documents,
  ~100 fully-covered questions each (selection script `ragbench_select_and_prep.py`, deterministic,
  provenance manifest per selection); (b) statistical treatment of RUN 1 via paired bootstrap
  confidence intervals over its 912 records (no additional generation). REASON: two further full
  DelucionQA runs (~$444) exceed the July API spend cap and measure only serve-time variance on one
  corpus; cross-corpus runs test generalization of the frontier shape at ~1/4 the cost. The run-to-run
  variance limitation is disclosed (M4 build nondeterminism already quantified in Sprint 1).
  Communicated to Dr. Xu by email 2026-07-11 with a stated proceed-unless-objection plan; this entry
  precedes any run-2 execution. Measurement infrastructure for runs 2–3: parallel checkpointed scorer
  (`E3_Parallel_Evaluation.py`), B4 run-guard with per-run artifact isolation (`--run-tag`),
  per-run API keys for usage attribution — none alters pipeline or judging logic.
- **2026-07-18 — Selection parameter set K=150 (pre-execution; supersedes the 50/60 estimate).**
  A K-sweep on both corpora (before any generation) showed K=60 leaves the minority stratum too
  thin (ExpertQA 15 answerable; HAGRID 12 unanswerable); K=150 yields ExpertQA 176 q (42 P / 134 N)
  and HAGRID 167 q (141 P / 26 N) at marginal reuse ≈ 1.0 q/doc, the knee of the curve.
  Representativeness table + complementary-strata rationale: `Subset_Selection_Validity.md` §4.
  ExpertQA selection executed 2026-07-18 (deterministic; verified identical across two independent
  executions); NO generation has occurred as of this entry.
- **2026-07-19 — RUN ORDER SWAPPED (HAGRID → run 2, ExpertQA → run 3) + JUNK-DOCUMENT FILTER
  (data-cleaning, evidence-driven, decided before either corpus generated any results).**
  The ExpertQA M1 build stalled deterministically on its first content slice; isolation testing
  reproduced the cause: Google's server returns **504 DEADLINE_EXCEEDED** on the slice opening with
  the corpus's most-reused document — an NCBI "Access Denied" scraping artifact (already identified
  and quantified in Subset_Selection_Validity.md §"junk" before the build). The document is
  machine-unprocessable by the chunking layer itself; retries are futile at temperature 0.
  AMENDMENTS: (a) selection gains a deterministic `--drop-junk` filter (pre-registered error-page
  markers + <40-word stubs), recorded per selection manifest; (b) run order swapped — HAGRID
  (clean wiki-passage text) proceeds first as run 2; ExpertQA retried as run 3 with the filter;
  CovidQA is the documented fallback if ExpertQA remains unbuildable. Rationale: bank a clean
  cross-corpus run before re-attempting the risky corpus. The unprocessable-document incident is
  itself reportable evidence for governance-layer evidence screening. Representativeness tables
  will be recomputed for every filtered selection. Build hardening added the same day
  (`B5_Build_Runner.py`: stall watchdog, retries, stage checkpoints, corpus/key guards) —
  orchestration only; frozen pipeline untouched.
- **2026-07-19 (later) — ROOT CAUSE CORRECTED + M1/M2 MODEL REPOINT (measurement/infrastructure
  fix, approved, before any run-2/3 generation).** Further isolation testing showed the 504
  DEADLINE_EXCEEDED reproduces on HAGRID's clean first slice too and vanishes entirely under
  `gemini-2.5-flash-lite` (4.1 s on the identical call): the cause is a DEGRADED
  `gemini-3-flash-preview` ENDPOINT, not corpus content — the earlier junk-document attribution
  is likely wrong and will be retested; the junk filter is RETAINED as data hygiene (462 stub/error
  documents excluded from HAGRID alone). REPAIRS (third model-line repair of the project, same
  class as the two gemma-404 repointings): M1 + M2 model line → `gemini-2.5-flash-lite`
  (`.bakM` backups); M1 additionally gains a 120 s per-call HTTP timeout and a per-slice progress
  print (observability; no logic or output-content change). DISCLOSURE: run-1's build used the
  preview model, run-2/3 builds use flash-lite — a build-stage infrastructure difference noted in
  all manifests; governance logic, serve models, and judge unchanged.
- **2026-07-19 (evening) — SECOND MODEL WITHDRAWAL SAME DAY + BUILD-CHAIN AUDIT (infrastructure
  fixes, approved, still before any run-2/3 generation).** ~1 hour after `gemini-2.5-flash-lite`
  passed the isolation test (OK 4.1 s), Google withdrew it: 404 "no longer available to new
  users" on the identical call (B5 caught it in 0.3 min, 3 attempts, ~$0). A four-candidate
  probe on the real HAGRID slice: 2.5-flash-lite FAIL(404); **3.1-flash-lite OK 4.4 s / 24
  items**; flash-lite-latest OK 4.6 s (floating alias — rejected for reproducibility);
  2.5-flash OK but 19.7 s and same sunsetting family. REPAIR: M1 + M2 repointed to
  **gemini-3.1-flash-lite** (GA version pin). A full model audit across D/M/Q/E pipelines then
  found (a) the three run-1 hardened build variants (M3.3_HARDENED, M4_PARALLEL, M5_HARDENED)
  present in the Paper2 harness mirror but absent from the repo `experiment\` — copied in
  unmodified except (b) M3.3_HARDENED and M4_PARALLEL carried the degraded
  `gemini-3-flash-preview` — repointed to gemini-3.1-flash-lite (`.bakM` backups). Embedding
  model (gemini-embedding-001) verified live same day via the D pipeline. Serve model
  (gemini-3.5-flash) and LOCKED judge (gemini-2.5-pro) to be probed before generation.
  JUSTIFICATION (for Limitations / audit): because Google deprecated the run-1 build models
  mid-study, run-2/3 indices are built with gemini-3.1-flash-lite (disclosed per-run in the
  manifests); all hypothesis tests are within-run governed-vs-naive comparisons over a shared
  index, so build-model variation across runs affects generalization breadth, not internal
  validity. H1–H4 are serve-time hypotheses; generation and judge models are unchanged across
  runs 1–3. Full note in RESEARCH_LOG.md (same date).
- **2026-07-19 (evening, cont.) — LOCKED JUDGE REPLACED: gemini-2.5-pro → gemini-3.1-pro-preview
  (measurement-instrument repair, approved, decided BEFORE any run-2/3 judging).** The same
  model sweep that removed 2.5-flash-lite also withdrew the LOCKED judge `gemini-2.5-pro`
  (404 "no longer available"). Probe of every pro-tier model visible to the project left two
  viable candidates; **gemini-3.1-pro-preview** chosen over the `gemini-pro-latest` alias
  because a locked judge must have a fixed, citable identity — an alias can drift silently
  mid-study, whereas a pinned model that dies fails loudly and is deviation-logged. Judge
  independence preserved (judge ≠ generation model gemini-3.5-flash). No frozen code involved:
  the judge is a CLI argument; harness defaults (E3_Parallel_Evaluation, B4 next-step hint) and
  the runbook updated. COMPARABILITY REMEDY (approved same day): after run 2 completes, run 1's
  archived 8,208 serve pairs will be RE-JUDGED with gemini-3.1-pro-preview (judge calls only,
  no generation) so all runs share one judge; run 1 will be reported under both judges as a
  judge-robustness check. Within-run governed-vs-naive comparisons — where all hypothesis
  tests live — are unaffected by the judge change in every run.
- **2026-07-19 (night) — STALE-RESUME CONTAMINATION CAUGHT BEFORE SERVING (build-integrity fix;
  no results generated or affected).** First hardened HAGRID build pass: M1/M1.5/M2/M3 produced
  a valid 298-node / 1,143-edge HAGRID graph, but M3.3/M4/M5's crash-resume logic (which keys on
  output-file existence, not corpus identity) silently "resumed" from run-1 DelucionQA partials
  still in the `output\` working slot (3,781-node graph; M4_alignment_results.jsonl dated Jul 5)
  and reported success with zero new work. Detected immediately from the topology mismatch in the
  live B5 logs. REMEDY: stale partials quarantined to `_quarantine\run1_stale_build_partials\`
  (run-1 canonical copies remain in the read-only archive), contaminated `index\hagrid_run2`
  snapshot set aside for deletion, B5 checkpoints for M3.3/M4/M5 reset, stages rerun fresh from
  the valid M3 output. Run-1 artifacts untouched. Root cause noted for the harness backlog:
  B5 should quarantine downstream partials whenever the D5 corpus changes.
- **2026-07-19 (night, cont.) — SERVE-MAP MATCHING MADE BIDIRECTIONAL (measurement-infrastructure
  fix, approved, before any run-2 serving).** The design-A question→chunk map used one-directional
  verbatim containment (chunk ⊆ document), correct for DelucionQA's long manuals but wrong for
  HAGRID's short wiki passages: M1 chunks (median 179, max ~6,000 chars) often span several
  passages (median 653 chars), so 71 of 73 unmatched documents were documents-inside-a-chunk;
  question coverage was 50.3%. FIX in `serve_map_questions_to_chunks.py` (harness, not frozen
  pipeline; `.bak` kept): containment tested in both directions + a windowed-overlap fallback.
  Effect: retrieval scope for a question may include neighboring-passage text sharing a spanning
  chunk — a slight widening (conservative direction; no evidence lost), identical behavior on
  run-1-style corpora where chunks are smaller than documents. Coverage re-verified before the
  smoke batch; preflight re-run.
- **2026-07-19 (night, cont. 2) — Q3 EMPTY-EVIDENCE STATE + B2 RUN-DERIVED QUESTION IDS
  (approved; smoke batch 0 surfaced both; before any completed run-2 serving).** (a) FROZEN-CODE
  fix, Q3 design-A branch: when every chunk mapped to a question yielded ZERO extracted triples
  (24/163 HAGRID questions — sparse wiki passages; impossible on DelucionQA's ~36 chunks/question),
  Q3 raised a fatal debug assertion ("_edge_cid attr wrong?"). Replaced with a defined
  EMPTY-EVIDENCE state: logged, empty evidence subgraph served with the question's real chunk
  text, downstream governance gates decide answer/abstain exactly as in the already-exercised
  zero-anchor path. No gate, threshold, walk, or scoring logic changed; a crash became a
  legitimate governed outcome (`.bakQ3` backup). Empty-evidence frequency will be reported
  per run. (b) HARNESS fix, B2: question ids were stamped with a hardcoded `delucionqa_q` prefix;
  now derived from the records filename (`hagrid_run2_q00003`) so run-2/3 artifacts carry
  truthful provenance ids. Gold joins are by question text; nothing keys on the prefix.
- **2026-07-19 (night, cont. 3) — E3P JOIN BUG FROM THE ID-PREFIX FIX; FIRST RUN-2 SCORING
  INVALIDATED AND RE-SCORED (measurement fix, same evening, before any results reported).**
  The approved B2 id-prefix change (run-derived question ids) broke an undetected twin
  assumption in E3_Parallel_Evaluation.py, which RECONSTRUCTED ids with a hardcoded
  "delucionqa_q%05d" to join governed answers: every governed lookup missed, empty answers
  scored as refusals, and the first run-2 summary wrongly reported 100% refusal for ALL
  governed configs including G1 (actual G1 serve data: 127/163 answered). Detected immediately
  by cross-checking the summary against the serve archives. FIX: join by the numeric index
  parsed from the record_id tail (prefix-agnostic); invalid outputs retained as *.bad_join
  evidence; full clean re-score executed with the same locked judge. Also same evening:
  E3P judge client gained the same 120 s per-call HTTP timeout as M1 (a hung judge socket
  had frozen the final pair indefinitely; approved). LESSON RECORDED: any id-format change
  must be grepped across the entire harness before serving.
- **2026-07-20 — RUN-1 RE-JUDGE COMPLETE (dual-judge robustness; approved 2026-07-19).**
  All 8,208 Run-1 pairs re-judged with gemini-3.1-pro-preview (the successor to the
  withdrawn locked judge). Original judging preserved bit-identical (post-run SHA
  verification 47/47); re-judge sealed as append-only archive `results/run1_rejudge/`
  (own SHA256SUMS). Agreement: κ=0.681 (substantial), 84.1% on judged pairs; successor
  systematically more lenient (MATCH .506→.578), concentrated on verbose answers
  (G0/G1). DISCLOSURE: H1's pre-registered ±.05 parity bound is judge-sensitive on
  Run 1 (Δ=.034 original vs Δ=.080 successor); the paper reports both judges, treats
  frontier structure (judge-invariant) and accuracy levels (judge-dependent) separately,
  and uses the single consistent judge for all cross-run comparisons.

### 4.2 Corpus selection and its validity (verbatim)

### Subset Selection Validity — Runs 2–3 (ExpertQA, HAGRID)
*Updated 2026-07-20: executed Run-3 (drop-junk, 150 q) representativeness table added.*
*Updated 2026-07-19: HAGRID K=150 representativeness table added (run-order swap: HAGRID is now Run 2).*
*Methodological justification for reduced-corpus evaluation. Drafted 2026-07-18, before Run-2
execution. Source for the paper's Methods (corpus construction) and Limitations sections.
Pairs with: Analysis_Plan_and_Stopping_Rule.md (deviation entry 2026-07-12),
ragbench_select_and_prep.py (the deterministic selection rule), git commit 54ef322.*

#### 1. Why not the full datasets (feasibility, quantified)
Generation and judging cost scale with question count; the **build** cost scales with corpus
size. Calibration from Run 1 (DelucionQA): 930-document build = $498.12; 912-question
serve+judge = $221.96. Extrapolation: ExpertQA full (7,403 documents, 2,027 unique questions)
≈ $3.5–4K build + ~$490 evaluation; HAGRID full (6,965 documents, 2,638 questions) similar.
Full-corpus replication across both datasets (~$8–10K) is infeasible for this project; the
reduced-corpus design reduces each run to ~$90–120 while preserving what runs 2–3 exist to
test (§3).

#### 2. Why the selection is not cherry-picking (four tests)
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

#### 2b. The junk-document filter is data cleaning, not selection (run 3, `--drop-junk`)

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

#### 3. Claim scoping (what runs 2–3 do and do not assert)
Run 1 evaluated the **complete** DelucionQA benchmark (all 912 unique questions); the
paper's headline quantitative claims rest on that full-coverage run. Runs 2–3 are
**cross-corpus generalization probes**: they test whether the *qualitative shape* of the
governance frontier — the monotone coverage/abstention dial, the faithfulness ceiling, the
localization of coverage cost at the authorization step — reproduces on different corpora,
including a far richer unanswerable stratum (ExpertQA: 55% unanswerable vs. DelucionQA's 7%).
They are not population estimates of full-ExpertQA/HAGRID performance, and the paper does
not present them as such. Pattern replication imposes weaker representativeness demands than
parameter estimation; the claim is scoped to "questions answerable from the selected corpus."

#### 4. Representativeness characterization (selection vs. population)
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

#### 5. Pre-committed text for the paper

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

#### 6. Reviewer-preemption note
If asked "why not random question sampling instead?": random questions reference documents
outside any affordable build — a question is only evaluable if its documents are built. The
unit of affordability is the document set; selecting documents (and taking all their
questions) is the only sampling scheme compatible with a bounded build, and reuse-maximizing
selection is the variant that maximizes evidence per dollar without reference to outcomes.

### 4.3 Metric definitions (verbatim)

### GovernRAG / Paper 2 — Evaluation Metrics Reference
*Single source of truth for every metric produced by E3_Unified_Evaluation.py (and B3_spectrum_axes.py).
Definitions, formulas, contextual meaning, and caveats. Use for the manuscript's Evaluation section.*

Notation: for a set of evaluation records, each record is scored under one **configuration** (a governance
setting) and belongs to one **answerability stratum**. Counts below are per-configuration unless noted.

---

#### 1. What is being evaluated — the configurations (governance spectrum + axes)

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

#### 2. Strata — answerability

Every record is labelled **answerable** or **unanswerable** from the gold benchmark (DelucionQA gold
`adherence_score`: answerable = the gold answer is supported by the provided context; unanswerable = it is not).
This is the DelucionQA generalization of E2's Positive/Negative (P/N) conditions.
- **Answerable (P):** correct behavior is to answer correctly.
- **Unanswerable (N):** correct behavior is to abstain (refuse).

Stratifying prevents a system from looking good by answering everything (inflating accuracy) or refusing
everything (inflating safety). Accuracy is judged on the answerable stratum; abstention quality on both.

---

#### 3. Per-answer judgments (LLM-as-judge)

##### 3.1 Verdict — MATCH / NO_MATCH / SAFE_SILENCE
The judge (a stable, independent LLM) compares the system answer to the gold answer after stripping
provenance markers (`[CHNK_...]`, `[RESIDUAL_...]`).
- **MATCH** — the answer contains the gold fact.
- **NO_MATCH** — the answer is factually wrong or hallucinated.
- **SAFE_SILENCE** — the answer explicitly refuses / abstains (e.g. "insufficient evidence", BLOCKED).
Meaning: separates *correct*, *wrong*, and *declined* — you cannot reduce governance quality to a single
right/wrong bit, because a refusal is neither correct nor a hallucination.

##### 3.2 Condition grade (E2 semantics, retained)
Combines verdict with the stratum:
- Answerable: `SUCCESS` if MATCH, else `FAILURE_<verdict>`.
- Unanswerable: `SUCCESS_boundary` if SAFE_SILENCE; `FAILURE_leakage` if MATCH (answered something it
  shouldn't have — parametric leakage / hallucination); `FAILURE_badoutput` otherwise.
Meaning: the human-readable per-record verdict; the origin of the governance-accuracy metric (Sec 5.2).

##### 3.3 Faithfulness — TRACe adherence
**TRACe** is the RAGBench evaluation framework (Relevance, Utilization, Completeness, **Adherence**).
We report **Adherence**: the fraction of the answer's claims that are grounded in the admitted context
(LLM-judged, per answered tuple). "Faithfulness" and "TRACe adherence" are the same column here.
- Range 0-1; 1.0 = every claim supported by context; low = ungrounded / hallucinated.
Caveat: computing it needs a second judge call per answer, hence the `--no-trace` fast-screen flag that
skips it. It is distinct from E2's per-record "verdict trace" printout (`--record N`).

---

#### 4. Coverage and accuracy

Let `total` = records scored under a config; `answered` = records not refused;
`answerable_total` = answerable records; `adh_match` = answerable records judged MATCH.

- **Coverage** = answered / total. The answer rate; falls as governance tightens. Judge-independent.
- **Accuracy (adherent stratum)**, written `acc(adh)` = adh_match / answerable_total. Of the questions that
  *should* be answerable, the fraction answered correctly (a refused answerable counts against it).
- **Risk-coverage frontier** = the curve of accuracy (or risk = 1-accuracy) vs coverage across G0..G4.
  The core artifact: it shows how much answer coverage is traded for governance strictness. Prior fail-closed
  systems report a single point on this curve; we report the whole curve.

---

#### 5. Governance metric triad (abstention quality)

Refusals are not uniformly good or bad; the triad separates them by stratum.

- **Refusal rate** = refused / total. How often the system declines (any reason). = 1 - coverage.
- **Correct-refusal rate** = (SAFE_SILENCE on unanswerable) / unanswerable_total. Of the questions that
  *should* be refused, the fraction correctly refused. Higher = better boundary maintenance.
- **False-rejection rate** = (refused on answerable) / answerable_total. Of the answerable questions, the
  fraction wrongly refused. Higher = more usable answers thrown away. This is the cost side of strictness,
  and the metric CogniGraph is nearly alone in reporting (its "49% false-rejection reduction").
Meaning: a governance layer is good if it raises correct-refusal without raising false-rejection.

---

#### 6. Comparability metrics (vs CogniGraph)

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

#### 7. Evidence-scoping metrics (what governance removed)

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

#### 8. Model protocol (validity guards)

- **Generation parity.** The G0 naive baseline uses the *same* generation model as the governed answer (Q6),
  so a naive-vs-governed difference reflects the *pipeline*, not a model swap. (E2's use of a different
  baseline model, gemma-3-4b-it, violated this; E3 fixes it.)
- **Judge independence.** The evaluation judge (default gemini-2.5-pro) differs from the generation model,
  so the judge is not grading its own outputs. A *stable* (non-preview) judge is used for reproducibility.
- **Determinism.** Generation and judging run at temperature 0; residual variation at small N is treated as
  noise (differences below ~1-2 records at N=20 are not interpreted).

---

#### 9. One-line reading guide
Coverage + acc(adh) + the frontier = the core trade-off. The triad = abstention quality (correct- vs
false-refusal). token-F1 / GA / Constrained-F1 = comparability to CogniGraph. Evidence-reduction + GR =
the mechanism (what governance removed). Faithfulness = grounding of what was answered.

### 4.4 Evidence scoping (design-A) finding (verbatim)

### Results — Ontology Axes on DelucionQA: Confirmed Diagnosis
*Paper 2, Results/Discussion. Updated 2026-07-07 with the confirmed empirical picture from the
20-record pilot + corpus-wide feature check. Pairs with Contribution_Positioning_Note.md and the
harness artifacts evidence_reduction.csv / affinity_tau_sweep.csv.*

#### Target claim (approved wording) — a HYPOTHESIS, to be established on a corpus that can support it
> Reference-ontology conformance (BIZBOK `alignment_status`) and viewpoint-domain affinity (`wa_score`)
> operate as **evidence-scoping constraints**: they measurably reduce the admitted evidence set
> (mean *N* triplets/chunks dropped per record) without a detectable change in end-task answer accuracy
> or faithfulness. This suggests these ontology-derived signals primarily shape *which evidence is
> considered* rather than *what is ultimately answered*, with end-task effects expected under domain
> heterogeneity or adversarial evidence.

**Status: NOT established on DelucionQA.** The pilot shows *why* it cannot be tested here (below). Report
this as the hypothesis motivating the multi-domain / adversarial evaluation, not as a DelucionQA result.

#### What DelucionQA actually shows (confirmed)
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

#### Root cause (single structural fact)
DelucionQA is **single-domain and triplet-sparse**. Domain affinity requires multiple domains to be
non-trivial (single domain -> affinity ≡ 1.0); ontology conformance requires a populated triplet channel
(sparse retrieval -> nothing to filter). Neither axis is *wrong*; the corpus cannot exercise either.

#### What to report / NOT report on this corpus
- **Report:** the chunk-authorization cliff (chkKept 32.9 -> 3.55) as the mechanism of the risk-coverage
  frontier; and the *negative characterization*: on single-domain, triplet-sparse data the two ontology-
  derived axes are un-exercisable (Axis A starved, Axis B degenerate).
- **Do NOT report:** an affinity τ choice or an affinity sensitivity curve for DelucionQA — there is no
  variance to threshold. Stating "we selected τ = X" here would be meaningless (or worse, look arbitrary).

#### Caveats / framing (state them plainly)
- Frame Axis A's null as "no *detectable* end-task change at this power on a triplet-sparse corpus," not
  "conformance does not matter." Frame Axis B as "feature has zero variance on single-domain data," not
  "affinity does not matter."
- The generalization ("effects emerge under heterogeneity/adversarial evidence") is an explicit
  **hypothesis / future work**, supported by the diagnosis, not a demonstrated result.

#### Why this is a contribution, not a failure
The instrumentation did not merely produce a null — it *explained* it: feature degeneracy (Axis B) and
triplet starvation (Axis A), both traceable to corpus composition. That is a precise, falsifiable account of
where these ontology-derived signals can and cannot pay off, and it is the concrete, evidence-backed
justification for a multi-domain, triplet-rich, adversarial corpus before the pre-registered 913 run.

#### Verification trail
- `results/evidence_reduction.csv` — predTrp 0, ontTrp 0 (except OntConf 0.75), affChk 0; chkKept 32.9->3.55.
- `results/affinity_tau_sweep.csv` — global/survivor wa_score ≡ 1.000; affChk 0 at all τ.
- `output/M1_Governed_Chunks.csv` — n=5037; viewpoint_domain = {Customer Support: 5037}; wa_values = {1.0}.

---

#### Update — bidirectional Q3 fix does not wake the axes (Pro judge, N=20, 2026-07-07)
The Q3 bidirectional-walk fix raised triplet yield 0.75 -> 2.70/record and roughly doubled governed
coverage (G2 20% -> 40%, accuracy 6% -> 33% on the Pro judge). It did NOT make the ontology axes
active: ontTrp = 0.05 (~1 triplet dropped total), affChk = 0. Under the Pro judge all axis variants
land at/below plain G2 (33%): OntNU/OntConf/OntNU+Aff = 28%, Aff = 22%. Because G2+Aff drops nothing
yet scores differently from G2, the sub-G2 differences are confirmed judge/generation noise at N=20.
Reading: more triplets != governance signal. Axis A needs ontology-conformance VARIATION (Unmapped/
Adaptive triplets in scope); Axis B needs MULTIPLE domains. Both remain corpus requirements, now
confirmed to persist after the retrieval fix. Faithfulness is saturated at 1.000 throughout.

---

## 5. Runs and results

### 5.1 Run 1 — DelucionQA, full benchmark (results memo, verbatim)

### Full Benchmark — Run 1 Results (N=912 DelucionQA, pre-registered)

*Task #33, run 1 of the replication plan. Generation 2026-07-09 (37 batches, K=25, ~8.6 h,
zero failures); scoring 2026-07-10 (E3, judge gemini-2.5-pro, sequential, ~24 h under API
latency variance). QA: 8,208/8,208 (record,config) pairs scored, 0 ERROR verdicts, strata
848 answerable / 64 unanswerable. Artifacts: results\E3_run1_master_eval_log.csv,
results\E3_run1_frontier_summary.csv, results\full_run\timing_log.csv.*

#### Frontier (headline table)

| Config | Coverage | Acc (adh) | Faith | corrRef | falseRej | tokF1 | C-F1 | Cited |
|---|---|---|---|---|---|---|---|---|
| G0 Naive | 100% | 67.8% | 0.99 | 32.8% | 2.7% | 0.57 | 0.61 | 0% |
| G1 Cited | 93% | 64.4% | 0.98 | 42.2% | 5.0% | 0.58 | 0.60 | 99.9% |
| G2 Grounded | 44% | 18.2% | 0.99 | 78.1% | 54.5% | 0.42 | 0.32 | 98.8% |
| G3 Strict | 38% | 14.7% | 0.99 | 78.1% | 60.7% | 0.41 | 0.30 | 97.7% |
| G4 Corrob | 35% | 14.3% | 0.98 | 82.8% | 64.0% | 0.40 | 0.30 | 98.1% |
| G2+OntNU | 45% | 19.6% | 0.99 | 75.0% | 54.2% | 0.42 | 0.33 | 97.8% |
| G2+OntConf | 44% | 18.6% | 0.99 | 75.0% | 54.6% | 0.42 | 0.32 | 98.0% |
| G2+Aff | 44% | 18.0% | 0.98 | 76.6% | 54.6% | 0.42 | 0.32 | 98.5% |
| G2+OntNU+Aff | 44% | 19.1% | 0.99 | 76.6% | 54.6% | 0.42 | 0.33 | 98.3% |

#### Pre-registered hypothesis verdicts (report-regardless)

**H1 — quality parity on the answerable stratum (bound ±0.05): SUPPORTED at G1 only.**
G1 vs naive: accuracy −3.4 pp, token-F1 +0.005 — inside the bound. G2 through G4 and all
axis combos: −48 to −53 pp accuracy — far outside. Parity survives citation-gating (G1);
it does not survive predicate authorization (G2+).

**H2 — faithfulness superiority: NOT SUPPORTED (ceiling effect).** TRACe adherence is
0.98–0.99 for every config including naive; hallucination-on-answered is 1.2–2.2%
everywhere. The N=20 pilot's "no headroom" finding replicates exactly at N=912: on
answerable DelucionQA, faithfulness is saturated and governance cannot raise it.

**H3 — selective abstention: PARTIALLY SUPPORTED, with the pre-registered coverage-cost
finding triggered.** Correct-refusal on the 64 unanswerable questions rises monotonically
33% (naive) → 42% (G1) → 75–83% (G2+), and parametric leakage (asserting an answer that
matches RAGBench's hallucinated reference) falls 17.2% → 12.5% → 4.7–7.8%. But
false-rejection on answerable questions at G2+ is 54–64% — the high-wrong-refusal clause
applies, so the G2+ result is reported as the coverage cost of authorization. G1 achieves
+9.4 pp correct-refusal at only 5% false-rejection.

**H4 — auditability: SUPPORTED.** 97.7–99.9% of answered governed outputs carry
source-resolvable [CHNK_*]/[RESIDUAL_*] citations (vs 0% naive), measured on full answers.

#### Findings for the paper

1. **The governance spectrum is a coverage/authorization dial at constant faithfulness**
   (pilot finding confirmed at 45× scale). Coverage 100→35% monotone across G0→G4;
   faithfulness flat at ~0.99.
2. **The cost is localized to authorization.** The cliff is G1→G2 (93%→44% coverage,
   64%→18% accuracy) — the D5 predicate filter — not the citation gate (G0→G1 is nearly
   free) and not the symbolic-triplet requirement (G2→G3 is small).
3. **G1_Cited is the operating point for parity claims:** quality parity + ~100%
   provenance + improved abstention at 5% recall loss.
4. **The ontology/affinity axes scope evidence without changing answers (dissociation
   confirmed):** G2-family drops ~35.9 chunks/record (keeping ~3.4 chunks + ~6.5 triplets)
   while accuracy/faithfulness stay within ~1 pp of G2 — governance restricts the evidence
   set, not answer quality on what it answers.
5. **Selectivity, not silence:** abstention quality (correct-refusal up, leakage down)
   improves monotonically with strictness — the reference monitor is doing its job; it is
   simply priced in coverage.

#### Caveats / open items
- Single run (run 1). Replication per the (possibly amended) N≥3 / bootstrap plan pending.
- 64-question unanswerable stratum is thin; corrRef percentages move ±1.6 pp per question.
- Faithfulness ceiling may partly be TRACe-adherence leniency on short cited answers
  (pilot caveat stands; a discriminant check is future work).
- Master-log `answer` column truncates at 200 chars — citation stats must be computed from
  the _spec_*.jsonl caches (as done here), not the master log.

### 5.2 Run 1 manifest (verbatim)

```yaml
# Run manifest — pre-registered full benchmark, RUN 1
# Format: Model_and_Reproducibility_Protocol.md §4. Assembled 2026-07-11 from run artifacts,
# git, AI Studio usage/spend, and environment capture. Gaps stated explicitly at bottom.

run_id: delucionqa_full_run1_20260709
git_commit: 51a7bdd            # tag: run1-complete, branch paper2-spectrum, github.com/gunavivek/GovernRAG1
git_note: committed 2026-07-11 immediately post-run; file contents identical to run-time state
          (run executed from the working tree later captured by this commit)

corpus:
  name: RAGBench/DelucionQA (deduplicated benchmark input)
  records: 912                 # 848 answerable / 64 unanswerable
  file: data/delucionqa_records_912.csv
  md5: 59527382dc15a0aa7361a9a8b45ea6c3
  gold_map: results/gold_map.json (md5 2f058303207fc267717c68de5efd912a)
  provenance: Paper2/2_Design/Benchmark_Input_Provenance.md

phase: serve + eval            # build phase was 2026-07-03..05 (separate; $498.12; embeddings 37K reqs Jul 5)

pipeline_models:               # single fixed pipeline, unchanged across all records/configs
  generation_q6_and_naive:
    provider: google
    model: gemini-3.5-flash    # alias as exposed by AI Studio; versioned suffix not shown in UI
    api_dates: 2026-07-09
  extraction_q2:
    provider: google
    model: gemini-2.5-flash-lite
    api_dates: 2026-07-09
  sdk: google-genai==1.56.0 (httpx 0.28.1)

judge:                         # independent of generation models (protocol §2)
  provider: google
  model: gemini-2.5-pro
  api_dates: 2026-07-09..10
  scorer: E3_Unified_Evaluation.py (sequential)
  prompt_hashes:
    correctness_md5: ab4e7d86f6960353468f254efdec9585   # trace_scorer.CORRECT_PROMPT
    trace_md5: 514c8783e89dc9f12060377decf7ea18          # trace_scorer.JUDGE_PROMPT

decoding:
  temperature: 0.0             # Q6 (frozen code line 111), naive baseline, both judge calls
  top_p: provider default (not set)
  max_tokens: provider default (not set)
  seed: not supported/not set

prompts: frozen in code at git tag run1-complete; no prompt edits between pilot validation and run

configs: 9 (G0_Naive, G1_Cited, G2_Grounded, G3_Strict, G4_Corrob, G2+OntNU, G2+OntConf,
         G2+Aff, G2+OntNU+Aff); SWEEP_TAU=0.35 (default; env var unset)

execution:
  driver: B4_Batch_Runner.py --records data/delucionqa_records_912.csv --k 25 --run-e3
  batches: 37 x K=25 (last 12), all completed, zero failed stages (results/full_run/timing_log.csv)
  generation_window: 2026-07-09 ~08:00 -> 18:39 CT (~8.6 h; 19.1 +/- 1.9 min/batch)
  eval_window: 2026-07-09 ~19:10 CT -> 2026-07-10 21:19 CT (sequential E3; pace 40 s/record
               daytime, ~150 s/record overnight under provider-side latency variance)
  api_reliability: ~19K requests, 100% success rate, 1x 503 total (AI Studio overview)

repeats: run 1 of N>=3 (replication design under advisor review; see Analysis_Plan deviation policy)

cost:                          # AI Studio Spend, daily (PDT attribution), exact
  generation_day_usd: 121.39   # Jul 9
  scoring_day_usd: 100.57      # Jul 10
  run_total_usd: 221.96
  per_question_usd: 0.243      # full 9-config frontier / 912 questions
  context: build phase (Jul 3-5) $498.12; pilot/diagnostics (Jul 6-7) $23.07; Jul 8 shows $0.00
           despite the 20-rec pilot (likely attribution lag; immaterial)
  monthly_cap_note: $743.14 / $999.00 cap as of Jul 11 -> two further full runs (~$444) exceed
           the July cap; raise cap or schedule run 3 after Aug 1 (PST reset)

latency:
  per_question_serve_amortized_s: ~34      # 8.6 h / 912 (all 9 configs' generation included)
  naive_per_question: exact per-record latency_s + token usage in results/serve_results.jsonl
  detail: results/full_run/timing_log.csv (per stage, per config, per batch)

peak_ram_mb: NOT INSTRUMENTED for serve/eval (gap; build-phase stats in runs/B1_*/ manifest)

environment:
  host: Windows 11 Home 10.0.26200, Intel64 Family 6 Model 140 (Tiger Lake), 16,150 MB RAM
  python: 3.11.9 (venv)
  key_libs: {networkx: 3.6.1, numpy: 2.4.0, pandas: 2.3.3, matplotlib: 3.10.8}
  full_freeze: run1_pip_freeze.txt (UTF-16LE encoding, PowerShell redirect)

outputs:
  per_pair_log: E3_run1_master_eval_log.csv (8,208 rows; QA: 0 ERROR verdicts)
  summary: E3_run1_frontier_summary.csv
  analysis: Paper2/6_Results/Full_Benchmark_Run1_Results.md (H1-H4 verdicts)

known_gaps:
  - exact model version strings: AI Studio exposes aliases only (as confirmed available);
    record alias + api_date per protocol fallback
  - serve/eval peak RAM not captured (instrument before run 2 if desired -- code change,
    requires approval)
  - gov_ratio not propagated by Q6 caches (risk-coverage proxy falls back to per-record
    kept-triplet counts from _spec_*_red.jsonl, as pre-registered)
```

### 5.3 Runs 2–3 manifests (verbatim)

```yaml
# Run 2 Manifest — HAGRID (GovernRAG Paper 2)
run_id: run2_hagrid
executed: 2026-07-19 (build 16:35–17:49 CDT after model migration; serve 17:5x–19:0x; judging 19:1x–21:0x incl. two invalidated passes)
status: COMPLETE_SEALED   # git tag run2-complete

corpus:
  source: RAGBench HAGRID (train+validation+test, 2,638 unique questions)
  selection: K=150 greedy full-cover by document reuse, --drop-junk (462 junk docs excluded)
  questions: 163  (answerable 137 / unanswerable 26)
  files:
    selection_manifest: data/hagrid_run2_selection.json   # sha256 b154d430dfd8609b…
    records: data/hagrid_run2_records.csv                 # sha256 6a64727481f5a7d0…
  representativeness: Subset_Selection_Validity.md §4 (mirrors population: 84.0% vs 85.5% answerable)

models:
  build_m1_m2_m33_m4: gemini-3.1-flash-lite   # repointed 2026-07-19 after Google withdrew
                                              # gemini-2.5-flash-lite and degraded 3-flash-preview (deviation log)
  embeddings: gemini-embedding-001
  serve_generation_and_naive: gemini-3.5-flash
  judge: gemini-3.1-pro-preview               # locked successor judge; replaced withdrawn gemini-2.5-pro (deviation log)

infrastructure:
  build: B5_Build_Runner (guards+watchdog); STALE-RESUME INCIDENT: first pass resumed run-1
    partials for M3.3/M4/M5 — detected from topology, quarantined, stages rebuilt fresh
    (deviation log 2026-07-19 night). Final build: M1 3.8 min, chain total ~25 min.
  index_snapshot: index/hagrid_run2/ (851 nodes / 5,815 edges; build_manifest.json; read-only)
  serve: B4 run-tag run2_hagrid, 7 batches, K=25; serve map = bidirectional containment fix
    (coverage 50.3%→100%, deviation-logged pre-serving); Q3 empty-evidence state (24/163 questions)
  scoring: E3_Parallel_Evaluation, 1,467 pairs, 0 errors (1,120 SAFE_SILENCE / 294 MATCH / 53 NO_MATCH)
  invalidated_passes: 2 scoring passes retained as *.bad_join evidence (E3P id-join bug from the
    B2 id-prefix fix; fixed same evening; deviation log "night, cont. 3")

cost_and_attribution:
  api_project: conceptual-GraphRAG (key "graphRAG", .env prefix AIzaSyDhK8 — CONFIRMED 2026-07-19)
  note: key named govrag-run2-expertqa (Personal Project) carried only morning legacy-tree activity
  run2_marginal_cost_usd: ~13-15   # Spend page Jul 19 bar at 20:47 CDT; MTD $41.01
  evidence: 6_Results/Run2_Evidence/ (8 screenshots + Run2_API_Usage_Evidence_2026-07-19.md)

archives:
  results: results/run2_hagrid/ (23 files + SHA256SUMS.txt, read-only)
  git: commits f6af3cc…ebc3a6e…39f4a0e…b9e9d94, tag run2-complete (github.com/gunavivek/GovernRAG1)

headline_results:  # judge gemini-3.1-pro-preview
  frontier: G1 cov 78% acc 72% faith 1.00 falseRej 18% | G2 cov 17% | G3/G4/Aff cov 0%
  reading: CLIFF — out-of-ontology corpus (25.8% M4-aligned concepts); Analysis_CrossRun.md
```

```yaml
# Run 3 Manifest — ExpertQA (GovernRAG Paper 2)
run_id: run3_expertqa
executed: 2026-07-19 21:0x CDT → 2026-07-20 00:4x CDT (selection→build→serve→judging, single evening)
status: COMPLETE_SEALED   # git tag run3-complete

corpus:
  source: RAGBench ExpertQA (train+validation+test, 2,027 unique questions)
  selection: K=150 greedy full-cover by document reuse, --drop-junk (80 junk docs excluded)
  questions: 150  (answerable 45 / unanswerable 105 — the N-heavy abstention probe)
  files:
    selection_manifest: data/expertqa_run3_selection.json  # sha256 e09ae6ecfeff6125…
    records: data/expertqa_run3_records.csv                # sha256 20d68efac13f5c87…
  junk_filter_justification: Subset_Selection_Validity.md §2b (content-only, pre-registered,
    uniform, hash-disclosed, conservative direction); representativeness refresh pending (7B-3)

models:
  build: gemini-3.1-flash-lite (M1/M2/M3.3/M4) + gemini-embedding-001 (M5)
  serve_generation_and_naive: gemini-3.5-flash
  judge: gemini-3.1-pro-preview

infrastructure:
  build: A1_RAGBench_D0_M0_Runner expertqa_run3 (D1 3.8 s; D0 42 s; M0 99.5 min; total 100.28 min)
    + B1 snapshot; working slot pre-cleaned (_quarantine/run2_hagrid_build_partials — the
    stale-resume lesson applied proactively). M4: 332 aligned, 366 low-conf (47.2% aligned share).
  index_snapshot: index/expertqa_run3/ (1,256 nodes / 7,066 edges; read-only)
  serve: B4 run-tag run3_expertqa, 6 batches, K=25 (~9-11 min/batch; long-form corpus)
  scoring: E3_Parallel_Evaluation, 1,350 pairs, 0 errors (1,018 SAFE_SILENCE / 208 MATCH / 124 NO_MATCH)

cost_and_attribution:
  api_project: conceptual-GraphRAG (same key as run 2)
  run3_block_cost_usd: ~30   # MTD $41.01 (19th 20:47) → $71.23 (20th 00:46); includes run-2's
                             # final re-scoring passes in the same window — boundary disclosed
  evidence: 6_Results/Run3_Evidence/ (3 screenshots + Run3_API_Usage_Evidence_2026-07-20.md)

archives:
  results: results/run3_expertqa/ (SHA256SUMS.txt, read-only)
  git: commits 3e03097…2ef21c5, tag run3-complete

headline_results:  # judge gemini-3.1-pro-preview
  frontier: G1 cov 59% | G2-tier BAND cov 33% with corrRef 75% vs naive 44% | G3/G4/Aff cov 0%
  notable: first config family where governance beats naive on GA (65-66% vs 55%) — N-heavy corpus;
    refuse-all GA=70% caveat applies; naive faithfulness 0.99 (first sub-ceiling observation)
  reading: BAND — partially-aligned corpus (47.2%); Analysis_CrossRun.md
```

### 5.4–5.8 Cross-run analysis (verbatim, v4 — frontier, H1–H4, judge robustness, moderator, bootstrap)

### Cross-Run Analysis — Runs 1–3 (DRAFT v1, 2026-07-20)

*v4 (2026-07-20): Run-1 paired bootstrap CIs added (§8).*
*v3 (2026-07-20): H4 complete for runs 2–3 (100.0%/100.0%).*
*v2 (2026-07-20 midday): Run-1 re-judge complete; judge-agreement section added; H1 row revised.*
*Sources: sealed archives `results/run1_delucionqa/` (tag `run1-complete`), `results/run2_hagrid/`
(`run2-complete`), `results/run3_expertqa/` (`run3-complete`). Every number below traces to an
`E3_*_frontier_summary.csv` in a hashed archive or to the sealed index snapshots.
PENDING: bootstrap CIs for runs 2–3 (probe-N; wide intervals expected).*

#### 1. The three corpora

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

#### 2. Three-corpus governance frontier (key configs)

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

#### 3. Hypothesis verdicts per corpus

| | DelucionQA | HAGRID | ExpertQA | Overall |
|---|---|---|---|---|
| **H1 quality parity @ G1** (±0.05 bound, answered-stratum accuracy) | **Judge-sensitive**: supported under original locked judge (Δ=.034); Δ=.080 under successor judge | Not supported (Δ=.138) | Not supported (Δ=.133) | Near-parity only in-ontology, within a judge-dependent 3–8-pt band; off-ontology the G1 cost is real (~13 pts) |
| **H2 faithfulness superiority** | Refuted (tie at ceiling: .98 vs .99) | Refuted (tie: 1.00 vs 1.00) | Refuted (tie: 1.00 vs .99) | **Consistently refuted** — gold-context benchmarks leave no hallucination headroom; contribution reframed (see §5) |
| **H3 selective abstention** | Supported w/ coverage cost (corrRef 33→83%, falseRej ≤64%) | Partial — cost extreme (falseRej 85–100% at G2+) | **Strongest support** (corrRef 75% vs naive 44%; GA 65% vs 55%) | Monotone dial replicates on all three; the *price* varies with ontology fit |
| **H4 auditability** | Supported (97.7–99.9% resolvable citations) | **Supported (100.0%**, 206/206 answers cited) | **Supported (100.0%**, 238/238 answers cited) | The one hypothesis with an unqualified cross-corpus verdict: full provenance + complete decision logs in every run |

Notable regularity: **correct-refusal at the G2 tier is ~75–78% on all three corpora** while
its cost (false rejection) varies 51→85% — the gate's *benefit* is stable, its *price* is
corpus-dependent.

#### 4. Exploratory finding: ontology coverage moderates the frontier shape

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

#### 5. Contribution framing (post-evidence, for the manuscript)
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

#### 6. Caveats carried into the paper
- Run-1 numbers above were judged by gemini-2.5-pro (withdrawn by Google 2026-07-19);
  runs 2–3 by gemini-3.1-pro-preview. The Run-1 re-judge under the new judge (in progress)
  provides the judge-agreement analysis; all cross-run comparisons will be restated under
  the single consistent judge, with the original preserved.
- accuracy-on-answered is conditional on each config's own answered subset (selection
  effects at low coverage: G2+ accuracies describe few, hard-filtered answers).
- Build-model difference run 1 vs 2–3 (forced deprecations, deviation-logged): affects
  generalization breadth, not within-run validity.
- Runs 2–3 are reduced-corpus probes (anti-cherry-picking defense: Subset_Selection_Validity.md).


#### 7. Judge robustness — Run-1 dual-judge analysis (7A-2, complete)

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


#### 8. Statistical inference — Run-1 paired bootstrap (7A-4, B=10,000, seed 20260720)

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

### 5.9 Worked examples
Eleven verbatim per-level walkthroughs (staircase, reshaping, false-rejection, non-monotone; one modal example per corpus): `Supplement_Governance_Dial_Examples` (HTML/PDF), record-id-cited to the sealed archives.

### 5.10 Headline figure
`Frontier_ThreeCorpora.png` — coverage and correct-refusal across G0–G4 for the three corpora, consistent judge.


---

## 6. Discussion

### 6.1 What governance costs, and what it buys
The dial's benefit is remarkably stable: at the grounding tier, correct refusal of
unanswerable questions reaches 75–78% on every corpus — in-domain manuals, open-domain
wiki, long-form expert prose alike — against 41–44% for the ungoverned baseline. Its price
is not stable, and that is the finding: false rejection of answerable questions ranges from
51% (in-ontology) to 85% (out-of-ontology), and coverage above G1 ranges from a usable 44%
to zero. Governance is a dial whose benefit is architectural and whose cost is a property
of the corpus–ontology relationship. On the abstention-heavy corpus (ExpertQA, 70%
unanswerable) the governed configuration outscores the ungoverned baseline on overall grade
(65% vs 55%) — with the disclosed caveat that refuse-everything attains 70% on that stratum
mix by construction, so the claim rests on the correct-refusal/false-rejection tradeoff
(75% vs 44% correct refusal at a 51% coverage price), not on the grade alone.

### 6.2 The slope/band/cliff taxonomy and the fit variable
Three corpora produced three frontier shapes, ordered exactly by M4's aligned-concept share
(98.2% → slope; 47.2% → band; 25.8% → cliff). The mechanism is legible: authorization
derives from the manifest's domain policy; where the ontology cannot name a corpus's
concepts, authorized-predicate sets thin out and the gates refuse. Deployment guidance
follows directly: **measure ontology–corpus fit (an M4 by-product, obtainable before any
serving spend) and choose the governance tier accordingly** — G1 everywhere;
G2+ only where fit is high or where the workload is abstention-heavy. This relationship was
identified post hoc across three corpora and is presented as exploratory; a pre-registered
confirmatory run on a strongly in-ontology corpus (FinQA/CUAD) is the designed follow-up.

### 6.3 The faithfulness ceiling, honestly
With gold context supplied, both governed and ungoverned answers are essentially fully
grounded (faithfulness ≥ 0.98 in every configuration and corpus). Governance cannot improve
what is already at ceiling; these benchmarks therefore cannot substantiate hallucination-
reduction claims — for any system. The measurable value of governance on such benchmarks
lies in calibrated abstention and structural auditability. We report this as a finding
about the evaluation landscape as much as about the artifact.

### 6.4 Positioning against 2026 governance-aware RAG
Three ways to use a knowledge graph in generation: as pre-generation context (GraphRAG,
KAG), as post-generation verification (CogniGraph's SemanticSHACLGate; SITL's terminal
validation; HalluGraph's detection), or — this program's position, previously unfilled —
as an authorization gate on the evidence admitted to generation. Where prior systems report
one operating point behind a single fail-closed gate, this work reports the full
strictness frontier with the abstention triad per level, adopts CogniGraph's Constrained-F1
for comparability, and adds a corpus-level predictor of the frontier's shape.


---

## 7. Threats to validity and the reproducibility record

### 7.1 Model and reproducibility protocol (verbatim)

### Paper 2 — Model Selection & Reproducibility Protocol

*Status: draft v1. Governs every result-generating run for Paper 2. Read before the first real build.*
*Owner: Vivek. Last updated: 2026-06-28.*

---

#### 0. Why this document exists

Paper 2 is a **measurement paper** (RAGBench / TRACe evaluation of the GovernRAG
pipeline). For a measurement paper, the single thing reviewers and a committee
will probe hardest is: **what produced these numbers, and can it be reproduced
from your artifact?** This protocol fixes those rules *before* the first run, so
the methods section writes itself and no result is ever in doubt.

The execution *venue* (laptop, a cloud VM, a sandbox) is **not** the issue — any
machine is just compute. The issues are: which model, who/what is allowed to
touch the results, and whether every run is pinned and logged.

---

#### 1. Decision 1 — one fixed, single-model pipeline

- Paper 2 uses **one result-generating pipeline**, fixed before the evaluation
  run and unchanged across all records and all conditions.
- The pipeline uses **a single LLM**, applied uniformly. No mixing providers or
  model versions across records — that is a confound that invalidates any
  cross-record comparison.
- Switching away from Paper 1's Gemini runs is **legitimate**: Paper 2 is a fresh
  experiment with no obligation to reuse Paper 1's model. The only consequence is
  the comparability caveat in §6.

#### 2. Decision 2 — pipeline model ≠ judge model (independence)

This is the constraint that decides the design, and the one most likely to sink
the paper if ignored.

- TRACe / RAG evaluation leans on **LLM-as-judge**. If the same model both
  *produces* the system output and *judges* it, you get **self-preference bias** —
  models systematically favor their own generations (Panickssery et al. 2024;
  self-enhancement bias in Zheng et al. 2023). A reviewer at a SIGIR/EMNLP-class
  venue will flag this immediately.
- **Rule:** the evaluator/judge must be **independent of the pipeline model.**
- **Recommended design (turns dual access into a strength):**
  - **Pipeline model = Claude** (extraction M2, anchoring D2/D3, generation Q6).
  - **Judge model = Gemini** (or a reference-based / open evaluator, or the
    RAGBench-released evaluator).
  - You have access to both, so use one for the system-under-test and the other
    for evaluation. This is *cleaner* than a single-vendor study, and it is
    defensible on exactly the axis reviewers attack.
- If you later want to argue robustness, report the metric under **both** judge
  choices and show the ranking of conditions is stable (a judge-sensitivity check).

#### 3. Decision 3 — execution environment & the agent bright line

- **Run real result-generating builds on a controlled environment you own and can
  document** — your laptop, or a cloud VM you provision with the key. **Not** the
  AI agent's sandbox: it is ephemeral, time-limited, undocumented, and outside
  your version control — the opposite of reproducible.
- **The bright line for AI assistance (hold this exactly):**
  - **Allowed:** AI writes and *smoke-tests harness/tooling code* against
    **synthetic** fixtures; AI helps analyze, tabulate, and write up results you
    generated. Disclose per venue policy (§7).
  - **Not allowed:** AI generating, imputing, "patching," or otherwise influencing
    the **measured outputs** of the system under test. Results must come from the
    fixed pipeline and be re-runnable from your artifact. The agent must never be
    both experimenter and part of the system being measured.

#### 4. Reproducibility harness — pin, log, freeze

Every run writes a **run manifest** capturing the full configuration. Minimum
fields:

```yaml
run_id:            <dataset>_<phase>_<UTC timestamp>
git_commit:        <pipeline repo commit hash>     # code provenance
corpus:            <name> + record count + data checksum
phase:             build | serve | eval
model:
  provider:        anthropic | google
  model_version:   <exact string, e.g. claude-sonnet-4-6 / gemini-...>
  api_date:        <YYYY-MM-DD of the API/version>
  sdk_version:     <client lib version>
decoding:
  temperature:     0
  top_p:           <value>
  max_tokens:      <value>
  seed:            <if supported>
prompts:
  template_hash:   <hash of each frozen prompt template>
judge:                                              # eval phase only
  provider/model_version/api_date: <independent of pipeline model>
library_versions:  {networkx, datasets, ...}
repeats:           <N>                              # see below
cost:              {input_tokens, output_tokens, usd}
latency:           {build_seconds, per_question_seconds}
peak_ram_mb:       <from B1 / serve harness>
```

Rules that go with it:

- **Pin** the exact model version string, `temperature=0`, `top_p`, `max_tokens`,
  SDK version, and API date. "We used Claude" is not reproducible; the version
  string is.
- **Repeat and report variance.** Hosted LLM APIs are **not bit-deterministic even
  at temperature 0** (server-side batching/routing). A single number is not
  credible — run **N ≥ 3 repeats** per condition and report mean ± std (or CI).
- **Freeze prompts on a dev split *before* touching the test set.** Tune prompts
  on held-out dev data, hash and freeze them, *then* run test. Iterating prompts
  against the eval set is overfitting to the test and quietly invalidates results.
- **Capture cost and latency**, not just quality. Part of the Paper 2 claim is
  "governance at no quality cost" — cost/latency is half of that argument.

#### 5. Provider abstraction (makes the above by-design, not by-discipline)

- Put the LLM call behind **one interface** (`generate(prompt, **decoding) -> text`
  / a structured-output variant), with **provider as a config flag**
  (`--provider claude|gemini`).
- Refactor only the call sites (M2 extraction client, D2/D3, Q6, and the eval
  judge) to go through it; **governance logic stays frozen.**
- Benefits: judge-independence becomes a config choice; the same harness runs the
  judge-sensitivity check in §2; the run manifest reads model fields from one
  place; swapping Gemini↔Claude is a flag, not a rewrite.
- Engineering note: M2 currently uses Gemini's async client + JSON mode. Claude
  structured output should go through **tool-use / JSON schema**; the extraction
  prompts will need re-tuning (do it on the dev split per §4).

#### 6. Integrity guardrails & caveats

- **One pipeline, fixed:** no silent changes between conditions or runs.
- **No mixed models** across records or phases (except the deliberate, reported
  judge-sensitivity check).
- **Comparability caveat:** Paper 2's absolute numbers are **internally
  consistent** but **not comparable to Paper 1's Gemini numbers** — do **not**
  claim a cross-paper delta. State this explicitly in the paper.
- **Attestable provenance:** you (the author) can re-run any reported number from
  the artifact + run manifest.

#### 7. Disclosure statement (draft, for the paper)

> *AI-assistance disclosure.* AI tools were used to author and test harness and
> analysis code and to assist drafting. All reported experimental results were
> produced by the fixed [Claude]-based GovernRAG pipeline described in §X and
> evaluated by an independent [Gemini]-based judge; configurations are recorded in
> per-run manifests released with the artifact. No AI tool generated, imputed, or
> altered any measured result.

Adapt to the venue's specific AI-use policy.

#### 8. References (verify exact bibliographic details before citing)

- **Zheng et al. 2023** — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
  (NeurIPS 2023). LLM-as-judge; position / verbosity / self-enhancement bias.
  *(confident)*
- **Panickssery et al. 2024** — "LLM Evaluators Recognize and Favor Their Own
  Generations" (NeurIPS 2024). Self-preference / self-recognition bias.
  *(confident on existence; verify author spelling — formerly Perez.)*
- **Friel, Belyi & Sanyal 2024** — "RAGBench: Explainable Benchmark for
  Retrieval-Augmented Generation Systems." TRACe = Relevance, Utilization,
  Adherence, Completeness. *(confident; confirm metric definitions against the
  paper.)*
- **Es et al. 2023/2024** — "RAGAS: Automated Evaluation of Retrieval Augmented
  Generation." *(reference-free RAG eval; context.)*
- LLM-API nondeterminism at temperature 0 is a **documented practitioner finding**
  (batching / MoE routing), not a single canonical paper — present as engineering
  reality, cite a primary source if you find a rigorous one. *(lower confidence —
  hedge in text.)*

---

##### One-paragraph summary
Standardize Paper 2 on a single, version-pinned LLM applied uniformly; make the
**judge a different model** than the pipeline (recommended: pipeline = Claude,
judge = Gemini) to avoid self-preference bias; run real builds on a controlled
machine, never the agent sandbox; keep AI on tooling/analysis and never on result
generation; log every run's full config to a manifest; repeat ≥3× and report
variance; freeze prompts on a dev split before touching test. Do this and the
approach is fully defensible.

### 7.2 Threats (consolidated)

**Judge validity.** The pre-registered judge was withdrawn by the provider mid-study;
all runs were (re-)judged under a pinned successor (inter-judge κ=0.681 on 8,208 pairs;
levels shift, structure is invariant; both judgings reported; H1's equivalence verdict is
judge-scoped with the G1 cost bounded 4–9 pp by paired bootstrap). **Model churn.** Four
model withdrawals occurred in a single day; every repointing is deviation-logged before
execution with terminal and provider-dashboard evidence — model mortality is treated as a
first-class reproducibility hazard of LLM-API research (a pattern already encountered in
Part 1's baseline replay). **Probe scale.** Runs 2–3 are reduced-corpus generalization
probes (163/150 questions) under a deterministic, outcome-blind, hash-published selection
(§4.2); claims are scoped to pattern replication, not population estimates. **Single
generation model; M4 nondeterminism** (quantified in Sprint 1); **exploratory status** of
the §6.2 moderator. **Internal validity is protected throughout:** within every run,
governed and ungoverned arms share the same index, models, and judge.

---

## 8. Reproducibility and audit artifacts (inventory)
Sealed archives (append-only, SHA-256 manifests, read-only, git-tagged): `results/
run1_delucionqa` (47 files + full output state), `results/run1_rejudge`, `results/
run2_hagrid` (23 files), `results/run3_expertqa`, `index/<corpus>` build snapshots.
Per-run manifests with cost and key attribution; provider-dashboard screenshot evidence
packs (Run1/2/3_Evidence). Public timestamps: github.com/gunavivek/GovernRAG1, branch
paper2-spectrum, tags run1-complete / run2-complete / run3-complete. Deviation log: §4.1.
Decision-log interop: OKF v0.1 conformance-verified export (one-paragraph treatment §2;
demo in 3_Positioning/OKF_Demo).

## 9. Future work and conclusion
Confirmatory in-ontology run with pre-registered shape prediction (FinQA/CUAD); a
conformal/risk-controlled wrapper over level choice (per-level guarantees the 2026
governance-RAG literature lacks); provider-abstraction and run-context refactoring of the
harness; the KG-framed companion study. Conclusion: governance in RAG is not a switch with
a hidden price but a dial with a measurable one — and both the dial's benefit and its
price are now characterized, pre-registered, and reproducible to the level of individual
judged answers.
