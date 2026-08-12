# Test Suite Reference

A phase-by-phase index of every test file under `project/tests/`, what module
it exercises, and what behaviour it actually covers. Written for the
dissertation's methodology/verification narrative — a reader should be able
to find "how was X verified?" here without opening the test files. Generated
2026-08-11 via `graphify query` + direct source inspection; 240 tests
collected (`uv run pytest --collect-only -q`), 239 pass + 1 live-API smoke
test skipped by default.

## Format

Each entry:

1. **Test file** → **module under test**.
2. **Count**: number of test functions.
3. **Covers**: grouped bullets of what behaviour is verified — not a
   line-by-line list of every test name (see the file itself for that), but
   the categories of correctness each file is responsible for.

Organised by project phase (`Phase Plan.md`), then a cross-cutting section
for infrastructure shared by every phase.

---

## Phase 1 — Infrastructure

**`test_config.py` → `llm_client/config.py`** (5 tests)
- Every pipeline stage (generator/critic/answerer/judge/p3_index_build) has a model routing entry.
- Anti-self-grading invariant: Generator ≠ Critic model family, Answerer ≠ Judge model family.
- `THROTTLE_LIMIT`/concurrency-cap constants have their documented values.

**`test_groq_client_backoff.py` → `llm_client/groq_client.py`** (5 tests)
- 429 responses trigger a retry that eventually succeeds (tenacity backoff).
- The semaphore bound actually limits concurrent in-flight calls.
- Tool schemas are passed through when given, omitted when not.
- Backward-compatible shim (`call_groq`) still works after the client refactor.

**`test_llm_client_nim.py` → `llm_client/nim_client.py`** (5 tests)
- NVIDIA NIM's `acomplete` routes through the real `AsyncOpenAI`-shaped client.
- `get_llm_client` returns an equivalent client for the `nvidia` provider; raises on an unknown provider.
- A `CallbackManager` is correctly wired in when provided, and construction still succeeds when omitted.

