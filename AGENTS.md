# AGENTS.md — OpenCode Agent Instructions for rag-techniques

## Project Overview

**COMP702 M.Sc. Dissertation**: Comparative benchmark of three RAG retrieval paradigms (semantic vector, statistical BM25, structural summary-tree) on SEC 10-K filings.

**Current state**: Phases 1–2 built and tested (39 passing tests). Phases 3–8 pending. Code lives in `project/`, not `src/`.

## Critical Architecture Facts

| Layer | Location | Status |
|-------|----------|--------|
| Infra (config, DB, Groq client, throttle) | `project/config.py`, `database_manager.py`, `groq_client.py`, `loop_template.py` | ✅ Built |
| Ingestion (SEC EDGAR → LlamaParse → nodes) | `project/ingest/` | ✅ Built (3/9 filings ingested) |
| P3 Summary Index | `project/pipelines/structural/build_summary_index.py` | ⏳ Phase 3 |
| Dataset Generation | `project/dataset_generation/` | ⏳ Phase 4 |
| Three Pipelines + Executor | `project/pipelines/`, `loop_executor.py` | ⏳ Phase 5 |
| Judge + Gate | `project/judge/` | ⏳ Phase 6 |
| Benchmark Runner | `run_benchmark.py` | ⏳ Phase 7 |
| Analysis | `project/analysis/` | ⏳ Phase 8 |

## Binding Constraints (from `resources/specs/Guardrails.md`)

1. **No per-hour or scale-to-non-zero infrastructure** — all local or free-tier
2. **Fixed model routing** (enforced in `config.MODEL_ROUTING`):
   - Generator: `openai/gpt-oss-120b`
   - Critic: `qwen/qwen3.6-27b` (with search tool)
   - P3 Index Build: `llama-3.1-8b-instant` (one-time, cached)
   - Answerer: `llama-3.3-70b-versatile` (shared across P1/P2/P3)
   - Judge: `qwen/qwen3.6-27b` (no search tool)
   - Embeddings: `bge-small-en-v1.5` (local CPU)
   - BM25: `rank_bm25` (local CPU)
3. **Anti-leakage**: Three query sets disjoint (100 PQ / 20 GQ / 20 JEQ). Pipelines receive only query + own retrieved nodes.
4. **Loop safety**: Every loop script has hardcoded `LOCAL_TEST_THROTTLE` boolean forcing `LIMIT 3`. Never centralised.
5. **Determinism**: All LLM calls `temperature=0`, each cell runs once. SQLite WAL mode mandatory.
6. **Judge gate**: >80% human agreement on 60 gate outputs before full 900-run matrix.

## Development Commands

```bash
# From project/ directory
uv sync                              # Install deps (uses uv.lock)
uv run pytest -q                     # Run all 39 tests
uv run pytest -q tests/test_groq_client_backoff.py  # Single test
uv run pytest -q -k "live"           # Live Groq tests (needs RUN_LIVE_GROQ_TESTS=1)

# Run ingestion (Phase 2)
uv run python -m ingest.run_ingestion

# Build P3 summary index (Phase 3)
uv run python -m pipelines.structural.build_summary_index

# Regenerate knowledge graph after code changes
graphify update .
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `project/config.py` | Model routing, env loading, throttle flag |
| `project/database_manager.py` | All SQLite operations (aiosqlite, WAL mode) |
| `project/groq_client.py` | Resilient async Groq wrapper (tenacity backoff, semaphore=5) |
| `project/loop_template.py` | Throttle helper (`apply_throttle`) for manifests |
| `project/data/filings_manifest.json` | Canonical corpus: AAPL/MSFT/TSLA × FY2023–2025 |
| `project/benchmark.db` | SQLite state (gitignored) |
| `storage/summary_index/<doc_id>/` | P3 TreeIndex persistence (docstore.json, index_store.json, etc.) |

## Known Discrepancies (Trust the Code, Not Stale Docs)

- `CLAUDE.md` says code in `src/` — **actual code is in `project/`**
- `README.md` repository layout is stale (describes `claude/`, omits `project/`, `resources/`)
- `README.md` names only Apple — corpus is AAPL/MSFT/TSLA × 3 years (9 filings)
- `resources/specs/` remain binding for Phases 3–8
- `Architecture.md` (v2) wins when docs disagree — resolved 8 design defects

## Environment

```bash
# Required env vars (in project/.env)
GROQ_API_KEY=...
LLAMA_CLOUD_API_KEY=...
SEC_EDGAR_USER_AGENT=...

# Optional for NIM fallback (Phase 3 P3 index build)
NVIDIA_NIM_API_KEY=...
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-8b-instruct
```

## Testing Quirks

- `pytest-asyncio` with `asyncio_mode = auto`
- Live Groq tests gated behind `RUN_LIVE_GROQ_TESTS=1` env var
- Tests mock `groq_client.call_groq` by default; live tests hit real API
- Run throttle tests first: `LOCAL_TEST_THROTTLE=true` (default in config)

## Graphify Knowledge Graph

```bash
graphify query "<question>"        # Scoped subgraph
graphify explain "<concept>"       # Focused explanation
graphify path "<A>" "<B>"          # Relationship
graphify update .                  # Refresh after changes (AST only)
```

Graph at `graphify-out/` — 1321 nodes, 185 communities (Phase 2 update).

## Monitor (Operations Log + Reports)

```bash
/monitor:init        # First-time setup
/monitor:log         # Append operation entry
/monitor:report      # Author HTML report + rebuild index
/monitor:record      # Log + report if code changed
/monitor:update      # Reconcile profile, refresh assets
```

Requires `monitor/profile.json` (run init first). Reports immutable.

## Document/Styling Rules (for deliverables)

- Colours: `resources/assets/design/palette.md` (Oxford Ink system)
- Typography: Garamond (body), Calibri (headings/tables/diagrams), Consolas (code)
- British English, no em dashes, native Word/PowerPoint features only
- Harvard references, Figure/Table X.Y labelling
- macOS `.docx`: `xattr -c file.docx && chmod 644 file.docx` before reopening

## OpenWiki

Start at `openwiki/quickstart.md` → links to architecture, benchmark design, working-in-this-repo.