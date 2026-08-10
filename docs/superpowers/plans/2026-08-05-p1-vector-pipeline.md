# P1 Vector Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build P1, the semantic vector retrieval pipeline (Architecture.md §6, Phase 5) — a local Chroma-backed index over every filing's `nodes`, retrieved via `bge-small-en-v1.5` embeddings + a `bge-reranker-base` cross-encoder reranker, filtered to one `document_id` per query.

**Architecture:** A one-time build script embeds every row in the `nodes` table into one shared Chroma collection (`storage/chroma/`), metadata-tagged by `document_id`. At query time, `P1VectorRetriever.retrieve(query_text, document_id, k)` pulls a wider metadata-filtered candidate set from Chroma, then a local cross-encoder reranker narrows it to `k`. Both embedding and reranking run fully locally via `fastembed` (ONNX Runtime) — no LLM call anywhere in P1.

**Tech Stack:** `chromadb` (persistent local vector store), `llama-index-vector-stores-chroma`, `llama-index-embeddings-fastembed` (wraps `fastembed.TextEmbedding`), `fastembed.rerank.cross_encoder.TextCrossEncoder` (wrapped in a small custom `BaseNodePostprocessor` — no official `llama-index-postprocessor-fastembed` package exists on PyPI, confirmed via `uv pip install --dry-run`).

## Global Constraints

- **Local only, no LLM calls in P1** — Guardrails.md: "Retrieval/indexing runs locally: FAISS/ChromaDB (P1)." Embeddings and reranking both run via `fastembed` (already the project's established substitute for `sentence-transformers`/`FlagEmbedding`, which have no `torch` wheel for this machine — see `resources/research/deviations.md` entry 9/13).
- **`document_id` filtering is required, not banned** — Architecture.md §0 Decision 2: "Retrieval scope: per document, not cross-corpus... this is *not* the metadata pre-filter Guardrails.md bans — that ban is about narrowing to a target *section* using answer-derived information." Every `retrieve()` call must filter to exactly the query's own `document_id` and never see another filing's nodes (Decision §0.2, `Retriever` ABC contract in Architecture.md §4.1).
- **No section/quadrant/answer-location pre-filter** — only `document_id` scoping is applied; nothing about the query's target section, quadrant, or node_type may influence retrieval (Project_Idea.md §7/§10 — this is the leakage boundary that keeps P1 comparable to P2/P3).
- **Model names, exact, from spec:** embeddings `BAAI/bge-small-en-v1.5` (Project_Idea.md, Architecture.md §5), reranker `BAAI/bge-reranker-base` (Project_Idea.md §4, Phase Plan.md §5.1).
- **`LOCAL_TEST_THROTTLE` pattern required** for the build script loop, reusing `loop_template.apply_throttle()` — same pattern as `build_summary_index.py` (Guardrails.md §7).
- **Resumable build, skip-if-cached** — matches the existing P3 pattern (`is_built()`/skip), not incremental checkpointing mid-document.
- **Out of scope for this plan:** `pipelines/answerer.py` and `loop_executor.py` (Architecture.md §6 Phase 5) are shared across P1/P2/P3 and are a separate plan — this plan delivers `Retriever.retrieve()` for P1 only, independently testable without an Answerer.

---

## File Structure

- `project/pipelines/base.py` — new. `Retriever` ABC (Architecture.md §4.1), shared by P1 now and P2/P3 later.
- `project/pipelines/vector/__init__.py` — new, empty (package marker, matches `pipelines/structural/__init__.py`).
- `project/pipelines/vector/fastembed_reranker.py` — new. `FastEmbedReranker`, a `BaseNodePostprocessor` wrapping `TextCrossEncoder("BAAI/bge-reranker-base")`. Standalone and testable without Chroma.
- `project/pipelines/vector/build_vector_index.py` — new. One-time build script: reads all `nodes` from the DB, embeds and upserts into the shared Chroma collection at `storage/chroma/`, skips a `document_id` already present.
- `project/pipelines/vector/p1_vector.py` — new. `P1VectorRetriever(Retriever)` — the query-time class.
- `project/tests/test_base_retriever.py` — new.
- `project/tests/test_fastembed_reranker.py` — new.
- `project/tests/test_build_vector_index.py` — new.
- `project/tests/test_p1_vector.py` — new.
- `project/pyproject.toml` — modify: add `chromadb`, `llama-index-vector-stores-chroma`, `llama-index-embeddings-fastembed` to `dependencies`.

---

### Task 1: Add dependencies

**Files:**
- Modify: `project/pyproject.toml:8-17` (the `dependencies` list)

**Interfaces:**
- Produces: `chromadb`, `llama_index.vector_stores.chroma.ChromaVectorStore`, `llama_index.embeddings.fastembed.FastEmbedEmbedding`, `fastembed.rerank.cross_encoder.TextCrossEncoder` all importable for later tasks.

- [ ] **Step 1: Install the three new packages**

Run from `project/`:
```bash
uv add chromadb llama-index-vector-stores-chroma llama-index-embeddings-fastembed
```
Expected: `pyproject.toml`'s `dependencies` list gains the three entries (uv edits it automatically); `uv.lock` updates.

- [ ] **Step 2: Verify no `torch` was pulled in**

```bash
uv pip list 2>&1 | grep -i torch
```
Expected: no output. `chromadb`, `llama-index-vector-stores-chroma`, and `llama-index-embeddings-fastembed` (which wraps `fastembed`, ONNX-based) do not depend on `torch`. This preserves the constraint from `resources/research/deviations.md` entry 9/13 (no `torch` wheel for macOS x86_64 + Python 3.13 on this machine).

- [ ] **Step 3: Verify imports work**

```bash
uv run python -c "
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
print('all imports OK')
"
```
Expected: `all imports OK`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add chromadb/fastembed vector-store dependencies for P1"
```

---

### Task 2: `Retriever` ABC

**Files:**
- Create: `project/pipelines/base.py`
- Test: `project/tests/test_base_retriever.py`

**Interfaces:**
- Produces: `class Retriever(ABC)` with abstract method `retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]`. This is the exact signature from Architecture.md §4.1 that P1 (this plan), and later P2/P3, must implement.

- [ ] **Step 1: Write the failing test**

```python
# project/tests/test_base_retriever.py
import pytest
from llama_index.core.schema import NodeWithScore

