# Guardrails.md

This document defines strict architectural constraints and explicit boundaries for this project. If you are an autonomous coding agent or developer script executing instructions, you are strictly prohibited from implementing or provisioning any system component that violates these rules.

The primary objective is to enforce the project's **near-zero-spend operating model** (every recurring component on a free tier or local CPU) **and** the **role-separation and anti-leakage rules** that make the automated evaluation academically defensible. The binding cost constraint is **Groq's per-day token throughput (TPD)**, not a dollar budget. See `Budget.md` for the full cost reconciliation and `Project_Idea.md` for the methodology.

---

## 1. Absolute Infrastructure Ban: No Per-Hour or Scale-to-Non-Zero Infrastructure
You must never provision any continuously billing, persistent, or per-hour cloud infrastructure. All retrieval indexing, processing, and matching must occur in local memory on the execution machine.

* **No managed vector / search endpoints:** no managed vector databases, hosted search APIs, or deployed indexes that charge hourly and do not scale to zero (e.g. Vertex AI Vector Search, hosted Pinecone tiers, managed Discovery/Search APIs).
* **No paid embedding or reranking APIs:** no hosted per-token embedding APIs (`text-embedding-004`, OpenAI `3-small`) or paid hosted rerankers (Cohere Rerank). Embeddings and re-ranking run **locally on CPU** (see §2).
* **Mandated local indexing:** for the vector pipeline (P1) use an in-memory or file-backed local store (local **FAISS**, **ChromaDB**, or LlamaIndex's native local storage). For the keyword pipeline (P2) use the pure-Python **`rank_bm25`**. For the structural pipeline (P3) use a local **`SummaryIndex`** persisted to disk.
* **P2 must remain purely statistical:** do **not** use LlamaIndex's `KeywordTableIndex` for P2. It invokes an LLM to extract keywords at index/query time, so it is neither statistical nor deterministic and adds per-node API cost — it would invalidate the clean semantic-vs-statistical comparison. **Use `rank_bm25` only.**
* **P3's LLM summary build is explicitly permitted (and is not a §1 violation):** unlike the banned `KeywordTableIndex`, P3's hierarchical summarisation is *the paradigm under test*, so its use of an LLM at index-build time is legitimate and disclosed. It must use the free-tier `llama-3.1-8b-instant`, run **once**, and be **cached to disk** — never rebuilt per query and never run on a per-hour endpoint. P3's LLM use is confined to this one-time build; P3 retrieval at query time is local.

---

## 2. Model Routing Matrix and Local Compute (per-stage LLM assignment)

All LLM calls run on **Groq's free tier** (open-source models, no credit card, rate-limited rather than billed). All retrieval-side compute (embeddings, re-ranking, BM25, P3 traversal) runs **locally on CPU at $0**. The model assigned to each stage is fixed:

```text
+------------------------------------------------------------------------+
|                      MANDATED MODEL ASSIGNMENT MAP                     |
+------------------------------------------------------------------------+
|  STAGE                          MODEL                      WHERE        |
|  -----------------------------  -------------------------  ----------   |
|  Dataset generation             openai/gpt-oss-120b        Groq free    |
|  Dataset critique (+ search)    Qwen3.6-27B                  Groq free    |
|  P3 summary-index build (1x)    llama-3.1-8b-instant       Groq free    |
|  Pipeline answers (P1/P2/P3)    Llama 3.3 70B  (SHARED)    Groq free    |
|  Judge / scoring (no search)    Qwen3.6-27B                  Groq free    |
|  -----------------------------  -------------------------  ----------   |
|  Embeddings (P1)                bge-small-en-v1.5          Local CPU $0 |
|  Re-ranker (P1)                 bge-reranker-base          Local CPU $0 |
|  BM25 (P2)                      rank_bm25                  Local CPU $0 |
|  Throwaway debugging            llama-3.1-8b-instant       Groq free    |
+------------------------------------------------------------------------+
```

### Mandatory role-separation rules
* **Generator ≠ Critic.** The Generator (`gpt-oss-120b`) and Critic (`Qwen3.6-27B`) must remain **different model families**, so dataset agreement reflects cross-architecture consensus rather than a model agreeing with itself.
* **Answerer ≠ Judge.** The pipeline answerer (`Llama 3.3 70B`) and the Judge (`Qwen3.6-27B`) must remain **different families**. No model may grade its own output. If the Judge is later swapped (e.g. to `gpt-oss-120b` to pass the §4 gate), it must still differ from the Llama answerer.
* **Shared answerer across pipelines.** All three pipelines (P1/P2/P3) must use the **same** answerer (`Llama 3.3 70B`) at the **same** generation settings. Differences in scores must come from *retrieval*, not from different answer models — otherwise the experiment measures generation, not retrieval.
* **Critic has a search tool; the Judge does not.** The Critic must be given a search tool over **all nodes of the filing** (independence requires searching beyond the source section). The Judge must **not** have a search tool — it already receives the ground-truth answer and citations and only needs to score the output against them. Adding search to the Judge is cost for no gain.

### Local-compute and context rules
* **Open-model context cap.** Open models cap at ~128K tokens — far short of a full 10-K. Generation must operate **per-section (chunked)**; the generator script must monitor context length and never inject an entire filing in one call.
* **Local retrieval models.** Embeddings use `BAAI/bge-small-en-v1.5`; re-ranking uses `BAAI/bge-reranker-base`. Both run on CPU. Persist embeddings/indexes to local cache / SQLite immediately so they are never recomputed.
* **Determinism.** All LLM calls run at **`temperature = 0`**. Each of the 900 benchmark cells is run **once**; do not add repeated runs (they multiply token cost without adding signal at temperature 0). Any robustness repeats are confined to the JEQ validation subset.

---

## 3. Anti-Leakage: What Each Model May and May Not See

Leakage between the teaching, validation, and test data — or handing the pipelines anything they should have to *retrieve* — would invalidate the results. The following are hard rules.

* **The three query sets are disjoint.** `queries` (100 PQ), `golden_queries` (20 GQ), and `judge_validation` (20 JEQ) must contain **non-overlapping** queries. No query may appear in more than one table.
* **Pipelines receive retrieved context + the question only.** The P1/P2/P3 answerer must **never** be given few-shot exemplars, the ground-truth answer, the ground-truth citations, or any answer-location hint. Anything beyond the question and the nodes its own retriever returned is leakage.
* **No metadata pre-filter / "section head-start" for P1.** The earlier optimized-vector design narrowed search to a target Item before retrieval. That step is **removed**: deciding the section at query time risks deriving it from ground truth (peeking at the answer key), and P2 has no equivalent step, so it would make the comparison unfair. P1 is a clean embeddings-plus-reranker pipeline. (A pre-filter ablation, with the section derived strictly from the *question*, is a permissible documented extension — never from `gt_citations`.)
* **Teaching set (GQ) feeds the Judge only.** The 20 GQ exemplars are injected into the **Judge's** prompt (per §4) — never into any pipeline.
* **Validation set (JEQ) feeds no prompt.** The 20 JEQ exist solely to be hand-scored and judge-scored for the §4 agreement gate. They must **never** be injected as exemplars into the Judge or the pipelines.

---

## 4. Judge Few-Shot Filtering and the Mandatory Validation Gate

### 4a. Dynamic few-shot filtering
You are prohibited from building a single static prompt containing all 20 GQ exemplars (it mixes table- and text-grading examples and bloats every call).

* Before scoring an output, `async_judge.py` must read the target query's quadrant and construct a prompt containing **exactly the 5 GQ exemplars matching that quadrant** (`WHERE quadrant = :current_quadrant` against `golden_queries`). The other 15 must be omitted.
* This yields **four cacheable prompt prefixes** (one per quadrant: rubric + 5 exemplars). Cache them — cached tokens do not count toward Groq limits.

### 4b. The judge-validation gate (hard prerequisite for the full run)
The automated Judge must be proven against the human standard **before** it grades the 900-run benchmark.

* **Procedure:** run the 20 JEQ through P1, P2, and P3 at a **single K = 5** → 60 outputs. The researcher hand-scores all 60; the Judge scores the same 60 (using 4a); the **human–judge Agreement Rate** is computed across the 60.
* **Gate:** the full 900-run judging phase may begin **only** once Agreement Rate **> 80%**. If it is not met, change the Judge's rubric and/or model (e.g. swap to `gpt-oss-120b`, still ≠ the Llama answerer) and re-run the check. Do **not** run the full matrix with an unvalidated judge.
* **Citation matching is code, not LLM.** The check "are the output's cited node IDs a subset of `gt_citations`?" must be computed deterministically in code, not delegated to the Judge.

---

## 5. Concurrency and Rate-Limiting Enforcement

Asynchronous worker pools running many free-tier calls simultaneously can exceed Groq's TPM/RPM quotas (and, over a long run, the TPD ceiling), causing HTTP 429 errors, crashes, and half-written tables.

* **Resilience dependency:** wrap all Groq API calls in a resilient wrapper (e.g. `tenacity`).
* **429 handling:** catch HTTP 429 explicitly and apply **exponential backoff with randomized jitter**; pause and retry smoothly rather than terminating mid-run.
* **Queue bounds:** cap concurrency with an `asyncio.Semaphore` to **≤ 5 parallel workers** unless token analysis confirms a higher ceiling is safe under Groq's published per-organization limits. Limits apply **per organization**, not per key — extra keys do not raise the ceiling.
* **TPD-aware pacing:** because the answerer (`Llama 3.3 70B`, ~100K TPD) is token-bound, long phases must be paced/spread across days (with §6 resume) rather than hammered in one session.

---

## 6. Relational Data Management and State Persistence

Writing outputs to raw CSV or nested JSON is forbidden for long-running batches.

* **Crash risk:** appending to an uncommitted flat file mid-run (e.g. run 700 of 900) can corrupt prior records.
* **Mandatory schema:** a local SQLite configuration (`database_manager.py`) must isolate **five** tables: `nodes`, `queries` (100 PQ), `golden_queries` (20 GQ), `judge_validation` (20 JEQ — question and ground-truth fields only), and `results` (every pipeline run: the 900 PQ benchmark rows plus the 60 JEQ gate-validation rows, distinguished by a `source_set ∈ {PQ, JEQ}` column — 960 rows total). See `Architecture.md` §3 for the full DDL.
* **State commits:** commit after each independent run. On restart, the worker must check `results` for existing rows and **resume from the last written row** instead of re-running inputs and consuming extra free-tier requests/tokens.
* * **WAL mode for concurrent writes:** SQLite serializes writes, so the bounded async worker pool (§5) can occasionally hit `database is locked`. Enable Write-Ahead Logging at startup (`PRAGMA journal_mode=WAL;`) so readers and the writer don't block each other, and let the `tenacity` wrapper retry the rare lock. With ≤ 5 workers each committing a single row, this fully removes lock contention — no need to switch to a client-server database (Postgres/MySQL), which would add a persistent server process for concurrency this project never requires.
* **`judge_validation` holds question/ground-truth fields only, written once at generation time** (`query_id`, `quadrant`, `query_text`, `ground_truth_answer`, `gt_citations`, `document_id`) and is never updated afterward. It has no per-row "pipeline output" column, because the Phase-2 gate runs each of the 20 JEQ through **three** pipelines (P1, P2, P3) — 60 outputs — which a 20-row table cannot hold without breaking normal form. Those 60 outputs, plus their `judge_score` and `human_score`, are written instead into `results` (tagged `source_set = 'JEQ'`), in the same row shape as the 900 PQ rows. The agreement rate compares `results.human_score` against `results.judge_score` across those 60 `source_set = 'JEQ'` rows.

---

## 7. Execution Loops and Local Safety Throttling

To protect against runaway loops, infinite recursion, or unhandled file exceptions, every iteration script must embed a programmatic cap.

* **Mandatory test-brake variable:** every loop script (`async_generator.py`, `async_critic.py`, `loop_executor.py`, `async_judge.py`, and the P3 summary-build script) must contain a hardcoded boolean `LOCAL_TEST_THROTTLE` at the top of the file.
* **Throttle logic:** when `LOCAL_TEST_THROTTLE = True`, force a strict fetch cap to **exactly 3 data items** (e.g. `LIMIT 3` in the SQL).
* **Removal protocol:** run the entire workflow — ingestion, P3 build, generation, critique, pipeline answering, and judging — under `LOCAL_TEST_THROTTLE = True` first. Only after a clean 3-item end-to-end run may the throttle be set to `False` to release the full batch.

---

## 8. Single Hard Rule

> **No component in this project may bill per-hour or scale-to-non-zero.** All retrieval and indexing run locally; all LLM calls run on a free tier with request/token-rate limits, not spend. P3's one-time summary build uses a free-tier LLM and is cached. If any design change would introduce a persistent or per-hour cloud charge (a managed vector DB endpoint, a hosted reranker, a premium parse tier), it must be re-scoped to a local or free-tier equivalent before implementation. This is the authoritative infrastructure ban referenced by `Budget.md`.