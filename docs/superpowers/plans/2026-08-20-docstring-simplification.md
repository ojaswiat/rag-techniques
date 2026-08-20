# Docstring and Comment Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite every docstring and comment in the 48 Python source files so they read like a senior engineer wrote them: short, factual, and about the code rather than about the specs.

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
- **Scope is source only.** The 42 files under `project/tests/` are out of scope for this plan and are a separate phase.
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
    specs += len(re.findall(r'(Architecture|Guardrails|Budget|deviations)\.md|§\s?\d', t))
print(f"remaining '--' dashes: {dash}")
print(f"remaining spec refs:   {specs}")
EOF
```

Expected: `--` dashes at 0, spec refs at 1 (the `config.py` routing-matrix comment kept in Step 2).

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

## Task 7: Whole-repo verification and the `dev` fast-forward

**Files:**
- Modify: none. This task only verifies and moves a branch pointer.

**Interfaces:**
- Consumes: every commit from Tasks 1 to 6.
- Produces: `dev` pointing at `presentation`.

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
    specs += len(re.findall(r'(Architecture|Guardrails|Budget|deviations)\.md|§\s?\d', t))
    m = re.match(r'\s*(?:r|u)?"""(.*?)"""', t, re.S)
    if m:
        lens.append(m.group(1).count('\n') + 1)
print(f"files:               {len(src)}   (baseline 48)")
print(f"'--' dashes:         {dash}   (baseline 103, target 0)")
print(f"spec refs:           {specs}   (baseline 102, target <= 48)")
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

- [ ] **Step 5: Fast-forward `dev` to `presentation`**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git merge-base --is-ancestor dev presentation && echo "fast-forward is safe"
git branch -f dev presentation
git rev-list --left-right --count dev...presentation
```

Expected: `fast-forward is safe`, then `0	0`. Use `git branch -f` rather than a checkout so the working tree stays on `presentation`.

- [ ] **Step 6: Report, and stop**

Print the before/after metrics from Step 2 and the branch state from Step 5. **Do not push.** Pushing is the user's call, and this repo's convention is that no commit or push happens without an explicit request in that turn.

---

## Self-review

**Spec coverage.** The style contract in Task 0 has seven rules: module docstring length, function docstring length, comments explain why, one spec reference per file, no `--`, no emphasis scaffolding, and do not invent. Tasks 1 to 6 each apply all seven across their package, and Task 7 Step 2 measures four of them numerically. The three that cannot be measured by regex, comments explaining why, one line per function, and do not invent, are covered by the per-task reviewer gate that subagent-driven-development provides.

**Placeholder scan.** No TBD, no "similar to Task N", no "handle edge cases". The checker script is given in full rather than described. Every verification step names the command and the expected output. The one deliberate repetition is the style contract, which lives in Task 0 and is referenced rather than restated, because a subagent reads Task 0 first by instruction in the task header.

**Type consistency.** The checker is `project/scripts/check_docstrings_only.py` in every task that invokes it, always with the same two-argument shape, `<git-rev> <files...>`. The baseline revision is written to `/tmp/docstring-baseline-rev` in Task 0 Step 5 and read back with `$(cat /tmp/docstring-baseline-rev)` in Tasks 1 to 7. Test counts are `339 passed, 2 skipped` throughout.

**One gap worth naming.** `/tmp/docstring-baseline-rev` does not survive a machine reboot between tasks. If it is missing, recover it with `git log --oneline --all | grep "add AST checker"` and use the commit immediately before that one.
