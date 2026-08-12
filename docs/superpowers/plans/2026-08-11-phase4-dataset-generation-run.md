# Phase 4 Dataset Generation: Fix Corpus Scope + Throttled First Run

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `run_dataset_generation.py` draw from the real 13-filing corpus instead of a stale 9-filing hardcode, then execute a real, throttled first run to prove the fixed Generator/Critic pipeline actually fills `queries`/`golden_queries`/`judge_validation` end to end.

**Architecture:** `run_dataset_generation.py`'s `main()` builds two content pools (text, table) from every filing's nodes and fills 140 quadrant-balanced slots across three tables via a Generator→Critic→`check_query` adversarial loop. `_ALL_FILINGS` is the input filing list this pool-building step iterates over — currently a hardcoded tuple, not sourced from the manifest that every other Phase 2/3/5 script already treats as the single source of truth for corpus scope.

**Tech Stack:** Python 3.13, pytest + pytest-asyncio, `uv run` (project venv), Groq API (`openai/gpt-oss-120b` Generator, `qwen/qwen3.6-27b` Critic), `fastembed`/`bge-small-en-v1.5` for local cross-check embeddings, SQLite (`benchmark.db`).

## Global Constraints

- Corpus is fixed at the 13 filings in `data/filings_manifest.json` (deviations.md entry 20): AAPL/MSFT/TSLA × FY2023-2025, JPM/JNJ × FY2023-2024.
- `LOCAL_TEST_THROTTLE` (default `true`, `project/llm_client/config.py`) caps a run at `THROTTLE_LIMIT` (3) sections — every loop script must be run clean at throttle before a full unthrottled batch (Guardrails.md, CLAUDE.md §4).
- All LLM calls run at `temperature=0` (already enforced inside `generate_query`/`critique_query`'s client construction — not re-passed at call sites).
- `queries`/`golden_queries`/`judge_validation` must stay disjoint; `database_manager.get_all_query_texts()` already unions all three tables for the duplicate-question check, so no additional disjointness work is needed here.
- Groq's per-day token throughput (TPD), not request count, is the binding cost constraint (Budget.md) — `gpt-oss-120b` (Generator) ~200K TPD, `qwen/qwen3.6-27b` (Critic) ~8K TPM is the tight axis. A throttled run must complete cleanly before any unthrottled run is attempted.
- No dev-history/fix-narrative comments in code (CLAUDE.md) — comments explain only non-obvious WHY.

---

### Task 1: Derive `_ALL_FILINGS` from `data/filings_manifest.json`

**Files:**
- Modify: `project/dataset_generation/run_dataset_generation.py:218-222` (the `_ALL_FILINGS` constant definition)
- Test: `project/tests/test_run_dataset_generation.py` (add one new test near the existing `_ALL_FILINGS`-related tests around line 222)

**Interfaces:**
- Consumes: `data/filings_manifest.json` — a JSON array of objects, each with a `document_id` key (e.g. `{"document_id": "AAPL_2023", "ticker": "AAPL", "fiscal_year": 2023}`). Same file and same access pattern already used by `project/pipelines/bm25/build_bm25_index.py` (`MANIFEST_PATH = "data/filings_manifest.json"`, `with open(MANIFEST_PATH) as f: manifest = json.load(f)`, `entry["document_id"]`).
- Produces: `_ALL_FILINGS: tuple[str, ...]` — same name, same type, same call sites as before (`main()`'s `document_ids = _ALL_FILINGS if document_ids is None else document_ids`, and every existing test that reads `rdg._ALL_FILINGS` dynamically rather than hardcoding a count). No other module imports `_ALL_FILINGS`, so this is a self-contained change.

- [ ] **Step 1: Write the failing test**

Add this test to `project/tests/test_run_dataset_generation.py`, near the other `_ALL_FILINGS`-related tests (after `test_main_with_document_ids_none_defaults_to_all_filings`, around line 250):

```python
def test_all_filings_derived_from_manifest_includes_all_13_current_filings():
    """_ALL_FILINGS must track data/filings_manifest.json, not a stale
    hardcoded list -- a mismatch here silently excludes filings from
    every future Phase 4 run with no error or warning."""
    assert len(rdg._ALL_FILINGS) == 13
    assert "JPM_2023" in rdg._ALL_FILINGS
    assert "JPM_2024" in rdg._ALL_FILINGS
    assert "JNJ_2023" in rdg._ALL_FILINGS
    assert "JNJ_2024" in rdg._ALL_FILINGS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_dataset_generation.py::test_all_filings_derived_from_manifest_includes_all_13_current_filings -v`

Expected: FAIL — `assert len(rdg._ALL_FILINGS) == 13` fails because the current hardcoded tuple has 9 entries and contains no `JPM_*`/`JNJ_*` document_ids.

- [ ] **Step 3: Write minimal implementation**

In `project/dataset_generation/run_dataset_generation.py`, replace the current hardcoded block:

```python
_ALL_FILINGS = (
    "AAPL_2023", "AAPL_2024", "AAPL_2025",
    "MSFT_2023", "MSFT_2024", "MSFT_2025",
    "TSLA_2023", "TSLA_2024", "TSLA_2025",
)
```

with:

```python
MANIFEST_PATH = "data/filings_manifest.json"


def _load_all_filings() -> tuple[str, ...]:
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    return tuple(entry["document_id"] for entry in manifest)


_ALL_FILINGS = _load_all_filings()
```

`json` is already imported at the top of this file (line 31), so no new import is needed. Place this block at the same location the old `_ALL_FILINGS` tuple occupied (around line 218), preserving its position relative to `_INSERTER_NAMES` and the rest of the module-level constants below it.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_dataset_generation.py::test_all_filings_derived_from_manifest_includes_all_13_current_filings -v`

Expected: PASS.

- [ ] **Step 5: Run the full test file, then the full suite, to confirm no other test broke**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_dataset_generation.py -v`

Expected: all tests pass, including `test_main_with_document_ids_none_defaults_to_all_filings` (line 222, reads `rdg._ALL_FILINGS` dynamically so it adapts automatically) and `test_main_with_empty_document_ids_tuple_stays_empty_not_all_filings` (line 192, passes an explicit empty tuple and is unaffected by this change).

Then run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest -q`

Expected: `238 passed, 1 skipped` (237 prior + 1 new test).

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/dataset_generation/run_dataset_generation.py project/tests/test_run_dataset_generation.py
git commit -m "fix(phase4): derive _ALL_FILINGS from filings_manifest.json instead of a stale 9-filing hardcode"
```

---

### Task 2: Throttled real first run of Phase 4

**Files:**
- None created or modified — this task executes the now-fixed orchestrator against real Groq calls and the real `benchmark.db`, and verifies the result. No test file (this is an operational verification task, not a unit-testable code change).

**Interfaces:**
- Consumes: `run_dataset_generation.main()` (Task 1's fixed `_ALL_FILINGS`), `project/llm_client/config.py`'s `LOCAL_TEST_THROTTLE`/`THROTTLE_LIMIT`, real `GROQ_API_KEY` from `project/.env`.
- Produces: real rows in `benchmark.db`'s `queries`/`golden_queries`/`judge_validation` tables (kept — this is the actual start of the real dataset, not a throwaway smoke test), plus `logs/dataset_generation_summary.json` and `logs/dataset_generation_progress.log`.

- [ ] **Step 1: Confirm throttle is active before spending any quota**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -c "from llm_client import config; print('LOCAL_TEST_THROTTLE:', config.LOCAL_TEST_THROTTLE); print('THROTTLE_LIMIT:', config.THROTTLE_LIMIT)"`

Expected output: `LOCAL_TEST_THROTTLE: True` and `THROTTLE_LIMIT: 3`. If `LOCAL_TEST_THROTTLE` prints `False`, stop and set `LOCAL_TEST_THROTTLE=true` in `project/.env` before continuing — do not run an unthrottled Generator/Critic pass as the first-ever real run.

- [ ] **Step 2: Run the throttled orchestrator**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -m dataset_generation.run_dataset_generation 2>&1 | tee /tmp/phase4-throttled-run.log`

This makes real Groq calls (Generator + Critic, at most 3 sections' worth of generate/critique attempts under throttle) and writes accepted rows directly into `benchmark.db`. Expected: the process completes without an unhandled exception (per-attempt failures are caught and logged inside `_attempt_fill`, not raised) and prints a final `format_underfill_summary` table to stdout, e.g. `queries: Q1_Direct_Text 0/25, ...` (most slots will show 0/25 or similar since throttle caps total sections processed at 3 — underfill at this stage is expected and correct, not a failure).

- [ ] **Step 3: Verify at least one filing outside the old 9-filing hardcode was reachable**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -c "
import sqlite3
con = sqlite3.connect('benchmark.db')
for table in ('queries', 'golden_queries', 'judge_validation'):
    rows = con.execute(f'SELECT query_id, document_id FROM {table}').fetchall()
    print(table, rows)
"`

Expected: zero or more rows (throttle caps this run small, so an empty result on this particular throttled pass is acceptable — the pool-building step, not just the accept step, is what Task 1 fixed). Confirm no error is raised and no row has a `document_id` outside the 13-filing manifest.

- [ ] **Step 4: Inspect the run's structured logs for exceptions**

Run: `cat /Users/ojaswi/Projects/rag-techniques/project/logs/dataset_generation_summary.json`

Then, if it exists: `cat /Users/ojaswi/Projects/rag-techniques/project/logs/dataset_generation_failures.json`

Expected: `dataset_generation_summary.json` shows a valid `counts`/`summary` structure. If `dataset_generation_failures.json` exists and has entries, read each `exception_type`/`exception_message` — an occasional `EXCEPTION`/`REJECTED` outcome from the Generator/Critic loop is normal (this is the adversarial-verification design working as intended, not a bug), but any exception whose message references `AttributeError: 'function' object has no attribute` or `chat.completions.create` would indicate the LLMFactory/call-shape bugs fixed earlier this session have regressed — stop and re-investigate if seen.

- [ ] **Step 5: Report the outcome**

No commit for this task (no files changed) — report back: whether the run completed cleanly, how many rows landed in each table, and whether any exceptions were logged. This is the last gate before disabling `LOCAL_TEST_THROTTLE` for the full 140-query run (a separate, later decision — not part of this plan).

**Outcome (recorded after execution):** Task 2 ran and found a real, previously-undiscovered bug: `run_dataset_generation.py:38` imports `from groq import APIStatusError`, but the actual live call path (`LLMFactory` → LlamaIndex's `OpenAILike.achat()` → `openai.AsyncOpenAI`) raises `openai.APIStatusError` instead — a completely separate, non-subclassed exception class (verified empirically: `issubclass(groq.APIStatusError, openai.APIStatusError)` is `False`). `_ATTEMPT_EXCEPTIONS` (line 124) therefore never catches a real Groq rate-limit/status error, so a run crashes on the first genuine 4xx/5xx instead of logging it and moving to the next attempt like every other per-attempt failure. This is not the previously-fixed call-shape regression (no `AttributeError`/`chat.completions.create`-shaped message) — it is a distinct, newly-found bug. Task 3 below fixes it and re-runs Task 2's verification.

---

### Task 3: Fix `_ATTEMPT_EXCEPTIONS`'s wrong `APIStatusError` class, re-verify with a real throttled run

**Files:**
- Modify: `project/dataset_generation/run_dataset_generation.py:38` (the import) and `:124` (the `_ATTEMPT_EXCEPTIONS` tuple)
- Test: `project/tests/test_run_dataset_generation.py` (add one new test)

**Interfaces:**
- Consumes: `openai.APIStatusError` (already a transitive dependency via `llama-index-llms-openai`, no new package needed — confirmed present at `project/.venv/lib/python3.13/site-packages/openai/__init__.py`).
- Produces: `_ATTEMPT_EXCEPTIONS: tuple[type[Exception], ...]` — same name, same call site (`_attempt_fill`'s `except _ATTEMPT_EXCEPTIONS as exc:` at line 549), now correctly catching the exception class the real client actually raises.

- [ ] **Step 1: Write the failing test**

Add this test to `project/tests/test_run_dataset_generation.py`, near the other exception-handling tests (e.g. after `test_groq_api_status_error_is_caught_and_logged` around line 593):

```python
@pytest.mark.asyncio
async def test_openai_api_status_error_is_caught_and_logged(monkeypatch, tmp_path):
    """The real Groq call path raises openai.APIStatusError (via LlamaIndex's
    OpenAILike -> openai.AsyncOpenAI), not groq.APIStatusError -- a genuine
    rate-limit/status failure must be caught and logged like any other
    per-attempt failure, not crash the whole orchestrator."""
    import openai

    failure_log = tmp_path / "failures.json"
    monkeypatch.setattr(rdg, "FAILURE_LOG_PATH", failure_log)

    fake_response = httpx.Response(
        status_code=429,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        json={"error": {"message": "rate limited", "type": "tokens", "code": "rate_limit_exceeded"}},
    )
    api_error = openai.APIStatusError(
        message="rate limited", response=fake_response, body={"error": {"message": "rate limited"}}
    )

    async def fake_generate_query(section, quadrant, previous_attempt_feedback=None):
        raise api_error

    monkeypatch.setattr(rdg, "generate_query", fake_generate_query)

    section = {"document_id": "DOC_A", "section_header": "Item 1A", "node_ids": ["n1"], "content": "x"}
    counts = {table: {q: 0 for q in _QUADRANTS} for table in _TABLE_ORDER}

    result = await rdg._attempt_fill(
        "unused.db", section, "queries", "Q1_Direct_Text", [], counts, "DOC_A"
    )

    assert result is False
    logged = json.loads(failure_log.read_text())
    assert logged[-1]["exception_type"] == "APIStatusError"
    assert logged[-1]["document_id"] == "DOC_A"
```

This test needs `import httpx` and `import json` at the top of `test_run_dataset_generation.py` if not already present — check the existing imports first (the file already imports `json` for other tests; add `import httpx` only if missing, `httpx` is already a transitive dependency of `openai`).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_dataset_generation.py::test_openai_api_status_error_is_caught_and_logged -v`

Expected: FAIL — the real `openai.APIStatusError` propagates out of `_attempt_fill` uncaught (an unhandled exception in the test itself, not an assertion failure), because `_ATTEMPT_EXCEPTIONS` currently only names `groq.APIStatusError`.

- [ ] **Step 3: Write minimal implementation**

In `project/dataset_generation/run_dataset_generation.py`, change line 38 from:

```python
from groq import APIStatusError
```

to:

```python
from openai import APIStatusError
```

No other line needs to change — `_ATTEMPT_EXCEPTIONS` at line 124 already references the name `APIStatusError`; only the import's source module changes, so the class the tuple actually names becomes the one the real client raises.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_dataset_generation.py::test_openai_api_status_error_is_caught_and_logged -v`

Expected: PASS.

- [ ] **Step 5: Run the full test file, then the full suite**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_dataset_generation.py -v`

Expected: all tests pass, including the pre-existing `test_groq_api_status_error_is_caught_and_logged` (that test's mock must be checked — if it constructs a `groq.APIStatusError` instance directly to simulate the failure, it will now fail for the opposite reason the new test used to fail: the code no longer catches that class. If so, update that existing test's mock to raise `openai.APIStatusError` instead, matching what the real client actually raises — do not keep both a groq-shaped and openai-shaped test claiming to cover the same real code path with different, non-overlapping exception classes).

Then run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest -q`

Expected: `239 passed, 1 skipped` (238 prior + 1 new test; net zero change if the pre-existing groq-shaped test was converted rather than kept alongside).

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/dataset_generation/run_dataset_generation.py project/tests/test_run_dataset_generation.py
git commit -m "fix(phase4): catch openai.APIStatusError, the class the real Groq call path actually raises"
```

- [ ] **Step 7: Re-run Task 2's throttled dry run to confirm the fix holds against a real Groq rate limit**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -m dataset_generation.run_dataset_generation 2>&1 | tee /tmp/phase4-throttled-run-2.log`

Expected: the process completes without an unhandled exception this time (per-attempt failures, including any real rate-limit 4xx/5xx, are now caught and logged via `append_failure_log` instead of crashing), and prints a final `format_underfill_summary` table to stdout. Underfill (e.g. `0/25` or a small count) is still expected and correct under throttle — the goal here is "no crash," not "140/140 filled."

Then verify: `cd /Users/ojaswi/Projects/rag-techniques/project && cat logs/dataset_generation_summary.json` — its mtime should now be current (this run's timestamp, not a stale leftover), confirming `main()` reached its normal completion path this time.

No commit for this step (verification only, no files changed) — report the outcome: row counts, whether any exception referencing the old `AttributeError`/`chat.completions.create` regression appeared (should be none), and whether any exception referencing `openai.APIStatusError` was now caught-and-logged rather than crashing (if a rate limit is hit again, this confirms the fix; if no rate limit is hit this time, that's also fine — Groq's TPM window resets, so a repeat 413 isn't guaranteed on every run).

---

## Self-Review

**Spec coverage:** Both gaps identified in the second-order-thinking pass are covered — the corpus-scope bug (Task 1) and the "has this ever actually run against real data" unknown (Task 2). No other Phase 4 code changes are needed: the Generator/Critic call-shape bugs were already fixed in a prior session (deviations.md entries 21, and the async_critic tool-calling fix), and the disjointness/duplicate-detection logic already spans all three tables via `get_all_query_texts()`.

**Placeholder scan:** No TBD/TODO markers; both tasks specify exact file paths, exact code, and exact commands.

**Type consistency:** `_ALL_FILINGS` stays `tuple[str, ...]` before and after Task 1 — every existing caller (`main()`'s `document_ids` parameter, all `test_run_dataset_generation.py` tests that reference `rdg._ALL_FILINGS`) is unaffected by the internal implementation change.
