# Deferred Items Log

Every deliberate deferral made during planning/implementation — what was pushed to a later phase, why, and where the decision is recorded. Read this before writing any new implementation plan so a later phase doesn't silently re-decide or forget something already decided.

## Format

Each entry: **What** / **Deferred from → to** / **Why** / **Recorded in** / **Status**

---

## 1. P3 retrieval pipeline (`as_retriever(retriever_mode="embedding")`)

- **Deferred from → to:** Phase 3 → Phase 5
- **Why:** Phase 3 only builds and persists the summary tree (`TreeIndex`); actually querying it (retrieval) is a Phase 5 pipeline concern, per Architecture.md's own phase split.
- **Recorded in:** `docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md` ("Out of scope" section); pointer added in `resources/specs/Phase Plan.md` Phase 5, Goal 3.
- **Status:** Resolved in Phase 5. `project/pipelines/structural/p3_structural.py` retrieves through `index.as_retriever(retriever_mode="select_leaf_embedding")`, with a MockLLM bound so traversal cannot make a stray LLM call. P3 answered all 300 of its benchmark cells.

## 2. Full unthrottled ingestion (MSFT ×3, TSLA ×3 — 6 filings)

- **Deferred from → to:** Phase 2 → whenever full-corpus ingestion is triggered (before Phase 4 dataset generation needs the complete corpus)
- **Why:** `LOCAL_TEST_THROTTLE` capped the Phase 2 live run to 3 filings (all AAPL). Routine re-run once ready — flip `LOCAL_TEST_THROTTLE` to `false`, re-run `uv run python -m ingest.run_ingestion`. Not a design decision, just not yet executed.
- **Recorded in:** `temp/phase2-human-actions.md` ("Not yet needed" section).
- **Status:** Resolved 2026-07-22 (branch `full-corpus-ingestion`). All 9 filings then in `nodes`: AAPL 2023/2024/2025 (715/684/682), MSFT 2023/2024/2025 (1103/1234/1025), TSLA 2023/2024/2025 (1020/1028/1052) — 8,543 nodes total. 49/49 tests still passing.
- **Superseded 2026-08:** the corpus was later expanded to 13 filings by adding JPM and JNJ at FY2023-2024, giving 18,297 nodes. Recorded as `resources/research/deviations.md` entry 20; `project/data/filings_manifest.json` is the authoritative list. The counts above are the Phase 2 figures, kept as the record of what this item resolved, not as the current corpus.

## 3. Full migration off `llama_cloud_services` to the raw `llama-cloud` SDK

- **Deferred from → to:** Phase 2 → not scheduled to any phase; deliberately open-ended
- **Why:** `llama_cloud_services.LlamaParse` is a deprecated-but-working convenience wrapper; the "new unified SDK" (`llama-cloud` v2.11.0) is a raw low-level REST client with no equivalent wrapper — migrating means writing a real upload/poll/download loop. Not urgent since the current import still works.
- **Recorded in:** `temp/phase2-human-actions.md` ("Passive" section).
- **Status:** Open, and the trigger has now fired. `llama-cloud-services` 0.6.94 emits a deprecation warning on import stating the package is maintained only until **1 May 2026**, a date that has now passed. It still imports and works on the version pinned in `project/.venv`.
- **Impact on this project: none.** Ingestion finished well before that date, the corpus is frozen at 13 filings, and nothing in Phases 4 to 8 imports it — `ingest/parse_filing.py` is the only caller and it is not re-run. The migration is a maintenance concern for anyone re-ingesting a fresh corpus, not a constraint on the results.
- **If re-ingestion is ever needed:** stay on the pinned `llama-cloud-services==0.6.94`, which still works, or write the upload/poll/download loop against `llama-cloud>=1.0`.

## 4. Index build cost measured for P3 only, and only into a git-ignored log

- **Deferred from → to:** Phase 3 → Phase 8
- **Why:** `build_summary_index.py` logged its own wall clock and tokens to `logs/index_build_costs.json` because a rate-limited LLM build needed that record for retry accounting. P1 and P2 build locally in a single pass and were never instrumented, so there was nothing to compare against, and the Phase 8 efficiency pillar reported latency and tokens only.
- **Recorded in:** `resources/specs/Phase Plan.md` Phase 8, Goal 1 ("efficiency (latency, tokens, index-build cost)").
- **Status:** Resolved in Phase 8. `project/index_build_cost.py` reads P3's attempt log, measures P1 and P2 by rebuilding each into a scratch directory under timing, and writes both to `project/data/index_build_costs.json`, which is tracked rather than git-ignored. `aggregate_results.py` carries the block through `build_report()` and `build_report.py` renders it as Table 5.3.
