# Quickstart

This repository is the workspace for a **COMP702 M.Sc. dissertation**: a comparative benchmark of three Retrieval-Augmented Generation (RAG) retrieval paradigms, evaluated against SEC 10-K financial filings.

The research question, from `README.md`: *which retrieval paradigm — semantic (vector), statistical (BM25), or structural (summary-tree) — performs best on complex, structurally dense financial documents, and under what conditions does each break down?*

## The one thing to know first

**Phases 1–3 are built and tested; Phase 4 is built and tested but hasn't been run to produce real data yet; Phases 5–8 are not built.** Implementation code lives under `project/`, not the `src/` that `CLAUDE.md` describes — that's a real discrepancy, see [Working in this repo](working-in-this-repo.md). Phase 1 built the infrastructure layer (`project/llm_client/` — multi-provider Groq/NVIDIA NIM client factory, `database_manager.py`, `loop_template.py`); Phase 2 built the SEC EDGAR → LlamaParse → `nodes` ingestion pipeline (`project/ingest/`); Phase 3 built the per-filing `TreeIndex` summary build (`project/pipelines/structural/`). Phase 4's dataset-generation subsystem (`project/dataset_generation/` — Generator, Critic, cross-check, search tool, GQ hand-labelling tooling) is fully coded and unit-tested, but `queries`/`golden_queries`/`judge_validation` are still empty — it has not yet been run end-to-end against the corpus. See [System architecture](system-architecture.md) for the phase-by-phase build table.

The specs in `resources/specs/` remain the binding design for everything not yet built (Phases 3–8: P3 summary index, dataset generation, the three retrieval pipelines, the judge, the full benchmark, analysis). Treat them as the contract for that remaining work.

## Where to go next

| Page | What it covers |
|---|---|
| [Benchmark design](benchmark-design.md) | The research question, the 140-query dataset, the four quadrants, the tri-pillar metrics, and the judge-validation gate |
| [System architecture](system-architecture.md) | The five-table SQLite schema, module map, the eight build phases, model routing, and data flow |
| [Working in this repo](working-in-this-repo.md) | The binding guardrails, the document and styling rules, and known stale content |

## Repository layout

```
project/                   # All application code (Phases 1-4 built, see below)
  llm_client/              # Phase 1: config.py, llm_factory.py (LLMFactory), groq_client.py,
                           # nim_client.py, utils.py -- multi-provider LLM client (Groq + NVIDIA NIM)
  database_manager.py, loop_template.py  # Phase 1
  ingest/                  # Phase 2: fetch_filings.py, parse_filing.py, node_builder.py,
                           # parsing_audit.py, run_ingestion.py
  pipelines/structural/    # Phase 3: build_summary_index.py (per-filing TreeIndex), node_convert.py
  dataset_generation/      # Phase 4: async_generator.py, async_critic.py, search_tool.py,
                           # cross_check.py, run_dataset_generation.py, gq_label_export.py/gq_label_import.py
  tests/                   # passing tests across all four phases
  benchmark.db             # SQLite state (gitignored)
resources/                 # User files and assets: the steering and reference layer
  specs/                   # Authoritative design docs (read these in the order below)
  artifacts/               # Proposal deliverables + Changes.md (spec deviations log)
  assets/                  # Design palette, typography, draw.io diagrams, data samples
  docs/                    # University brief and proposal template (read-only)
docs/superpowers/plans/    # Task-by-task implementation plans for each phase
temp/                      # Scratch notes, human-action reports, sample data references
monitor/                   # Operation logs and generated HTML reports
CLAUDE.md                  # Agent instructions for this repository
README.md                  # Short project summary
graphify-out/              # Generated knowledge graph over the corpus and code
openwiki/                  # This wiki
```

### Reading order for the specs

`CLAUDE.md` prescribes this order, and it is the right one — each document assumes the previous:

1. `resources/specs/Project Idea.md` — the research concept, dataset design, and evaluation methodology
2. `resources/specs/Architecture.md` — full DDL, HLD/LLD, sequence diagrams, phase-by-phase module map
3. `resources/specs/Phase Plan.md` — the ten-week, eight-phase build schedule
4. `resources/specs/Guardrails.md` — hard constraints; binding, not advisory
5. `resources/specs/Budget.md` — the $0 cost model and the Groq throughput maths

`Architecture.md` is the most load-bearing of the five. It is a v2 that resolved eight concrete design defects found when the earlier narrative plan was turned into an actual table design (see [System architecture](system-architecture.md)), and where it disagrees with an older document, it wins.

## The shape of the project in one paragraph

Six to nine SEC 10-K filings are parsed with LlamaParse into `TextNode`s, each carrying a stable `node_id` that is the canonical evidence anchor for everything downstream. A generator model writes 140 candidate queries; a critic model from a different family independently verifies each one; the verified pool is split into three disjoint sets of 100 / 20 / 20. Three retrieval pipelines answer the 100-query test set at three values of K, producing a 900-run matrix, all scored by an LLM judge that must first clear an 80% agreement gate against human scores. Everything runs locally or on free tiers, at $0, into one SQLite database.

## Current state and open items

Phases 1–3 (infrastructure, ingestion, P3 summary index) are built and tested. Phase 4 (dataset generation) is built and tested but has not yet been run against the full corpus — its three query tables are still empty. Phase 5 onward (P1/P2/P3 retrieval pipelines, judge, benchmark, analysis) follow the specs as designed but are not yet built. Several things remain genuinely unresolved:

- **LLM calls now route through a multi-provider factory.** `project/llm_client/llm_factory.py`'s `LLMFactory.get_client_for_stage(stage)` reads `config.MODEL_ROUTING[stage]` (now `{model, provider}` pairs) and dispatches to either `groq_client.py` or `nim_client.py`. P3's index build uses this to call NVIDIA NIM (`nvidia/nemotron-3-super-120b-a12b`) instead of Groq. See `resources/artifacts/Changes.md` (2026-07-31 entry).

- **The filing corpus has since expanded to 18 filings and is fully ingested.** Original corpus was AAPL/MSFT/TSLA × FY2023–2025 (9 filings); expanded to 6 companies (added JPM, JNJ, WMT) × FY2023–2025 = 18 filings, all fetched/parsed (26,050 nodes in `benchmark.db`, confirmed 2026-07-29). See `resources/artifacts/Changes.md` and `project/data/filings_manifest.json` for the authoritative current list.
- **Context-mass standardisation is asserted but not enforced.** `Project Idea.md` §10 principle 1 requires context mass held constant across pipelines, but K is standardised as node *count*, not token count, and node sizes vary. `Architecture.md` §11 item 4 recommends accepting and documenting the variance rather than adding a truncation step. Flagged for the researcher to confirm. Not yet relevant — no pipeline exists yet to standardise.
- **`README.md`'s repository-layout section is stale.** It describes a `claude/` folder and does not mention `project/` or `resources/`.
- **`CLAUDE.md` says code goes in `src/`; the actual Phase 1/2 code is in `project/`.** See [Working in this repo](working-in-this-repo.md) for the reasoning.
- **`TODO.md` is empty**; day-to-day task notes live in `temp/todo.md` instead.
