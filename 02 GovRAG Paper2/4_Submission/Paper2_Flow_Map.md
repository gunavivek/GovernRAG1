# Paper 2 Flow Map — the river, one page

*Created 2026-07-28 at Vivek's direction (W6). The cross-reference instrument:
spine ↔ paper ↔ flow map. Every W6 edit justifies itself against this page; any
passage that does not feed the main line is a trim candidate. Frozen alongside
the dictionary; changes only on Vivek's approval.*

## THE MAIN WATER LINE (one sentence)

**Evidence use in RAG can be governed by declared policy — and this paper
measures what that governance buys and costs.**

## The river, section by section

| Paper § | Role in the river | Joins (branches in) | Leaves (branches out) | Spine anchor | Numbers carried |
|---|---|---|---|---|---|
| Abstract | The river in miniature | — | — | §1 claim | 1,225 · 11,025/8,208 · 41–44→75–78% · 97.7–100% · <$800 |
| I. Introduction | States the line; why it matters | Regulated-enterprise need (EU AI Act [31] + NIST AI RMF [34]); 3 contributions | Forward pointers only | §1 + F-headlines | headline set + both failed hypotheses |
| II. Related Work | Positions the line | 3 streams join: KG-before/KG-after → third position; confidence dial vs authorisation dial; KG access control (unmeasured) | Paper-1 citation (once, under review) | §6 | — |
| III. System | The mechanism that makes the line possible | R/D/M/Q pipelines; D5 manifest (M1+Q1+Q5); Q5 admissibility / Q6 sufficiency; levels G0–G4 + axes | Fig. 1 | §5 | 553 concepts; level criteria |
| IV. Evaluation Design | The instrument that measures the line | Pre-registration + deviation log; corpora & strata; outcome-blind selection; evidence scoping; judge policy; metric formulas | Deviation log & repo (anonymised) | §4 + dictionary formulas | 912/163/150 · 7/16/70% · 39.3/3.9/13.0 · 9 configs · 15.0/7.4/10.8 s/q |
| V. Results | THE MAIN CURRENT — the measurements | Fig. 2; Tables I & II | Appendix (dual-judge study) | §2–§3: F1 (V.A/B), F2 (V.B), F4 (V.C), F3 (V.D), F5 (V.E), F6 (V.F), F7 (V.G); H1–H4 (Table II) | frontier set; leakage 23.4→15.6→1.6–7.8; κ=0.681; 504/190 |
| VI. Discussion | Three branches LEAVE the river | — | Operator advice (F1/F5/F6); economics (F8+T2, Q5<1%); position among systems (§6) + regulated-enterprise fit (FINRA/SEC) | §6 + F8 | $498/$222/<$45≈$765 · 2.7¢/pair · CF1 0.080–0.668 |
| VII. Threats & Repro | The banks — where the river ends | — | Future-work seeds (cross-family judge, out-of-sample test, triplet tag, open-corpus) | §7 + T1/T2 dispositions | κ scope; N=3 confound |
| VIII. Conclusion | The river reaches the sea | — | Future work named once | §1 restated as measured | one-line recap set |
| Appendices (outside 10 pp) | Side channels | — | — | F7 full protocol; Q5/Q6 worked example (task 26); deviation-log pointer | per-config tables |

## Spine → paper index (findings and hypotheses land here)

| Spine item | Paper location |
|---|---|
| Claim (§1) | Abstract · §I · §VIII |
| F1 refusal quality | §V.A, §V.B |
| F2 coverage cost + localisation | §V.B |
| F3 auditability (+T1 wording) | §V.D · §VII.A |
| F4 faithfulness ceiling | §V.C |
| F5 abstention-heavy win | §V.E · abstract |
| F6 ontology fit (exploratory) | §V.F · §VI.A |
| F7 judge sensitivity | §V.G · appendix · §VII.A |
| F8 economics (+T2 latency) | §VI.B · §IV.D |
| H1–H4 ledger | Table II (verdicts) · woven: H1→V.G, H2→V.C, H3→V.A/B, H4→V.D |
| §4 method minimum | §IV |
| §5 system minimum | §III |
| §6 positioning | §II · §VI.C |
| §7 limitations | §VII.A |

## Scope rules the map enforces

1. A passage that feeds no row of this map is a trim candidate — trims start
   from the branches, never the main current (§V).
2. Each number appears at full precision ONCE (in its home section per the
   table); elsewhere it may be rounded or referenced.
3. Branches must visibly join ("this stream leads to the third position") and
   visibly leave ("future work", forward pointer) — no unmarked tributaries.
4. Reviewers read non-linearly: abstract → figures/tables → conclusion first.
   Each of those four artefacts must carry the main line standing alone.
