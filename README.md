# RAG Techniques — COMP702 M.Sc. Dissertation

A rigorous comparative benchmark of three Retrieval-Augmented Generation (RAG) retrieval paradigms evaluated against SEC 10-K financial filings.

## Research Question

Which retrieval paradigm — semantic (vector), statistical (BM25), or structural (summary-tree) — performs best on complex, structurally dense financial documents, and under what conditions does each break down?

## The Three Pipelines

| Pipeline | Method | Library |
|---|---|---|
| P1 — Semantic | Dense vector embeddings, plus a cross-encoder re-rank | ChromaDB + `fastembed` (`bge-small-en-v1.5`, `bge-reranker-base`) |
| P2 — Statistical | Okapi BM25 keyword ranking | `rank_bm25` |
| P3 — Structural | LLM-generated summary tree traversal | LlamaIndex `TreeIndex`, one per filing |

All three share a single answerer (`llama-3.3-70b-versatile`) at identical settings, so score differences come from retrieval, not generation.

## Benchmark Design

- **140 queries** across three sets: 100 Pipeline Queries (PQ), 20 Golden Queries (GQ), 20 Judge Evaluation Queries (JEQ)
- **Dataset**: 13 SEC 10-K filings (EDGAR) across 5 companies — AAPL, MSFT, TSLA × FY2023-2025, JPM, JNJ × FY2023-2024
- **Judge**: LLM-as-judge with a >80% human-agreement gate before the full 900-run benchmark runs
- **Corpus**: 18,297 parsed nodes across the 13 filings
- **Storage**: SQLite with WAL mode, fully resumable runs
- **Models**: free tiers of Groq, NVIDIA NIM and OpenRouter; all retrieval compute is local CPU. See `resources/specs/Guardrails.md` §2 for the fixed routing matrix

## Repository Layout

```
project/             # All source code
  ingest/            # SEC EDGAR fetch, LlamaParse parsing, node building
  dataset_generation/# Generator + Critic loop that builds the 140-query dataset
  pipelines/         # P1 vector, P2 bm25, P3 structural, and the shared answerer
  judge/             # LLM-as-judge, scoring metrics, numeric normalisation
  llm_client/        # Provider clients (Groq, NIM, OpenRouter) behind LLMFactory
  tests/             # Test suite
  data/              # filings_manifest.json, raw and parsed filings
  benchmark.db       # SQLite results database
resources/           # User files and steering layer — not source code
  specs/             # Architecture, Guardrails, Budget, Phase Plan, Project Idea
  artifacts/         # Proposal deliverables
  assets/            # Design palette, typography, diagrams
  research/          # Deviations log, planning notes
  docs/              # University brief and template (read-only)
graphify-out/        # Pre-built knowledge graph (see below)
openwiki/            # Generated documentation wiki
README.md            # This file
CLAUDE.md            # Instructions for the Claude Code agent
```

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

Phases 1 to 6 are built and tested; the full benchmark run has not started.

| Phase | State |
|---|---|
| 1. Environment and infrastructure | Complete |
| 2. Ingestion and parsing | Complete — 13 filings, 18,297 nodes |
| 3. P3 tree-index build | Complete — one index per filing |
| 4. Dataset generation | Complete — 100 PQ, 20 GQ, 20 JEQ in the database |
| 5. Pipeline implementation | Complete — P1, P2, P3 and the shared answerer |
| 6. Judge and validation gate | Built; the >80% agreement gate has not been run |
| 7. Full benchmark execution | Not started — the `results` table is empty |
| 8. Analysis and write-up | Not started |

Test suite: 339 passing, 2 skipped (the skips are live-API smoke tests, gated behind an environment variable).

Deviations from the specs are logged in `resources/research/deviations.md`.
