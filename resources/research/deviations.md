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

### 2. LLM temperature not pinned to 0 (2026-08-04)

1. **Originally proposed:** Guardrails.md mandates `temperature = 0` for all LLM calls, project-wide.
2. **Deviation:** `LLMFactory.get_client()` built `OpenAILike(...)` with no `temperature` kwarg, silently falling back to `llama_index`'s default of `0.1`.
3. **What we did:** Set `temperature=0` explicitly on every LLM client `LLMFactory` constructs.
4. **How we did it:** Added `temperature=0` to both `OpenAILike(...)` constructor calls (`groq` and `nvidia` branches) in `llm_factory.py`.
5. **Why we did it:** At `0.1`, sampling is stochastic — the same model, same document, could produce a different-length summary and token count run to run, undermining reproducibility.

### 3. Multi-provider LLM client abstraction (NVIDIA NIM) (2026-07-31)

1. **Originally proposed:** All LLM calls run on Groq's free tier.
2. **Deviation:** Groq's free tier was repeatedly exhausted during P3 builds and Phase 4 testing — daily/per-minute limits ran out before a clean run completed.
3. **What we did:** Added NVIDIA NIM as a second provider, used specifically for P3's index build, to give it quota headroom outside Groq's shared limits.
4. **How we did it:** New `project/llm_client/` package — `nim_client.py` (40 RPM limit, semaphore, retry), `llm_factory.py`'s `LLMFactory` (provider dispatch by `{model, provider}` config), `config.py` updated for NIM keys/endpoint. P3's model moved to `nemotron-3-super-120b-a12b` via NIM.
5. **Why we did it:** A second provider was the only way to keep P3 builds running without hitting Groq's daily/per-minute ceiling mid-build.

### 4. No backup/restore for downloaded and generated project data (2026-08-04)

1. **Originally proposed:** No explicit requirement — but ingested filings, parsed text, and built indexes are gitignored, expensive-to-reproduce state.
2. **Deviation:** No recovery path existed if that state was lost — a crash or bad experiment meant redoing SEC EDGAR fetches, LlamaParse credits, and Groq/NIM-billed index builds.
3. **What we did:** Added scripts to snapshot and restore that state.
4. **How we did it:** `project/scripts/backup_data.sh` snapshots `benchmark.db`(+WAL/SHM), `storage/`, `.env`, `data/raw`, `data/parsed`, `logs` into timestamped folders; `reload_backup.sh` restores a chosen snapshot with a pre-restore safety snapshot and SHA-256 checksum verification.
5. **Why we did it:** To make expensive, quota-consuming rebuilds recoverable rather than a total loss.

### 5. Critic/Judge model no longer available on Groq (2026-07-21)

1. **Originally proposed:** Critic and Judge run on `Qwen3-32b`.
2. **Deviation:** Groq's free tier stopped hosting `qwen/qwen3-32b` (confirmed via a live `models.list()` call returning 404 on all Critic/Judge routes).
3. **What we did:** Swapped both roles to `qwen/qwen3.6-27b`, the closest available Qwen model on the account.
4. **How we did it:** Updated the model routing config and every spec document that named the old model.
5. **Why we did it:** The originally specified model was withdrawn from the free tier; role-separation invariants (Critic/Judge ≠ Generator/Answerer family) were preserved with the replacement.

### 6. P3 index build bypasses the shared Groq client wrapper (2026-07-22)

1. **Originally proposed:** All Groq calls route through `groq_client.call_groq()`.
2. **Deviation:** P3's index build calls `llama_index.llms.groq.Groq` directly instead.
3. **What we did:** Kept this as a scoped, deliberate exception rather than reworking Phase 5.
4. **How we did it:** Mitigated the risk (no tuned 429 backoff on the direct client) with sequential-only builds, atomic temp-dir-then-rename persistence, and per-filing token/wall-clock cost logging.
5. **Why we did it:** Phase 5's P3 pipeline needs a real `TreeIndex.as_retriever()`, which only exists on a genuine LlamaIndex index object — a custom-built tree would have forced a larger deviation later.

### 7. LlamaParse table-header extraction defect (2026-07-26)

1. **Originally proposed:** Parsed 10-K tables should have clean, correctly aligned header rows.
2. **Deviation:** 31 tables across 5 of 9 filings (`MSFT` x3, `TSLA_2023`, `TSLA_2025`) have a units caption merged into the header row, shifting header/separator rows down by one.
3. **What we did:** Ran a full data-integrity audit; applied no fix.
4. **How we did it:** Verified storage-file validity, tree-structure consistency, and DB sanity all passed clean — only header/column labeling is affected, not the underlying figures.
5. **Why we did it:** Root cause is upstream in LlamaParse's handling of caption-prefixed tables, not this project's code — documented as a known limitation for the dissertation rather than worked around.

### 8. Dataset-generation retry and grading were too rigid (2026-07-28)

