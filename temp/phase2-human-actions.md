# Phase 2 — Human Action Report

## Active — needs your input before Phase 2 is fully closed out

None remaining.

## Passive — already handled, no action needed unless you want to change it

- **`llama-parse` deprecation resolved (partially)**: you asked whether
  migrating would change behaviour. Checked directly (not guessed):
  `llama-parse`'s `LlamaParse` class is literally the same object as
  `llama_cloud_services`'s `LlamaParse` — `llama-parse` was just a thin
  import-path wrapper. Swapped `parse_filing.py`'s import to
  `llama_cloud_services` directly, removed `llama-parse` from
  dependencies (no longer even installed), added `llama-cloud-services`.
  Zero behaviour change, verified: 39/39 tests pass, live smoke test
  parses identically. One deeper layer remains deliberately unmigrated:
  `llama_cloud_services` itself points to a "new unified SDK" (`llama-cloud`
  v2.11.0), which is a raw, low-level REST API client with no convenience
  wrapper — migrating to it fully means writing your own upload/poll/
  download loop, a real rewrite. Not done; not urgent, since
  `llama_cloud_services` still works.
- **Parsing audit report reviewed**: you read `project/parsing_audit_report.md`
  and confirmed everything looks fine — the corpus is trusted for Phase 4.
- **Filing corpus confirmed**: AAPL, MSFT, TSLA × FY2023-2025 (9 filings) —
  you confirmed the spec's own illustrative default. Real ingestion for the
  throttled 3 (all AAPL) already ran successfully; the remaining 6 filings
  (MSFT × 3, TSLA × 3) haven't been fetched yet — that happens when
  `LOCAL_TEST_THROTTLE` is flipped to `false` and the full ingestion re-runs.
- **LlamaParse API key**: `project/.env` already had a real, working
  `LLAMA_CLOUD_API_KEY` — no setup needed from you this phase.
- **SEC EDGAR User-Agent**: auto-filled as `rag-techniques-benchmark
  ojaswiat@gmail.com` in `.env`/`.env.example` — change
  `SEC_EDGAR_USER_AGENT` if a different contact address should be on file
  with SEC.
- **Filing URLs were verified before spending real requests**: before the
  live run, all 9 manifest entries' CIKs and resolved 10-K URLs were printed
  and checked against known public facts (correct CIKs for Apple/Microsoft/
  Tesla, correct fiscal-year-end dates for each) — not just trusted blindly.
- **Two real bugs found and fixed during the live run** (both logged in
  `resources/artifacts/Changes.md` with full detail): (1) a deprecated
  LlamaParse constructor parameter, corrected to preserve the tool's tuned
  default parsing behaviour rather than silently degrading it; (2) a table
  misclassification bug (an exhibit-index table with no blank line before
  its rows was tagged `text` instead of `table`) — found via a real-data
  spot-check the plan was amended to require, fixed immediately, and
  covered by a new regression test. Neither ever bisected a table (the
  project's one hard invariant here) — both were metadata-tagging bugs,
  now fixed.
- **A cosmetic issue was found and deliberately NOT fixed**: 174 of 682
  AAPL_2025 nodes have a raw `#` character in their content (front-matter
  headings like `# FORM 10-K`, `# Apple Inc.` that aren't real "Item N"
  sections, so they're correctly left unattributed — but the markdown
  syntax itself isn't stripped). This doesn't corrupt anything Phase 4/5
  depend on (Item-header attribution, table integrity), so it was logged
  rather than chased down mid-phase. Fine to leave as-is.
- 48-hour parse caching is confirmed working — re-running ingestion for
  the same 3 filings hit the cache and spent $0 in additional LlamaParse
  credits.

## Not yet needed (deferred to their own phase)

- **P3 summary-index build** (Phase 3): needs the `nodes` table populated
  (it is, for 3 of 9 filings so far), nothing else new from you.
- **Full (unthrottled) ingestion of the remaining 6 filings**: needed
  before Phase 4's dataset generation can draw from the complete corpus.
  This is a routine re-run once you're ready (flip `LOCAL_TEST_THROTTLE` to
  `false` and re-run `uv run python -m ingest.run_ingestion`), not something
  requiring a new decision.
