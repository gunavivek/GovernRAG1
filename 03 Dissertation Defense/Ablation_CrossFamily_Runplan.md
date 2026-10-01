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

## Model selection justification (added 2026-10-01 at Vivek's request — goes to deviation log + §8.6)
Selection is CRITERIA-driven; exact model strings are pinned only at the LIVE PROBE (standing rule
after the Google same-day withdrawals), with probe transcript + billing capture as evidence.
Criteria:
 C1. Distinct pretraining lineage from Google/Gemini (otherwise it is not a family test).
 C2. Tier-matched to gemini-3.5-flash (flash/mini serving tier). A frontier model would confound
     FAMILY with CAPABILITY; a weaker tier would confound it the other way.
 C3. Deterministic decoding supported (T=0), context window >= max sealed prompt (~12k chars — trivial).
 C4. Ecosystem coverage: one CLOSED-API family + one OPEN-WEIGHTS family. Open weights add a
     permanent-reproducibility property no API family can offer (weights outlive the vendor).
 C5. Pinnable dated snapshot (closed) or weights-pinned endpoint (open).
 C6. Neither family may equal the JUDGE family (judge = Gemini). Both candidates are non-Gemini;
     the residual Gemini-judge/Gemini-campaign asymmetry is exactly what the judge-agreement
     add-on measures.
Chosen (classes, pinned at probe):
 Family 1 (closed API): OpenAI mini tier — GPT-5-mini / GPT-4.1-mini class. Largest non-Google
     closed ecosystem; already present in the build provenance (GPT-4o at D3/D4), so the
     dissertation's model inventory stays coherent.
 Family 2 (open weights): Meta Llama class (3.3-70B / Llama-4 tier) via hosted inference
     (Together or Groq — Vivek chooses provider at key time). Most widely adopted open family;
     satisfies C4's reproducibility property.
Recommended pins (2026-10-01 analysis; FINAL strings set only at live probe):
 Family 1: gpt-5-mini, dated snapshot (current catalog snapshot 2025-08-07 class); in-family
     backup gpt-4.1-mini. Rationale: OpenAI's serving-tier peer of gemini-3.5-flash (C2);
     OpenAI lineage already in build provenance (GPT-4o at D3/D4) — no "third lab from nowhere".
 Family 2: llama-3.3-70b-versatile on Groq (= Llama-3.3-70B-Instruct-Turbo on Together;
     provider = Vivek's choice at key time); in-family backup: hosted Llama-4-tier equivalent.
     Rationale: most-adopted open-weights model at tier (C2, C4); weights public -> this arm is
     PERMANENTLY reproducible, a property no closed API offers.
 Pair-level justification: the pair spans closed-API + open-weights ecosystems and gives three
 distinct pretraining lineages across the study (Google campaign / OpenAI / Meta), none equal to
 the judge family. Structure holding on BOTH generalizes resilience across vendor type; holding
 on one but not the other is itself a publishable bounded-resilience contrast.
Alternatives considered: Anthropic Claude Haiku class (qualifies on C1–C3, C5; held as ALTERNATE
if either probe fails); Qwen / Mistral open classes (qualify; Llama preferred on adoption breadth
and provider determinism options). PRC-origin open families (Qwen, DeepSeek, Kimi/GLM classes): technically QUALIFY on C1/C3/C5
and are documented as eligible alternates, not rejected on quality. Llama preferred for the
single open-weights slot on three grounds: (i) tier fit — DeepSeek's flagship open models are
frontier-scale MoE (above the C2 tier; Qwen does offer tier-matched sizes); (ii) reviewer
familiarity — Llama is the default open family in the RAG literature the committee knows;
(iii) deployment-context fit — GovernRAG targets public-sector deployment, and during 2025
several U.S. states and federal agencies restricted PRC-origin AI models/services on government
systems; model provenance is itself a governance variable in this dissertation's framing, and
choosing a family the target context may prohibit would invite a policy debate orthogonal to
the resilience question. If the committee asks for a Qwen/DeepSeek arm, the sealed-prompt
replay design makes it a bounded ~$85 follow-up, not a redesign.
Rejected: any Gemini-lineage model (C1), any frontier-tier
model (C2).

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

## Six-job runbook (operational; exact flags finalized with the approved adapter diff)
EXECUTION ENVIRONMENT: Vivek's machine, VS Code terminal, SAME venv as the campaign (launcher
verify first — Start-GovRAG.ps1, 3-line check). Rationale: instrument/environment parity with the
sealed campaign; API keys stay on his machine as session env vars (never in files, never in chat);
sealed archives are local; Claude's remote shell caps each command at ~3 minutes — unsuitable for
multi-hour jobs. Division of labor: Vivek runs the jobs in his terminal; Claude prepares/verifies
everything through the mounted repo (adapter, manifests, spot-diffs, archive sealing, analysis).

