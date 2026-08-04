# Changes

Simple running list of changes made to the project after the proposal was submitted.

- 2026-08-04: Corrects/expands the reasoning behind the 2026-07-31 entry below.
   `nim_client.py` and `LLMFactory`'s provider dispatch were added, and P3's
   index-build model was moved to NVIDIA NIM's `nemotron-3-super-120b-a12b`,
   because Groq's free tier was repeatedly getting exhausted during P3 builds
   and Phase 4 testing -- daily/per-minute limits ran out too fast to get a
   clean run, not purely a provider "evaluation" as the original entry implied.
   NVIDIA NIM was added as a second provider specifically to give P3's build
   headroom outside Groq's shared quota. No files changed by this entry --
   text-only clarification of prior reasoning.
- 2026-08-04: Added `project/scripts/backup_data.sh` and
   `project/scripts/reload_backup.sh`. Reason: downloaded/generated project
   state (`benchmark.db` + its WAL/SHM files, `storage/`, `.env`, `data/raw`,
   `data/parsed`, `logs`) is gitignored and expensive to reproduce -- it comes
   from SEC EDGAR fetches, LlamaParse credits, and Groq/NIM-billed index
   builds -- so a crash, bad experiment, or accidental overwrite could mean
   redoing hours of work and re-spending free-tier quota. `backup_data.sh`
   snapshots those paths into `backups/backup-<timestamp>/`, skipping any
   that don't exist and reporting what was/wasn't backed up. `reload_backup.sh`
   lists available snapshots, restores the chosen one only after explicit
   confirmation, takes a safety snapshot of current state first, and verifies
   the restore via SHA-256 checksum comparison rather than assuming success.
   Already used in practice: the 2026-07-29 P3 model-swap rebuild backed up
   the 9 pre-existing `storage/summary_index/` directories through this
   mechanism before forcing the clean rebuild.
- 2026-07-31: Added LLM provider abstraction supporting both Groq and NVIDIA NIM.
   Reason: To enable evaluation of NVIDIA Nemotron 3 Super for P3 index build while preserving existing Groq‑based workflows.
   Updated files: project/config.py, project/llm_client.py, project/groq_client.py (shim), resources/specs/Guardrails.md.
- 2026-07-21: Swapped Critic/Judge model from `Qwen3-32b` to `qwen/qwen3.6-27b`.
   Reason: Groq's free tier no longer hosts `qwen/qwen3-32b` (confirmed via live
   `models.list()` call and a 404 on all Critic/Judge routes). `qwen/qwen3.6-27b`
   is the closest available Qwen model on the account. Updated everywhere:
   `project/config.py`, `CLAUDE.md`, `resources/specs/resources/specs/Guardrails.md`,
   `resources/specs/Architecture.md`, `resources/specs/Budget.md`,
   `resources/specs/Project Idea.md`, `resources/specs/Phase Plan.md`,
   `openwiki/benchmark-design.md`, `openwiki/system-architecture.md`,
   `temp/directory-structure.md`. Role-separation invariants unaffected
   (Critic/Judge still a different model family from Generator/Answerer).
- 2026-07-22: Phase 3's index build calls `llama_index.llms.groq.Groq`
   directly instead of routing through `groq_client.call_groq()`. Reason:
   Phase 5's P3 pipeline needs `TreeIndex.as_retriever()`, which only exists
   on a real LlamaIndex index object -- a custom-built tree would force a
   second, larger deviation in Phase 5. Risk: LlamaIndex's own Groq client
   has no tuned 429 backoff/semaphore, and one filing's build fires dozens of
   summarization calls in a burst (TPM/RPM risk, not just daily volume).
   Could cost real time/money if unmitigated: a corrupted cache forcing a
   manual re-run, or repeated rate-limit failures pushing an earlier-than-
   planned move to Groq's paid Developer tier. Mitigated: builds run
   sequentially (never concurrent across filings), persisted via
   temp-dir-then-atomic-rename (a crash never leaves a false-positive cache
   hit), and token/wall-clock cost is logged per filing via
   `TokenCountingHandler`. Scoped to this one build step only -- Phase 4/6/7
   Groq calls remain on `call_groq()` unconditionally. Full reasoning in
   `docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md`.
