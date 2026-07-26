# Numbers Verification Ledger — Paper 2 manuscript & spine

*2026-07-27 · every number recomputed from sealed primary artifacts on Vivek's
machine (eval logs, spec files, serve maps, timing logs, M3/M4/M5 index files,
R ontology graphml). Method: independent recomputation, compared against the
claimed value and its sealed source. Re-run before submission (script:
5_Drafts\generators\ — passes 1 & 2 recorded in session log 2026-07-27).*

## VERIFIED — exact match (claimed = recomputed = sealed source)

| # | Claim | Recomputed | Source |
|---|---|---|---|
| 1 | Questions 912 / 163 / 150 | 912 / 163 / 150 | eval logs |
| 2 | Unanswerable 64 (7.0%) / 26 (16.0%) / 105 (70.0%) | identical | eval logs |
| 3 | 11,025 judged pairs; 8,208 re-judged | 11,025; 8,208 (both logs) | eval logs |
| 4 | Table I coverage / corrRef / falseRej (all rows) | match ≤0.15 pp | frontier CSVs + log recompute |
| 5 | Table I acc(adh) values | match sealed CSVs | frontier CSVs (see FIX-1) |
| 6 | G0 spontaneous declines 40.6% (26/64) | 40.6% | primary eval log |
| 7 | Leakage primary 23.4 / 15.6 / 1.6–7.8% | 15/64, 10/64 etc. | primary eval log |
| 8 | Leakage initial 17.2 / 12.5 / 4.7–7.8% | 11/64, 8/64 etc. | initial eval log |
| 9 | κ = 0.681 graded; 0.863 incl refusals | 0.681; 0.863 | joined logs |
| 10 | 84.1% = raw agreement on jointly graded pairs | 84.1% (jointly graded = 53.2% of pairs) | joined logs (see FIX-2) |
| 11 | Flips 504 vs 190 | 504 primary-upgrades vs 190 downgrades | joined logs (see FIX-3: direction) |
| 12 | Net flips per level +17.9 / +14.4 / — / +3.2 / −0.3% | +17.9 / +14.4 / +1.5 (G2 tier) / +3.2 / −0.3 | joined logs (see S42c) |
| 13 | Auditability run 1: 97.7–99.9% (Cited) | reproduced per config with sealed detector | run1 spec files |
| 14 | Auditability HAGRID 206/206 | 206/206 | run2 spec + eval log |
| 15 | Scoped chunks 39.3 / 3.9 / 13.0 per question | 39.30 (912/912) / 3.88 / 12.97 | serve maps |
| 16 | Latency 15.0 / 7.4 / 10.8 s/q amortised | identical | timing logs |
| 17 | Reference ontology 553 concepts | 553 nodes | R graphml |
| 18 | Concept-graph nodes 3,781 / 703 / 298 | identical | M3 graphml |
| 19 | Ontology-aligned share 25.8% (77/298) HAGRID | 77/298 (79 M4 rows − 2 unmapped) | M4 + M3 |
| 20 | Ontology-aligned share 47.2% (332/703) ExpertQA | 332/703 (337 − 5) | M4 + M3 |
| 21 | H1 point Δ initial .034; HAGRID .138→(.139); ExpertQA .133 | .0342 / .1387 / .1333 | frontier CSVs |

## DEFINITIONS PINNED (from frozen E3_Parallel_Evaluation.py)
- coverage = 1 − system-refusal rate (BLOCKED mode or refusal text), NOT judge-verdict based.
- acc(adh) = MATCH share over the WHOLE ANSWERABLE stratum — refusals count as misses.
- corrRef = SAFE_SILENCE share on unanswerables; falseRej = refusal share on answerables.
- Verdict SAFE_SILENCE can occur without system refusal (judge credits a spontaneous decline).

## FIXES APPLIED TO §V DRAFT (v3)
- FIX-1 Table I caption: "Acc = accuracy on answered" → "accuracy on the answerable stratum (refusals counted as misses)".
- FIX-2 V.G: "84.1% of pairs" → "raw agreement 84.1% on jointly graded pairs (53.2% of pairs jointly graded)".
- FIX-3 V.G direction INVERTED in draft: the PRIMARY (successor) judge is net-lenient (504 upgrades vs 190), not the initial judge. Sentence rewritten; per-level figures set to recomputed +17.9/+14.4/+1.5/+3.2/−0.3.
- FIX-4 V.G H1: primary-judge answerable-stratum gap is .074 (0.8585−0.7842), not 8.0 points; text now 3.4 / 7.4.
- FIX-5 V.C: "hallucination-on-answered 1.2–2.2%" NOT reproducible from primary-judge artifacts (primary faithfulness 0.9949–1.0000) — same judge-era class as S41. Pending source verification, V.C states the ceiling under both judges and the 1.2–2.2% figure is held out of the draft.

## SPINE ERRATA — proposed S42 (awaiting Vivek's approval + "update spine")
- a) H1 primary point Δ ".080" → ".074" (CSV: .8585 − .7842 = .0743).
- b) Judge-leniency direction: successor/primary judge is the net-lenient one (504 upgrades) — label direction explicitly.
- c) G2-tier net flip "+2.0%" → "+1.5%" (tier aggregate over 2,005 jointly graded pairs).
- d) M4 DelucionQA aligned numerator 3,713 → 3,714 (3,781 − 67 unmapped; share unchanged at 98.2%).
- e) F4 halluc-on-answered "1.2–2.2%" → label by judge or replace with primary-judge value once source verified.

## CLOSURE PASS (2026-07-27, second sweep — completes the recomputable set)
- GA verified 7/7 exact (82.7/75.9 · 79.1/68.1 · 55.3/64.7/66.0) from condition_grade.
- CF1 verified via E3's exact formula (0.5·tokF1 + 0.5·GA); apparent G0 deviations were
  the verifier's filter (E3 includes G0 spontaneous-decline token-F1), reconciled.
- Faithfulness verified: primary 0.9932–1.0000; initial 0.9779–0.9877 — "≥0.98 both
  arms, both judges" holds.
- "Hallucination-on-answered 1.2–2.2%" SOURCE FOUND: = 1 − faithfulness, INITIAL judge,
  run 1 governed configs (exact). Primary-judge equivalent 0–0.7%. → S42e: restore the
  figure to V.C/spine WITH judge labels.
- NOT RECOMPUTED (sealed-artifact-sourced, enumerated and closed): paired-bootstrap CIs
  (B=10,000, seed 20260720 — sealed bootstrap outputs); cost/spend figures (provider
  screenshots + run manifests). These are quotations of sealed artifacts, not derived
  arithmetic, and are labelled as such wherever they appear.

## NOTED, NO ACTION (definitional, both readings defensible)
- ExpertQA auditability "238/238" uses refusal-based answered counts; verdict-based
  count is 234/234 — both are 100%; definition footnote suffices if ever probed.
- M4 files for HAGRID/ExpertQA contain evaluated subsets (79 / 337 rows); nodes
  absent from M4 results count as unaligned in the share — construction documented.
- Cost figures ($498 + $222 + <$45; 2.7¢/pair) and bootstrap CIs (B=10,000, seed
  20260720) are sealed-artifact values (spend screenshots; bootstrap outputs), not
  recomputed here.
