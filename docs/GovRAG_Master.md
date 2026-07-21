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
- 0.1 Reading guide + extraction recipes (this page). SOURCED.
- 0.2 **Proposal-contribution map** (the defense spine): the four committed contributions
  (BA-aligned RAG framework · concept-attribute-value mapping · TRACe enterprise metrics ·
  governance-friendly adoption pathway) → where delivered → evidence file. DRAFT — from
  Email B text + Dissertation Proposal_v3 §5. 
- 0.3 Timeline of the research program (proposal Apr 2025 → Paper 1 → Paper 2 campaign
  Jul 2026 → defense). DRAFT — from Sprint_Log / RESEARCH_LOG.

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
