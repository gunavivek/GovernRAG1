**KG / neuro-symbolic faithfulness:**

Review knowledge-graph-grounded and neuro-symbolic retrieval-augmented generation (including GraphRAG). How is faithfulness/attribution enforced and measured, and has any work used symbolic authorization (allowed predicates or ontology conformance) as a governance mechanism to gate or abstain from generation, rather than to improve retrieval recall?

The KG-RAG / neuro-symbolic literature clusters around two moves — using graph structure to *improve* retrieval, and using graph structure to *check* generation. The governance-style question you're asking — whether allowed-predicate or ontology-conformance checks are ever used as an *authorization gate* (fail-closed abstention) rather than as a recall-boosting retriever — is answered "yes, but only in a small and very recent slice of the work."

**How faithfulness is enforced in KG/GraphRAG**

Most Graph-RAG systems still treat the KG as a smarter *retriever*: subgraph retrieval, path-guided prompting, or graph-aware constrained decoding to keep generation on well-formed KG chains rather than free text. DoG (Decoding on Graphs) is the canonical example — it constrains decoding so outputs are sequences of interrelated triplets grounded on the KG, arguing "well-formed chains" are the principled unit of faithful KGQA reasoning [^1]. C2RAG adds constraint-checked retrieval (decomposing queries into atomic constraint triples) plus an explicit *sufficiency check* that decides whether current evidence justifies structural propagation, otherwise falling back to text — a soft abstention over the graph [^2].

A parallel track puts the KG *after* generation as a verification layer rather than before it as context. HalluGraph extracts KGs from context, query, and response and quantifies hallucination via structural alignment — Entity Grounding (are response entities in the sources?) and Relation Preservation (are asserted relations supported?) — producing bounded, auditable scores with full audit trails from assertions back to source passages [^3]. Sheth and colleagues generalize this as "Symbolic-in-the-Loop" (SITL): traditional RAG uses KGs for pre-generation context, but SITL *repositions the KG at the end of the pipeline as a formal verification layer*, grounding probabilistic output into a deterministic ontology and, they report, eliminating semantic drift [^4]. GraphRAG-specific hallucination detectors like GGA use interpretability signals (Path Reliance Degree, Semantic Alignment Score) to flag when the model has drifted from the linearized subgraph [^5].

**How faithfulness/attribution is measured**

The measurement literature has recently split "cited-and-correct" from "cited-and-actually-relied-upon." Wallat et al. introduce *citation faithfulness* — whether the model's reliance on cited documents is genuine rather than post-rationalized — and find up to 57% of RAG citations fail this stricter test even when they support the statement [^6]. KG-SMILE gives a perturbation-based, component-level attribution method specifically for Graph-RAG, identifying which graph entities and relations most influence a generated answer and scoring outputs on fidelity, faithfulness, consistency, stability, and accuracy [^7]. CAQA takes the opposite direction — using KGs to *auto-generate* attribution benchmarks with fine-grained attribution categories that current LLM judges are then tested on [^8].

**Symbolic authorization as a governance gate — the specific question**

This is where the literature is thinnest, but there is a clear, very recent thread that does exactly what you're describing: use symbolic/ontology conformance not to improve retrieval, but as an *authorization check* on generation, with rejection as the default action.

- **CogniGraph (2026)** is the closest fit to "symbolic authorization." It puts a *SemanticSHACLGate* on every agent output, enforcing three-layer semantic validation — framework fidelity, scope boundary, and cross-reference integrity — and it is explicitly framed as the mechanism to supply "governance guarantees that the EU AI Act mandates." On MultiGov-30 (AI Act, GDPR, DORA, NIS2), it reports 99.4% governance accuracy — 100% framework fidelity, 100% scope adherence, 98.3% cross-reference integrity — while more than doubling a "Constrained F1" score that penalizes governance violations against an ungoverned Claude baseline (0.756 vs 0.328).[^9] They also show that moving from format-based to *semantic* SHACL validation eliminated 49% of false rejections of correct answers, which speaks directly to the fail-closed-vs-usable tradeoff you'd worry about with an authorization gate [^9].

- **Ontology-to-tools compilation (World Avatar, 2026)** enforces conformance *during* generation rather than after: ontological specifications are compiled into executable tool interfaces that LLM agents "must use" to create or modify KG instances, so an ontology violation is not something the model can emit — it isn't in the tool's action space [^10]. This is the strongest form of allowed-predicate authorization: the predicates the agent is permitted to assert are literally the ontology's compiled interface.

