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

## 1. Introduction — CORE-S1 · CORE-S2 · EXT
The governance gap in RAG; research questions; contributions of the program. SOURCED
(Paper 1 §1, adapt) + DRAFT (Paper-2 contributions paragraph from Analysis_CrossRun §5).

## 2. Related work — CORE-S1(compressed) · CORE-S2 · EXT
SOURCED (Paper 1 §2, incl. §2.7 comparison artifact) + DRAFT: 2026 governance-RAG delta
(CogniGraph, Jain et al., Korosuke — single-operating-point vs our frontier) ← Sprint 7C-1
output when done. OKF: ONE interop paragraph (3_Positioning/Positioning_relative_to_OKF.md).

## 3. The GovernRAG framework [Part 1] — CORE-S2 · CORE-KG · EXT
- 3.1 Governance-manifest architecture; reference-monitor mediation. SOURCED (Paper 1 §4).
- 3.2 R/D pipelines: reference ontology, domain governance profiles. SOURCED (Paper 1 §4 + repo).
- 3.3 M pipeline: concept-graph construction, BIZBOK alignment (M4). SOURCED.
- 3.4 Q pipeline: intent gate → signature/warrant → governed walk → Q5 monitor → synthesis. SOURCED.
- 3.5 Governance dial G0–G4 + Ont/Aff axes: semantics of each gate. SOURCED (Paper 1 + Frozen_Code_Changes).
- 3.9 **One-page framework summary** — CORE-S1 (the ONLY §3 content in Scenario 1). DRAFT.

## 4. Design-science methodology — EXT (CORE-S2 one paragraph)
DSR approach, design objectives, kernel theories, design principles DP1–DP3. SOURCED (Paper 1 §3, §3.4).

## 5. Part-1 demonstration & ablation — EXT (5.4 → CORE-S2)
- 5.1 Ten-case walkthrough. SOURCED (Paper 1 §5–6).
- 5.2 Outcome matrix. SOURCED (Paper 1 §6.1).
- 5.4 Ablation: causal contribution of DP3. SOURCED (Paper 1 §6.2).
- 5.5 Boundary modes. SOURCED (Paper 1 §7). Pilot limit (n=10) → motivates Part 2. DRAFT (1 para).

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
