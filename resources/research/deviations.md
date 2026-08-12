# Deviations from Original Proposed Idea

Each entry: what was originally intended, what deviation/gap occurred, what was done, how, and why. Newest first.

---

### 1. Dataset generation had no duplicate-question check (2026-08-04)

1. **Originally proposed:** The Generator/Critic/cross-check pipeline should produce 140 unique benchmark questions.
2. **Deviation:** Nothing stopped two near-identical questions, generated from different sections or documents, from both being accepted into the final set.
3. **What we did:** Rejected any candidate question too similar to one already accepted.
4. **How we did it:** Added `database_manager.get_all_query_texts()`, pulling `(query_id, query_text)` across all three quadrant-fill tables; `_attempt_fill()` now rejects a candidate scoring ≥0.92 `bge-small-en-v1.5` embedding similarity against any accepted query, retrying with feedback naming the duplicate.
5. **Why we did it:** Duplicate questions in the evaluation set would inflate or bias the pipeline comparison results.

### 2. Dataset generation could silently fall short of its 140-question target (2026-08-04)

1. **Originally proposed:** Each run should produce the full 140-question dataset (100 PQ / 20 GQ / 20 JEQ).
2. **Deviation:** If a run couldn't fill every target, it stopped quietly with no indication of how far short it fell.
3. **What we did:** Added an end-of-run underfill report.
4. **How we did it:** `format_underfill_summary()` builds a per-quadrant/per-table fill-vs-target summary, printed and durably logged at the end of every run.
5. **Why we did it:** A reported dataset size of "140 questions" needs to be verifiable at face value, not silently short, for the methodology write-up.

### 3. Empty filing-list argument was indistinguishable from "not provided" (2026-08-04)

1. **Originally proposed:** Dataset generation should be restrictable to an explicit subset of filings, including an explicitly empty subset.
2. **Deviation:** `document_ids or _ALL_FILINGS` treated an explicitly empty tuple the same as `None`, since both are falsy in Python — both defaulted to all filings.
3. **What we did:** Made "not provided" the only case that defaults to all filings.
4. **How we did it:** Changed to `document_ids = _ALL_FILINGS if document_ids is None else document_ids`.
5. **Why we did it:** A silent "use everything" default when zero filings was intended could run a dataset generation pass against the wrong scope with no error or warning.

### 4. Questions clustered by company instead of by quadrant difficulty (2026-08-04)

1. **Originally proposed:** Quadrant difficulty (direct/implicit, text/table) should be the dataset's only structural axis.
2. **Deviation:** Sections were filled into quadrants in encounter order, so one company's filings could dominate a quadrant simply because they were processed first.
3. **What we did:** Interleaved sections across companies within each content pool.
4. **How we did it:** Added `_round_robin_interleave()`, cycling through companies one section at a time in `build_pools()`, instead of exhausting one company's sections before moving to the next.
5. **Why we did it:** Without this, an observed "pipeline X struggles on hard questions" result could really mean "pipeline X struggles on Company Y's filings" — no way to separate the two explanations.

### 5. P3 token-cost logging silently recorded zero (2026-08-04)

1. **Originally proposed:** Every P3 build should log real input/output token counts via `TokenCountingHandler`, so build cost is auditable.
2. **Deviation:** After the `LLMFactory` refactor, every P3 build logged `input_tokens: 0, output_tokens: 0` — real summaries were generated, but cost went unrecorded.
3. **What we did:** Wired the LLM object itself to the same `CallbackManager` already passed to `TreeIndex`, so token-usage events reach the counter.
4. **How we did it:** Added an optional `callback_manager` parameter to `LLMFactory.get_client()`/`get_client_for_stage()`, forwarded into `OpenAILike(...)`; `build_index_for_document()` now passes one shared `CallbackManager` to both `LLMFactory` and `TreeIndex`.
5. **Why we did it:** `llama_index`'s `llm_chat_callback()` decorator fires usage events on the LLM's own `callback_manager` attribute, not the index's — `TreeIndex` only forwards its bus to an LLM at query time, not during the build.

### 6. LLM temperature not pinned to 0 (2026-08-04)

