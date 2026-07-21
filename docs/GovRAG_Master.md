# GovRAG Master — Dissertation Foundation Document
*Created 2026-07-21. THE single source of truth for the defense and every extraction.
Rule: every number cited here traces to a sealed archive; every section carries its SOURCE
and its EXTRACTION MARKS. Edit this document only — papers and slides are derived.*

**Extraction marks:** `CORE-S1` = Scenario-1 TPS paper (Paper 2 standalone, cites published
Paper 1) · `CORE-S2` = Scenario-2 combined paper (QASC rejects; framework promoted, results
compressed) · `CORE-KG` = 2027 knowledge-graph paper (ESWC/ICKG) · `EXT` = dissertation/
defense only. **Status:** SOURCED = text exists and is cited to its file · DRAFT = to write.

## Extraction recipes (assemble a paper by taking ONLY its marked sections)
- **Scenario-1 TPS paper (≈8 pp IEEE):** 1 · 2(compressed) · 3.9 (one-page framework) ·
  6(½ pp) · 7 · 8(headline tables only) · 9 · 10 · 12. Cite Paper 1 for everything in 3–5.
- **Scenario-2 combined paper:** 1 · 2 · 3(promoted, compressed) · 5.4(ablation core) ·
  6(½ pp) · 7(compressed) · 8(headline only) · 9 · 10 · 12.
- **KG paper (2027):** 3.2–3.5 · 6 · 8.4(moderator) · 9.2 + new confirmatory run.
- **Defense deck:** 0.2 map · 1 · 3.9 · 5.4 · 8(figures) · 9 · 12 + dial supplement demo.

---

## 0. Front matter — EXT

### 0.1 Reading guide
This master is the single source of truth for the GovRAG research program. Papers, slides,
and the dissertation chapters are EXTRACTIONS assembled from the recipes above. Every
quantitative claim cites a sealed, SHA-256-manifested archive; sections marked EXPLORATORY
may not be presented as confirmatory anywhere downstream.

### 0.2 Proposal-contribution map — the defense spine  [STATUS: DONE, M-1]
The dissertation proposal (approved April 16, 2025; committee: Xu, Talburt, Wu, Wang)
committed to four contributions (§5). Each was delivered and measured:

| # | Proposal commitment (Apr 2025, §5 verbatim intent) | Delivered as | Evidence (auditable) |
|---|---|---|---|
| C1 | **Business Architecture–Aligned RAG Framework** — Information Concepts from Business Architecture integrated into RAG for semantic alignment, retrieval precision, traceability | The GovernRAG governed concept-graph pipeline: BIZBOK reference ontology (R-pipeline, 553 concepts), domain governance profiles (D-pipeline), concept-graph construction with ontology alignment (M-pipeline), reference-monitor-mediated serving (Q-pipeline). Frozen and evaluated at benchmark scale. | Paper 1 v10.2 §4 (architecture); repo `experiment/`; per-corpus `index/<corpus>/build_manifest.json` (sealed) |
| C2 | **Structured Concept Mapping Approach** — concept–attribute–value alignment between queries, documents, and BA constructs | Operational end-to-end: D5 governance manifests bind corpora to domain profiles; Q2 signatures carry attribute targets per query; M4 assigns every concept an alignment status (Match / Adaptive / Unmapped). Measuring the aligned share per corpus (98.2% / 47.2% / 25.8%) yielded the ontology-fit variable that predicts governance cost — a result BEYOND the proposal. | Paper 1 §4; `M4_alignment_results.jsonl` + graph attributes in each sealed index; Analysis_CrossRun §4 |
| C3 | **Enterprise-Grade Evaluation Metrics** — Relevance, Utilization, Completeness, Adherence applied to retrieval and generation quality | Applied exactly as proposed (RAGBench TRACe), extended with abstention correctness, provenance coverage, and cost — in a pre-registered, report-regardless design: 1,225 questions, 3 corpora, 9 configurations, dual-judge robustness (κ=0.681), paired bootstrap CIs. | `Analysis_Plan_and_Stopping_Rule.md` (pre-registration + deviation log); `E3_*_master_eval_log.csv` in each sealed archive; Analysis_CrossRun §2–§3, §7–§8 |
| C4 | **Pathway for Enterprise AI Adoption** — standards-based, explainable, governance-friendly deployment | The governance dial with priced operating points: G1 ≈ auditability nearly free (93% coverage in-domain, 97.7–100% resolvable citations, complete decision logs); strict tiers buy reliable refusal (corrRef 75–78% vs 41–44% ungoverned) at a coverage price predictable from C2's aligned share. Deployment guidance: measure ontology–corpus fit BEFORE enabling strict tiers. Interop: decision logs export to OKF v0.1 (conformance-verified). | Analysis_CrossRun §5 (contribution framing); `Supplement_Governance_Dial_Examples` (11 verbatim walkthroughs); `3_Positioning/OKF_Demo/`; Run manifests (cost) |

