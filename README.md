# RAG Techniques — COMP702 M.Sc. Dissertation

A rigorous comparative benchmark of three Retrieval-Augmented Generation (RAG) retrieval paradigms evaluated against SEC 10-K financial filings.

## Research Question

Which retrieval paradigm — semantic (vector), statistical (BM25), or structural (summary-tree) — performs best on complex, structurally dense financial documents, and under what conditions does each break down?

## The Three Pipelines

| Pipeline | Method | Library |
|---|---|---|
| P1 — Semantic | Dense vector embeddings | FAISS / ChromaDB |
| P2 — Statistical | Okapi BM25 keyword ranking | `rank_bm25` |
| P3 — Structural | LLM-generated summary tree traversal | LlamaIndex `SummaryIndex` |

## Benchmark Design

- **140 queries** across three sets: 100 Pipeline Queries (PQ), 20 Golden Queries (GQ), 20 Judge Evaluation Queries (JEQ)
- **Dataset**: 13 SEC 10-K filings (EDGAR) across 5 companies — AAPL, MSFT, TSLA × FY2023-2025, JPM, JNJ × FY2023-2024
- **Judge**: LLM-as-judge with a >80% human-agreement gate before the full 900-run benchmark runs
- **Storage**: SQLite with WAL mode, fully resumable runs

## Repository Layout

```
claude/          # Agent steering files — not project source code (see below)
specs/           # (inside claude/) Architecture, guardrails, budget, phase plan
artifacts/       # (inside claude/) Proposal deliverables
README.md        # This file
CLAUDE.md        # Instructions for the Claude Code agent
TODO.md          # Active task list
```

> Implementation source code (Python modules `ingest/`, `pipelines/`, `judge/`) has not been started yet. Phase 1 of the phase plan is the next milestone.

## Knowledge Graph

A pre-built knowledge graph of the codebase is committed to `graphify-out/`, so it is
available on clone with no build step and no API key.

| File | What it is |
|---|---|
| `graphify-out/graph.html` | Interactive graph, open it directly in a browser |
| `graphify-out/GRAPH_REPORT.md` | Plain-language report: communities, hub nodes, cross-file links |
| `graphify-out/graph.json` | Raw graph data for tooling |

Query it from the command line:

```bash
graphify query "How does fetch_filing resolve a 10-K from SEC EDGAR?"
graphify explain "_find_10k()"
graphify path "run_ingestion" "database_manager"
```

Regenerate after changing code (AST only, no LLM, no cost):

```bash
graphify update .
```

Scope is set by `.graphifyignore`. The parsed 10-K corpus and its backups are excluded
on purpose: they are benchmark input data, not part of the system, and they outnumbered
the code roughly twenty to one.

## Status

Planning / proposal phase complete. Technical build not yet started.
