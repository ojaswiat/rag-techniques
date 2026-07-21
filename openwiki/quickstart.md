# Quickstart

This repository is the workspace for a **COMP702 M.Sc. dissertation**: a comparative benchmark of three Retrieval-Augmented Generation (RAG) retrieval paradigms, evaluated against SEC 10-K financial filings.

The research question, from `README.md`: *which retrieval paradigm — semantic (vector), statistical (BM25), or structural (summary-tree) — performs best on complex, structurally dense financial documents, and under what conditions does each break down?*

## The one thing to know first

**There is no implementation code yet.** The repository currently holds only design specifications, proposal deliverables, and design assets. `src/` exists but is empty; the Python modules described throughout the specs (`ingest/`, `pipelines/`, `judge/`, `loop_executor.py`) have not been written. Phase 1 of the build plan is the next milestone.

That means the specs in `resources/specs/` are not documentation *of* a system — they are the binding design *for* a system that is about to be built. Treat them as the contract, not as a description of reality.

## Where to go next

| Page | What it covers |
|---|---|
| [Benchmark design](benchmark-design.md) | The research question, the 140-query dataset, the four quadrants, the tri-pillar metrics, and the judge-validation gate |
| [System architecture](system-architecture.md) | The five-table SQLite schema, module map, the eight build phases, model routing, and data flow |
| [Working in this repo](working-in-this-repo.md) | The binding guardrails, the document and styling rules, and known stale content |

## Repository layout

```
src/                       # All application and research code — currently empty
resources/                 # User files and assets: the steering and reference layer
  specs/                   # Authoritative design docs (read these in the order below)
  artifacts/               # Proposal deliverables (.docx, .pdf)
  assets/                  # Design palette, typography, draw.io diagrams, data samples
  docs/                    # University brief and proposal template (read-only)
CLAUDE.md                  # Agent instructions for this repository
README.md                  # Short project summary
TODO.md                    # Currently empty
skills-lock.json           # Pinned agent skills (docx, rag-implementation)
graphify-out/              # Generated knowledge graph over the corpus
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

Planning and proposal work is complete. The build has not started. Several things are genuinely unresolved and are recorded in `Architecture.md` §11 rather than hidden:

- **The exact filing list is not fixed.** `Architecture.md` §0.1 sets the corpus at 6–9 filings across 2–3 companies and 2–3 fiscal years, and §11 item 2 notes that AAPL/MSFT/TSLA × FY2023–2025 is only an illustrative example. `README.md` says "Apple Inc. SEC 10-K filings", which is narrower than the current design; prefer `Architecture.md`.
- **Context-mass standardisation is asserted but not enforced.** `Project Idea.md` §10 principle 1 requires context mass held constant across pipelines, but K is standardised as node *count*, not token count, and node sizes vary. `Architecture.md` §11 item 4 recommends accepting and documenting the variance rather than adding a truncation step. Flagged for the researcher to confirm.
- **`README.md`'s repository-layout section is stale.** It still describes a `claude/` folder and does not mention `src/` or `resources/`. The folder was renamed to `resources/` and that rename is currently uncommitted.
- **`TODO.md` is empty.**
