# Bugs Found During Development

A defect log, distinct from `deviations.md` (departures from the originally
proposed design) and `resources/artifacts/dev_history.md` (dev-facing
narrative archive of removed code comments). This file is a pure bug
record: what broke, why, how bad it would have been, and what fixed it.
Only major/load-bearing bugs are logged here, not every minor nit caught
in review. Newest first, numbered.

Each entry:

1. **Bug:** what broke, concretely.
2. **Root cause:** why it happened.
3. **Impact / Severity:** what would have shipped if unfixed; Critical / High / Medium / Low.
4. **Fix:** what changed.
5. **Found via:** how it was caught.

---

### 1. Reasoning-tuned models could return `content=None`, crashing `json.loads()` in Generator and Critic (2026-08-12)

1. **Bug:** `async_generator.py` and `async_critic.py` both call `json.loads(response.message.content)` on the final LLM turn with no null check. Live runs on OpenRouter (Generator: `nvidia/nemotron-3-super-120b-a12b:free`; Critic: `openai/gpt-oss-20b:free`) hit `TypeError: the JSON object must be str, bytes or bytearray, not NoneType` 28 times in one session's failure log -- the single largest failure category, ahead of citation-mismatch rejections.
2. **Root cause:** Both models are reasoning-tuned. Reasoning tokens draw from the same completion-token budget as the visible answer; with no `max_tokens` set and no reasoning-effort cap configured anywhere in `llm_factory.py`'s `OpenAILike` construction, a long reasoning trace can exhaust the entire budget, leaving `message.content=None` with `finish_reason="length"`. This is a documented failure mode for reasoning models generally (confirmed via live web research against OpenAI/OpenRouter community reports), not specific to any one provider.
3. **Impact / Severity:** High -- silently crashed ~2/3 of Generator/Critic attempts during real runs, burning free-tier request quota on unusable attempts and making yield/throughput far worse than the citation-mismatch rejection rate alone would suggest.
4. **Fix:** Added `additional_kwargs={"extra_body": {"reasoning": {"effort": "low"}}}` to the `openrouter` branch of `LLMFactory.get_client()` (`llm_client/llm_factory.py`), which OpenRouter's OpenAI-compatible endpoint applies as its documented unified `reasoning` request field (not a typed `openai` SDK kwarg, hence `extra_body`). `effort: "none"` was tried first and worked for the Generator's model but was rejected outright by the Critic's (`400: "Reasoning is mandatory for this endpoint and cannot be disabled"`); `"low"` was verified live against both real models and returns clean, non-null content for both.
5. **Found via:** Requested log/root-cause review surfaced the `TypeError` pattern; live web research identified the reasoning-token-budget mechanism; fix verified live against both real Generator and Critic OpenRouter endpoints, plus the existing test suite extended with a regression test asserting the `extra_body` reasoning kwarg reaches the wrapped client's `create()` call.

### 2. Dataset-generation orchestrator only ever saw 9 of the 13 in-scope filings (2026-08-11)

1. **Bug:** `run_dataset_generation.py`'s `_ALL_FILINGS` was a hardcoded 9-filing tuple (AAPL/MSFT/TSLA only), left over from before the corpus was expanded to 18 filings and then fixed at 13 (`deviations.md` #20). Every dataset-generation run silently excluded JPM and JNJ -- 4 of the 13 in-scope filings, specifically the two carrying the densest tabular/footnote structure the corpus was trimmed to preserve.
2. **Root cause:** The constant was never wired to `data/filings_manifest.json`, unlike every sibling build script (`build_bm25_index.py`, `build_summary_index.py`, `build_vector_index.py`), which all derive their filing list from that manifest. It simply wasn't updated when the manifest changed.
3. **Impact / Severity:** High -- silent scope truncation of the benchmark's own query-generation corpus, with no error or warning; would have shipped a dataset missing two companies entirely.
4. **Fix:** `_ALL_FILINGS` now derives from `data/filings_manifest.json`, lazily -- via a module-level `__getattr__` (PEP 562) rather than at import time, so importing the module from an unexpected working directory (e.g. the repo root instead of `project/`) doesn't crash before any function runs, matching the sibling scripts' lazy-load convention. A task review during implementation flagged the first (eager) version of this fix as a plan-mandated deviation from that convention; the human partner decided to make it lazy.
5. **Found via:** Second-order-thinking review before starting a real Phase 4 run, confirmed by a new regression test asserting `len(_ALL_FILINGS) == 13` and that JPM/JNJ are present.

