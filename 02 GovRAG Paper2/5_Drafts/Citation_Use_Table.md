# Citation-Use Table — Paper 2 (W6)

*Built 2026-07-29 from the sealed shell (all 34 references verified; ledger:
Citation_Verification_Ledger.md). One row per reference: where it is cited, the
citing sentence (trimmed), the role the citation plays, and how it was verified.
Instrument for Vivek's ownership pass (Aug 10–14). Read-only record — no shell
changes were made in building it.*

**Role legend.** POSITION = places our work among others · WEDGE = carries a
contrast claim our contribution rests on · FOUNDATION = classical concept the
design derives from · LINEAGE = method/metric ancestry · DATA = corpus or
benchmark provenance · MOTIVATION = regulatory/deployment anchor.

| # | Reference (short) | Cited in | Citing sentence (trimmed) | Role | Verified via |
|---|---|---|---|---|---|
| 1 | CogniGraph (Kumar, SSRN 2026) | §II ×2 | "…CogniGraph validates answers through a fail-closed semantic gate and introduces Constrained-F1 [1]" · "…adopt Constrained-F1 [1] for comparability." | WEDGE — closest post-generation competitor AND source of the CF1 metric we adopt; load-bearing for comparability | Local PDF (title page); author H. Kumar corrected |
| 2 | Symbolic-in-the-loop (Nadimuthu et al., IEEE IC 2026) | §II | "symbolic-in-the-loop engineering checks generated content against curated graphs [2]" | POSITION — post-generation verification stream | Local PDF; author A. Das corrected |
| 3 | Governance-aware agentic RAG (Jain et al., ICAISET 2026) | §II | "governance-aware agentic RAG routes low-evidence cases to a single abstain gate [3]" | WEDGE — nearest neighbour on governance+abstention; contrast: one-shot gate vs graded per-level authorisation | IEEE Xplore + official BibTeX (Vivek); "Yarrrabothu" triple-r publisher-confirmed |
| 4 | Korosuke (Singh et al., SCEECS 2026) | §II | "security-aware retrieval optimises a scalar relevance–security trade-off [4]" | WEDGE — nearest neighbour on security-aware retrieval; contrast: scalar knob vs ontology-derived tiers | IEEE Xplore + S2 BibTeX (Vivek); M. Singh approved 2026-07-29 |
| 5 | HalluGraph (Noël et al., 2025) | §II | "HalluGraph audits outputs for entity and relation grounding [5]" | POSITION — post-generation audit stream | arXiv:2512.01659 (real title corrected) |
| 6 | C-RAG (Kang et al., ICML 2024) | §II | "certified generation risk [6]" | POSITION — confidence-dial family; contrast class for the authorisation dial | ICML 2024 proceedings |
| 7 | Conformal factuality (Feng et al., SIGIR 2025) | §II | "conformal factuality [7]" | POSITION — confidence-dial family | ACM DL, doi:10.1145/3726302.3730244; N. Feng pinned |
| 8 | Conformal LM (Quach et al., ICLR 2024) | §II | "conformal language modelling [8]" | POSITION — confidence-dial family | ICLR 2024 proceedings |
| 9 | Learned abstention (Tayebati et al., 2025) | §II | "learned abstention policies [9]" | POSITION — confidence-dial family | arXiv:2502.06884 |
| 10 | Selective QA (Kamath et al., ACL 2020) | §II | "extending selective prediction [10], [11]" | LINEAGE — selective-prediction ancestry of the conformal family | ACL 2020 Anthology |
| 11 | Self-eval selective (Chen et al., EMNLP 2023) | §II | "extending selective prediction [10], [11]" | LINEAGE — selective-prediction ancestry | Findings EMNLP 2023 Anthology |
| 12 | Abstention survey (Wen et al., TACL 2025) | §II | "a recent survey maps the refusal landscape [12]" | LINEAGE — survey grounding the refusal landscape | TACL, doi:10.1162/tacl_a_00754; final title "Know Your Limits" |
| 13 | DL-over-RBAC (Knechtel & Hladik, 2008) | §II | "description-logic reasoning over RBAC hierarchies [13]" | POSITION — KG access-control stream (the wedge: its generation effects are unmeasured) | IADIS ICWI 2008 (TU Dresden ICCL record) |
| 14 | Fine-grained KG access (Valzelli et al., 2020) | §II | "fine-grained triple-level control [14], [15]" | POSITION — KG access-control stream | SECRYPT/ICETE 2020 pp. 595–601 (SciTePress page) |
| 15 | RDF/RDFS+RBAC (Saripalle et al., ICSC 2015) | §II | "fine-grained triple-level control [14], [15]" | POSITION — KG access-control stream | IEEE Xplore (Vivek), doi:10.1109/ICOSC.2015.7050817 |
| 16 | KB-agent authorisation (Abdelrazek et al., 2025) | §II | "dynamic authorisation for knowledge-base agents [16]" | POSITION — KG access-control stream | arXiv:2510.19324 (real title corrected) |
| 17 | Policy-aware lakehouse RAG (Venkatesan et al., CCWC 2026) | §II | "policy-aware retrieval over governed lakehouses [17]" | POSITION — nearest infrastructure neighbour in the access-control stream | IEEE Xplore (Vivek), doi:10.1109/CCWC67433.2026.11393771; triple-match verified |
| 18 | GraphRAG (Edge et al., 2024) | §II | "GraphRAG builds community summaries over an entity graph [18]" | POSITION — KG-before-generation stream | arXiv:2404.16130 |
| 19 | DoG (Li et al., ACL 2025) | §II | "DoG decodes along graph paths [19]" | POSITION — KG-before-generation stream | ACL 2025 Anthology (2025.acl-long.1186) |
| 20 | Robust GraphRAG (Ma et al., 2026) | §II | "robustness variants harden the pattern [20]" | POSITION — KG-before-generation stream | arXiv:2603.14828; authors pinned from listing |
| 21 | RAG (Lewis et al., NeurIPS 2020) | §II | "all extending the retrieve-then-generate paradigm [21]" | FOUNDATION — the paradigm every stream extends | NeurIPS 2020 proceedings |
| 22 | Attributed QA (Bohnet et al., 2022) | §II | "attributed question answering [22]" | LINEAGE — attribution measurement vocabulary | arXiv:2212.08037 |
| 23 | AttributionBench (Li et al., ACL 2024) | §II | "attribution benchmarks [23], [24]" | LINEAGE — attribution benchmarks | Findings ACL 2024 (arXiv:2402.15089) |
| 24 | Attribution survey (Schreieder et al., 2025) | §II | "attribution benchmarks [23], [24]" | LINEAGE — attribution survey | arXiv:2508.15396 |
| 25 | Correctness ≠ faithfulness (Wallat et al., 2024) | §II | "citation faithfulness — whether cited evidence is genuinely relied upon [25]" | WEDGE — motivates extending citation presence to decision-level reconstructability | arXiv:2412.18004; year corrected to 2024 |
| 26 | RAGBench (Friel et al., 2024) | §IV.B | "three corpora from RAGBench [26], chosen for complementary unanswerable strata" | DATA — source benchmark suite | arXiv:2407.11005 |
| 27 | DelucionQA (Sadat et al., 2023) | §IV.B | "DelucionQA [27] (automotive troubleshooting; … 912 questions, … 7.0% unanswerable)" | DATA — corpus 1 | Findings EMNLP 2023 Anthology |
| 28 | HAGRID (Kamalloo et al., 2023) | §IV.B | "HAGRID [28] (attributable …)" | DATA — corpus 2 | arXiv:2307.16883 |
| 29 | ExpertQA (Malaviya et al., NAACL 2024) | §IV.B | "ExpertQA [29] (expert-curated …)" | DATA — corpus 3 | NAACL 2024 Anthology |
| 30 | Anderson report (1972) | §II · §III | "under the classical reference-monitor concept [30]" · "a Reference Monitor in the classical operating-systems sense [30], [32]" | FOUNDATION — the design's central concept; load-bearing in both positioning and system sections | ESD-TR-73-51 (U.S. Air Force technical report) |
| 31 | EU AI Act (2024) | §I | "horizontal frameworks such as the EU AI Act [31] and the NIST AI Risk Management Framework [34] — ask for records that an ungoverned RAG pipeline does not keep" | MOTIVATION — regulatory anchor; also named in the TPS CFP | Regulation (EU) 2024/1689 (EUR-Lex) |
| 32 | Saltzer–Schroeder (1975) | §III | "a Reference Monitor in the classical operating-systems sense [30], [32] — it mediates every access …" | FOUNDATION — complete-mediation principle behind Q5/Q6 | Proc. IEEE vol. 63 no. 9 |
| 33 | GovernRAG architecture (anonymous, under review) | §II | "The GovernRAG architecture itself was introduced by the architecture paper [33], demonstrated on ten cases; the present study contributes its first benchmark-scale evaluation." | POSITION — system provenance; keeps the Paper-1/Paper-2 separation (architecture credited there, evaluation claimed here) | Own manuscript; ANONYMOUS under review — swap to named form on QASC decision |
| 34 | NIST AI RMF 1.0 (NIST AI 100-1, 2023) | §I | "horizontal frameworks such as the EU AI Act [31] and the NIST AI Risk Management Framework [34] — ask for records …" | MOTIVATION — second regulatory anchor; named in the TPS CFP | NIST primary record, doi:10.6028/NIST.AI.100-1 (verified 2026-07-29) |

## Ownership-pass notes

1. The load-bearing rows are 1, 3, 4, 25, 26–29, 30, 33 — these carry claims a
   reviewer may probe. Each contrast claim ([1] single-operating-point, [3]
   one-shot gate, [4] scalar trade-off) is grounded in the cited paper's own
   abstract/keywords per the ledger.
2. Four entries ([3], [4], [15], [17]) are Xplore-only records invisible to web
   search; the verification channel is Vivek's Xplore access, recorded per
   entry in the ledger.
3. [33] is the only entry with pending action: swap to the named citation when
   the QASC decision lands.
4. Every reference (34 after the approved NIST addition) is cited at least once and every bracket resolves —
   bidirectional check passed 2026-07-29 (re-run after [34]: 34/34 both directions).
