# Docstring and Comment Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite every docstring and comment in all 90 Python files, 48 source and 42 test, so they read like a senior engineer wrote them: short, factual, and about the code rather than about the specs.

**Architecture:** Prose-only edits. No executable line changes anywhere. Each task takes one package, rewrites its docstrings and comments, then proves nothing executable moved by comparing the Python AST with all docstrings stripped, before and after. Work lands on `presentation`; `dev` fast-forwards at the end because it is already an ancestor.

**Tech Stack:** Python 3.13, `ast` module (stdlib) for the equivalence check, pytest 9.1 for the regression suite, `uv`-managed venv at `project/.venv`.

**Spec:** This plan is its own spec. The style contract is Task 0 below. Supporting constraints come from `CLAUDE.md` (no development history in code) and the `avoid-ai-writing` skill at `.claude/skills/avoid-ai-writing/SKILL.md`.

## Global Constraints

- **Never change an executable line.** Not one. No renames, no reordering, no import changes, no formatting of code. The AST check in every task is what enforces this, and a task that fails it is not done.
- **Run everything through the project venv:** `project/.venv/bin/python`. Never bare `python3`, never `pip`.
- **The full test suite must stay at 339 passed, 2 skipped** after every task.
- **Work on branch `presentation`.** Do not touch `dev` until Task 7.
- **No development history in comments.** No "previously", "used to", "was changed to", "fixed a bug where", no session or agent references, no `Doubt:` tags. Describe the code as it is.
- **British English**, matching the rest of the repo.
- **Two phases.** Phase 1 is the 48 source files (Tasks 1 to 7). Phase 2 is the 42 files under `project/tests/` (Tasks 8 to 12). `dev` moves only in Task 13, after both.
- **Commit after every task**, with the message given in that task's final step.

---

## Task 0: Style contract and the AST equivalence checker

This task produces the tool every later task depends on, plus the written style rules those tasks apply. Read this task in full before starting any other.

### The style contract

Apply these rules to every docstring and comment you touch.

**Module docstrings: 1 to 3 lines.** State what the module does. Stop.

Before, from `pipelines/answerer.py`, 15 lines:

```python
"""Shared Answerer: turns (query, retrieved nodes) into a cited answer.

One Answerer serves all three pipelines (Architecture.md §4.1). Holding the
generation step constant is what makes the benchmark a comparison of
*retrieval* strategies -- any difference in answer quality between P1, P2
and P3 must come from which nodes reached this class, never from how those
nodes were turned into prose.

Anti-leakage (Architecture.md §4.1, Guardrails.md §3): the prompt carries
only the query text and the retrieved nodes' ids and content. No
exemplars, no ground-truth answer, no gt_citations, no quadrant label, and
no node metadata -- a node's parent_item_header or page number would hint
at where the answer lives, which is exactly what the retrieval step is
being measured on.
"""
```

After, 4 lines:

```python
"""Turns a query plus its retrieved nodes into a cited answer.

All three pipelines share one Answerer so that score differences come from
retrieval rather than generation. The prompt gets the query text and the
nodes' ids and content, nothing else.
"""
```

**Function and method docstrings: one line, unless the signature genuinely needs more.** A one-line summary in the imperative or third person. Add an `Args:`/`Returns:` block only when a parameter's meaning or a return shape is not obvious from its name and type hint. Delete docstrings on private helpers whose name already says it, like `_headers()`.

One case that always counts as not obvious: **a return annotation of `Any`, or no return annotation at all.** The hint tells the reader nothing, so keep a one-line `Returns:` naming the real type and what it is for. The same applies to a parameter whose behaviour when omitted is not visible from its default.

**Comments explain why, never what.** Delete any comment that restates the line under it. Keep the ones that record a non-obvious reason: a workaround for an upstream bug, a rate limit, an ordering requirement, a constraint that would look wrong to a reader who did not know it.

Keep, because the reason is not visible in the code:

```python
# "recent" is a fixed-size window, not a fixed time window, so a frequent
# filer's 10-K can age out of it within a couple of years.
```

Delete, because the code already says it:

```python
# Loop over each filing and fetch it
for filing in filings:
```

**At most one spec reference per file**, in the module docstring, and only where the spec constrains behaviour the code cannot show on its own. There are currently 102 across 48 files. Drop the inline ones. `Architecture.md §4.5a` mid-sentence in a function body is archaeology.

**No `--` as an em-dash substitute.** There are 103. Use a comma, a full stop, or brackets. Rewrite the sentence if none of those fit.

**Cut the emphasis scaffolding.** No `*italics*` for stress. No "which is exactly what", "it is worth noting", "worth stating plainly". There are 36 uses of "never" doing emphatic work; keep it only where it states a real invariant, such as an anti-leakage rule.

**Do not invent.** If a docstring claims something you cannot verify from the code in front of you, cut the claim rather than restate it. Never add a number, a model name, or a mechanism that is not already in the file.

### Steps