from pipelines.base import Retriever


def test_retriever_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Retriever()


def test_concrete_subclass_must_implement_retrieve():
    class Incomplete(Retriever):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_concrete_subclass_with_retrieve_can_be_instantiated_and_called():
    class Dummy(Retriever):
        def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]:
            return []

    instance = Dummy()
    assert instance.retrieve("q", "AAPL_2023", 5) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd project && uv run pytest tests/test_base_retriever.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.base'`

- [ ] **Step 3: Write minimal implementation**

```python
# project/pipelines/base.py
"""Shared retriever interface for P1/P2/P3 (Architecture.md §4.1).

Every retrieval pipeline implements retrieve(), which must filter to the
given document_id internally and never return nodes from another filing
(Architecture.md §0 Decision 2 -- per-document retrieval scope, not a
banned metadata pre-filter, since document_id is a property of the query
itself, not an answer-location hint).
"""
from abc import ABC, abstractmethod

from llama_index.core.schema import NodeWithScore


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd project && uv run pytest tests/test_base_retriever.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add pipelines/base.py tests/test_base_retriever.py
git commit -m "feat: add shared Retriever ABC for P1/P2/P3"
```

---

### Task 3: `FastEmbedReranker` postprocessor

**Files:**
- Create: `project/pipelines/vector/__init__.py` (empty)
- Create: `project/pipelines/vector/fastembed_reranker.py`
- Test: `project/tests/test_fastembed_reranker.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `class FastEmbedReranker(BaseNodePostprocessor)`, constructor `FastEmbedReranker(model_name: str = "BAAI/bge-reranker-base", top_n: int | None = None)`, method `postprocess_nodes(nodes: list[NodeWithScore], query_str: str) -> list[NodeWithScore]` (inherited from `BaseNodePostprocessor`, calls `_postprocess_nodes` internally) — returns nodes re-scored and sorted descending by reranker score, truncated to `top_n` if set. Task 5 (`p1_vector.py`) instantiates this and calls `.postprocess_nodes(candidates, query_str=query_text)`.

- [ ] **Step 1: Write the failing test**

```python
# project/tests/test_fastembed_reranker.py
from llama_index.core.schema import NodeWithScore, TextNode

from pipelines.vector.fastembed_reranker import FastEmbedReranker


