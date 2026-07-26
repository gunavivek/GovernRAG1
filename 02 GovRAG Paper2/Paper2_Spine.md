# Paper 2 — Spine (markdown twin)

*Text twin of Paper2_Spine.docx v2.3, generated 2026-07-25 for git timestamping under the
repo's no-Office-binaries policy. The .docx is the reading/markup copy; content is identical.
Binary deliverables are timestamped by hash in DELIVERABLES_SHA256.md.*

**Paper 2 — Spine**

*v2.3 — S39 erratum applied on Vivek’s “update spine” (2026-07-26): §4 evidence-scoping means corrected to 39.3 / 3.9 / 13.0 chunks per question (DelucionQA mean recomputed from the full serve map joined to the sealed 912-question evaluated set, 912/912 matched; HAGRID 3.88, n=163; ExpertQA 12.97, n=150 — T2 analysis pass).*

*v2.2 — S38 applied on Vivek’s instruction (2026-07-26): §5 architecture-figure pointer updated to GovernRAG_Architecture_Simple Master.pptx (the reviewed, code-aligned Figure-1 source; Diagram2b remains a design-history artefact).*

*v2.1 — S37 erratum applied on Vivek’s “update spine” (2026-07-25): §5 modelling-pipeline description corrected — no bridge-discovery mechanism exists in M1–M5 (verified against harness code; Recursive Bridge Discovery is Q3.5/Q3.6, Paper 1’s C2, and was not in the Paper-2 executed serve path B2: Q1→Q6).*

*v2.0 — full topic-by-topic adversarial review completed with Vivek (Topics 1–15, 2026-07-24/25); batch S6–S36 + N1–N5 applied on Vivek’s “update spine”. Review record: Master_Update_Queue.md. PURPOSE: the spine is the seed of the research publication; the dissertation layer is out of scope here (see Annex A pointer). Scenario-neutral: pours into the IEEE shell (QASC accepts / silent) or the upgraded v25 body (QASC rejects). JUDGE POLICY: primary results use ONE judge (gemini-3.1-pro-preview) for all three runs; run 1’s initial scoring by the withdrawn original judge is an appendix robustness study only. Every number verified against sealed archives during the review.*

**1. The claim**

**An ontology-derived reference monitor, placed on the evidence admitted to retrieval-augmented generation and tunable over five governance levels, turns governance policy itself into the abstention mechanism. Its risk–coverage behaviour is measurable at every level, with near-total decision auditability, at commodity cost — and where abstention matters, governance outperforms the ungoverned baseline outright.**

**2. The findings (the vertebrae)**

**F1 Policy-driven refusal works, and it is stable across corpora**

At the Grounded level (G2) — the strictest level at which all three corpora still answer questions — the correct-refusal rate on unanswerable questions rises to 75–78% on all three corpora, from 41–44% for the ungoverned baseline. The baseline's 41–44% reflects spontaneous declines that the judge credits as safe silence; governance nearly doubles this rate, and does so by explicit policy rather than by the model's disposition — making the comparison conservative in the baseline's favour. Three very different corpora, same governed behaviour.

> **Numbers:** corrRef G2: 78.1% (DelucionQA) / 76.9% (HAGRID) / 75.2% (ExpertQA) vs naive 40.6 / 42.3 / 43.8%; unanswerable strata 7.0% (64/912) / 16.0% (26/163) / 70.0% (105/150)
>
> **Sealed source:** results\run1_rejudge, run2_hagrid, run3_expertqa — E3\_\*\_frontier_summary.csv
>
> **Reinforces:** *Abstention as a governance outcome, not a model-confidence signal — the core GovernRAG mechanism, observed working.*

**F2 The governance frontier exists and is measurable per level**

Coverage falls monotonically as strictness rises, and the cost concentrates at the authorization step: the correct-answer false-rejection rate at G2 spans 51–85% depending on corpus. By design the levels differ only in the authorization gate — retrieval, graph, and models are identical across levels — and the audit metadata localises the cost: at G2 the monitor drops on average ~36 chunks per question and coverage halves, while G3–G4 drop no further evidence and lose coverage only through the stricter answer gate. Prior governance-aware systems report one operating point; this work reports the whole curve.

> **Numbers:** coverage G0→G2: 100→44.1% (D) / 100→16.6% (H) / 100→32.7% (E); falseRej G2: 54.3 / 84.7 / 51.1%; chunks dropped by monitor: 0.0 (G1) → 35.9 avg (G2+), DelucionQA
>
> **Sealed source:** same three frontier summaries + audit-metadata drop columns; figure 3_Figures\Frontier_ThreeCorpora.png
>
> **Reinforces:** *The dial is real: each notch buys refusal quality and charges coverage — measured, not asserted (contribution C5).*

