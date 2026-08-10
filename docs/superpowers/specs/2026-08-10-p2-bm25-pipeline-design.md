# P2 BM25 Pipeline — Design

**Branch:** `phase5-pipeline2-bm25`, branched from `phase5-pipeline-implementation` (== `phase4-dataset-generation` tip), then locally merged forward to include `phase5-pipeline1-vector`'s `pipelines/base.py` (Retriever ABC) and `conftest.py`. Not pushed.

## Goal

Implement P2, the statistical retrieval pipeline, per `resources/specs/Project Idea.md` §6 and `resources/specs/Architecture.md` §4.1/§6. Deterministic, local, zero LLM calls at retrieval time.

## Spec constraints (binding, copied verbatim from source docs)

- **Library:** `rank_bm25`, `BM25Okapi` class specifically (Project Idea.md §6: "the statistical Okapi BM25 algorithm"). `LlamaIndex`'s `KeywordTableIndex` is explicitly rejected — it calls an LLM, breaking the statistical/deterministic contract (CLAUDE.md §4, Project Idea.md §6).
- **Tokenizer (Project Idea.md §6, decisive and custom):**
  - preserves numbers, decimals, `%`, and currency tokens
  - strips table-markdown pipes (`|`) but keeps cell values
  - applies no stemming
  - **used identically at index time and query time** — one function, both call sites
- **Retriever contract** (`Architecture.md` §4.1, same ABC as P1/P3):
  ```python
  class Retriever(ABC):
      def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]: ...
  ```
  Must filter to `document_id` internally; never search cross-corpus (Architecture.md §0 Decision 2).
- **Storage:** `storage/bm25/` (Architecture.md §2.2 deployment view), pickled corpora.
- **Resumability:** per-document, matching P1 (`build_vector_index.py`) and P3 (`build_summary_index.py`)'s skip-if-already-built pattern.
- **`LOCAL_TEST_THROTTLE`:** every loop script needs the hardcoded throttle boolean (CLAUDE.md §4 Loop Safety), via the existing `loop_template.apply_throttle()` helper.
- **No metadata pre-filter beyond document_id** — same rule as P1, not a new one: `document_id` scoping is a property of the query, not a banned answer-location hint.

## Architecture

P2 skips the LlamaIndex/embedding stack entirely — `BM25Okapi` operates on tokenized strings, not `TextNode` objects. Retrieval reads directly from `database_manager.get_nodes_by_document()`'s raw dict rows (`node_id`, `content`, ...) rather than going through `pipelines/structural/node_convert.py`'s `nodes_to_llama_nodes()` (which exists for P1/P3's LlamaIndex-based indexes). This keeps P2 a genuinely raw statistical baseline — routing it through LlamaIndex machinery it doesn't need would blur the paradigm contrast the benchmark is built to measure.

## Files

- `project/pipelines/bm25/__init__.py` — empty, package marker.
- `project/pipelines/bm25/tokenizer.py`
  - `tokenize(text: str) -> list[str]`
  - Regex-based; standalone and independently unit-tested (this is the one genuinely tricky piece — everything downstream depends on index-time and query-time tokenization matching exactly, since they're the same function call).
- `project/pipelines/bm25/build_bm25_index.py`
  - `STORAGE_ROOT = Path("storage/bm25")`, `DB_PATH = "benchmark.db"`, `MANIFEST_PATH = "data/filings_manifest.json"`
  - `is_document_indexed(document_id, storage_root=None) -> bool` — checks `<storage_root>/<document_id>.pkl` exists
  - `async def build_index_for_document(document_id, db_path=DB_PATH, storage_root=None) -> dict`
    - skip-if-indexed check (mirrors P1's `is_document_indexed` early return)
    - `nodes = await dbm.get_nodes_by_document(db_path, document_id)`; raise `ValueError` if empty (same rationale as P1: an empty corpus must surface as a hard ingestion gap, not a silently "successful" no-op build)
    - tokenize each node's `content` with `tokenizer.tokenize`
    - `bm25 = BM25Okapi(tokenized_corpus)`
    - pickle `{"node_ids": [n["node_id"] for n in nodes], "bm25": bm25}` to `<storage_root>/<document_id>.pkl` (atomic write: temp file + rename, matching P3's pattern, so a crash mid-write can't leave a corrupt pickle that `is_document_indexed` would then treat as done)
  - `async def main()` — same manifest-loop shape as `build_vector_index.py`/`build_summary_index.py`, `loop_template.apply_throttle()` applied
- `project/pipelines/bm25/p2_bm25.py`
  - `class P2BM25Retriever(Retriever)`
  - `retrieve(query_text, document_id, k)`:
    - loads `<storage_root>/<document_id>.pkl`; raises a clear error if not built yet (no silent empty-result fallback — matches P1's "build before query" expectation)
    - tokenizes `query_text` with the *same* `tokenizer.tokenize`
    - `scores = bm25.get_scores(tokenized_query)`
    - top-k selection: stable sort descending by score, ties broken by original node order (document reading order) — Python's `sorted()` is stable, so sorting the zipped `(score, original_index, node_id)` list by `(-score, original_index)` gets this for free, no extra logic
    - fetches node content for the top-k `node_ids` from `nodes` table (`dbm.get_nodes_by_document` already available, or a lighter targeted fetch — decide at implementation time) and returns `list[NodeWithScore]`

## Testing

TDD per file, mirroring P1's task-by-task test structure:
- `tokenizer.py`: numbers, decimals, `%`, currency symbols preserved; table pipes stripped but cell values kept; no stemming applied; empty string; whitespace-only input
- `build_bm25_index.py`: skip-if-already-built, empty-corpus raises, per-document isolation (two documents don't leak into each other's pickle), atomic-write survives interruption (temp file present but no final `.pkl` after a simulated crash)
- `p2_bm25.py`: retrieves correct top-k, respects `document_id` filtering, tie-break is stable/reproducible across repeated calls, raises clearly when index not built

## Out of scope

`pipelines/answerer.py` and `loop_executor.py` (shared across P1/P2/P3) — same exclusion as the P1 plan, a separate future piece.

## Deviation to log post-implementation

`resources/research/deviations.md`: Architecture.md names `storage/bm25/` "pickled corpora" without specifying per-document vs. combined-file granularity. Decision: one pickle per `document_id`, matching P1/P3's per-filing resumability pattern (crash-safe, `LOCAL_TEST_THROTTLE`-friendly, consistent with the rest of the codebase) over a single combined pickle (which would lose per-document resumability and put the whole corpus at risk on a mid-build crash).