def _node(node_id: str, text: str) -> NodeWithScore:
    return NodeWithScore(node=TextNode(id_=node_id, text=text), score=0.0)


def test_reranks_by_relevance_to_query():
    reranker = FastEmbedReranker()
    nodes = [
        _node("n1", "The weather today is sunny with a chance of rain."),
        _node("n2", "Apple reported total net sales of $394.3 billion in fiscal 2023."),
        _node("n3", "The cat sat on the mat."),
    ]

    result = reranker.postprocess_nodes(nodes, query_str="What were Apple's total net sales?")

    assert len(result) == 3
    assert result[0].node.node_id == "n2"
    # scores must be set and sorted descending
    assert all(result[i].score >= result[i + 1].score for i in range(len(result) - 1))


def test_top_n_truncates_result():
    reranker = FastEmbedReranker(top_n=1)
    nodes = [
        _node("n1", "Irrelevant text about weather."),
        _node("n2", "Apple's total net sales were $394.3 billion."),
    ]

    result = reranker.postprocess_nodes(nodes, query_str="What were Apple's total net sales?")

    assert len(result) == 1
    assert result[0].node.node_id == "n2"


def test_empty_nodes_returns_empty():
    reranker = FastEmbedReranker()
    assert reranker.postprocess_nodes([], query_str="anything") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd project && uv run pytest tests/test_fastembed_reranker.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.vector'`

- [ ] **Step 3: Write minimal implementation**

```python
# project/pipelines/vector/__init__.py
```

```python
# project/pipelines/vector/fastembed_reranker.py
"""Cross-encoder reranker for P1, backed by fastembed's ONNX TextCrossEncoder.

No official llama-index postprocessor package wraps fastembed's reranker
(confirmed absent from PyPI), so this is a small custom
BaseNodePostprocessor -- the same fastembed-over-torch substitution already
used project-wide for BAAI/bge-small-en-v1.5 (see
resources/research/deviations.md entry 9/13), applied here to
BAAI/bge-reranker-base.
"""
from typing import Optional

from fastembed.rerank.cross_encoder import TextCrossEncoder
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle


class FastEmbedReranker(BaseNodePostprocessor):
    model_name: str = "BAAI/bge-reranker-base"
    top_n: Optional[int] = None

    _model: TextCrossEncoder = PrivateAttr()

    def __init__(self, model_name: str = "BAAI/bge-reranker-base", top_n: Optional[int] = None, **kwargs):
        super().__init__(model_name=model_name, top_n=top_n, **kwargs)
        self._model = TextCrossEncoder(model_name=model_name)

    @classmethod
    def class_name(cls) -> str:
        return "FastEmbedReranker"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> list[NodeWithScore]:
        if not nodes or query_bundle is None:
            return nodes

        texts = [node.node.get_content() for node in nodes]
        scores = list(self._model.rerank(query_bundle.query_str, texts))

        for node, score in zip(nodes, scores):
            node.score = float(score)

        ranked = sorted(nodes, key=lambda n: n.score, reverse=True)
        return ranked[: self.top_n] if self.top_n is not None else ranked
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd project && uv run pytest tests/test_fastembed_reranker.py -v`
Expected: PASS (3 passed). If `PrivateAttr` import path or `BaseNodePostprocessor`'s constructor signature differs from the installed `llama-index-core==0.14.23` API, adjust the import to match (`uv run python -c "from llama_index.core.postprocessor.types import BaseNodePostprocessor; help(BaseNodePostprocessor)"` to check) — the test is the source of truth, not this snippet.

- [ ] **Step 5: Commit**

```bash
git add pipelines/vector/__init__.py pipelines/vector/fastembed_reranker.py tests/test_fastembed_reranker.py
git commit -m "feat: add fastembed-backed cross-encoder reranker for P1"
```

---

### Task 4: Vector index build script

**Files:**
- Create: `project/pipelines/vector/build_vector_index.py`
- Test: `project/tests/test_build_vector_index.py`

