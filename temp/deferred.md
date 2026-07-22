# Deferred Items Log

Every deliberate deferral made during planning/implementation — what was pushed to a later phase, why, and where the decision is recorded. Read this before writing any new implementation plan so a later phase doesn't silently re-decide or forget something already decided.

## Format

Each entry: **What** / **Deferred from → to** / **Why** / **Recorded in** / **Status**

---

## 1. P3 retrieval pipeline (`as_retriever(retriever_mode="embedding")`)

- **Deferred from → to:** Phase 3 → Phase 5
- **Why:** Phase 3 only builds and persists the summary tree (`TreeIndex`); actually querying it (retrieval) is a Phase 5 pipeline concern, per Architecture.md's own phase split.
- **Recorded in:** `docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md` ("Out of scope" section); pointer added in `resources/specs/Phase Plan.md` Phase 5, Goal 3.
- **Status:** Open, expected — not a problem, just sequencing.

## 2. Full unthrottled ingestion (MSFT ×3, TSLA ×3 — 6 filings)

- **Deferred from → to:** Phase 2 → whenever full-corpus ingestion is triggered (before Phase 4 dataset generation needs the complete corpus)
- **Why:** `LOCAL_TEST_THROTTLE` capped the Phase 2 live run to 3 filings (all AAPL). Routine re-run once ready — flip `LOCAL_TEST_THROTTLE` to `false`, re-run `uv run python -m ingest.run_ingestion`. Not a design decision, just not yet executed.
- **Recorded in:** `temp/phase2-human-actions.md` ("Not yet needed" section).
- **Status:** Open, blocking Phase 4 if not done before then.

## 3. Full migration off `llama_cloud_services` to the raw `llama-cloud` SDK

- **Deferred from → to:** Phase 2 → not scheduled to any phase; deliberately open-ended
- **Why:** `llama_cloud_services.LlamaParse` is a deprecated-but-working convenience wrapper; the "new unified SDK" (`llama-cloud` v2.11.0) is a raw low-level REST client with no equivalent wrapper — migrating means writing a real upload/poll/download loop. Not urgent since the current import still works.
- **Recorded in:** `temp/phase2-human-actions.md` ("Passive" section).
- **Status:** Open, no deadline, revisit only if `llama_cloud_services` breaks or is removed.