1. **Originally proposed:** Guardrails.md mandates `temperature = 0` for all LLM calls, project-wide.
2. **Deviation:** `LLMFactory.get_client()` built `OpenAILike(...)` with no `temperature` kwarg, silently falling back to `llama_index`'s default of `0.1`.
3. **What we did:** Set `temperature=0` explicitly on every LLM client `LLMFactory` constructs.
4. **How we did it:** Added `temperature=0` to both `OpenAILike(...)` constructor calls (`groq` and `nvidia` branches) in `llm_factory.py`.
5. **Why we did it:** At `0.1`, sampling is stochastic — the same model, same document, could produce a different-length summary and token count run to run, undermining reproducibility.

### 7. Multi-provider LLM client abstraction (NVIDIA NIM) (2026-07-31)

1. **Originally proposed:** All LLM calls run on Groq's free tier.
2. **Deviation:** Groq's free tier was repeatedly exhausted during P3 builds and Phase 4 testing — daily/per-minute limits ran out before a clean run completed.
3. **What we did:** Added NVIDIA NIM as a second provider, used specifically for P3's index build, to give it quota headroom outside Groq's shared limits.
4. **How we did it:** New `project/llm_client/` package — `nim_client.py` (40 RPM limit, semaphore, retry), `llm_factory.py`'s `LLMFactory` (provider dispatch by `{model, provider}` config), `config.py` updated for NIM keys/endpoint. P3's model moved to `nemotron-3-super-120b-a12b` via NIM.
5. **Why we did it:** A second provider was the only way to keep P3 builds running without hitting Groq's daily/per-minute ceiling mid-build.

### 8. No backup/restore for downloaded and generated project data (2026-08-04)

1. **Originally proposed:** No explicit requirement — but ingested filings, parsed text, and built indexes are gitignored, expensive-to-reproduce state.
2. **Deviation:** No recovery path existed if that state was lost — a crash or bad experiment meant redoing SEC EDGAR fetches, LlamaParse credits, and Groq/NIM-billed index builds.
3. **What we did:** Added scripts to snapshot and restore that state.
4. **How we did it:** `project/scripts/backup_data.sh` snapshots `benchmark.db`(+WAL/SHM), `storage/`, `.env`, `data/raw`, `data/parsed`, `logs` into timestamped folders; `reload_backup.sh` restores a chosen snapshot with a pre-restore safety snapshot and SHA-256 checksum verification.
5. **Why we did it:** To make expensive, quota-consuming rebuilds recoverable rather than a total loss.

### 9. Critic/Judge model no longer available on Groq (2026-07-21)

1. **Originally proposed:** Critic and Judge run on `Qwen3-32b`.
2. **Deviation:** Groq's free tier stopped hosting `qwen/qwen3-32b` (confirmed via a live `models.list()` call returning 404 on all Critic/Judge routes).
3. **What we did:** Swapped both roles to `qwen/qwen3.6-27b`, the closest available Qwen model on the account.
4. **How we did it:** Updated the model routing config and every spec document that named the old model.
5. **Why we did it:** The originally specified model was withdrawn from the free tier; role-separation invariants (Critic/Judge ≠ Generator/Answerer family) were preserved with the replacement.

### 10. P3 index build bypasses the shared Groq client wrapper (2026-07-22)

1. **Originally proposed:** All Groq calls route through `groq_client.call_groq()`.
2. **Deviation:** P3's index build calls `llama_index.llms.groq.Groq` directly instead.
3. **What we did:** Kept this as a scoped, deliberate exception rather than reworking Phase 5.
4. **How we did it:** Mitigated the risk (no tuned 429 backoff on the direct client) with sequential-only builds, atomic temp-dir-then-rename persistence, and per-filing token/wall-clock cost logging.
5. **Why we did it:** Phase 5's P3 pipeline needs a real `TreeIndex.as_retriever()`, which only exists on a genuine LlamaIndex index object — a custom-built tree would have forced a larger deviation later.

### 11. LlamaParse table-header extraction defect (2026-07-26)

1. **Originally proposed:** Parsed 10-K tables should have clean, correctly aligned header rows.
2. **Deviation:** 31 tables across 5 of 9 filings (`MSFT` x3, `TSLA_2023`, `TSLA_2025`) have a units caption merged into the header row, shifting header/separator rows down by one.
3. **What we did:** Ran a full data-integrity audit; applied no fix.
4. **How we did it:** Verified storage-file validity, tree-structure consistency, and DB sanity all passed clean — only header/column labeling is affected, not the underlying figures.
5. **Why we did it:** Root cause is upstream in LlamaParse's handling of caption-prefixed tables, not this project's code — documented as a known limitation for the dissertation rather than worked around.