**Interfaces:**
- Consumes: `database_manager.get_nodes_by_document(db_path, document_id)` (existing, returns `list[dict]` with keys `node_id, document_id, parent_item_header, node_type, source_page_num, content, token_count`), `pipelines.structural.node_convert.nodes_to_llama_nodes(nodes: list[dict]) -> list[TextNode]` (existing, reused as-is — same node-dict-to-`TextNode` mapping P3 already uses).
- Produces: `is_document_indexed(document_id: str, storage_root: Path = STORAGE_ROOT) -> bool`; `build_index_for_document(document_id: str, db_path: str = DB_PATH, storage_root: Path = STORAGE_ROOT) -> dict` returning `{"document_id": ..., "skipped": bool, "node_count": int}`; `main()` iterating `data/filings_manifest.json` under `loop_template.apply_throttle()`. `p1_vector.py` (Task 5) opens the same Chroma collection this script writes to.

- [ ] **Step 1: Write the failing test**

```python
# project/tests/test_build_vector_index.py
from unittest.mock import AsyncMock, patch

import pytest

import pipelines.vector.build_vector_index as bvi


@pytest.mark.asyncio
async def test_build_index_for_document_embeds_and_indexes_nodes(tmp_path, monkeypatch):
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)

    fake_nodes = [
        {"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
         "parent_item_header": None, "node_type": "text",
         "source_page_num": 1, "content": "Total net sales were $394.3 billion.",
         "token_count": 8},
        {"node_id": "AAPL_2025_n0002", "document_id": "AAPL_2025",
         "parent_item_header": None, "node_type": "text",
         "source_page_num": 2, "content": "Gross margin was 44 percent.",
         "token_count": 6},
    ]

    with patch.object(bvi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)):
        result = await bvi.build_index_for_document("AAPL_2025")

    assert result == {"document_id": "AAPL_2025", "skipped": False, "node_count": 2}
    assert bvi.is_document_indexed("AAPL_2025", storage_root=tmp_path) is True


@pytest.mark.asyncio
async def test_build_index_for_document_skips_if_already_indexed(tmp_path, monkeypatch):
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)

    fake_nodes = [
        {"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
         "parent_item_header": None, "node_type": "text",
         "source_page_num": 1, "content": "Total net sales were $394.3 billion.",
         "token_count": 8},
    ]

    with patch.object(bvi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)):
        first = await bvi.build_index_for_document("AAPL_2025")
        assert first["skipped"] is False

        second = await bvi.build_index_for_document("AAPL_2025")
        assert second == {"document_id": "AAPL_2025", "skipped": True, "node_count": 0}


@pytest.mark.asyncio
async def test_build_index_for_document_raises_on_no_nodes(tmp_path, monkeypatch):
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)

    with patch.object(bvi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=[])):
        with pytest.raises(ValueError):
            await bvi.build_index_for_document("MSFT_2025")


def test_is_document_indexed_false_for_empty_collection(tmp_path):
    assert bvi.is_document_indexed("AAPL_2025", storage_root=tmp_path) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd project && uv run pytest tests/test_build_vector_index.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.vector.build_vector_index'`

- [ ] **Step 3: Write minimal implementation**

```python
# project/pipelines/vector/build_vector_index.py
"""Builds the shared P1 vector index (Phase 5) -- one Chroma collection,
metadata-tagged by document_id, covering every filing's nodes.

Fully local: embeddings via fastembed (BAAI/bge-small-en-v1.5), no LLM
call, per Guardrails.md's "Retrieval/indexing runs locally" rule.
Resumable at document granularity, matching build_summary_index.py's
skip-if-already-built pattern.
"""
import asyncio
import json
from pathlib import Path

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

import database_manager as dbm
import loop_template
from pipelines.structural.node_convert import nodes_to_llama_nodes

STORAGE_ROOT = Path("storage/chroma")
COLLECTION_NAME = "p1_vector"
DB_PATH = "benchmark.db"
MANIFEST_PATH = "data/filings_manifest.json"
_EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"


def _get_collection(storage_root: Path = STORAGE_ROOT):
    client = chromadb.PersistentClient(path=str(storage_root))
    return client.get_or_create_collection(COLLECTION_NAME)


def is_document_indexed(document_id: str, storage_root: Path = STORAGE_ROOT) -> bool:
    collection = _get_collection(storage_root)
    existing = collection.get(where={"document_id": document_id}, limit=1)
    return len(existing["ids"]) > 0


async def build_index_for_document(
    document_id: str,
    db_path: str = DB_PATH,
    storage_root: Path = STORAGE_ROOT,
) -> dict:
    if is_document_indexed(document_id, storage_root=storage_root):
        return {"document_id": document_id, "skipped": True, "node_count": 0}

    nodes = await dbm.get_nodes_by_document(db_path, document_id)
    if not nodes:
        raise ValueError(
            f"No nodes found for document_id={document_id!r} -- this filing "
            "has not been ingested yet (Phase 2). Refusing to index nothing, "
            "which would leave is_document_indexed() permanently False for "
            "a real gap vs a not-yet-run build."
        )

    llama_nodes = nodes_to_llama_nodes(nodes)
    collection = _get_collection(storage_root)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = FastEmbedEmbedding(model_name=_EMBED_MODEL_NAME)

    VectorStoreIndex(
        nodes=llama_nodes,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    return {"document_id": document_id, "skipped": False, "node_count": len(nodes)}


async def main():
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    manifest = loop_template.apply_throttle(manifest)

    for entry in manifest:
        document_id = entry["document_id"]
        result = await build_index_for_document(document_id)
        status = "skipped (cached)" if result["skipped"] else f"indexed ({result['node_count']} nodes)"
        print(f"{document_id}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd project && uv run pytest tests/test_build_vector_index.py -v`
