# Paper 2 — Analysis Plan & Stopping Rule (pre-registration)

**Author:** Vivek  **Date committed:** 2026-07-06
**Purpose:** lock the run and the reporting *before* seeing results, to protect against
scope creep and result-driven tuning. This is a commitment, not a plan to revisit.

---

## The commitment (verbatim)

> *"I run the full benchmark once, N≥3, stratified by answerability, on the frozen pipeline
> (anchor fix included). I report faithfulness, abstention correctness, provenance coverage,
> and answerable-stratum accuracy — whatever they are — and that is the paper."*

**Report-regardless clause.** The results of the pre-registered run are the paper, whether
they support, partially support, or refute the hypotheses. A refuting or mixed result is a
valid Design-Science contribution (an evaluated artifact with characterized boundary
conditions) and will be reported as such — not tuned away.

---

## Frozen design (locked — no further changes)

- **Pipeline:** R/D/M build (done, `index/delucionqa/`) + frozen Q1–Q6 + Q5 reference monitor.
- **Only permitted edits already applied & reviewed:** Q2 (anchor-linking + JSON hardening),
  Q3 (design-A scoping), model lines. Recorded in `Frozen_Code_Changes.md`.
- **Generation model (parity pair):** Q6 == naive baseline == `gemini-3.5-flash` (GA; pin exact
  version at run time). Q2 same. **Judge ≠ generation** (`gemini-2.5-flash` or DeBERTa).
- **Serving:** build-once/serve-many, design-A per-question chunk scoping, anchor-linking ON.
- **No more pipeline tuning to raise answer rate.** Out of scope for this paper.

---

## Strata (independent of GovernRAG — fixed before the run)

Each question labelled **answerable** / **unanswerable** from an independent source:
native benchmark answerability field (preferred) → gold-derived → NLI-entailment fallback.
Labels frozen before serving; never defined by GovernRAG's own refusals.

---

## Metrics (exact) — reported per stratum + overall

1. **Faithfulness (headline).** TRACe **Adherence** (answered tuples only) and **hallucination
   rate** = answered-but-unsupported / answered. Governed vs naive.
2. **Abstention correctness.** Unanswerable stratum: % correctly refused (governed vs naive).
   Answerable stratum: % wrongly refused (recall loss — kept visible, not hidden).
3. **Provenance coverage.** % governed outputs with source-resolvable `[CHNK_*]`/`[RESIDUAL_*]`.
4. **Answerable-stratum accuracy (parity).** Correctness (MATCH/NO_MATCH judge) + TRACe
   Relevance/Utilization/Completeness, governed vs naive, with a stated equivalence bound.
5. **Selective prediction.** Risk–coverage curve (confidence proxy = Q5 governance ratio /
   kept-triplet count); governed = curve, naive = single point.
6. **Governance-native (context).** Governance Ratio distribution; decision-log completeness
   (Q5 audit / Z2–Z3). Naive ≈ 0 by construction.
7. **Cost + latency.** Per-question $ and seconds, governed vs naive.

## Hypotheses & decision rules (set now)

- **H1 (quality parity, answerable stratum):** supported if governed vs naive difference on
  accuracy + R/U/C falls within the pre-set equivalence bound (state bound before run, e.g. ±0.05).
- **H2 (faithfulness superiority):** supported if governed Adherence ≥ naive and governed
  hallucination rate < naive (report effect size + N≥3 variance).
- **H3 (selective abstention):** supported if correct-abstention(unanswerable) ≫ naive AND
  wrong-refusal(answerable) is low. If wrong-refusal is high → reported as the coverage-cost finding.
- **H4 (auditability):** supported if provenance + decision-log coverage ≈ 100% for governed.

---

## Scale & runs

- **N ≥ 3** independent runs (temp-0 nondeterminism); report **mean ± sd**.
- Scale: 20 (smoke, done) → validate ruler on ~50–100 → **full benchmark once**.
- Corpora: DelucionQA first (built); Emanual next if time permits; FinQA/CUAD = future work.

---

## Measurement layer to finish BEFORE the pre-registered run (bounded; not design changes)

1. Fix `gold` loading + pull native **answerability** label from source data.
2. Stratified reporting in `trace_scorer` (answerable/unanswerable split).
3. Adherence scored on answered tuples only.
4. Risk–coverage from existing signals; per-run cost/latency logging.

These build the *ruler*; none alters governance logic. When (1)–(4) pass a sanity check on
~50 questions (naive accuracy is non-zero and plausible), the ruler is trusted and the
pre-registered full run proceeds.

---

## Deviation policy