- [ ] **Step 1: Write the AST equivalence checker**

Create `project/scripts/check_docstrings_only.py`:

```python
"""Verifies that a rewrite touched only docstrings, never executable code.

Compares the AST of two revisions of the same file with every docstring
replaced by a placeholder. If the dumps differ, something other than a
docstring moved.
"""
import ast
import subprocess
import sys


_DOC_HOLDERS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if not isinstance(node, _DOC_HOLDERS):
            continue
        body = node.body
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            first.value.value = "<docstring>"
    return tree


def normalise(source: str) -> str:
    return ast.dump(strip_docstrings(ast.parse(source)), annotate_fields=True)


def git_show(rev: str, path: str) -> str:
    out = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: check_docstrings_only.py <git-rev> <file> [<file>...]")
        return 2
    rev, paths = argv[1], argv[2:]
    failures = []
    for path in paths:
        try:
            before = normalise(git_show(rev, path))
        except subprocess.CalledProcessError:
            print(f"SKIP (new file) {path}")
            continue
        with open(path, encoding="utf-8") as handle:
            after = normalise(handle.read())
        if before != after:
            failures.append(path)
            print(f"FAIL {path}: executable code changed")
        else:
            print(f"ok   {path}")
    if failures:
        print(f"\n{len(failures)} file(s) changed more than docstrings")
        return 1
    print(f"\nall {len(paths)} file(s) docstring-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 2: Prove the checker catches a real code change**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
cp pipelines/answerer.py /tmp/answerer.bak
printf '\nUNUSED_SENTINEL = 1\n' >> pipelines/answerer.py
.venv/bin/python scripts/check_docstrings_only.py HEAD pipelines/answerer.py
```

Expected: `FAIL pipelines/answerer.py: executable code changed`, exit code 1.

- [ ] **Step 3: Prove the checker passes a docstring-only change**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
cp /tmp/answerer.bak pipelines/answerer.py
.venv/bin/python - <<'EOF'
import pathlib
p = pathlib.Path("pipelines/answerer.py")
t = p.read_text(encoding="utf-8")
p.write_text(t.replace('"""Shared Answerer:', '"""CHECKER PROBE Answerer:', 1), encoding="utf-8")
EOF
.venv/bin/python scripts/check_docstrings_only.py HEAD pipelines/answerer.py
```

Expected: `ok   pipelines/answerer.py`, exit code 0.

- [ ] **Step 4: Restore the probe file**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
cp /tmp/answerer.bak pipelines/answerer.py
git diff --stat pipelines/answerer.py
```

Expected: no output. The file is back to its committed state.

- [ ] **Step 5: Record the baseline**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
git rev-parse HEAD > /tmp/docstring-baseline-rev
cat /tmp/docstring-baseline-rev
```

Expected: `339 passed, 2 skipped`. Save that revision; every later task passes it to the checker.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/scripts/check_docstrings_only.py docs/superpowers/plans/2026-08-20-docstring-simplification.md
git commit -m "chore(scripts): add AST checker proving a rewrite touched only docstrings"
```

---

## Task 1: `llm_client/` (7 files)

Start here. It is the smallest package with real prose and it sets the tone the later tasks copy.

**Files:**
- Modify: `project/llm_client/__init__.py`
- Modify: `project/llm_client/config.py`
- Modify: `project/llm_client/llm_factory.py`
- Modify: `project/llm_client/groq_client.py`
- Modify: `project/llm_client/nim_client.py`
- Modify: `project/llm_client/openrouter_client.py`
- Modify: `project/llm_client/utils.py`
- Test: `project/tests/test_llm_factory.py`, `project/tests/test_config.py`, `project/tests/test_llm_client_nim.py`, `project/tests/test_llm_client_openrouter.py`, `project/tests/test_groq_client_backoff.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0, invoked as `.venv/bin/python scripts/check_docstrings_only.py <baseline-rev> <files...>`.
- Produces: nothing importable. Later tasks reuse only the style contract in Task 0 and the checker.

- [ ] **Step 1: Read all seven files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in llm_client/*.py; do echo "===== $f ====="; cat "$f"; done
```

Do not edit yet. You need the whole package in context before deciding what a comment is for.

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract to all seven files. One note specific to this package: `config.py` carries the line `# Guardrails.md §2 — fixed model routing matrix. Do not change without updating the spec.` Keep that comment. It records a real cross-file obligation a reader cannot infer, and it is the one spec reference this file is allowed.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" llm_client/*.py
```

Expected: `ok` on every file, then `all 7 file(s) docstring-only`, exit code 0. If any line says FAIL, you changed code. Revert that file with `git checkout -- <path>` and redo it.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Check the prose actually got simpler**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'EOF'
import re, pathlib
files = sorted(pathlib.Path("llm_client").glob("*.py"))
dash = specs = 0
for p in files:
    t = p.read_text(encoding="utf-8")
    dash += len(re.findall(r'\S\s--\s\S', t))
    specs += sum(
        1 for line in t.splitlines()
        if re.search(r'(Architecture|Guardrails|Budget|deviations)\.md|§\s?\d', line)
    )
print(f"remaining '--' dashes:    {dash}")
print(f"remaining spec-ref lines: {specs}")
EOF
```

