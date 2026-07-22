> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\5_Manuscript\Prior_Art_Synthesis.md — edit the canonical, then re-snapshot. See Source_Register.docx.

# Prior-Art Synthesis & Positioning (from Elicit Researcher, 2026-07-07)

*Distilled from three Elicit Researcher reports in `Prior Art Literature Review/`. Purpose:
lock the contribution framing, the works to cite/differentiate, and the terminology for Paper 2.*

## Verdict
The three ingredients — (1) RAG governance, (2) ontology/KG-derived authorization, (3) calibrated
abstention — each exist, but **no prior work fuses them into a tunable, multi-level, ontology-derived
governance dial that drives the risk–coverage curve with governance strictness instead of model
confidence.** That composition is the unclaimed intersection = GovernRAG's contribution.

## One-sentence contribution
> GovernRAG uses **graded, ontology-derived authorization strictness as the abstention substrate itself**
> — a tunable reference monitor whose levels trade answer coverage against faithfulness and provenance —
> and characterizes the full per-level risk–coverage frontier, which governance-aware RAG reports as a
> single operating point and conformal RAG drives with confidence rather than authorization.

## Closest prior work — cite and differentiate
| Work | What it does | Our wedge |
|---|---|---|
| **CogniGraph** (Kumar 2026) — the one to beat | SemanticSHACL gate on output; EU-AI-Act framing; "Constrained F1"; 49% false-rejection cut | single fail-closed gate vs our **tunable multi-level spectrum + full frontier** |
| **Korosuke** (Singh 2026) | hierarchical security embeddings + adaptive re-ranker; relevance–security utility | scalar utility knob vs our **ontology-derived tiers with per-level faithfulness** |
| **Governance-Aware Agentic RAG** (Jain 2026) | governance reranker + evidence abstention + extractive composer | one answerable/abstain gate; no KG substrate; no dial |
| **C-RAG** (Kang 2024) / **Conformal-RAG** (Feng 2025) | certified coverage-vs-risk knob, per-claim guarantees | risk axis = factuality/confidence, **not authorization strictness** |
| **HalluGraph** (Noël 2025) | KG-alignment audit (Entity Grounding, Relation Preservation), source-linked | a **detector**, no abstention **policy** |
| **SITL** (Nadimuthu 2026), **ontology-to-tools** (Zhou 2026), **Abdelrazek 6G** (2026) | fail-closed ontology conformance / triple-level RBAC | not tied to a coverage/faithfulness **dial** |
| **Tayebati** (2025) | RL-learned adaptive conformal abstention thresholds | template for a **conformal wrapper** over our governance levels (future work / strength) |

## The field's own admitted gaps = our cleanest contributions
1. **Per-strictness faithfulness-vs-coverage curve** — "field default is a single operating point." Our
   G0–G4 frontier is that missing curve.
2. **Governance metric triad** — refusal rate, *correct*-refusal rate, and *correct-answer false-rejection
   rate* — "almost nothing outside CogniGraph reports" it. Our stratified scorer produces exactly this.
3. **Open question nobody tested:** does stricter authorization actually improve *attributability*, or only
   reduce leakage?

## Terminology to standardize (use the field's handles)
risk–coverage curve / frontier · selective prediction · abstention · conformal / risk-controlled (position
*against* — ours is governance-driven) · faithfulness / attribution / groundedness · **citation faithfulness**
(cited *and relied upon*, Wallat 2025) · **fail-closed** gating · **reference monitor** (= our Q5) ·
allowed-predicate / ontology-conformance authorization · **Constrained-F1** (report to compare vs CogniGraph).

## Strategic notes
- **Hot, 2026-heavy space** (CogniGraph, Korosuke, BalanceRAG, SITL, ontology-to-tools all 2026 preprints):
  move fast; differentiate from CogniGraph explicitly; watch pre-emption.
- The gap analysis **endorses** adding the two ontology-derived axes (reference-ontology conformance +
  domain-affinity): they make authorization *ontology-derived and multi-dimensional* — the wedge vs scalar
  Korosuke and single-gate CogniGraph.
