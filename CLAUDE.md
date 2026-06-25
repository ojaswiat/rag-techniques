# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is the planning/proposal workspace for a COMP702 M.Sc. dissertation: a comparative benchmark of three RAG retrieval paradigms (semantic vector, statistical BM25, structural summary-tree) against SEC 10-K financial filings. **No implementation code exists yet** — the repository currently holds the design specs, the CA1 proposal deliverable, and styling assets. The technical build (Python, SQLite, the `ingest/`/`pipelines/`/`judge/` modules described in `specs/Architecture.md`) has not been started; Phase 1 of `specs/Phase Plan.md` is the next milestone whenever that work begins.

There is no build, lint, or test tooling to run yet — there is no `requirements.txt`, no source package, and no test suite in the repo.

## Repository layout

- `specs/` — the authoritative design documents, read in this order when context is needed:
  - `Project Idea.md` — the research question, the 140-query benchmark design, the three in-scope pipelines (P1 vector / P2 BM25 / P3 structural), the dataset-generation and judge-validation methodology.
  - `Architecture.md` — the technical build plan: SQLite ER diagram and full DDL (`nodes`, `queries`, `golden_queries`, `judge_validation`, `results`), HLD/LLD, sequence diagrams, phase-by-phase module map, proposed repo layout.
  - `Guardrails.md` — hard constraints for any future implementation (see below). Treat this as binding, not advisory.
  - `Budget.md` — the $0/free-tier cost model and Groq TPD/TPM throughput math.
  - `Phase Plan.md` — the 10-week, 8-phase build schedule this all maps onto.
- `artifacts/` — the actual CA1 proposal deliverable (`Proposal_v1.0.0.docx`/`.pdf`) and `prompt.md`, the brief used to generate it (typography, citation, diagram, and tone rules for that document).
- `assets/design/` — `palette.md` ("Oxford Ink" colour system) and `typography.md` (fonts/sizes), the single source of truth for any Word/PDF/PowerPoint/diagram styling in this project.
- `assets/diagrams/` — `.drawio` source diagrams for the architecture figures.
- `docs/` — official university brief (`ProposalGuidelines.pdf`, `ProposalTemplate.pdf`) — read-only reference, not to be edited.
- `reports/PROPOSAL_GRADING_REPORT.md` — a strict self-grading pass against the official brief; useful for understanding what the proposal still needs to address.
- `schemas/db_schema_example.jsonc` — **stale**: reflects an old 2-pipeline/600-row/12-JEQ design. `Architecture.md` §3 is the current schema; this file is flagged in `Architecture.md` §11 for regeneration and should not be trusted on its own.

## If implementing the technical build

When the project moves from planning to code, `specs/Guardrails.md` is the binding constraint document — it is written as strict rules for an autonomous coding agent, not suggestions. The load-bearing ones:

- **No per-hour or scale-to-non-zero infrastructure, ever.** Retrieval/indexing run locally (FAISS/ChromaDB for P1, `rank_bm25` for P2, local `SummaryIndex` for P3); all LLM calls run on Groq's free tier.
- **Fixed model routing, not swappable per convenience:** Generator = `openai/gpt-oss-120b`, Critic = `Qwen3-32b` (+ search tool, no search for the Judge), P3 index build = `llama-3.1-8b-instant`, shared pipeline Answerer = `Llama 3.3 70B`, Judge = `Qwen3-32b`. Generator ≠ Critic family; Answerer ≠ Judge family — this is an anti-self-grading invariant, not a style choice.
- **P2 must stay purely statistical** — `rank_bm25` only, never LlamaIndex's `KeywordTableIndex` (it calls an LLM and breaks the semantic-vs-statistical contrast).
- **Anti-leakage:** `queries` (100 PQ) / `golden_queries` (20 GQ) / `judge_validation` (20 JEQ) must stay disjoint. Pipelines receive only the query + their own retrieved nodes — never exemplars, ground truth, or answer-location hints. No metadata pre-filter for P1.
- **The Judge must clear a >80% human-agreement gate** (Phase 2, on the 20 JEQ × 3 pipelines = 60 outputs) before it is allowed to grade the full 900-run benchmark. This gate runs before, not after, the expensive full run.
- **Every loop script needs a hardcoded `LOCAL_TEST_THROTTLE` boolean** (forces `LIMIT 3`) and must be run clean end-to-end at that throttle before release to the full batch.
- **SQLite (`aiosqlite`, WAL mode) is mandatory**, not flat files — five tables per `Architecture.md` §3.2, resumable via `results.UNIQUE(source_set, query_id, pipeline, k_value)` so a crash never re-spends free-tier quota.
- All LLM calls run at `temperature = 0`; each benchmark cell runs once (no repeated sampling).

`Architecture.md` §1 documents eight design issues already found and resolved (e.g. the `judge_validation` cardinality fix, the `[[node:<node_id>]]` citation marker convention, JSON-in-`TEXT` storage for list columns) — check there before re-deriving a design decision the doc already settled.

## Working on documents (proposal/dissertation/slides)

This project generates polished Word/PDF/PowerPoint deliverables using the `docx` skill, not by hand-authoring `.docx` XML from scratch unless the skill's own tooling requires it.

- Styling is governed by `assets/design/palette.md` (colours) and `assets/design/typography.md` (fonts/sizes) — pull from these files rather than re-deriving choices. Typography is currently **Garamond** for body/references, **Calibri** for headings/tables/diagrams/captions, **Consolas** for code (this supersedes the original Optima request in `artifacts/prompt.md` — Optima did not make it into the final build).
- Hard rules carried across every document in this project: British English; no em dashes (commas/semicolons, or plain hyphens for ranges); diagrams/charts/tables built with native Word features only, never attached images; Harvard referencing with real, high-citation sources; figures/tables labelled `Figure X.Y` / `Table X.Y` (section.number).
- After rebuilding a `.docx` on macOS, clear any inherited quarantine attribute before reopening: `xattr -c <file>.docx && chmod 644 <file>.docx`.
- Validate generated OOXML with the docx skill's `validate.py` — note it has no schema for the `wps`/`wpg` DrawingML namespaces, so it will pass files that Word itself refuses to open. Native Word tables (not hand-built group shapes) are the proven-safe way to build diagrams in this project.
- **LibreOffice is installed** at `/Applications/LibreOffice.app` but `soffice` is not on `PATH`, so the docx skill's `scripts/office/soffice.py` wrapper (which calls bare `soffice`) fails with `FileNotFoundError` unless `PATH` is extended first. Use it for real PDF/visual verification of `.docx` edits — don't skip this step on the assumption LibreOffice is unavailable:
  ```bash
  PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH" SAL_USE_VCLPLUGIN=svp soffice --headless --convert-to pdf yourfile.docx
  ```
  `pdftoppm`/Poppler is not installed, so render PDF pages to images with PyMuPDF (`python3 -c "import fitz; ..."`, confirmed installed) instead, e.g. `fitz.open(path)[i].get_pixmap(dpi=130).save(...)`.