### 12. Dataset-generation retry and grading were too rigid (2026-07-28)

1. **Originally proposed:** A rejected candidate query gets retried; two equivalent answers should both pass the cross-check.
2. **Deviation:** Retries used identical, temperature-0 input, guaranteeing the same rejected output; numeric matching required an exact count of numbers, so "$100 million" failed against "$100 million in 2025."
3. **What we did:** Retries now carry forward what specifically failed; numeric matching now checks subset containment, not exact count.
4. **How we did it:** Retry prompts include the rejection reason and nudge toward a different node/angle; added a third gate — `bge-small-en-v1.5` embedding cosine similarity between answers — alongside the loosened numeric check.
5. **Why we did it:** Identical retries wasted attempts and quota for no chance of success; overly strict numeric matching penalised correct answers for unrelated extra numbers.

### 13. Embedding library unavailable on this platform (2026-07-28)

1. **Originally proposed:** `sentence-transformers`/`FlagEmbedding` load `bge-small-en-v1.5` for embedding similarity.
2. **Deviation:** Both depend on `torch`, which publishes no wheel for macOS x86_64 + Python 3.13 — confirmed via a live install dry-run.
3. **What we did:** Used `fastembed` instead, loading the identical model weights.
4. **How we did it:** Pinned `fastembed` with `onnxruntime==1.23.2`; verified identical similarity scores against the originally intended library.
5. **Why we did it:** Same model, ONNX Runtime instead of PyTorch — installable on this machine with a much smaller footprint; Phase 5's P1 embedding path should re-check this same constraint later.

### 14. No token-size guard on Generator prompts (2026-07-29)

1. **Originally proposed:** The Generator receives a full filing section's content in one prompt.
2. **Deviation:** A few real sections run to ~29,000 tokens, and the DB's `token_count` column is a plain word count, not a real tokenizer count — no reliable guard against exceeding the model's request limit.
3. **What we did:** Added a real token count check and automatic chunking for oversized sections.
4. **How we did it:** Added `tiktoken` to count tokens accurately; sections over 60,000 tokens are split at node boundaries via `chunk_section()`.
5. **Why we did it:** To close a real correctness gap before it caused a hard failure — the largest section measured (~29,478 tokens) is currently safe, but corpus size may grow.

### 15. P3 summariser model judged too weak (2026-07-29)

1. **Originally proposed:** P3 uses `llama-3.1-8b-instant`, chosen for its high free-tier request ceiling.
2. **Deviation:** 8B was judged too small for reliable summary quality on dense financial filing sections.
3. **What we did:** Swapped to `openai/gpt-oss-20b` and rebuilt the full corpus.
4. **How we did it:** Considered and rejected `Llama 3.3 70B` (shared with the Answerer — unfair advantage) and `Qwen3.6-27B` (already reused for Critic/Judge); also fixed the filing manifest, which was still pinned to 9 filings instead of the expanded 18.
5. **Why we did it:** Quality, not throughput, was the concern this time — a cleaner model with no role overlap and no client rewrite needed.

### 16. GQ hand-labelling scale had no validation (2026-07-29)

1. **Originally proposed:** Human graders score each of the 20 golden queries 1–10.
2. **Deviation:** No sanity check existed — a typo like "99" would be silently accepted; a mistyped query ID during import silently updated nothing while still reporting success.
3. **What we did:** Rescaled scoring to 0–100 with enforced validation, and added a separate "good/bad exemplar" flag.
4. **How we did it:** `update_golden_query_labels()` now raises on an out-of-range score; label import raises on an unmatched query ID instead of silently no-op'ing; added a nullable `is_good` column and label-file field; also fixed a schema-drift bug (`CREATE TABLE IF NOT EXISTS` never updates an existing table) with a migration that refuses to touch real data, and a regex bug that silently dropped older-format entries.
5. **Why we did it:** Silent failure on human-entered data is exactly the kind of error that corrupts a dissertation's evaluation labels without anyone noticing.

### 17. Query ID format was long and quadrant-label-ambiguous (2026-07-29)

