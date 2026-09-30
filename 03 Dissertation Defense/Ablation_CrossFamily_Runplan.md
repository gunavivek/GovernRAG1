# Cross-family ablation — run plan (LOCKED design v2, 2026-09-30; execution starts next session)
_Vivek approvals 2026-09-29/30: budget YES ($250 cap) · TWO families · keys at run time · this ablation
takes priority over all other tasks · run with the same campaign discipline (sealed artifacts, deviation
log first, probes before spend). 2026-09-30 rulings: FULL three corpora (subset dropped) · swap scope =
**Q6-only replay** (Q2 NOT swapped) · judge-agreement add-on = YES._

## Objective
Dr. Xu's X6: is the solution/design dependent on the LLM? Test whether the governance dial's
STRUCTURE survives a change of the generation model, holding admitted evidence identical. Framing:
post-hoc robustness study that closes the dissertation's own declared limitation (§10.2 "one model
family"). NOT pre-registered with the original campaign — deviation-logged before execution,
disclosed as post-hoc.

## Design (locked v2)
- Corpora: FULL DelucionQA 912 · FULL HAGRID 163 · FULL ExpertQA 150 (subset design dropped —
  full corpora make results directly comparable to the published frontier, no stratification
  machinery to defend). 1,225 questions × 5 levels = 6,125 judged pairs per family.
- Configurations: five dial levels G0–G4 ONLY. Axis variants excluded on principle: they isolate
  substrate ingredients (ontology conformance, domain affinity); the substrate is frozen here.
- **Swap scope: Q6-only REPLAY (ruled 2026-09-30).** The sealed per-run `_spec_*.jsonl` files
  contain the exact prompts sent to the serve model — Gemini-retrieved evidence embedded verbatim,
  all five levels including the naive baseline. The ablation replays these sealed prompts
  byte-identical to each new family's API at T=0. Consequences:
  · identical admitted evidence per question BY CONSTRUCTION (not by assertion);
  · every verdict difference attributable to exactly one variable — the generation model;
  · no Q1–Q5 execution, no B1 index copy-in, no retrieval nondeterminism, no frozen-pipeline touch;
  · adapter is a small standalone replay script (read spec jsonl → call API → write answers jsonl
    in E3P-expected format), NOT a modification of B2/B4.
  Claim wording this design supports: **generation-step resilience** — "given the same admitted
  evidence, the governed dial structure holds across model families." It does NOT claim whole-stack
  portability; defense answers if pressed: D-stage already multi-family (GPT-4o at D3/D4), Q1/Q3/
  Q4/Q5 deterministic (no LLM), Q2 is a structured-extraction task — small-subset Q2 sensitivity
  check available as a later contingency, not run now.
- Judge: gemini-3.1-pro-preview, CONSTANT across all ablation runs (instrument held fixed).
- **Judge-agreement add-on (ruled 2026-09-30: YES, ~$5–10):** re-judge ~500 sealed Gemini-era
  pairs (seeded sample across corpora/levels/verdict classes, selection script + seed committed)
  with a second judge family; report agreement (κ) vs the campaign judge. Answers "is the
  architecture family-sensitive at JUDGING" with data; own sealed archive.
- Families (tier-matched to gemini-3.5-flash — frontier models would confound family with
  capability): (A) OpenAI GPT-4o-mini/4.1-mini class; (B) hosted open-weights Llama 3.x class
  (Haiku alternate if a provider fails probe). EXACT pinned model strings probed LIVE before any
  spend (standing rule; aliases rejected — dated snapshots or weights-pinned endpoints only).
- Bootstrap: same paired machinery, B = 10,000, NEW seed chosen and logged in the deviation entry.
- Dependence-map showcase table (for §8.6 + deck): Q5 monitor = resilient by construction (no
  LLM) · D build stage = already cross-family (GPT-4o) · Q6 generation = THIS study · judging =
  add-on above · M/R stages = future work (confounded replication).