- 2026-07-26: Data integrity audit of the full 9-filing corpus (post P3 build)
   found a LlamaParse extraction defect: 31 tables across 5 of 9 filings
   (`MSFT_2023/2024/2025`, `TSLA_2023`, `TSLA_2025`) have a misaligned header
   row where a units caption (e.g. `(in millions)`) merges into the table's
   first cell instead of sitting on its own line, shifting the header/
   separator rows down by one. `AAPL_2023/2024/2025` and `TSLA_2024` are
   clean. Underlying figures are intact -- only header/column labeling is
   affected, not the data itself. Storage-file validity (45/45), TreeIndex
   tree-structure consistency (9/9), and DB sanity (8,543 nodes, 0 empty/
   duplicate rows) all passed clean. Root cause is upstream in LlamaParse's
   handling of caption-prefixed tables, not this project's own parsing or
   chunking code. No fix applied -- read-only audit, documented for the
   dissertation's data-quality/limitations discussion. Full report:
   `monitor/reports/2026-07-26-data-integrity-audit-full-corpus.html`.
- 2026-07-28: Two fixes to Phase 4's dataset-generation cross-check, per
   discussion recorded in the final whole-branch review's Doubts #3/#4.
   (1) **Generator retry no longer identical.** All LLM calls run at
   `temperature=0` (deterministic) per spec, so retrying a rejected candidate
   query with the exact same input was guaranteed to reproduce the exact same
   rejected output -- wasted attempts and Groq quota for no chance of success.
   Fixed by feeding the retry what specifically failed (citation mismatch vs.
   value mismatch, and what the Critic found instead) and nudging toward a
   different node/angle within the same section, so each retry is a genuine
   second attempt.
   (2) **Cross-check numeric matching was too strict.** `values_match()`
   required the Generator's and Critic's answers to contain the exact same
   *count* of numbers, so a correct answer like "$100 million" failed against
   an equally correct "$100 million in 2025" purely because of an unrelated
   extra number (the year). Fixed by requiring only that every number in the
   Generator's answer appear (within tolerance) in the Critic's answer --
   extra numbers are permitted, not penalised. Considered and rejected an
   LLM-based semantic-similarity check as an alternative/addition (a third
   Groq call per attempt, ~50% more spend/latency, reintroduces
   non-determinism, and duplicates the Critic's own independent re-derivation
   -- the exact reasoning the spec already used to keep the Citation Audit
   code-only rather than Judge-graded). Instead added a third, complementary,
   still-deterministic gate: `bge-small-en-v1.5` embedding cosine similarity
   between the two answer texts (same model already used for P1/P3
   retrieval, local, free, no Groq call) above a threshold, to catch a
   Critic answer whose numbers happen to match by coincidence but whose
   surrounding text is otherwise unrelated. Numeric-subset matching was kept
   alongside embedding similarity (not replaced by it) because embeddings
   are unreliable at penalising a single wrong figure in an otherwise
   similarly-worded sentence (e.g. "$100 million" vs. "$150 million" score
   as highly similar) -- the three gates (citation overlap, numeric subset,
   embedding similarity) each catch a distinct failure mode none of the
   others cover.