- **R2-Guard (2024)** encodes safety-category knowledge as first-order logical rules embedded in a probabilistic graphical model (Markov logic networks / probabilistic circuits) and routes data-driven per-category unsafety probabilities through that symbolic reasoner for the final gating decision [^11]. It's a safety guardrail rather than a domain-ontology governance layer, but architecturally it's the same pattern: symbolic rules as the authorization arbiter, neural models as evidence.

- **MedRule-KG (2025)** and adjacent "constrained-inference" work sit between improvement and gating: they inject curated symbolic facts and then run a deterministic rule-satisfaction checker, formalizing generation as constrained inference. Reported effect is an 83.2% reduction in domain-rule violations vs. chain-of-thought [^12]. The verifier is deterministic and rejection-capable, but the paper frames it primarily as violation-reduction rather than as an abstention regime.

- **SITL (above)** is essentially a fail-closed symbolic verifier on the output side — the paper's framing is that outputs are only released once grounded into the deterministic ontology [^4].

**Where the gap is**

Two things are notably underdeveloped for your framing. First, most "improve KG-RAG" work still treats the KG as retrieval augmentation and evaluates on QA accuracy, not on rejection quality — even C2RAG's sufficiency check is framed as *fallback to text*, not as principled abstention [^2]. Second, almost nothing outside CogniGraph reports the governance-relevant metric pair — how often the gate refused, how often it refused *correctly*, and what the correct-answer false-rejection rate is. The 49% false-rejection reduction between format-SHACL and semantic-SHACL in CogniGraph is one of the only numbers in the corpus that even lets you reason about a gate's precision as a governance instrument [^9]. If your paper's argument is that ontology conformance / allowed-predicate checks should be a first-class governance primitive with abstention semantics, the strongest positive precedents are CogniGraph and SITL; the strongest evidence of the surrounding gap is that (a) faithfulness work like HalluGraph produces auditable scores but stops short of a policy for what to do with a low score, and (b) attribution work (Wallat et al., KG-SMILE, CAQA) is oriented toward measurement rather than enforcement.

I searched primarily paper indices; a small handful of the most relevant items (CogniGraph, SITL, ontology-to-tools) are very recent 2026 preprints, so this thread is still consolidating. If you want, I can pull full text on the SHACL/SITL/ontology-tools papers to extract exact gate semantics and abstention rules for the paper.

[^1]: Li et al., 2025. Decoding on Graphs: Faithful and Sound Reasoning on Knowledge Graphs through Generation of Well-Formed Chains. Annual Meeting of the Association for Computational Linguistics.

[^2]: Ma et al., 2026. Toward Robust GraphRAG: Mitigating Retrieval Drift and Hallucination from Imperfect Knowledge Graphs.

[^3]: Noël et al., 2025. HalluGraph: Auditable Hallucination Detection for Legal RAG Systems via Knowledge Graph Alignment. arXiv.org.

[^4]: Nadimuthu et al., 2026. Symbolic-in-the-Loop: Leveraging Knowledge Graph Engineering to Ensure High-Assurance Generative Artificial Intelligence Outcomes. IEEE Internet Computing.

[^5]: Li et al., 2025. Detecting Hallucinations in Graph Retrieval-Augmented Generation via Attention Patterns and Semantic Alignment. arXiv.org.

[^6]: Wallat et al., 2025. Correctness is not Faithfulness in Retrieval Augmented Generation Attributions. International Conference on the Theory of Information Retrieval.

[^7]: Moghaddam et al., 2025. Explainable Knowledge Graph Retrieval-Augmented Generation (KG-RAG) with KG-SMILE. arXiv.org.

[^8]: Hu et al., 2024. Can LLMs Evaluate Complex Attribution in QA? Automatic Benchmarking using Knowledge Graphs. Annual Meeting of the Association for Computational Linguistics.

[^9]: Kumar, 2026. CogniGraph: Governed Graph-of-Agents Reasoning over Knowledge Graph Topologies with Semantic SHACL Validation and Constrained F1 Evaluation. Social Science Research Network.

[^10]: Zhou et al., 2026. Ontology-to-tools compilation for executable semantic constraint enforcement in LLM agents. arXiv.org.

[^11]: Kang & Li, 2024. R2-Guard: Robust Reasoning Enabled LLM Guardrail via Knowledge-Enhanced Logical Reasoning. arXiv.org.

[^12]: Su, 2025. MedRule-KG: A Knowledge-Graph--Steered Scaffold for Reliable Mathematical and Biomedical Reasoning.