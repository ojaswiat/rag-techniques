# Guardrails.md

This document defines strict architectural constraints and explicit boundaries for this project. If you are an autonomous coding agent or developer script executing instructions, you are strictly prohibited from implementing or provisioning any system design component that violates these rules.

The primary objective of these guardrails is to enforce the project's **near-zero-spend operating model**: every recurring component must sit on a free tier or run locally on CPU. The binding constraint is **API request rate** (Groq per-day caps, LlamaParse monthly free credits), **not a dollar budget**. See `Budget.md` for the full cost reconciliation.

---

## 1. Absolute Infrastructure Ban: No Per-Hour or Scale-to-Non-Zero Infrastructure
You must never provision any continuously billing, persistent, or per-hour cloud infrastructure. All retrieval data indexing, processing, and array matching must occur completely inside local memory on the local execution machine.

* **No managed vector / search endpoints:** Do not provision managed vector databases, hosted search APIs, or any deployed index that charges continuous hourly server rates that do not scale to zero (e.g. Vertex AI Vector Search / Matching Engine, hosted Pinecone tiers, managed Discovery/Search APIs). These bill even when idle and break the $0 model.
* **No paid embedding or reranking APIs:** Do not call hosted, per-token embedding APIs (e.g. `text-embedding-004`, OpenAI `3-small`) or paid hosted rerankers (e.g. Cohere Rerank). Embeddings and re-ranking run **locally on CPU** (see §2).
* **Mandated Local Replacement:** Implement all vector and keyword indexing strictly via local Python libraries. For the active vector pipeline (Pipeline 3), use an in-memory or file-backed store (local **FAISS**, **ChromaDB**, or LlamaIndex's native local index storage). For the keyword pipeline (Pipeline 4), use a pure-Python statistical index — **`rank_bm25`**.
* **Banned even though "local":** Do **not** use LlamaIndex's `KeywordTableIndex` for Pipeline 4. It invokes an LLM to extract keywords at index/query time, so it is neither statistical nor deterministic and adds per-node API cost — it would invalidate the clean semantic-vs-statistical comparison. Use `rank_bm25` only.

---

## 2. Model Routing Matrix and Local Compute
All LLM calls run on **Groq's free tier** (open-source models, no credit card, rate-limited rather than billed). All retrieval-side compute (embeddings, re-ranking, BM25) runs **locally on CPU at $0**.

```text
+------------------------------------------------------------------------+
|                      MANDATED MODEL ASSIGNMENT MAP                     |
+------------------------------------------------------------------------+
|  Phase 1: Dataset Generation   --> Llama 3.3 70B (Groq free tier)       |
|  Phase 1: Dataset Critique      --> Qwen3 32B    (Groq free tier)       |
|  Phase 2: RAG Pipeline Retrieval--> Local CPU (bge embeddings /         |
|                                     bge-reranker / rank_bm25), $0       |
|  Phase 3: Automated Evaluation  --> Llama 3.3 70B (Groq free tier)      |
+------------------------------------------------------------------------+

```

* **Cross-family Generator/Critic:** The Generator (Llama 3.3 70B) and Critic (Qwen3 32B) must remain **different model families** so dataset agreement reflects cross-architecture consensus rather than a model agreeing with itself.
* **Open-model context cap:** Open models cap at a ~128K-token context window — far short of a full 10-K. Generation must operate **per-section (chunked)**; you must monitor context length in the generator script and never attempt to inject an entire filing in a single call.
* **Local retrieval models:** Embeddings use `BAAI/bge-small-en-v1.5`; re-ranking uses `BAAI/bge-reranker-base`. Both run on CPU without a GPU. Persist generated embeddings to a local cache / SQLite immediately so they are never recomputed.
* **Throwaway debugging:** Use a smaller, higher-limit model (e.g. `llama-3.1-8b-instant`) for any throwaway debugging, reserving the 70B model's tighter daily cap for real generation and judging.

---

## 3. Mandatory Dynamic Few-Shot Filtering

You are strictly prohibited from building a single static prompt template containing all 12 human-evaluated "Gold Standard" benchmark items.

* **The Throughput Problem:** Passing all 12 robust examples (query, ground truth, output, 1–10 scoring matrix, and full qualitative reasoning) introduces a structural ~6,000-token payload overhead per interaction. Replicating this across 600 automated evaluation runs burns millions of unnecessary input tokens and mixes table-grading and text-grading exemplars indiscriminately.
* **The Mandatory Code Implementation:** The evaluation script inside `async_judge.py` must query the central SQLite database dynamically. Before a pipeline output is evaluated, the script must look up the target query's category quadrant (e.g., `Q1_Direct_Text` vs `Q4_Implicit_Table`) and construct a dynamic system prompt containing **exactly 3 contextual examples** matching that specific quadrant (`WHERE is_golden = 1 AND quadrant = :current_quadrant`). The remaining 9 examples must be completely omitted from the payload.

---

## 4. Execution Loops and Local Safety Throttling

To protect against runaway request loops, infinite recursive functions, or unhandled file reading exceptions, you must embed programmatic execution caps inside all iteration scripts.

* **Mandatory Test-Brake Variable:** Every loop script (`async_generator.py`, `loop_executor.py`, and `async_judge.py`) must contain a hardcoded Boolean configuration variable named `LOCAL_TEST_THROTTLE` at the top of the file.
* **Throttle Execution Logic:** When `LOCAL_TEST_THROTTLE = True`, the script must force a strict database fetch cap, restricting execution to **exactly 3 data items** (e.g., using `LIMIT 3` inside the SQL statement).
* **Removal Protocol:** You must run the entire workflow sequentially — document ingestion, synthesis, pipeline generation, and judge evaluation — under `LOCAL_TEST_THROTTLE = True` to verify data integrity. Only when an entire 3-item run concludes successfully without error codes may the throttle be set to `False` to release the full batch.

---

## 5. Concurrency and Rate Limiting Enforcement

Asynchronous worker pools running many free-tier lookups simultaneously can exceed Groq's Token-Per-Minute (TPM) and Requests-Per-Minute (RPM) quotas, causing HTTP 429 errors, script crashes, and half-written data tables.

* **Resilience Dependency:** You must wrap all cloud API request loops using a resilient wrapper library (such as `tenacity`).
* **Mandatory Exception Handling:** Catch all HTTP 429 exceptions (Rate Limit Exceeded) explicitly. The connection code must use **exponential backoff with randomized jitter**. If a rate cap is triggered, the script must pause, back off smoothly, and retry without terminating the pipeline mid-run.
* **Queue Bounds:** Cap max concurrent tasks within an `asyncio.Semaphore` to a maximum of 5 parallel workers unless initial token analysis confirms a higher ceiling is safe under Groq's published per-organization limits. Note: free-tier limits apply **per organization**, not per API key — creating extra keys does not raise the ceiling.

---

## 6. Relational Data Management and State Persistence

Writing execution outputs directly to raw CSV files or nested JSON blocks is strictly forbidden for long-running batches.

* **The Crash Risk:** If an asynchronous loop encounters an unhandled runtime error or connection loss partway through a run (e.g. run 450 of 600), appending data to an uncommitted flat text file can corrupt or erase previous records.
* **Mandatory Architecture:** A local relational database configuration file (`database_manager.py`) must isolate schemas into distinct relational structures (`nodes`, `queries`, and `results`).
* **State Commits:** The pipeline execution script must perform a SQL commit immediately after each independent run completes. If the system crashes mid-execution, the worker must check the database table for existing records and resume cleanly from the last successfully written row instead of re-running past inputs and consuming extra free-tier requests.

---

## 7. Single Hard Rule

> **No component in this project may bill per-hour or scale-to-non-zero.** All retrieval and indexing run locally; all LLM calls run on a free tier with request-rate limits, not spend. If any design change would introduce a persistent or per-hour cloud charge (e.g. a managed vector DB endpoint, a hosted reranker, a premium parse tier), it must be re-scoped back to a local or free-tier equivalent before implementation. This is the authoritative infrastructure ban referenced by `Budget.md`.