- 2026-07-28: Embedding library substitution for the Doubt #4 cross-check
   fix above. `Architecture.md`'s Phase 5 package list names
   `sentence-transformers`/`FlagEmbedding` as the project's embedding path
   for `bge-small-en-v1.5`. Neither could be installed on this development
   machine: `torch` (a hard dependency of both) publishes no wheel for
   macOS x86_64 + Python 3.13 at any version -- confirmed live via
   `uv pip install torch --dry-run`, which fails on this exact venv
   (verified independently during code review, not just claimed by the
   implementer). Used `fastembed` (Qdrant's ONNX Runtime-based embedding
   library) instead, pinned with `onnxruntime==1.23.2`, loading the
   identical `BAAI/bge-small-en-v1.5` model weights -- same model, different
   loading library, verified via live reproduction of similarity scores
   during review. Lighter install footprint than `torch`+`sentence-transformers`
   would have been (~25MB of wheels vs. torch's much larger footprint).
   This only affects Phase 4's cross-check embedding use; Phase 5's actual
   P1 vector-store embedding path (not yet built) should re-evaluate this
   same platform constraint when it's implemented, since `Architecture.md`
   still names `sentence-transformers` there too.
- 2026-07-29: Added `tiktoken` as a new Phase 4 dependency, not listed in
   `Architecture.md`'s Phase 4 package line ("`groq`, `rank_bm25`
   (already introduced)"). Reason: fixed a real correctness gap (Doubt #8) --
   the Generator receives an entire filing section's concatenated content in
   one prompt, and a few real sections run large. The DB's existing
   `nodes.token_count` column is a plain whitespace word count
   (`len(stripped.split())` in `ingest/node_builder.py`), not a real
   tokenizer count, so it can't be trusted to guard against exceeding the
   Generator model's request limit. `tiktoken` gives an accurate local count
   (no Groq call) to check section size before sending, and to drive
   `chunk_section()`'s node-boundary splitting when a section exceeds
   `_MAX_SECTION_TOKENS` (60,000, chosen with headroom under `gpt-oss-120b`'s
   128K window). Live-verified the corpus's actual largest section is
   ~29,478 tokens -- comfortably under both the model's real limit and the
   new threshold, so this fix is precautionary today, not an active
   blocker, but a real gap worth closing since corpus size may grow.
   Pinned as a floor (`tiktoken>=0.12.0`), matching the project's dominant
   dependency-pinning style. Operational note: `cl100k_base`'s encoding
   table downloads over the network on first use (cached locally after) --
   not an issue in this environment, but would need pre-warming or a
   documented fallback in a fully offline/CI run.
- 2026-07-29: Swapped P3's summariser model from `llama-3.1-8b-instant` to
   `openai/gpt-oss-20b` (`config.MODEL_ROUTING["p3_index_build"]`). Reason:
   8B judged too small for reliable summary quality on dense financial
   filing sections -- a real quality concern, not a throughput one (8B was
   originally chosen purely for its high free-tier daily request ceiling,
   per `Budget.md`). Considered and rejected `Llama 3.3 70B` (would be the
   same model as the shared Answerer -- gives P3 alone an unfair "home
   advantage" reading its own writing style, a structural confound against
   P1/P2). Considered and rejected `Qwen3.6-27B` (viable but already reused
   for Critic and Judge -- more role overlap than necessary when a cleaner
   option exists). Considered switching provider entirely (Gemini,
   OpenRouter, SambaNova, Cerebras) -- rejected for now: Cerebras's "free
   tier" turned out to be a $5 trial credit, not perpetual free (corrected
   after an initial wrong claim); Gemini's per-minute request cap (~10 RPM)
   risks throttling this bursty per-filing build harder than Groq's TPD
   wall did; all three require a real client rewrite (`build_summary_index.py`
   calls `llama_index.llms.groq.Groq` directly, not a swappable wrapper) and
   a new live rate-limit verification pass, disproportionate to the problem
   being solved. `openai/gpt-oss-20b` needed no client change, no new
   Guardrails deviation beyond the model ID itself, and no role overlap.
   This requires a full 18-filing P3 rebuild (not just the 9 previously
   built on 8B) for cross-filing summarization consistency -- deleted the 9
   stale `storage/summary_index/` directories (already preserved in
   `project/backups/backup-20260729-100133/`) to force a clean rebuild.
   Also found and fixed a related gap while wiring this up:
   `data/filings_manifest.json` on this branch (`phase3-summary-index-build`)
   was still pinned to the original 9 filings; the JPM/JNJ/WMT entries only
   existed on the unmerged `corpus-expansion-3-companies` branch. Copied the
   18-filing manifest content directly rather than merging branches (per
   standing instruction not to merge/sync branches without being asked) --
   node data for all 18 filings was already present in `benchmark.db`
   regardless of git branch (it's gitignored, filesystem-level state).
- 2026-07-29: Changed the GQ (golden query) hand-labeling scheme in
   `golden_queries.human_score` from a 1-10 scale to **0-100**, and added
   loud, non-silent validation: `gq_label_import.parse_label_markdown()` now
   raises `ValueError` (naming the query_id and bad value) on a non-blank
   score that fails `int()`, instead of silently skipping the entry as
   before; `database_manager.update_golden_query_labels()` now raises
   `ValueError` if `human_score` isn't an integer in 0-100 (this is the
   single source of truth for the range check, matching where the schema's
   own `CHECK (human_score BETWEEN 0 AND 100)` constraint lives). This
   supersedes the original Doubt #10 finding ("no sanity check on the 1-10
   score -- '99' would be silently accepted"). Also added a new nullable
   schema column, `golden_queries.is_good INTEGER CHECK (is_good IS NULL OR
   is_good IN (0, 1))`, so the researcher can mark 10 of the 20 GQ as "good"
   exemplars and 10 as "bad" -- a genuinely new, human-filled dimension,
   deliberately **not derived from `human_score`** (a low/high numeric score
   and a "good/bad" exemplar-quality judgement are different questions).
   Left nullable (no placeholder value, no `NOT NULL`) since it has no
   legacy insert-time placeholder pattern to match, unlike `human_score`/
   `human_reasoning` (which get `1`/`"PENDING_HUMAN_LABEL"` from
   `run_dataset_generation.py`'s `_accept_query`, left unchanged -- still
   valid on the new 0-100 range). `gq_label_export.py`'s markdown template
   gained a `**Good Example (yes/no):**` line; `gq_label_import.py` parses
   it (blank -> `None`, "yes" -> `True`/1, "no" -> `False`/0, anything else
   non-blank -> `ValueError` naming the query_id, raised at parse time since
   it's a closed-vocabulary check). `update_golden_query_labels()` gained an
   `is_good: bool | None = None` parameter (default keeps all 3 existing
   call sites working). Explicit scope decision: `results.human_score` and
   `results.judge_score` (the Phase 6 JEQ human-vs-judge agreement gate,
   still 1-10, a different concept -- grading pipeline *answers*, not GQ
   *exemplars*) were deliberately left untouched, not conflated with this
   change. Open question, not resolved here: `Guardrails.md` §4a's Judge
   few-shot selection is purely quadrant-based (5 GQ per quadrant) and has
   not been redesigned to use the new `is_good` good/bad dimension --
   flagged in both `Architecture.md` and `Guardrails.md` for whoever builds
   Phase 6. `golden_queries` had zero real rows at the time of this change
   (verified live), so no data migration was needed. Updated:
   `project/database_manager.py`, `project/dataset_generation/gq_label_export.py`,
   `project/dataset_generation/gq_label_import.py`,
   `project/tests/test_gq_labeling.py`, `project/tests/test_database_manager.py`,
   `resources/specs/Architecture.md`, `resources/specs/Guardrails.md`.
- 2026-07-29: Two real bugs caught by `/code-review` on the 0-100/`is_good`
   change above, fixed before commit. (1) **Schema drift between code and
   the live database.** `database_manager._SCHEMA` uses
   `CREATE TABLE IF NOT EXISTS`, which never alters an already-existing
   table -- confirmed live: this repo's actual `project/benchmark.db` still
   had `golden_queries` under the *old* schema (`human_score BETWEEN 1 AND
   10`, no `is_good` column), because the table already existed when the
   schema source changed. The next real `gq_label_import.main()` run would
   have hit `sqlite3.OperationalError: no such column: is_good`. Fixed by
   adding `database_manager._migrate_golden_queries_schema()`, called from
   `init_db()`: detects a missing `is_good` column via `PRAGMA table_info`,
   and if the table is empty, drops and recreates it from the current
   `_SCHEMA`; if it holds real rows, raises `RuntimeError` instead of
   silently discarding them (SQLite can't `ALTER` an existing `CHECK`
   constraint, so fixing one requires recreating the table -- this refuses
   to do that blindly once real research data exists). Also ran this
   migration against the actual live `benchmark.db` (0 rows, migrated
   cleanly). (2) **Regex silently dropped entries missing the new field.**
   `gq_label_import.py`'s `_ENTRY_RE` hard-required the new
   `**Good Example (yes/no):**` line inside every entry; an entry from an
   older-format `golden_queries_to_label.md` (or one hand-edited to drop
   that line) simply failed to match at all, so `parse_label_markdown`
   silently returned `[]` for it and `main()` printed a false
   `"Imported 0 human labels"` success -- the exact silent-failure pattern
   Doubt #9/#10 were meant to eliminate. Fixed by making that line optional
   in the regex (`(?:...)?`), so a missing line now correctly yields
   `is_good: None` instead of dropping the whole entry. Both fixes covered
   by new regression tests (`test_init_db_migrates_stale_golden_queries_schema_when_empty`,
   `test_init_db_refuses_to_migrate_stale_golden_queries_schema_with_real_rows`,
   `test_parse_label_markdown_handles_entry_missing_good_example_line`).
- 2026-07-29: Shortened the `query_id` format `_accept_query()` constructs
   in `run_dataset_generation.py`, from `{full_quadrant}_{full_table}_{seq:04d}`
   (e.g. `Q1_Direct_Text_queries_0001`) to `{QT#}_{table_code}_{seq:03d}`
   (e.g. `QT1_PQ_001`). This closes Doubt #11 ("naming is clunky, IDs longer
   than necessary") plus a follow-up decision made after the user was asked:
   the quadrant labels `Q1`-`Q4` read as ambiguous against fiscal quarters
   in a project built entirely on SEC 10-K financial filings, so the new
   prefix is `QT` (Query Type) rather than reusing `Q` for quadrant. Two
   small module-level dicts do the mapping -- `_QUADRANT_TO_QT`
   (`Q1_Direct_Text`->`QT1`, `Q2_Implicit_Text`->`QT2`, `Q3_Direct_Table`->`QT3`,
   `Q4_Implicit_Table`->`QT4`) and `_TABLE_CODE` (`queries`->`PQ`,
   `golden_queries`->`GQ`, `judge_validation`->`JEQ`). Sequence padding
   dropped from 4 digits to 3, sized to the project's real fixed per-quadrant
   caps (25 PQ / 5 GQ / 5 JEQ per quadrant, i.e. 100/20/20 total per
   `Project Idea.md`), not an arbitrary round number. Explicit scope
   boundary, confirmed with the user before making this change: only the
   constructed `query_id` string changed. The `quadrant` column and its
   values (`Q1_Direct_Text` .. `Q4_Implicit_Table`), that column's `CHECK`
   constraint, the `_QUADRANT_GUIDANCE` prompt-guidance dict keys in
   `async_generator.py`, and "quadrant" terminology everywhere else in the
   codebase and docs are untouched. Also reconciled `Architecture.md`'s and
   `Project Idea.md`'s example `query_id` values (`Q3_017`, `Q2_044`,
   `G_Q4_03`, `V_Q1_02`, `Q4_087`), which never actually matched what the
   code produced in the first place -- a separate pre-existing doc/code
   mismatch, not introduced by this change -- to the new canonical format
   (`QT3_PQ_017`, `QT2_PQ_044`, `QT4_GQ_003`, `QT1_JEQ_002`, `QT4_PQ_087`).
   `queries`, `golden_queries`, and `judge_validation` all had zero real
   rows at the time of this change (verified live, same as the 0-100/`is_good`
   change above), so no data migration was needed. Updated:
   `project/dataset_generation/run_dataset_generation.py`,
   `project/tests/test_run_dataset_generation.py`,
   `resources/specs/Architecture.md`, `resources/specs/Project Idea.md`.
