# Working in this repo

What to watch out for when changing anything here. Sources: `CLAUDE.md`, `resources/specs/Guardrails.md`, `resources/assets/design/palette.md`, `resources/assets/design/typography.md`.

## The two-layer split

- **`project/`** holds all application and research code — pipelines, ingestion, judge, utilities, scripts, tests. **`CLAUDE.md` says `src/`**, but Phase 1 and Phase 2 were actually built under `project/` (it already carries its own `.venv`, `pyproject.toml`, and `uv.lock`). Follow the established practice — `project/` — not the stale instruction; new code goes there.
- **`resources/`** holds user files and assets: the steering and reference layer. Read from it freely; do not write to it speculatively. `resources/docs/` in particular is the university brief and proposal template, and is read-only. `resources/artifacts/Changes.md` specifically logs genuine deviations from the proposal/design spec (e.g. a spec-mandated model no longer being available) — it is not a general changelog for ordinary bugfixes, which belong in `monitor/` logs instead.

## Guardrails are binding, not advisory

`resources/specs/Guardrails.md` opens by addressing autonomous agents and developer scripts directly: you are prohibited from implementing anything that violates it. Treat every rule below as a hard constraint, and if a design change would break one, re-scope the change rather than the rule.

### The single hard rule

> No component in this project may bill per-hour or scale-to-non-zero.

No managed vector databases, no hosted search APIs, no paid embedding or reranking APIs, no premium parse tiers. All retrieval and indexing run locally; all LLM calls run on a free tier with rate limits rather than spend.

P3's one-time summary build is the one LLM-driven index build permitted, and it is not an exception to the rule: hierarchical summarisation is *the paradigm under test*, so its LLM use is legitimate and disclosed. It must use `llama-3.1-8b-instant`, run once, and be cached to disk — never rebuilt per query.

### Anti-leakage

Leakage would invalidate the results, so these are absolute:

- The three query sets — `queries` (100 PQ), `golden_queries` (20 GQ), `judge_validation` (20 JEQ) — must stay disjoint. No query in more than one table.
- Pipelines receive **only** the question and the nodes their own retriever returned. Never exemplars, never the ground-truth answer or citations, never an answer-location hint.
- No metadata pre-filter or section head-start for P1.
- GQ feeds the judge's prompt only, never a pipeline. JEQ feeds no prompt at all.

`tests/test_no_leakage.py` is specified for exactly this: asserting the answerer's prompt never contains anything beyond its own retrieved nodes.

### Loop safety

Every loop script — `async_generator.py`, `async_critic.py`, `loop_executor.py`, `async_judge.py`, and the P3 build script — must carry a hardcoded `LOCAL_TEST_THROTTLE` boolean at the top of the file. When true, it forces a strict cap of exactly 3 items (`LIMIT 3` in the SQL).

It stays **hardcoded per script and is never centralised**, because the point is that it must be consciously toggled in each file. The removal protocol is a whole-workflow one: run ingestion, P3 build, generation, critique, answering, and judging end to end under throttle, and only after a clean 3-item run may any script be released to the full batch.

### Determinism and state

- All LLM calls at `temperature = 0`; each of the 900 cells runs exactly once. Repeated runs multiply token cost without adding signal.
- SQLite with WAL mode is mandatory. Writing long-running batch output to CSV or nested JSON is forbidden — appending to an uncommitted flat file at run 700 of 900 can corrupt everything before it.
- Commit after each independent run, and resume from `results` on restart.

### The judge gate

