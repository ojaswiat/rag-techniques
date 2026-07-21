# System architecture

How the benchmark is meant to be built. Primary source: `resources/specs/Architecture.md` (v2), with the schedule in `resources/specs/Phase Plan.md` and the throughput maths in `resources/specs/Budget.md`.

None of this exists in code yet. Everything below is the design to build against.

## Shape of the system

Everything runs as plain Python processes on one local machine — no server, no container, no managed cloud component. Outbound HTTPS reaches three external services only: Groq (all LLM calls, free tier), LlamaParse (parsing, free tier), and SEC EDGAR (public filings).

```
SEC EDGAR ──► ingest/ ──► nodes (SQLite)
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        dataset_gen/               pipeline index builders
   (generator + critic)        P1 ChromaDB · P2 rank_bm25 · P3 SummaryIndex
                │                         │
                └──────────┬──────────────┘
                           ▼
                   loop_executor.py
        retrieve → answer (shared Llama 3.3 70B, temp 0) → upsert
                           ▼
                   results (SQLite)
                           ▼
              judge/ ──► analysis/ (pandas, matplotlib)
```

`nodes` is the single source for everything downstream. Two consumers read it independently — dataset generation and the three index builders — and both feed `loop_executor.py`, which is the **only** writer of `results`. `results` is then the single input to both the judge and the analysis scripts.

Local on-disk state sits alongside `benchmark.db`: `storage/chroma/` (P1), `storage/bm25/` (P2, pickled per document), `storage/summary_index/` (P3, per filing), and the HuggingFace model cache for the bge models.

## Retrieval scope: per document, not cross-corpus

Every pipeline retrieves only within the one filing a query is about (`Architecture.md` §0.2). Every query already carries its `document_id`, so this narrowing is a property of the query, applied identically to all three pipelines.

This is deliberately *not* the metadata pre-filter that `Guardrails.md` §3 bans. That ban is about narrowing to a target *section* using information derived from the answer; narrowing to the correct *filing* leaks nothing.

## The five-table schema

SQLite with `PRAGMA journal_mode = WAL`, accessed through `aiosqlite`. Exactly five tables (`Architecture.md` §3.2):

| Table | Rows | Holds |
|---|---|---|
| `nodes` | a few thousand | `node_id` (PK), `document_id`, `parent_item_header`, `node_type` (`text`/`table`), `source_page_num`, `content`, `token_count` |
| `queries` | 100 | The PQ test set: quadrant, query text, ground-truth answer, `gt_citations`, `document_id`, `verified` |
| `golden_queries` | 20 | The GQ teaching set, plus `example_output`, `human_score`, `human_reasoning` |
| `judge_validation` | 20 | The JEQ validation set — question and ground-truth fields **only** |
| `results` | 960 | Every pipeline run: 900 PQ benchmark rows plus 60 JEQ gate rows |

### Two schema decisions that carry weight

**`source_set` on `results`.** The original design had `judge_validation` holding the gate outputs. It cannot: the gate runs 20 JEQ through 3 pipelines, producing 60 outputs, and a 20-row table cannot hold those without repeating columns or breaking first normal form. The fix keeps `judge_validation` to its 20 question rows and puts *all* pipeline outputs — both the 900 PQ runs and the 60 gate runs — into one `results` table, distinguished by `source_set ∈ {PQ, JEQ}`, with a nullable `human_score` populated only on JEQ rows. Still exactly five tables. This was defect #1 of the eight that `Architecture.md` §1 found and resolved.

**`UNIQUE (source_set, query_id, pipeline, k_value)`.** This constraint is simultaneously the integrity rule and the literal resume key. `get_completed_keys()` queries exactly that shape, and `loop_executor.py` skips any cell already present. A crash at run 700 of 900 therefore never re-spends free-tier quota — which matters a great deal when the full run spans weeks.