- 2026-07-29: Fixed Doubt #12 in the Critic's local search tool,
   `project/dataset_generation/search_tool.py`'s `search_filing_nodes()`.
   It scored nodes by raw query-term occurrence count with no length
   normalization, which biases toward long/wordy nodes over short precise
   ones -- a short node with a single exact hit could rank below a long
   node that happens to repeat a term several times across far more
   surrounding text. Fixed with plain length-normalized TF:
   `score = raw_count / len(node_tokens)` instead of `score = raw_count`,
   with a `not node_tokens: continue` guard so an empty-content node can't
   raise `ZeroDivisionError`. Considered and rejected adding IDF (i.e.
   real TF-IDF) or pulling in a library (`rank_bm25` or any TF-IDF
   package): this tool isn't just incidental plumbing -- the Critic uses
   it to independently re-derive an answer and verify Generator queries
   before they're accepted into `queries`/`golden_queries`/
   `judge_validation`. IDF is BM25's core differentiator, and P2's real
   benchmarked pipeline in Phase 5 *is* BM25 (`rank_bm25`); any resemblance
   between this verification tool's ranking and real BM25 scoring would
   mean queries whose evidence BM25-like scoring finds easily are more
   likely to survive into the dataset, an unearned advantage for P2 baked
   into the dataset's composition before the benchmark even runs. Plain
   length-normalized TF (no IDF, no library) fixes the actual bug without
   reintroducing that risk. Regression-tested with the concrete case that
   motivated the fix: a 7-token node with one "revenue" hit
   (score ~=0.143) now correctly outranks a 60-token node mentioning
   "revenue" five times (score ~=0.083) for the query "revenue" -- under
   the old raw-count scoring the 60-token node would have won 5-to-1.
   Updated: `project/dataset_generation/search_tool.py` (function +
   module docstring), `project/tests/test_search_tool.py`.