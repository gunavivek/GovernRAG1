*W1 --- §III APPROVED v6 (III.A--III.D all reviewed by Vivek 2026-07-26) · 25 July 2026 · v2: §III.A rulings (D amended; M = modelling pipeline; build-once rationale). v3: §III.B restructured (reference ontology opens the subsection; record defined; manifest forward-binding; BIZBOK detail deferred to §IV; classical reference-monitor citations added in III.A). v4: bridge-discovery corrections 1--4 approved and applied --- M stages stated as executed (no bridge discovery); Q3.5/Q3.6 omitted from the manuscript; spine erratum S37 queued; dictionary amended. v5: III.B manifest-consumption sentence corrected per code verification (D5 consumed at M1, Q1, Q5); D5→Q1 edge added; Figure 1 (GovernRAG_Architecture_Simple Master) fully aligned. v6: III.C admissibility/sufficiency prose applied; III.D approved as written.*

*Voice: fresh-written, no Paper-1 text; British spellings per the locked guide; every technical statement traceable to spine v2.0 §5 / Governance_Spectrum_Design.*

**III. THE GOVERNRAG SYSTEM**

***A. Design position***

GovernRAG rests on a single architectural commitment: the decision of which retrieved evidence a language model may condition on is made by a dedicated enforcement component, not by retrieval ranking and not by the model itself. The component is a Reference Monitor in the classical operating-systems sense \[Anderson; Saltzer--Schroeder --- refs resolved at W6\] --- it mediates every access of the generator to evidence, it cannot be bypassed while governance is active, and it logs every decision it takes. What distinguishes GovernRAG\'s monitor is its origin: its authorisation rules are derived from a reference ontology, so that what counts as admissible evidence is defined by an explicit domain vocabulary rather than by similarity scores.

The system comprises four pipelines (Fig. 1). A reference ontology (R) supplies the domain vocabulary. A governance-definition pipeline (D) compiles governance policy together with domain-specific data into a per-record Governance Manifest. A modelling pipeline (M) constructs a governed index from the corpus. A query pipeline (Q) serves questions under a selected governance level. The build/serve split mirrors how documents are used in an enterprise --- a document is written once and queried many times, not written to answer a single question --- so governance work that depends only on the corpus is paid once at build time, and each query pays only the marginal cost of authorisation and synthesis; Section VI quantifies this economy.

***B. Reference ontology and the Governance Manifest***

Authority in GovernRAG originates in the reference ontology: an explicit, documented domain vocabulary from which every authorisation rule is derived. Governance is applied per record --- a record being one source document, the atomic unit of governance --- so that what a record\'s evidence may support is fixed by policy before any question arrives. The architecture is ontology-agnostic; the instantiation used in our evaluation (an enterprise reference vocabulary of 553 concepts derived from BIZBOK) is treated as an experimental condition in Section IV.

The governance-definition pipeline terminates in the Governance Manifest (D5), a machine-readable policy artefact produced per record and bound forward through every downstream stage --- the manifest travels with the record. It carries three elements: the authorised predicates for the record, the ontology rules in force, and a domain-affinity specification. It is the single point of policy definition, and it is enforced wherever evidence is handled: the modelling pipeline consumes it when constructing the governed index; at serve time the query pipeline consumes it twice --- at intent gating, where the manifest\'s domain profiles and authorised predicates scope what retrieval may seek, and at the Reference Monitor, which audits every candidate evidence item against it before admission. A policy change is therefore made in one place and enforced at every stage that touches evidence.

***C. Build and query pipelines***

The modelling pipeline (M1--M5) performs governed chunking, concept and triple extraction, concept-graph construction, alignment of extracted concepts against the reference ontology, and graph embedding with assembly of the governed index. Alignment at M4 is the step that later gives governance its selectivity: each extracted concept is either matched to the ontology or recorded as unmatched, and this alignment status travels with the evidence into the index.

At serve time the query pipeline runs intent gating, signature extraction, governed graph retrieval, and residual retrieval, producing candidate evidence for the question. The Q5 Reference Monitor then examines each candidate under the manifest and the active governance level, admitting or dropping it and writing one log entry per decision --- the evidence item, the rule applied, and the outcome. Q6 cited synthesis enforces the level\'s answer gate on the admitted evidence: the model answers with citations drawn only from admitted evidence, or the system refuses. The gate is fail-closed --- when admitted evidence does not satisfy the active level\'s requirement, refusal is the designed outcome, not an error state. The two stages separate concerns that single-gate designs merge. Q5 rules on admissibility, item by item: one admit-or-drop decision per candidate, each logged with its rule, producing the admitted set. Q6 rules on sufficiency, once per question: whether the admitted set satisfies the active level\'s answer requirement. The distinction is visible when the dial turns: the same admitted evidence that suffices at G2 may fail G3\'s requirement, flipping the outcome from cited answer to governed refusal without any change in what was admitted. From the logs alone, an auditor can reconstruct which evidence was admitted, which was dropped and under which rule, and which citations support each answer, without re-running the system.

***D. Governance levels and axis variants***

Strictness is set by a governance level, chosen per deployment as a matter of policy. Five levels are defined, and they nest: each level retains every constraint of the level below and adds one. G0 (naive) bypasses the query pipeline entirely --- retrieval passes straight to the model --- and serves as the ungoverned baseline; because G0 differs from the governed levels only in the bypass, measured differences are attributable to governance rather than to the serving model or retrieval. G1 (Cited) requires at least one retrieved chunk and a citation in the answer. G2 (Grounded) requires at least one authorised chunk --- a chunk that passes the monitor\'s predicate filter --- together with the citation requirement. G3 (Strict) requires at least one authorised symbolic triplet. G4 (Corroborated) requires multiple authorised triplets, or one triplet supported by an independent agreeing authorised chunk. Under this construction the refusal behaviour of the system follows the declared policy: turning the dial from G1 to G4 only ever tightens what evidence may be used and what an answer must rest on.

Within a level, two ontology-derived axis variants filter the admitted evidence further: ontology conformance restricts triplets by their alignment status against the reference ontology, and domain affinity restricts chunks by a domain-affinity score. The levels and the two axes together define the configuration space evaluated in this study --- nine configurations per question (Section IV). Whether the axes can be exercised at all proved to be a property of the corpus, a finding reported in Section V.

*\[Figure 1 near §III.A --- architecture, exported from 3_Figures\\GovernRAG_Architecture_Simple Master.pptx (diagram frame only, defence footer cropped): R+D pipeline, build-time M pipeline, D5 feeding M1, Q1 and Q5, serve-time Q pipeline with the Q5 monitor and Q6 answer gate.\]*

**Reviewer notes (not part of the manuscript)**

-- Length: \~870 words ≈ 1.45 pp two-column with Figure 1 --- inside the 1.5 pp budget.

-- Every level definition, pipeline name, and the 553-concept instantiation checked against spine v2.0 §5 verbatim semantics; no Paper-1 sentences reused.

-- Term discipline: Reference Monitor, Governance Manifest, governance level, admitted evidence, authorised chunk --- one term each, throughout.

-- The empty-evidence refusal state is stated here only as the fail-closed principle; its operational definition (questions whose admitted evidence yields no triplets) stays in §IV to avoid duplication.

-- Open item for the final pass: the shell\'s abstract uses American spellings (authorization, behavior) while the locked voice guide mandates British (authorised, behaviour). One convention must win at W6 --- flagging now, no action taken.

-- Figure 1 export from GovernRAG_Architecture_Simple Master.pptx (frame only) happens at manuscript assembly (W6).
