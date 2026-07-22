# Phase 3 — P3 Summary-Index Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and persist one hierarchical `TreeIndex` per filing (9 total), using `llama-3.1-8b-instant` on Groq, cached so it is never rebuilt after the first successful build.

**Architecture:** A real `llama_index.core.TreeIndex` per `document_id`, built from that document's `nodes` table rows converted to `TextNode`s. Built sequentially (never concurrent across filings), persisted atomically (temp-dir then rename) to `storage/summary_index/{document_id}/`. Cost (wall-clock + tokens) logged per filing to `logs/index_build_costs.json`.

**Tech Stack:** `llama-index-core` (already installed, v0.14.23, transitive via `llama-cloud-services`), `llama-index-llms-groq` (new dependency), existing `database_manager.py`, `loop_template.py`, `config.py`.

## Global Constraints

- `LOCAL_TEST_THROTTLE` (from `config.py`) caps every loop to `THROTTLE_LIMIT = 3` filings — must run clean end-to-end at throttle before the full 9-filing release (Guardrails.md §7).
- Groq calls in this module use `llama_index.llms.groq.Groq` directly, **not** `call_groq()` — this is a deliberate, scoped, documented exception (see `docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md`). No other module may adopt this exception.
- Model routing: `config.MODEL_ROUTING["p3_index_build"] == "llama-3.1-8b-instant"` — never hardcode the model string.
- Builds must be sequential (one filing's `TreeIndex` construction completes before the next starts) — no `asyncio.gather` across filings.
- Cache test is directory existence of the **final** path only; a crash must never leave a false-positive cache hit (temp-dir-then-atomic-rename).
- `resources/artifacts/Changes.md` gets exactly one new entry for the `call_groq()` bypass (this plan's Task 6) — nothing else in this plan touches that file.

---

### Task 1: Add `llama-index-llms-groq` dependency

**Files:**
- Modify: `project/pyproject.toml`

**Interfaces:**
- Produces: `llama_index.llms.groq.Groq` importable from any later task.

- [ ] **Step 1: Install the package**

```bash
cd project && uv add llama-index-llms-groq
```

- [ ] **Step 2: Verify import**

```bash
cd project && .venv/bin/python -c "from llama_index.llms.groq import Groq; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add project/pyproject.toml project/uv.lock
git commit -m "build: add llama-index-llms-groq dependency for Phase 3 index build"
```

---

### Task 2: Node-to-TextNode conversion

**Files:**
- Create: `project/pipelines/__init__.py` (empty)
- Create: `project/pipelines/structural/__init__.py` (empty)
- Create: `project/pipelines/structural/node_convert.py`
- Test: `project/tests/test_node_convert.py`

**Interfaces:**
- Consumes: node dicts shaped like `database_manager.get_nodes_by_document()`'s return value — keys `node_id, document_id, parent_item_header, node_type, source_page_num, content, token_count`.
- Produces: `nodes_to_llama_nodes(nodes: list[dict]) -> list[TextNode]` — used by Task 3.

- [ ] **Step 1: Write the failing tests**

```python
# project/tests/test_node_convert.py
import pipelines.structural.node_convert as node_convert


def test_nodes_to_llama_nodes_preserves_id_and_text():
    nodes = [
        {"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
         "parent_item_header": "Item 1A. Risk Factors", "node_type": "text",
         "source_page_num": None, "content": "hello world", "token_count": 2},
    ]
    result = node_convert.nodes_to_llama_nodes(nodes)
    assert len(result) == 1
    assert result[0].id_ == "AAPL_2025_n0001"
    assert result[0].text == "hello world"


def test_nodes_to_llama_nodes_preserves_metadata():
    nodes = [
        {"node_id": "AAPL_2025_n0002", "document_id": "AAPL_2025",
         "parent_item_header": None, "node_type": "table",
         "source_page_num": None, "content": "| a | b |", "token_count": 3},
    ]
    result = node_convert.nodes_to_llama_nodes(nodes)
    assert result[0].metadata["document_id"] == "AAPL_2025"
    assert result[0].metadata["node_type"] == "table"
    assert result[0].metadata["parent_item_header"] is None


def test_nodes_to_llama_nodes_empty_list():
    assert node_convert.nodes_to_llama_nodes([]) == []
```

- [ ] **Step 2: Run to verify failure**

```bash
cd project && .venv/bin/python -m pytest tests/test_node_convert.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipelines'`

- [ ] **Step 3: Write the implementation**

```python
# project/pipelines/__init__.py
```

```python
# project/pipelines/structural/__init__.py
```

```python
# project/pipelines/structural/node_convert.py
"""Converts nodes-table rows into LlamaIndex TextNode objects for Phase 3's
TreeIndex build. Kept separate from build_summary_index.py so the shape
mapping (node dict -> TextNode) can be unit-tested without touching Groq.
"""
from llama_index.core.schema import TextNode


def nodes_to_llama_nodes(nodes: list[dict]) -> list[TextNode]:
    return [
        TextNode(
            id_=node["node_id"],
            text=node["content"],
            metadata={
                "document_id": node["document_id"],
                "parent_item_header": node["parent_item_header"],
                "node_type": node["node_type"],
                "source_page_num": node["source_page_num"],
            },
        )
        for node in nodes
    ]
```

- [ ] **Step 4: Run to verify pass**

```bash
cd project && .venv/bin/python -m pytest tests/test_node_convert.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add project/pipelines project/tests/test_node_convert.py
git commit -m "feat: convert nodes-table rows to LlamaIndex TextNode for Phase 3"
```

---

### Task 3: Build-and-persist core logic (atomic cache, mocked in tests)

**Files:**
- Create: `project/pipelines/structural/build_summary_index.py`
- Test: `project/tests/test_build_summary_index.py`

**Interfaces:**
- Consumes: `pipelines.structural.node_convert.nodes_to_llama_nodes()` (Task 2); `database_manager.get_nodes_by_document(db_path, document_id)` (existing); `config.MODEL_ROUTING["p3_index_build"]`, `config.GROQ_API_KEY` (existing).
- Produces: `is_built(document_id: str) -> bool`; `async def build_index_for_document(document_id: str) -> dict` returning `{"document_id": str, "skipped": bool}` or `{"document_id": str, "skipped": False, "wall_clock_sec": float, "input_tokens": int, "output_tokens": int}` — consumed by Task 4 and Task 5.

- [ ] **Step 1: Write the failing tests**

```python
# project/tests/test_build_summary_index.py
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import pipelines.structural.build_summary_index as bsi


@pytest.mark.asyncio
async def test_build_index_for_document_skips_if_final_dir_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)
    (tmp_path / "AAPL_2025").mkdir()

    result = await bsi.build_index_for_document("AAPL_2025")

    assert result == {"document_id": "AAPL_2025", "skipped": True}


@pytest.mark.asyncio
async def test_build_index_for_document_builds_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)

    fake_nodes = [{"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
                   "parent_item_header": None, "node_type": "text",
                   "source_page_num": None, "content": "hello", "token_count": 1}]

    fake_index = MagicMock()

    def fake_persist(persist_dir):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        (Path(persist_dir) / "docstore.json").write_text("{}")

    fake_index.storage_context.persist.side_effect = fake_persist

    with patch.object(bsi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)), \
         patch.object(bsi, "TreeIndex", return_value=fake_index) as mock_tree, \
         patch.object(bsi, "Groq"):
        result = await bsi.build_index_for_document("AAPL_2025")

    assert result["document_id"] == "AAPL_2025"
    assert result["skipped"] is False
    assert (tmp_path / "AAPL_2025" / "docstore.json").exists()
    assert not (tmp_path / "AAPL_2025.tmp").exists()
    mock_tree.assert_called_once()


@pytest.mark.asyncio
async def test_build_index_for_document_crash_leaves_only_temp_dir(tmp_path, monkeypatch):
    """A crash between persist() and the atomic rename must never leave a
    false-positive cache hit -- the final dir must stay absent."""
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)

    fake_nodes = [{"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
                   "parent_item_header": None, "node_type": "text",
                   "source_page_num": None, "content": "hello", "token_count": 1}]

    fake_index = MagicMock()

    def fake_persist(persist_dir):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

    fake_index.storage_context.persist.side_effect = fake_persist

    with patch.object(bsi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)), \
         patch.object(bsi, "TreeIndex", return_value=fake_index), \
         patch.object(bsi, "Groq"), \
         patch.object(bsi.os, "rename", side_effect=OSError("simulated crash")):
        with pytest.raises(OSError):
            await bsi.build_index_for_document("AAPL_2025")

    assert (tmp_path / "AAPL_2025.tmp").exists()
    assert not (tmp_path / "AAPL_2025").exists()
    assert bsi.is_built("AAPL_2025") is False


@pytest.mark.asyncio
async def test_build_index_for_document_cleans_stale_temp_dir_before_retry(tmp_path, monkeypatch):
    """A leftover temp dir from a prior crashed build must not break the next attempt."""
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)
    stale_temp = tmp_path / "AAPL_2025.tmp"
    stale_temp.mkdir()
    (stale_temp / "leftover.json").write_text("{}")

    fake_nodes = [{"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
                   "parent_item_header": None, "node_type": "text",
                   "source_page_num": None, "content": "hello", "token_count": 1}]

    fake_index = MagicMock()

    def fake_persist(persist_dir):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        (Path(persist_dir) / "docstore.json").write_text("{}")

    fake_index.storage_context.persist.side_effect = fake_persist

    with patch.object(bsi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)), \
         patch.object(bsi, "TreeIndex", return_value=fake_index), \
         patch.object(bsi, "Groq"):
        result = await bsi.build_index_for_document("AAPL_2025")

    assert result["skipped"] is False
    assert (tmp_path / "AAPL_2025" / "docstore.json").exists()
    assert not (tmp_path / "AAPL_2025.tmp").exists()
```

- [ ] **Step 2: Run to verify failure**

```bash
cd project && .venv/bin/python -m pytest tests/test_build_summary_index.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipelines.structural.build_summary_index'`

- [ ] **Step 3: Write the implementation**

```python
# project/pipelines/structural/build_summary_index.py
"""Builds and persists one hierarchical TreeIndex per filing (Phase 3,
Guardrails.md §1 -- the only index build permitted to call an LLM, and it
must run once and be cached, never per query).

Deliberately uses llama_index.llms.groq.Groq directly rather than routing
through groq_client.call_groq() -- see
docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md for why
(Phase 5's P3 pipeline needs a real TreeIndex.as_retriever(), which a
custom-built tree wouldn't provide) and the scoped, mitigated risk this
carries (documented in resources/artifacts/Changes.md).
"""
import os
import shutil
import time
from pathlib import Path

from llama_index.core import TreeIndex
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.groq import Groq

import config
import database_manager as dbm
from pipelines.structural.node_convert import nodes_to_llama_nodes

STORAGE_ROOT = Path("storage/summary_index")
DB_PATH = "benchmark.db"


def _final_dir(document_id: str) -> Path:
    return STORAGE_ROOT / document_id


def _temp_dir(document_id: str) -> Path:
    return STORAGE_ROOT / f"{document_id}.tmp"


def is_built(document_id: str) -> bool:
    return _final_dir(document_id).exists()


async def build_index_for_document(document_id: str) -> dict:
    if is_built(document_id):
        return {"document_id": document_id, "skipped": True}

    nodes = await dbm.get_nodes_by_document(DB_PATH, document_id)
    llama_nodes = nodes_to_llama_nodes(nodes)

    token_counter = TokenCountingHandler()
    llm = Groq(
        model=config.MODEL_ROUTING["p3_index_build"],
        api_key=config.GROQ_API_KEY or "placeholder-key-for-import-only",
        callback_manager=CallbackManager([token_counter]),
    )

    start = time.monotonic()
    index = TreeIndex(nodes=llama_nodes, llm=llm, build_tree=True)
    wall_clock_sec = time.monotonic() - start

    temp_dir = _temp_dir(document_id)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    index.storage_context.persist(persist_dir=str(temp_dir))
    os.rename(temp_dir, _final_dir(document_id))

    return {
        "document_id": document_id,
        "skipped": False,
        "wall_clock_sec": wall_clock_sec,
        "input_tokens": token_counter.total_prompt_tokens,
        "output_tokens": token_counter.total_completion_tokens,
    }
```

- [ ] **Step 4: Run to verify pass**

```bash
cd project && .venv/bin/python -m pytest tests/test_build_summary_index.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add project/pipelines/structural/build_summary_index.py project/tests/test_build_summary_index.py
git commit -m "feat: build and atomically persist per-filing TreeIndex for Phase 3"
```

---

### Task 4: Cost logging

**Files:**
- Modify: `project/pipelines/structural/build_summary_index.py`
- Test: `project/tests/test_build_summary_index.py` (append to same file)

**Interfaces:**
- Consumes: cost-row dicts produced by `build_index_for_document()` (Task 3).
- Produces: `append_cost_log(cost_row: dict, log_path: Path = COST_LOG_PATH) -> None` — consumed by Task 5's `main()`.

- [ ] **Step 1: Write the failing test**

```python
# append to project/tests/test_build_summary_index.py
import json


def test_append_cost_log_creates_and_appends(tmp_path):
    log_path = tmp_path / "logs" / "index_build_costs.json"
    bsi.append_cost_log(
        {"document_id": "AAPL_2025", "skipped": False, "wall_clock_sec": 1.0,
         "input_tokens": 10, "output_tokens": 5},
        log_path=log_path,
    )
    bsi.append_cost_log({"document_id": "AAPL_2024", "skipped": True}, log_path=log_path)

    rows = json.loads(log_path.read_text())
    assert len(rows) == 2
    assert rows[0]["document_id"] == "AAPL_2025"
    assert rows[1]["skipped"] is True
```

- [ ] **Step 2: Run to verify failure**

```bash
cd project && .venv/bin/python -m pytest tests/test_build_summary_index.py::test_append_cost_log_creates_and_appends -v
```

Expected: FAIL — `AttributeError: module 'pipelines.structural.build_summary_index' has no attribute 'append_cost_log'`

- [ ] **Step 3: Add the implementation**

```python
# add to project/pipelines/structural/build_summary_index.py, near the top
import json

COST_LOG_PATH = Path("logs/index_build_costs.json")
```

```python
# add to project/pipelines/structural/build_summary_index.py, at the end
def append_cost_log(cost_row: dict, log_path: Path = COST_LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(log_path.read_text()) if log_path.exists() else []
    rows.append(cost_row)
    log_path.write_text(json.dumps(rows, indent=2))
```

- [ ] **Step 4: Run to verify pass**

```bash
cd project && .venv/bin/python -m pytest tests/test_build_summary_index.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add project/pipelines/structural/build_summary_index.py project/tests/test_build_summary_index.py
git commit -m "feat: log per-filing wall-clock and token cost for Phase 3 build"
```

---

### Task 5: Sequential orchestrator (`main()`)

**Files:**
- Modify: `project/pipelines/structural/build_summary_index.py`
- Test: `project/tests/test_build_summary_index.py` (append to same file)

**Interfaces:**
- Consumes: `build_index_for_document()` (Task 3), `append_cost_log()` (Task 4), `loop_template.apply_throttle(items: list) -> list` (existing), `data/filings_manifest.json` (existing, 9 entries with `document_id, ticker, fiscal_year`).
- Produces: `async def main()` — the script entry point, run manually (Task 6) and never imported elsewhere.

- [ ] **Step 1: Write the failing test**

```python
# append to project/tests/test_build_summary_index.py
@pytest.mark.asyncio
async def test_main_builds_each_manifest_entry_sequentially(tmp_path, monkeypatch):
    manifest = [
        {"document_id": "AAPL_2023", "ticker": "AAPL", "fiscal_year": 2023},
        {"document_id": "AAPL_2024", "ticker": "AAPL", "fiscal_year": 2024},
    ]
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)
    monkeypatch.setattr(bsi.loop_template, "apply_throttle", lambda items: items)

    with patch("builtins.open", create=True) as mock_open, \
         patch.object(bsi, "build_index_for_document", new=AsyncMock(
             side_effect=[{"document_id": "AAPL_2023", "skipped": False},
                          {"document_id": "AAPL_2024", "skipped": True}])) as mock_build, \
         patch.object(bsi, "append_cost_log") as mock_log:
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(manifest)
        await bsi.main()

    assert mock_build.call_count == 2
    mock_build.assert_any_call("AAPL_2023")
    mock_build.assert_any_call("AAPL_2024")
    assert mock_log.call_count == 2
```

- [ ] **Step 2: Run to verify failure**

```bash
cd project && .venv/bin/python -m pytest tests/test_build_summary_index.py::test_main_builds_each_manifest_entry_sequentially -v
```

Expected: FAIL — `AttributeError: module 'pipelines.structural.build_summary_index' has no attribute 'main'`

- [ ] **Step 3: Add the implementation**

```python
# add to project/pipelines/structural/build_summary_index.py, near the top
import asyncio

import loop_template

MANIFEST_PATH = "data/filings_manifest.json"
```

```python
# add to project/pipelines/structural/build_summary_index.py, at the end
async def main():
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    manifest = loop_template.apply_throttle(manifest)

    for entry in manifest:
        cost_row = await build_index_for_document(entry["document_id"])
        append_cost_log(cost_row)
        status = "skipped (cached)" if cost_row.get("skipped") else "built"
        print(f"{entry['document_id']}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run to verify pass**

```bash
cd project && .venv/bin/python -m pytest tests/test_build_summary_index.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add project/pipelines/structural/build_summary_index.py project/tests/test_build_summary_index.py
git commit -m "feat: sequential throttle-aware orchestrator for Phase 3 index build"
```

---

### Task 6: Changes.md entry, then live throttled end-to-end run

**Files:**
- Modify: `resources/artifacts/Changes.md`

**Interfaces:**
- Consumes: `pipelines.structural.build_summary_index.main()` (Task 5) run live against real `benchmark.db` (3 AAPL filings already ingested in Phase 2).
- Produces: nothing further downstream in this plan — Phase 5 consumes the persisted `storage/summary_index/{document_id}/` directories.

- [ ] **Step 1: Add the Changes.md entry**

```markdown
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
```

- [ ] **Step 2: Commit the Changes.md entry**

```bash
git add resources/artifacts/Changes.md
git commit -m "docs: record Phase 3 call_groq() bypass as a scoped, mitigated deviation"
```

- [ ] **Step 3: Confirm `LOCAL_TEST_THROTTLE` is `true`**

```bash
cd project && grep LOCAL_TEST_THROTTLE .env
```

Expected: `LOCAL_TEST_THROTTLE=true` (or absent, since `config.py` defaults to `true`)

- [ ] **Step 4: Run the full test suite (mocked tests only, no live spend)**

```bash
cd project && .venv/bin/python -m pytest -v
```

Expected: all tests pass, including the new Phase 3 tests from Tasks 2-5.

- [ ] **Step 5: Run the live throttled build (real Groq spend, 3 filings)**

```bash
cd project && .venv/bin/python -m pipelines.structural.build_summary_index
```

Expected: prints `AAPL_2023: built`, `AAPL_2024: built`, `AAPL_2025: built` (or `skipped (cached)` if already run before); `storage/summary_index/AAPL_2023/`, `.../AAPL_2024/`, `.../AAPL_2025/` each contain LlamaIndex's persisted files (`docstore.json`, `index_store.json`); `logs/index_build_costs.json` has one row per filing with `wall_clock_sec`, `input_tokens`, `output_tokens`.

- [ ] **Step 6: Confirm caching works (second run makes zero new Groq calls)**

```bash
cd project && .venv/bin/python -m pipelines.structural.build_summary_index
```

Expected: prints `skipped (cached)` for all 3 filings, `logs/index_build_costs.json` grows by 3 more rows all with `"skipped": true` and no `wall_clock_sec`/token fields — confirming Architecture.md's evaluation criterion ("loads from cache thereafter, never rebuilt").

No commit for this task's live-run steps — nothing to check in beyond what Tasks 1-5 and Step 2 already committed; `storage/` and `logs/` are gitignored.

---

## Notes for the full-corpus release (not part of this plan's tasks)

Once satisfied with the throttled 3-filing run, flip `LOCAL_TEST_THROTTLE=false` in `project/.env` and re-run Step 5 above to build the remaining 6 filings' trees — but only after the remaining 6 filings are actually ingested (see `temp/deferred.md`, item 2 — MSFT/TSLA ingestion is still outstanding from Phase 2). This is a routine re-run, not a new task; no plan update needed for it.