- Budget: serve replay ≈$2–7/family · judging ≈$80–85/family · two families ≈$165 · add-on $5–10
  · cap $250 total. Billing captures BEFORE and AFTER each family (Table 6.1 pattern).

## Pre-stated decision rule (goes in the deviation log verbatim, before first token)
Evidence is held identical, so criteria test governed-GENERATION behavior. Architecture is claimed
resilient at the generation step iff, under each new family:
(a) dial monotonicity holds (coverage non-increasing G0→G4, each corpus);
(b) the G1→G2 coverage cliff is present on the aligned corpus and the above-G1 collapse on HAGRID;
(c) correct-refusal ordering preserved (governed tiers ≫ naive, unanswerable stratum);
(d) resolvable-citation/auditability remains at ceiling (shown, not assumed).
Accuracy LEVELS may shift (as with the judge succession); STRUCTURE is the claim. If any criterion
fails: report as a bounded-resilience finding; §10.2's limitation stands as written. Either outcome
is publishable; only an unrun question is not defensible.

## Execution
1. VERIFY sealed inputs: `_spec_*.jsonl` present for all 15 corpus×level combos (runs 1–3 archives);
   record counts + SHA-256 of each spec file consumed. No run until all 15 verified.
2. LIVE MODEL PROBE for both families before any spend (model string, T=0 support, context
   window ≥ max spec prompt length, price).
3. REPLAY ADAPTER: standalone script (new file, outside frozen pipeline and outside B-harness).
   Per standing rule it is still presented as a full diff for Vivek's approval BEFORE first call;
   grep check that it touches no existing file; .bak discipline n/a (no existing file modified).
   Output format validated against E3P input expectations on the pilot before full run.
4. DEVIATION-LOG ENTRY (docs/Analysis_Plan_and_Stopping_Rule.md + OneDrive mirror) with design,
   swap-scope rationale (Q6-only, why Q2 excluded), decision rule, add-on sample seed, budget cap —
   COMMITTED AND PUSHED to GitHub BEFORE the run (public timestamp).
5. FORMAT PILOT: 20 questions per family (mixed levels) → eyeball answer format, refusal phrasing
   compatibility with E3P parsing → fix adapter output mapping if needed → then full run.
6. Runs: replay per corpus per family (checkpointed, resumable, run-tag guard); then E3P scoring
   with per-pair checkpoints, bounded timeouts. Family A fully archived before Family B starts
   (or parallel if keys/quotas allow — decide at run time).
7. Judge-agreement add-on: seeded ~500-pair selection script committed → second-judge re-judge →
   own sealed archive results/ablation_judgeagreement/.
8. Archives: results/ablation_<family>_<corpus>/ — append-only, SHA-256 manifests, run manifest
   yaml naming pinned model strings + spec-file hashes consumed. Billing captures per family.
9. Analysis: structural criteria (a)–(d) + per-level deltas with bootstrap CIs vs the Gemini
   campaign numbers · family performance/cost table (Xu's "which family suits" ask) · add-on κ.
10. Outputs, in order AFTER results (per Vivek: ablation first, everything else waits):
    summary to Dr. Xu → manuscript §8.6 "Cross-family robustness" + §10.2 softening (Batch 29)
    → deck v9 Experiment/Evaluation content → committee email with manuscript + Doodle (both
    late-Oct AND early-Nov windows offered).

## Next session start checklist
[ ] Verify 15 spec files + hashes  [ ] Vivek provides OpenAI key + hosted-Llama provider key
    (e.g., Together/Groq — his choice)
[ ] Approve replay-adapter diff  [ ] Live model probe → pin strings  [ ] Deviation entry push
[ ] Add-on sample script + seed commit  [ ] 20-q pilot per family  [ ] Family A full replay begins
Est. wall time: replay hours not days per family (no pipeline re-run); E3P judging is the long
pole (~1 day per family); analysis same-day after E3P completes.
