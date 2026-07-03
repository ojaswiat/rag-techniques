# CLAUDE.md — Agent Instructions

This file governs how the Claude Code agent operates within this repository. Read it fully before taking any action.

---

## 1. Project Overview

This is the workspace for a **COMP702 M.Sc. Dissertation**: a comparative benchmark of three RAG retrieval paradigms (semantic vector, statistical BM25, structural summary-tree) evaluated against SEC 10-K financial filings.

**Current state:** Planning and proposal phase. No implementation code exists yet. The technical build (Python, SQLite, `ingest/` / `pipelines/` / `judge/` modules) has not started. Phase 1 of `claude/specs/Phase Plan.md` is the next milestone.

---

## 2. The `claude/` Folder — Agent Steering Layer

The `claude/` directory is **not project source code**. It is the business and steering layer that drives the agent. Do not modify files inside `claude/` unless explicitly instructed. Always read from it; never write to it speculatively.

### `claude/` Subdirectory Reference

| Folder | Purpose |
|---|---|
| `claude/specs/` | Authoritative design documents — architecture, guardrails, budget, phase plan, project idea |
| `claude/artifacts/` | Deliverable files: proposals, papers, sheets, etc `.docx`, `.pdf`, `.xlsx`, `.csv`, `.md`, etc |
| `claude/assets/` | Meta assets for agent use: design palette, typography, diagrams (`.drawio`), data samples |
| `claude/docs/` | University brief and proposal template — read-only reference, never edit |
| `claude/logs/` | Brief operational logs tracking agent history and context across sessions |
| `claude/reports/` | Output folder for any report the agent is asked to generate |

### Reading Order for `claude/specs/`

When context is needed, read specs in this order:

1. `claude/specs/Project Idea.md` — research question, 140-query benchmark design, three pipelines, dataset and judge methodology
2. `claude/specs/Architecture.md` — SQLite schema (full DDL), HLD/LLD, sequence diagrams, phase-by-phase module map, proposed repo layout
3. `claude/specs/Phase Plan.md` — 10-week, 8-phase build schedule
4. `claude/specs/Guardrails.md` — hard constraints for implementation (treat as binding, not advisory)
5. `claude/specs/Budget.md` — $0/free-tier cost model and Groq throughput math

---

## 3. Styling and Document Rules

All documents, slides, and Word files in this project follow the rules below. Pull from the source files rather than re-deriving values.

- **Colours**: `claude/assets/design/palette.md` ("Oxford Ink" colour system)
- **Typography**: `claude/assets/design/typography.md`
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

When the project moves to the technical build, `claude/specs/Guardrails.md` is the binding constraint document. Key rules:

### Infrastructure
- **No per-hour or scale-to-non-zero infrastructure, ever.**
- Retrieval/indexing runs locally: FAISS/ChromaDB (P1), `rank_bm25` (P2), local `SummaryIndex` (P3)
- All LLM calls run on **Groq's free tier**

### Fixed Model Routing

| Role | Model |
|---|---|
| Generator | `openai/gpt-oss-120b` |
| Critic | `Qwen3-32b` (with search tool; no search for Judge) |
| P3 index build | `llama-3.1-8b-instant` |
| Pipeline Answerer | `Llama 3.3 70B` |
| Judge | `Qwen3-32b` |

Generator ≠ Critic family; Answerer ≠ Judge family — this is an anti-self-grading invariant.

### Pipeline Constraints
- **P2 must stay purely statistical**: `rank_bm25` only — never LlamaIndex's `KeywordTableIndex` (it calls an LLM and breaks the semantic-vs-statistical contrast)
- **Anti-leakage**: `queries` (100 PQ) / `golden_queries` (20 GQ) / `judge_validation` (20 JEQ) must remain disjoint sets. Pipelines receive only the query + their own retrieved nodes — never exemplars, ground truth, or answer-location hints. No metadata pre-filter for P1.

### Judge Gate
The Judge must clear a **>80% human-agreement gate** (Phase 2, on 20 JEQ × 3 pipelines = 60 outputs) before grading the full 900-run benchmark. This gate runs before the expensive full run.

### Loop Safety
Every loop script must include a hardcoded `LOCAL_TEST_THROTTLE` boolean (forces `LIMIT 3`) and must be run clean end-to-end at throttle before release to the full batch.

### Storage
- **SQLite (`aiosqlite`, WAL mode) is mandatory** — five tables per `claude/specs/Architecture.md` §3.2
- Resumable via `results.UNIQUE(source_set, query_id, pipeline, k_value)` — a crash never re-spends free-tier quota
- All LLM calls at `temperature = 0`; each benchmark cell runs once (no repeated sampling)

---

## 6. Logs

After significant operations, write a brief log entry to `claude/logs/` summarising what was done, decisions made, and any open issues. This preserves context across sessions and prevents re-deriving decisions already settled.

---

## 7. Reports

When asked to generate a report of any kind (grading, plagiarism check, analysis, evaluation, etc.), write the output to `claude/reports/`.
