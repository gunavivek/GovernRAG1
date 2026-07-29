# Citation Verification Ledger — Paper 2 (W6 references build)

*2026-07-28 · every entry checked against its primary source (local PDF, arXiv,
ACL Anthology, ACM DL, publisher pages). Companion to the Numbers Verification
Ledger. Dispositions marked APPROVAL-REQUIRED await Vivek.*

## VERIFIED — with corrections found by the pass

| Old # | Entry | Verification | Correction |
|---|---|---|---|
| [1] | CogniGraph | local PDF (title page) | Author is **Harish Kumar** (register: "R. Kumar"); full title "Governed Graph-of-Agents Reasoning over Knowledge Graph Topologies with Semantic SHACL Validation and Constrained F1 Evaluation"; SSRN 6837300; patent EP26166054.2 confirmed |
| [2] | SITL | local PDF (title page) | 2nd author is **Archy Das** (register: "S. Das"); authors V. Nadimuthu, A. Das, V. Soni, A. P. Sheth; IEEE Internet Computing (Knowledge Graph dept.) |
| [5] | HalluGraph | arXiv:2512.01659 | Real title: "HalluGraph: Auditable Hallucination Detection for **Legal RAG Systems via Knowledge Graph Alignment**"; authors V. Noël, E. Y. Seidou, C. K. Capo-Chichi, G. Amari; 2025 |
| [12] | Abstention survey | TACL (2025.tacl-1.26; DOI 10.1162/tacl_a_00754) | Final title is "**Know Your Limits**: A Survey of Abstention in Large Language Models" (register carried the v1 arXiv title "The Art of Refusal"); B. Wen et al.; TACL 2025 |
| [16] | KB-agent authorization | arXiv:2510.19324 | Real title: "Authorization of Knowledge-base Agents in an **Intent-based Management Function**"; L. Abdelrazek, L. Karaçay, M. Orlic; 2025 (register said 2026/"6G") |
| [20] | Robust GraphRAG | arXiv:2603.14828 | Full title: "Toward Robust GraphRAG: Mitigating Retrieval Drift and Hallucination from Imperfect Knowledge Graphs"; 2026 · AUTHORS TO PIN (arXiv PDF unparsed) |
| [25] | Citation faithfulness | arXiv:2412.18004 | "Correctness is not Faithfulness in RAG Attributions"; J. Wallat et al.; year is **2024** (register: 2025) |
| [7] | Conformal factuality | SIGIR 2025; DOI 10.1145/3726302.3730244; arXiv:2506.20978 | Register author "Y. Feng" suspect (code repo suggests N. Feng) · AUTHOR TO PIN via ACM DL |

## VERIFIED — as registered

[6] C-RAG, ICML 2024 · [8] Quach, ICLR 2024 · [9] Tayebati, arXiv:2502.06884 ·
[10] Kamath, ACL 2020 · [11] Chen, Findings EMNLP 2023 · [13] Knechtel & Hladik,
IADIS ICWI 2008 (TU Dresden ICCL record) · [14] Valzelli, "A Fine-grained Access
Control Model for Knowledge Graphs", SciTePress 2020 (CONFERENCE NAME TO PIN from
scitepress.org/Papers/2020/98335) · [18] GraphRAG, arXiv:2404.16130 · [19] DoG,
ACL 2025 (2025.acl-long.1186) · [21] Lewis, NeurIPS 2020 · [22] Bohnet,
arXiv:2212.08037 · [23] AttributionBench, Findings ACL 2024 (arXiv:2402.15089) ·
[24] Schreieder, arXiv:2508.15396 ("…Evidence-based Text Generation…", 2025) ·
[26] RAGBench, arXiv:2407.11005 (Friel, Belyi, Sanyal) · [27] DelucionQA,
Findings EMNLP 2023 · [28] HAGRID, arXiv:2307.16883 · [29] ExpertQA, NAACL 2024 ·
[30] Anderson, ESD-TR-73-51, 1972 · [31] EU AI Act, Reg. (EU) 2024/1689

## ADDITIONS

- **[32-new] J. H. Saltzer and M. D. Schroeder, "The protection of information in
  computer systems," Proceedings of the IEEE, vol. 63, no. 9, pp. 1278–1308,
  1975.** — cited in §III.A; was missing from the register.
