# CLAUDE.md — Agent Instructions

This file governs how the Claude Code agent operates within this repository. Read it fully before taking any action.

---

## 1. Project Overview

This is the workspace for a **COMP702 M.Sc. Dissertation**: a comparative benchmark of three RAG retrieval paradigms (semantic vector, statistical BM25, structural summary-tree) evaluated against SEC 10-K financial filings.

**Current state:** Planning and proposal phase. No implementation code exists yet. The technical build (Python, SQLite, `ingest/` / `pipelines/` / `judge/` modules) has not started. Phase 1 of `resources/specs/Phase Plan.md` is the next milestone.

### Repository Layout

| Folder | Purpose |
|---|---|
| `src/` | **All project code** — application and research code, pipelines, ingestion, judge, utilities, scripts, everything executable. New code goes here unless told otherwise. |
| `resources/` | **User files and assets** — the steering and reference layer, not source code. See below. |

---

## 2. The `resources/` Folder — User Files and Steering Layer

The `resources/` directory is **not project source code**. It holds the user's files and assets: the business and steering layer that drives the agent. Do not modify files inside `resources/` unless explicitly instructed. Always read from it; never write to it speculatively.

### `resources/` Subdirectory Reference

| Folder | Purpose |
|---|---|
| `resources/specs/` | Authoritative design documents — architecture, guardrails, budget, phase plan, project idea |
| `resources/artifacts/` | Deliverable files: proposals, papers, sheets, etc `.docx`, `.pdf`, `.xlsx`, `.csv`, `.md`, etc |
| `resources/assets/` | Meta assets for agent use: design palette, typography, diagrams (`.drawio`), images, data samples |
| `resources/docs/` | University brief and proposal template — read-only reference, never edit |

### Reading Order for `resources/specs/`

When context is needed, read specs in this order:

1. `resources/specs/Project Idea.md` — research question, 140-query benchmark design, three pipelines, dataset and judge methodology
2. `resources/specs/Architecture.md` — SQLite schema (full DDL), HLD/LLD, sequence diagrams, phase-by-phase module map, proposed repo layout
3. `resources/specs/Phase Plan.md` — 10-week, 8-phase build schedule
4. `resources/specs/Guardrails.md` — hard constraints for implementation (treat as binding, not advisory)
5. `resources/specs/Budget.md` — $0/free-tier cost model and Groq throughput math

---

## 3. Styling and Document Rules

All documents, slides, and Word files in this project follow the rules below. Pull from the source files rather than re-deriving values.

- **Colours**: `resources/assets/design/palette.md` ("Oxford Ink" colour system)
- **Typography**: `resources/assets/design/typography.md`
  - Body / references: **Garamond**
  - Headings / tables / diagrams / captions: **Calibri**
  - Code: **Consolas**
- **Language**: British English throughout
- **Punctuation**: No em dashes — use commas, semicolons (rarely). Use simple/spoken English punctuations.
- **Diagrams / charts / tables**: Built with native Word/PowerPoint features only — never attached images
- **References**: Harvard style with real, high-citation sources
- **Labelling**: `Figure X.Y` / `Table X.Y` (section.number)

### Post-build `.docx` Steps (macOS)

After rebuilding a `.docx`, clear the quarantine attribute before reopening:

```bash
xattr -c <file>.docx && chmod 644 <file>.docx
```

Validate with the docx skill's `validate.py`. Note: it has no schema for `wps`/`wpg` DrawingML namespaces, so it may pass files Word refuses to open — use native Word tables, not group shapes.

### PDF Verification

LibreOffice is installed at `/Applications/LibreOffice.app` but `soffice` is not on `PATH`. Extend `PATH` before using:

```bash
PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH" SAL_USE_VCLPLUGIN=svp soffice --headless --convert-to pdf yourfile.docx
```

Render PDF pages to images with PyMuPDF (confirmed installed), not `pdftoppm`:

```python
import fitz
fitz.open(path)[i].get_pixmap(dpi=130).save(...)
```

---

## 4. Implementation Guardrails (Binding)

When the project moves to the technical build, `resources/specs/Guardrails.md` is the binding constraint document. Key rules:

### Infrastructure
- **No per-hour or scale-to-non-zero infrastructure, ever.**
- Retrieval/indexing runs locally: FAISS/ChromaDB (P1), `rank_bm25` (P2), local `SummaryIndex` (P3)
- All LLM calls run on **Groq's free tier**