**F3 Near-total decision auditability — the promise, priced**

Citations resolve to archived evidence for 97.7–100% of governed answers; the Q5 decision log — every admit/reject with its rule — is present for governed decisions by construction, refusals included. Concretely: from the logs alone, an auditor can take any governed answer and reconstruct which chunks were retrieved, which the Reference Monitor admitted or dropped and under which manifest rule, and which admitted evidence the answer cites — without re-running the system. The trail is nearly free: at G1, coverage stays at 92.5 / 77.9 / 58.7% with full provenance, decision logs, and ceiling faithfulness — auditability almost without the coverage price. This is the only hypothesis supported without qualification on every corpus.

> **Numbers:** resolvable citations: 97.7–99.9% (DelucionQA; root cause of the remainder pending T1) / 100.0% (206/206, HAGRID) / 100.0% (238/238, ExpertQA); G1 coverage 92.5 / 77.9 / 58.7%
>
> **Sealed source:** audit-metadata coverage in sealed run archives; Analysis_CrossRun.md v4 §H4 (“auditability ~for free at G1”)
>
> **Reinforces:** *The Reference Monitor's audit-grade provenance claim, now demonstrated at benchmark scale.*

**F4 Faithfulness sits at a ceiling that governance does not disturb**

When the system answers, the answer adheres to cited evidence ≥0.98 at every governance level on every corpus — and the ungoverned baseline is at the same ceiling. Stated honestly: H2 (faithfulness superiority) is REFUTED; the paper claims no hallucination reduction. The ceiling has a structural cause: on gold-context benchmarks each question is served its own source documents, leaving little hallucination headroom for any configuration (hallucination-on-answered is 1.2–2.2% everywhere) — which is why we report the refutation rather than hiding it. Pre-registered caveat: the ceiling may partly reflect TRACe-adherence leniency on short cited answers (a discriminant check is future work), though the ceiling is observed independently under both judges. The refutation sharpens the paper's claim rather than weakening it: governance's measured value lies in refusal quality (F1) and auditability (F3), not in improving what is already saturated.

> **Numbers:** faithfulness 0.983–1.000 at every level; run1 rejudged G0 1.000, G1 0.999, G2 1.000; hallucination-on-answered 1.2–2.2%
>
> **Sealed source:** faithfulness column, all frontier summaries; run-1 results (pre-registered leniency caveat)
>
> **Reinforces:** *Honest scoping is the credibility spine: governance does not degrade answers; it also cannot improve a ceiling.*

**F5 Where abstention matters, governance wins outright**

On the abstention-heavy corpus (ExpertQA: 70% of the evaluated set unanswerable, 105/150; the full corpus is 55% unanswerable), governed configurations beat the naive baseline on governance accuracy 66% vs 55%, and Constrained-F1 rises under governance (0.566 vs 0.502) — coverage lost is more than repaid in correctness. A refuse-everything policy scores governance accuracy equal to the unanswerable share — 7%, 16%, and 70% on the three corpora — so it is tempting only where abstention dominates. The study contains this policy empirically: at G3/G4, HAGRID and ExpertQA refuse every question, scoring Constrained-F1 of 0.080 and 0.350. On ExpertQA the governed G2-tier configuration reaches 66% governance accuracy with Constrained-F1 0.566 while answering a third of the questions — approaching the degenerate policy's safety while dominating it on the joint metric. The direction of the governance effect follows the stratum: on the answerable-heavy corpora naive retains higher governance accuracy (82.7% vs 75.9%; 79.1% vs 68.1%), and on the abstention-heavy corpus governance wins outright — the regime dependence the frontier quantifies. Observed on the study's designed abstention probe — ExpertQA was selected under the complementary-strata design precisely to stress this regime; replication on further abstention-heavy corpora is future work. The effect is not an artifact of the axis variant: plain G2 shows it too (GA 64.7%, CF1 0.559), and all nine configurations are reported.

> **Numbers:** GA 66.0% (G2+OntNU) vs 55.3% (G0); CF1 0.566 vs 0.502; refuse-all CF1 0.080 (H) / 0.350 (E); naive GA 82.7 / 79.1% on answerable-heavy corpora; plain G2: GA 64.7%, CF1 0.559
>
> **Sealed source:** all three frontier summaries; Analysis_CrossRun.md v4
>
> **Reinforces:** *The governed regime is not merely safer — on the right corpus it is more accurate: governance as value, not tax.*

