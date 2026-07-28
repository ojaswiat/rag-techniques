# Phase 4: Dataset Generation & Adversarial Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate the `queries` (100 PQ), `golden_queries` (20 GQ), and `judge_validation` (20 JEQ) SQLite tables with 140 cross-verified queries (35 per quadrant) generated from the 9-filing corpus, using two different LLM families in an adversarial generate-then-verify loop, plus tooling to hand-label the 20 GQ.

**Architecture:** A Generator model (`gpt-oss-120b`) reads one filing section at a time (grouped by `parent_item_header`) and proposes a query + ground truth + citations. A Critic model (`qwen3.6-27b`, a different family, with a local keyword-search tool over the whole filing) independently re-derives an answer blind. Plain Python code (not an LLM) accepts or rejects based on citation overlap and normalized numeric match. Accepted queries are distributed into PQ/GQ/JEQ as they're produced, keeping the three sets disjoint by construction.

**Tech Stack:** Python 3.13, `aiosqlite`, existing `groq_client.call_groq()` (Groq SDK under the hood), `tenacity` (already wired into `call_groq`), `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`), `unittest.mock` for LLM-call mocking.

## Global Constraints

- Generator family (`openai/gpt-oss-120b`) must never equal Critic family (`qwen/qwen3.6-27b`) — anti-self-grading invariant (`CLAUDE.md` §4).
- `queries` / `golden_queries` / `judge_validation` must remain disjoint sets — each accepted query is written to exactly one table at generation time, never copied or moved afterward (`CLAUDE.md` §4, Guardrails.md).
- All LLM calls in this phase route through `groq_client.call_groq()` — no direct `AsyncGroq` client instantiation (unlike Phase 3's documented, scoped exception; Phase 4 has none).
- `temperature = 0` for every LLM call (`call_groq`'s existing default already satisfies this; do not override).
- `config.LOCAL_TEST_THROTTLE` (already exists, defaults from `.env`) must cap a test run to `config.THROTTLE_LIMIT` (3) sections total before any full run — do not invent a second throttle flag.
- Do not alter the `queries` / `golden_queries` / `judge_validation` schemas in `database_manager.py` — they already exist (Phase 1). This phase only adds new functions to populate them.
- `golden_queries.human_score`, `.human_reasoning`, `.example_output` are `NOT NULL` in the existing schema — since human labeling happens *after* generation, insert placeholder values at generation time (`human_score=1`, `human_reasoning="PENDING_HUMAN_LABEL"`, `example_output=ground_truth_answer`) and overwrite them later via `update_golden_query_labels()`.
- Every new test file follows the existing convention in `project/tests/`: a `TEST_DB` constant + `clean_db` autouse fixture for DB tests (see `test_database_manager.py`), `@pytest.mark.asyncio` on async tests, `unittest.mock.patch`/`AsyncMock` for mocking `call_groq` (see `test_groq_client_backoff.py`). No live Groq calls in the default test run.
- All file paths below are relative to `project/` (the repo's Python package root — `pyproject.toml`, `pytest.ini_options` live there).

---

### Task 1: Database helpers for queries / golden_queries / judge_validation

**Files:**
- Modify: `database_manager.py` (add functions after `get_completed_keys`, before `_dumps`)
- Test: `tests/test_database_manager.py` (append new test functions to the existing file)

**Interfaces:**
- Consumes: existing `_dumps`/`_loads` helpers, existing `_SCHEMA` (unchanged).
- Produces (used by Task 7's orchestrator and Task 8's label tools):
  - `async def insert_query(db_path: str, row: dict) -> None` — `row` keys: `query_id, quadrant, query_text, ground_truth_answer, gt_citations (list[str]), document_id`. `verified` defaults to `1`.
  - `async def insert_golden_query(db_path: str, row: dict) -> None` — `row` keys: `query_id, quadrant, query_text, ground_truth_answer, gt_citations (list[str]), example_output, human_score (int), human_reasoning, document_id`.
  - `async def insert_judge_validation(db_path: str, row: dict) -> None` — `row` keys: `query_id, quadrant, query_text, ground_truth_answer, gt_citations (list[str]), document_id`.
  - `async def get_quadrant_counts(db_path: str, table: str) -> dict[str, int]` — `table` is one of `"queries"`, `"golden_queries"`, `"judge_validation"`; returns all 4 quadrants as keys (0 if absent), raises `ValueError` for any other table name.
  - `async def get_golden_queries(db_path: str) -> list[dict]` — returns all rows from `golden_queries` with `gt_citations` already JSON-decoded to `list[str]`.
  - `async def update_golden_query_labels(db_path: str, query_id: str, human_score: int, human_reasoning: str) -> None`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_database_manager.py`:

```python
@pytest.mark.asyncio
async def test_insert_query_and_quadrant_counts():
    await dbm.init_db(TEST_DB)
    await dbm.insert_query(TEST_DB, {
        "query_id": "Q1_TEST_001",
        "quadrant": "Q1_Direct_Text",
        "query_text": "What is the total revenue?",
        "ground_truth_answer": "$100 million",
        "gt_citations": ["TEST_2025_n0001"],
        "document_id": "SEC_10K_TEST_2025",
    })
    counts = await dbm.get_quadrant_counts(TEST_DB, "queries")
    assert counts == {
        "Q1_Direct_Text": 1,
        "Q2_Implicit_Text": 0,
        "Q3_Direct_Table": 0,
        "Q4_Implicit_Table": 0,
    }


@pytest.mark.asyncio
async def test_get_quadrant_counts_rejects_unknown_table():
    await dbm.init_db(TEST_DB)
    with pytest.raises(ValueError):
        await dbm.get_quadrant_counts(TEST_DB, "results")


@pytest.mark.asyncio
async def test_insert_golden_query_and_update_labels():
    await dbm.init_db(TEST_DB)
    await dbm.insert_golden_query(TEST_DB, {
        "query_id": "Q1_GQ_001",
        "quadrant": "Q1_Direct_Text",
        "query_text": "What is the total revenue?",
        "ground_truth_answer": "$100 million",
        "gt_citations": ["TEST_2025_n0001"],
        "example_output": "$100 million",
        "human_score": 1,
        "human_reasoning": "PENDING_HUMAN_LABEL",
        "document_id": "SEC_10K_TEST_2025",
    })
    golden = await dbm.get_golden_queries(TEST_DB)
    assert len(golden) == 1
    assert golden[0]["gt_citations"] == ["TEST_2025_n0001"]
    assert golden[0]["human_reasoning"] == "PENDING_HUMAN_LABEL"

    await dbm.update_golden_query_labels(TEST_DB, "Q1_GQ_001", 8, "Clean, unambiguous fact retrieval.")
    golden = await dbm.get_golden_queries(TEST_DB)
    assert golden[0]["human_score"] == 8
    assert golden[0]["human_reasoning"] == "Clean, unambiguous fact retrieval."


@pytest.mark.asyncio
async def test_insert_judge_validation():
    await dbm.init_db(TEST_DB)
    await dbm.insert_judge_validation(TEST_DB, {
        "query_id": "Q1_JEQ_001",
        "quadrant": "Q1_Direct_Text",
        "query_text": "What is the total revenue?",
        "ground_truth_answer": "$100 million",
        "gt_citations": ["TEST_2025_n0001"],
        "document_id": "SEC_10K_TEST_2025",
    })
    counts = await dbm.get_quadrant_counts(TEST_DB, "judge_validation")
    assert counts["Q1_Direct_Text"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_database_manager.py -v -k "quadrant or golden or judge_validation"`
Expected: FAIL with `AttributeError: module 'database_manager' has no attribute 'insert_query'` (and similarly for the other new functions).

- [ ] **Step 3: Implement the minimal code**

Add to `database_manager.py`, immediately after `get_completed_keys` and before `def _dumps`:

```python
_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table")
_QUADRANT_TABLES = ("queries", "golden_queries", "judge_validation")


async def insert_query(db_path: str, row: dict) -> None:
    params = {**row, "gt_citations": _dumps(row["gt_citations"]), "verified": int(row.get("verified", 1))}
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO queries
               (query_id, quadrant, query_text, ground_truth_answer, gt_citations, document_id, verified)
               VALUES (:query_id, :quadrant, :query_text, :ground_truth_answer, :gt_citations, :document_id, :verified)""",
            params,
        )
        await conn.commit()


async def insert_golden_query(db_path: str, row: dict) -> None:
    params = {**row, "gt_citations": _dumps(row["gt_citations"])}
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO golden_queries
               (query_id, quadrant, query_text, ground_truth_answer, gt_citations,
                example_output, human_score, human_reasoning, document_id)
               VALUES (:query_id, :quadrant, :query_text, :ground_truth_answer, :gt_citations,
                       :example_output, :human_score, :human_reasoning, :document_id)""",
            params,
        )
        await conn.commit()


async def insert_judge_validation(db_path: str, row: dict) -> None:
    params = {**row, "gt_citations": _dumps(row["gt_citations"])}
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO judge_validation
               (query_id, quadrant, query_text, ground_truth_answer, gt_citations, document_id)
               VALUES (:query_id, :quadrant, :query_text, :ground_truth_answer, :gt_citations, :document_id)""",
            params,
        )
        await conn.commit()


async def get_quadrant_counts(db_path: str, table: str) -> dict[str, int]:
    if table not in _QUADRANT_TABLES:
        raise ValueError(f"unsupported table for quadrant counts: {table!r}")
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(f"SELECT quadrant, COUNT(*) FROM {table} GROUP BY quadrant")
        rows = await cursor.fetchall()
    counts = {q: 0 for q in _QUADRANTS}
    counts.update({r[0]: r[1] for r in rows})
    return counts


async def get_golden_queries(db_path: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM golden_queries")
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["gt_citations"] = _loads(d["gt_citations"])
        result.append(d)
    return result


async def update_golden_query_labels(db_path: str, query_id: str, human_score: int, human_reasoning: str) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            "UPDATE golden_queries SET human_score = ?, human_reasoning = ? WHERE query_id = ?",
            (human_score, human_reasoning, query_id),
        )
        await conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_database_manager.py -v`
Expected: PASS (all tests in the file, old and new).

- [ ] **Step 5: Commit**

```bash
git add database_manager.py tests/test_database_manager.py
git commit -m "feat: add queries/golden_queries/judge_validation DB helpers for Phase 4"
```

---

### Task 2: Section grouper

**Files:**
- Create: `dataset_generation/__init__.py` (empty)
- Create: `dataset_generation/section_grouper.py`
- Test: `tests/test_section_grouper.py`

**Interfaces:**
- Consumes: nothing from other Phase 4 modules — pure function over plain dicts (shape matches `database_manager.get_nodes_by_document`'s return: `{node_id, document_id, parent_item_header, node_type, source_page_num, content, token_count}`).
- Produces (used by Task 7's orchestrator): `def group_sections(nodes: list[dict]) -> list[dict]` — each returned dict has keys `document_id: str, section_header: str, node_ids: list[str], content: str, token_count: int`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_section_grouper.py`:

```python
from dataset_generation.section_grouper import group_sections


def _node(node_id, document_id, header, content="text", token_count=10):
    return {
        "node_id": node_id,
        "document_id": document_id,
        "parent_item_header": header,
        "node_type": "text",
        "source_page_num": 1,
        "content": content,
        "token_count": token_count,
    }


def test_groups_nodes_by_document_and_header():
    nodes = [
        _node("n1", "DOC_A", "Item 1A. Risk Factors", content="risk one", token_count=5),
        _node("n2", "DOC_A", "Item 1A. Risk Factors", content="risk two", token_count=7),
        _node("n3", "DOC_A", "Item 7. MD&A", content="md and a", token_count=9),
    ]
    sections = group_sections(nodes)
    assert len(sections) == 2
    risk_section = next(s for s in sections if "Risk Factors" in s["section_header"])
    assert risk_section["node_ids"] == ["n1", "n2"]
    assert risk_section["content"] == "risk one\n\nrisk two"
    assert risk_section["token_count"] == 12


def test_normalizes_header_case_into_one_section():
    nodes = [
        _node("n1", "DOC_A", "ITEM 1A. RISK FACTORS"),
        _node("n2", "DOC_A", "Item 1A. Risk Factors"),
    ]
    sections = group_sections(nodes)
    assert len(sections) == 1
    assert sections[0]["node_ids"] == ["n1", "n2"]


def test_excludes_null_and_empty_headers():
    nodes = [
        _node("n1", "DOC_A", None),
        _node("n2", "DOC_A", ""),
        _node("n3", "DOC_A", "   "),
        _node("n4", "DOC_A", "Item 8. Financial Statements"),
    ]
    sections = group_sections(nodes)
    assert len(sections) == 1
    assert sections[0]["node_ids"] == ["n4"]


def test_keeps_documents_separate():
    nodes = [
        _node("n1", "DOC_A", "Item 1A. Risk Factors"),
        _node("n2", "DOC_B", "Item 1A. Risk Factors"),
    ]
    sections = group_sections(nodes)
    assert len(sections) == 2
    assert {s["document_id"] for s in sections} == {"DOC_A", "DOC_B"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_section_grouper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dataset_generation'`.

- [ ] **Step 3: Write the implementation**

Create `dataset_generation/__init__.py` (empty file).

Create `dataset_generation/section_grouper.py`:

```python
"""Groups Phase 2 nodes into per-section chunks for the Phase 4 Generator.

A "section" is every node sharing the same (document_id, parent_item_header),
case-normalized. Nodes with no header (cover pages, TOC, signature blocks --
~6% of the corpus, confirmed during Phase 4 brainstorming) are excluded.
"""


def group_sections(nodes: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], dict] = {}

    for node in nodes:
        header = node.get("parent_item_header")
        if not header or not header.strip():
            continue

        key = (node["document_id"], header.strip().upper())
        if key not in groups:
            groups[key] = {
                "document_id": node["document_id"],
                "section_header": header.strip(),
                "node_ids": [],
                "content_parts": [],
                "token_count": 0,
            }

        groups[key]["node_ids"].append(node["node_id"])
        groups[key]["content_parts"].append(node["content"])
        groups[key]["token_count"] += node["token_count"]

    return [
        {
            "document_id": g["document_id"],
            "section_header": g["section_header"],
            "node_ids": g["node_ids"],
            "content": "\n\n".join(g["content_parts"]),
            "token_count": g["token_count"],
        }
        for g in groups.values()
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_section_grouper.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add dataset_generation/__init__.py dataset_generation/section_grouper.py tests/test_section_grouper.py
git commit -m "feat: add section_grouper for Phase 4 per-section chunking"
```

---

### Task 3: Cross-check (deterministic accept/reject)

**Files:**
- Create: `dataset_generation/cross_check.py`
- Test: `tests/test_cross_check.py`

**Interfaces:**
- Consumes: nothing from other Phase 4 modules — pure functions over plain values.
- Produces (used by Task 7's orchestrator): `def check_query(gt_citations: list[str], gt_answer: str, critic_cited_ids: list[str], critic_answer: str) -> bool`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_cross_check.py`:

```python
from dataset_generation.cross_check import check_query, citations_overlap, extract_numbers, values_match


def test_citations_overlap_true_on_any_shared_node():
    assert citations_overlap(["n1", "n2"], ["n2", "n9"]) is True


def test_citations_overlap_false_on_disjoint_sets():
    assert citations_overlap(["n1", "n2"], ["n8", "n9"]) is False


def test_extract_numbers_handles_currency_and_commas():
    assert extract_numbers("$52,866 million") == [52866.0]


def test_extract_numbers_handles_multiple_values_in_order():
    assert extract_numbers(
        "Operating expenses decreased 4.2% YoY. Factoring in the $15M impairment, normalized expenses rose 1.1%."
    ) == [4.2, 15.0, 1.1]


def test_values_match_exact_after_normalization():
    assert values_match("$52,866 million", "52866") is True


def test_values_match_within_tolerance():
    assert values_match("4.2%", "4.205%") is True


def test_values_match_false_on_real_difference():
    assert values_match("4.2%", "6.7%") is False


def test_values_match_false_on_mismatched_number_count():
    assert values_match("4.2% and 1.1%", "4.2%") is False


def test_values_match_falls_back_to_text_equality_with_no_numbers():
    assert values_match("increased", "increased") is True
    assert values_match("increased", "decreased") is False


def test_check_query_accepts_on_overlap_and_matching_value():
    assert check_query(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n2", "n9"],
        critic_answer="100 million",
    ) is True


def test_check_query_rejects_on_no_citation_overlap():
    assert check_query(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n8", "n9"],
        critic_answer="100 million",
    ) is False


def test_check_query_rejects_on_value_mismatch():
    assert check_query(
        gt_citations=["n1", "n2"],
        gt_answer="$100 million",
        critic_cited_ids=["n2"],
        critic_answer="200 million",
    ) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cross_check.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dataset_generation.cross_check'`.

- [ ] **Step 3: Write the implementation**

Create `dataset_generation/cross_check.py`:

```python
"""Deterministic accept/reject logic for the Generator/Critic adversarial loop.

Plain code, not an LLM judgement (Phase Plan.md Phase 4 Evaluation 3): accept
a candidate query only if the Critic's independently-found node citations
overlap the Generator's, and the Critic's independently-computed answer
matches the Generator's ground truth after numeric normalization.
"""
import re

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def citations_overlap(gt_citations: list[str], critic_cited_ids: list[str]) -> bool:
    return bool(set(gt_citations) & set(critic_cited_ids))


def extract_numbers(text: str) -> list[float]:
    numbers = []
    for match in _NUMBER_RE.findall(text or ""):
        cleaned = match.replace(",", "")
        try:
            numbers.append(float(cleaned))
        except ValueError:
            continue
    return numbers


def values_match(gt_answer: str, critic_answer: str, tolerance: float = 0.01) -> bool:
    gt_numbers = extract_numbers(gt_answer)
    critic_numbers = extract_numbers(critic_answer)

    if not gt_numbers or not critic_numbers:
        return gt_answer.strip().lower() == critic_answer.strip().lower()

    if len(gt_numbers) != len(critic_numbers):
        return False

    return all(abs(g - c) <= tolerance for g, c in zip(gt_numbers, critic_numbers))


def check_query(
    gt_citations: list[str],
    gt_answer: str,
    critic_cited_ids: list[str],
    critic_answer: str,
) -> bool:
    return citations_overlap(gt_citations, critic_cited_ids) and values_match(gt_answer, critic_answer)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_cross_check.py -v`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
git add dataset_generation/cross_check.py tests/test_cross_check.py
git commit -m "feat: add deterministic cross-check for Phase 4 query verification"
```

---

### Task 4: Local search tool for the Critic

**Files:**
- Create: `dataset_generation/search_tool.py`
- Test: `tests/test_search_tool.py`

**Interfaces:**
- Consumes: node dicts shaped like `database_manager.get_nodes_by_document`'s return (`node_id`, `content` at minimum).
- Produces (used by Task 6's `async_critic.py`):
  - `SEARCH_TOOL_SCHEMA: dict` — an OpenAI/Groq function-calling tool schema named `search_filing`.
  - `def search_filing_nodes(nodes: list[dict], query: str, top_k: int = 5) -> list[dict]` — returns the `top_k` nodes (full dicts, unmodified) ranked by keyword-overlap score, ties broken by `node_id` ascending.

- [ ] **Step 1: Write the failing test**

Create `tests/test_search_tool.py`:

```python
from dataset_generation.search_tool import SEARCH_TOOL_SCHEMA, search_filing_nodes


def _node(node_id, content):
    return {"node_id": node_id, "content": content}


def test_ranks_by_keyword_overlap():
    nodes = [
        _node("n1", "Total revenue increased due to strong iPhone sales"),
        _node("n2", "The board of directors met quarterly"),
        _node("n3", "Total revenue and total operating expenses both rose"),
    ]
    results = search_filing_nodes(nodes, "total revenue", top_k=5)
    assert [r["node_id"] for r in results] == ["n3", "n1"]


def test_excludes_zero_overlap_nodes():
    nodes = [
        _node("n1", "unrelated content about employees"),
    ]
    results = search_filing_nodes(nodes, "total revenue", top_k=5)
    assert results == []


def test_respects_top_k():
    nodes = [_node(f"n{i}", "revenue revenue revenue") for i in range(10)]
    results = search_filing_nodes(nodes, "revenue", top_k=3)
    assert len(results) == 3


def test_ties_broken_by_node_id():
    nodes = [
        _node("n9", "revenue figures"),
        _node("n2", "revenue figures"),
    ]
    results = search_filing_nodes(nodes, "revenue", top_k=5)
    assert [r["node_id"] for r in results] == ["n2", "n9"]


def test_tool_schema_shape():
    assert SEARCH_TOOL_SCHEMA["type"] == "function"
    assert SEARCH_TOOL_SCHEMA["function"]["name"] == "search_filing"
    assert "query" in SEARCH_TOOL_SCHEMA["function"]["parameters"]["properties"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_search_tool.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dataset_generation.search_tool'`.

- [ ] **Step 3: Write the implementation**

Create `dataset_generation/search_tool.py`:

```python
"""Local, dependency-free keyword search the Critic uses to find evidence.

Not a retrieval pipeline (Guardrails.md's P2-purity rule is about the
benchmarked BM25 pipeline in Phase 5, not incidental tooling here) --
just simple word-overlap scoring so the Critic can locate candidate nodes
in a filing before answering.
"""
import re

_WORD_RE = re.compile(r"[a-z0-9]+")

SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_filing",
        "description": (
            "Search this filing's nodes for content matching a query. "
            "Returns up to 5 of the most relevant nodes with their node_id and content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to search for in the filing",
                },
            },
            "required": ["query"],
        },
    },
}


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def search_filing_nodes(nodes: list[dict], query: str, top_k: int = 5) -> list[dict]:
    query_tokens = _tokenize(query)
    scored = []
    for node in nodes:
        score = len(query_tokens & _tokenize(node["content"]))
        if score > 0:
            scored.append((score, node["node_id"], node))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [node for _, _, node in scored[:top_k]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_search_tool.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add dataset_generation/search_tool.py tests/test_search_tool.py
git commit -m "feat: add local keyword search tool for Phase 4 Critic"
```

---

### Task 5: `call_groq` tools param + async Generator

**Files:**
- Modify: `groq_client.py:34-40` (add an optional `tools` parameter)
- Test: `tests/test_groq_client_backoff.py` (append one test)
- Create: `dataset_generation/async_generator.py`
- Test: `tests/test_async_generator.py`

**Interfaces:**
- Consumes: `groq_client.call_groq(model, messages, temperature=0.0, tools=None)` (extended), `config.MODEL_ROUTING["generator"]`, section dicts from Task 2 (`document_id, section_header, node_ids, content, token_count`).
- Produces (used by Task 7's orchestrator): `async def generate_query(section: dict, quadrant: str) -> dict` — returns `{query_text, ground_truth_answer, gt_citations (list[str]), quadrant, document_id}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_groq_client_backoff.py`:

```python
@pytest.mark.asyncio
async def test_call_groq_passes_tools_through_when_given():
    success_result = {"choices": [{"message": {"content": "ok"}}]}
    captured_kwargs = {}

    async def capture_create(**kwargs):
        captured_kwargs.update(kwargs)
        return success_result

    with patch.object(groq_client, "_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=capture_create)
        await groq_client.call_groq(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "hi"}],
            tools=[{"type": "function", "function": {"name": "search_filing"}}],
        )

    assert "tools" in captured_kwargs
    assert captured_kwargs["tools"][0]["function"]["name"] == "search_filing"


@pytest.mark.asyncio
async def test_call_groq_omits_tools_when_not_given():
    success_result = {"choices": [{"message": {"content": "ok"}}]}
    captured_kwargs = {}

    async def capture_create(**kwargs):
        captured_kwargs.update(kwargs)
        return success_result

    with patch.object(groq_client, "_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=capture_create)
        await groq_client.call_groq(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": "hi"}])

    assert "tools" not in captured_kwargs
```

Create `tests/test_async_generator.py`:

```python
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.async_generator import generate_query


def _fake_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )


@pytest.mark.asyncio
async def test_generate_query_parses_generator_response():
    section = {
        "document_id": "SEC_10K_TEST_2025",
        "section_header": "Item 7. MD&A",
        "node_ids": ["n1", "n2"],
        "content": "Total revenue was $100 million, up from $90 million.",
        "token_count": 20,
    }
    payload = {
        "query_text": "What was total revenue?",
        "ground_truth_answer": "$100 million",
        "gt_citations": ["n1"],
    }

    with patch(
        "dataset_generation.async_generator.groq_client.call_groq",
        new=AsyncMock(return_value=_fake_response(payload)),
    ) as mock_call:
        result = await generate_query(section, "Q1_Direct_Text")

    assert result["query_text"] == "What was total revenue?"
    assert result["ground_truth_answer"] == "$100 million"
    assert result["gt_citations"] == ["n1"]
    assert result["quadrant"] == "Q1_Direct_Text"
    assert result["document_id"] == "SEC_10K_TEST_2025"
    mock_call.assert_awaited_once()
    _, kwargs = mock_call.call_args
    assert kwargs["model"] == "openai/gpt-oss-120b"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_groq_client_backoff.py tests/test_async_generator.py -v`
Expected: `test_call_groq_passes_tools_through_when_given` FAILs with `TypeError: call_groq() got an unexpected keyword argument 'tools'`; the async_generator tests FAIL with `ModuleNotFoundError: No module named 'dataset_generation.async_generator'`.

- [ ] **Step 3: Write the implementation**

Modify `groq_client.py`, replacing the `call_groq` function (lines 34-40):

```python
@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)
async def call_groq(model: str, messages: list[dict], temperature: float = 0.0, tools: list[dict] | None = None):
    async with _semaphore:
        kwargs = {"model": model, "messages": messages, "temperature": temperature}
        if tools:
            kwargs["tools"] = tools
        return await _client.chat.completions.create(**kwargs)
```

Create `dataset_generation/async_generator.py`:

```python
"""Generator: proposes a query + ground truth + citations for one filing section.

Uses openai/gpt-oss-120b (config.MODEL_ROUTING["generator"]) -- a different
model family from the Critic (Task 6), per the anti-self-grading invariant.
"""
import json

import config
import groq_client

_QUADRANT_GUIDANCE = {
    "Q1_Direct_Text": "Ask a direct fact-retrieval question answerable from a single explicit statement in continuous prose.",
    "Q2_Implicit_Text": "Ask a question requiring synthesis across multiple narrative passages in this section (not a single sentence).",
    "Q3_Direct_Table": "Ask a question requiring exact extraction of a specific cell/value from a table in this section.",
    "Q4_Implicit_Table": "Ask a question requiring a calculation or cross-row/footnote inference using a table in this section.",
}

_SYSTEM_PROMPT = (
    "You are generating one benchmark question from a section of a SEC 10-K filing. "
    "Respond with ONLY a JSON object (no markdown fences, no commentary): "
    '{"query_text": "...", "ground_truth_answer": "...", "gt_citations": ["node_id", ...]}. '
    "gt_citations must only contain node_id values that were given to you in the section."
)


async def generate_query(section: dict, quadrant: str) -> dict:
    guidance = _QUADRANT_GUIDANCE[quadrant]
    user_content = (
        f"{guidance}\n\n"
        f"Section: {section['section_header']}\n"
        f"Available node_ids: {section['node_ids']}\n\n"
        f"Section content:\n{section['content']}"
    )

    response = await groq_client.call_groq(
        model=config.MODEL_ROUTING["generator"],
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    payload = json.loads(response.choices[0].message.content)

    return {
        "query_text": payload["query_text"],
        "ground_truth_answer": payload["ground_truth_answer"],
        "gt_citations": payload["gt_citations"],
        "quadrant": quadrant,
        "document_id": section["document_id"],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_groq_client_backoff.py tests/test_async_generator.py -v`
Expected: PASS (all tests, including the pre-existing two in `test_groq_client_backoff.py`).

- [ ] **Step 5: Commit**

```bash
git add groq_client.py tests/test_groq_client_backoff.py dataset_generation/async_generator.py tests/test_async_generator.py
git commit -m "feat: add tools param to call_groq and Phase 4 async Generator"
```

---

### Task 6: Async Critic (tool-calling loop)

**Files:**
- Create: `dataset_generation/async_critic.py`
- Test: `tests/test_async_critic.py`

**Interfaces:**
- Consumes: `groq_client.call_groq(model, messages, temperature=0.0, tools=None)` (Task 5), `dataset_generation.search_tool.SEARCH_TOOL_SCHEMA` + `search_filing_nodes` (Task 4), `config.MODEL_ROUTING["critic"]`.
- Produces (used by Task 7's orchestrator): `async def critique_query(query_text: str, all_nodes: list[dict]) -> dict` — returns `{cited_node_ids: list[str], computed_answer: str}`. Raises `RuntimeError` if the Critic doesn't produce a final answer within 5 tool-call rounds.

- [ ] **Step 1: Write the failing test**

Create `tests/test_async_critic.py`:

```python
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.async_critic import critique_query

_NODES = [
    {"node_id": "n1", "content": "Total revenue was $100 million in fiscal 2025."},
    {"node_id": "n2", "content": "The board of directors met quarterly."},
]


def _tool_call_response():
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="search_filing", arguments=json.dumps({"query": "total revenue"})),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool_call]))]
    )


def _final_response(payload: dict):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload), tool_calls=None))]
    )


@pytest.mark.asyncio
async def test_critique_query_uses_search_tool_then_answers():
    final_payload = {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}

    with patch(
        "dataset_generation.async_critic.groq_client.call_groq",
        new=AsyncMock(side_effect=[_tool_call_response(), _final_response(final_payload)]),
    ) as mock_call:
        result = await critique_query("What was total revenue?", _NODES)

    assert result == {"cited_node_ids": ["n1"], "computed_answer": "$100 million"}
    assert mock_call.await_count == 2
    _, kwargs = mock_call.call_args_list[0]
    assert kwargs["model"] == "qwen/qwen3.6-27b"
    assert kwargs["tools"][0]["function"]["name"] == "search_filing"


@pytest.mark.asyncio
async def test_critique_query_raises_after_max_rounds_without_final_answer():
    with patch(
        "dataset_generation.async_critic.groq_client.call_groq",
        new=AsyncMock(return_value=_tool_call_response()),
    ):
        with pytest.raises(RuntimeError, match="exceeded"):
            await critique_query("What was total revenue?", _NODES)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_async_critic.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dataset_generation.async_critic'`.

- [ ] **Step 3: Write the implementation**

Create `dataset_generation/async_critic.py`:

```python
"""Critic: independently re-derives an answer using a local search tool.

Uses qwen/qwen3.6-27b (config.MODEL_ROUTING["critic"]) -- a different model
family from the Generator (Task 5), per the anti-self-grading invariant.
Given only the query text (never the Generator's answer or citations), it
must search the filing itself before answering.
"""
import json

import config
import groq_client
from dataset_generation.search_tool import SEARCH_TOOL_SCHEMA, search_filing_nodes

_MAX_TOOL_ROUNDS = 5

_SYSTEM_PROMPT = (
    "You are a financial-filing fact-checker. You will be given a question about "
    "a SEC 10-K filing. You do not know the answer yet. Use the search_filing tool "
    "to find the relevant passages, then respond with ONLY a JSON object (no "
    'markdown fences, no commentary): {"cited_node_ids": ["node_id", ...], '
    '"computed_answer": "..."}. Cite only node_ids you actually found via search_filing.'
)


async def critique_query(query_text: str, all_nodes: list[dict]) -> dict:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": query_text},
    ]

    for _ in range(_MAX_TOOL_ROUNDS):
        response = await groq_client.call_groq(
            model=config.MODEL_ROUTING["critic"],
            messages=messages,
            tools=[SEARCH_TOOL_SCHEMA],
        )
        message = response.choices[0].message

        if getattr(message, "tool_calls", None):
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls,
            })
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                results = search_filing_nodes(all_nodes, args["query"])
                tool_output = json.dumps(
                    [{"node_id": r["node_id"], "content": r["content"]} for r in results]
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                })
            continue

        return json.loads(message.content)

    raise RuntimeError(f"Critic exceeded {_MAX_TOOL_ROUNDS} tool-call rounds without a final answer")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_async_critic.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add dataset_generation/async_critic.py tests/test_async_critic.py
git commit -m "feat: add Phase 4 async Critic with local search-tool loop"
```

---

### Task 7: Orchestrator (`run_dataset_generation.py`)

**Files:**
- Create: `dataset_generation/run_dataset_generation.py`
- Test: `tests/test_run_dataset_generation.py`

**Interfaces:**
- Consumes: `database_manager` (Task 1: `get_nodes_by_document`, `get_quadrant_counts`, `insert_query`, `insert_golden_query`, `insert_judge_validation`), `dataset_generation.section_grouper.group_sections` (Task 2), `dataset_generation.cross_check.check_query` (Task 3), `dataset_generation.async_generator.generate_query` (Task 5), `dataset_generation.async_critic.critique_query` (Task 6), `config.LOCAL_TEST_THROTTLE`, `config.THROTTLE_LIMIT`.
- Produces: `def next_target(counts: dict[str, dict[str, int]]) -> tuple[str, str] | None` (pure, unit-tested directly) and `async def main(db_path: str = "benchmark.db") -> None` (the live orchestrator, smoke-tested only under throttle).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_run_dataset_generation.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest

from dataset_generation.run_dataset_generation import main, next_target, _QUADRANTS, _TARGETS


def _empty_counts():
    return {
        table: {q: 0 for q in _QUADRANTS}
        for table in ("queries", "golden_queries", "judge_validation")
    }


def test_next_target_fills_queries_before_golden_before_judge():
    counts = _empty_counts()
    assert next_target(counts) == ("queries", "Q1_Direct_Text")


def test_next_target_moves_to_golden_queries_once_pq_full():
    counts = _empty_counts()
    counts["queries"]["Q1_Direct_Text"] = _TARGETS["queries"]
    assert next_target(counts) == ("golden_queries", "Q1_Direct_Text")


def test_next_target_moves_to_next_quadrant_once_all_three_full():
    counts = _empty_counts()
    counts["queries"]["Q1_Direct_Text"] = _TARGETS["queries"]
    counts["golden_queries"]["Q1_Direct_Text"] = _TARGETS["golden_queries"]
    counts["judge_validation"]["Q1_Direct_Text"] = _TARGETS["judge_validation"]
    assert next_target(counts) == ("queries", "Q2_Implicit_Text")


def test_next_target_returns_none_when_all_140_filled():
    counts = _empty_counts()
    for table in counts:
        for q in _QUADRANTS:
            counts[table][q] = _TARGETS[table]
    assert next_target(counts) is None


@pytest.mark.asyncio
async def test_main_smoke_runs_under_throttle(monkeypatch):
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.LOCAL_TEST_THROTTLE", True)
    monkeypatch.setattr("dataset_generation.run_dataset_generation.config.THROTTLE_LIMIT", 1)

    fake_nodes = [
        {
            "node_id": "n1",
            "document_id": "DOC_A",
            "parent_item_header": "Item 1A. Risk Factors",
            "node_type": "text",
            "source_page_num": 1,
            "content": "Total revenue was $100 million.",
            "token_count": 10,
        }
    ]

    with (
        patch("dataset_generation.run_dataset_generation.dbm.init_db", new=AsyncMock()),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_quadrant_counts",
            new=AsyncMock(return_value={q: 0 for q in _QUADRANTS}),
        ),
        patch(
            "dataset_generation.run_dataset_generation.dbm.get_nodes_by_document",
            new=AsyncMock(return_value=fake_nodes),
        ),
        patch("dataset_generation.run_dataset_generation.dbm.insert_query", new=AsyncMock()) as mock_insert,
        patch(
            "dataset_generation.run_dataset_generation.generate_query",
            new=AsyncMock(return_value={
                "query_text": "What was total revenue?",
                "ground_truth_answer": "$100 million",
                "gt_citations": ["n1"],
                "quadrant": "Q1_Direct_Text",
                "document_id": "DOC_A",
            }),
        ),
        patch(
            "dataset_generation.run_dataset_generation.critique_query",
            new=AsyncMock(return_value={"cited_node_ids": ["n1"], "computed_answer": "$100 million"}),
        ),
    ):
        await main(db_path="unused.db", document_ids=["DOC_A"])

    mock_insert.assert_awaited_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_run_dataset_generation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dataset_generation.run_dataset_generation'`.

- [ ] **Step 3: Write the implementation**

Create `dataset_generation/run_dataset_generation.py`:

```python
"""Orchestrator: fills queries/golden_queries/judge_validation to 140 total.

Resumable -- re-checks quadrant counts on every startup and skips already-full
quadrant/table slots, so a crash never re-spends Groq quota on accepted
queries (same resumability principle as Phase 3's build). LOCAL_TEST_THROTTLE
caps a run to THROTTLE_LIMIT sections total (Guardrails.md §7).
"""
import config
import database_manager as dbm
from dataset_generation.async_critic import critique_query
from dataset_generation.async_generator import generate_query
from dataset_generation.cross_check import check_query
from dataset_generation.section_grouper import group_sections

_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table")
_TABLE_ORDER = ("queries", "golden_queries", "judge_validation")
_TARGETS = {"queries": 25, "golden_queries": 5, "judge_validation": 5}
_MAX_ATTEMPTS_PER_SECTION = 3

_ALL_FILINGS = (
    "AAPL_2023", "AAPL_2024", "AAPL_2025",
    "MSFT_2023", "MSFT_2024", "MSFT_2025",
    "TSLA_2023", "TSLA_2024", "TSLA_2025",
)

_INSERTERS = {
    "queries": dbm.insert_query,
    "golden_queries": dbm.insert_golden_query,
    "judge_validation": dbm.insert_judge_validation,
}


def next_target(counts: dict[str, dict[str, int]]) -> tuple[str, str] | None:
    for quadrant in _QUADRANTS:
        for table in _TABLE_ORDER:
            if counts[table][quadrant] < _TARGETS[table]:
                return table, quadrant
    return None


async def _load_counts(db_path: str) -> dict[str, dict[str, int]]:
    return {table: await dbm.get_quadrant_counts(db_path, table) for table in _TABLE_ORDER}


async def _accept_query(db_path: str, table: str, generated: dict, query_index: int) -> None:
    query_id = f"{generated['quadrant']}_{table}_{query_index:04d}"
    row = {
        "query_id": query_id,
        "quadrant": generated["quadrant"],
        "query_text": generated["query_text"],
        "ground_truth_answer": generated["ground_truth_answer"],
        "gt_citations": generated["gt_citations"],
        "document_id": generated["document_id"],
    }
    if table == "golden_queries":
        row.update({
            "example_output": generated["ground_truth_answer"],
            "human_score": 1,
            "human_reasoning": "PENDING_HUMAN_LABEL",
        })
    await _INSERTERS[table](db_path, row)


async def main(db_path: str = "benchmark.db", document_ids: tuple[str, ...] | None = None) -> None:
    await dbm.init_db(db_path)
    document_ids = document_ids or _ALL_FILINGS
    max_sections = config.THROTTLE_LIMIT if config.LOCAL_TEST_THROTTLE else None

    sections_processed = 0
    query_index = 0

    for document_id in document_ids:
        nodes = await dbm.get_nodes_by_document(db_path, document_id)
        sections = group_sections(nodes)

        for section in sections:
            if max_sections is not None and sections_processed >= max_sections:
                return

            counts = await _load_counts(db_path)
            target = next_target(counts)
            if target is None:
                return
            table, quadrant = target

            for _attempt in range(_MAX_ATTEMPTS_PER_SECTION):
                generated = await generate_query(section, quadrant)
                critic_result = await critique_query(generated["query_text"], nodes)
                accepted = check_query(
                    gt_citations=generated["gt_citations"],
                    gt_answer=generated["ground_truth_answer"],
                    critic_cited_ids=critic_result["cited_node_ids"],
                    critic_answer=critic_result["computed_answer"],
                )
                if accepted:
                    query_index += 1
                    await _accept_query(db_path, table, generated, query_index)
                    break

            sections_processed += 1


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_run_dataset_generation.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add dataset_generation/run_dataset_generation.py tests/test_run_dataset_generation.py
git commit -m "feat: add Phase 4 orchestrator with resumable quadrant-fill logic"
```

---

### Task 8: GQ human-labeling export/import

**Files:**
- Create: `dataset_generation/gq_label_export.py`
- Create: `dataset_generation/gq_label_import.py`
- Test: `tests/test_gq_labeling.py`

**Interfaces:**
- Consumes: `database_manager.get_golden_queries` / `update_golden_query_labels` (Task 1).
- Produces: `def render_label_markdown(golden_queries: list[dict]) -> str` (pure, used by `gq_label_export.py`'s `main`), `def parse_label_markdown(markdown_text: str) -> list[dict]` (pure, returns `[{query_id, human_score, human_reasoning}, ...]`, used by `gq_label_import.py`'s `main`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_gq_labeling.py`:

```python
from dataset_generation.gq_label_export import render_label_markdown
from dataset_generation.gq_label_import import parse_label_markdown

_GOLDEN = [
    {
        "query_id": "Q1_GQ_0001",
        "quadrant": "Q1_Direct_Text",
        "query_text": "What was total revenue?",
        "ground_truth_answer": "$100 million",
        "gt_citations": ["n1"],
        "document_id": "AAPL_2023",
    },
]


def test_render_label_markdown_includes_query_and_blank_fields():
    md = render_label_markdown(_GOLDEN)
    assert "Q1_GQ_0001" in md
    assert "What was total revenue?" in md
    assert "$100 million" in md
    assert "Score (1-10):" in md
    assert "Why this answer is good:" in md


def test_parse_label_markdown_round_trips_filled_fields():
    filled = """## Q1_GQ_0001

**Quadrant:** Q1_Direct_Text
**Document:** AAPL_2023
**Query:** What was total revenue?
**Ground truth:** $100 million

**Score (1-10):** 9
**Why this answer is good:** Unambiguous single-fact retrieval, directly stated.

---
"""
    parsed = parse_label_markdown(filled)
    assert parsed == [{
        "query_id": "Q1_GQ_0001",
        "human_score": 9,
        "human_reasoning": "Unambiguous single-fact retrieval, directly stated.",
    }]


def test_parse_label_markdown_skips_unfilled_entries():
    unfilled = """## Q1_GQ_0001

**Quadrant:** Q1_Direct_Text
**Document:** AAPL_2023
**Query:** What was total revenue?
**Ground truth:** $100 million

**Score (1-10):**
**Why this answer is good:**

---
"""
    assert parse_label_markdown(unfilled) == []


def test_parse_label_markdown_handles_multiple_entries_without_bleeding():
    two_entries = """## Q1_GQ_0001

**Quadrant:** Q1_Direct_Text
**Document:** AAPL_2023
**Query:** What was total revenue?
**Ground truth:** $100 million

**Score (1-10):** 9
**Why this answer is good:** Unambiguous single-fact retrieval, directly stated.

---

## Q3_GQ_0002

**Quadrant:** Q3_Direct_Table
**Document:** MSFT_2024
**Query:** What was total operating expenses?
**Ground truth:** $52,866 million

**Score (1-10):** 7
**Why this answer is good:** Clean cell extraction, single correct value.

---
"""
    parsed = parse_label_markdown(two_entries)
    assert parsed == [
        {
            "query_id": "Q1_GQ_0001",
            "human_score": 9,
            "human_reasoning": "Unambiguous single-fact retrieval, directly stated.",
        },
        {
            "query_id": "Q3_GQ_0002",
            "human_score": 7,
            "human_reasoning": "Clean cell extraction, single correct value.",
        },
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_gq_labeling.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dataset_generation.gq_label_export'`.

- [ ] **Step 3: Write the implementation**

Create `dataset_generation/gq_label_export.py`:

```python
"""Writes golden_queries_to_label.md so the researcher can hand-write the
'why this answer is good' note + 1-10 score for each of the 20 GQ
(Phase Plan.md Phase 4 Goal 5). This is the only manual step in Phase 4."""
import asyncio

import database_manager as dbm


def render_label_markdown(golden_queries: list[dict]) -> str:
    parts = ["# Golden Queries -- Human Labeling\n"]
    for gq in golden_queries:
        parts.append(
            f"## {gq['query_id']}\n\n"
            f"**Quadrant:** {gq['quadrant']}\n"
            f"**Document:** {gq['document_id']}\n"
            f"**Query:** {gq['query_text']}\n"
            f"**Ground truth:** {gq['ground_truth_answer']}\n\n"
            f"**Score (1-10):** \n"
            f"**Why this answer is good:** \n\n"
            f"---\n"
        )
    return "\n".join(parts)


async def main(db_path: str = "benchmark.db", out_path: str = "golden_queries_to_label.md") -> None:
    golden_queries = await dbm.get_golden_queries(db_path)
    markdown = render_label_markdown(golden_queries)
    with open(out_path, "w") as f:
        f.write(markdown)
    print(f"Wrote {len(golden_queries)} golden queries to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
```

Create `dataset_generation/gq_label_import.py`:

```python
"""Reads the filled-in golden_queries_to_label.md back into golden_queries."""
import asyncio
import re

import database_manager as dbm

_ENTRY_RE = re.compile(
    r"^## (?P<query_id>\S+)\n\n"
    r".*?"
    r"\*\*Score \(1-10\):\*\*\s*(?P<score>\S+)?\s*\n"
    r"\*\*Why this answer is good:\*\*\s*(?P<reasoning>.*?)\s*\n",
    re.DOTALL | re.MULTILINE,
)


def parse_label_markdown(markdown_text: str) -> list[dict]:
    results = []
    for match in _ENTRY_RE.finditer(markdown_text):
        score_raw = match.group("score")
        reasoning = (match.group("reasoning") or "").strip()
        if not score_raw or not reasoning:
            continue
        try:
            score = int(score_raw)
        except ValueError:
            continue
        results.append({
            "query_id": match.group("query_id"),
            "human_score": score,
            "human_reasoning": reasoning,
        })
    return results


async def main(db_path: str = "benchmark.db", in_path: str = "golden_queries_to_label.md") -> None:
    with open(in_path) as f:
        markdown_text = f.read()

    labels = parse_label_markdown(markdown_text)
    for label in labels:
        await dbm.update_golden_query_labels(
            db_path, label["query_id"], label["human_score"], label["human_reasoning"]
        )
    print(f"Imported {len(labels)} human labels from {in_path}")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_gq_labeling.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add dataset_generation/gq_label_export.py dataset_generation/gq_label_import.py tests/test_gq_labeling.py
git commit -m "feat: add GQ human-labeling export/import tooling"
```

---

## After All Tasks: Full Test Suite + Throttled Live Smoke Run

- [ ] Run the complete test suite: `.venv/bin/python -m pytest -q` -- expect all tests passing (previous 49 + this plan's new tests), zero live Groq calls.
- [ ] With `LOCAL_TEST_THROTTLE=true` (the `.env` default), run `.venv/bin/python -m dataset_generation.run_dataset_generation` once live against real Groq -- verify it processes exactly `THROTTLE_LIMIT` (3) sections, inserts at most 3 accepted queries, and does not crash. Confirm via `sqlite3 benchmark.db "SELECT quadrant, COUNT(*) FROM queries GROUP BY quadrant"` that counts look sane.
- [ ] Only after the throttled run is clean: consider flipping `LOCAL_TEST_THROTTLE` for the full 140-query run -- this is a real Groq-quota-spending decision and must be confirmed with the user first, same as Phase 2/3's full-run gate.