Expected: PASS (4 passed). `chromadb.PersistentClient` creates real on-disk state under `tmp_path` — no mocking of Chroma itself needed since it's pure-local/fast.

- [ ] **Step 5: Commit**

```bash
git add pipelines/vector/build_vector_index.py tests/test_build_vector_index.py
git commit -m "feat: add P1 vector index build script (Chroma + fastembed)"
```

---

### Task 5: `P1VectorRetriever`

**Files:**
- Create: `project/pipelines/vector/p1_vector.py`
- Test: `project/tests/test_p1_vector.py`

**Interfaces:**
- Consumes: `pipelines.base.Retriever` (Task 2), `pipelines.vector.fastembed_reranker.FastEmbedReranker` (Task 3), `pipelines.vector.build_vector_index.STORAGE_ROOT`/`COLLECTION_NAME`/`_EMBED_MODEL_NAME`/`_get_collection` (Task 4) — same collection this class queries against must be the one Task 4 built.
- Produces: `class P1VectorRetriever(Retriever)`, `retrieve(query_text: str, document_id: str, k: int) -> list[NodeWithScore]`. This is the deliverable of the whole plan — the class `loop_executor.py` (future plan) will instantiate for P1.

- [ ] **Step 1: Write the failing test**

```python
# project/tests/test_p1_vector.py
import chromadb
import pytest
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from pipelines.vector.p1_vector import P1VectorRetriever


def _seed_collection(storage_root, collection_name):
    client = chromadb.PersistentClient(path=str(storage_root))
    collection = client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

    nodes = [
        TextNode(
            id_="AAPL_2025_n0001",
            text="Apple's total net sales were $394.3 billion in fiscal 2025.",
            metadata={"document_id": "AAPL_2025"},
        ),
        TextNode(
            id_="AAPL_2025_n0002",
            text="Apple's research and development expense grew 10 percent.",
            metadata={"document_id": "AAPL_2025"},
        ),
        TextNode(
            id_="MSFT_2025_n0001",
            text="Microsoft's total revenue was $245 billion in fiscal 2025.",
            metadata={"document_id": "MSFT_2025"},
        ),
    ]
    VectorStoreIndex(nodes=nodes, storage_context=storage_context, embed_model=embed_model)


def test_retrieve_filters_to_given_document_id(tmp_path, monkeypatch):
    import pipelines.vector.build_vector_index as bvi
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)
    _seed_collection(tmp_path, bvi.COLLECTION_NAME)

    retriever = P1VectorRetriever(storage_root=tmp_path)
    results = retriever.retrieve("What were total net sales?", document_id="AAPL_2025", k=5)

    assert len(results) > 0
    assert all(node.node.metadata["document_id"] == "AAPL_2025" for node in results)
    node_ids = {node.node.node_id for node in results}
    assert "MSFT_2025_n0001" not in node_ids


def test_retrieve_respects_k(tmp_path, monkeypatch):
    import pipelines.vector.build_vector_index as bvi
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)
    _seed_collection(tmp_path, bvi.COLLECTION_NAME)

    retriever = P1VectorRetriever(storage_root=tmp_path)
    results = retriever.retrieve("What were total net sales?", document_id="AAPL_2025", k=1)

    assert len(results) == 1


def test_retrieve_returns_most_relevant_node_first(tmp_path, monkeypatch):
    import pipelines.vector.build_vector_index as bvi
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)
    _seed_collection(tmp_path, bvi.COLLECTION_NAME)

    retriever = P1VectorRetriever(storage_root=tmp_path)
    results = retriever.retrieve("What were Apple's total net sales?", document_id="AAPL_2025", k=2)

    assert results[0].node.node_id == "AAPL_2025_n0001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd project && uv run pytest tests/test_p1_vector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipelines.vector.p1_vector'`