Any change after this point (pipeline, metric, stratum, model) is **logged with date + reason**
in this file before it is made. Silent changes are not permitted. If a deviation is required to
fix a *measurement* bug, that is allowed and logged; a deviation to improve *results* is not.

## Deviation log
- **2026-07-06 — Gold + answerability source (measurement fix).** The served CSV had no gold/answerability
  columns (empty-`gold` bug). Gold answer + answerability label (`adherence_score`) now joined from
  RAGBench `delucionqa_questions.jsonl` by question (100% coverage). `build_gold_map.py` + `trace_scorer` join.
- **2026-07-06 — Judge model gemini-2.5-flash → gemini-2.5-pro (measurement fix).** Flash mis-scored
  "answer contains the gold fact" cases as NO_MATCH (e.g. the ABS answer). Pro judge is correct and still
  independent of the gemini-3.5-flash generator. Pro is the locked judge for the pre-registered run.
- **2026-07-06 — N corrected 1826 → 913 (data-artifact fix).** Records CSV duplicated each question ×2;
  effective unique N = 913. Full run dedups to 913.
- **2026-07-06 — Governance-level parameter added to Q6 + Q5 (new experimental axis, PILOT).**
  `GOVRAG_LEVEL` (G0–G4) parameterizes the Q6 answer gate and a Q5 filter toggle (G1). DEFAULT unset =
  G3 = exactly prior behavior (verified). This ADDS an experimental variable (governance spectrum),
  it does NOT tune the STRICT result. Reversible (`.bakL`, patchers `apply_q6_levels.py`/`apply_q5_g1.py`).
  Pilot on 20 Q to see the frontier; production use pending Dr. Xu sign-off (governance semantics).
- **2026-07-09 — N corrected 913 → 912 (data-artifact fix).** Actual unique-question count of the
  records export is 912 ({2:911, 4:1} duplication; one question appears 4× with divergent context,
  first occurrence kept). Frozen benchmark input: `data/delucionqa_records_912.csv`
  (see `Benchmark_Input_Provenance.md`). Change sets 5–6 signed off by Dr. Xu (relayed 2026-07-09);
  full run executed 2026-07-09/10 (RUN 1, results in `6_Results/Full_Benchmark_Run1_Results.md`).
- **2026-07-12 — REPLICATION DESIGN AMENDED (cost-motivated; decided BEFORE runs 2–3 execute).**
  Original commitment: N≥3 full-benchmark repeats on DelucionQA (mean ± sd). Amended to:
  (a) cross-corpus generalization — runs 2–3 on two additional RAGBench subsets selected by
  document-reuse (per discussion with Dr. Wang): **ExpertQA** and **HAGRID**, top-50/60 documents,
  ~100 fully-covered questions each (selection script `ragbench_select_and_prep.py`, deterministic,
  provenance manifest per selection); (b) statistical treatment of RUN 1 via paired bootstrap
  confidence intervals over its 912 records (no additional generation). REASON: two further full
  DelucionQA runs (~$444) exceed the July API spend cap and measure only serve-time variance on one
  corpus; cross-corpus runs test generalization of the frontier shape at ~1/4 the cost. The run-to-run
  variance limitation is disclosed (M4 build nondeterminism already quantified in Sprint 1).
  Communicated to Dr. Xu by email 2026-07-11 with a stated proceed-unless-objection plan; this entry
  precedes any run-2 execution. Measurement infrastructure for runs 2–3: parallel checkpointed scorer
  (`E3_Parallel_Evaluation.py`), B4 run-guard with per-run artifact isolation (`--run-tag`),
  per-run API keys for usage attribution — none alters pipeline or judging logic.
- **2026-07-18 — Selection parameter set K=150 (pre-execution; supersedes the 50/60 estimate).**
  A K-sweep on both corpora (before any generation) showed K=60 leaves the minority stratum too
  thin (ExpertQA 15 answerable; HAGRID 12 unanswerable); K=150 yields ExpertQA 176 q (42 P / 134 N)
  and HAGRID 167 q (141 P / 26 N) at marginal reuse ≈ 1.0 q/doc, the knee of the curve.
  Representativeness table + complementary-strata rationale: `Subset_Selection_Validity.md` §4.
  ExpertQA selection executed 2026-07-18 (deterministic; verified identical across two independent
  executions); NO generation has occurred as of this entry.