Expected: `--` dashes at 0, spec-ref lines at 1 (the `config.py` routing-matrix comment kept in Step 2). Count lines, not regex matches: that one comment contains both `Guardrails.md` and `§2`, so a match count reports 2 for a single reference.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/llm_client/
git commit -m "docs(llm_client): simplify docstrings and comments"
```

---

## Task 2: `ingest/` (6 files)

**Files:**
- Modify: `project/ingest/__init__.py`
- Modify: `project/ingest/fetch_filings.py`
- Modify: `project/ingest/parse_filing.py`
- Modify: `project/ingest/node_builder.py`
- Modify: `project/ingest/parsing_audit.py`
- Modify: `project/ingest/run_ingestion.py`
- Test: `project/tests/test_fetch_filings.py`, `project/tests/test_parse_filing.py`, `project/tests/test_node_builder.py`, `project/tests/test_parsing_audit.py`, `project/tests/test_run_ingestion.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read all six files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in ingest/*.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract. Two package-specific notes.

`fetch_filings.py` has a comment explaining the SEC `recent` window. Keep the reason, drop the length:

```python
    # High-filing-frequency issuers (e.g. banks filing frequent 8-Ks/prospectus
    # supplements) can push a 10-K out of "recent" within a couple of years --
    # "recent" is a fixed-size window, not a fixed time window. Fall back to
    # the paginated older-filings archives (newest page first) if needed.
```

becomes:

```python
    # "recent" is a fixed-size window, not a fixed time window, so a frequent
    # filer's 10-K can drop out of it within a couple of years. Fall back to
    # the paginated archives, newest page first.
```

`node_builder.py` has a 10-line module docstring. Cut it to at most 3 lines describing what a node is and what the module produces.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" ingest/*.py
```

Expected: `all 6 file(s) docstring-only`, exit code 0.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/ingest/
git commit -m "docs(ingest): simplify docstrings and comments"
```

---

## Task 3: `pipelines/` (15 files)

The largest package. It covers the shared base plus all three retrieval pipelines.

**Files:**
- Modify: `project/pipelines/__init__.py`, `project/pipelines/base.py`, `project/pipelines/answerer.py`
- Modify: `project/pipelines/vector/__init__.py`, `project/pipelines/vector/build_vector_index.py`, `project/pipelines/vector/fastembed_reranker.py`, `project/pipelines/vector/p1_vector.py`
- Modify: `project/pipelines/bm25/__init__.py`, `project/pipelines/bm25/tokenizer.py`, `project/pipelines/bm25/build_bm25_index.py`, `project/pipelines/bm25/p2_bm25.py`
- Modify: `project/pipelines/structural/__init__.py`, `project/pipelines/structural/node_convert.py`, `project/pipelines/structural/build_summary_index.py`, `project/pipelines/structural/p3_structural.py`
- Test: `project/tests/test_answerer.py`, `project/tests/test_base_retriever.py`, `project/tests/test_p1_vector.py`, `project/tests/test_p2_bm25.py`, `project/tests/test_p3_structural.py`, `project/tests/test_build_vector_index.py`, `project/tests/test_build_bm25_index.py`, `project/tests/test_build_summary_index.py`, `project/tests/test_fastembed_reranker.py`, `project/tests/test_tokenizer.py`, `project/tests/test_node_convert.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read the package end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in pipelines/*.py pipelines/*/*.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite `answerer.py` first**

Use the exact before/after in Task 0's style contract as the target. It is the reference rewrite for this whole task.

- [ ] **Step 3: Rewrite the remaining 14 files**

Apply the Task 0 style contract. Two package-specific notes.

`base.py` defines the shared `Retriever` ABC. Its method docstrings are the contract three implementations rely on, so keep an `Args:`/`Returns:` block on the abstract `retrieve` method even though the contract says one line by default. An interface others implement against is exactly the case where more than one line earns its place.

`tokenizer.py` holds the regex tokeniser shared by P2 and the Critic's search tool. If a comment explains a specific regex decision, such as how commas inside numbers are handled, keep that reason. It is not recoverable from the pattern alone.

- [ ] **Step 4: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" pipelines/*.py pipelines/*/*.py
```

Expected: `all 15 file(s) docstring-only`, exit code 0.

- [ ] **Step 5: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/pipelines/
git commit -m "docs(pipelines): simplify docstrings and comments"
```

---

## Task 4: `dataset_generation/` (9 files)

This package holds the two longest docstrings in the codebase, both 30 lines.