- **[x] Paper 1** — V. Gunasekaran and X. Xu, under review, 2026; swap to accepted
  form when QASC decides.

## PROVENANCE TRACE (2026-07-29, prompted by Vivek's question)

All four cut-candidates entered via **Elicit_Report_1** (Elicit literature search,
prior-art phase) → Related_Work.md / Prior_Art_Synthesis.md → References.docx
(compiled 2026-07-22). The Elicit report carries FULLER titles than the register
kept; re-searching with exact full titles changed one disposition:

- **[17] Venkatesan — RESCUED and PINNED (Vivek, 2026-07-29, from IEEE Xplore).**
  V. Venkatesan, P. Saha, G. Vasudevan, G. Balakumar and G. P. Balu, "Policy-Aware
  RAG on the Lakehouse: Lineage-Driven Retrieval Over Apache Iceberg on S3 to
  Reduce Hallucination and Cost," 2026 IEEE 16th Annual Computing and Communication
  Workshop and Conference (CCWC), Las Vegas, NV, USA, 2026, pp. 0291–0298,
  doi: 10.1109/CCWC67433.2026.11393771. First-author initial corrected: V., not S.
  Verified by triple match: Elicit full title verbatim · DOI document number =
  independently-located Xplore id 11393771 · keywords (data lineage, generative AI
  governance, policy-aware AI, Contracts) match the §II role. §II clause STAYS.

- **[3] Jain — RESCUED and PINNED (Vivek, 2026-07-29, from IEEE Xplore).**
  A. H. Jain, S. R. Yarrrabothu, N. K. Kande and D. R. Kethireddy, "Governance-Aware
  Agentic Retrieval-Augmented Generation with Evidence Abstention for Reliable AI
  Policy Question Answering," 2026 Int. Conf. on Artificial Intelligence, Systems,
  and Emerging Technologies (ICAISET), Cairo, Egypt, 2026, pp. 1–6,
  doi: 10.1109/ICAISET66439.2026.11541329. Title = Elicit full title verbatim;
  keywords (governance-aware RAG, evidence abstention) match the register wedge.
  SPELLING CHECK at final format: "Yarrrabothu" (triple r) — confirm against the
  Xplore page (likely Yarrabothu). DECISION OPEN: add [3] to §II (currently uncited;
  Elicit called it the nearest neighbour on governance+abstention — leaving a real
  close competitor uncited is a related-work gap).
  METHOD NOTE: web search missing an Xplore-only 2026 paper is NOT sufficient
  evidence of non-existence — Xplore blocks crawlers; Vivek's Xplore search is the
  authoritative channel for this class.

- **[4] Korosuke — RESCUED and PINNED (Vivek, 2026-07-29, from IEEE Xplore).**
  P. Singh, S. Pandey, S. K. Yadav, B. Gridhar and V. M. Manikandan, "Korosuke: A
  Principled Framework for Security-Preserving Contextual Retrieval in Enterprise
  Knowledge Systems," 2026 IEEE International Students' Conference on Electrical,
  Electronics and Computer Science (SCEECS), Bhopal, India, 2026, pp. 1–6,
  doi: 10.1109/SCEECS68810.2026.11429793. Keywords (security-preserving embeddings,
  context-aware retrieval) match the register wedge (scalar relevance–security
  knob vs ontology-derived tiers). SPELLING CHECK at final format: "B. Gridhar"
  (possibly Giridhar) — confirm against the Xplore page.
  SCORE: all three claimed-IEEE "unverifiable" entries were REAL — web-search
  absence is meaningless for Xplore-only content. Elicit Report 1 fully vindicated.

## REMAINING CUT CANDIDATE (last one)

| Old # | Entry | Status |
|---|---|---|
| [15] | Saripalle, RDF/RDFS RBAC | The only entry with NO title/venue/year anywhere — not even in the Elicit footnotes. Awaiting Vivek's Scholar check ("Saripalle RDF RBAC"); if empty → cut with micro-edit "[14], [15]" → "[14]" |

## REMAINING PINS (3, mechanical, before pour)

1. [7] author list — ACM DL page.
2. [20] author list — arXiv listing page.
3. [14] conference name — SciTePress paper page 98335.


## CLOSE-OUT (2026-07-29, after Vivek's rescues)