### 3. Real Groq API failures crashed the whole dataset-generation run instead of being retried (2026-08-11)

1. **Bug:** `run_dataset_generation.py`'s per-attempt exception guard imported `groq.APIStatusError`, but the real call path (via `LLMFactory` -> LlamaIndex's `OpenAILike.achat()` -> `openai.AsyncOpenAI`) raises `openai.APIStatusError` instead -- a completely separate, non-subclassed exception class. A genuine Groq rate limit (413, TPM exceeded) during a real throttled run crashed the entire orchestrator instead of being logged and retried like every other per-attempt failure.
2. **Root cause:** `groq.APIStatusError` and `openai.APIStatusError` share no inheritance relationship (`issubclass()` false in both directions), so catching one never catches the other. The code had been updated to use the real `achat()` interface (see bug #4 below) but the exception-handling import was never updated to match. Widening further during the same session's final review also surfaced that even the corrected `openai.APIStatusError` catch alone missed `openai.APIConnectionError`/`openai.APITimeoutError` (dropped connections, timeouts) -- neither is a subclass of `APIStatusError`, only of their shared parent `openai.APIError`.
3. **Impact / Severity:** High -- this bug was invisible to every existing test (all mocked the exception at the old, wrong class) and was only caught because a real throttled run was actually executed against the live Groq API. At the unthrottled scale (140 queries x up to 3 attempts x two LLM round-trips each, running for hours), a transient network error or rate limit is near-certain; losing the whole run to one costs quota that free-tier limits cannot refund.
4. **Fix:** Import changed to `from openai import APIError` (the common parent of `APIStatusError`/`APIConnectionError`/`APITimeoutError`), so any error from the OpenAI-compatible client -- whether or not a response arrived -- is caught and logged rather than propagating. A pre-existing test that had been asserting against the wrong (`groq`) exception class was converted, not duplicated, to test the real one. Verified live, twice: the fix's first version was proven against a real 413 that crashed the run; the widened version was proven against a second real 413 (TSLA_2023) that was correctly caught-and-logged instead of crashing.
5. **Found via:** A real, throttled dry run of the fixed orchestrator against live Groq traffic -- the first time this code path had ever been exercised against a genuine API failure rather than a mock.

### 4. LLMFactory's retry/backoff wrapper was silently never applied (2026-08-11)

1. **Bug:** Every LLM call routed through `LLMFactory.get_client()` (Generator, Critic, all 13 completed P3 tree-index builds) ran with zero retry/backoff/concurrency protection, despite `groq_client.py`/`nim_client.py` building that protection correctly. Separately, `async_generator.py`'s `generate_query()` called `client.chat.completions.create(...)`, a raw-OpenAI-SDK shape that doesn't exist on the object the factory actually returns.
2. **Root cause:** `OpenAILike(..., async_client=raw_client, ...)` passed the wrapped client to a kwarg that isn't a real field on `OpenAILike`/`OpenAI` -- pydantic's `arbitrary_types_allowed` silently accepted and discarded it, so `OpenAILike._get_aclient()` built its own unwrapped `AsyncOpenAI` internally instead. The `.chat.completions.create` call shape was never caught because the existing test suite mocked around that exact (wrong) interface rather than exercising the real one.
3. **Impact / Severity:** High. Silent -- no error, no exception, builds completed and produced correct output, but with no resilience against transient API failures during long, quota-throttled runs (see `challenges.md` #1). Already-completed P3 content is unaffected in correctness, only in the resilience gap during those builds.
4. **Fix:** Set the private `_aclient` cache slot directly on the constructed `OpenAILike` instance (`llm._aclient = raw_client`) instead of the nonexistent kwarg. Fixed `generate_query()` to call `client.achat([ChatMessage(...)])`, the real LlamaIndex interface. Added `tests/test_llm_factory.py` and rewrote `tests/test_async_generator.py` against a real `OpenAILike` object so the regression fails under the old pattern and passes under the fix.
5. **Found via:** Manual trace after noticing a resilience gap; confirmed empirically by constructing a real `OpenAILike` and observing `async_client=` silently dropped and `.chat.completions.create` absent, before writing any fix (systematic debugging).

### 5. Chroma silently dropped real filing data on duplicate node IDs (2026-08-10)

1. **Bug:** The on-disk `project/storage/chroma` collection had been poisoned during earlier P1 test runs with 2 rows of fabricated test text under real node IDs (`AAPL_2025_n0001`/`n0002`), tagged `document_id='None'`. A real Phase 5 index build against this collection would have silently and permanently failed to index those two real filing nodes -- forever invisible to `document_id`-filtered retrieval, with zero error signal anywhere.
2. **Root cause:** Chroma's `collection.add()` keeps the OLD row and silently drops the new one on an ID collision, instead of erroring or overwriting.
3. **Impact / Severity:** Critical. A production data-integrity risk caught only by an independent final-review re-query, not by any test that existed before that review.
4. **Fix:** Deleted the poisoned `storage/chroma` collection. Added a post-build verification step in `build_index_for_document()`: re-query `collection.get(where={"document_id": document_id})` and raise `RuntimeError` if the row count doesn't match the expected node count, turning a silent gap into a hard build-time failure.
5. **Found via:** Final whole-branch code review, verified independently (not just trusting the fix report) by re-running the isolation check against the live collection.

### 6. ChromaVectorStore's reserved metadata key silently overwrote our own `document_id` (2026-08-10)

1. **Bug:** LlamaIndex's `ChromaVectorStore` writes a reserved top-level `document_id` Chroma metadata field derived from `node.ref_doc_id`, independent of the custom `metadata["document_id"]` set by `nodes_to_llama_nodes()`. Without a source relationship, `ref_doc_id` is `None`, and that reserved field overwrote ours with the literal string `"None"` -- breaking every `document_id`-filtered query.
2. **Root cause:** Two different mechanisms (LlamaIndex's internal `node_to_metadata_dict`, and this project's own metadata dict) both claim the same key name, and the internal one wins on write.
3. **Impact / Severity:** Critical -- would have broken P1's core per-document retrieval isolation invariant (Architecture.md §0 Decision 2) for every indexed filing.
4. **Fix:** Explicitly set `node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=document_id)` on every node before indexing, so both the reserved field and the custom metadata agree.
5. **Found via:** Implementer self-discovery during Task 4, confirmed by an independent two-document isolation test dispatched specifically because this was flagged as the plan's most important review.

### 7. Structural metadata leaked into P1's embedded/reranked text (2026-08-10)

1. **Bug:** `VectorStoreIndex` defaults to `MetadataMode.EMBED`, which embeds `TextNode.metadata` fields (`parent_item_header`, `node_type`, `source_page_num`) alongside the actual content. P1 would have received extra structural signal that P2 (BM25) and P3 (summary tree) don't get at retrieval time, giving P1 an unfair, comparability-breaking advantage in the eventual 900-run benchmark.
2. **Root cause:** LlamaIndex's default embed/LLM metadata mode is opt-out, not opt-in -- nothing in the P1 build code excluded these fields.
3. **Impact / Severity:** High -- a methodology-invalidating bug for the dissertation's core paradigm-vs-paradigm comparison, not a functional crash.
4. **Fix:** Set `excluded_embed_metadata_keys`/`excluded_llm_metadata_keys` on every node to strip `parent_item_header`, `node_type`, `source_page_num`, `document_id` before embedding.
5. **Found via:** Final whole-branch review, cross-checking the plan's own stated Global Constraint (no metadata pre-filter / fair comparison) against the actual indexing code.

### 8. `storage_root` late-binding broke test isolation and silently reused production paths (2026-08-10)

1. **Bug:** `storage_root: Path = STORAGE_ROOT` as a function default binds the module-level constant at *import* time, not call time. `monkeypatch.setattr` on `bvi.STORAGE_ROOT` in tests had no effect on functions already holding the old default -- tests could silently read/write the real `storage/chroma` path instead of an isolated test path. The same bug reappeared independently in `P1VectorRetriever.__init__`.
2. **Root cause:** Python evaluates default argument values once, at function-definition time, not per-call.
3. **Impact / Severity:** Medium -- a test-isolation bug, not a production-data bug on its own, but it's exactly the mechanism that let bug #5 (Chroma poisoning) happen in the first place.
4. **Fix:** Changed every such default to `storage_root: Path | None = None`, resolved to `STORAGE_ROOT`/`bvi.STORAGE_ROOT` inside the function body at call time.
5. **Found via:** Implementer self-discovery in Task 4; confirmed to have reappeared in Task 5 (`p1_vector.py`) during final whole-branch review.

### 9. GQ hand-labelling accepted invalid scores and silently no-op'd on typos (2026-07-29)

1. **Bug:** A human-entered score like `99` (outside the 1-10 scale) was accepted with no validation. A mistyped query ID during label import matched nothing but still reported success, silently updating zero rows. Separately, `CREATE TABLE IF NOT EXISTS` never applies schema changes to an already-existing table, and a regex used during import silently dropped older-format label entries.
2. **Root cause:** No range/existence validation on human-entered evaluation data; a schema-migration pattern (`CREATE TABLE IF NOT EXISTS`) that only applies to fresh databases.
3. **Impact / Severity:** High -- this is hand-scored data that feeds the Judge-validation gate (`CLAUDE.md` §4); silent corruption here would have propagated into the >80% human-agreement gate with no way to detect it after the fact.
4. **Fix:** Rescaled scoring to 0-100 with enforced range validation (raises on out-of-range); label import now raises on an unmatched query ID instead of silently no-op'ing; added a real migration that refuses to touch existing data; fixed the regex to stop dropping older-format entries.
5. **Found via:** Manual review of the hand-labelling pipeline during Phase 6 prep.

### 10. P3 build logged zero token cost despite generating real summaries (2026-08-04)

1. **Bug:** After the `LLMFactory` refactor, every P3 build logged `input_tokens: 0, output_tokens: 0` in the cost log -- real summaries were generated correctly, but the cost record was silently wrong.
2. **Root cause:** `llama_index`'s `llm_chat_callback()` decorator fires usage events on the LLM object's own `callback_manager` attribute, not the index's -- `TreeIndex` only forwards its callback bus to an LLM at query time, not during the build, so the LLM object never had a manager wired in to fire events on.
3. **Impact / Severity:** Medium -- no functional impact on the build itself, but breaks the token-cost audit trail the dissertation's budget accounting depends on (`token_usage.md`).
4. **Fix:** Added an optional `callback_manager` parameter to `LLMFactory.get_client()`/`get_client_for_stage()`, forwarded into `OpenAILike(...)`; `build_index_for_document()` now passes one shared `CallbackManager` to both the LLM client and `TreeIndex`.
5. **Found via:** Cost-log review showing implausible zero-token entries against known-successful builds.

### 11. LLM temperature silently fell back to 0.1, not the mandated 0 (2026-08-04)

1. **Bug:** `LLMFactory.get_client()` built every `OpenAILike(...)` client with no explicit `temperature` kwarg, silently taking `llama_index`'s default of `0.1` instead of the project-wide `temperature=0` requirement.
2. **Root cause:** Missing kwarg; no test asserted on the constructed client's temperature.
3. **Impact / Severity:** Medium -- at `0.1`, sampling is stochastic, so the same model/document could produce a different-length summary and token count run to run, undermining the reproducibility `CLAUDE.md` §4 requires.
4. **Fix:** Added `temperature=0` explicitly to both `OpenAILike(...)` constructor calls (groq and nvidia branches).
5. **Found via:** Manual audit against `Guardrails.md`'s `temperature = 0` requirement.

### 12. Empty filing-list argument was indistinguishable from "not provided" (2026-08-04)

1. **Bug:** `document_ids = document_ids or _ALL_FILINGS` treated an explicitly empty tuple (`()`, meaning "restrict to zero filings") identically to `None` ("not provided"), since both are falsy in Python -- both silently defaulted to using every filing.
2. **Root cause:** Truthiness-based fallback (`x or default`) instead of an explicit `is None` check, on a parameter where the empty-collection case is a meaningful, distinct input.
3. **Impact / Severity:** High -- a dataset-generation run intended to be scoped to zero/specific filings could silently run against the entire corpus with no error or warning, corrupting scope control for that run.
4. **Fix:** Changed to `document_ids = _ALL_FILINGS if document_ids is None else document_ids`.
5. **Found via:** Manual code review flagged during a tracked-issues pass (Doubt #13).

### 13. No duplicate-question check let near-identical questions into the benchmark set (2026-08-04)

1. **Bug:** Nothing stopped two near-identical questions, generated independently from different sections or documents, from both being accepted into the final 140-query benchmark set.
2. **Root cause:** The acceptance path checked a candidate against its own generation constraints only, never against the growing set of already-accepted questions.
3. **Impact / Severity:** High -- duplicate questions in the evaluation set could inflate or bias the three-pipeline comparison results, the dissertation's core output.
4. **Fix:** Added `database_manager.get_all_query_texts()` and a rejection check: a candidate scoring >=0.92 embedding similarity against any already-accepted query is rejected and retried with feedback naming the duplicate.
5. **Found via:** Manual review flagged during a tracked-issues pass (Doubt #14).

---

*Bugs #12 and #13 above are the same underlying fixes as `deviations.md` entries 3 and 1 respectively -- both files record them because this one captures the defect/root-cause framing, while `deviations.md` captures the spec-conformance framing. See that file for the fuller "originally proposed vs. what we did" account.*