### Fixed Model Routing

| Role | Model |
|---|---|
| Generator | `openai/gpt-oss-120b` |
| Critic | `Qwen3.6-27B` (with search tool; no search for Judge) |
| P3 index build | `llama-3.1-8b-instant` |
| Pipeline Answerer | `Llama 3.3 70B` |
| Judge | `Qwen3.6-27B` |

Generator ≠ Critic family; Answerer ≠ Judge family — this is an anti-self-grading invariant.

### Pipeline Constraints
- **P2 must stay purely statistical**: `rank_bm25` only — never LlamaIndex's `KeywordTableIndex` (it calls an LLM and breaks the semantic-vs-statistical contrast)
- **Anti-leakage**: `queries` (100 PQ) / `golden_queries` (20 GQ) / `judge_validation` (20 JEQ) must remain disjoint sets. Pipelines receive only the query + their own retrieved nodes — never exemplars, ground truth, or answer-location hints. No metadata pre-filter for P1.

### Judge Gate
The Judge must clear a **>80% human-agreement gate** (Phase 2, on 20 JEQ × 3 pipelines = 60 outputs) before grading the full 900-run benchmark. This gate runs before the expensive full run.

### Loop Safety
Every loop script must include a hardcoded `LOCAL_TEST_THROTTLE` boolean (forces `LIMIT 3`) and must be run clean end-to-end at throttle before release to the full batch.

### Storage
- **SQLite (`aiosqlite`, WAL mode) is mandatory** — five tables per `resources/specs/Architecture.md` §3.2
- Resumable via `results.UNIQUE(source_set, query_id, pipeline, k_value)` — a crash never re-spends free-tier quota
- All LLM calls at `temperature = 0`; each benchmark cell runs once (no repeated sampling)

---

<!-- monitor:start -->
## monitor — operations log + reports

This project has **monitor** installed: a local logging/reporting workflow.
It keeps a project-local `monitor/` folder — a Dashboard linking a **Reports**
page (one self-contained HTML report per task/change) and a **Logs** page
(rendered from `monitor/logs/operations.log`). Rules for using it live in
the skill at `SKILL.md` (or `$CLAUDE_PLUGIN_ROOT/skills/monitor/SKILL.md`
when installed as a plugin) — read it before running any command below.

**When to use it:**
- After a state-changing operation (edit+build+commit can be one entry) —
  run `/monitor:log` or `/monitor:record` (log **and** report in one step).
- After code changes specifically — write a report with `/monitor:report`
  (or via `/monitor:record`). Never report a discussion or doc-only tweak.
- On failure, log it anyway with `status=failure` and the real error —
  don't skip logging just because the operation didn't succeed.

**Commands:**
| Command | Does |
|---|---|
| `/monitor:init` | First-time setup (idempotent). Run once per project. |
| `/monitor:log` | Append one operation entry to the log. |
| `/monitor:report` | Author one HTML report + rebuild the Reports index. |
| `/monitor:record` | Log, and if code changed, report — in one step. |
| `/monitor:update` | Re-detect + additively reconcile the profile, refresh assets. |
| `/monitor:clean-logs <N>` | Delete the newest N log entries; re-render Logs. |
| `/monitor:clean-reports <N>` | Delete the newest N reports; re-render Reports + Dashboard. |

**Rules:**
- Every command except `/monitor:init` requires `monitor/profile.json` to exist — it fails fast otherwise. Run init first if it's missing.
- Never hand-edit `monitor/logs/operations.log` — always go through `logger.py` (via `/monitor:log` or `/monitor:record`); hand-edits desync the log from the rendered Logs page.
- Reports are immutable snapshots — never rewrite an old report when the template changes; only new reports pick up new sections.
- `monitor/profile.json` evolves additively only — `/monitor:update` adds detected fields, never removes or renames existing ones.
<!-- monitor:end -->

---

## OpenWiki

This repository has documentation located in the /openwiki directory.

Start here:
- [OpenWiki quickstart](openwiki/quickstart.md)

OpenWiki includes repository overview, architecture notes, workflows, domain concepts, operations, integrations, testing guidance, and source maps.

When working in this repository, read the OpenWiki quickstart first, then follow its links to the relevant architecture, workflow, domain, operation, and testing notes.

---

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