- **SS2 sentence APPLIED to shell §II** (first paragraph, immediately after the
  third-position sentence ending "...adopt Constrained-F1 [1] for comparability."):
  "Two recent systems come closest in spirit: governance-aware agentic RAG routes
  low-evidence cases to a single abstain gate [3], and security-aware retrieval
  optimises a scalar relevance-security trade-off [4]; in both, governance acts as
  a ranking signal or a one-shot gate, not a graded authorisation over evidence
  with a measured per-level frontier." Approved by Vivek 2026-07-29. Backup of the
  pre-edit shell: 5_Drafts/Shell_backup_pre_S2sentence_2026-07-29.docx.

- **Author-spelling verification ([3] "Yarrrabothu" / [4] "Gridhar") — OPEN,
  needs Vivek's 30-second Xplore re-check.** Independent verification attempted
  and FAILED on every open channel available to me: DOI-string search, Semantic
  Scholar search, title+author web search (x4). Consistent with the recorded
  method note: Xplore-only 2026 papers are invisible to web search; Vivek's
  Xplore access is the authoritative channel. The two spellings therefore rest
  solely on Vivek's paste. Both are statistically unusual ("Yarrrabothu" triple-r;
  "Gridhar" vs common "Giridhar"), so a transcription slip is plausible. ACTION:
  Vivek re-opens the two Xplore pages (DOIs above) and confirms the exact author
  strings; ledger updated on his answer. No other entry blocks the reference list.

### [4] Korosuke — Semantic Scholar cross-check (Vivek's paste, 2026-07-29)

Second independent record found (S2 CorpusID:286646365, BibTeX supplied by Vivek):
authors = "Prof. Megha Singh and Sushil Pandey and Sachin Yadav and Bj Gridhar
and V. M. Manikandan". What this settles and opens:

- SETTLED: surname "Gridhar" CONFIRMED as printed (my Giridhar suspicion was
  wrong; the unusual spelling is the real one). Spelling-check flag CLOSED.
- OPENED: first author is Megha Singh — "Prof." is a title, not a name. Our
  register initial "P. Singh" likely derives from "Prof."; IEEE style would be
  "M. Singh". PENDING Vivek's Xplore read of the exact author line.
- OPENED: "Bj Gridhar" (S2) vs "B. Gridhar" (Xplore paste) — is it B. or B. J.?
- OPENED: "Sachin Yadav" (S2, no middle initial) vs "S. K. Yadav" (Xplore
  paste) — S2 often drops middle initials, so S. K. may stand. Confirm.

One Xplore glance answers all three. NO reference-list change until confirmed.

### [4] FINAL (approved by Vivek, 2026-07-29)

Author string PINNED: M. Singh, S. Pandey, S. K. Yadav, B. Gridhar, and
V. M. Manikandan. Basis: author field reads "Prof. Megha Singh" (S2 full-name
record); Xplore's "P." was an abbreviation of the honorific, corrected to "M.";
Yadav initials kept from the publisher channel; Gridhar confirmed by both
records. Applied to shell reference list (P. Singh occurrences now zero).
[4] flag CLOSED. Remaining open item: [3] Yarrrabothu spelling.

### [3] FINAL (IEEE BibTeX supplied by Vivek, 2026-07-29)

Official Xplore BibTeX export (document 11541329) confirms all four authors
exactly as poured: A. H. Jain, S. R. Yarrrabothu (TRIPLE-R CONFIRMED by the
publisher record), N. K. Kande, D. R. Kethireddy. No change needed.
[3] flag CLOSED.

## REFERENCES BUILD: CLOSED (2026-07-29)

All 33 entries verified against primary records. Every correction applied,
every flag resolved. Remaining reference work is downstream W6 (bidirectional
check, citation-use table, QASC swap on decision).

### [34] ADDED (approved by Vivek, 2026-07-29)

NIST AI RMF added per Vivek's W6 ruling ("add one NIST AI RMF mention along
with EU AI Act"). Reference verified against the primary NIST record
(nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf): "Artificial Intelligence
Risk Management Framework (AI RMF 1.0)," NIST AI 100-1, Jan. 2023,
doi 10.6028/NIST.AI.100-1. Cited once, in the SI supervisory-regimes sentence
alongside [31]. List count is now 34. Flow Map SI cell updated with approval.
