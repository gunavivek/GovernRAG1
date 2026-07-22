> **SNAPSHOT 2026-07-22** — read-only copy for paper writing. CANONICAL: OneDrive Paper2\2_Design\BuildServe_Refactor_Plan.md (git mirror: repo docs\ where present) — edit the canonical, then re-snapshot. See Source_Register.docx.

# Build–Serve Refactor Plan — Unbounding *n* for the RAGBench Evaluation

**Goal:** move from n ≈ 10 (per-query rebuild) to n ≫ 1000 by building the GovernRAG index once per corpus and serving all questions against it. Corpus choice: **enterprise-like RAGBench subsets** (FinQA, CUAD, TechQA), which fit the BIZBOK anchoring and avoid the orphan-patch.

---

## 1. What the code actually does today (inspection findings)
| Component | Behaviour | Implication |
|---|---|---|
| `A0_GovRAG_Runner.py` | Orchestrates D00→D0→M0→Q0→E2→Z0 for **one record per run**, writing to single-slot `output/` | Build is coupled to a single query and overwritten each run |
| `M3 / M5` | Build a NetworkX **MultiDiGraph**; persist `output/M5_Embedded_Graph.graphml`; edge keys carry `record_id` | **Graph is already multi-record** |
| `D5` | Per-record manifests in one `D5_Extraction_Manifest.jsonl` | **Manifest store is already multi-record** |
| `Q3` (`Q3_..._Retrieval_Engine`) | `nx.read_graphml(M5_Embedded_Graph.graphml)` then **prunes by `record_id`** (`filter_id`) | **Per-record serving from a global graph already works** — but it re-reads the graphml on every instantiation |
| `Q0` | Loads + runs Q1..Q6 for a given `record_id` (no rebuild) | Serve path is already load-based |

**Conclusion:** the expensive D+M build is corpus-capable; the harness simply runs it per record and discards it. The refactor is an **orchestration + persistence** change, not a pipeline rewrite.

---

## 2. Target design — two phases

### Phase 1 — BUILD (once per dataset/corpus)
1. Stage the **full parent corpus** as a multi-record JSONL (every slice/document as a record), instead of one-record-per-question.
2. Run `D0` → `M0` **once** → produces one multi-record `D5_Extraction_Manifest.jsonl` + one global `M5_Embedded_Graph` covering all records.
3. Persist as a **read-only, keyed index**:
   ```
   index/<dataset>/
       D5_Extraction_Manifest.jsonl
       M1_Governed_Chunks.csv
       M5_Embedded_Graph.graphml      (or load into a graph DB — §4)
       build_manifest.json            (corpus id, record count, model, hash, timestamp)
   ```
   → **C_build paid once per dataset**, never per question.

### Phase 2 — SERVE (per question; looped + parallel)
1. Load the index **once** (a long-lived graph object or a DB connection), reused across all questions.
2. For each question: `Q0(record_id)` + `E2` (Naive baseline) + **TRACe scoring** → answer, citations, governance log, metrics.
3. Write results to `results/<dataset>/...`; **parallelize** across questions (they are independent).
   → **C_query in minutes (or seconds), n unbounded.**

---

## 3. Concrete, minimal-risk changes
1. **New stager** (adapt `A0_RAGBench_PerQuestion_Stager`): emit the full parent corpus as multi-record, not per-question.
2. **New build runner** (adapt `A1_RAGBench_D0_M0_Runner`): run D0→M0 once over the full corpus; write to `index/<dataset>/` (keyed, not single-slot `output/`).
3. **Refactor Q3 + Q5 to read the index path and load the graph ONCE** (a service object created before the question loop), instead of re-reading `output/M5_Embedded_Graph.graphml` per question. Keep the existing `record_id` filtering as-is.
4. **New serve runner**: `for q in questions: Q0(record_id_of(q)) + E2 + eval`, reading from `index/<dataset>/`, writing to `results/<dataset>/`. Add a worker pool for parallelism.
5. **Add the TRACe metric step** (the missing harness) in the eval — Relevance, Utilization, Completeness, Adherence — wired to RAGBench gold annotations + the generated answer/context.