Beyond the proposal: (i) the slope/band/cliff frontier taxonomy with the ontology-fit
moderator (EXPLORATORY — motivates the confirmatory in-ontology study in ch 12); (ii) the
build-once/serve-many re-engineering that reduced evaluation cost O(n·C_build)→O(C_build+
n·C_query), making 1,225-question evaluation feasible for under $1,000 total.

### 0.3 Program timeline  [STATUS: DONE, M-1]
Jan 2021 program entry (two-paper requirement not yet in effect — applicability question
posed to Dr. Talburt 2026-07-21) · Apr 16, 2025 proposal approved · 2025–2026 framework
construction (Part 1) · May 2026 Paper 1 v10.2 FINAL submitted to QASC/QUAIC 2026 (decision
expected ~Jul 31; conference Aug 28) · Jun–Jul 2026 build-once/serve-many re-engineering ·
Jul 6, 2026 pre-registration committed · Jul 9–10 Run 1 (DelucionQA, 912 q, 8,208 judged
pairs) · Jul 12–18 cross-corpus design + selection (deviation-logged) · Jul 19–20 Runs 2–3
(HAGRID 163 q; ExpertQA 150 q) + forced model migration (4 withdrawals) + Run-1 re-judge
under successor judge · Jul 20–21 cross-run analysis sealed; committee engaged; venue plan
(TPS Aug 15 → notify Sept 20) · Jul 22–31 master assembly (Sprint M) · Aug 1–15 extraction
+ TPS submission (Sprint E) · target: defense upon acceptance + committee green light.

## 1. Introduction — CORE-S1 · CORE-S2 · EXT  [STATUS: DONE, M-2 — program-level adaptation of Paper 1 §1]
*Reference numbering [n] follows Paper 1 v10.2 until the unified bibliography pass (M-9).*

### 1.1 The governance gap in retrieval-augmented generation
Retrieval-Augmented Generation (RAG) has become the dominant pattern for grounding large
language models in non-parametric knowledge sources [1]. Variants — Corrective RAG [2],
Self-RAG [3], GraphRAG [4], KAG [5], and the modular architectures surveyed in [6] — extend
the retrieval primitive principally to improve answer accuracy. What every variant shares is
an architectural commitment to retrieval as the only operation between query and model, and
to answer accuracy as the central measure of quality.

That commitment is unsuitable for enterprise document environments. In banking, healthcare,
and legal-discovery contexts, governance frameworks lack adequate LLM-specific controls for
hallucination risk [7]; the deployment question is not only *did the model produce the right
answer* but *can the answer be demonstrated to derive from authorised evidence, recorded with
audit-defensible provenance, externally verifiable against documented governance objectives*.
These are properties of the architecture above the model — supplied neither by prompt
engineering nor by model improvement. Three observations make the gap concrete: where RAG
variants expose governance controls (SD-RAG [8], OPA two-plane [9], SafeRAG [10], OG-RAG
[11], KAG [5]), none anchors governance on a documented cross-industry enterprise reference
vocabulary; no published RAG system uses a recognised enterprise body of knowledge as its
reference plane; and RAG evaluation measures generation quality (RAGBench/TRACe [20]) rather
than architectural enforcement.

