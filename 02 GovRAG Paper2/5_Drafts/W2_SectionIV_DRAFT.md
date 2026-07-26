*W2 --- §IV draft v3 · 26 July 2026 · ALL SUBSECTIONS APPROVED: IV.A keep, IV.B good, IV.C simplified + exact means (39.3/3.9/13.0), IV.D T2 latency sentence in · not yet poured into the IEEE shell · every number verbatim from spine v2.2 §4 / Analysis Plan*

**IV. EVALUATION DESIGN**

***A. Pre-registration and integrity protocol***

The study was pre-registered: hypotheses, metrics, and the stopping rule were committed to a public repository and timestamped before any generation ran. Every deviation that arose during execution --- model withdrawals by the provider, harness fixes --- was recorded in a deviation log and pushed before the affected step executed, so the log\'s timestamps bound each change to its place in the study. Models were pinned by exact identifier: build and extraction used gemini-3.1-flash-lite, embeddings gemini-embedding-001, serving (governed and naive arms alike) gemini-3.5-flash, and judging gemini-3.1-pro-preview. Mid-study model withdrawals and the resulting repoints are themselves entries in the public deviation log \[repo citation --- anonymised link at W6\]. Sealed run archives carry SHA-256 manifests, so every reported number is traceable to a hashed artefact.

***B. Corpora and selection***

We evaluate on three corpora from RAGBench, chosen for complementary unanswerable strata: DelucionQA (automotive troubleshooting; evaluated in full, 912 questions, of which 7.0% are unanswerable), HAGRID (attributable information-seeking, 163 questions, 16.0% unanswerable), and ExpertQA (expert-curated questions, 150 questions, 70.0% unanswerable in the evaluated set). The strata span the regimes a governed system must face: answer-heavy, mixed, and abstention-heavy.

Because HAGRID and ExpertQA were evaluated on subsets, selection was outcome-blind and deterministic: questions were selected by a document-reuse criterion computed on system-independent observables, with a pre-committed junk-document filter (462 junk documents excluded on HAGRID), and the selection code and lists were committed publicly before any generation ran \[commit id in repo citation\]. Representativeness is characterised against the full populations on system-independent observables; the junk filter moved the ExpertQA selection closer to the population (answerable share 23.9% to 30.0%, against 44.5% in the population), and we scope all claims for these two corpora to the selected sets.

***C. Configurations and serving protocol***

Each question is served under nine configurations: the five governance levels G0--G4, plus ontology-conformance and domain-affinity axis variants at the applicable levels. Across 1,225 questions this yields 11,025 judged pairs, of which 8,208 were additionally re-judged by a second judge. Serving is evidence-scoped. Each benchmark supplies, for every question, the source documents that the question is meant to be answered from; retrieval therefore searches only those documents, never the whole corpus. We map each question\'s documents to the pipeline\'s chunks by exact text match, giving every question its own scoped evidence pool --- on average 39.3 chunks on DelucionQA, 3.9 on HAGRID, and 13.0 on ExpertQA. The governed and naive arms share the same serving model and the same scoped evidence, so the arms differ only in governance. Questions whose admitted evidence yields no triplets enter the governed refusal state by design; they are counted as refusals, not errors.

***D. Judging and metrics***

Every answer is judged against the benchmark\'s gold answer and assigned MATCH, NO_MATCH, or SAFE_SILENCE --- the last a credited decline, so that governed refusal is scored as a decision, not a failure. Primary results use a single judge (gemini-3.1-pro-preview) across all three corpora. The 8,208 re-judged pairs, scored independently by a second judge, form an inter-judge robustness study reported in the appendix; agreement and its effect on each finding are quantified there rather than assumed.

We report: coverage (the fraction of questions answered); accuracy on the answered stratum; faithfulness (adherence of answered content to admitted evidence, with hallucination-on-answered as its complement); the refusal triad --- refusal rate, correct-refusal rate on unanswerable questions, and false rejection, the refusal of answerable ones; auditability (the fraction of outputs whose citations resolve to admitted evidence in the logs); and cost. Constrained-F1 is computed under CogniGraph\'s published definition and reported as a secondary, within-system metric for comparability; our claims rest on the frontier\'s shape, not on cross-benchmark metric comparison. Per-question latency is reported as amortised serving time from logged per-batch wall-clock: 15.0 s per question on DelucionQA, 7.4 on HAGRID, and 10.8 on ExpertQA; signature extraction dominates (58--93% of stage time), while reference-monitor enforcement contributes under 1%.

**Reviewer notes (not part of the manuscript)**

-- Length: \~700 words ≈ 1.2 pp two-column --- inside the 1.25 pp budget, T2 latency sentence included (15.0/7.4/10.8 s/q amortised, from sealed timing logs).

-- Every number verbatim from spine v2.2 §4: 912/163/150; 7.0/16.0/70.0%; 462 junk docs; 23.9→30.0 vs 44.5%; \~36/3.9/13 chunks; 9 configs; locked pair-count phrase; model pins by exact string.

-- Stopping rule: named in A as pre-registered; its content (what rule) is stated in the Analysis Plan --- decide at review whether one sentence summarising it belongs here or stays in the repo citation.

-- Double-blind: repo/deviation-log citations enter as anonymised links at W6 (e.g. anonymous.4open.science); commit id 54ef322 quoted only inside the anonymised citation.

-- T2 marker in D: resolved after this review, before pour, per agreed sequencing (W2 → T1+T2 → W3).

-- Dual-judge protocol wording follows the locked judge-policy note (U4): primary = successor judge; run-1 initial scoring = appendix robustness study.
