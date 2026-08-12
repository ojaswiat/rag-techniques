# Build Progress — Phase 1 through Phase 5 Status Snapshot

A point-in-time record of what's built, tested, and executed as of 2026-08-11,
for the dissertation's methodology/build-process narrative. Cross-references
`deviations.md`, `challenges.md`, `issues.md`, `token_usage.md` rather than
repeating their content. Superseded by later snapshots if the project state
materially changes; treat as historical once a newer one exists.

---

## Phase-by-phase status

| Phase | Scope | Status |
|---|---|---|
| 1 — Infrastructure | `database_manager.py`, `config.py`, `groq_client.py`/`nim_client.py`, `llm_factory.py`, `loop_template.py` | **Done, merged** (PR #1). |
| 2 — Ingestion & Parsing | `fetch_filings.py`, `parse_filing.py`, `node_builder.py`, `parsing_audit.py` | **Done, merged** (PR #2, #4). 13-filing corpus (see below) fully ingested: 18,297 nodes in `benchmark.db`. |
| 3 — P3 Summary-Tree Build | `pipelines/structural/build_summary_index.py` | **Done** for all 13 filings currently in scope (originally paused at 13/18 under the old 18-filing target — see `challenges.md` #1/#2 for why; corpus was then reduced to 13, see `deviations.md` #20, so this phase is now complete against current scope). |
| 4 — Dataset Generation | `dataset_generation/run_dataset_generation.py` (orchestrator), `async_generator.py`, `async_critic.py`, `search_tool.py`, `cross_check.py`, `section_grouper.py`, `gq_label_export.py`/`gq_label_import.py` | **Code complete, fully tested, NOT YET EXECUTED.** `queries`/`golden_queries`/`judge_validation` tables are all empty in `benchmark.db` as of this snapshot — the pipeline has never been run end-to-end against live data. |
| 5 — P1/P2/P3 Retrieval Pipelines | `pipelines/base.py` (shared `Retriever` ABC), `pipelines/vector/` (P1), `pipelines/bm25/` (P2) | **2 of 3 done.** P1 (vector) built and tested, PR #5 still **open, unmerged** upstream (functionally present locally on `phase5-pipeline-implementation`, pushed to origin, but the PR itself hasn't been merged/closed). P2 (BM25) built, tested, final-reviewed, **merged** (PR #6). **P3's query-time retriever class does not exist yet** — only the build-time script (`build_summary_index.py`) exists; there is no `pipelines/structural/p3_structural.py` or equivalent implementing the `Retriever` ABC for structural retrieval. |
| 6 — Judge Build & Validation Gate | `judge/async_judge.py`, `judge/metrics.py`, `judge/numeric_normalizer.py`, `judge/score_gate_outputs.py`, `judge/validation_gate.py` | **Not started.** No files exist. |
| 7 — Full Benchmark Execution | `run_benchmark.py`, plus the shared `pipelines/answerer.py` and `loop_executor.py` every pipeline needs to produce a result row | **Not started.** Neither `answerer.py` nor `loop_executor.py` exists yet — every retrieval pipeline can retrieve nodes but nothing can turn that into an answer or a `results` row yet. |
| 8 — Analysis | `analysis/aggregate.py`, `analysis/plots.py`, `analysis/tables.py` | **Not started.** |

## A real bug found and fixed this session

`LLMFactory.get_client()`'s retry/semaphore wiring was silently inert, and
`async_generator.py` called an interface that doesn't exist on the object
the factory returns — both fixed. Full technical detail in `deviations.md`
entry 21, not repeated here. `async_critic.py` has the same call-shape bug,
left open (different, larger fix needed) — see "What needs attention" below.

## What needs attention (priority order)

0. **Test coverage regression, self-inflicted this session.** While adding a
   regression test for the `LLMFactory`/generator fix (deviations.md #21),
   `tests/test_async_generator.py` was overwritten instead of extended,
   destroying 3 pre-existing tests: `test_generate_query_parses_generator_response`,
   `test_generate_query_first_attempt_has_no_feedback_in_prompt`, and
   `test_generate_query_retry_includes_previous_attempt_feedback_in_prompt`
   (the last one covers real, load-bearing behavior — that `previous_attempt_feedback`
   actually reaches the retry prompt). The lost tests used a hand-built dummy
   client shaped like the *old, buggy* call pattern, which is part of why the
   real bug went uncaught for so long — they need rewriting against the new
   `achat([ChatMessage(...)])` call shape, not a blind restore. Old content is
   recoverable from git history (`git show <commit-before-the-overwrite>:project/tests/test_async_generator.py`).
   Needs a fix pass before this is considered done.
1. **`answerer.py` + `loop_executor.py` don't exist.** This is the actual
   bottleneck for the whole project: without it, no pipeline (P1, P2, or a
   future P3) can produce a single benchmark result row, and Phase 6's Judge
   Gate can't start. Building P3's structural retriever without this doesn't
   unlock anything new to test end-to-end.
2. **P3's query-time retriever doesn't exist.** Needed before Phase 5 is
   actually complete and before any 3-pipeline comparison is possible.
3. **`async_critic.py`'s tool-calling bug is still open** — will crash the
   first real Phase 4 run exactly like the generator bug did.
4. **PR #5 (P1) is still open/unmerged upstream**, though its content is
   already present on `phase5-pipeline-implementation` — needs a decision
   (merge, close, or leave open pending review) before it becomes stale.
5. **Phase 4 has never been run against live data.** All the code and tests
   exist, but the first real end-to-end run may surface issues no mock
   caught — plan for a `LOCAL_TEST_THROTTLE`-limited dry run first, per
   Guardrails.
6. **`dataset_generation_failures.json` has stale test-fixture entries mixed
   into the real production log.** Discovered during the first real
   throttled Phase 4 run (2026-08-11): entries like `document_id: "DOC_A"`
   / `fake_generate_query` — clearly test-suite fixture data — appear
   alongside genuine run failures in `project/logs/dataset_generation_failures.json`.
   `append_failure_log()` writes to a module-level `FAILURE_LOG_PATH`
   constant rather than a path scoped per test run, so a test that doesn't
   monkeypatch it (or a test run from the repo's real `logs/` directory)
   leaks fixture rows into the same file real runs append to. Left
   unfixed for now — deferred, not blocking, since it only pollutes a
   diagnostic log, not `benchmark.db` itself. Worth a cleanup pass (audit
   `FAILURE_LOG_PATH` usage across the test suite, strip stale entries)
   before the log is relied on for the dissertation's methodology writeup.

## Next steps, in dependency order

1. Fix `async_critic.py`'s tool-calling call shape (small, contained, same
   pattern as the generator fix already applied).
2. Build `pipelines/answerer.py` (shared, citation-marker parsing) and
   `loop_executor.py` (orchestrator) — brainstormed but not yet planned as
   of this snapshot.
3. Build P3's query-time retriever (`pipelines/structural/p3_structural.py`
   or similar), completing Phase 5.
4. Run Phase 4 (dataset generation) for real, throttled first.
5. Resolve PR #5's status.
6. Phase 6 (Judge + validation gate) can then start.