### 1.2 The research program: from architecture to priced governance
This dissertation closes that gap in two movements. **Part 1** (the GovernRAG architecture)
contributes the missing composition: a per-record governance contract anchored on a
documented enterprise reference vocabulary, predicate-validated retrieval expansion under
that contract, and reference-monitor mediation of the generation context as the contract's
enforcement gate — demonstrated end-to-end on ten cases. **Part 2** answers the question the
architecture makes askable: *evaluated at benchmark scale, what does governance actually
cost, and what does it buy?* A build-once/serve-many re-engineering of the execution layer
(governance logic frozen) made a pre-registered, three-corpus, 1,225-question evaluation
feasible, producing the first per-level governance–coverage frontier for RAG and an
ontology-fit variable that predicts the frontier's shape.

### 1.3 Contributions of the program
Part 1 (Hevner taxonomy [22]; validated §5–§6): **C1 — Governance Manifest** (construct): a
per-record, machine-executable governance contract derived from an enterprise reference
vocabulary and forward-bound through every downstream stage (D5). **C2 — Recursive Bridge
Discovery** (method): audit-driven, predicate-validated retrieval expansion, bounded to one
iteration (Q3.5/Q3.6). **C3 — Reference Monitor** (composition): the Anderson/Saltzer–
Schroeder pattern [25, 26] instantiated as the output gate over the manifest substrate (Q5).