1. **Originally proposed:** No fixed format was mandated for query IDs.
2. **Deviation:** IDs like `Q1_Direct_Text_queries_0001` were needlessly long, and `Q1`–`Q4` read as ambiguous against fiscal quarters in a project built on 10-K filings.
3. **What we did:** Shortened the format and renamed the prefix.
4. **How we did it:** New format `{QT#}_{table_code}_{seq:03d}` (e.g. `QT1_PQ_001`), using `QT` (Query Type) instead of reusing `Q`; sequence padding reduced from 4 digits to 3 to match the real per-quadrant caps.
5. **Why we did it:** Readability and to remove ambiguity with fiscal-quarter terminology, at the user's explicit request.

### 18. Search tool biased toward long, wordy text (2026-07-29)

1. **Originally proposed:** The Critic's local search tool should find the most relevant filing text for a query.
2. **Deviation:** It scored nodes by raw keyword-occurrence count, so a long node repeating a term several times could outrank a short, precise, more relevant node.
3. **What we did:** Switched to length-normalised term frequency.
4. **How we did it:** `score = raw_count / len(node_tokens)` instead of raw count, with a floor on the denominator so a degenerate 1–2 token node can't win purely by being tiny.
5. **Why we did it:** Deliberately avoided adding IDF or a BM25 library — this tool gatekeeps which questions enter the dataset, and resembling P2's real BM25 scoring too closely would bias the dataset toward questions P2 finds easy, an unearned advantage in the later benchmark.

### 19. P2 BM25 storage granularity unspecified (2026-08-10)

1. **Originally proposed:** `Architecture.md` names `storage/bm25/` "pickled corpora" without specifying per-document vs. combined-file granularity.
2. **Deviation:** No single-file structure was defined, so the build/resumability contract was ambiguous going into implementation.
3. **What we did:** One pickle per `document_id` (`storage/bm25/<document_id>.pkl`), each holding `{"node_ids": [...], "bm25": BM25Okapi}` for that filing only.
4. **How we did it:** `build_bm25_index.py` mirrors P1's (`build_vector_index.py`) and P3's (`build_summary_index.py`) skip-if-already-built pattern, keyed on document id, with an atomic temp-file-plus-rename write.
5. **Why we did it:** Per-document resumability is crash-safe and `LOCAL_TEST_THROTTLE`-friendly, and matches the rest of the codebase's per-filing granularity — a single combined pickle would lose per-document resumability and put the whole corpus at risk on a mid-build crash.

### 20. Corpus reduced from 18 to 13 filings (2026-08-11)

1. **Originally proposed:** `Architecture.md` §0 fixed the corpus at 18 filings (6 companies × 3 fiscal years: AAPL, MSFT, TSLA, JPM, JNJ, WMT × FY2023–2025).
2. **Deviation:** Only 13 of the 18 filings had a P3 summary-tree index built (P1/P2 build lazily per document and were unaffected). Missing: WMT (all 3 fiscal years) and JPM/JNJ's FY2025 filing each. Ingestion (Phase 2) had already completed for all 18; dataset generation (Phase 4) had not started (`queries`/`golden_queries`/`judge_validation` all empty at the time of this decision).
3. **What we did:** Fixed the corpus at the 13 already-built filings — AAPL, MSFT, TSLA at FY2023–2025 (3 years each), JPM and JNJ at FY2023–2024 (2 years each) — dropping Walmart and both companies' FY2025 filings, rather than completing the remaining 5 P3 builds.
4. **How we did it:** Trimmed `data/filings_manifest.json` to the 13 entries so every downstream stage (dataset generation, P1/P2/P3 index builds) treats 13 as the full corpus consistently; updated `Architecture.md`, `Phase Plan.md`, `README.md`, and `token_usage.md`'s Phase 3 cost projection (scaled 18→13 proportionally, since input tokens scale linearly with filing count) to match. Left `resources/artifacts/` (the submitted proposal) and historical entries in `issues.md`/this file untouched, since they are accurate records of what was true at the time they were written, not statements of current scope. Left the already-ingested raw/parsed data for the dropped filings and their `nodes` rows in place rather than deleting them, since removing them is irreversible (not git-tracked) and they are harmless if simply unreferenced by the trimmed manifest.
5. **Why we did it:** The 5 missing filings had not entered the query dataset yet, so this was the cheapest possible point to cut scope — zero query-generation rework. Continuing to the full 18 would have cost 5 more LLM-based tree-index builds for no research benefit: the study compares retrieval paradigms on 10-K structure, not cross-industry generalization, and the retained 13 filings keep the industry with the densest tabular/footnote structure (JPM) in scope, so paradigm-stress-testing coverage is preserved despite the narrower company count.

