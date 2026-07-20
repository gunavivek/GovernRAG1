# Run 3 — Gemini API Usage Evidence (AI Studio screenshots, captured 2026-07-20 ~00:44–00:46 CDT)

Three screenshots saved by Vivek from Google AI Studio (project conceptual-GraphRAG — the
project owning the .env key AIzaSyDhK8..., attribution confirmed 2026-07-19; see
Run2_Evidence for the confirmation trail). This note indexes them against the
terminal-verified Run-3 activity of the same night.

## Files
1. `Run3_API Usage_Live API_Screenshot 2026-07-20 004417.png` — Generate-content usage.
2. `Run3_Embed_Screenshot 2026-07-20 004519.png` — Embedding usage.
3. `Run3_Spend_Screenshot 2026-07-20 004625.png` — Spend page after Run 3.

## Terminal-verified activity these charts corroborate (evening/night of Jul 19→20)
- **Build (A1 → D+M chain), 100.28 min total:** D1 3.8 s; D0 42.2 s; M0 99.5 min.
  M1 chunking + M2 async extraction + M3.3 augmentation on **gemini-3.1-flash-lite**
  (2,036 chunks; 1,256-node / 7,066-edge final graph). M4 PARALLEL alignment: 337 LLM
  calls in 15.78 min (366 low-confidence concepts skipped without LLM — disclosed).
- **M5 embedding:** 88 MB graph vectorized on gemini-embedding-001 — the Run-3 embedding
  spike (larger than Run 2's: 1,256 nodes / 7,066 edges vs 851 / 5,815).
- **Serving (B4, run-tag run3_expertqa):** 150 questions × 16 configs + naive, 6 batches,
  ~9–11 min/batch on **gemini-3.5-flash** — the sustained generate-content band; ExpertQA's
  long-form answers drive higher output tokens than Run 2.
- **Judging (E3P):** 1,350 pairs on **gemini-3.1-pro-preview**, 10.4 min, zero errors
  (208 MATCH / 124 NO_MATCH / 1,018 SAFE_SILENCE).
- **Spend:** Run-3 marginal cost = the Jul 19→20 increment on the Spend chart, on top of
  the $41.01 month-to-date recorded in the Run-2 evidence note. Record the exact figure
  in Run3_Manifest.yaml when the Spend page settles (up to 24 h latency per Google).

All Run-3 traffic on project conceptual-GraphRAG; no traffic expected on the
"govrag-run2-expertqa" key (Personal Project) for this run.
