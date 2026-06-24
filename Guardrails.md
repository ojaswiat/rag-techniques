# Guardrails.md

This document defines strict architectural constraints and explicit boundaries for this project. If you are an autonomous coding agent or developer script executing instructions, you are strictly prohibited from implementing or provisioning any system design component that violates these rules. 

The primary objective of these guardrails is to prevent accidental or unthrottled cloud API use, protecting our hard project ceiling of $150.00 in Google Cloud credits.

---

## 1. Absolute Infrastructure Ban: No Managed Cloud Endpoints
You must never provision any continuously billing, persistent infrastructure on Google Cloud. All retrieval data indexing, processing, and array matching must occur completely inside local memory on the local execution machine.

* **Banned Component: Vertex AI Vector Search (Matching Engine):** Do not call or write code referencing `aiplatform.MatchingEngineIndex` or deploy endpoints using Google Cloud virtual machine nodes (such as `e2-standard-2`). Managed indexes charge continuous hourly server rates that do not scale to zero, which will exhaust the credit budget within weeks even if completely idle.
* **Banned Component: Vertex AI Agent Builder / Discovery Engine:** Do not build datastores using the managed Search API ($1.50 to $4.00+ per 1,000 queries). 
* **Mandated Local Replacement:** You must implement all vector and keyword indexing strictly via local Python libraries. For Pipeline 2 and Pipeline 3, use an in-memory or file-backed storage client (such as local **FAISS**, **ChromaDB**, or LlamaIndex's native local memory index storage). For Pipeline 4, use a pure python-based statistical keyword index (such as **rank_bm25** or LlamaIndex's local `KeywordTableIndex`). 
* **Embedding Constraints:** You are authorized to use the online Vertex Text Embeddings API (`text-embedding-004`) to generate text arrays, as it charges dynamically per token fraction rather than a flat hosting fee. Save these generated arrays locally to a cache file or to the local SQLite storage immediately.

---

## 2. Model Routing Matrix and Payload Caps
To minimize token transaction costs, you must carefully segment and assign model tasks based on pricing tiers. 

```text
+------------------------------------------------------------------------+
|                      MANDATED MODEL ASSIGNMENT MAP                     |
+------------------------------------------------------------------------+
|  Phase 1: Dataset Generation (High Complexity)  --> Gemini 1.5 Pro      |
|  Phase 1: Dataset Critique (Validation)        --> Gemini 1.5 Flash    |
|  Phase 2: RAG Pipeline Generation (Bulk Work)   --> Gemini 1.5 Flash    |
|  Phase 3: Automated Evaluation (Bulk Scoring)   --> Gemini 1.5 Flash    |
+------------------------------------------------------------------------+

```

* **Gemini 1.5 Pro Restrictions:** Authorized only for reading the comprehensive context chunks to synthesize the initial 400 validation questions.
* **The 200K Threshold Cost Trap:** Gemini 1.5 Pro input rates double if a single prompt payload crosses 200,000 tokens. You must monitor context length within the generator script and enforce a hard payload limit well below 150,000 tokens per call.
* **Gemini 1.5 Flash Mandate:** Every bulk-execution component—including the 400 question verifications, the 4,000 pipeline RAG text generation runs, and the 4,000 evaluation system lookups—must run exclusively on Gemini 1.5 Flash or Gemini 1.5 Flash-Lite.

---

## 3. Mandatory Dynamic Few-Shot Filtering

You are strictly prohibited from building a single static prompt template containing all 40 human-evaluated "Gold Standard" benchmark items.

* **The Billing Problem:** Passing 40 robust examples (query, ground truth, output, 1-10 scoring matrix, and full qualitative reasoning) introduces a structural 20,000 token payload overhead per interaction. Replicating this across 4,000 automated evaluation runs will burn millions of unnecessary input tokens.
* **The Mandatory Code Implementation:** The evaluation script inside `async_judge.py` must query the central SQLite database dynamically. Before a pipeline output is evaluated, the script must look up the target query's category quadrant field (e.g., `Q1_Direct_Text` vs `Q4_Implicit_Table`) and construct a dynamic system prompt containing **exactly 10 contextual examples** matching that specific category. The remaining 30 examples must be completely omitted from the payload.

---

## 4. Execution Loops and Local Safety Throttling

To protect against runaway cost loops, infinite recursive functions, or unhandled file reading exceptions, you must embed programmatic execution caps inside all iteration scripts.

* **Mandatory Test-Brake Variable:** Every loops script (`async_generator.py`, `loop_executor.py`, and `async_judge.py`) must contain a hardcoded Boolean configuration variable named `LOCAL_TEST_THROTTLE` at the top of the file.
* **Throttle Execution Logic:** When `LOCAL_TEST_THROTTLE = True`, the script must force a strict database fetch cap, restricting execution to **exactly 3 data items** (e.g., using `LIMIT 3` inside the SQL statement).
* **Removal Protocol:** You must run the entire workflow sequentially from document ingestion, synthesis, pipeline generation, and judge evaluation under `LOCAL_TEST_THROTTLE = True` to verify data integrity. Only when an entire 3-item run concludes successfully without error codes may the throttle variable be turned to `False` to release the full batch processing loop.

---

## 5. Concurrency and Rate Limiting Enforcement

Asynchronous worker pools running thousands of cloud lookups simultaneously can quickly exceed API Token-Per-Minute (TPM) and Requests-Per-Minute (RPM) quotas, causing script crashes and half-written data tables.

* **Resilience Dependency:** You must wrap all cloud API request loops using a resilient wrapper library (such as `tenacity`).
* **Mandatory Exception Handling:** Catch all HTTP 429 exceptions (Rate Limits Exceeded) explicitly. The connection code must utilize an **exponential backoff with randomized jitter** algorithm. If a rate cap is triggered, the script must pause execution, back away smoothly, and retry without terminating the pipeline mid-run.
* **Queue Bounds:** Cap your max concurrent task parameters within `asyncio.Semaphore` to a maximum of 5 parallel worker threads unless initial token analysis confirms a higher ceiling is safe under university quota constraints.

---

## 6. Relational Data Management and State Persistence

Writing execution outputs directly to raw CSV files or nested JSON blocks is strictly forbidden for long-running batches.

* **The Crash Risk:** If an asynchronous loop encounters an unhandled runtime error or connection loss at run 2,500 out of 4,000, appending data to an uncommitted flat text file can corrupt or erase previous records.
* **Mandatory Architecture:** A local relational database configuration file (`database_manager.py`) must isolate schemas into distinct relational structures (`nodes`, `queries`, and `results`).
* **State Commits:** The pipeline execution script must perform a SQL commit immediately after an independent run completes. If the system crashes mid-execution, the worker must check the database table for existing records and pick up cleanly from the last successfully written index row instead of re-running past inputs and consuming extra API tokens.
