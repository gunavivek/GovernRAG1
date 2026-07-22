> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\2_Design\Model_and_Reproducibility_Protocol.md (git mirror: repo docs\ where present) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Paper 2 — Model Selection & Reproducibility Protocol

*Status: draft v1. Governs every result-generating run for Paper 2. Read before the first real build.*
*Owner: Vivek. Last updated: 2026-06-28.*

---

## 0. Why this document exists

Paper 2 is a **measurement paper** (RAGBench / TRACe evaluation of the GovernRAG
pipeline). For a measurement paper, the single thing reviewers and a committee
will probe hardest is: **what produced these numbers, and can it be reproduced
from your artifact?** This protocol fixes those rules *before* the first run, so
the methods section writes itself and no result is ever in doubt.

The execution *venue* (laptop, a cloud VM, a sandbox) is **not** the issue — any
machine is just compute. The issues are: which model, who/what is allowed to
touch the results, and whether every run is pinned and logged.

---

## 1. Decision 1 — one fixed, single-model pipeline

- Paper 2 uses **one result-generating pipeline**, fixed before the evaluation
  run and unchanged across all records and all conditions.
- The pipeline uses **a single LLM**, applied uniformly. No mixing providers or
  model versions across records — that is a confound that invalidates any
  cross-record comparison.
- Switching away from Paper 1's Gemini runs is **legitimate**: Paper 2 is a fresh
  experiment with no obligation to reuse Paper 1's model. The only consequence is
  the comparability caveat in §6.

## 2. Decision 2 — pipeline model ≠ judge model (independence)

This is the constraint that decides the design, and the one most likely to sink
the paper if ignored.

- TRACe / RAG evaluation leans on **LLM-as-judge**. If the same model both
  *produces* the system output and *judges* it, you get **self-preference bias** —
  models systematically favor their own generations (Panickssery et al. 2024;
  self-enhancement bias in Zheng et al. 2023). A reviewer at a SIGIR/EMNLP-class
  venue will flag this immediately.
- **Rule:** the evaluator/judge must be **independent of the pipeline model.**
- **Recommended design (turns dual access into a strength):**
  - **Pipeline model = Claude** (extraction M2, anchoring D2/D3, generation Q6).
  - **Judge model = Gemini** (or a reference-based / open evaluator, or the
    RAGBench-released evaluator).
  - You have access to both, so use one for the system-under-test and the other
    for evaluation. This is *cleaner* than a single-vendor study, and it is
    defensible on exactly the axis reviewers attack.
- If you later want to argue robustness, report the metric under **both** judge
  choices and show the ranking of conditions is stable (a judge-sensitivity check).

## 3. Decision 3 — execution environment & the agent bright line

- **Run real result-generating builds on a controlled environment you own and can
  document** — your laptop, or a cloud VM you provision with the key. **Not** the
  AI agent's sandbox: it is ephemeral, time-limited, undocumented, and outside
  your version control — the opposite of reproducible.
- **The bright line for AI assistance (hold this exactly):**
  - **Allowed:** AI writes and *smoke-tests harness/tooling code* against
    **synthetic** fixtures; AI helps analyze, tabulate, and write up results you
    generated. Disclose per venue policy (§7).
  - **Not allowed:** AI generating, imputing, "patching," or otherwise influencing
    the **measured outputs** of the system under test. Results must come from the
    fixed pipeline and be re-runnable from your artifact. The agent must never be
    both experimenter and part of the system being measured.

## 4. Reproducibility harness — pin, log, freeze

Every run writes a **run manifest** capturing the full configuration. Minimum
fields:

```yaml
run_id:            <dataset>_<phase>_<UTC timestamp>
git_commit:        <pipeline repo commit hash>     # code provenance
corpus:            <name> + record count + data checksum
phase:             build | serve | eval
model:
  provider:        anthropic | google
  model_version:   <exact string, e.g. claude-sonnet-4-6 / gemini-...>
  api_date:        <YYYY-MM-DD of the API/version>
  sdk_version:     <client lib version>
decoding:
  temperature:     0
  top_p:           <value>
  max_tokens:      <value>
  seed:            <if supported>
prompts:
  template_hash:   <hash of each frozen prompt template>
judge:                                              # eval phase only
  provider/model_version/api_date: <independent of pipeline model>
library_versions:  {networkx, datasets, ...}
repeats:           <N>                              # see below
cost:              {input_tokens, output_tokens, usd}
latency:           {build_seconds, per_question_seconds}
peak_ram_mb:       <from B1 / serve harness>
```