1. **Originally proposed:** A rejected candidate query gets retried; two equivalent answers should both pass the cross-check.
2. **Deviation:** Retries used identical, temperature-0 input, guaranteeing the same rejected output; numeric matching required an exact count of numbers, so "$100 million" failed against "$100 million in 2025."
3. **What we did:** Retries now carry forward what specifically failed; numeric matching now checks subset containment, not exact count.
4. **How we did it:** Retry prompts include the rejection reason and nudge toward a different node/angle; added a third gate — `bge-small-en-v1.5` embedding cosine similarity between answers — alongside the loosened numeric check.
5. **Why we did it:** Identical retries wasted attempts and quota for no chance of success; overly strict numeric matching penalised correct answers for unrelated extra numbers.

### 9. Embedding library unavailable on this platform (2026-07-28)

1. **Originally proposed:** `sentence-transformers`/`FlagEmbedding` load `bge-small-en-v1.5` for embedding similarity.
2. **Deviation:** Both depend on `torch`, which publishes no wheel for macOS x86_64 + Python 3.13 — confirmed via a live install dry-run.
3. **What we did:** Used `fastembed` instead, loading the identical model weights.
4. **How we did it:** Pinned `fastembed` with `onnxruntime==1.23.2`; verified identical similarity scores against the originally intended library.
5. **Why we did it:** Same model, ONNX Runtime instead of PyTorch — installable on this machine with a much smaller footprint; Phase 5's P1 embedding path should re-check this same constraint later.

### 10. No token-size guard on Generator prompts (2026-07-29)

1. **Originally proposed:** The Generator receives a full filing section's content in one prompt.
2. **Deviation:** A few real sections run to ~29,000 tokens, and the DB's `token_count` column is a plain word count, not a real tokenizer count — no reliable guard against exceeding the model's request limit.
3. **What we did:** Added a real token count check and automatic chunking for oversized sections.
4. **How we did it:** Added `tiktoken` to count tokens accurately; sections over 60,000 tokens are split at node boundaries via `chunk_section()`.
5. **Why we did it:** To close a real correctness gap before it caused a hard failure — the largest section measured (~29,478 tokens) is currently safe, but corpus size may grow.

### 11. P3 summariser model judged too weak (2026-07-29)

1. **Originally proposed:** P3 uses `llama-3.1-8b-instant`, chosen for its high free-tier request ceiling.
2. **Deviation:** 8B was judged too small for reliable summary quality on dense financial filing sections.
3. **What we did:** Swapped to `openai/gpt-oss-20b` and rebuilt the full corpus.
4. **How we did it:** Considered and rejected `Llama 3.3 70B` (shared with the Answerer — unfair advantage) and `Qwen3.6-27B` (already reused for Critic/Judge); also fixed the filing manifest, which was still pinned to 9 filings instead of the expanded 18.
5. **Why we did it:** Quality, not throughput, was the concern this time — a cleaner model with no role overlap and no client rewrite needed.

### 12. GQ hand-labelling scale had no validation (2026-07-29)

1. **Originally proposed:** Human graders score each of the 20 golden queries 1–10.
2. **Deviation:** No sanity check existed — a typo like "99" would be silently accepted; a mistyped query ID during import silently updated nothing while still reporting success.
3. **What we did:** Rescaled scoring to 0–100 with enforced validation, and added a separate "good/bad exemplar" flag.
4. **How we did it:** `update_golden_query_labels()` now raises on an out-of-range score; label import raises on an unmatched query ID instead of silently no-op'ing; added a nullable `is_good` column and label-file field; also fixed a schema-drift bug (`CREATE TABLE IF NOT EXISTS` never updates an existing table) with a migration that refuses to touch real data, and a regex bug that silently dropped older-format entries.
5. **Why we did it:** Silent failure on human-entered data is exactly the kind of error that corrupts a dissertation's evaluation labels without anyone noticing.

### 13. Query ID format was long and quadrant-label-ambiguous (2026-07-29)

1. **Originally proposed:** No fixed format was mandated for query IDs.
2. **Deviation:** IDs like `Q1_Direct_Text_queries_0001` were needlessly long, and `Q1`–`Q4` read as ambiguous against fiscal quarters in a project built on 10-K filings.
3. **What we did:** Shortened the format and renamed the prefix.
4. **How we did it:** New format `{QT#}_{table_code}_{seq:03d}` (e.g. `QT1_PQ_001`), using `QT` (Query Type) instead of reusing `Q`; sequence padding reduced from 4 digits to 3 to match the real per-quadrant caps.
5. **Why we did it:** Readability and to remove ambiguity with fiscal-quarter terminology, at the user's explicit request.

### 14. Search tool biased toward long, wordy text (2026-07-29)

1. **Originally proposed:** The Critic's local search tool should find the most relevant filing text for a query.
2. **Deviation:** It scored nodes by raw keyword-occurrence count, so a long node repeating a term several times could outrank a short, precise, more relevant node.
3. **What we did:** Switched to length-normalised term frequency.
4. **How we did it:** `score = raw_count / len(node_tokens)` instead of raw count, with a floor on the denominator so a degenerate 1–2 token node can't win purely by being tiny.
5. **Why we did it:** Deliberately avoided adding IDF or a BM25 library — this tool gatekeeps which questions enter the dataset, and resembling P2's real BM25 scoring too closely would bias the dataset toward questions P2 finds easy, an unearned advantage in the later benchmark.
