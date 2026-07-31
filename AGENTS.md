# AGENTS.md — OpenCode Agent Instructions for rag-techniques

## Critical Execution & Problem-Solving Rules

### Execution Restrictions
- **NEVER** read, inspect, or search files within the `./temp` directory under any circumstances.
- **NEVER** commit changes (e.g., `git commit`) unless explicitly instructed to do so.

### Problem Diagnosis Protocol
Whenever asked about an issue or problem, you must format your response using the following breakdown:

1. **Issue Statement:** State the issue directly as it is.
2. **Issue Description:** Describe the issue technical details as they are.
3. **Execution Context:** Identify the exact phase, flow, and step where the issue is occurring.
4. **Simple Explanation (ELI12):** Describe the issue as if explaining to a 12-year-old.
5. **Recommended Solution:** State your recommended solution.
6. **Solution Context (ELI12):** Describe how your recommended solution solves the problem as if explaining to a 12-year-old.

## Project Overview

**COMP702 M.Sc. Dissertation**: Comparative benchmark of three RAG retrieval paradigms (semantic vector, statistical BM25, structural summary-tree) on SEC 10-K filings.

**Current state**: Core infrastructure built (config, database, Groq client, throttle). Ingestion pipeline operational. Dataset generation and P3 summary index implemented. Three retrieval pipelines partially implemented. Judge and full benchmark runner pending.

## Critical Architecture Facts

| Component | Location | Status |
|-----------|----------|--------|
| Infra (config, DB, Groq client, throttle) | `project/config.py`, `database_manager.py`, `groq_client.py`, `loop_template.py` | ✅ Built |
| Ingestion (SEC EDGAR → LlamaParse → nodes) | `project/ingest/` | ✅ Built |
| P3 Summary Index | `project/pipelines/structural/build_summary_index.py` | ✅ Built |
| Dataset Generation | `project/dataset_generation/` | ✅ Built |
| Three Retrieval Pipelines | `project/dataset_generation/` (generator, critic, search tool) | 🔧 Partial |
| Judge + Gate | Not yet implemented | ⏳ Pending |
| Benchmark Runner | Not yet implemented | ⏳ Pending |
| Analysis | Not yet implemented | ⏳ Pending |

## Binding Constraints (from `resources/specs/Guardrails.md`)

1. **No per-hour or scale-to-non-zero infrastructure** — all local or free-tier
2. **Fixed model routing** (enforced in `config.MODEL_ROUTING`):
   - Generator/Dataset generation: `openai/gpt-oss-120b`
   - Critic/Dataset critique (+ search): `qwen/qwen3.6-27b`
   - **P3 Index Build**: `llama-3.1-8b-instant` (one-time, cached) *[NOTE: config.py currently shows openai/gpt-oss-20b - this is an error; follow Guardrails.md]*
   - Answerer (P1/P2/P3): `llama-3.3-70b-versatile` (shared)
   - Judge: `qwen/qwen3.6-27b` (no search tool)
   - Embeddings: `bge-small-en-v1.5` (local CPU)
   - BM25: `rank_bm25` (local CPU)
   - Debugging: `llama-3.1-8b-instant`
3. **Anti-leakage**: Three query sets disjoint (100 PQ / 20 GQ / 20 JEQ). Pipelines receive only query + own retrieved nodes.
4. **Loop safety**: Every loop script has hardcoded `LOCAL_TEST_THROTTLE` boolean forcing `LIMIT 3`. Never centralised.
5. **Determinism**: All LLM calls `temperature=0`, each cell runs once. SQLite WAL mode mandatory.
6. **Judge gate**: >80% human agreement on 60 gate outputs before full 900-run matrix.

## Development Commands

```bash
# From project/ directory
uv sync                              # Install deps (uses uv.lock)
uv run pytest -q                     # Run all tests (currently 142 passing, 1 failing, 1 skipped)
uv run pytest -q tests/test_groq_client_backoff.py  # Single test

# Run ingestion (Phase 2)
uv run python -m ingest.run_ingestion

# Build P3 summary index (Phase 3)
uv run python -m pipelines.structural.build_summary_index

# Run dataset generation
uv run python -m dataset_generation.run_dataset_generation

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
| `project/dataset_generation/` | Dataset generation scripts (async_generator.py, async_critic.py, search_tool.py) |
| `project/pipelines/structural/build_summary_index.py` | P3 TreeIndex persistence builder |
| `storage/summary_index/<doc_id>/` | P3 TreeIndex persistence (docstore.json, index_store.json, etc.) |

## Known Discrepancies (Trust the Code, Not Stale Docs)

- `README.md` repository layout is stale (describes `claude/`, omits `project/`, `resources/`)
- `README.md` names only Apple — corpus is AAPL/MSFT/TSLA × 3 years (9 filings)
- `resources/specs/` remain binding for implementation
- `Architecture.md` (v2) wins when docs disagree

## Environment

```bash
# Required env vars (in project/.env)
GROQ_API_KEY=...
LLAMA_CLOUD_API_KEY=...
SEC_EDGAR_USER_AGENT=...

# Throttle control (WARNING: .env currently has LOCAL_TEST_THROTTLE=false)
LOCAL_TEST_THROTTLE=true  # Set true for development/testing (3-item limit)
```

## Testing Quirks

- `pytest-asyncio` with `asyncio_mode = auto`
- Tests mock `groq_client.call_groq` by default; live tests need `RUN_LIVE_GROQ_TESTS=1`
- Run throttle tests first: `LOCAL_TEST_THROTTLE=true` (default in config if env not set)
- Currently 142 passing tests, 1 failing (test_search_tool.py), 1 skipped

## Graphify Knowledge Graph

```bash
graphify query "<question>"        # Scoped subgraph
graphify explain "<concept>"       # Focused explanation
graphify path "<A>" "<B>"          # Relationship
graphify update .                  # Refresh after changes (AST only)
```

Graph at `graphify-out/` — nodes and communities updated through Phase 3.

Requires `monitor/profile.json` (run init first). Reports immutable.

## Document/Styling Rules (for deliverables)

- Colours: `resources/assets/design/palette.md` (Oxford Ink system)
- Typography: Garamond (body), Calibri (headings/tables/diagrams), Consolas (code)
- British English, no em dashes, native Word/PowerPoint features only
- Harvard references, Figure/Table X.Y labelling
- macOS `.docx`: `xattr -c file.docx && chmod 644 file.docx` before reopening

## OpenWiki

Start at `openwiki/quickstart.md` → links to architecture, benchmark design, working-in-this-repo.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

<!-- OPENWIKI:START -->

## OpenWiki

This repository uses OpenWiki for recurring code documentation. Start with `openwiki/quickstart.md`, then follow its links to architecture, workflows, domain concepts, operations, integrations, testing guidance, and source maps.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->