### 21. LLMFactory silently dropped its own retry/semaphore wrapping (2026-08-11)

1. **Originally proposed:** `LLMFactory.get_client()` builds a retry+semaphore-wrapped async client (`groq_client.get_groq_client()` / `nim_client.get_nim_client()`) and wires it into the `OpenAILike` LLM object every stage (Generator, Critic, P3 index build, and the not-yet-built Answerer) is meant to use, so backoff/concurrency limiting applies everywhere per Guardrails.md §1's resilient-client requirement.
2. **Deviation:** The wiring used `OpenAILike(..., async_client=raw_client, ...)`, but `async_client` isn't a real field on `OpenAILike`/`OpenAI` — pydantic's `arbitrary_types_allowed` config silently accepts and discards unknown kwargs, so `raw_client` was never stored anywhere. `OpenAILike._get_aclient()` built its own plain `AsyncOpenAI` internally instead, meaning every call through this factory (including the already-completed Phase 3 P3 builds, all 13 filings) ran with zero retry/backoff/concurrency protection despite `groq_client.py`/`nim_client.py` building that protection correctly. Separately, `async_generator.py`'s `generate_query()` called `client.chat.completions.create(...)` — a raw-OpenAI-SDK shape that doesn't exist on the `OpenAILike` object the factory actually returns (`AttributeError: 'function' object has no attribute 'completions'`); never caught because the existing test suite mocked around this exact shape rather than exercising the real interface.
3. **What we did:** Set the private `_aclient` cache slot directly on the constructed `OpenAILike` instance (`llm._aclient = raw_client`) instead of passing the nonexistent kwarg. Fixed `generate_query()` to call `client.achat([ChatMessage(...)])`, the real LlamaIndex interface already proven working via `build_summary_index.py`'s `TreeIndex` usage.
4. **How we did it:** Verified the root cause empirically (constructed a real `OpenAILike`, confirmed `async_client=` is silently dropped and `.chat.completions.create` doesn't exist) before changing anything, per systematic debugging. Added `tests/test_llm_factory.py` (proves `_aclient` injection is honored for both groq and nvidia branches) and rewrote `tests/test_async_generator.py` using a real `OpenAILike` with a swapped `_aclient`, so the regression test fails under the old call pattern and passes under the fix — not just an interface mock.
5. **Why we did it:** This was the correct minimal fix at the actual root cause (the factory's client-injection point), not a workaround at each call site — every current and future stage that goes through `LLMFactory.get_client()` gets the fix for free. Already-completed P3 summary content is unaffected (a completed build's API responses are genuine regardless of retry wrapping; the gap was resilience against transient failures during the build, not output correctness). `async_critic.py` has the identical call-shape bug but its multi-round tool-calling loop needs LlamaIndex's `achat_with_tools()` — a different shape than the raw OpenAI tool schema it uses now — left open as a separate, larger fix rather than bundled into this one.

### 22. Architecture.md still described P3 as `SummaryIndex`, not the `TreeIndex` actually built (2026-08-11)

1. **Originally proposed:** `Architecture.md` §5/§6 and its module table describe P3's build and query-time retrieval as `SummaryIndex.as_retriever(retriever_mode="embedding", similarity_top_k=k)`.
2. **Deviation:** Entry 10 above already committed P3's build step to a real `TreeIndex` instead of `SummaryIndex` (2026-07-22), specifically because `TreeIndex.as_retriever()` is a genuine LlamaIndex retriever and a hand-built tree over `SummaryIndex` would have forced a larger rework later. `Architecture.md`'s prose was never updated to match, so it still names the wrong class and the wrong `retriever_mode` string in four places. This surfaced because `pipelines/structural/p3_structural.py` (the query-time retriever, built this session to close the Phase 5 gap) was implemented against the real `TreeIndex` persisted on disk, not against the stale spec text.
3. **What we did:** Implemented `P3StructuralRetriever` against `TreeIndex.as_retriever(retriever_mode="select_leaf_embedding")` — `TreeIndex`'s equivalent of pure cosine-similarity leaf selection, with `MockLLM` bound at load so no LLM call can occur at query time, preserving the same no-LLM-at-query-time invariant the stale spec text was trying to describe. Corrected `Architecture.md`'s four `SummaryIndex`/`"embedding"` references to `TreeIndex`/`"select_leaf_embedding"` to match.
4. **How we did it:** Traced the mismatch by cross-referencing `build_summary_index.py`'s actual persisted index type against `Architecture.md`'s §5 prose and module table, confirmed entry 10 already covered the build-side decision, and updated only the query-time-retrieval wording (build-side wording in entry 10 was already correct).
5. **Why we did it:** Documentation drift, not a functional bug — `select_leaf_embedding` delivers the same "local, embedding-only, no Groq call" behaviour the spec always intended. Left uncorrected, a reader implementing against the spec text alone would look for a `SummaryIndex`/`"embedding"` retriever mode that doesn't exist on the object this project actually persists.

### 23. Generator moved from Groq to NVIDIA NIM to escape a structural TPM wall (2026-08-12)

1. **Originally proposed:** `Guardrails.md` §2 fixes the Generator (`openai/gpt-oss-120b`) on Groq's free tier, alongside every other stage except P3's index build.
2. **Deviation:** Groq's free tier caps `gpt-oss-120b` at ~8,000 tokens per minute (TPM). `_MAX_SECTION_TOKENS` allows a filing section up to 60,000 tokens before the Generator prompt is built, so any section over roughly 8,000 tokens is guaranteed to fail with a 413 (`rate_limit_exceeded`) on every attempt — not a transient failure, a structural one. Confirmed live: `TSLA_2023`, `JPM_2023`, and `JNJ_2023` each hit this wall 3/3 attempts during the real throttled dry runs earlier this session (see `bugs.md` #2), wasting all three retries per section for a guaranteed-zero chance of success.
3. **What we did:** Repointed `MODEL_ROUTING["generator"]`'s provider from `groq` to `nvidia`, keeping the exact same model id (`openai/gpt-oss-120b` — NIM hosts the identical model under the identical name). NIM's free tier is rate-limited by requests-per-minute (40 RPM, already enforced in `nim_client.py`), not by tokens-per-minute — no published TPM/TPD ceiling exists for NIM, so an oversized section that Groq structurally cannot accept is no longer capped by a token budget on the provider side.
4. **How we did it:** One-line change in `llm_client/config.py` (`MODEL_ROUTING["generator"]["provider"]`), no code path changes needed since `LLMFactory.get_client()` already dispatches on provider via the existing `match` statement, and `nim_client.get_nim_client()` already exists (originally built for P3's index build, deviation #7). Updated `Guardrails.md`'s model-assignment table (`Dataset generation` row) from "Groq free" to "NIM free" to keep the binding spec in sync, per the file's own "do not change without updating the spec" comment in `config.py`. Verified with a real, throttled run pinned to the three filings that previously 413'd (`TSLA_2023`, `JPM_2023`, `JNJ_2023`).
5. **Why we did it:** Widening the exception catch (deviation/bug fix earlier this session) stopped the 413 from crashing the orchestrator, but did nothing to stop the 413 from happening in the first place — every oversized section was still guaranteed to burn all 3 retries for zero acceptance chance. Switching providers addresses the actual root cause (Groq's per-model token ceiling) rather than papering over its symptom. The anti-self-grading invariant (Generator ≠ Critic model family) is unaffected — Critic remains on Groq's `qwen/qwen3.6-27b`, a different model family regardless of provider.

### 24. Generator moved a second time, from NVIDIA NIM to OpenRouter, with a $10 credit top-up (2026-08-12)

1. **Originally proposed:** `Budget.md`'s headline figure is **$0.00 expected spend** — every recurring component runs on a free tier or locally, no billing anywhere in the pipeline. Deviation #23 (above) had already moved the Generator from Groq to NVIDIA NIM to escape a structural token-per-minute wall.
2. **Deviation:** A real, live throttled run on NIM (verifying deviation #23's fix) completed without crashing, but with erratic per-call latency — one gap of roughly 3.5 hours between two Generator calls, against NIM's advertised 40 RPM ceiling, with no way from this project's logs alone to distinguish "NIM's shared-traffic queuing" from "NIM's own undocumented throttling" (NIM publishes no TPM/TPD limit, only the 40 RPM figure already enforced in code). This made wall-clock time for the full 140-query run unpredictable, and NIM's own limits are unquantified beyond RPM, unlike Groq's fully published table in `Budget.md`.
3. **What we did:** Moved the Generator to OpenRouter, using the free-suffixed model id (`openai/gpt-oss-120b:free`, still $0 per token), and funded the OpenRouter account with a one-time **$10 credit top-up** — not to pay for Generator tokens (the `:free` model remains $0/token even after funding), but because OpenRouter's own published limits state that reaching $10+ in lifetime credit purchases raises the free-model daily request cap from 50/day to 1,000/day; the per-minute cap (20 RPM) is unaffected by funding either way.
4. **How we did it:** Added `project/llm_client/openrouter_client.py` (mirrors `nim_client.py`'s retry/semaphore/rate-limit wrapper pattern exactly, at 20 RPM instead of 40), added `OPENROUTER_API_KEY`/`OPENROUTER_API_ENDPOINT`/`OPENROUTER_MAX_CONCURRENCY` to `config.py`, added an `"openrouter"` case to `LLMFactory.get_client()`'s existing provider dispatch (no changes needed to the dispatch mechanism itself — it already matched on a `provider` string). `MODEL_ROUTING["generator"]` now reads `{"model": "openai/gpt-oss-120b:free", "provider": "openrouter"}`. Updated `Guardrails.md`'s model-assignment table (`Dataset generation` row, `NIM free` → `OpenRouter`) to match, per the file's own "do not change without updating the spec" convention. Added `tests/test_llm_client_openrouter.py` and a factory-level regression test in `tests/test_llm_factory.py`, mirroring the existing groq/nvidia coverage.
5. **Why we did it:** OpenRouter's published limits are fully quantified (20 RPM, 50 or 1,000 req/day depending on funding) — unlike NIM's single-documented-number (40 RPM) with everything else unpublished — giving a predictable, plannable throughput ceiling for the real unthrottled run instead of an empirically-observed-but-unexplained multi-hour stall. The $10 top-up is a real, non-zero, one-time cost, and a genuine departure from `Budget.md`'s $0 headline claim — disclosed here explicitly per the project's existing precedent for exactly this tradeoff (`Budget.md`'s own "Headroom levers" section names a paid Developer tier as an acceptable, disclosed fallback for Groq specifically; the same reasoning is applied to OpenRouter here). It is a one-time account top-up, not a recurring or per-hour charge, so it does not violate `Guardrails.md` §1's absolute ban on per-hour/scale-to-non-zero infrastructure. The anti-self-grading invariant (Generator ≠ Critic model family) remains unaffected — Critic stays on Groq's `qwen/qwen3.6-27b`.

### 25. Generator's OpenRouter model swapped from `openai/gpt-oss-120b:free` to `nvidia/nemotron-3-super-120b-a12b:free` (2026-08-12)

1. **Originally proposed:** Deviation #24 (above) moved the Generator to OpenRouter using `openai/gpt-oss-120b:free`, chosen specifically to stay closest to the model family `Guardrails.md` §2 originally named for the Generator role.
2. **Deviation:** A live smoke test against the real OpenRouter API failed immediately with `404 Not Found`: `"This model is unavailable for free. The paid version is available now - use this slug instead: openai/gpt-oss-120b"`. `gpt-oss-120b:free` had been withdrawn from OpenRouter's free-model catalogue between the choice being made and the smoke test running minutes later — a live-catalogue drift, not a planning error.
3. **What we did:** Queried OpenRouter's `/api/v1/models` endpoint directly (406 models total) and filtered for `pricing.prompt == "0"` to get the actual, current list of free models — 19 results — rather than trusting search-engine/blog summaries a second time (the first provider-limits check earlier this session had already been flagged as needing a stricter live-source standard). Selected `nvidia/nemotron-3-super-120b-a12b:free` (262K context) from that live list: it is the exact same model already used and quality-vetted in this project for P3's index build (`p3_index_build` stage, `MODEL_ROUTING`), so its suitability for dense financial-filing text was already established, not a new unknown. `openai/gpt-oss-20b:free` (131K context, same family as the original spec, also quality-vetted per deviation #15's P3-summariser precedent) was presented as the closer-to-spec alternative but not chosen.
4. **How we did it:** One-line change to `MODEL_ROUTING["generator"]["model"]` in `config.py`; no other code changes needed (the `LLMFactory`/`openrouter_client.py` plumbing from deviation #24 is model-agnostic). Updated `Guardrails.md`'s model-assignment table to match. Verified live: `LLMFactory.get_client_for_stage("generator")` followed by a real `achat()` call returned a genuine completion (`"pong"`), then the full test suite (243 tests) run clean.
5. **Why we did it:** Correctness over minimal-deviation-from-spec — the originally chosen model was simply unavailable, confirmed via the provider's own live API rather than a second guess. Reusing P3's already-proven model for the Generator is a stronger quality bet than picking an untested-in-this-project alternative, and required no additional evaluation to justify. The anti-self-grading invariant (Generator ≠ Critic model family) still holds — Critic remains Qwen-family on Groq, Generator is now NVIDIA-family on OpenRouter.

### 26. Critic moved from Groq (`qwen/qwen3.6-27b`) to OpenRouter (`openai/gpt-oss-20b:free`) (2026-08-12)

1. **Originally proposed:** `Guardrails.md` §2 named the Critic role `Qwen3.6-27B` on Groq's free tier, chosen for its search-tool (function-calling) support and to stay a different model family from the Generator.
2. **Deviation:** A live run's failure log (`dataset_generation_failures.json`) showed the Critic hitting Groq's **daily token cap**: `"Rate limit reached for model qwen/qwen3.6-27b ... tokens per day (TPD): Limit 200000, Used 199648"`. With the Generator already moved to OpenRouter (deviations #24/#25), Groq's only remaining dataset-generation consumer was the Critic, and it alone was exhausting a 200K/day ceiling — stalling the run for repeated multi-minute waits with no headroom left for the day.
3. **What we did:** Moved the Critic to OpenRouter as well, on a free model that supports tool/function calling (a hard requirement — `async_critic.py` uses `achat_with_tools`, not plain chat). Queried OpenRouter's live `/api/v1/models` endpoint and filtered for `pricing.prompt == "0"` AND `"tools" in supported_parameters`: 16 of 19 free models qualified. Excluded every `nvidia/nemotron-*` entry to preserve the anti-self-grading invariant (Generator is `nvidia/nemotron-3-super-120b-a12b:free`; Critic must stay a different family). First tried `openai/gpt-oss-20b:free` — live smoke test hit a transient upstream 429 (`"temporarily rate-limited upstream"`, provider `Darkbloom`, shared free pool) that did not clear on immediate retry, so switched to `google/gemma-4-31b-it:free` (262K context, Google family) as a fallback — that smoke test succeeded after the retry/backoff wrapper absorbed a couple of transient 429s. Minutes later, on request, re-tried `openai/gpt-oss-20b:free` — the earlier congestion had cleared, and it now succeeded cleanly with zero retries. Settled on `openai/gpt-oss-20b:free` as final: same family already trusted in this project's Groq-era history, correctly searched (`achat_with_tools` tool-call round confirmed in the message history) and cited the one relevant node out of a mixed set.
4. **How we did it:** One-line change to `MODEL_ROUTING["critic"]` in `config.py` (final value `{"model": "openai/gpt-oss-20b:free", "provider": "openrouter"}`) — no plumbing changes needed, `LLMFactory`'s `"openrouter"` provider branch and `openrouter_client.py` are already model-agnostic from deviation #24. Updated `Guardrails.md`'s model-assignment table (`Dataset critique (+ search)` row) and its Generator≠Critic rule statement to match. Verified live via `dataset_generation.async_critic.critique_query()` directly against real nodes (JNJ_2023 Rule 10b5-1 question) for both candidate models, then full test suite (243 tests) run clean after the final switch.
5. **Why we did it:** Groq's daily cap was a hard, already-hit wall for the Critic specifically — not a hypothetical — and the same $0-cost, RPM-only-limited OpenRouter path already proven for the Generator applies equally well here, removing Groq from the dataset-generation critical path entirely (Groq now only serves the Answerer/Judge/debug stages, unaffected by this change). The anti-self-grading invariant is preserved by construction (excluded same-family candidates before selecting). This explicitly supersedes the original architectural choice of Groq/Qwen for the Critic role, per direct instruction to disregard that earlier decision in favour of resolving the live quota wall. The mid-session model swap (gemma → gpt-oss-20b) reflects OpenRouter's free-tier congestion being transient/provider-specific rather than a property of any one model — both cleared within minutes.