Rules that go with it:

- **Pin** the exact model version string, `temperature=0`, `top_p`, `max_tokens`,
  SDK version, and API date. "We used Claude" is not reproducible; the version
  string is.
- **Repeat and report variance.** Hosted LLM APIs are **not bit-deterministic even
  at temperature 0** (server-side batching/routing). A single number is not
  credible — run **N ≥ 3 repeats** per condition and report mean ± std (or CI).
- **Freeze prompts on a dev split *before* touching the test set.** Tune prompts
  on held-out dev data, hash and freeze them, *then* run test. Iterating prompts
  against the eval set is overfitting to the test and quietly invalidates results.
- **Capture cost and latency**, not just quality. Part of the Paper 2 claim is
  "governance at no quality cost" — cost/latency is half of that argument.

## 5. Provider abstraction (makes the above by-design, not by-discipline)

- Put the LLM call behind **one interface** (`generate(prompt, **decoding) -> text`
  / a structured-output variant), with **provider as a config flag**
  (`--provider claude|gemini`).
- Refactor only the call sites (M2 extraction client, D2/D3, Q6, and the eval
  judge) to go through it; **governance logic stays frozen.**
- Benefits: judge-independence becomes a config choice; the same harness runs the
  judge-sensitivity check in §2; the run manifest reads model fields from one
  place; swapping Gemini↔Claude is a flag, not a rewrite.
- Engineering note: M2 currently uses Gemini's async client + JSON mode. Claude
  structured output should go through **tool-use / JSON schema**; the extraction
  prompts will need re-tuning (do it on the dev split per §4).

## 6. Integrity guardrails & caveats

- **One pipeline, fixed:** no silent changes between conditions or runs.
- **No mixed models** across records or phases (except the deliberate, reported
  judge-sensitivity check).
- **Comparability caveat:** Paper 2's absolute numbers are **internally
  consistent** but **not comparable to Paper 1's Gemini numbers** — do **not**
  claim a cross-paper delta. State this explicitly in the paper.
- **Attestable provenance:** you (the author) can re-run any reported number from
  the artifact + run manifest.

## 7. Disclosure statement (draft, for the paper)

> *AI-assistance disclosure.* AI tools were used to author and test harness and
> analysis code and to assist drafting. All reported experimental results were
> produced by the fixed [Claude]-based GovernRAG pipeline described in §X and
> evaluated by an independent [Gemini]-based judge; configurations are recorded in
> per-run manifests released with the artifact. No AI tool generated, imputed, or
> altered any measured result.

Adapt to the venue's specific AI-use policy.

## 8. References (verify exact bibliographic details before citing)

- **Zheng et al. 2023** — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
  (NeurIPS 2023). LLM-as-judge; position / verbosity / self-enhancement bias.
  *(confident)*
- **Panickssery et al. 2024** — "LLM Evaluators Recognize and Favor Their Own
  Generations" (NeurIPS 2024). Self-preference / self-recognition bias.
  *(confident on existence; verify author spelling — formerly Perez.)*
- **Friel, Belyi & Sanyal 2024** — "RAGBench: Explainable Benchmark for
  Retrieval-Augmented Generation Systems." TRACe = Relevance, Utilization,
  Adherence, Completeness. *(confident; confirm metric definitions against the
  paper.)*
- **Es et al. 2023/2024** — "RAGAS: Automated Evaluation of Retrieval Augmented
  Generation." *(reference-free RAG eval; context.)*
- LLM-API nondeterminism at temperature 0 is a **documented practitioner finding**
  (batching / MoE routing), not a single canonical paper — present as engineering
  reality, cite a primary source if you find a rigorous one. *(lower confidence —
  hedge in text.)*

---

### One-paragraph summary
Standardize Paper 2 on a single, version-pinned LLM applied uniformly; make the
**judge a different model** than the pipeline (recommended: pipeline = Claude,
judge = Gemini) to avoid self-preference bias; run real builds on a controlled
machine, never the agent sandbox; keep AI on tooling/analysis and never on result
generation; log every run's full config to a manifest; repeat ≥3× and report
variance; freeze prompts on a dev split before touching test. Do this and the
approach is fully defensible.