**F6 Ontology fit orders the frontier's shape (exploratory)**

The fraction of extracted corpus concepts alignable to the reference ontology — 98.2% / 47.2% / 25.8% — orders the three coverage curves into slope, band, and cliff — in operator terms, the dial is usable through G4 (DelucionQA), through the G2 tier (ExpertQA), and only to G1 (HAGRID). A build-stage statistic thus anticipates what strict governance will cost before any evaluation. With three corpora the ordering could arise by chance; we claim an observation, not a validated predictor. The observation has a mechanism, however: low ontology alignment means the predicate filter authorises less — the same evidence-dropping F2 localises — so the prediction is causally plausible, and its pre-registered out-of-sample test is future work. Aligned share and graph richness co-vary on these corpora (concept graphs of 3,781 / 703 / 298 nodes) and cannot be separated at N=3 — a further reason for the exploratory label, and a design requirement for the out-of-sample test. Negative characterisation (an honest boundary): on the single-domain, triplet-sparse corpus the two axis variants could not act at all — ontology conformance was starved (\<1 triplet per record retrieved) and domain affinity degenerate (affinity ≡ 1.0 for all 5,037 chunks) — so the study also characterises when ontology-derived filters cannot be exercised.

> **Numbers:** M4 ontology-aligned share 98.2% (3,713/3,781, D) / 47.2% (332/703, E) / 25.8% (77/298, H) ↔ slope / band / cliff
>
> **Sealed source:** M4 build statistics in index\\corpus\> snapshots; Analysis_CrossRun.md v4; Evidence_Scoping_Finding.md (axis exercisability)
>
> **Reinforces:** *The ontology is not decoration — its fit to the corpus is the operative variable (contribution C6; seed of Paper 3).*

**F7 Appendix robustness study: the findings survive a judge change**

Run 1 was initially scored by the original judge; upon its withdrawal, all runs were scored by the successor, which is the paper's single primary judge. The initial scoring is retained as an appendix robustness study: on the 4,365 pairs where both judges graded an answer, agreement is 84.1% (κ=0.681), the successor is systematically more lenient (504 NO_MATCH→MATCH flips vs 190 reverse), refusal-side results are judge-invariant (G2 correct-refusal 0.7812 under both), and the frontier's structure is unchanged while accuracy levels shift. Per-configuration flips (computed from the sealed evaluation logs; reproducible join) show the disagreement concentrates in the ungoverned regime: net lenient flips +17.9% (G0) and +14.4% (G1) of graded pairs versus ≤+3.2% at G2–G4 — governed answers are markedly more judge-stable, and the successor's leniency favoured the baseline most, so H1's parity failure under the primary judge cannot be attributed to harshness toward governed answers. Both judges are from the same model family; the comparison bounds within-family judge variation, not judge bias in general — a cross-family check is future work. The comparison exists for run 1 only; runs 2–3 carry single-judge scoring.

> **Numbers:** κ=0.681 (graded pairs; 0.863 incl. refusals); flips 504 vs 190; net lenient flips +17.9 / +14.4 / +2.0 / +3.2 / −0.3% (G0..G4); Δacc(G1−naive): −.018 \[−.050,+.014\] initial vs −.065 \[−.090,−.041\] primary
>
> **Sealed source:** results\run1_delucionqa vs run1_rejudge (8,208 pairs under each judge)
>
> **Reinforces:** *Robustness by construction: conclusions rest on structure that two independent judges reproduce — and governed answers are the judge-stable ones.*

**F8 Governed evaluation is affordable**

A build-once/serve-many execution model reduces evaluation cost from O(n·C_build) to O(C_build + n·C_query). The full DelucionQA benchmark (912 questions × 9 configurations) was served and judged for \$222 on a \$498 build — about 2.7 cents per judged answer-pair — and the two additional corpora cost under \$45 combined (≈\$13–15 run 2; ≈\$30 run-3 block including run-2 tail, as recorded on the AI Studio spend page): the primary three-corpus evaluation ran for well under \$800 on commodity APIs. The reduced-corpus builds priced the cost model's terms empirically — build cost scales with corpus size (930 documents → \$498; 150-document selections → a few dollars each), serve cost with question count — making O(C_build + n·C_query) a measured property rather than an asymptotic claim. The recorded day totals include the failed and invalidated passes of those days (all-in day costs, not idealised marginal costs); all figures are API spend only, researcher time excluded. The appendix re-judge added one judging-only pass, documented in the spend evidence packs but not separately itemised.