**Soft foreign keys.** `gt_citations`, `retrieved_node_ids`, and `cited_node_ids` are lists, and SQLite has no array type, so they are stored as JSON-encoded `TEXT`. SQLite cannot enforce a foreign key into values inside a JSON array, so referential integrity for these is an application-level invariant — a debug assertion in `database_manager.py` — not a database constraint. `database_manager.py` is also the *only* module that touches the raw JSON; every other module sends and receives plain `list[str]`.

## Key interfaces

From `Architecture.md` §4.1. Three of these are worth knowing before writing any pipeline code:

```python
# pipelines/base.py
class Retriever(ABC):
    def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]: ...
    # every implementation must filter to document_id internally

class Answerer:
    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.0): ...
    async def answer(self, query_text: str, nodes: list[NodeWithScore]) -> AnswerResult: ...
    # prompt contains ONLY query_text + node content — no exemplars, no ground truth

# pipelines/keyword/tokenizer.py
def tokenize(text: str) -> list[str]: ...
    # ONE function, imported by both index-build and query-time — never two implementations
```

**LlamaIndex is the common backbone.** A node is a LlamaIndex `TextNode`; a retrieval result is `list[NodeWithScore]` for all three pipelines. That uniformity is what lets `loop_executor.py` and the answerer stay free of pipeline-specific branching.

### Citation markers

The answerer's prompt instructs the model to append `[[node:<node_id>]]` immediately after any claim drawn from a source. `Answerer.answer()` then runs `re.findall(r"\[\[node:([\w\-]+)\]\]", raw_text)` to populate `cited_node_ids`, deduplicated and order-preserved. The markers are deliberately **kept** in the stored `pipeline_output` rather than stripped, so the raw output stays auditable against its own citations.

### Numeric normalisation

`judge/numeric_normalizer.py` strips currency symbols and thousands separators and expands suffix multipliers (K/M/B/T and the spelled-out forms), returning a `Decimal` or `None`. `exact_match()` tries it on both sides; if both parse it compares within a 1% relative epsilon, so `$394.3B` matches `394,300 million`. If either side fails to parse — a short named-entity answer, typically Q1 — it falls back to normalised string comparison.

## Model routing

Fixed per stage (`Guardrails.md` §2). This table is not a suggestion; the family separations encoded in it are what make the evaluation defensible.

| Stage | Model | Where |
|---|---|---|
| Dataset generation | `openai/gpt-oss-120b` | Groq free |
| Dataset critique (with search tool) | `Qwen3.6-27B` | Groq free |
| P3 summary-index build (one-time) | `llama-3.1-8b-instant` | Groq free |
| Pipeline answers, all of P1/P2/P3 | `Llama 3.3 70B` (shared) | Groq free |
| Judge / scoring (no search tool) | `Qwen3.6-27B` | Groq free |
| Embeddings (P1) | `bge-small-en-v1.5` | Local CPU, $0 |
| Re-ranker (P1) | `bge-reranker-base` | Local CPU, $0 |
| BM25 (P2) | `rank_bm25` | Local CPU, $0 |
| Throwaway debugging | `llama-3.1-8b-instant` | Groq free |

Three invariants ride on this table:

- **Generator ≠ Critic family**, so dataset agreement reflects cross-architecture consensus rather than a model agreeing with itself.
- **Answerer ≠ Judge family**, so no model grades its own output. If the judge is later swapped to pass the gate, it must still differ from the Llama answerer.
- **The answerer is shared and identical across P1/P2/P3**, at the same settings. Any score difference must come from retrieval — otherwise the experiment measures generation, not retrieval.

The critic gets a search tool; the judge does not. The judge already receives the ground-truth answer and citations, so search would be cost for no gain.

## Throughput: what actually binds

The project is designed to run at **$0.00** — every recurring component is free-tier or local CPU. The binding constraint is therefore not money but **Groq's tokens-per-day ceiling**, and specifically not request count (`Budget.md` §2).

Answer generation is the bottleneck: roughly 960 calls at 1–3K tokens each, on the order of 2M tokens, against `llama-3.3-70b-versatile`'s ~100K TPD. That is **two to three weeks of intermittent free-tier running**, not the one to two days an earlier budget draft claimed. It fits comfortably inside the ten-week timeline, but only because the run resumes rather than restarts.

