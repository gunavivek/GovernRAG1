*W5 --- §II + §I + §VIII draft v1 for review · 28 July 2026 · not yet poured · citations \[n\] per References.docx numbering; Paper 1 cited once as under review per locked guide (QASC decision expected this week --- swap at W6 if accepted)*

**II. RELATED WORK**

Knowledge graphs serve RAG systems at two established positions. Before generation, they enrich retrieval context: GraphRAG builds community summaries over an entity graph \[18\], DoG decodes along graph paths \[19\], and robustness variants harden the pattern \[20\], all extending the retrieve-then-generate paradigm \[21\]. After generation, they verify outputs: CogniGraph validates answers through a fail-closed semantic gate and introduces Constrained-F1 \[1\]; symbolic-in-the-loop engineering checks generated content against curated graphs \[2\]; HalluGraph audits outputs for entity and relation grounding \[5\]. This paper\'s system occupies a third position: the graph derives an authorisation layer that decides, before generation, which retrieved evidence the model may use. The GovernRAG architecture itself was introduced by Gunasekaran and Xu \[x --- under review\], demonstrated on ten cases; the present study contributes its first benchmark-scale evaluation. Post-generation validators report single operating points; we report the per-level frontier such points sit on, and adopt Constrained-F1 \[1\] for comparability.

A second stream makes abstention adaptive. Conformal methods calibrate when a model should refuse --- certified generation risk \[6\], conformal factuality \[7\], conformal language modelling \[8\], and learned abstention policies \[9\] --- extending selective prediction \[10\], \[11\]; a recent survey maps the refusal landscape \[12\]. These systems turn a confidence dial: abstention follows the model\'s estimated uncertainty. GovernRAG turns an authorisation dial: abstention follows declared policy about evidence, independent of model confidence. The two are complementary --- a conformal wrapper over a governed pipeline is future work --- but they answer different deployment questions: how sure is the model, versus what is the model allowed to rest an answer on.

A third stream governs knowledge-graph access itself: description-logic reasoning over RBAC hierarchies \[13\], fine-grained triple-level control \[14\], \[15\], dynamic authorisation for knowledge-base agents \[16\], and policy-aware retrieval over governed lakehouses \[17\]. This machinery restricts who may read which triples, but its effect on generation behaviour --- coverage, refusal quality, faithfulness --- has not been measured. Connecting authorisation decisions to measured generation outcomes is precisely this study\'s contribution. Attribution research supplies the measurement vocabulary: attributed question answering \[22\], attribution benchmarks \[23\], \[24\], and citation faithfulness --- whether cited evidence is genuinely relied upon \[25\]. Our audit-trail metrics extend this line from citation presence to decision-level reconstructability, under the classical reference-monitor concept \[30\].

**I. INTRODUCTION**

Enterprises deploying retrieval-augmented generation face a question that neither better retrieval nor output checking answers: what is the model allowed to base its answer on? In regulated settings the question is concrete. Supervisory regimes --- financial-services rules that require firms to evidence how a decision was reached, and horizontal frameworks such as the EU AI Act \[31\] --- ask for records that an ungoverned RAG pipeline does not keep: which sources were permitted, which were excluded, under which rule, and why the system answered at all. An ungoverned pipeline retrieves by similarity, generates from whatever was retrieved, and refuses only when the model happens to feel unsure. Its refusal behaviour is an accident of confidence, and its audit trail begins only after the answer exists.

GovernRAG makes evidence use a governed decision. A reference monitor, derived from a domain ontology, authorises or drops each retrieved evidence item before generation, logs every decision, and enforces an answer gate: answer with citations from admitted evidence, or refuse. Strictness is set by a five-level governance dial, G0 to G4, so refusal behaviour follows declared policy rather than model confidence. The architecture was introduced and demonstrated at case scale; what has been missing is the measurement --- what each notch of the dial buys and costs at benchmark scale. That measurement is this paper.

We evaluate GovernRAG in a pre-registered study across three public benchmarks with complementary unanswerable strata --- 1,225 questions under nine configurations, 11,025 judged pairs, of which 8,208 were additionally re-judged by a second judge. This paper makes three contributions:

> • The first benchmark-scale characterisation of evidence-authorization governance: the complete risk--coverage frontier across governance levels, on three corpora spanning answer-heavy to abstention-heavy regimes.
>
> • An evaluation methodology for governed RAG: pre-registered hypotheses with a public deviation log, a refusal-quality metric triad alongside faithfulness and auditability, and a dual-judge robustness protocol.
>
> • An exploratory observation connecting build-time ontology fit to the frontier\'s shape: the aligned concept share, known before any question is served, anticipated how far the dial could usefully turn.

The headline results: turning the dial to the grounded tier roughly doubles the correct-refusal rate (from 41--44% to 75--78%) at a measured coverage cost; on the abstention-heavy corpus, governance beats the ungoverned baseline outright; citation resolvability is 97.7--100% with complete decision logs; and the whole evaluation ran for under \$800 on commodity APIs. Two pre-registered hypotheses did not survive: faithfulness was already at ceiling in both arms, and full quality parity on answered questions held only on the in-ontology corpus. We report both plainly.

The remainder of this paper is organised as follows. Section II positions the work among governed and abstaining RAG systems. Section III describes the GovernRAG system. Section IV presents the evaluation design. Section V reports results; Section VI discusses operating points, economics, and fit; Section VII states threats to validity and reproducibility; Section VIII concludes.

**VIII. CONCLUSION**

GovernRAG makes the evidence a language model may use a governed, logged decision, tunable over five levels. Its benchmark-scale evaluation shows what governance buys and costs: near-free citation discipline and audit trails at G1; roughly doubled correct refusal at the grounded tier, paid for in coverage; an outright win over the ungoverned baseline where abstention matters; and decision-level auditability of 97.7--100% throughout. Build-time ontology fit anticipated how far the dial could turn on each corpus --- an exploratory signal with a pre-registered out-of-sample test as future work, alongside a conformal wrapper composing the confidence dial with the authorisation dial, a triplet-level citation tag, and evaluation under open-corpus retrieval.

**Reviewer notes (not part of the manuscript)**

-- Lengths: §II \~460 words ≈ 0.75 pp · §I \~560 words + 3 bullets ≈ 1.0 pp · §VIII \~120 words ≈ 0.2 pp --- all inside budget.

-- Citations use References.docx numbering \[1\]--\[31\]; \[x\] = Paper 1 (under review, per your QASC ruling; swap to accepted form at W6 if the decision lands). Missing from register: Saltzer--Schroeder (cited in §III.A) --- needs adding as \[32\] at W6.

-- §I hook follows the approved VI.A regulated-enterprise pivot (FINRA/SEC generalised to \'financial-services rules\' + EU AI Act \[31\] as the citable anchor --- FINRA/SEC named in VI.A, not duplicated here).

-- Contributions claim ONLY the evaluation (frontier, methodology, exploratory observation) --- the architecture is credited to the cited prior work, preserving the Paper-1/Paper-2 separation.

-- Headline-results paragraph includes the two failed hypotheses deliberately (integrity-forward framing).

-- Abstract final pass NOT included in this draft --- one open ruling first: the abstract uses American spellings (authorization, behavior) while §I--§VIII use British (authorisation, behaviour). One convention must win. Recommend British throughout per the locked voice guide; the abstract keeps \'evidence authorization\' as a TERM only if you prefer the term anchored to US spelling. Your ruling applies at W6.

-- Double-blind note: citing Paper 1 by author name in third person is standard; if QASC acceptance arrives before Aug 15, the citation becomes verifiable, which is strictly better.
