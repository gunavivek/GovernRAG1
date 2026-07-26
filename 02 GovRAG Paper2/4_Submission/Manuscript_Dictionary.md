# Paper 2 Manuscript Dictionary (TPS venue manuscript)

*Created 2026-07-25 at Vivek's direction (W1 §III.A review, item 0). APPROVED by
Vivek 2026-07-25 (M = modelling pipeline; B-series excluded from the pipeline set).
One concept, one term, one definition — every section is written against this
register and the W6 submission pass verifies against it. Changes only on Vivek's
approval. Companion to the Voice & Framing Guide (which governs style; this file
governs terms).*

## Pipelines (letters fixed by the public artifact names — M1–M5, Q5, D5)

| Letter | Manuscript name | Definition (as used in the manuscript) |
|---|---|---|
| R | reference ontology | Supplies the domain vocabulary from which authorisation rules derive. Evaluation instance: enterprise reference vocabulary of 553 concepts derived from BIZBOK; the architecture is ontology-agnostic (instantiation treated in §IV). |
| D | governance-definition pipeline | Compiles governance policy together with domain-specific data into the per-record Governance Manifest (D5). |
| M | modelling pipeline | Build-time pipeline M1–M5: governed chunking (M1), concept and triple extraction (M2), concept-graph construction (M3, with M3.3 concept augmentation), ontology alignment (M4), graph embedding and governed index assembly (M5). Runs once per corpus. No bridge-discovery mechanism exists in M (verified against harness code 2026-07-25). |
| Q | query pipeline | Serve-time pipeline: intent gating, signature extraction, governed graph retrieval, residual retrieval; Q5 Reference Monitor; Q6 cited synthesis. |

*Note (not a pipeline): the B-series scripts (B2 serve, B4 batch runner, B5 build
runner) are the batch-execution harness — execution jobs, not system components.
They are never described as pipelines or components anywhere in the manuscript.*

*Note (excluded component): Recursive Bridge Discovery (Q3.5/Q3.6) is Paper 1's C2
contribution, query-side. It was NOT in the Paper-2 executed serve path
(B2: Q1→Q2→Q3→Q4→Q5→Q6, verified 2026-07-25) and is therefore not described
anywhere in this manuscript. (Vivek approved corrections 1–4, 2026-07-25.)*

## Components

| Term | Definition |
|---|---|
| Governance Manifest (D5) | Per-record machine-readable policy artefact: authorised predicates, ontology rules, domain-affinity specification. Single point of policy definition; consumed by M1 at build time and at serve time by Q1 (domain activation + authorised-predicate scoping → the Q2 search warrant) and Q5 (admit/drop audit). Verified against D5_Orchestrator/Q1/Q5/M1/B2 code 2026-07-25. |
| Reference Monitor (Q5) | Enforcement component that examines each candidate evidence item under the manifest and the active governance level, admits or drops it, and writes one log entry per decision (evidence item, rule applied, outcome). |
| answer gate (Q6) | Cited synthesis enforcing the active level's answer requirement on admitted evidence: answer with citations drawn only from admitted evidence, or refuse. Fail-closed. |

## Governance levels (names exactly as in the experiment; levels nest — constraints only grow)

| Level | Name | Requirement added |
|---|---|---|
| G0 | naive | Query pipeline bypassed; retrieval straight to the model. The ungoverned baseline. |
| G1 | Cited | ≥1 retrieved chunk; citation required in the answer. |
| G2 | Grounded | ≥1 authorised chunk (passes the monitor's predicate filter), plus citation. |
| G3 | Strict | ≥1 authorised symbolic triplet, plus citation. |
| G4 | Corroborated | Multiple authorised triplets, or one triplet plus an independent agreeing authorised chunk. |

## Axis variants (within a level)

| Term | Definition |
|---|---|
| ontology conformance | Triplets filtered by alignment status against the reference ontology. |
| domain affinity | Chunks filtered by a domain-affinity score. |

## Evidence and behaviour terms

| Term | Definition |
|---|---|
| admitted evidence | Evidence the Reference Monitor has authorised for use at the active level. |
| authorised chunk / authorised triplet | Chunk passing the Q5 predicate filter / triplet meeting the level's symbolic requirement. |
| evidence-scoped serving | Retrieval per question restricted to that question's own source documents (the benchmark's gold-context design), mapped to pipeline chunks by verbatim containment. |
| empty-evidence refusal state | Questions whose admitted evidence yields no triplets enter a legitimate governed refusal, not an error path. (Operational definition lives in §IV.) |
| fail-closed | When admitted evidence does not satisfy the active level's requirement, refusal is the designed outcome. |
| build/serve split | Corpus-dependent governance work paid once at build; queries pay marginal authorisation + synthesis cost. Rationale (§III.A): an organisation writes a document once and queries it many times. Quantified in §VI (F8 unit economics). |

