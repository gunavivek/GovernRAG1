# Paper 2 — Working Bibliography (IEEE numbered)
*Compiled 2026-07-22 from Related_Work.md, Prior_Art_Synthesis.md, and the prior-art
library (2_Prior_Art\). Entries marked ⚠ need final bibliographic verification (page
numbers / exact venue / DOI) at TPS extraction. "WEDGE" = our one-line differentiation,
for use while writing §2 and rebuttals.*

## A. Direct competitors (cite AND differentiate)

[1] R. Kumar, "CogniGraph: Governed graph-of-agents with Semantic SHACL validation and Constrained F1," SSRN preprint 6837300, 2026. (Patent EP26166054.2.) ⚠
    WEDGE: single fail-closed SemanticSHACL gate on the OUTPUT, fixed thresholds, one operating point; GovernRAG governs ADMITTED EVIDENCE across a tunable G0–G4 spectrum and reports the full frontier. Adopt its Constrained-F1 for comparability. PDF: 2_Prior_Art\CogniGraph_Kumar2026_SSRN-6837300.pdf

[2] V. Nadimuthu, S. Das, A. Soni, and A. Sheth, "Symbolic-in-the-loop: Leveraging knowledge graph engineering to ensure high-assurance generative AI outcomes," IEEE Internet Computing, 2026. ⚠
    WEDGE: post-hoc KG verification of output, binary validate/reject; GovernRAG is pre-admission authorization, graded, with a measured frontier. Source of the three-position taxonomy. PDF: 2_Prior_Art\SITL_Nadimuthu2026_IEEE-Internet-Computing.pdf

[3] A. Jain et al., "Governance-aware agentic RAG with evidence abstention," Proc. ICAISET, 2026. ⚠
    WEDGE: governance as reranking feature + one answerable/abstain gate; no KG substrate, no dial.

[4] P. Singh et al., "Korosuke: Hierarchical security-aware retrieval," Proc. IEEE SCEECS, 2026. ⚠
    WEDGE: scalar relevance–security utility knob; GovernRAG has ontology-derived tiers with per-level faithfulness.

[5] L. Noël et al., "HalluGraph: Auditing LLM outputs against knowledge graphs," arXiv preprint, 2025. ⚠
    WEDGE: a detector (entity grounding / relation preservation), no abstention policy.

## B. Conformal / selective prediction (position AGAINST: their dial is confidence, ours is authorization)

[6] M. Kang et al., "C-RAG: Certified generation risks for retrieval-augmented language models," Proc. ICML, 2024. ⚠
[7] Y. Feng et al., "Response quality assessment for RAG via conditional conformal factuality," Proc. SIGIR, 2025. ⚠
[8] V. Quach et al., "Conformal language modeling," Proc. ICLR, 2024. ⚠ (paper circulated 2023)
[9] S. Tayebati et al., "Learning conformal abstention policies for adaptive risk management," arXiv preprint, 2025. ⚠ — template for the conformal-wrapper Future Work (§9).
[10] A. Kamath, R. Jia, and P. Liang, "Selective question answering under domain shift," Proc. ACL, 2020.
[11] J. Chen et al., "Adaptation with self-evaluation to improve selective prediction in LLMs," Findings of EMNLP, 2023. ⚠
[12] Y. Wen et al., "The art of refusal: A survey of abstention in large language models," arXiv preprint, 2024. ⚠

## C. Ontology/KG-derived authorization (machinery exists; never connected to generation behavior)

[13] M. Knechtel and J. Hladik, "RBAC authorization decision with DL reasoning," Proc. ICWI, 2008. ⚠ (RBAC-CH)
[14] M. Valzelli et al., "Fine-grained access control for knowledge graphs," 2020. ⚠
[15] R. Saripalle et al., RDF/RDFS-based RBAC. ⚠ (locate exact cite at extraction)
[16] M. Abdelrazek et al., "Dynamic authorization for knowledge-base agents in 6G," 2026. ⚠ — triple-level RBAC, no coverage/faithfulness link.
[17] S. Venkatesan et al., "Policy-aware RAG on the lakehouse," 2026. ⚠ — lineage/data-contract enforcement.

## D. KG-RAG / neuro-symbolic (KG-before context vs KG-after verification)

[18] D. Edge et al., "From local to global: A graph RAG approach to query-focused summarization," arXiv:2404.16130, 2024. (GraphRAG)
[19] K. Li et al., "Decoding on graphs (DoG)," Proc. ACL, 2025. ⚠
[20] J. Ma et al., "Toward robust GraphRAG (C2RAG)," 2026. ⚠
[21] P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," Proc. NeurIPS, 2020.

## E. Attribution / faithfulness measurement

[22] B. Bohnet et al., "Attributed question answering: Evaluation and modeling for attributed large language models," arXiv:2212.08037, 2022.
[23] Y. Li et al., "AttributionBench," Findings of ACL, 2024. ⚠
[24] T. Schreieder et al., "Attribution, citation, and quotation: A survey," arXiv preprint, 2025. ⚠
[25] J. Wallat et al., citation faithfulness (cited AND relied upon), 2025. ⚠ — source of the "citation faithfulness" handle.

## F. Benchmarks & datasets (Paper 2 corpora)

[26] R. Friel, M. Belyi, and A. Sanyal, "RAGBench: Explainable benchmark for retrieval-augmented generation systems," arXiv:2407.11005, 2024. — source of all three corpora + TRACe gold annotations. ⚠ verify author order
[27] M. Sadat et al., "DelucionQA: Detecting hallucinations in domain-specific question answering," Findings of EMNLP, 2023. — Run 1, full 912-question benchmark.
[28] E. Kamalloo et al., "HAGRID: A human-LLM collaborative dataset for generative information-seeking with attribution," arXiv:2307.16883, 2023. — Run 2 (K=150 selection, 163 q).
[29] C. Malaviya et al., "ExpertQA: Expert-curated questions and attributed answers," Proc. NAACL, 2024. — Run 3 (K=150 selection, 150 q).

## G. Governance framing / reference monitor

[30] J. P. Anderson, "Computer security technology planning study," ESD-TR-73-51, USAF, 1972. — origin of the reference-monitor concept (Q5 = our reference monitor).
[31] EU Artificial Intelligence Act, Regulation (EU) 2024/1689. ⚠ — shared motivation with CogniGraph; cite the regulation, not press coverage.

---
*Count: 31 working entries. Sections A–B are the argumentative core of §2; F is mandatory
for Methods; G anchors terminology. Before TPS submission: resolve every ⚠ against the
publisher page (not Google Scholar scrape), add DOIs, and convert to the IEEE .bst/venue
format. Vivek's Zotero (home dir \Zotero) can ingest this list if preferred.*
