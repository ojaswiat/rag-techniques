# Quickstart

This repository is the workspace for a **COMP702 M.Sc. dissertation**: a comparative benchmark of three Retrieval-Augmented Generation (RAG) retrieval paradigms, evaluated against SEC 10-K financial filings.

The research question, from `README.md`: *which retrieval paradigm — semantic (vector), statistical (BM25), or structural (summary-tree) — performs best on complex, structurally dense financial documents, and under what conditions does each break down?*

## The one thing to know first

**Phase 1 and Phase 2 of the build are done; Phases 3–8 are not.** Implementation code lives under `project/`, not the `src/` that `CLAUDE.md` describes — that's a real discrepancy, see [Working in this repo](working-in-this-repo.md). Phase 1 built the infrastructure layer (`config.py`, `database_manager.py`, `groq_client.py`, `loop_template.py`); Phase 2 built the SEC EDGAR → LlamaParse → `nodes` ingestion pipeline (`project/ingest/`). Both are tested (39 passing tests) and verified against real, live SEC EDGAR and LlamaParse data, not just mocks.

The specs in `resources/specs/` remain the binding design for everything not yet built (Phases 3–8: P3 summary index, dataset generation, the three retrieval pipelines, the judge, the full benchmark, analysis). Treat them as the contract for that remaining work.

## Where to go next

| Page | What it covers |
|---|---|
| [Benchmark design](benchmark-design.md) | The research question, the 140-query dataset, the four quadrants, the tri-pillar metrics, and the judge-validation gate |
| [System architecture](system-architecture.md) | The five-table SQLite schema, module map, the eight build phases, model routing, and data flow |
| [Working in this repo](working-in-this-repo.md) | The binding guardrails, the document and styling rules, and known stale content |

## Repository layout

```
project/                   # All application code (Phases 1-2 built, see below)
  config.py, database_manager.py, groq_client.py, loop_template.py  # Phase 1
  ingest/                  # Phase 2: fetch_filings.py, parse_filing.py, node_builder.py,
                           # parsing_audit.py, run_ingestion.py
  tests/                   # 39 passing tests
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

Phase 1 (infrastructure) and Phase 2 (ingestion) are built and tested. Phase 3 onward (P3 summary index, dataset generation, pipelines, judge, benchmark, analysis) follow the specs as designed. Several things remain genuinely unresolved:

- **The filing corpus is confirmed but only partly ingested.** The human confirmed `Architecture.md` §11's illustrative example — AAPL/MSFT/TSLA × FY2023–2025, 9 filings — as the real corpus. Only 3 (AAPL × 3 years, 2081 nodes) have actually been fetched and parsed; MSFT and TSLA await an unthrottled ingestion run. `README.md` still says "Apple Inc. SEC 10-K filings", narrower than the confirmed design; prefer `Architecture.md` and `project/data/filings_manifest.json`.
- **Context-mass standardisation is asserted but not enforced.** `Project Idea.md` §10 principle 1 requires context mass held constant across pipelines, but K is standardised as node *count*, not token count, and node sizes vary. `Architecture.md` §11 item 4 recommends accepting and documenting the variance rather than adding a truncation step. Flagged for the researcher to confirm. Not yet relevant — no pipeline exists yet to standardise.
- **`README.md`'s repository-layout section is stale.** It describes a `claude/` folder and does not mention `project/` or `resources/`.
- **`CLAUDE.md` says code goes in `src/`; the actual Phase 1/2 code is in `project/`.** See [Working in this repo](working-in-this-repo.md) for the reasoning.
- **`TODO.md` is empty**; day-to-day task notes live in `temp/todo.md` instead.