**Files:**
- Modify: `project/dataset_generation/__init__.py`
- Modify: `project/dataset_generation/async_generator.py`
- Modify: `project/dataset_generation/async_critic.py`
- Modify: `project/dataset_generation/search_tool.py`
- Modify: `project/dataset_generation/cross_check.py`
- Modify: `project/dataset_generation/section_grouper.py`
- Modify: `project/dataset_generation/run_dataset_generation.py`
- Modify: `project/dataset_generation/gq_label_export.py`
- Modify: `project/dataset_generation/gq_label_import.py`
- Test: `project/tests/test_async_generator.py`, `project/tests/test_async_critic.py`, `project/tests/test_search_tool.py`, `project/tests/test_cross_check.py`, `project/tests/test_section_grouper.py`, `project/tests/test_run_dataset_generation.py`, `project/tests/test_gq_labeling.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read the package end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in dataset_generation/*.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Cut the two 30-line module docstrings first**

`run_dataset_generation.py` and `cross_check.py` are the worst offenders. Target 3 lines each. Everything they currently explain about quadrant strata, retry policy, and the disjointness rule belongs in `resources/specs/`, which already documents it.

- [ ] **Step 3: Rewrite the remaining 7 files**

Apply the Task 0 style contract. One package-specific note: the anti-leakage rules in `async_critic.py` and `search_tool.py` are real invariants, so a one-line statement of each survives. The Critic being blind to the Generator's answer and citations is a property a reader cannot see from the call site, and breaking it silently invalidates the dataset. State it once, plainly, and drop the paragraph around it.

- [ ] **Step 4: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" dataset_generation/*.py
```

Expected: `all 9 file(s) docstring-only`, exit code 0.

- [ ] **Step 5: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`. This package has the heaviest test coverage in the repo, so a failure here is a real signal, not flake.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/dataset_generation/
git commit -m "docs(dataset_generation): simplify docstrings and comments"
```

---

## Task 5: `judge/` (4 files)

**Files:**
- Modify: `project/judge/__init__.py`
- Modify: `project/judge/async_judge.py`
- Modify: `project/judge/metrics.py`
- Modify: `project/judge/numeric_normalizer.py`
- Test: `project/tests/test_async_judge.py`, `project/tests/test_metrics.py`, `project/tests/test_numeric_normalizer.py`, `project/tests/test_exact_match.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read all four files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in judge/*.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract. `async_judge.py`'s 17-line module docstring currently lists three Guardrails invariants as a bulleted essay. Two of them survive as plain statements because they constrain behaviour the code does not show: the prompt carries only the five quadrant-matched exemplars, and the citation check is computed in code rather than asked of the model. The third, that the Judge has no search tool, is already visible from the `achat()` call, so drop it.

`numeric_normalizer.py` handles financial-figure comparison. Any comment recording a specific normalisation decision, such as how a figure in thousands is reconciled against one in millions, states a rule that is not obvious from the arithmetic. Keep those, shortened.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" judge/*.py
```

Expected: `all 4 file(s) docstring-only`, exit code 0.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/judge/
git commit -m "docs(judge): simplify docstrings and comments"
```

---

## Task 6: Package root (7 files)

**Files:**
- Modify: `project/__init__.py`
- Modify: `project/conftest.py`
- Modify: `project/database_manager.py`
- Modify: `project/loop_executor.py`
- Modify: `project/loop_template.py`
- Modify: `project/score_gate_outputs.py`
- Modify: `project/validation_gate.py`
- Test: `project/tests/test_database_manager.py`, `project/tests/test_database_manager_judge.py`, `project/tests/test_loop_executor.py`, `project/tests/test_loop_template.py`, `project/tests/test_score_gate_outputs.py`, `project/tests/test_validation_gate.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read all seven files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in __init__.py conftest.py database_manager.py loop_executor.py loop_template.py score_gate_outputs.py validation_gate.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite `loop_executor.py` first**

Its 23-line module docstring is the third longest in the codebase. Target 4 lines. Two facts in it survive because a reader cannot recover them from the code: resumability rests on the `UNIQUE(source_set, query_id, pipeline, k_value)` constraint, and retrievers are injected rather than imported because constructing all three eagerly would make a single-pipeline run pay for all of them. Everything else, including the list of columns the Judge fills in later, goes.

- [ ] **Step 3: Rewrite the remaining 6 files**

Apply the Task 0 style contract. `loop_template.py` is the shared throttle helper every loop script calls, so its docstring states the contract other modules code against. One or two lines, but keep the fact that `LOCAL_TEST_THROTTLE` comes from `config.py` rather than each script declaring its own.

- [ ] **Step 4: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" __init__.py conftest.py database_manager.py loop_executor.py loop_template.py score_gate_outputs.py validation_gate.py
```

Expected: `all 7 file(s) docstring-only`, exit code 0.

- [ ] **Step 5: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/__init__.py project/conftest.py project/database_manager.py project/loop_executor.py project/loop_template.py project/score_gate_outputs.py project/validation_gate.py
git commit -m "docs(project): simplify docstrings and comments in package root"
```

---

