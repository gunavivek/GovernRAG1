> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\6_Results\Full_Benchmark_Run1_Results.md (git mirror: repo docs\Analysis_CrossRun.md) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Full Benchmark — Run 1 Results (N=912 DelucionQA, pre-registered)

*Task #33, run 1 of the replication plan. Generation 2026-07-09 (37 batches, K=25, ~8.6 h,
zero failures); scoring 2026-07-10 (E3, judge gemini-2.5-pro, sequential, ~24 h under API
latency variance). QA: 8,208/8,208 (record,config) pairs scored, 0 ERROR verdicts, strata
848 answerable / 64 unanswerable. Artifacts: results\E3_run1_master_eval_log.csv,
results\E3_run1_frontier_summary.csv, results\full_run\timing_log.csv.*

## Frontier (headline table)

| Config | Coverage | Acc (adh) | Faith | corrRef | falseRej | tokF1 | C-F1 | Cited |
|---|---|---|---|---|---|---|---|---|
| G0 Naive | 100% | 67.8% | 0.99 | 32.8% | 2.7% | 0.57 | 0.61 | 0% |
| G1 Cited | 93% | 64.4% | 0.98 | 42.2% | 5.0% | 0.58 | 0.60 | 99.9% |
| G2 Grounded | 44% | 18.2% | 0.99 | 78.1% | 54.5% | 0.42 | 0.32 | 98.8% |
| G3 Strict | 38% | 14.7% | 0.99 | 78.1% | 60.7% | 0.41 | 0.30 | 97.7% |
| G4 Corrob | 35% | 14.3% | 0.98 | 82.8% | 64.0% | 0.40 | 0.30 | 98.1% |
| G2+OntNU | 45% | 19.6% | 0.99 | 75.0% | 54.2% | 0.42 | 0.33 | 97.8% |
| G2+OntConf | 44% | 18.6% | 0.99 | 75.0% | 54.6% | 0.42 | 0.32 | 98.0% |
| G2+Aff | 44% | 18.0% | 0.98 | 76.6% | 54.6% | 0.42 | 0.32 | 98.5% |
| G2+OntNU+Aff | 44% | 19.1% | 0.99 | 76.6% | 54.6% | 0.42 | 0.33 | 98.3% |

## Pre-registered hypothesis verdicts (report-regardless)

**H1 — quality parity on the answerable stratum (bound ±0.05): SUPPORTED at G1 only.**
G1 vs naive: accuracy −3.4 pp, token-F1 +0.005 — inside the bound. G2 through G4 and all
axis combos: −48 to −53 pp accuracy — far outside. Parity survives citation-gating (G1);
it does not survive predicate authorization (G2+).

**H2 — faithfulness superiority: NOT SUPPORTED (ceiling effect).** TRACe adherence is
0.98–0.99 for every config including naive; hallucination-on-answered is 1.2–2.2%
everywhere. The N=20 pilot's "no headroom" finding replicates exactly at N=912: on
answerable DelucionQA, faithfulness is saturated and governance cannot raise it.

**H3 — selective abstention: PARTIALLY SUPPORTED, with the pre-registered coverage-cost
finding triggered.** Correct-refusal on the 64 unanswerable questions rises monotonically
33% (naive) → 42% (G1) → 75–83% (G2+), and parametric leakage (asserting an answer that
matches RAGBench's hallucinated reference) falls 17.2% → 12.5% → 4.7–7.8%. But
false-rejection on answerable questions at G2+ is 54–64% — the high-wrong-refusal clause
applies, so the G2+ result is reported as the coverage cost of authorization. G1 achieves
+9.4 pp correct-refusal at only 5% false-rejection.

**H4 — auditability: SUPPORTED.** 97.7–99.9% of answered governed outputs carry
source-resolvable [CHNK_*]/[RESIDUAL_*] citations (vs 0% naive), measured on full answers.

## Findings for the paper

1. **The governance spectrum is a coverage/authorization dial at constant faithfulness**
   (pilot finding confirmed at 45× scale). Coverage 100→35% monotone across G0→G4;
   faithfulness flat at ~0.99.
2. **The cost is localized to authorization.** The cliff is G1→G2 (93%→44% coverage,
   64%→18% accuracy) — the D5 predicate filter — not the citation gate (G0→G1 is nearly
   free) and not the symbolic-triplet requirement (G2→G3 is small).
3. **G1_Cited is the operating point for parity claims:** quality parity + ~100%
   provenance + improved abstention at 5% recall loss.
4. **The ontology/affinity axes scope evidence without changing answers (dissociation
   confirmed):** G2-family drops ~35.9 chunks/record (keeping ~3.4 chunks + ~6.5 triplets)
   while accuracy/faithfulness stay within ~1 pp of G2 — governance restricts the evidence
   set, not answer quality on what it answers.
5. **Selectivity, not silence:** abstention quality (correct-refusal up, leakage down)
   improves monotonically with strictness — the reference monitor is doing its job; it is
   simply priced in coverage.

## Caveats / open items
- Single run (run 1). Replication per the (possibly amended) N≥3 / bootstrap plan pending.
- 64-question unanswerable stratum is thin; corrRef percentages move ±1.6 pp per question.
- Faithfulness ceiling may partly be TRACe-adherence leniency on short cited answers
  (pilot caveat stands; a discriminant check is future work).
- Master-log `answer` column truncates at 200 chars — citation stats must be computed from
  the _spec_*.jsonl caches (as done here), not the master log.