- **2026-07-19 — RUN ORDER SWAPPED (HAGRID → run 2, ExpertQA → run 3) + JUNK-DOCUMENT FILTER
  (data-cleaning, evidence-driven, decided before either corpus generated any results).**
  The ExpertQA M1 build stalled deterministically on its first content slice; isolation testing
  reproduced the cause: Google's server returns **504 DEADLINE_EXCEEDED** on the slice opening with
  the corpus's most-reused document — an NCBI "Access Denied" scraping artifact (already identified
  and quantified in Subset_Selection_Validity.md §"junk" before the build). The document is
  machine-unprocessable by the chunking layer itself; retries are futile at temperature 0.
  AMENDMENTS: (a) selection gains a deterministic `--drop-junk` filter (pre-registered error-page
  markers + <40-word stubs), recorded per selection manifest; (b) run order swapped — HAGRID
  (clean wiki-passage text) proceeds first as run 2; ExpertQA retried as run 3 with the filter;
  CovidQA is the documented fallback if ExpertQA remains unbuildable. Rationale: bank a clean
  cross-corpus run before re-attempting the risky corpus. The unprocessable-document incident is
  itself reportable evidence for governance-layer evidence screening. Representativeness tables
  will be recomputed for every filtered selection. Build hardening added the same day
  (`B5_Build_Runner.py`: stall watchdog, retries, stage checkpoints, corpus/key guards) —
  orchestration only; frozen pipeline untouched.
- **2026-07-19 (later) — ROOT CAUSE CORRECTED + M1/M2 MODEL REPOINT (measurement/infrastructure
  fix, approved, before any run-2/3 generation).** Further isolation testing showed the 504
  DEADLINE_EXCEEDED reproduces on HAGRID's clean first slice too and vanishes entirely under
  `gemini-2.5-flash-lite` (4.1 s on the identical call): the cause is a DEGRADED
  `gemini-3-flash-preview` ENDPOINT, not corpus content — the earlier junk-document attribution
  is likely wrong and will be retested; the junk filter is RETAINED as data hygiene (462 stub/error
  documents excluded from HAGRID alone). REPAIRS (third model-line repair of the project, same
  class as the two gemma-404 repointings): M1 + M2 model line → `gemini-2.5-flash-lite`
  (`.bakM` backups); M1 additionally gains a 120 s per-call HTTP timeout and a per-slice progress
  print (observability; no logic or output-content change). DISCLOSURE: run-1's build used the
  preview model, run-2/3 builds use flash-lite — a build-stage infrastructure difference noted in
  all manifests; governance logic, serve models, and judge unchanged.