**`test_llm_factory.py` → `llm_client/llm_factory.py`** (2 tests)
- For both `groq` and `nvidia` providers, `LLMFactory.get_client()`'s retry/semaphore-wrapped client is actually used by `.achat()` — regression coverage for the session's "client silently dropped" bug (deviations.md #21), using a real `OpenAILike` with `._aclient` swapped, not a hand-rolled fake.

**`test_loop_template.py` → `loop_template.py`** (3 tests)
- The shared `LOCAL_TEST_THROTTLE` SQL-limit clause matches `config.THROTTLE_LIMIT`.
- `apply_throttle()` caps a list at 3 items when the flag is on, passes through unchanged when off.

**`test_database_manager.py` → `database_manager.py`** (19 tests)
- Schema: all five tables created; WAL mode enabled.
- `golden_queries` stale-schema migration runs when the table is empty, refuses (raises) when it holds real rows.
- Node insert/read round-trip; `results` upsert + `get_completed_keys` resumability; the `UNIQUE(source_set, query_id, pipeline, k_value)` constraint actually blocks a duplicate insert.
- Query insert + per-quadrant counting; unknown table name rejected.
- Golden-query label updates: happy path, and every validation rejection (score >100, negative score, non-integer score, invalid `is_good`) each has its own test.
- `get_all_query_texts` reads across all three quadrant-fill tables (PQ/GQ/JEQ) combined — the duplicate-question check's data source.
- `judge_validation` insert.

## Phase 2 — Ingestion & Parsing

**`test_fetch_filings.py` → `ingest/fetch_filings.py`** (5 tests)
- CIK resolution from ticker; raises for an unknown ticker.
- Filing download + local cache write; skips re-download if already cached; raises when no matching 10-K exists.

**`test_parse_filing.py` → `ingest/parse_filing.py`** (3 tests)
- LlamaParse is called and its output cached.
- Re-parse is skipped within a 48h cache window; forced again once the cache is older than 48h.

**`test_node_builder.py` → `ingest/node_builder.py`** (8 tests)
- Correct output keys per node; sequential `node_id` assignment; `parent_item_header` tracked.
- Tables stay atomic (never split mid-table); text vs. table classification, including the captioned-table edge case (deviations.md-relevant LlamaParse defect).
- `document_id`/page-number carried through; token count is always positive.

**`test_parsing_audit.py` → `ingest/parsing_audit.py`** (3 tests)
- Section sampling returns at most N sections, capped correctly at the boundary.
- The audit report is written as readable Markdown.

**`test_run_ingestion.py` → `ingest/run_ingestion.py`** (2 tests)
- One document's fetch → parse → build → insert chain runs in order.
- Already-ingested documents are skipped (resumability).

**`test_filings_manifest.py` → `data/filings_manifest.json`** (3 tests)
- The manifest file exists and is a list; every entry has the required keys; every `document_id` is unique.

## Phase 3 — P3 Summary-Tree Build

**`test_build_summary_index.py` → `pipelines/structural/build_summary_index.py`** (12 tests)
- Skip-if-already-built (both a "final dir exists" check and idempotent re-runs).
- Crash safety: a crash mid-build leaves only a temp dir behind (never a half-written final dir); a stale temp dir from a prior crash is cleaned up before the next retry — atomic temp-dir-then-rename persistence.
- Raises clearly when a document has no nodes.
- The LLM's `CallbackManager` is shared with the `TreeIndex` build (token-usage accounting fix, deviations.md-relevant).
- The interactive confirm-before-building prompt: accepts `y`, rejects `n`, reprompts on invalid input; a user decline skips just that document, not the whole manifest run.
- Cost log (`append_cost_log`) creates and appends correctly.
- `main()` walks every manifest entry sequentially.

**`test_node_convert.py` → `pipelines/structural/node_convert.py`** (3 tests)
- DB node rows convert to LlamaIndex `TextNode`s preserving id/text and full metadata; empty input list handled.

## Phase 4 — Dataset Generation & Adversarial Verification

**`test_run_dataset_generation.py` → `dataset_generation/run_dataset_generation.py`** (37 tests — the largest file in the suite)
- **Quadrant fill-order (`next_target`)**: fills `queries` before `golden_queries` before `judge_validation`; moves to the next quadrant once one is full; returns `None` once all 140 slots are filled; a `quadrants` subset restricts the search correctly.
- **`_ALL_FILINGS` corpus scope**: derives from `data/filings_manifest.json` and includes all 13 current filings (JPM/JNJ included) — this session's Task 1 fix, see `deviations.md`.
- **`document_ids` parameter contract**: `None` defaults to all filings; an explicit empty tuple stays empty rather than silently falling back.
- **Resumability**: re-running after a restart derives the next `query_id` suffix from the freshly-loaded DB count, never colliding with already-committed rows.
- **Duplicate-question detection**: a near-verbatim restatement (cosine similarity ≥ threshold) of an already-accepted query is rejected and retried with feedback; a genuinely different question below threshold is accepted normally.
- **Retry-feedback loop**: a rejected first attempt's diagnosis reaches the second attempt's prompt; an accepted first attempt passes no feedback.
- **Per-attempt exception handling** (this session's main debugging focus): a `RuntimeError` from the Critic on attempt 1 recovers on attempt 2; all three attempts raising `JSONDecodeError` skips the section without crashing `main()`; `openai.APIStatusError` (both the original narrower catch and the later `APIError`-widened catch) is caught and logged, not raised; `null` `gt_citations`/`computed_answer` fields (`TypeError`/`AttributeError`) are caught and logged.
- **Section classification & chunking**: text vs. table classification (any-node-is-table rule); round-robin interleaving across companies (including the shorter-bucket-stops-contributing case); pool building routes content to the right quadrant pool; `chunk_section` returns a section unchanged when under the token limit, splits correctly when over it, never splits a text node away from an immediately-following table, and logs+skips a single oversized node while still packing the rest.
- **Loop safety**: pool cycling is capped and terminates (never spins forever burning quota); table sections are only ever routed to table quadrants (Q3/Q4).
- **Structured logging**: accepted/rejected/exception-caught attempts each log the right fields; calling `main()` twice doesn't duplicate log handlers.
- **`format_underfill_summary`**: only marks quadrants below target as underfilled.

**`test_async_generator.py` → `dataset_generation/async_generator.py`** (3 tests)
- `generate_query()` returns the correctly parsed payload via the real `achat([ChatMessage(...)])` interface (not the old, buggy `chat.completions.create` shape).
- First attempt's prompt contains no leftover "previous attempt" text; a retry's prompt does contain the previous-attempt feedback and the word "different".

**`test_async_critic.py` → `dataset_generation/async_critic.py`** (6 tests)
- The tool-calling loop uses the search tool then produces a final answer.
- The search-tool schema actually reaches the request payload sent over the wire.
- Tool results are fed back keyed by `tool_call_id`.
- Exceeding `_MAX_TOOL_ROUNDS` without a final answer raises.
- Default return shape is unchanged; `return_messages=True` includes the full message history.

**`test_async_critic_live_smoke.py` → `dataset_generation/async_critic.py`** (1 test, skipped by default)
- One real, throttled round-trip against the live Groq API, proving the tool-calling protocol actually works end-to-end — not just against the mocked shape asserted elsewhere.

**`test_search_tool.py` → `dataset_generation/search_tool.py`** (8 tests)
- Keyword-overlap ranking; zero-overlap nodes excluded; `top_k` respected; ties broken deterministically by `node_id`.
- Tool schema shape matches the expected JSON structure.
- Length-bias correctness: a short, precise node outranks a long, wordy one; an empty-content node is skipped without a divide-by-zero; a degenerate tiny node doesn't unfairly outrank a real one.

**`test_cross_check.py` → `dataset_generation/cross_check.py`** (22 tests)
- `citations_overlap`: true on any shared node, false on fully disjoint sets.
- `extract_numbers`: handles currency symbols, thousands separators, multiple values in order.
- `values_match`: exact match after normalization, within-tolerance match, false on a real difference, false on mismatched number count, true when the Critic has an extra unrelated number, false on a genuinely wrong number, falls back to text equality when neither answer has numbers.
- `check_query`'s three-gate AND logic: accepts only when citation overlap AND value match AND embedding similarity all hold; individually tested rejection on citation mismatch, value mismatch, and the "numbers coincidentally match but text is unrelated" case embeddings alone catch.
- `diagnose_rejection`: reports the correct human-readable reason for each of the three gate failures.
- `embedding_similarity`: high for similar answers, low for unrelated ones, threshold comparison correct.

**`test_section_grouper.py` → `dataset_generation/section_grouper.py`** (4 tests)
- Groups nodes by `(document_id, header)`; normalizes header case into one section; excludes null/empty headers; keeps different documents' sections separate.

**`test_gq_labeling.py` → `dataset_generation/gq_label_export.py` / `gq_label_import.py`** (7 tests)
- Markdown label rendering includes the query text and blank fields for human labeling.
- Round-trip parsing of filled-in labels; unfilled entries are skipped; multiple entries in one file don't bleed into each other.
- Malformed input raises clearly: non-integer score, unrecognized `is_good` value, an entry missing its "good example" line.

## Phase 5 — Retrieval Pipelines (P1/P2/P3) + Answerer + Loop Executor

**`test_base_retriever.py` → `pipelines/base.py`** (3 tests)
- The `Retriever` ABC cannot be instantiated directly; a subclass missing `retrieve()` can't be instantiated either; a subclass that implements it can be instantiated and called.

**`test_tokenizer.py` → `pipelines/bm25/tokenizer.py`** (8 tests)
- Numbers/decimals, percent signs, and currency symbols are preserved as tokens.
- Table pipe characters (`|`) are stripped but cell values kept.
- A trailing comma isn't absorbed into a preceding number.
- No stemming is applied (P2 must stay purely statistical, per Guardrails).
- Empty-string and whitespace-only inputs return an empty token list.

**`test_build_bm25_index.py` → `pipelines/bm25/build_bm25_index.py`** (6 tests)
- Builds and pickles a per-document BM25 corpus; skips if already indexed; raises on a document with no nodes.
- `is_document_indexed` is false for empty storage.
- Nodes are isolated across documents (no cross-filing leakage into one index).
- Atomic write survives an interruption (same crash-safety pattern as P3's build).

**`test_p2_bm25.py` → `pipelines/bm25/p2_bm25.py`** (4 tests)
- Returns the correct top-K by BM25 score; filters strictly to the given `document_id`; tie-breaking is stable across repeated calls; raises clearly if the index hasn't been built yet.

**`test_build_vector_index.py` → `pipelines/vector/build_vector_index.py`** (7 tests)
- Embeds and indexes nodes; skips if already indexed; raises on no nodes; isolates nodes across documents.
- Embeds only raw node content (not structural metadata bleeding into the embedding).
- Raises on colliding Chroma IDs across documents (silent-collision guard).

**`test_fastembed_reranker.py` → `pipelines/vector/fastembed_reranker.py`** (3 tests)
- Reranks candidates by relevance to the query; `top_n` truncates the result; an empty node list returns empty without erroring.

**`test_p1_vector.py` → `pipelines/vector/p1_vector.py`** (4 tests)
- Filters to the given `document_id`; respects `k`; returns the most relevant node first; returns an empty list (not an error) for an unindexed `document_id`.

**`test_p3_structural.py` → `pipelines/structural/p3_structural.py`** (8 tests)
- Filters to the given `document_id`; respects `k`; returns the most relevant node first; returned nodes carry full metadata.
- Makes no LLM call at retrieval time (`MockLLM`-enforced invariant); ranking is stable across repeated calls.
- Raises clearly when the index hasn't been built; `storage_root` defaults correctly to the build module's constant.

**`test_answerer.py` → `pipelines/answerer.py`** (15 tests)
- Citation-marker parsing: extracts `[[node:...]]`, preserves order and deduplicates, returns empty when no markers present, accepts hyphenated node IDs, ignores malformed markers.
- Prompt construction: contains only query text and node content (nothing else); excludes node metadata; handles an empty node list.
- **Anti-leakage, on the actual wire payload**: the prompt sent to the LLM leaks no ground truth; the prompt correctly instructs the citation-marker format.
- `answer()` populates all `AnswerResult` fields correctly; keeps citation markers in the raw output text (not stripped).
- Construction-time guards: rejects any model other than the one fixed in `MODEL_ROUTING["answerer"]`; rejects a nonzero temperature; constructing an `Answerer` does not itself build a client (lazy construction).

**`test_loop_executor.py` → `loop_executor.py`** (16 tests)
- `build_cells` is query-major across pipelines (same query answered by all pipelines before moving to the next); skips already-completed `(query_id, pipeline, k_value)` keys.
- `result_id` is derived from the natural key, not a counter (crash-safe, can't collide after a restart).
- `run_cell` writes a row with judge-score columns left `NULL` (Phase 6 hasn't run yet); passes the right `document_id`/`k` to the retriever; tolerates a sync retriever that internally calls `asyncio.run()` (the `asyncio.to_thread` wrapping this session added).
- `main()`: runs every cell for one pipeline; skips already-completed cells on a second run; resumes only the missing cells; keeps PQ and JEQ source sets separate; `LOCAL_TEST_THROTTLE` caps a run at 3 cells; an unthrottled run is not capped; a single failing cell doesn't abort the whole run; rejects an empty retriever map; rejects an unknown pipeline name.
- `get_queries` structurally rejects reading from the `golden_queries` (GQ/exemplar) pool — the Judge's exemplar set must never be reachable from pipeline-facing code.

---

## Phases 6-8

No tests yet — `judge/`, the full-benchmark runner, and `analysis/` don't exist yet (see `build_progress.md`).