- Consider a **conformal/risk-controlled wrapper** over the level choice (Tayebati-style) to claim per-level
  guarantees the governance-RAG papers lack — strong core move or headline Future Work.
- Reporting a risk–coverage curve **without** an attribution/faithfulness metric is now considered
  incomplete — our dual-axis design already satisfies this.

## Full-text-confirmed differentiation — CogniGraph & SITL (read 2026-07-07)

**The three-position framing (use the competitors' OWN taxonomy — the cleanest wedge).**
SITL states it directly: "Traditional RAG uses KGs for pre-generation context. Instead, SITL repositions
the KG at the end of the pipeline as a formal verification layer." That gives three ways to use a KG in
generation, and GovernRAG occupies the **unfilled third slot**:
1. **KG-before as context** — standard RAG / GraphRAG (improve retrieval recall).
2. **KG-after as verification** — SITL, CogniGraph, HalluGraph (validate/reject the *output*).
3. **KG-as-authorization-gate on the evidence admitted to generation** — **GovernRAG.** The reference
   monitor (Q5) governs *what the model may condition on*, tunable across a strictness spectrum, reported
   as a risk–coverage frontier. Neither pre-generation context nor post-generation verification.

**CogniGraph (Kumar 2026, SSRN 6837300; patent EP26166054.2).** Multi-agent Graph-of-Agents (each KG node
hosts an LLM agent); the SemanticSHACLGate is OWL-aware 3-layer validation (framework fidelity, scope
boundary, cross-reference integrity) that — in the paper's words — "operates one level higher: post-generation,
semantically" on "every agent output," with fixed per-layer thresholds (FFmin/SBmin/XRmin, composite gamma_min).
Metric: Constrained F1 = 0.5*F1_token + 0.5*Governance-Accuracy (0.756 vs 0.328 ungoverned; GA 99.4%);
benchmark MultiGov-30 (EU AI Act/GDPR/DORA/NIS2). Differentiators: (a) it validates the OUTPUT; GovernRAG
governs the ADMITTED evidence; (b) single gate config; GovernRAG is a tunable G0–G4 spectrum with a frontier;
(c) authored SHACL/OWL shapes; GovernRAG's authorization is corpus/ontology-derived (D-manifest + R/M) and
multi-dimensional; (d) multi-agent regulatory reasoning, not RAG over a corpus with source-chunk provenance.
Shared: EU-AI-Act motivation and false-rejection awareness (its 49% false-rejection cut ↔ our recall-loss).
Adopt its Constrained-F1 for comparability, then show the frontier it does not report.

**SITL (Nadimuthu, Das, Soni, Sheth 2026, IEEE Internet Computing).** A terminal / post-generation KG
verification layer: Step 1 user input → Step 2 LLM generation → Step 3 KG verification via semantic
decomposition + triple validation, which "automatically validates or rejects stochastic neural output" by
grounding it into a deterministic ontology (goal: eliminate semantic drift, replace human-in-the-loop).
Differentiators: (a) post-hoc verification; GovernRAG is pre-admission authorization; (b) binary
validate/reject; GovernRAG is a graded, tunable dial with a measured frontier; (c) single deterministic
grounding vs GovernRAG's ontology-conformance as one tunable axis among predicate-authorization and affinity.

**Net (one sentence for the paper):** Where CogniGraph and SITL place a single, fail-closed symbolic gate on
the model's OUTPUT, GovernRAG places a tunable, ontology-derived reference monitor on the EVIDENCE ADMITTED to
generation, and reports the full governance-strictness risk–coverage frontier neither of them characterizes.

## Venue implication
Positioning fits governance/trustworthy-AI venues (FAccT, AIES, AI & Ethics, Big Data & Society) and
IS/DSR (DESRIST, ICIS) — the artifact + design principles + the evaluation instrument are the contribution.

Sources: `Prior Art Literature Review/` — 3 Elicit Researcher reports + full text of CogniGraph
(ssrn-6837300.pdf) and SITL (IEEE Internet Computing), read 2026-07-07.