> **Numbers:** T = D·C_build + n·C_query; \$498 build + \$222 serve/judge (run 1, ≈\$0.027/pair) + \<\$45 (runs 2–3) ≈ \$765 primary
>
> **Sealed source:** run manifests (Run2/Run3_Manifest.yaml, run-1 manifest) + API usage evidence packs
>
> **Reinforces:** *Feasibility is a contribution (C4): any team can afford to measure its own frontier.*

**3. Hypothesis ledger (pre-registered; report-regardless)**

| **H** | **Pre-registered statement (condensed)**                                                                                        | **Verdict**                                                                                                                 | **Evidence (spine ref)**                                                                                                                                                                                                                                                                                                                                                                          |
|-------|---------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| H1    | Quality parity on the answerable stratum: governed vs naive within ±0.05 equivalence bound                                      | NOT SUPPORTED under the primary judge (any corpus); borderline under the initial judge on run 1 only                        | Point Δ (per-arm answered-stratum accuracy): .034 (run 1, initial) / .080 (run 1, primary) / .138 (HAGRID) / .133 (ExpertQA). Paired bootstrap (identical resamples, B=10,000, seed 20260720, run 1): −.018 \[−.050,+.014\] initial / −.065 \[−.090,−.041\] primary. Reading: near-parity only in-ontology, within a judge-dependent 3–8-pt band; off-ontology the G1 cost is real (~13 pts) (F7) |
| H2    | Faithfulness superiority: governed adherence ≥ naive, hallucination \< naive                                                    | REFUTED                                                                                                                     | Both arms at ceiling ≥0.98 on every corpus (.98 vs .99 / 1.00 vs 1.00 / 1.00 vs .99) — consistently refuted; no superiority claim possible or made (F4)                                                                                                                                                                                                                                           |
| H3    | Selective abstention: correct-abstention ≫ naive AND wrong-refusal low; if wrong-refusal high → report as coverage-cost finding | SUPPORTED on the benefit on all three corpora; pre-registered coverage-cost branch triggered, extreme on the low-fit corpus | corrRef 75–78% vs 41–44% (F1); falseRej 51–85% at G2, 85–100% at G2+ on HAGRID (F2); parametric leakage on unanswerables falls 17.2% → 12.5% → 4.7–7.8% (naive → G1 → G2+, run 1)                                                                                                                                                                                                                 |
| H4    | Auditability: provenance + decision-log coverage ≈ 100%                                                                         | SUPPORTED                                                                                                                   | 97.7–100% on every corpus (F3)                                                                                                                                                                                                                                                                                                                                                                    |

*The ledger is the paper's integrity exhibit: one hypothesis refuted, one not supported under the primary judge, both reported plainly. Run-1 CIs computed; runs 2–3 carry point estimates only (bootstrap at probe-N pending, as the sealed analysis states). Wording condensed from docs\Analysis_Plan_and_Stopping_Rule.md (pre-registered, git-timestamped before execution).*

**4. Method minimum (what the venue paper must state)**