## Task 7: Source-phase verification gate

**Files:**
- Modify: none. This task only verifies.

**Interfaces:**
- Consumes: every commit from Tasks 1 to 6.
- Produces: a verified source phase. The tests phase (Tasks 8 to 12) starts from here, and `dev` moves only in Task 13.

- [ ] **Step 1: Re-verify all 48 files against the original baseline**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" \
  $(find . -name '*.py' -not -path './.venv/*' -not -path '*__pycache__*' -not -path './tests/*' -not -path './scripts/*')
```

Expected: `all 48 file(s) docstring-only`, exit code 0. This is the single check that matters. It proves the entire six-task sequence moved no executable line.

- [ ] **Step 2: Confirm the prose targets were hit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'EOF'
import re, pathlib
src = [p for p in pathlib.Path('.').rglob('*.py')
       if '.venv' not in p.parts and '__pycache__' not in p.parts
       and 'tests' not in p.parts and 'scripts' not in p.parts]
dash = specs = 0
lens = []
for p in src:
    t = p.read_text(encoding='utf-8')
    dash += len(re.findall(r'\S\s--\s\S', t))
    specs += sum(
        1 for line in t.splitlines()
        if re.search(r'(Architecture|Guardrails|Budget|deviations)\.md|§\s?\d', line)
    )
    m = re.match(r'\s*(?:r|u)?"""(.*?)"""', t, re.S)
    if m:
        lens.append(m.group(1).count('\n') + 1)
print(f"files:               {len(src)}   (baseline 48)")
print(f"'--' dashes:         {dash}   (baseline 103, target 0)")
print(f"spec-ref lines:      {specs}   (baseline 102, target <= 48)")
print(f"longest docstring:   {max(lens)} lines   (baseline 30, target <= 6)")
print(f"mean docstring:      {sum(lens)/len(lens):.1f} lines   (baseline 9.2, target <= 4)")
EOF
```

Expected: dashes at 0, spec refs at 48 or fewer, longest module docstring 6 lines or fewer, mean 4 lines or fewer. If any target is missed, name the files that miss it and fix them before continuing.

- [ ] **Step 3: Run the full suite one final time**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 4: Confirm the working tree is clean and everything is committed**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git status --short
git log --oneline "$(cat /tmp/docstring-baseline-rev)"..presentation
```

Expected: empty status, and seven commits listed (Task 0 plus Tasks 1 to 6).

- [ ] **Step 5: Report and hand over to the tests phase**

Print the before/after metrics from Step 2. Do not move any branch pointer. `dev` stays where it is until Task 13.

---

# Phase 2: test files

The 42 files under `project/tests/` total 6,240 lines and carry 53 `--` dashes, 20 spec-reference lines, and 17 module docstrings averaging 7.6 lines. Lighter than the source phase, with one difference that changes the work.

**A test's name is its documentation.** `test_fetch_filing_falls_back_to_paginated_archives` already says what the test does, so a docstring reading "Tests that fetch_filing falls back to paginated archives" is pure restatement. In this phase the default action on a test docstring is **delete**, not shorten. Keep one only where it records something the name cannot: why the fixture is shaped oddly, what upstream bug the case pins, which edge case the numbers encode.

**The AST checker matters more here, not less.** A silently altered assertion is worse than a silently altered source line, because the suite would still pass while testing something different. Every task in this phase runs the same check.

The style contract in Task 0 applies unchanged, including both Task 1 rulings: never add a module docstring where none exists, and keep a one-line `Returns:` when the annotation is `Any` or absent.

---

## Self-review

**Spec coverage.** The style contract in Task 0 has seven rules: module docstring length, function docstring length, comments explain why, one spec reference per file, no `--`, no emphasis scaffolding, and do not invent. Tasks 1 to 6 each apply all seven across their package, and Task 7 Step 2 measures four of them numerically. The three that cannot be measured by regex, comments explaining why, one line per function, and do not invent, are covered by the per-task reviewer gate that subagent-driven-development provides.

**Placeholder scan.** No TBD, no "similar to Task N", no "handle edge cases". The checker script is given in full rather than described. Every verification step names the command and the expected output. The one deliberate repetition is the style contract, which lives in Task 0 and is referenced rather than restated, because a subagent reads Task 0 first by instruction in the task header.

**Type consistency.** The checker is `project/scripts/check_docstrings_only.py` in every task that invokes it, always with the same two-argument shape, `<git-rev> <files...>`. The baseline revision is written to `/tmp/docstring-baseline-rev` in Task 0 Step 5 and read back with `$(cat /tmp/docstring-baseline-rev)` in Tasks 1 to 7. Test counts are `339 passed, 2 skipped` throughout.

**One gap worth naming.** `/tmp/docstring-baseline-rev` does not survive a machine reboot between tasks. If it is missing, recover it with `git log --oneline --all | grep "add AST checker"` and use the commit immediately before that one.

---

## Task 8: Client and loop tests (7 files)

**Files:**
- Modify: `project/tests/__init__.py`, `project/tests/test_config.py`, `project/tests/test_llm_factory.py`, `project/tests/test_llm_client_nim.py`, `project/tests/test_llm_client_openrouter.py`, `project/tests/test_groq_client_backoff.py`, `project/tests/test_loop_template.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable. Sets the tone Tasks 9 to 12 copy for test prose.