PHASE 0 — gates, once, in order (no spend before 0.4):
 0.1 Claude writes AB1_Replay_Serve.py (NEW standalone file; reads sealed archives read-only;
     --probe, --pilot, --corpus/--provider/--model modes; checkpointed + resumable; asserts
     byte-identity of prompt fields against the sealed originals on every record) ->
     presented as a diff -> VIVEK APPROVES -> committed.
 0.2 Keys as env vars in the VS Code terminal session only:
     $env:OPENAI_API_KEY="..."   $env:GROQ_API_KEY="..."   (+ existing Gemini key for E3P judge)
 0.3 LIVE PROBE both pins (1-token calls): model-id echo, T=0 accepted, context length, price;
     probe transcript saved; billing baseline captured.
 0.4 Deviation-log entry (design, swap-scope rationale, decision rule, pins, add-on seed, cap)
     -> git commit + PUSH to GitHub BEFORE the first full-run token.
 0.5 PILOT: 20 DelucionQA questions x mixed levels per family -> replay -> E3P end-to-end ->
     verify verdict parsing, refusal encoding, and the naive prompt-template reconstruction
     (template = B2_Serve.py naive_baseline(), line ~139, cited by git hash in the manifest).

OVERWRITE PROTECTION (verified 2026-10-01: results/ ROOT currently holds the full run-1 slot —
20 _spec_* files + serve_results.jsonl; root serve_results.jsonl is MD5-identical to the sealed
run1_delucionqa/ copy, i.e. root = duplicate of sealed state):
 O1. Pre-flight hash audit (read-only): every root file the ablation would write is
     SHA-256-compared against its sealed-archive counterpart; audit report saved.
 O2. Only a root file PROVEN identical to a sealed copy is MOVED (never deleted, never
     overwritten) to results/_campaign_slot_run1_<date>/ — fully reversible. Any mismatch ->
     HARD STOP, no run (a mismatch would mean the seal is not faithful; investigate first).
 O3. Adapter fail-fast: refuses to write ANY destination that already exists; there is no
     overwrite mode in the code. It also requires the O1 audit report to exist before writing.
 O4. E3P outputs isolated by --out-prefix ABL_<f>_<c>: E3P was built for this (its own header:
     prefixes exist "so run-1's E3_* files are never clobbered"); existing checkpoints are
     E3_run1*/E3_run2*/E3_run3* — ABL_* collides with nothing.
 O5. Sealed archives are read-only by construction: the adapter asserts no write path ever
     contains run1_/run2_/run3_/full_run.
 O6. Ablation seals go to brand-new dirs ablation_<f>_<c>/, asserted non-existent before create.
 O7. Each job's slot files are sealed into their ablation dir BEFORE the next job starts, so
     job N+1 cannot touch job N's outputs.

PER JOB (6 jobs = corpus c in {run1_delucionqa, run2_hagrid, run3_expertqa} x family f in {oai, llama}):
 J1. Slot hygiene: results/ root must hold no stale _spec_*/checkpoint files (quarantine to
     results/_quarantine_<date>/ if any — stale-resume hazard from the campaign).
 J2. Replay:  python AB1_Replay_Serve.py --corpus <c> --provider <f> --model <pinned>
     Writes into the results/ slot: the four frontier _spec files (prompt fields byte-identical,
     generated_answer replaced, model identity in metadata) + ablation serve_results.jsonl
     (naive, from sealed question+context + frozen B2 template).
 J3. Spot-diff gate (automatic in adapter; manual spot check optional): one record per config
     diffed vs sealed original -> only generated_answer and model metadata may differ.
 J4. Judge:   python E3_Parallel_Evaluation.py --serve results/serve_results.jsonl
              --out-prefix ABL_<f>_<c>        (judge stays default gemini-3.1-pro-preview)
 J5. Seal:    move slot outputs -> results/ablation_<f>_<c>/ ; SHA-256 manifest; run_manifest.yaml
     naming pinned model string, spec-file hashes consumed, B2 template hash, timestamps.
 J6. Billing capture at each family boundary (before/after per family).
 Order: jobs 1-3 = Family 1 across all three corpora, seal, billing; jobs 4-6 = Family 2 same;
 JOB 7 (add-on): seeded ~500-pair selection -> second-judge re-judge -> results/ablation_judgeagreement/.

ANALYSIS (after all seals): criteria (a)-(d) per family vs campaign frontier; bootstrap B=10,000
(new seed from deviation entry); family performance/cost table; add-on kappa.

## Next session start checklist
[ ] Verify 15 spec files + hashes  [ ] Vivek provides OpenAI key + hosted-Llama provider key
    (e.g., Together/Groq — his choice)
[ ] Approve replay-adapter diff  [ ] Live model probe → pin strings  [ ] Deviation entry push
[ ] Add-on sample script + seed commit  [ ] 20-q pilot per family  [ ] Family A full replay begins
Est. wall time: replay hours not days per family (no pipeline re-run); E3P judging is the long
pole (~1 day per family); analysis same-day after E3P completes.
