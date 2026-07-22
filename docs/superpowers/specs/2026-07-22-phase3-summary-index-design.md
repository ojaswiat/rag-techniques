# Phase 3 — P3 Summary-Index Build: Design

**Goal:** Build one hierarchical summary tree per filing (9 filings total), used later by the P3 structural pipeline (Phase 5), using `llama-3.1-8b-instant` on Groq's free tier. This is the only index build permitted to call an LLM (Guardrails §1) and must run once, cached, never rebuilt per query.

**Architecture:** Real LlamaIndex objects (`llama-index-core`, `llama-index-llms-groq`), not a custom-built tree. Persisted per filing to `storage/summary_index/{document_id}/`; directory-existence check is the cache test (Architecture.md §Phase 3).

**Tech Stack:** `llama-index-core`, `llama-index-llms-groq`, existing `database_manager.py` (read-only, source of nodes), `loop_template.py` (throttle).

## Decision: Real LlamaIndex objects over a custom builder

Two options were weighed:

- **Custom builder** — hand-rolled recursive summarization, every Groq call routed through the project's existing `call_groq()` wrapper (semaphore + tenacity backoff).
- **Real LlamaIndex index** (chosen) — LlamaIndex's own build/persist/retrieve machinery, using `llama_index.llms.groq.Groq` for LLM calls (bypasses `call_groq()`).

**Why real LlamaIndex wins:** Architecture.md §Phase 5 spec's P3 retrieval as `SummaryIndex.as_retriever(retriever_mode="embedding")` — a method that only exists on a real LlamaIndex index object. A custom-built tree would force a second, larger deviation in Phase 5 (hand-written retrieval/traversal code, no free `.as_retriever()`). Building the real object now avoids that cascade.

**Real cost of this decision — this is a genuine, tracked deviation, not just a package substitution:**

- LlamaIndex's `Groq` LLM class does not go through `call_groq()`. It has its own (less-tuned) retry, not our specific 429 handling, jitter, or `GROQ_MAX_CONCURRENCY` semaphore.
- **Risk is real, not hypothetical, even at only 9 filings.** A single filing (e.g. AAPL_2025, 682 nodes) needs dozens of recursive summarization calls fired in a short burst while building its tree. Burst rate (TPM/RPM), not total daily volume, is what actually risks a 429 — and 9 filings' low *daily* total does not protect against that burst.
- **This can cost real money / real time if the mitigations below fail:** an unhandled 429 mid-build could corrupt a filing's cache (see mitigation 2), forcing a manual re-run; repeated rate-limit failures eating into the free-tier daily cap could force falling back to Groq's paid Developer tier (Budget.md's documented fallback) earlier than planned, or delay Phase 4+ if quota is contended. None of this is likely at 9 filings, but it is possible, and the mitigations exist specifically to keep the probability low, not to make it zero.

**Mitigations (mandatory, not optional):**

1. **Sequential builds, one filing at a time** — never build multiple filings' trees concurrently. Keeps burst request rate bounded to one filing's summarization fan-out at a time.
2. **Build-to-temp-dir, atomic rename on success** — build into `storage/summary_index/{document_id}.tmp/`, only `os.rename()` to the real `storage/summary_index/{document_id}/` path once the full build succeeds. Prevents a crash mid-build from leaving a partially-written directory that a naive `exists()` cache check would wrongly treat as complete.
3. **Token/cost logging via `TokenCountingHandler`** — LlamaIndex's `Groq` LLM class doesn't expose token usage by default; wire in `llama_index.core.callbacks.TokenCountingHandler` to get real numbers for the cost log.

**Recorded in `resources/artifacts/Changes.md`:** the `call_groq()` bypass for this one build step, scoped explicitly to Phase 3's one-time index build (never Phase 4/6/7's Groq calls, which remain on `call_groq()` unconditionally), with the risk and mitigations above.

## Open technical verification (do first, before locking implementation)

LlamaIndex's actual hierarchical-summarization API needs verifying against the installed `llama-index-core` version before writing real code — `SummaryIndex` (current LlamaIndex naming) is a flat list index with no build-time LLM calls; the flat/hierarchical distinction and the exact class (`TreeIndex` with `build_tree=True`, `DocumentSummaryIndex`, or current `SummaryIndex` equivalent) must be confirmed live, the same way Phase 1 re-verified live Groq model availability rather than trusting the spec's names blindly. First implementation task must include this live check.

## Components

| Module | Responsibility |
|---|---|
| `pipelines/structural/build_summary_index.py` | Per `document_id`: skip if `storage/summary_index/{document_id}/` exists; else load nodes via `dbm.get_nodes_by_document`, convert to LlamaIndex nodes, build the verified hierarchical index sequentially with `TokenCountingHandler` attached, build to temp dir, atomic rename on success, append a cost row. |
| `logs/index_build_costs.json` | One flat-file row per filing: `document_id`, wall-clock seconds, input/output tokens. Flat-file per spec (~9 rows, no crash-resume requirement, unlike `results`) — unchanged from Architecture.md's own justification. |

## Testing

- Unit tests mock the LlamaIndex build call (no live Groq spend in CI) to verify: skip-if-exists behavior, atomic temp-dir-then-rename behavior (including a simulated crash leaving only the temp dir, and confirming the real path is never treated as valid), and the cost-log row shape.
- One live, `LOCAL_TEST_THROTTLE`-limited (3 filings) end-to-end run before releasing the full 9-filing batch, per Guardrails §7 / Phase Plan scheduling note.

## Out of scope (deferred to Phase 5)

- The actual P3 retrieval pipeline (`as_retriever(retriever_mode="embedding")`) — Phase 3 only builds and persists the index.