- [ ] **Step 3: Write minimal implementation**

```python
# project/pipelines/vector/p1_vector.py
"""P1: semantic vector retrieval (Architecture.md §6 Phase 5).

Filters to the query's own document_id (required, not the banned
metadata pre-filter -- see Architecture.md Decision 0.2), then reranks a
wider Chroma candidate set down to k with a local cross-encoder. No LLM
call anywhere in this class.
"""
from pathlib import Path
from typing import Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import (
    ExactMatchFilter,
    MetadataFilters,
)
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from pipelines.base import Retriever
from pipelines.vector.build_vector_index import (
    STORAGE_ROOT,
    _EMBED_MODEL_NAME,
    _get_collection,
)
from pipelines.vector.fastembed_reranker import FastEmbedReranker

_PREFETCH_MULTIPLIER = 4
_MIN_PREFETCH = 20


class P1VectorRetriever(Retriever):
    def __init__(self, storage_root: Path = STORAGE_ROOT):
        collection = _get_collection(storage_root)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        embed_model = FastEmbedEmbedding(model_name=_EMBED_MODEL_NAME)
        self._index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
        self._reranker = FastEmbedReranker()

    def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]:
        prefetch_k = max(k * _PREFETCH_MULTIPLIER, _MIN_PREFETCH)
        filters = MetadataFilters(filters=[ExactMatchFilter(key="document_id", value=document_id)])
        base_retriever = self._index.as_retriever(similarity_top_k=prefetch_k, filters=filters)
        candidates = base_retriever.retrieve(query_text)
        reranked = self._reranker.postprocess_nodes(candidates, query_str=query_text)
        return reranked[:k]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd project && uv run pytest tests/test_p1_vector.py -v`
Expected: PASS (3 passed). If `MetadataFilters`/`ExactMatchFilter` import paths differ in the installed `llama-index-core==0.14.23` (some versions moved these to `llama_index.core.vector_stores.types`), adjust the import — verify with `uv run python -c "from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters; print('ok')"` first.

- [ ] **Step 5: Commit**

```bash
git add pipelines/vector/p1_vector.py tests/test_p1_vector.py
git commit -m "feat: implement P1VectorRetriever (Chroma + fastembed reranker)"
```

---

### Task 6: Full-suite regression check

**Files:**
- None modified — verification only.

- [ ] **Step 1: Run the entire test suite**

Run: `cd project && uv run pytest -q`
Expected: all previously-passing tests still pass, plus the new tests from Tasks 2-5 (13 new tests total). No regressions in `test_build_summary_index.py`, `test_run_dataset_generation.py`, etc. — this task touched no shared files besides `pyproject.toml`.

- [ ] **Step 2: Confirm no accidental network/LLM calls**

```bash
grep -rn "GROQ_API_KEY\|NIM_API_KEY\|llm_client" pipelines/vector/
```
Expected: no output — confirms P1's build and retrieval path never imports `llm_client`, matching the "no LLM call in P1" constraint.

---

## Verification (end-to-end, manual)

Not part of the automated test suite — run once after all tasks land, against real ingested data (`AAPL_2025` is already ingested per Phase 2):

```bash
cd project
uv run python -c "
import asyncio
from pipelines.vector.build_vector_index import build_index_for_document

async def main():
    result = await build_index_for_document('AAPL_2025')
    print(result)

asyncio.run(main())
"
uv run python -c "
from pipelines.vector.p1_vector import P1VectorRetriever

retriever = P1VectorRetriever()
results = retriever.retrieve('What were total net sales?', document_id='AAPL_2025', k=5)
for r in results:
    print(round(r.score, 4), r.node.node_id, r.node.get_content()[:80])
"
```
Expected: 5 nodes printed, all from `AAPL_2025`, ordered by descending reranker score, with the most relevant-looking node about net sales near the top.