Pre-registered hypotheses, metrics, and stopping rule, publicly timestamped before execution; every deviation (model withdrawals, fixes) logged and pushed before the affected step ran. Models: build/extraction gemini-3.1-flash-lite; embeddings gemini-embedding-001; serving (governed and naive) gemini-3.5-flash; judge gemini-3.1-pro-preview — pinned by exact string, with every mid-study withdrawal and repoint recorded in the public deviation log. Three RAGBench corpora: DelucionQA complete (912 questions); HAGRID and ExpertQA by outcome-blind, deterministic document-reuse selection with a pre-committed junk-document filter (462 junk documents excluded on HAGRID), committed publicly before any generation (commit 54ef322; 163 and 150 questions). Representativeness is characterised against the full populations on system-independent observables, and the junk filter moved the ExpertQA selection closer to the population (answerable share 23.9% → 30.0%, vs 44.5% in the population). Serving is evidence-scoped: retrieval for each question is restricted to that question's own source documents (the benchmark's gold-context design), mapped to pipeline chunks by verbatim containment — 39.3 / 3.9 / 13.0 chunks scoped per question (means over the evaluated sets) on the three corpora. Questions whose admitted evidence yields no triplets enter a legitimate governed refusal state, not an error path. Nine configurations per question (G0–G4 plus ontology/affinity axis variants): 1,225 questions and 11,025 judged pairs, of which 8,208 were additionally re-judged by a second judge. The judge assigns each answer MATCH, NO_MATCH, or SAFE_SILENCE (a credited decline). Metrics: coverage, accuracy-on-adherent, faithfulness, the refusal triad (refusal, correct-refusal, correct-answer false-rejection), Constrained-F1 (CogniGraph's definition, for comparability), auditability, cost.

**5. System minimum (standalone)**

GovernRAG comprises a reference ontology (R; instantiated in our evaluation with the BIZBOK-derived enterprise reference vocabulary, 553 concepts), a governance-definition pipeline ending in the per-record Governance Manifest (D5: authorised predicates, ontology rules, domain affinity), a build pipeline (M1–M5: governed chunking, concept and triple extraction, concept graph, ontology alignment, governed index), and a query pipeline (intent gating, signature extraction, governed graph retrieval, residuals) in which the Q5 Reference Monitor admits or drops candidate evidence under the manifest, logging every decision, and Q6 cited synthesis enforces the chosen level's answer gate — answering with citations or refusing. Levels, which nest so that constraints only grow: G0 naive (the Q-pipeline is bypassed; retrieval straight to the model); G1 Cited (at least one retrieved chunk, citation required); G2 Grounded (at least one authorised chunk — one that passes the Q5 predicate filter — plus citation); G3 Strict (at least one authorised symbolic triplet, plus citation); G4 Corroborated (multiple triplets, or a triplet plus an independent agreeing authorised chunk). Within a level, two ontology-derived axis variants further filter admitted evidence: ontology conformance (triplets filtered by alignment status against the reference ontology) and domain affinity (chunks filtered by a domain-affinity score) — axes whose exercisability itself proved corpus-dependent (F6). Figures: 3_Figures\GovernRAG_Architecture_Simple Master.pptx (architecture — manuscript Figure 1 exports the diagram frame only, cropping the defence footer), GovernanceDial_Staircase.pptx (level semantics), Frontier_ThreeCorpora.png (results).

**6. Positioning minimum**

Knowledge graphs are used before generation (context: GraphRAG) or after generation (output verification: CogniGraph, SITL, HalluGraph). GovernRAG occupies the third position: authorization of the evidence admitted to generation. Prior governed systems report a single operating point; this work reports the per-level frontier. Constrained-F1 framing is the pre-committed Scenario B: our best-level CF1 (0.668 / 0.646 / 0.566, consistent judge) is reported as a secondary, within-system metric; claims rest on the frontier's shape. Within the study, Constrained-F1 spans the empirically contained refuse-everything policies (0.080–0.350) to the governed best (0.566–0.668) — the scale on which the within-system metric is read; cross-benchmark comparison with CogniGraph's 0.756 is not made. CogniGraph and SITL are not run as live baselines: they gate at a different pipeline position (post-generation output validation versus pre-admission evidence authorisation), their code and the MultiGov-30 benchmark are not available, and this work's claim is to characterise the curve that each of their operating points sits on — comparison is at the metric level, not on identical data. Guardrail: never “we beat CogniGraph”; always “we characterise the curve their operating point sits on.” Terminology follows the field's handles: risk–coverage frontier, selective prediction, abstention, fail-closed gating, reference monitor, Constrained-F1.

**7. Limitations minimum (pre-assembled for the manuscript)**

Both judges are from one model family (the robustness study bounds within-family variation; a cross-family check is future work). The dual-judge comparison covers run 1 only; runs 2–3 carry single-judge scoring and point estimates (bootstrap CIs at probe-N pending). Claims for HAGRID and ExpertQA are scoped to the selected corpora — generalisation probes of the frontier's shape, not population estimates. The faithfulness ceiling may partly reflect judge leniency on short cited answers (pre-registered caveat; discriminant check future work). Aligned share and graph richness co-vary at N=3 (the F6 confound). Each run executed once; no seed replication. Per-question latency was pre-registered but is not yet reported, and the \<2.3% unresolved citations on DelucionQA are not yet root-caused — both tracked in the technical queue (T2, T1) and resolved or disclosed as deviations before submission.

**Annex A — Defence layer (reference only; strip before any submission)**

The proposal-alignment map, hypothesis ledger for the committee, and defence materials are maintained in Dissertation_to_Paper2_Mapping.docx (same folder). The spine is the publication seed; the dissertation layer is out of scope for the manuscript and carries no content here.

**Review record**

*Topic-by-topic adversarial review, Topics 1–15, completed 2026-07-25 with Vivek: every finding statement re-verified against sealed archives; two numeric corrections found and fixed during review (F5 GA 65→66%; ExpertQA stratum 55→70% evaluated-set); two derived analyses added from sealed logs (per-config judge flips; refuse-all CF1 containment); one structural addition (§7 Limitations). Full S-item log: Master_Update_Queue.md. Technical queue: T1 (unresolved-citation root cause), T2 (latency extraction or deviation entry).*
