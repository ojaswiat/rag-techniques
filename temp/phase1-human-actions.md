# Phase 1 — Human Action Report

Generated after Phase 1 build. Two categories below: things already done
during the build (passive) and things still blocking full completion
(active, need your input).

## Active — needs your input before Phase 1 is fully closed out

- [ ] **Groq rate-limit numbers (RPD/TPD split)**: `project/groq_limits.md`
  captures live RPM/TPM-style figures from response headers (requests
  limit + tokens limit per stage), but Groq doesn't expose which window
  (per-minute vs per-day) each number belongs to, or the TPD ceiling at
  all, via the API. Visit https://console.groq.com/settings/limits and
  paste the RPM/RPD/TPM/TPD numbers you see there into `groq_limits.md`'s
  table. This blocks Phase 7 pacing decisions (the 900-run matrix), not
  Phases 1-6.

## Passive — already handled, no action needed unless you want to change it

- **Groq API key**: `project/.env` has a working `GROQ_API_KEY` — you
  fixed an initially-invalid key mid-build, and it's now verified live
  against all 5 model routes.
- **Model substitution**: Groq no longer hosts `qwen/qwen3-32b` (the
  model originally specced for Critic/Judge in `Guardrails.md`). You
  approved swapping to `qwen/qwen3.6-27b` project-wide. This is recorded
  in `resources/artifacts/Changes.md` and applied consistently across
  `project/config.py`, `CLAUDE.md`, `resources/specs/*.md`,
  `openwiki/*.md`, and `temp/directory-structure.md`. The anti-self-
  grading invariant (Generator ≠ Critic family, Answerer ≠ Judge family)
  still holds with the new model.
- `project/.env.example` was created with placeholder keys and setup
  instructions for both `GROQ_API_KEY` and `LLAMA_CLOUD_API_KEY` (the
  latter needed from Phase 2 onward, not Phase 1).
- `LOCAL_TEST_THROTTLE` defaults to `true` in `.env.example` — every
  future loop script inherits this safe default until you explicitly
  flip it.
- Five-table SQLite schema, WAL mode, and the resilient Groq client
  (backoff + 5-worker semaphore) are built and test-covered (15 tests,
  all passing) — no further setup needed for Phase 2 onward to start
  consuming them.
- A fresh-clone simulation (`rm -rf .venv && uv sync`) was run and
  verified clean, confirming the pinned dependency manifest installs
  without conflicts.

## Known cosmetic gaps (logged, not blocking)

- `project/README.md` and `project/.python-version` are referenced by
  `pyproject.toml` (`readme = "README.md"`) but were never created —
  a fresh clone's `pyproject.toml` points at a file that doesn't exist
  in the repo. Low priority; add them whenever convenient.
- The ASCII-art model-routing diagrams in `resources/specs/Architecture.md`
  §2.1 and `resources/specs/Guardrails.md` §2 have minor column
  misalignment after the `Qwen3-32b` → `Qwen3.6-27B` swap (2 characters
  longer). Purely visual, no markdown table is broken.
- `graphify-out/GRAPH_REPORT.md` may still show stale `Qwen3-32b`
  references in prose sections extracted from docs (the AST-only
  `graphify update .` run doesn't re-run the LLM-based doc extraction
  that produced those nodes). Re-run graphify's doc-update flow if you
  want the knowledge graph fully in sync; not required for the build.

## Not yet needed (deferred to their own phase)

- **LlamaParse account/key**: needed starting Phase 2 (ingestion). Get
  one at https://cloud.llamaindex.ai/api-key.
- **Filing manifest** (exact tickers/fiscal years): needed starting
  Phase 2 — `Architecture.md` §11 flags this as still open (illustrative
  AAPL/MSFT/TSLA example only, not a real decision yet).
