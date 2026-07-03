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
- **Dataset**: Apple Inc. SEC 10-K filings (EDGAR XBRL)
- **Judge**: LLM-as-judge with a >80% human-agreement gate before the full 900-run benchmark runs
- **Storage**: SQLite with WAL mode, fully resumable runs

## Repository Layout

```
claude/          # Agent steering files — not project source code (see below)
specs/           # (inside claude/) Architecture, guardrails, budget, phase plan
artifacts/       # (inside claude/) Proposal deliverables
README.md        # This file
CLAUDE.md        # Instructions for the Claude Code agent
todo.md          # Active task list
```

> Implementation source code (Python modules `ingest/`, `pipelines/`, `judge/`) has not been started yet. Phase 1 of the phase plan is the next milestone.

## Status

Planning / proposal phase complete. Technical build not yet started.