The levers, in priority order: run the throttle first; pass the judge gate before the full run; cache the static judge prefix (cached tokens do not count toward limits, which is the single biggest free lever); resume rather than restart; build the P3 index once; and use the 8B model for throwaway debugging so the 70B's daily budget is reserved for real work.

Limits apply **per organisation**, not per API key — extra keys do not raise the ceiling. Concurrency is capped at ≤ 5 parallel workers via `asyncio.Semaphore`, with `tenacity` exponential backoff and jitter on HTTP 429.

If the free tier ever proves too slow, the documented fallback is Groq's Developer tier, which compresses the run to a day or two. The worst-case total spend for the entire LLM workload is on the order of **$3–5** — a trivial ceiling, but the strict-$0 path remains the default.

## The eight phases

Ten weeks total, with active build work (Phases 1–6) wrapping by end of Week 7 so the write-up has room (`Phase Plan.md`, `Architecture.md` §6/§8).

| Phase | Weeks | What gets built | Key modules |
|---|---|---|---|
| **1 — Infrastructure** | 1 | SQLite state layer, resilient Groq wrapper, throttle scaffolding | `config.py`, `database_manager.py`, `groq_client.py` |
| **2 — Ingestion & parsing** | 1–3 | Filings → clean, metadata-rich nodes | `ingest/fetch_filings.py`, `parse_filing.py`, `node_builder.py`, `parsing_audit.py` |
| **3 — P3 summary index** | 3 | One-time LLM-built summary tree per filing, cached | `pipelines/structural/build_summary_index.py` |
| **4 — Dataset generation** | 4–5 | 140 verified queries, split into three disjoint sets, GQ hand-labelled | `dataset_gen/async_generator.py`, `async_critic.py`, `cross_check.py`, `split_and_label.py` |
| **5 — Pipelines** | 5–6 | P1, P2, P3 plus the shared answerer and the executor | `pipelines/*`, `loop_executor.py` |
| **6 — Judge & gate** | 6–7 | Judge with quadrant-routed few-shot, code metrics, the 80% gate | `judge/async_judge.py`, `metrics.py`, `validation_gate.py` |
| **7 — Full benchmark** | 7–9 | The 900-cell matrix, TPD-paced, resumable, in the background | `run_benchmark.py` |
| **8 — Analysis** | 8–10 | Tri-pillar aggregation, per-quadrant breakdown, tables and figures | `analysis/aggregate.py`, `plots.py`, `tables.py` |

Phase 2 was extended from two weeks to three, and the overall plan from eight weeks to ten, when the corpus grew from a single filing to roughly nine. The extra time goes into ingestion, parsing, and more generation chunks — not new scope.

**Two manual bottlenecks cannot be parallelised away**: hand-labelling the 20 GQ exemplars at the end of Phase 4, and hand-scoring the 60 gate outputs in Phase 6.

## The central loop

The most-repeated flow in the system runs 960 times (`Architecture.md` §4.5a):

```
loop_executor.py
  ├─ get_completed_keys(source_set)          → skip cells already in results
  ├─ retrieve(query_text, document_id, k)    → list[NodeWithScore], P1/P2/P3
  ├─ answer(query_text, nodes)               → Groq, Llama 3.3 70B, temp 0
  │    └─ parse [[node:...]] → cited_node_ids
  └─ upsert_result(row)                      → results
```

Everything about crash-resumability, cost control, and reproducibility hangs off the first and last lines of that loop.

## Where this connects

- Why the query sets are disjoint and what the metrics measure: [Benchmark design](benchmark-design.md)
- The constraints that make these choices non-negotiable: [Working in this repo](working-in-this-repo.md)
- Full DDL, sequence diagrams, and worked example rows: `resources/specs/Architecture.md` §3–§4
- Proposed repository layout and the dependency manifest: `resources/specs/Architecture.md` §9–§10
