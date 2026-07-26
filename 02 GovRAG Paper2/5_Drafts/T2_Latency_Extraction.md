# T2 — Per-Question Latency Extraction (analysis record)

*2026-07-26 · read-only analysis of sealed archives · approved by Vivek (three
approvals: IV.C symmetric means, IV.D latency sentence, S39 queued). No frozen
code touched; no archive modified.*

## Question
Pre-registration promised "per-question $ and seconds". Dollars were reported
(2.7¢/pair etc.); seconds were absent from every sealed summary. T2: extract from
run logs, or file a dated deviation.

## Sources (sealed, read-only)
- results\run1_delucionqa\full_run\timing_log.csv (852 rows)
- results\run2_hagrid\timing_log.csv (163 rows)
- results\run3_expertqa\timing_log.csv (139 rows)
Schema: batch, phase (B2_serve · B2_stage:Q1..Q6 · BATCH_TOTAL · Q5 · Q6),
config, seconds, n_records, ok, when. B2_Serve.py writes these per serve slice
("metric #7 amortized-latency source", B2 line ~236).

## Method
Sum `seconds` and `n_records` over ok=True B2_serve rows per run; amortised
per-question latency = total seconds / total records. Stage shares from
ok=True B2_stage rows. Failed batches excluded; their retries counted.

## Results
| Corpus | ok batches | failed | records | total s | s/question |
|---|---|---|---|---|---|
| DelucionQA (run 1) | 37 | 0 | 925 | 13,880 | **15.0** |
| HAGRID (run 2) | 7 | 1 | 175 | 1,292 | **7.4** |
| ExpertQA (run 3) | 6 | 0 | 150 | 1,625 | **10.8** |

Stage shares of serve time: Q2 signature extraction 58% / 91% / 93%;
Q6 synthesis 35% / 5% / 3%; Q3 retrieval 7% / 4% / 4%; Q1 intent gate ≈0%;
**Q5 Reference Monitor <1% on all three corpora.**

Caveats (stated in §IV.D): wall-clock was logged per 25-question batch →
figures are amortised, not per-individual-question; records slightly exceed
corpus sizes (925 vs 912; 175 vs 163) from resume/re-serve overlap of slices.

## Disposition
- Pre-registered promise fulfilled by extraction; **no deviation entry needed**.
- §IV.D sentence added (draft v3). §VI may use: governance enforcement (Q5) is
  <1% of serve time — the LLM calls are the cost, not the monitor.
- Symmetric-precision side-result: evidence-scoping means recomputed exactly —
  39.3 (DelucionQA, 912/912 join, min 1 max 139) / 3.88 (HAGRID, n=163) /
  12.97 (ExpertQA, n=150). Spine "~36" for DelucionQA is an erratum → S39 queued.
- Serve-map file locations are rotated on disk (HAGRID map in
  index\expertqa_run3\, DelucionQA's in index\hagrid_run2\ and run1 final state,
  ExpertQA's in output\); identified by n and mean. Housekeeping note only.