The judge must clear **>80% human agreement** on the 60 gate outputs before it is allowed near the 900-run benchmark. Do not run the full matrix with an unvalidated judge. Details in [Benchmark design](benchmark-design.md#the-judge-validation-gate).

## Document and styling rules

All proposal, dissertation, and slide deliverables follow one house style. Pull values from the source files rather than re-deriving them.

- **Colours**: `resources/assets/design/palette.md` — the "Oxford Ink" system. A single blue hue varied by lightness, a blue-tinted neutral grey scale, and one reserved gold accent used sparingly for emphasis. It is the single source of truth for any Word template, PowerPoint master, or draw.io style library.
- **Typography**: `resources/assets/design/typography.md` — Garamond for body text and references, Calibri for all headings, tables, diagrams, and captions, Consolas for code.
- **Language**: British English throughout.
- **Punctuation**: no em dashes. Use commas and, rarely, semicolons. Simple spoken punctuation.
- **Diagrams, charts, tables**: built with native Word or PowerPoint features only — never attached images.
- **References**: Harvard style, real high-citation sources.
- **Labelling**: `Figure X.Y` / `Table X.Y`, section then number.
- **Page breaks**: never split a paragraph, diagram, table, figure, or chart across two pages.

### Rebuilding a `.docx` on macOS

Clear the quarantine attribute before reopening, or Word will refuse the file:

```bash
xattr -c <file>.docx && chmod 644 <file>.docx
```

Validate with the docx skill's `validate.py`. It has no schema for the `wps`/`wpg` DrawingML namespaces, so it can pass files Word still refuses to open — use native Word tables rather than group shapes.

### Verifying a PDF

LibreOffice is installed but `soffice` is not on `PATH`:

```bash
PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH" SAL_USE_VCLPLUGIN=svp \
  soffice --headless --convert-to pdf yourfile.docx
```

Render pages to images with PyMuPDF (confirmed installed), not `pdftoppm`:

```python
import fitz
fitz.open(path)[i].get_pixmap(dpi=130).save(...)
```

## Version drift

LlamaIndex changes fast and breaks syntax between minor versions. `Phase Plan.md` gives `llama-index==0.10.x` as an example pin, but `Architecture.md` §10 notes the current line is already 0.14.x. **Re-verify and pin exact versions at implementation time against current docs**, not against the example strings in the specs. Feed current documentation to any coding assistant so it does not invent parameters.

The same applies to Groq's free-tier limits and LlamaParse's credit allowances: both rotate frequently, and `Budget.md` figures are marked "verified mid-2026". Re-check at `console.groq.com` before any large batch run.

## Known stale or unresolved content

Worth knowing before trusting any single document:

- **`README.md`'s repository-layout section is stale.** It describes a `claude/` folder and does not mention `project/` or `resources/`.
- **`README.md` names Apple as the dataset**, while the confirmed corpus (per `project/data/filings_manifest.json`) is AAPL/MSFT/TSLA × FY2023–2025 — only AAPL is actually ingested so far. Prefer the manifest and `Architecture.md` over `README.md`.
- **`schemas/db_schema_example.jsonc`** is referenced by `Architecture.md` §11 item 1 as needing regeneration, but the file was deleted from the repo. §3.2's DDL is the sole source of truth for the schema.
- **Context-mass standardisation** is asserted in `Project Idea.md` §10 but not mechanically enforced anywhere (`Architecture.md` §11 item 4). The recommendation is to treat "same K" as the operational definition and document the token-volume variance as an accepted approximation. Awaiting the researcher's confirmation.
- **`TODO.md` is empty.**
- **`resources/artifacts/ProjectProposal.pdf` and `Proposal_v1.0.0.pdf` are the same document**, differing only in a rewritten §4. Treat v1.0.0 as canonical.

Where two documents disagree, `Architecture.md` (v2) wins — it was written specifically to resolve contradictions the earlier narrative specs left behind, and it records each resolution in its §1 table.

## The knowledge graph

`graphify-out/` holds a generated knowledge graph over this corpus — 1321 nodes across 185 communities as of the Phase 2 update, built from the specs, proposals, design assets, and now the Phase 1/2 source code. `CLAUDE.md` directs agents to query it before grepping raw files:

```bash
graphify query "<question>"        # scoped subgraph
graphify explain "<concept>"       # focused explanation
graphify path "<A>" "<B>"          # relationship between two concepts
graphify update .                  # refresh after changes (AST only, no API cost)
```

`graphify-out/GRAPH_REPORT.md` is the audit report; use it for broad architecture review when the scoped queries do not surface enough.
