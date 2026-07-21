# Phase 2 — Ingestion & Parsing Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn ~6–9 raw SEC 10-K filings into a clean, metadata-rich `nodes` table — the canonical node store every later phase's metrics key off via `node_id`.

**Architecture:** A `data/filings_manifest.json` list drives four scripts in `project/ingest/`: `fetch_filings.py` resolves each filing's real URL from SEC EDGAR's public JSON APIs (never hardcoded/guessed URLs) and downloads it; `parse_filing.py` sends it to LlamaParse (Cost-effective tier, atomic-table mode) and caches the Markdown; `node_builder.py` splits that Markdown into atomic `TextNode`-shaped dicts (tables never bisected) and writes them via Phase 1's `database_manager.insert_node`; `parsing_audit.py` samples 20 sections across the corpus for a human accuracy check. Everything is cached aggressively (skip re-download, skip re-parse within 48h) and runs under Phase 1's `LOCAL_TEST_THROTTLE` pattern first.

**Tech Stack:** Python (`project/.venv`, `uv`), `llama-parse`, `requests`, Phase 1's `config.py` / `database_manager.py` / `groq_client.py` / `loop_template.py`.

## Global Constraints

- **Never bisect a table block.** A Markdown table is one atomic node — never split across two `TextNode`s (`resources/specs/Project Idea.md` §2, `Guardrails.md` §1).
- **`node_id` is the canonical evidence anchor**, format `{ticker}_{fiscal_year}_n{NNNN}` (4-digit zero-padded, per-document counter starting at `0001`) — every later phase's citation/metric logic keys off this, never off page numbers (`Project Idea.md` §2, `Architecture.md` §6 module table).
- **`source_page_num` is display-only, never a match key** — SEC filings are native HTML with no intrinsic pages, so this may be `NULL` (`Project Idea.md` §2).
- **`node_type` is `'text'` or `'table'`** — matches the CHECK constraint already in `database_manager.py`'s `nodes` table (Phase 1, `Architecture.md` §3.2).
- **LlamaParse: Cost-effective tier only**, atomic-table instructions, output Markdown — never Agentic/Premium tiers (15–30× more expensive, unnecessary here) (`Budget.md` §3, `Phase Plan.md` Phase 2 Goal 2).
- **Cache aggressively.** Re-parsing the same file within 48 hours costs 0 LlamaParse credits — skip re-parsing if a fresh cached copy exists (`Phase Plan.md` Phase 2 Goal 4, `Budget.md` §3).
- **Persist to SQLite immediately** — every parsed node is written to the `nodes` table via `database_manager.insert_node` as soon as it's built, not batched in memory (`Phase Plan.md` Phase 2 Goal 4).
- **Corpus scope: 2–3 companies × 2–3 fiscal years (~6–9 filings)**, retrieval stays per-document — never cross-corpus (`Architecture.md` §0).
- **No hardcoded/guessed filing URLs.** SEC EDGAR accession numbers and document paths must be resolved at runtime from SEC's own public JSON APIs (`data.sec.gov/submissions/CIK##########.json`), never invented or hand-typed — an invented accession number is indistinguishable from a real one until it 404s, which is a silent-failure risk this plan avoids by construction.
- **SEC EDGAR fair-access policy: identify yourself.** Every request must carry a descriptive `User-Agent` header (`"<project> <contact-email>"`) — SEC blocks/rate-limits anonymous or generic user agents.
- **`LOCAL_TEST_THROTTLE` applies here too** — run the full ingestion pipeline end-to-end on 3 filings first (`Guardrails.md` §7, reusing Phase 1's `project/loop_template.py`).
- **Packages this phase adds:** `llama-parse`, `requests` (`Architecture.md` §10 — `llama-index-core` is deferred to Phase 3/5 since Phase 2 doesn't need LlamaIndex's node/document classes, only LlamaParse's raw client).
- All code goes under `project/`; tests under `project/tests/`; all Python commands run via `uv run` from `project/`.
- British English in any prose/docs produced.

---

## Human Intervention Ledger (read this before starting)

- **[ACTIVE]** — Task 1, Step 1: confirm or edit the exact company/fiscal-year list in `data/filings_manifest.json`. The plan seeds it with the spec's own illustrative example (AAPL/MSFT/TSLA × FY2023–2025) since `Architecture.md` §11 explicitly flags this as still open — but this is a real research-design decision (which companies represent the corpus), not a technical one, so it must be confirmed or changed by the human before Task 2 fetches anything for real.
- **[ACTIVE]** — Task 3: a real `LLAMA_CLOUD_API_KEY` must exist in `project/.env` before the live parse smoke test can run (mirrors Phase 1 Task 5's Groq key gate).
- **[ACTIVE]** — Task 6: the full ingestion run (even throttled to 3 filings) needs SEC EDGAR to be reachable, a valid LlamaParse key, and the confirmed filing manifest all at once — this is the first point all three combine.
- **[PASSIVE]** — Task 2: the SEC EDGAR `User-Agent` header is auto-filled from the project name + the human's known contact email (`ojaswiat@gmail.com`) — no block, but flagged in case the human wants a different contact address on file with SEC.
- **[PASSIVE]** — Task 5's 20-section audit report is generated automatically, but the actual eyeballing of "does this look right" (per `Project Idea.md` §2's audit intent) is inherently a human judgement call — the script surfaces the sample, it cannot self-certify.

---

### Task 1: Filings manifest + Phase 2 dependencies

**Files:**
- Create: `project/data/filings_manifest.json`
- Modify: `project/pyproject.toml`
- Modify: `project/.env.example`
- Create: `project/tests/test_filings_manifest.py`

**Interfaces:**
- Consumes: nothing new (first task of this phase).
- Produces: `data/filings_manifest.json` — a JSON array of `{"document_id": str, "ticker": str, "fiscal_year": int}` objects. Task 2's `fetch_filings.py` reads this file by exact key names `document_id`, `ticker`, `fiscal_year` — do not rename.

- [ ] **Step 1: [ACTIVE — human input required] Confirm the filing corpus**

Ask the human:

> "Phase 2 needs a real list of SEC 10-K filings to ingest — `Architecture.md` §11 leaves this open, only giving AAPL/MSFT/TSLA × FY2023–2025 as an illustrative example. Should I use exactly that 9-filing set, a subset (2–3 companies × 2–3 years, per `Architecture.md` §0's corpus-size rule), or a different set of companies entirely? I need real tickers and real fiscal years — this becomes the entire evaluation corpus for the dissertation, so it's your call, not a technical default."

Do not proceed to Step 2 until the human confirms a specific list (or explicitly says "use the illustrative 9-filing default"). Record their answer in `data/filings_manifest.json` exactly as specified below, substituting the confirmed tickers/years for the illustrative ones if they differ.

- [ ] **Step 2: Write the manifest with the confirmed (or default) filing list**

Write `project/data/filings_manifest.json`:

```json
[
  {"document_id": "AAPL_2023", "ticker": "AAPL", "fiscal_year": 2023},
  {"document_id": "AAPL_2024", "ticker": "AAPL", "fiscal_year": 2024},
  {"document_id": "AAPL_2025", "ticker": "AAPL", "fiscal_year": 2025},
  {"document_id": "MSFT_2023", "ticker": "MSFT", "fiscal_year": 2023},
  {"document_id": "MSFT_2024", "ticker": "MSFT", "fiscal_year": 2024},
  {"document_id": "MSFT_2025", "ticker": "MSFT", "fiscal_year": 2025},
  {"document_id": "TSLA_2023", "ticker": "TSLA", "fiscal_year": 2023},
  {"document_id": "TSLA_2024", "ticker": "TSLA", "fiscal_year": 2024},
  {"document_id": "TSLA_2025", "ticker": "TSLA", "fiscal_year": 2025}
]
```

`document_id` format is `{ticker}_{fiscal_year}` — Task 2 uses this as the cache filename stem and Task 4 uses it as the `node_id` prefix.

- [ ] **Step 3: Write the failing manifest-shape test**

```python
# project/tests/test_filings_manifest.py
import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent.parent / "data" / "filings_manifest.json"


def test_manifest_exists_and_is_a_list():
    assert MANIFEST_PATH.exists()
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert isinstance(manifest, list)
    assert len(manifest) > 0


def test_every_entry_has_required_keys():
    manifest = json.loads(MANIFEST_PATH.read_text())
    for entry in manifest:
        assert set(entry.keys()) == {"document_id", "ticker", "fiscal_year"}
        assert entry["document_id"] == f"{entry['ticker']}_{entry['fiscal_year']}"


def test_document_ids_are_unique():
    manifest = json.loads(MANIFEST_PATH.read_text())
    ids = [entry["document_id"] for entry in manifest]
    assert len(ids) == len(set(ids))
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_filings_manifest.py -v`

Expected: FAIL with `assert False` on `MANIFEST_PATH.exists()` (file doesn't exist yet) — unless you did Step 2 first; if so, skip to Step 6. (This task's manifest content itself is data, not logic, so writing it before the test is acceptable here — same exception Phase 1 Task 1 used for `config.py`.)

- [ ] **Step 5: Confirm the manifest file exists (from Step 2)**

If not already done, write the file from Step 2 now.

- [ ] **Step 6: Add Phase 2 dependencies**

Run:
```bash
cd /Users/ojaswi/Projects/rag-techniques/project
uv add llama-parse requests
```

Expected: `pyproject.toml` gains `llama-parse` and `requests` in `[project.dependencies]`; `uv.lock` updates.

- [ ] **Step 7: Add LlamaParse + SEC EDGAR settings to `.env.example`**

Edit `project/.env.example`, adding after the existing `LLAMA_CLOUD_API_KEY` line (which already exists from Phase 1 — do not duplicate it, just confirm it's there):

```bash
# SEC EDGAR requires a descriptive User-Agent for automated access (fair-access
# policy) - format: "<project name> <contact email>". No account/key needed,
# this is just an identifying string SEC asks every automated requester to send.
SEC_EDGAR_USER_AGENT=rag-techniques-benchmark ojaswiat@gmail.com
```

- [ ] **Step 8: Run tests, confirm they pass**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_filings_manifest.py -v`

Expected: `3 passed`

- [ ] **Step 9: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add data/filings_manifest.json pyproject.toml uv.lock .env.example tests/test_filings_manifest.py
git commit -m "feat: add Phase 2 dependencies and the confirmed filings manifest"
```

---

### Task 2: `ingest/fetch_filings.py` — download filings from SEC EDGAR

**Files:**
- Create: `project/ingest/__init__.py`
- Create: `project/ingest/fetch_filings.py`
- Create: `project/tests/test_fetch_filings.py`

**Interfaces:**
- Consumes: `config.py` (Phase 1) for `SEC_EDGAR_USER_AGENT`; `data/filings_manifest.json` (Task 1) for `{document_id, ticker, fiscal_year}`.
- Produces: `async def fetch_filing(ticker: str, fiscal_year: int, document_id: str, raw_dir: str = "data/raw") -> str` — returns the path to the cached raw HTML file. Task 3's `parse_filing.py` calls this exact signature.
- Produces: `def resolve_cik(ticker: str) -> str` — used internally, but Task 6's verification script may call it directly to sanity-check a ticker resolves.

- [ ] **Step 1: Add `SEC_EDGAR_USER_AGENT` to `config.py`**

Edit `project/config.py`, adding after the `LLAMA_CLOUD_API_KEY` line:

```python
SEC_EDGAR_USER_AGENT: str = os.getenv("SEC_EDGAR_USER_AGENT", "rag-techniques-benchmark unknown@example.com")
```

- [ ] **Step 2: Write the failing test (mocked HTTP, no real network)**

```python
# project/tests/test_fetch_filings.py
import json
import os
from unittest.mock import MagicMock, patch

import pytest

import fetch_filings_test_fixtures as _unused  # placeholder import removed below
```

Replace the above placeholder entirely with the real test file:

```python
# project/tests/test_fetch_filings.py
import os
from unittest.mock import MagicMock, patch

import pytest

import ingest.fetch_filings as fetch_filings

FAKE_TICKERS_JSON = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
}

FAKE_SUBMISSIONS_JSON = {
    "filings": {
        "recent": {
            "form": ["10-K", "8-K", "10-K"],
            "reportDate": ["2025-09-28", "2025-06-01", "2024-09-30"],
            "accessionNumber": ["0000320193-25-000010", "0000320193-25-000005", "0000320193-24-000010"],
            "primaryDocument": ["aapl-20250928.htm", "aapl-8k.htm", "aapl-20240930.htm"],
        }
    }
}


def test_resolve_cik_finds_ticker():
    with patch.object(fetch_filings, "_get_json", return_value=FAKE_TICKERS_JSON) as mock_get:
        cik = fetch_filings.resolve_cik("AAPL")
    assert cik == "0000320193"
    mock_get.assert_called_once()


def test_resolve_cik_raises_for_unknown_ticker():
    with patch.object(fetch_filings, "_get_json", return_value=FAKE_TICKERS_JSON):
        with pytest.raises(ValueError, match="no CIK found for ticker"):
            fetch_filings.resolve_cik("NOPE")


@pytest.mark.asyncio
async def test_fetch_filing_downloads_and_caches(tmp_path):
    raw_dir = str(tmp_path)
    fake_html = b"<html>fake 10-K content</html>"

    with patch.object(fetch_filings, "resolve_cik", return_value="0000320193"), \
         patch.object(fetch_filings, "_get_json", return_value=FAKE_SUBMISSIONS_JSON), \
         patch.object(fetch_filings, "_download_bytes", return_value=fake_html) as mock_download:
        path = await fetch_filings.fetch_filing("AAPL", 2025, "AAPL_2025", raw_dir=raw_dir)

    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == fake_html
    mock_download.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_filing_skips_download_if_cached(tmp_path):
    raw_dir = str(tmp_path)
    cached_path = os.path.join(raw_dir, "AAPL_2025.html")
    with open(cached_path, "wb") as f:
        f.write(b"already cached")

    with patch.object(fetch_filings, "resolve_cik") as mock_resolve, \
         patch.object(fetch_filings, "_download_bytes") as mock_download:
        path = await fetch_filings.fetch_filing("AAPL", 2025, "AAPL_2025", raw_dir=raw_dir)

    assert path == cached_path
    mock_resolve.assert_not_called()
    mock_download.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_filing_raises_when_no_matching_10k(tmp_path):
    raw_dir = str(tmp_path)
    empty_submissions = {"filings": {"recent": {"form": [], "reportDate": [], "accessionNumber": [], "primaryDocument": []}}}
    with patch.object(fetch_filings, "resolve_cik", return_value="0000320193"), \
         patch.object(fetch_filings, "_get_json", return_value=empty_submissions):
        with pytest.raises(ValueError, match="no 10-K found"):
            await fetch_filings.fetch_filing("AAPL", 2025, "AAPL_2025", raw_dir=raw_dir)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_fetch_filings.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'ingest'` (or `'ingest.fetch_filings'`)

- [ ] **Step 4: Write `ingest/__init__.py`**

```python
# project/ingest/__init__.py
```

(empty — makes `ingest` a package so `import ingest.fetch_filings` works)

- [ ] **Step 5: Write `ingest/fetch_filings.py`**

```python
"""Downloads SEC 10-K filings, resolving real URLs from SEC EDGAR's public
JSON APIs at runtime -- never hardcoded accession numbers or document paths.

See resources/specs/Architecture.md §0.3 and the Global Constraints in this
phase's plan: SEC EDGAR requires a descriptive User-Agent (fair-access
policy) and this module must never guess a filing's URL.
"""
import os

import requests

import config

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{accession_no_dashes}/{primary_document}"


def _headers() -> dict:
    return {"User-Agent": config.SEC_EDGAR_USER_AGENT}


def _get_json(url: str) -> dict:
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def _download_bytes(url: str) -> bytes:
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.content


def resolve_cik(ticker: str) -> str:
    tickers = _get_json(_TICKERS_URL)
    for entry in tickers.values():
        if entry["ticker"].upper() == ticker.upper():
            return f"{entry['cik_str']:010d}"
    raise ValueError(f"no CIK found for ticker {ticker!r}")


async def fetch_filing(ticker: str, fiscal_year: int, document_id: str, raw_dir: str = "data/raw") -> str:
    os.makedirs(raw_dir, exist_ok=True)
    cached_path = os.path.join(raw_dir, f"{document_id}.html")
    if os.path.exists(cached_path):
        return cached_path

    cik = resolve_cik(ticker)
    submissions = _get_json(_SUBMISSIONS_URL.format(cik=cik))
    recent = submissions["filings"]["recent"]

    for form, report_date, accession, primary_doc in zip(
        recent["form"], recent["reportDate"], recent["accessionNumber"], recent["primaryDocument"]
    ):
        if form == "10-K" and report_date.startswith(str(fiscal_year)):
            accession_no_dashes = accession.replace("-", "")
            cik_no_zeros = str(int(cik))
            url = _ARCHIVE_URL.format(
                cik_no_zeros=cik_no_zeros,
                accession_no_dashes=accession_no_dashes,
                primary_document=primary_doc,
            )
            content = _download_bytes(url)
            with open(cached_path, "wb") as f:
                f.write(content)
            return cached_path

    raise ValueError(f"no 10-K found for {ticker} fiscal year {fiscal_year}")
```

- [ ] **Step 6: Run tests, confirm they pass**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_fetch_filings.py -v`

Expected: `5 passed`

- [ ] **Step 7: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add ingest/__init__.py ingest/fetch_filings.py tests/test_fetch_filings.py config.py
git commit -m "feat: add SEC EDGAR filing fetcher with runtime URL resolution and caching"
```

---

### Task 3: `ingest/parse_filing.py` — LlamaParse atomic-table parsing

**Files:**
- Create: `project/ingest/parse_filing.py`
- Create: `project/tests/test_parse_filing.py`

**Interfaces:**
- Consumes: `config.LLAMA_CLOUD_API_KEY` (Phase 1); the raw HTML path returned by Task 2's `fetch_filing`.
- Produces: `async def parse_filing(document_id: str, raw_path: str, parsed_dir: str = "data/parsed") -> str` — returns the path to the cached parsed Markdown file. Task 4's `node_builder.py` reads this file's contents.

- [ ] **Step 1: Write the failing test (mocked LlamaParse client, no real network/API key needed)**

```python
# project/tests/test_parse_filing.py
import os
import time
from unittest.mock import AsyncMock, patch

import pytest

import ingest.parse_filing as parse_filing


@pytest.mark.asyncio
async def test_parse_filing_calls_llamaparse_and_caches(tmp_path):
    raw_path = tmp_path / "AAPL_2025.html"
    raw_path.write_text("<html>fake filing</html>")
    parsed_dir = str(tmp_path / "parsed")

    with patch.object(
        parse_filing, "_parser"
    ) as mock_parser:
        mock_parser.aload_data = AsyncMock(return_value=[
            type("Doc", (), {"text": "# Item 1A. Risk Factors\n\nSome risk text."})()
        ])
        result_path = await parse_filing.parse_filing("AAPL_2025", str(raw_path), parsed_dir=parsed_dir)

    assert os.path.exists(result_path)
    with open(result_path) as f:
        assert "Item 1A" in f.read()
    mock_parser.aload_data.assert_called_once()


@pytest.mark.asyncio
async def test_parse_filing_skips_reparse_within_48h(tmp_path):
    raw_path = tmp_path / "AAPL_2025.html"
    raw_path.write_text("<html>fake filing</html>")
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    cached_md = parsed_dir / "AAPL_2025.md"
    cached_md.write_text("already parsed")

    with patch.object(parse_filing, "_parser") as mock_parser:
        mock_parser.aload_data = AsyncMock()
        result_path = await parse_filing.parse_filing("AAPL_2025", str(raw_path), parsed_dir=str(parsed_dir))

    assert result_path == str(cached_md)
    mock_parser.aload_data.assert_not_called()


@pytest.mark.asyncio
async def test_parse_filing_reparses_if_cache_older_than_48h(tmp_path):
    raw_path = tmp_path / "AAPL_2025.html"
    raw_path.write_text("<html>fake filing</html>")
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    cached_md = parsed_dir / "AAPL_2025.md"
    cached_md.write_text("stale parse")
    stale_time = time.time() - (49 * 3600)
    os.utime(cached_md, (stale_time, stale_time))

    with patch.object(parse_filing, "_parser") as mock_parser:
        mock_parser.aload_data = AsyncMock(return_value=[
            type("Doc", (), {"text": "fresh content"})()
        ])
        result_path = await parse_filing.parse_filing("AAPL_2025", str(raw_path), parsed_dir=str(parsed_dir))

    with open(result_path) as f:
        assert f.read() == "fresh content"
    mock_parser.aload_data.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_parse_filing.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'ingest.parse_filing'`

- [ ] **Step 3: Write `ingest/parse_filing.py`**

```python
"""Parses raw filings into clean Markdown via LlamaParse (Cost-effective
tier, atomic-table mode). Caches aggressively: re-parsing the same file
within 48 hours is free on LlamaParse's side, but we still skip the network
call entirely when a fresh cached copy already exists.

See resources/specs/Budget.md §3 and this phase's plan Global Constraints:
Cost-effective tier only, never Agentic/Premium.
"""
import os
import time

from llama_parse import LlamaParse

import config

_CACHE_FRESH_SECONDS = 48 * 3600

_parser = LlamaParse(
    api_key=config.LLAMA_CLOUD_API_KEY or "placeholder-key-for-import-only",
    result_type="markdown",
    parsing_instruction=(
        "This is a SEC 10-K filing. Extract all tables as clean, complete "
        "Markdown tables -- never split or truncate a table across multiple "
        "chunks. Preserve section headers (e.g. 'Item 1A. Risk Factors') as "
        "Markdown headings."
    ),
)


def _is_cache_fresh(path: str) -> bool:
    if not os.path.exists(path):
        return False
    age = time.time() - os.path.getmtime(path)
    return age < _CACHE_FRESH_SECONDS


async def parse_filing(document_id: str, raw_path: str, parsed_dir: str = "data/parsed") -> str:
    os.makedirs(parsed_dir, exist_ok=True)
    cached_path = os.path.join(parsed_dir, f"{document_id}.md")

    if _is_cache_fresh(cached_path):
        return cached_path

    documents = await _parser.aload_data(raw_path)
    markdown_text = "\n\n".join(doc.text for doc in documents)

    with open(cached_path, "w") as f:
        f.write(markdown_text)

    return cached_path
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_parse_filing.py -v`

Expected: `3 passed`

- [ ] **Step 5: [ACTIVE — human input required] Confirm `LLAMA_CLOUD_API_KEY` is real**

Ask the human (skip if `project/.env` already has a working key — check first, same pattern as Phase 1 Task 5):

> "Phase 2's live parse smoke test needs a real LlamaParse API key in `project/.env` as `LLAMA_CLOUD_API_KEY`. Get one free at https://cloud.llamaindex.ai/api-key (sign in with Google/GitHub/email, no card needed for Cost-effective tier), then paste it into `project/.env`. Let me know when it's there, or tell me to skip the live check."

- [ ] **Step 6: Live smoke test (only after Step 5's key is confirmed)**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -c "
import asyncio, ingest.parse_filing as pf
async def main():
    with open('/tmp/smoke_filing.html', 'w') as f:
        f.write('<html><body><h1>Item 1A. Risk Factors</h1><p>Test risk paragraph.</p></body></html>')
    path = await pf.parse_filing('SMOKE_TEST', '/tmp/smoke_filing.html', parsed_dir='/tmp/smoke_parsed')
    print('parsed to:', path)
    with open(path) as fh:
        print(fh.read()[:300])
asyncio.run(main())
"`

Expected: prints a path and Markdown content containing recognizable text from the test HTML — confirms the real LlamaParse API accepts calls with the configured key and settings.

- [ ] **Step 7: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add ingest/parse_filing.py tests/test_parse_filing.py
git commit -m "feat: add LlamaParse-based filing parser with 48h cache freshness check"
```

---

### Task 4: `ingest/node_builder.py` — Markdown → atomic nodes

**Files:**
- Create: `project/ingest/node_builder.py`
- Create: `project/tests/test_node_builder.py`

**Interfaces:**
- Consumes: the Markdown text produced by Task 3's `parse_filing`; `database_manager.insert_node` (Phase 1) to persist.
- Produces: `def build_nodes(document_id: str, ticker: str, fiscal_year: int, markdown_text: str) -> list[dict]` — each dict has exactly the keys `database_manager.insert_node` expects: `node_id`, `document_id`, `parent_item_header`, `node_type`, `source_page_num`, `content`, `token_count`. Task 5's audit script and Task 6's verification both rely on this exact key set.

- [ ] **Step 1: Write the failing test**

```python
# project/tests/test_node_builder.py
import ingest.node_builder as node_builder

SAMPLE_MARKDOWN = """# Item 1A. Risk Factors

Our business faces intense competition from other companies.

Weather conditions could adversely affect our operations.

# Item 8. Financial Statements

| Year | Net Sales |
|------|-----------|
| 2025 | 394328    |
| 2024 | 383285    |

Some closing narrative after the table.
"""


def test_build_nodes_returns_correct_keys():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    assert len(nodes) > 0
    expected_keys = {"node_id", "document_id", "parent_item_header", "node_type", "source_page_num", "content", "token_count"}
    for node in nodes:
        assert set(node.keys()) == expected_keys


def test_build_nodes_assigns_sequential_node_ids():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    ids = [n["node_id"] for n in nodes]
    assert ids[0] == "AAPL_2025_n0001"
    assert ids[1] == "AAPL_2025_n0002"
    assert ids == sorted(ids)


def test_build_nodes_tracks_parent_item_header():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    risk_nodes = [n for n in nodes if "competition" in n["content"]]
    assert len(risk_nodes) == 1
    assert risk_nodes[0]["parent_item_header"] == "Item 1A. Risk Factors"

    financial_nodes = [n for n in nodes if "closing narrative" in n["content"]]
    assert len(financial_nodes) == 1
    assert financial_nodes[0]["parent_item_header"] == "Item 8. Financial Statements"


def test_build_nodes_keeps_table_atomic():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    table_nodes = [n for n in nodes if n["node_type"] == "table"]
    assert len(table_nodes) == 1
    assert "394328" in table_nodes[0]["content"]
    assert "383285" in table_nodes[0]["content"]
    assert "Year" in table_nodes[0]["content"]


def test_build_nodes_classifies_text_vs_table():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    types = {n["node_type"] for n in nodes}
    assert types == {"text", "table"}


def test_build_nodes_document_id_and_page_num():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    for node in nodes:
        assert node["document_id"] == "AAPL_2025"
        assert node["source_page_num"] is None


def test_build_nodes_token_count_is_positive():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    for node in nodes:
        assert node["token_count"] > 0
        assert node["token_count"] == len(node["content"].split())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_node_builder.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'ingest.node_builder'`

- [ ] **Step 3: Write `ingest/node_builder.py`**

```python
"""Splits parsed Markdown into atomic TextNode-shaped dicts.

A Markdown table is one atomic node -- never bisected. Section headers
("Item 1A. Risk Factors") are tracked and attached to every node that
follows until the next header, per resources/specs/Project Idea.md §2.

source_page_num is always None: SEC filings are native HTML with no
intrinsic pages (Project Idea.md §2) -- this is a display-only field with
nothing reliable to populate it from at this stage.
"""
import re

_HEADER_RE = re.compile(r"^#{1,3}\s*(Item\s+\d+[A-Za-z]?\.?\s*.+?)\s*$", re.IGNORECASE)


def _is_table_block(block: str) -> bool:
    lines = [line for line in block.splitlines() if line.strip()]
    if not lines:
        return False
    return lines[0].strip().startswith("|")


def build_nodes(document_id: str, ticker: str, fiscal_year: int, markdown_text: str) -> list[dict]:
    blocks = [b for b in markdown_text.split("\n\n") if b.strip()]

    nodes = []
    current_header = None
    counter = 1

    for block in blocks:
        stripped = block.strip()
        header_match = _HEADER_RE.match(stripped)
        if header_match:
            current_header = header_match.group(1).strip()
            continue

        node_type = "table" if _is_table_block(stripped) else "text"
        node_id = f"{document_id}_n{counter:04d}"
        nodes.append({
            "node_id": node_id,
            "document_id": document_id,
            "parent_item_header": current_header,
            "node_type": node_type,
            "source_page_num": None,
            "content": stripped,
            "token_count": len(stripped.split()),
        })
        counter += 1

    return nodes
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_node_builder.py -v`

Expected: `7 passed`

- [ ] **Step 5: Wire node persistence — write `ingest/run_ingestion.py`**

This is the orchestration script that ties Tasks 2–4 together and writes to SQLite.

```python
# project/ingest/run_ingestion.py
"""Orchestrates fetch -> parse -> node_builder -> database_manager.insert_node
for every filing in data/filings_manifest.json, honoring LOCAL_TEST_THROTTLE.
"""
import asyncio
import json

import database_manager as dbm
import loop_template
from ingest.fetch_filings import fetch_filing
from ingest.node_builder import build_nodes
from ingest.parse_filing import parse_filing

DB_PATH = "benchmark.db"
MANIFEST_PATH = "data/filings_manifest.json"


async def ingest_one(entry: dict) -> int:
    raw_path = await fetch_filing(entry["ticker"], entry["fiscal_year"], entry["document_id"])
    parsed_path = await parse_filing(entry["document_id"], raw_path)
    with open(parsed_path) as f:
        markdown_text = f.read()
    nodes = build_nodes(entry["document_id"], entry["ticker"], entry["fiscal_year"], markdown_text)
    for node in nodes:
        await dbm.insert_node(DB_PATH, node)
    return len(nodes)


async def main():
    await dbm.init_db(DB_PATH)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    manifest = loop_template.apply_throttle(manifest)

    for entry in manifest:
        count = await ingest_one(entry)
        print(f"{entry['document_id']}: {count} nodes")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 6: Write the failing orchestration test**

```python
# project/tests/test_run_ingestion.py
from unittest.mock import AsyncMock, patch

import pytest

import ingest.run_ingestion as run_ingestion


@pytest.mark.asyncio
async def test_ingest_one_calls_fetch_parse_build_and_insert(tmp_path):
    entry = {"document_id": "AAPL_2025", "ticker": "AAPL", "fiscal_year": 2025}

    with patch.object(run_ingestion, "fetch_filing", new=AsyncMock(return_value="/tmp/fake.html")), \
         patch.object(run_ingestion, "parse_filing", new=AsyncMock(return_value="/tmp/fake.md")), \
         patch("builtins.open", create=True) as mock_open, \
         patch.object(run_ingestion, "build_nodes", return_value=[
             {"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025", "parent_item_header": None,
              "node_type": "text", "source_page_num": None, "content": "x", "token_count": 1}
         ]) as mock_build, \
         patch.object(run_ingestion.dbm, "insert_node", new=AsyncMock()) as mock_insert:
        mock_open.return_value.__enter__.return_value.read.return_value = "markdown content"
        count = await run_ingestion.ingest_one(entry)

    assert count == 1
    mock_build.assert_called_once_with("AAPL_2025", "AAPL", 2025, "markdown content")
    mock_insert.assert_called_once()
```

- [ ] **Step 7: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_ingestion.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'ingest.run_ingestion'`

- [ ] **Step 8: Run tests, confirm they pass**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_run_ingestion.py -v`

Expected: `1 passed`

- [ ] **Step 9: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add ingest/node_builder.py ingest/run_ingestion.py tests/test_node_builder.py tests/test_run_ingestion.py
git commit -m "feat: add node_builder (atomic table splitting) and ingestion orchestration script"
```

---

### Task 5: `ingest/parsing_audit.py` — 20-section validation sample

**Files:**
- Create: `project/ingest/parsing_audit.py`
- Create: `project/tests/test_parsing_audit.py`

**Interfaces:**
- Consumes: `database_manager` (Phase 1) to read the populated `nodes` table.
- Produces: `async def sample_sections(db_path: str, n: int = 20) -> list[dict]` — returns `n` randomly sampled node rows (or fewer, if the corpus has fewer than `n` nodes) for human review. `def write_audit_report(samples: list[dict], out_path: str) -> None` writes a Markdown report.

- [ ] **Step 1: Write the failing test**

```python
# project/tests/test_parsing_audit.py
import pytest

import database_manager as dbm
import ingest.parsing_audit as parsing_audit

TEST_DB = "test_audit.db"


@pytest.fixture(autouse=True)
def clean_db():
    import os
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(TEST_DB + suffix):
            os.remove(TEST_DB + suffix)
    yield
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(TEST_DB + suffix):
            os.remove(TEST_DB + suffix)


@pytest.mark.asyncio
async def test_sample_sections_returns_at_most_n():
    await dbm.init_db(TEST_DB)
    for i in range(5):
        await dbm.insert_node(TEST_DB, {
            "node_id": f"TEST_2025_n{i:04d}", "document_id": "TEST_2025",
            "parent_item_header": "Item 1A", "node_type": "text",
            "source_page_num": None, "content": f"content {i}", "token_count": 2,
        })
    samples = await parsing_audit.sample_sections(TEST_DB, n=20)
    assert len(samples) == 5


@pytest.mark.asyncio
async def test_sample_sections_caps_at_n():
    await dbm.init_db(TEST_DB)
    for i in range(30):
        await dbm.insert_node(TEST_DB, {
            "node_id": f"TEST_2025_n{i:04d}", "document_id": "TEST_2025",
            "parent_item_header": "Item 1A", "node_type": "text",
            "source_page_num": None, "content": f"content {i}", "token_count": 2,
        })
    samples = await parsing_audit.sample_sections(TEST_DB, n=20)
    assert len(samples) == 20


def test_write_audit_report_creates_readable_markdown(tmp_path):
    samples = [
        {"node_id": "TEST_2025_n0001", "document_id": "TEST_2025", "parent_item_header": "Item 1A",
         "node_type": "text", "content": "Sample risk text.", "token_count": 3},
    ]
    out_path = str(tmp_path / "audit_report.md")
    parsing_audit.write_audit_report(samples, out_path)

    with open(out_path) as f:
        text = f.read()
    assert "TEST_2025_n0001" in text
    assert "Item 1A" in text
    assert "Sample risk text." in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_parsing_audit.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'ingest.parsing_audit'`

- [ ] **Step 3: Write `ingest/parsing_audit.py`**

```python
"""Randomized 20-section parsing validation audit.

Samples nodes across the corpus for a human to eyeball: does the table
survive intact, is the markdown rendering clean, is anything truncated?
See resources/specs/Project Idea.md §2 -- this script surfaces the sample,
it cannot self-certify the result; a human must actually look.
"""
import random

import aiosqlite


async def sample_sections(db_path: str, n: int = 20) -> list[dict]:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM nodes")
        rows = [dict(row) for row in await cursor.fetchall()]

    if len(rows) <= n:
        return rows
    return random.sample(rows, n)


def write_audit_report(samples: list[dict], out_path: str) -> None:
    lines = ["# Parsing Validation Audit", "", f"Sampled {len(samples)} node(s) for manual review.", ""]
    for s in samples:
        lines.append(f"## {s['node_id']} ({s['node_type']})")
        lines.append(f"- Document: {s['document_id']}")
        lines.append(f"- Section: {s.get('parent_item_header') or '(none)'}")
        lines.append(f"- Token count: {s['token_count']}")
        lines.append("")
        lines.append("```")
        lines.append(s["content"])
        lines.append("```")
        lines.append("")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_parsing_audit.py -v`

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add ingest/parsing_audit.py tests/test_parsing_audit.py
git commit -m "feat: add 20-section parsing validation audit script"
```

---

### Task 6: End-to-end Phase 2 verification

**Files:**
- No new files — runs everything Tasks 1–5 built, against the real (throttled) filing manifest.

**Interfaces:**
- Consumes: `ingest.run_ingestion.main()`, `ingest.parsing_audit.sample_sections`/`write_audit_report`, all Phase 1 + Phase 2 test files.

- [ ] **Step 1: [ACTIVE — human input required] Confirm all three prerequisites are in place**

Ask the human (skip whichever is already confirmed from earlier tasks):

> "Before I run the real (throttled, 3-filing) ingestion: (1) is `data/filings_manifest.json`'s company list final — Task 1's confirmed list? (2) is `LLAMA_CLOUD_API_KEY` in `project/.env` real and working — Task 3's smoke test passed? (3) OK for me to make live requests to SEC EDGAR and LlamaParse now, using `LOCAL_TEST_THROTTLE=true` (3 filings only)?"

Do not proceed until all three are confirmed.

- [ ] **Step 2: Confirm `LOCAL_TEST_THROTTLE=true` in `project/.env`**

Run: `grep LOCAL_TEST_THROTTLE /Users/ojaswi/Projects/rag-techniques/project/.env`

Expected: `LOCAL_TEST_THROTTLE=true` (Phase 1's default — confirm it wasn't flipped to `false`).

- [ ] **Step 3: Run the throttled ingestion end-to-end**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -m ingest.run_ingestion`

Expected: prints 3 lines like `AAPL_2025: 47 nodes` (one per throttled filing, exact node counts will vary with real filing content) — confirms fetch → parse → node_builder → SQLite insert all work end-to-end against real data.

- [ ] **Step 4: Run the parsing audit against the real throttled data**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -c "
import asyncio
import ingest.parsing_audit as audit

async def main():
    samples = await audit.sample_sections('benchmark.db', n=20)
    audit.write_audit_report(samples, 'parsing_audit_report.md')
    print(f'wrote {len(samples)} samples to parsing_audit_report.md')

asyncio.run(main())
"`

Expected: prints `wrote N samples to parsing_audit_report.md` where `N` is up to 20 (fewer if the throttled 3-filing run produced fewer than 20 total nodes).

- [ ] **Step 5: [PASSIVE — logged, human review still needed] Note the audit report needs eyeballing**

The audit report at `project/parsing_audit_report.md` is generated automatically, but per `Project Idea.md` §2 a human still needs to actually read a few sampled sections and confirm: no table looks truncated, no column is missing, headers render cleanly. This does not block moving on to Phase 3, but should happen before trusting the corpus for Phase 4's dataset generation.

- [ ] **Step 6: Run the full test suite**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/ -v`

Expected: all Phase 1 + Phase 2 tests pass — 15 (Phase 1) + 3 (manifest) + 5 (fetch_filings) + 3 (parse_filing) + 7 (node_builder) + 1 (run_ingestion) + 3 (parsing_audit) = **37 passed**.

- [ ] **Step 7: Commit the audit report and throttled `benchmark.db` state**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add parsing_audit_report.md
git commit -m "chore: run throttled end-to-end ingestion and commit parsing audit report"
```

Note: `benchmark.db` itself stays gitignored (per Phase 1's `.gitignore`) — only the human-readable audit report is committed.

---

### Task 7: Human Action Report

**Files:**
- Create: `temp/phase2-human-actions.md`

**Interfaces:**
- Consumes: the actual outcomes of Task 1 Step 1 (which filing list was confirmed), Task 3 Step 5 (was the LlamaParse key already present or added mid-plan), Task 6 Step 5 (has the audit report actually been eyeballed yet).
- Produces: a human-readable report — no code interface.

- [ ] **Step 1: Write the report reflecting what actually happened**

Write `temp/phase2-human-actions.md`, resolving every bracket from the real outcomes (do not leave placeholder text in the final file):

```markdown
# Phase 2 — Human Action Report

## Active — needs your input before Phase 2 is fully closed out

- [ ] **Eyeball the parsing audit report**: [state whether `project/parsing_audit_report.md`
  has actually been reviewed by a human yet, per Task 6 Step 5 — if not, ask
  the human to open it and check a handful of sampled sections for table
  truncation, column misalignment, or garbled markdown before Phase 4 starts
  generating queries against this corpus]
- [ ] **Confirm the final filing list is right for the dissertation**: [state
  which companies/years were actually used, per Task 1 Step 1 — this is the
  permanent evaluation corpus from here on; changing it later means
  re-running ingestion, dataset generation, and the whole benchmark]

## Passive — already handled, no action needed unless you want to change it

- **LlamaParse API key**: [state whether `project/.env` had a real
  `LLAMA_CLOUD_API_KEY` already, or whether it was added mid-plan at Task 3
  Step 5]
- **SEC EDGAR User-Agent**: auto-filled as `rag-techniques-benchmark
  ojaswiat@gmail.com` in `.env.example` — change `SEC_EDGAR_USER_AGENT` in
  `.env` if a different contact address should be on file with SEC.
- Filing URLs were never hand-typed — `fetch_filings.py` resolves the real
  accession number and document path from SEC's own JSON APIs at runtime,
  so there's no risk of a wrong/stale hardcoded URL.
- 48-hour parse caching is in place — re-running ingestion within 48h of a
  parse costs $0 in LlamaParse credits.

## Not yet needed (deferred to their own phase)

- **P3 summary-index build** (Phase 3): needs the `nodes` table populated
  here, nothing else new from the human.
- **Dataset generation** (Phase 4): needs the parsing audit actually signed
  off (see Active items above) before trusting query ground truth built on
  top of this corpus.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add temp/phase2-human-actions.md
git commit -m "docs: add Phase 2 human action report"
```

Note: run this `git add`/`git commit` from the repo root, not from `project/` — `temp/` is a root-level directory.

---

## Self-Review Notes

- **Spec coverage:** Phase Plan.md Phase 2 Goals 1–5 map to Tasks 1 (source filings via manifest), 2+6 (LlamaParse atomic-table parse, never bisect a table), 4 (metadata enrichment: `node_id`, `parent_item_header`, `node_type`, `source_page_num`), 4+6 (persist to SQLite immediately, cache aggressively), 5+6 (20-section audit). Evaluations 1–3 map to Task 4's atomicity tests, Task 4's `node_id` uniqueness/sequencing tests, and Task 6's full population + cache-hit re-run. Deliverables 1–3 map to Task 6 (populated `nodes` table), Tasks 2–4 (the ingestion/parsing scripts with caching), Task 5+6 (the audit report).
- **Placeholder scan:** the LlamaParse client fallback (`config.LLAMA_CLOUD_API_KEY or "placeholder-key-for-import-only"`) mirrors Phase 1's `groq_client.py` fix for the same reason (keyless import must not crash); this is an intentional, tested pattern, not a stray placeholder.
- **Type consistency:** `build_nodes()`'s return dict keys match `database_manager.insert_node()`'s expected columns exactly (`node_id`, `document_id`, `parent_item_header`, `node_type`, `source_page_num`, `content`, `token_count`) — verified against Phase 1's actual `_SCHEMA` and `insert_node()` signature, not just the spec's DDL.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-21-phase2-ingestion-parsing.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
