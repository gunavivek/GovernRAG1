> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\2_Design\Problem_Statement_Throughput.md (git mirror: repo docs\ where present) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Problem Statement — Throughput Bottleneck in Per-Query Knowledge-Artifact Materialization

## Abstract framing
Evaluating GovernRAG requires, for each (document, question) trial, (i) constructing a governance-bounded knowledge artifact — the D-pipeline **Governance Manifest** and the M-pipeline **knowledge graph** — and then (ii) resolving the query against it (Q + E pipelines) and scoring it. In the current evaluation harness the artifact is **re-materialized for every trial and then discarded**, so the achievable sample size *n* is bounded by

> **T_total = n · (C_build + C_query)**, with **C_build ≈ 3 h ≫ C_query**.

With C_build dominating, n ≈ 10 already costs ~30 h and n > a few dozen is infeasible. This prevents statistically meaningful evaluation (no confidence intervals, no power), which is the central empirical gap between the Level-1 existence proof (Paper 1) and the quantitative study the dissertation proposal requires.

## The underlying problem
The harness **conflates offline index construction (ingestion) with online query serving (retrieval)** and keeps **no persistent, reusable index**. Concretely, a *corpus-level* artifact (graph + manifest) is rebuilt at *query-level* granularity.

The required property is **build–query separation with index reuse** (a.k.a. offline-indexing / online-serving, build-once / query-many): construct the per-corpus artifact once and amortize it over many queries.

## Formal cost model
- **Current:** `T = n · (C_build + C_query)` → **O(n · C_build)** since C_build ≫ C_query.
- **Target:** `T = D · C_build + n · C_query`, where **D = number of distinct corpora** (often 1, since records are slices of one parent corpus) → **O(C_build + n · C_query)**.
- Because the query phase is stateless and embarrassingly parallel, the serve term reduces further to **n · C_query / P** for parallelism P.

Net effect: *n* becomes bounded by data availability, not by build time — enabling n > 1000.

## Sub-problems to solve
1. **Artifact persistence & addressability** — materialize the graph + manifest once and key them by corpus/record id (a read-only "index").
2. **Query-time serving without rebuild** — the Q-pipeline loads (not rebuilds) the index; load-once-in-memory or database-backed.
3. **Build determinism / reusability** — the index must be a valid, fixed artifact to reuse across all trials (LLM-based extraction must be pinned, or the index treated as a one-time frozen build).
4. **(Optional) incremental materialization** — append new documents without a full rebuild (relevant only if corpora evolve).

## Why this is an *execution-model* problem, not an architecture problem
Code inspection shows the pipelines already support the amortized pattern:
- `M3/M5` build a NetworkX **MultiDiGraph** whose forensic edge keys embed `record_id` → one graph holds many records.
- `D5` emits **per-record manifests** in a single multi-record JSONL.
- `Q3` already does `nx.read_graphml(global_graph)` and **prunes by `record_id`** (`filter_id`) at query time.

So a single global graph + manifest store can serve arbitrarily many queries by record-id filtering. The bottleneck is the *runner* (`A0_GovRAG_Runner`: one record per run into single-slot `output/`, then overwrite), not the pipeline logic.

## Relevant concepts / search terms (for prior art and solutions)
- "offline indexing vs online retrieval", "ingestion–retrieval decoupling" (RAG/IR systems)
- "index construction amortization", "build-once query-many", "amortized preprocessing"
- "materialized index / view reuse", "incremental materialization" (databases)
- "computation memoization / caching of intermediate artifacts" (pipeline/workflow systems)
- "knowledge-graph persistence & indexed subgraph query" (graph databases: Neo4j, Memgraph, KùzuDB)
- "vector/graph index persistence and reload" (FAISS/Chroma serialize; NetworkX `read/write_graphml`)
- experiment design: "shared fixture reuse across trials", "stateful test corpus"

## One-line statement (for a methods section)
*GovernRAG's evaluation throughput is bounded by per-query re-materialization of a corpus-level knowledge artifact; we remove this bound by separating one-time offline index construction from stateless online query serving with a persisted, record-addressable index, reducing total cost from O(n·C_build) to O(C_build + n·C_query) and enabling statistically powered evaluation (n ≫ 10³).*
