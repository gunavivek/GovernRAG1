# Run 2 — Gemini API Usage Evidence (AI Studio screenshots, captured 2026-07-19 ~20:32–20:35 CDT)

Six screenshots saved by Vivek from Google AI Studio → Usage (1-day view, UTC-8 axis).
Raw PNGs: stored alongside this note in the Run-2 evidence pack. This note is the index
and interpretation; entries cross-reference the deviation log of the same date.

## Project "conceptual-GraphRAG" (key shown: "graphRAG") — Tier 3
- **Total API Requests:** near-zero through the night; small bars ~08:00–12:00 (isolation
  probes, model tests); heavy bars ~13:00–18:00 peaking near 1,000 requests/hour — the
  HAGRID build (M1 chunking, M2 async extraction, M3.3 augmentation, M4 alignment),
  B4 serving (7 batches × 16 configs + naive), and three E3P judging passes.
- **Success-rate dip ~12:00–13:00** coincides with the gemini-2.5-flash-lite withdrawal
  (404 "no longer available to new users") and the pre-fix B5 attempts.
- **Total API Errors:** 400 BadRequest, **404 NotFound** (bars ~12:00 — the 2.5-family
  withdrawals: flash-lite, then 2.5-pro; also gemini-3-flash probe), **504 GatewayTimeout**
  (~15:00–17:00 — residual preview-endpoint degradation; corroborates the morning's
  root-cause finding). These error charts independently corroborate deviation-log entries
  "2026-07-19 (evening)" and "(evening, cont.)".
- **Models seen (input/output tokens + requests):** Gemini 2.5 Flash / Flash Lite / Pro
  (pre-withdrawal attempts), Gemini 3 Flash (404 probe), **Gemini 3.1 Flash Lite** (build,
  green spike ~13:00), **Gemini 3.5 Flash** (serving, dark-blue spike ~16:00–17:00, ~800
  requests + ~1M-token input peak), **Gemini 3.1 Pro** (judging, purple output spike
  ~17:00), plus one-off probe artifacts (Nano Banana Pro, Lyria 3 Pro — the pro-tier
  judge-candidate sweep; Lyria's 32.7 s "music" response was rejected).
- **Embed content:** single spike ~13:00 — ~6K embedding requests / ~240K tokens on
  Gemini Embedding 1 = M5 vectorization of the HAGRID graph (851 nodes / 5,815 edges,
  node+edge batches), consistent with M5's 6.3-minute wall time.

## Project "Personal Project" (key shown: "govrag-run2-expertqa")
- Activity only ~04:00–08:00 UTC-8 (≤80 requests/hour; Gemini 2.5 Flash Lite +
  Gemini 3 Flash): the MORNING work — legacy-tree M1 run and early isolation tests.
  No embedding traffic; no evening traffic.
- **ATTRIBUTION CONFIRMED (Vivek, 2026-07-19 20:47 CDT, for Run2_Manifest.yaml):** the
  .env key AIzaSyDhK8... belongs to project **conceptual-GraphRAG** — all Run-2
  build/serve/judge spend is billed there, NOT to the key named "govrag-run2-expertqa"
  (Personal Project; morning activity only). The manifest records actual attribution.

## Spend (AI Studio Spend page, conceptual-GraphRAG, captured 2026-07-19 20:47 CDT)
- Month-to-date: **$41.01** (no cap set). 7-day (Jul 13-19): **$16.41**.
- Jul 19 (Run-2 day: two builds, full serve, three judging passes, all probes): **~$13-14**.
- Jul 18 (prep day): ~$3.5. Run-2 marginal cost ≈ one-tenth of a Run-1-scale day —
  the document-reuse selection economics working as designed.

## Why this matters for the paper
Independent, Google-side corroboration of: (a) the model-withdrawal deviations (404s at
the documented hours), (b) the endpoint-degradation root cause (504s), (c) the build/serve/
judge activity envelope and volumes for Run 2, and (d) per-run cost attribution.