## Judgement and metric terms

| Term | Definition |
|---|---|
| MATCH / NO_MATCH / SAFE_SILENCE | Judge verdict per answer; SAFE_SILENCE is a credited decline. |
| correct refusal | Refusal on an unanswerable question. |
| false rejection | Refusal on an answerable question (correct-answer forgone). |
| governance accuracy (GA) | As defined in §IV (sealed definition; Source_Register). |
| Constrained-F1 (CF1) | CogniGraph's definition, computed for comparability; reported as a secondary, within-system metric. |
| coverage | Fraction of questions answered (not refused). |
| faithfulness | Adherence of answered content to admitted evidence (TRACe-style); ceiling caveat per F4. |
| risk–coverage frontier | The per-level curve of quality vs coverage across G0–G4; the paper's primary object. |
| pre-registered | Hypotheses, metrics, stopping rule publicly timestamped before execution; deviations logged before the affected step ran. |

## Metric formulas (locked 2026-07-27 at Vivek's direction — every result number is
## computed by exactly these definitions, from the frozen E3 evaluator and verified
## against sealed logs; the Numbers Verification Ledger re-runs them as the gate)

| Metric | Formula (per config, per corpus) | Note |
|---|---|---|
| coverage | 1 − (system-refused / N) | system-refused = BLOCKED mode or refusal-text; a judge SAFE_SILENCE verdict on a delivered answer is NOT a system refusal (G0 spontaneous declines) |
| accuracy (adh) | MATCH ∧ answerable / answerable | refusals count as misses; the answerable stratum, not the answered set |
| correct-refusal | SAFE_SILENCE ∧ unanswerable / unanswerable | |
| false rejection | system-refused ∧ answerable / answerable | |
| faithfulness | mean adherence over answered rows | TRACe-style; report judge label |
| hallucination-on-answered | 1 − faithfulness | initial judge run 1: 1.2–2.2%; primary judge: 0–0.7% — ALWAYS labelled by judge |
| token-F1 | mean over (not system-refused ∧ answerable) rows | E3 filter — includes G0 spontaneous declines |
| governance accuracy (GA) | condition_grade startswith SUCCESS / N | |
| Constrained-F1 | 0.5 · mean token-F1 + 0.5 · GA | E3's instantiation of CogniGraph's definition |
| parametric leakage | MATCH ∧ unanswerable / unanswerable | always labelled by judge (primary 23.4/15.6/1.6–7.8; initial 17.2/12.5/4.7–7.8) |
| auditability (Cited%) | answered-graded with ≥1 [CHNK_*]/[RESIDUAL_*] bracket / answered-graded | detector = has_citations regex (A0 runner) |
| κ (inter-judge) | Cohen's kappa; jointly graded = both verdicts ≠ SAFE_SILENCE (53.2% of pairs) | raw agreement on jointly graded = 84.1%; κ incl. refusals = 0.863 |
| H1 point Δ | acc(adh)_G0 − acc(adh)_G1, per judge | initial .034; primary .074 |
| ontology-aligned share | (M4 result rows − Unmapped) / M3 concept-graph nodes | 3,714/3,781 · 332/703 · 77/298 |
| amortised latency | Σ seconds over ok B2_serve batches / Σ n_records | per-batch wall-clock, disclosed as amortised |
| scoped-chunk mean | mean chunk_ids per question over the evaluated-set join | 39.30 / 3.88 / 12.97 |

## Standard phrases (locked)

- "11,025 judged pairs, of which 8,208 were additionally re-judged by a second judge."
- Judge policy: primary results use the single successor judge for all runs; run 1's initial scoring is retained as an inter-judge robustness study (appendix).
- CF1 guardrail: never "we beat CogniGraph"; always "we characterise the curve their operating point sits on."
- Ontology-fit observation always carries "exploratory" / "we observe".

## Spelling and style pointers

British/Commonwealth spellings throughout (authorised, behaviour, modelling, artefact,
characterise) per the Voice & Framing Guide. OPEN ITEM (W6): the shell abstract
currently uses American spellings — one convention must win across abstract + body.