Part 2 (this dissertation's evaluation contributions; ch 6–9): **C4 — Feasible governed
evaluation**: build-once/serve-many execution reducing cost O(n·C_build) → O(C_build +
n·C_query), enabling benchmark-scale governed evaluation for under $1,000. **C5 — The
governance frontier**: pre-registered measurement of coverage, accuracy, faithfulness,
abstention, and auditability across governance levels G0–G4 on three corpora — governance
as a priced dial, not a switch. **C6 — Ontology-fit as a deployment predictor**
(exploratory): the corpus's ontology-aligned concept share (98.2% / 47.2% / 25.8%) orders
the frontier's shape (slope / band / cliff), giving practitioners a measurable pre-deployment
predictor of governance cost.

## 2. Related work — CORE-S1(compressed) · CORE-S2 · EXT  [STATUS: DONE, M-2 + M-2b]

### 2.1 RAG variants and taxonomy  [ported, Paper 1 §2.1]
Survey literature [6, 29] organises RAG into Naive, Advanced, and Modular; failure handling
spans robust-retriever selection [28, 32], iterative/adaptive loops [30, 31], self-reflection
[3], trajectory repair [33], and agentic reframings [34, 35]. GovernRAG positions as Modular
RAG whose modularity is *governance-driven*: pipeline boundaries drawn for audit and contract
enforcement. Within graph-augmented RAG (GraphRAG [4], KAG [5]) the graph schema is emergent
from the corpus; GovernRAG inverts this — an enterprise reference graph is constructed
globally and per-corpus graphs are aligned to it. *(Part 2 gives this inversion empirical
teeth: the alignment rate itself becomes the cost predictor, ch 8.4.)*

### 2.2 Policy and management frameworks  [ported, Paper 1 §2.2]
ISO/IEC 42001:2023 [21] and the NIST AI RMF [44] specify *what* evidence regulated
deployments must produce (lineage, decision traceability, per-output evidence), not *how* to
produce it structurally [7, 19]. GovernRAG addresses the complementary architectural layer:
the manifest (C1) and per-chunk decision log (C3) are exactly the per-record evidence
artefacts these frameworks require, produced structurally. *(Part 2 quantifies the claim:
97.7–100% resolvable citations and complete decision logs across 1,225 questions, ch 8.3.)*

### 2.3 Ontology-grounded RAG  [ported, Paper 1 §2.3]
DeBellis et al. [14], OG-RAG [11], OntoRAG [36], and the ArchiMate line [12, 13] use
ontologies as schema layers. GovernRAG differs twice over: the anchor is a documented
enterprise reference vocabulary (BAGuild IRM [40]; vocabulary-agnostic in principle), and
the constraint is forward-bound through D, M, and Q pipelines rather than applied at
retrieval time only.

### 2.4 Retrieval-stage policy enforcement  [ported, Paper 1 §2.4]
SD-RAG [8], OPA two-plane [9], SafeRAG [10], ARBITER [23], conformal filtering [37], and
Le Ray's policy-governed triptych [43] enforce policy over retrieval or attest what was
generated. GovernRAG operates at the complementary point — architectural enforcement of
*what can be generated* — via the reference-monitor pattern over a per-record,
vocabulary-anchored contract.

### 2.5 Governance evaluation  [ported, Paper 1 §2.5 + DELTA SLOT]
Generation-quality evaluation (RAGBench/TRACe [20], [15–18, 38]) measures relevance,
accuracy, faithfulness — not architectural enforcement.
**The 2026 governance-RAG delta [M-2b — DONE, from Prior_Art_Synthesis.md, full texts
read 2026-07-07].** Three ways to use a KG in generation frame the field (SITL's own
taxonomy): KG-before as retrieval context (GraphRAG [4], KAG [5]); KG-after as output
verification — CogniGraph's SemanticSHACLGate (Kumar 2026, SSRN 6837300) validates every
agent output post-generation at fixed thresholds, SITL (Nadimuthu et al. 2026, IEEE
Internet Computing) grounds outputs into a deterministic ontology binary-validate/reject,
HalluGraph (Noël 2025) detects misalignment without an abstention policy. **GovernRAG
occupies the unfilled third position: KG-as-authorization-gate on the evidence ADMITTED to
generation** — the reference monitor governs what the model may condition on, tunably.
Adjacent single-point systems sharpen the wedge: Korosuke (Singh 2026) collapses security
into a scalar re-ranking utility; Governance-Aware Agentic RAG (Jain 2026) offers one
answerable/abstain gate without a KG substrate; C-RAG (Kang 2024) and Conformal-RAG (Feng
2025) drive risk–coverage with model *confidence*, not authorization strictness. Every one
of these systems reports a **single operating point**; the field's own gap analyses name the
missing per-strictness faithfulness-versus-coverage curve and the refusal/correct-refusal/
false-rejection triad as unreported. Part 2 contributes exactly these: the G0–G4 frontier
across three corpora, the abstention triad per level, and (beyond the field's asks) a
corpus-level predictor of the frontier's shape. One sentence: *where CogniGraph and SITL
place a single fail-closed symbolic gate on the model's output, GovernRAG places a tunable,
ontology-derived reference monitor on the admitted evidence — and reports the full
governance-strictness frontier neither characterizes.* (Comparability: report CogniGraph's
Constrained-F1 alongside ours — done, E3P `C-F1` column, ch 8.)

### 2.6 Theoretical foundations  [ported, Paper 1 §2.6]
Kernel theories per design principle: DP3 extends information-flow security and the
reference-monitor pattern [25, 26] (complete mediation, tamper-resistance, verifiability);
DP1 extends EA reference principles, pipes-and-filters [39], and data-provenance theory;
DP2 extends IR under typed constraints and bounded graph traversal.

### 2.7 Comparison artifact  [ported by reference, Paper 1 §2.7 Table 1]
Gap matrix C1–C3 × {ARBITER, Stop-RAG, Doctor-RAG, DecoupleSearch, Naive RAG} — carry
Table 1 verbatim into extractions needing it. Part 2 adds a second comparison axis (operating
points vs frontier) to be tabulated in ch 8/9 once M-2b lands.

### 2.8 OKF interoperability  [one paragraph — per positioning decision]
GovernRAG's decision logs and provenance bundles export losslessly to Google's Open
Knowledge Format v0.1 (conformance-verified demo, `3_Positioning/OKF_Demo/`): the audit
artefacts H4 measures are portable to an emerging vendor standard, not proprietary to this
architecture. OKF is an alignment target, not a dependency.

## 3. The GovernRAG framework [Part 1] — CORE-S2 · CORE-KG · EXT  [STATUS: PORTED, M-3 — condensed; full text = Paper 1 v10.2 §4 + Supp. A/B]
*Porting depth: this chapter carries the architecture at extraction depth; the dissertation's
Phase-5 pass expands from Paper 1 verbatim where needed. Figures: Paper 1 Fig. 1 (architecture),
Table 2 (pipeline summary) — carry into S2 extractions.*

### 3.1 Architecture overview
GovernRAG is five capability pipelines plus a cross-cutting audit layer, connected by five
typed flows (vocabulary, manifest, evidence, response, audit): **R** — Reference Vocabulary
Construction (global, corpus-independent; R3.5 ontology builder, R4 embedder); **D** —
Governance Contract Generation (per corpus; tiered domain anchoring D1–D3, control packets
D4, **manifest composer D5 = C1's locus**); **M** — Document Knowledge Management (per
corpus; predicate-bound chunking M1, triple extraction M2, graph construction M3, concept
augmentation M3.3, ontology alignment M4, embedding M5); **Q** — Audited Query Resolution
(per question; intent gate Q1, signature Q2, governed retrieval Q3, **bridge discovery
Q3.5/Q3.6 = C2**, residuals Q4, **Reference Monitor Q5 = C3**, cited synthesis Q6); **E** —
comparative evaluation vs Naive baseline; **Z** — audit composition (provenance, decision
logs). The manifest is forward-bound: one governance thread from vocabulary to answer.

### 3.2–3.4 Pipeline mechanisms  [by reference]
Full mechanisms in Paper 1 §4 + Supplementary A (R ontology construction; D three-tier
domain anchoring; M extraction under the predicate budget; Q governed retrieval). Part-2-
relevant detail: M4 assigns every concept node an alignment status (Match/Adaptive/
Unmapped(Low-Conf)) against the 553-concept BIZBOK reference — the per-corpus aligned share
that ch 8.4 elevates to the cost predictor.

### 3.5 The governance dial (Part-2 instrument over the Part-1 substrate)
G0 = ungoverned baseline (identical model, no contract) · G1 Cited = citation-bearing
answers required · G2 Grounded = evidence must satisfy the manifest's authorized predicates ·
G3 Strict = strict authorization · G4 Corroborated = multi-source corroboration; plus
orthogonal axes (ontology-conformance: drop non-conformant triples; domain-affinity:
threshold on chunk affinity). Levels parameterize Q5/Q6 behavior only — retrieval and graph
are level-invariant, so per-level differences isolate the governance mechanism. (Genesis:
`GOVRAG_LEVEL` pilot, deviation log 2026-07-06; Dr. Xu sign-off relayed 2026-07-09.)

### 3.9 **One-page framework summary** — CORE-S1 (the ONLY §3 content in Scenario 1). DRAFT — task M-4.

## 4. Design-science methodology — EXT (CORE-S2 one paragraph)  [STATUS: PORTED, M-3]
Positioned in Design Science Research [22, 27]: the contribution is the artifact + three
design principles + boundary characterisation — architectural and constructive. Five design
objectives: **DO1–DO4 uniform-realisation** (per-record contract; per-chunk audit log of
admission/exclusion with reasons; cited answer or boundary-maintained refusal; end-to-end
verifiability) — satisfied 10/10 by construction; **DO5 categorical-differentiation**
(a capability Naive RAG cannot exhibit by design: boundary-maintained refusal), decomposed
by enforcement layer DO5a (Q6 structural check on empty evidence) / DO5b (model competence) /
DO5c (DP3 structural guarantee). Three design principles ground the contributions: **DP1**
per-record forward-bound governance contract (primary; kernel: EA reference principles,
pipes-and-filters, provenance theory) · **DP2** audit-driven predicate-validated expansion
(kernel: IR under typed constraints) · **DP3** reference-monitor mediation (kernel:
Lampson/Anderson/Saltzer–Schroeder; complete mediation, tamper-resistance, verifiability).
Part 2 completes the DSR cycle: Peffers Step-6 Evaluation, executed as the pre-registered
benchmark campaign (ch 7–8) that Paper 1 §8 named as next-step work.

## 5. Part-1 demonstration & ablation — EXT (5.4 → CORE-S2)  [STATUS: PORTED, M-3]
### 5.1–5.2 Ten-case demonstration and outcome matrix  [by reference: Paper 1 §5–6, Table 3]
Ten RGB cases (five questions × positive/negative evidence; same model both arms). DO1–DO4
hold 10/10; categorical differentiation (DO5) exhibited in 3/5 negative cases (rgb_5_N,
rgb_104_N, rgb_3_N — Naive bled/hallucinated, GovernRAG refused); remaining cases classify
into named boundary modes (BM1 over-strict refusal; BM2 predicate-authorised bleeding;
BM3 parametric leakage) — characterised, not hidden.
### 5.4 Ablation  [by reference: Paper 1 §6.2 — CORE-S2]
DP3's causal role isolated by ablation and reframed honestly: a model-agnostic, audit-grade
structural guarantee operating in defence-in-depth with Q6's structural check and model
competence — not the sole causal mechanism of refusal. (Note for ch 10: Paper 1 also
absorbed a forced model substitution — gemma-3-4b-it deprecated, baseline replayed on its
successor — prefiguring Part 2's model-mortality protocol.)
### 5.5 Bridge: from demonstration to measurement  [DRAFT DONE, M-3]
The Part-1 demonstration establishes that the architecture *realises* governance properties
uniformly — but at n=10, purposively selected, on one corpus, with the original per-question
execution model rebuilding the graph for every case (~3 h/question), it cannot say what
governance *costs* at scale, how refusal behaves across a full answerability distribution,
or whether the properties generalise across corpora. Those are frontier questions, and they
required re-engineering the execution layer without touching a single governance decision —
the subject of chapter 6.

## 6. Scale-out: build-once / serve-many — CORE-all
The execution-layer re-engineering that made benchmark scale feasible (O(C_build + n·C_query));
frozen-logic guarantee; B1–B5/E3P harness with guards. SOURCED (Paper2 2_Design docs,
PROJECT_STATUS) — needs prose pass. Cost result: 912-q run $222; reduced-corpus runs <$45.

## 7. Evaluation methodology [Part 2] — CORE-S1 · CORE-S2
- 7.1 Pre-registration + deviation policy. SOURCED (Analysis_Plan_and_Stopping_Rule.md).
- 7.2 Corpora + document-reuse selection + junk filter + representativeness. SOURCED
  (Subset_Selection_Validity.md §1–§4 — paper-ready text exists in §5).
- 7.3 Metrics (TRACe R/U/C/A + abstention + provenance + cost) and judge protocol incl.
  dual-judge robustness. SOURCED (Analysis_CrossRun §7).
- 7.4 Configurations: G0–G4 × axes; per-level serving. SOURCED (B4/manifests).

## 8. Results: the three-corpus governance frontier — CORE-S1 · CORE-S2
- 8.1 Frontier (Fig. Frontier_ThreeCorpora.png) + per-level table. HEADLINE. SOURCED (Analysis §2).
- 8.2 H1–H4 verdict matrix incl. judge-scoped parity + bootstrap CIs. HEADLINE. SOURCED (§3, §8).
- 8.3 Auditability results (97.7–100%; decision logs). HEADLINE. SOURCED (§3).
- 8.4 Ontology-fit moderator (98.2/47.2/25.8 → slope/band/cliff) — EXPLORATORY framing
  mandatory. HEADLINE + CORE-KG. SOURCED (§4).
- 8.5 Axis variants, dual-judge detail, full CIs → SUPPLEMENT under page limits. SOURCED (§7–8).
- 8.6 Worked examples: pointer to dial supplement (11 examples). SOURCED.

## 9. Discussion — CORE-S1 · CORE-S2
- 9.1 What governance costs and buys: stable benefit, corpus-dependent price; deployment
  guidance (measure M4 aligned share pre-deployment). SOURCED (Analysis §5) — prose pass.
- 9.2 Slope/band/cliff taxonomy; when to use which G-level. DRAFT.
- 9.3 The H2 ceiling honestly: what these benchmarks cannot show. DRAFT (1 para).

## 10. Threats to validity — CORE-S1 · CORE-S2 · EXT
Merged Part-1 (§7.1) + Part-2 threats: judge replacement (dual-judge evidence), model
churn (forced, logged), probe-scale runs 2–3, single generation model, M4 nondeterminism,
exploratory moderator status. SOURCED (Analysis §6 + Paper 1 §7.1) — merge pass.

## 11. Governance & reproducibility record — EXT
Deviation log (full, as appendix); sealed-archive inventory + SHA manifests; evidence packs;
per-run manifests; git tags. SOURCED — assembly only. This chapter IS the audit defense.

## 12. Future work & conclusion — CORE-all
Confirmatory in-ontology run (FinQA/CUAD prediction test); provider abstraction; run-context
refactor; KG-paper agenda. SOURCED fragments (Paper 1 §8–9 + Analysis §5) — prose pass.

## Appendices — EXT
A dial supplement (11 examples) · B full result tables · C deviation log verbatim ·
D venue/publication record (Venue_Options.md + decisions) · E harness documentation.