These touch the *runners and the Q3/Q5 I/O*, not the governance logic (D/M/Q internals stay frozen).

---

## 4. Storage decision — GraphML vs Graph database
**Recommendation: do (A) first for the immediate win; adopt (B) when the corpus graph outgrows RAM or you want incremental/concurrent builds.**

**(A) Keep GraphML, load-once-serve-many (fastest, ~1–2 days).**
- Refactor Q3 to load the global graph a single time into a reused object; the question loop never reloads.
- Removes *both* the rebuild and the per-query graphml reload.
- Works well if one enterprise-subset graph fits in RAM (verify by profiling — §6).

**(B) Embedded / server graph database (for scale, incremental, concurrency).**
- Persist the graph in a DB; `Q3` queries by `record_id` via an **indexed** lookup (no whole-graph load), supports concurrent question serving and incremental corpus updates.
- **KùzuDB** — embedded (no server), Cypher, columnar, fast, has vector indexes; ideal for a single-researcher reproducible pipeline. Lowest ops overhead.
- **Neo4j** — industry standard, great tooling/Browser, vector index in v5; heavier (server) but well-documented.
- **Memgraph** — in-memory, very fast, Cypher; good if the graph fits in RAM but you want DB semantics.
- The M5 graph also carries embeddings, so a DB with a **vector index** (Neo4j 5 / Kùzu) can unify symbolic + dense retrieval and remove the separate FAISS/embedding step.

**Practical path:** GraphML load-once now → if the FinQA/CUAD graph is too big for RAM or you want to keep appending corpora, port the persisted graph to **KùzuDB** (least friction) and have Q3 issue a record-scoped Cypher query.

---

## 5. Throughput math
| Setup | n = 1000 | Notes |
|---|---|---|
| Current (rebuild per query) | ~3,000 h | infeasible |
| GraphML load-once, serial serve | C_build (hrs, once) + 1000·C_query | if C_query ≈ 1–2 min → ~1 day |
| + parallel serve (P=8) | C_build + 1000·C_query/8 | hours |
| Graph DB, record-scoped query | C_build + 1000·(indexed query) | no whole-graph RAM load; concurrent |

---

## 6. Risks / things to verify before committing
- **Governance granularity:** decide whether each parent-corpus *document* is a `record` (per-document manifests inside a shared graph — preserves the governance story) or the whole corpus is one record (simpler, weaker governance claim). This choice should match Paper 2's claim ("governance at parity").
- **Build determinism:** M2 triple extraction is LLM-based. To *reuse* the index legitimately, either pin model/temperature/seed, or treat the build as a **frozen one-time artifact** for the study (acceptable, and you already froze the code).
- **Memory profile:** build the index on one enterprise subset first and measure graph size + RAM before choosing GraphML-in-memory vs DB.
- **BIZBOK orphan-patch:** with enterprise subsets, D2 should anchor without heavy patching — confirm the orphan rate drops vs the manuals.
- **Record↔question linkage:** confirm how RAGBench `record_id` maps questions to parent-corpus slices (quick check of `*_parent.jsonl` / `*_questions.jsonl`).

---

## 7. Recommended next steps (in order)
1. **Confirm data structure** — inspect `*_parent.jsonl` vs `*_questions.jsonl` to lock the record↔question key.
2. **Build the index once on one enterprise subset** (start with FinQA) → measure C_build, graph size, RAM.
3. **Implement Q3/Q5 load-once + a serial serve loop + TRACe scoring** → measure C_query on ~50 questions.
4. **Parallelize the serve loop**, scale to n ≫ 1000.
5. **Decide GraphML-in-memory vs KùzuDB/Neo4j** based on the measured graph size and whether you want incremental corpora.

This unbounds *n* without changing the governance architecture — exactly the unlock needed to turn Paper 1's existence proof into Paper 2's statistically powered evaluation.