- [ ] **Step 1: Read all seven files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in tests/__init__.py tests/test_config.py tests/test_llm_factory.py tests/test_llm_client_nim.py tests/test_llm_client_openrouter.py tests/test_groq_client_backoff.py tests/test_loop_template.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract, with the phase-2 default: delete a test docstring that restates its function name. These files cover provider clients and the shared throttle helper, so the comments worth keeping are the ones recording a provider's real limit or why a mock is shaped the way it is. A comment saying "patch the client" above a `patch.object` call is not.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" tests/__init__.py tests/test_config.py tests/test_llm_factory.py tests/test_llm_client_nim.py tests/test_llm_client_openrouter.py tests/test_groq_client_backoff.py tests/test_loop_template.py
```

Expected: `all 7 file(s) docstring-only`, exit code 0.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/tests/__init__.py project/tests/test_config.py project/tests/test_llm_factory.py project/tests/test_llm_client_nim.py project/tests/test_llm_client_openrouter.py project/tests/test_groq_client_backoff.py project/tests/test_loop_template.py
git commit -m "docs(tests): simplify docstrings and comments in client and loop tests"
```

---

## Task 9: Ingestion and storage tests (8 files)

**Files:**
- Modify: `project/tests/test_fetch_filings.py`, `project/tests/test_parse_filing.py`, `project/tests/test_node_builder.py`, `project/tests/test_parsing_audit.py`, `project/tests/test_run_ingestion.py`, `project/tests/test_filings_manifest.py`, `project/tests/test_database_manager.py`, `project/tests/test_database_manager_judge.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read all eight files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in tests/test_fetch_filings.py tests/test_parse_filing.py tests/test_node_builder.py tests/test_parsing_audit.py tests/test_run_ingestion.py tests/test_filings_manifest.py tests/test_database_manager.py tests/test_database_manager_judge.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract and the phase-2 default. Two notes. `test_fetch_filings.py` contains fixtures built from real SEC accession numbers and report dates; a comment explaining why a fixture uses a particular date shape records an upstream fact and survives. `test_database_manager.py` and `test_database_manager_judge.py` cover the five-table SQLite schema, and any comment recording a schema constraint the assertion depends on, such as the `UNIQUE(source_set, query_id, pipeline, k_value)` resumability key, states something the test body alone does not show.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" tests/test_fetch_filings.py tests/test_parse_filing.py tests/test_node_builder.py tests/test_parsing_audit.py tests/test_run_ingestion.py tests/test_filings_manifest.py tests/test_database_manager.py tests/test_database_manager_judge.py
```

Expected: `all 8 file(s) docstring-only`, exit code 0.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/tests/test_fetch_filings.py project/tests/test_parse_filing.py project/tests/test_node_builder.py project/tests/test_parsing_audit.py project/tests/test_run_ingestion.py project/tests/test_filings_manifest.py project/tests/test_database_manager.py project/tests/test_database_manager_judge.py
git commit -m "docs(tests): simplify docstrings and comments in ingestion and storage tests"
```

---

## Task 10: Pipeline tests (11 files)

**Files:**
- Modify: `project/tests/test_answerer.py`, `project/tests/test_base_retriever.py`, `project/tests/test_p1_vector.py`, `project/tests/test_p2_bm25.py`, `project/tests/test_p3_structural.py`, `project/tests/test_build_vector_index.py`, `project/tests/test_build_bm25_index.py`, `project/tests/test_build_summary_index.py`, `project/tests/test_fastembed_reranker.py`, `project/tests/test_tokenizer.py`, `project/tests/test_node_convert.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read all eleven files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in tests/test_answerer.py tests/test_base_retriever.py tests/test_p1_vector.py tests/test_p2_bm25.py tests/test_p3_structural.py tests/test_build_vector_index.py tests/test_build_bm25_index.py tests/test_build_summary_index.py tests/test_fastembed_reranker.py tests/test_tokenizer.py tests/test_node_convert.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract and the phase-2 default. Three notes. `test_p2_bm25.py` uses a three-document corpus specifically because BM25's inverse document frequency goes to zero on a smaller one, and that reason must survive in some form; without it the corpus size looks arbitrary and a later reader will shrink it. `test_answerer.py` covers the anti-leakage rule that the prompt carries only the query and retrieved nodes, which is a real invariant worth one plain line. `test_tokenizer.py` pins specific tokenisation decisions, so a comment naming the input that motivated a case is recording an example, not narrating the code.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" tests/test_answerer.py tests/test_base_retriever.py tests/test_p1_vector.py tests/test_p2_bm25.py tests/test_p3_structural.py tests/test_build_vector_index.py tests/test_build_bm25_index.py tests/test_build_summary_index.py tests/test_fastembed_reranker.py tests/test_tokenizer.py tests/test_node_convert.py
```

Expected: `all 11 file(s) docstring-only`, exit code 0.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/tests/test_answerer.py project/tests/test_base_retriever.py project/tests/test_p1_vector.py project/tests/test_p2_bm25.py project/tests/test_p3_structural.py project/tests/test_build_vector_index.py project/tests/test_build_bm25_index.py project/tests/test_build_summary_index.py project/tests/test_fastembed_reranker.py project/tests/test_tokenizer.py project/tests/test_node_convert.py
git commit -m "docs(tests): simplify docstrings and comments in pipeline tests"
```