- **2026-07-19 (evening) — SECOND MODEL WITHDRAWAL SAME DAY + BUILD-CHAIN AUDIT (infrastructure
  fixes, approved, still before any run-2/3 generation).** ~1 hour after `gemini-2.5-flash-lite`
  passed the isolation test (OK 4.1 s), Google withdrew it: 404 "no longer available to new
  users" on the identical call (B5 caught it in 0.3 min, 3 attempts, ~$0). A four-candidate
  probe on the real HAGRID slice: 2.5-flash-lite FAIL(404); **3.1-flash-lite OK 4.4 s / 24
  items**; flash-lite-latest OK 4.6 s (floating alias — rejected for reproducibility);
  2.5-flash OK but 19.7 s and same sunsetting family. REPAIR: M1 + M2 repointed to
  **gemini-3.1-flash-lite** (GA version pin). A full model audit across D/M/Q/E pipelines then
  found (a) the three run-1 hardened build variants (M3.3_HARDENED, M4_PARALLEL, M5_HARDENED)
  present in the Paper2 harness mirror but absent from the repo `experiment\` — copied in
  unmodified except (b) M3.3_HARDENED and M4_PARALLEL carried the degraded
  `gemini-3-flash-preview` — repointed to gemini-3.1-flash-lite (`.bakM` backups). Embedding
  model (gemini-embedding-001) verified live same day via the D pipeline. Serve model
  (gemini-3.5-flash) and LOCKED judge (gemini-2.5-pro) to be probed before generation.
  JUSTIFICATION (for Limitations / audit): because Google deprecated the run-1 build models
  mid-study, run-2/3 indices are built with gemini-3.1-flash-lite (disclosed per-run in the
  manifests); all hypothesis tests are within-run governed-vs-naive comparisons over a shared
  index, so build-model variation across runs affects generalization breadth, not internal
  validity. H1–H4 are serve-time hypotheses; generation and judge models are unchanged across
  runs 1–3. Full note in RESEARCH_LOG.md (same date).
- **2026-07-19 (evening, cont.) — LOCKED JUDGE REPLACED: gemini-2.5-pro → gemini-3.1-pro-preview
  (measurement-instrument repair, approved, decided BEFORE any run-2/3 judging).** The same
  model sweep that removed 2.5-flash-lite also withdrew the LOCKED judge `gemini-2.5-pro`
  (404 "no longer available"). Probe of every pro-tier model visible to the project left two
  viable candidates; **gemini-3.1-pro-preview** chosen over the `gemini-pro-latest` alias
  because a locked judge must have a fixed, citable identity — an alias can drift silently
  mid-study, whereas a pinned model that dies fails loudly and is deviation-logged. Judge
  independence preserved (judge ≠ generation model gemini-3.5-flash). No frozen code involved:
  the judge is a CLI argument; harness defaults (E3_Parallel_Evaluation, B4 next-step hint) and
  the runbook updated. COMPARABILITY REMEDY (approved same day): after run 2 completes, run 1's
  archived 8,208 serve pairs will be RE-JUDGED with gemini-3.1-pro-preview (judge calls only,
  no generation) so all runs share one judge; run 1 will be reported under both judges as a
  judge-robustness check. Within-run governed-vs-naive comparisons — where all hypothesis
  tests live — are unaffected by the judge change in every run.
- **2026-07-19 (night) — STALE-RESUME CONTAMINATION CAUGHT BEFORE SERVING (build-integrity fix;
  no results generated or affected).** First hardened HAGRID build pass: M1/M1.5/M2/M3 produced
  a valid 298-node / 1,143-edge HAGRID graph, but M3.3/M4/M5's crash-resume logic (which keys on
  output-file existence, not corpus identity) silently "resumed" from run-1 DelucionQA partials
  still in the `output\` working slot (3,781-node graph; M4_alignment_results.jsonl dated Jul 5)
  and reported success with zero new work. Detected immediately from the topology mismatch in the
  live B5 logs. REMEDY: stale partials quarantined to `_quarantine\run1_stale_build_partials\`
  (run-1 canonical copies remain in the read-only archive), contaminated `index\hagrid_run2`
  snapshot set aside for deletion, B5 checkpoints for M3.3/M4/M5 reset, stages rerun fresh from
  the valid M3 output. Run-1 artifacts untouched. Root cause noted for the harness backlog:
  B5 should quarantine downstream partials whenever the D5 corpus changes.
- **2026-07-19 (night, cont.) — SERVE-MAP MATCHING MADE BIDIRECTIONAL (measurement-infrastructure
  fix, approved, before any run-2 serving).** The design-A question→chunk map used one-directional
  verbatim containment (chunk ⊆ document), correct for DelucionQA's long manuals but wrong for
  HAGRID's short wiki passages: M1 chunks (median 179, max ~6,000 chars) often span several
  passages (median 653 chars), so 71 of 73 unmatched documents were documents-inside-a-chunk;
  question coverage was 50.3%. FIX in `serve_map_questions_to_chunks.py` (harness, not frozen
  pipeline; `.bak` kept): containment tested in both directions + a windowed-overlap fallback.
  Effect: retrieval scope for a question may include neighboring-passage text sharing a spanning
  chunk — a slight widening (conservative direction; no evidence lost), identical behavior on
  run-1-style corpora where chunks are smaller than documents. Coverage re-verified before the
  smoke batch; preflight re-run.
- **2026-07-19 (night, cont. 2) — Q3 EMPTY-EVIDENCE STATE + B2 RUN-DERIVED QUESTION IDS
  (approved; smoke batch 0 surfaced both; before any completed run-2 serving).** (a) FROZEN-CODE
  fix, Q3 design-A branch: when every chunk mapped to a question yielded ZERO extracted triples
  (24/163 HAGRID questions — sparse wiki passages; impossible on DelucionQA's ~36 chunks/question),
  Q3 raised a fatal debug assertion ("_edge_cid attr wrong?"). Replaced with a defined
  EMPTY-EVIDENCE state: logged, empty evidence subgraph served with the question's real chunk
  text, downstream governance gates decide answer/abstain exactly as in the already-exercised
  zero-anchor path. No gate, threshold, walk, or scoring logic changed; a crash became a
  legitimate governed outcome (`.bakQ3` backup). Empty-evidence frequency will be reported
  per run. (b) HARNESS fix, B2: question ids were stamped with a hardcoded `delucionqa_q` prefix;
  now derived from the records filename (`hagrid_run2_q00003`) so run-2/3 artifacts carry
  truthful provenance ids. Gold joins are by question text; nothing keys on the prefix.
- **2026-07-19 (night, cont. 3) — E3P JOIN BUG FROM THE ID-PREFIX FIX; FIRST RUN-2 SCORING
  INVALIDATED AND RE-SCORED (measurement fix, same evening, before any results reported).**
  The approved B2 id-prefix change (run-derived question ids) broke an undetected twin
  assumption in E3_Parallel_Evaluation.py, which RECONSTRUCTED ids with a hardcoded
  "delucionqa_q%05d" to join governed answers: every governed lookup missed, empty answers
  scored as refusals, and the first run-2 summary wrongly reported 100% refusal for ALL
  governed configs including G1 (actual G1 serve data: 127/163 answered). Detected immediately
  by cross-checking the summary against the serve archives. FIX: join by the numeric index
  parsed from the record_id tail (prefix-agnostic); invalid outputs retained as *.bad_join
  evidence; full clean re-score executed with the same locked judge. Also same evening:
  E3P judge client gained the same 120 s per-call HTTP timeout as M1 (a hung judge socket
  had frozen the final pair indefinitely; approved). LESSON RECORDED: any id-format change
  must be grepped across the entire harness before serving.
- **2026-07-20 — RUN-1 RE-JUDGE COMPLETE (dual-judge robustness; approved 2026-07-19).**
  All 8,208 Run-1 pairs re-judged with gemini-3.1-pro-preview (the successor to the
  withdrawn locked judge). Original judging preserved bit-identical (post-run SHA
  verification 47/47); re-judge sealed as append-only archive `results/run1_rejudge/`
  (own SHA256SUMS). Agreement: κ=0.681 (substantial), 84.1% on judged pairs; successor
  systematically more lenient (MATCH .506→.578), concentrated on verbose answers
  (G0/G1). DISCLOSURE: H1's pre-registered ±.05 parity bound is judge-sensitive on
  Run 1 (Δ=.034 original vs Δ=.080 successor); the paper reports both judges, treats
  frontier structure (judge-invariant) and accuracy levels (judge-dependent) separately,
  and uses the single consistent judge for all cross-run comparisons.

- **2026-08-02 — Anonymised artifact package assembled and published (documentation).** A
  scrubbed, copy-only package (pre-registration + deviation log, selection code and frozen
  lists, per-run SHA-256 manifests, run-1 evaluation layer, and the complete run-1R/2/3
  archives) was assembled for the double-blind venue submission and published via an
  anonymised mirror. Two execution-state files withheld (local paths; hash lines retained);
  identity strings neutralised in document copies; no sealed original modified. Publishing
  artifacts is not a methods change.
- **2026-08-02 — Venue-paper SIII overlap check vs Paper 1: CLEAN (documentation).** Decision
  recorded: the venue paper keeps its standalone SIII depth (option b of the reviewer's T7).
  A sentence-level comparison of the full venue manuscript (283 sentences; 43 in SIII)
  against the submitted Paper 1 manuscript (v25 PDF; 345 sentences) found zero exact and
  zero near-duplicate sentences (similarity >= 0.80); the sole shared string is the defined
  six-word term "source document, the atomic unit of governance". The fresh-prose rule for
  SIII is thereby verified, not merely asserted; no text change required under either QASC
  outcome.

- **2026-08-03 — Section V-E derived metrics verified against sealed archives (documentation).**
  All governance-accuracy values in V-E recomputed verbatim from the sealed evaluation logs
  under the locked formula (condition_grade SUCCESS*/N): DelucionQA (run-1 re-judge, primary
  judge) G0 754/912 = 82.7, G1 692/912 = 75.9; HAGRID (run 2) G0 129/163 = 79.1, G1 111/163
  = 68.1; ExpertQA (run 3) G0 83/150 = 55.3, G2+OntNU 99/150 = 66.0, plain G2 97/150 =
  64.666... -> printed 64.7 confirmed. Comparison levels now disclosed in the text (G1 /
  G2-tier); a derivability note (GA = Acc*(1-u) + cRef*u, up to rounding) added beside the
  metric definition in Section IV-D.

- **2026-08-03 — Axis-variant Table I differences verified against sealed serve archives
  (documentation).** Byte-level prompt-identity comparison of G2_Grounded vs G2+OntNU:
  prompts identical on 874/912 (DelucionQA), 163/163 (HAGRID), 150/150 (ExpertQA). Of the
  twelve DelucionQA outcome flips between the configs, eleven occurred on byte-identical
  prompts; HAGRID's single flip (unanswerable q00118, identical prompt) is exactly the
  printed cRef step 76.9 -> 80.8 (20/26 -> 21/26). The small G2-vs-variant differences in
  Table I are serving-pass variance at the model-mediated answer gate, not filter effects;
  an explanatory clause was added to Section V-F, and a no-matched-coverage-baseline
  rationale sentence to Section II. Rebuttal reserve filed (5_Drafts).