---

## Task 11: Dataset-generation tests (8 files)

The heaviest package by test volume. `test_run_dataset_generation.py` alone is over 1,300 lines.

**Files:**
- Modify: `project/tests/test_async_generator.py`, `project/tests/test_async_critic.py`, `project/tests/test_async_critic_live_smoke.py`, `project/tests/test_search_tool.py`, `project/tests/test_cross_check.py`, `project/tests/test_section_grouper.py`, `project/tests/test_run_dataset_generation.py`, `project/tests/test_gq_labeling.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable.

- [ ] **Step 1: Read all eight files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in tests/test_async_generator.py tests/test_async_critic.py tests/test_async_critic_live_smoke.py tests/test_search_tool.py tests/test_cross_check.py tests/test_section_grouper.py tests/test_gq_labeling.py; do echo "===== $f ====="; cat "$f"; done
wc -l tests/test_run_dataset_generation.py
```

Read `test_run_dataset_generation.py` in sections rather than one call. It is the largest file in the repo.

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract and the phase-2 default. Three notes. `test_async_critic_live_smoke.py` has the longest module docstring in the test suite at 22 lines, and it is one of the two tests skipped by default; its docstring must still say how to run it, because that is the one thing a reader cannot get from the code. `test_async_critic.py` covers the Critic being blind to the Generator's answer and citations, which is a dataset-validity invariant and survives as one line. In `test_run_dataset_generation.py`, expect many `monkeypatch.setattr(... LOCAL_TEST_THROTTLE ...)` lines with comments restating them; those comments go.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" tests/test_async_generator.py tests/test_async_critic.py tests/test_async_critic_live_smoke.py tests/test_search_tool.py tests/test_cross_check.py tests/test_section_grouper.py tests/test_run_dataset_generation.py tests/test_gq_labeling.py
```

Expected: `all 8 file(s) docstring-only`, exit code 0.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/tests/test_async_generator.py project/tests/test_async_critic.py project/tests/test_async_critic_live_smoke.py project/tests/test_search_tool.py project/tests/test_cross_check.py project/tests/test_section_grouper.py project/tests/test_run_dataset_generation.py project/tests/test_gq_labeling.py
git commit -m "docs(tests): simplify docstrings and comments in dataset-generation tests"
```

---

## Task 12: Judge and gate tests (8 files)

**Files:**
- Modify: `project/tests/test_async_judge.py`, `project/tests/test_async_judge_live_smoke.py`, `project/tests/test_metrics.py`, `project/tests/test_numeric_normalizer.py`, `project/tests/test_exact_match.py`, `project/tests/test_score_gate_outputs.py`, `project/tests/test_validation_gate.py`, `project/tests/test_loop_executor.py`

**Interfaces:**
- Consumes: `project/scripts/check_docstrings_only.py` from Task 0.
- Produces: nothing importable. Last task of the tests phase.

- [ ] **Step 1: Read all eight files end to end**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for f in tests/test_async_judge.py tests/test_async_judge_live_smoke.py tests/test_metrics.py tests/test_numeric_normalizer.py tests/test_exact_match.py tests/test_score_gate_outputs.py tests/test_validation_gate.py tests/test_loop_executor.py; do echo "===== $f ====="; cat "$f"; done
```

- [ ] **Step 2: Rewrite the docstrings and comments**

Apply the Task 0 style contract and the phase-2 default. Three notes. `test_async_judge_live_smoke.py` is the second default-skipped test, so like its critic counterpart it keeps the line saying how to run it. `test_numeric_normalizer.py` and `test_exact_match.py` encode financial-figure comparison rules, and a comment naming why a particular pair of figures should or should not match is recording the rule, not the code. `test_loop_executor.py` covers row-level resumability, so a comment about the `UNIQUE` key that makes a skip correct survives as one line.

- [ ] **Step 3: Verify only docstrings moved**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" tests/test_async_judge.py tests/test_async_judge_live_smoke.py tests/test_metrics.py tests/test_numeric_normalizer.py tests/test_exact_match.py tests/test_score_gate_outputs.py tests/test_validation_gate.py tests/test_loop_executor.py
```

Expected: `all 8 file(s) docstring-only`, exit code 0.

- [ ] **Step 4: Run the tests**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/tests/test_async_judge.py project/tests/test_async_judge_live_smoke.py project/tests/test_metrics.py project/tests/test_numeric_normalizer.py project/tests/test_exact_match.py project/tests/test_score_gate_outputs.py project/tests/test_validation_gate.py project/tests/test_loop_executor.py
git commit -m "docs(tests): simplify docstrings and comments in judge and gate tests"
```

---

## Task 13: Whole-repo verification and the `dev` fast-forward

**Files:**
- Modify: none. This task verifies and moves one branch pointer.

**Interfaces:**
- Consumes: every commit from Tasks 1 to 12.
- Produces: `dev` pointing at `presentation`.

- [ ] **Step 1: Re-verify all 90 files against the original baseline**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python scripts/check_docstrings_only.py "$(cat /tmp/docstring-baseline-rev)" \
  $(find . -name '*.py' -not -path './.venv/*' -not -path '*__pycache__*' -not -path './scripts/*')
```

Expected: `all 90 file(s) docstring-only`, exit code 0. This is the check that matters. It proves the entire twelve-task sequence moved no executable line, in source or in tests.

- [ ] **Step 2: Confirm the prose targets were hit across both phases**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'EOF'
import re, pathlib, io, tokenize

def count_prose_dashes(path):
    """Counts ' -- ' in real docstrings and comments only.

    Uses ast.get_docstring rather than a token heuristic. A STRING token that
    merely begins a logical line is not a docstring: continuation strings inside
    a parenthesised expression look identical to the tokenizer, and this project
    has four of them (an LLM retry prompt, a logger format string, a LlamaParse
    prompt, a RuntimeError message) that must never be rewritten.

    A dash inside a normal string literal is data, not prose. parse_filing.py
    sends one to LlamaParse in system_prompt_append; rewriting it would change
    behaviour, and the AST checker would rightly fail the task for it.
    """
    n = 0
    with open(path, "rb") as fh:
        toks = list(tokenize.tokenize(fh.readline))
    for i, tok in enumerate(toks):
        is_comment = tok.type == tokenize.COMMENT
        is_docstring = (
            tok.type == tokenize.STRING
            and i > 0
            and toks[i - 1].type in (tokenize.INDENT, tokenize.NEWLINE, tokenize.NL, tokenize.ENCODING)
        )
        if is_comment or is_docstring:
            n += len(re.findall(r'\S\s--\s\S', tok.string))
    return n

def scan(paths):
    dash = specs = 0; lens = []
    for p in paths:
        t = p.read_text(encoding='utf-8')
        dash += count_prose_dashes(p)
        specs += sum(1 for L in t.splitlines()
                     if re.search(r'(Architecture|Guardrails|Budget|deviations)\.md|§\s?\d', L))
        m = re.match(r'\s*(?:r|u)?"""(.*?)"""', t, re.S)
        if m: lens.append(m.group(1).count('\n') + 1)
    return dash, specs, lens
allpy = [p for p in pathlib.Path('.').rglob('*.py')
         if '.venv' not in p.parts and '__pycache__' not in p.parts and 'scripts' not in p.parts]
src = [p for p in allpy if 'tests' not in p.parts]
tst = [p for p in allpy if 'tests' in p.parts]
for name, group, base_dash, base_spec, base_max in (
        ("source", src, 103, 102, 30), ("tests", tst, 53, 20, 22)):
    d, s, l = scan(group)
    print(f"{name:>7}: {len(group):>3} files | dashes {d:>3} (was {base_dash}) | "
          f"spec lines {s:>3} (was {base_spec}) | longest docstring {max(l) if l else 0} (was {base_max}) | "
          f"mean {sum(l)/len(l):.1f}" if l else "")
EOF
```

Expected: dashes at 0 in both groups, spec lines at one per file or fewer, longest module docstring 6 lines or fewer in source and 6 or fewer in tests apart from the two live-smoke files that keep their run instructions.

- [ ] **Step 3: Run the full suite one final time**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q 2>&1 | tail -3
```

Expected: `339 passed, 2 skipped`.

- [ ] **Step 4: Confirm the working tree is clean**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git status --short
git log --oneline "$(cat /tmp/docstring-baseline-rev)"..presentation
```

Expected: empty status, and thirteen commits listed.

- [ ] **Step 5: Fast-forward `dev` to `presentation`**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git merge-base --is-ancestor dev presentation && echo "fast-forward is safe"
git branch -f dev presentation
git rev-list --left-right --count dev...presentation
```

Expected: `fast-forward is safe`, then `0	0`. Use `git branch -f` rather than a checkout so the working tree stays on `presentation`.

- [ ] **Step 6: Report, and stop**

Print the Step 2 metrics and the Step 5 branch state. **Do not push.** Pushing is the user's call, and this repo's convention is that no commit or push happens without an explicit request in that turn.
