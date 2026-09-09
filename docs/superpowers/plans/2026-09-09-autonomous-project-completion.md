# Autonomous Project Completion (Phases 6b–8) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the COMP702 RAG benchmark end-to-end with no human input — calibrate the Judge, clear the validation gate, execute all 900 cells, score them, and produce the analysis artefacts the dissertation draws on.

**Architecture:** Three local retrievers (ChromaDB+fastembed, rank_bm25, LlamaIndex TreeIndex) already exist and make zero LLM calls. Only two stages spend money: the Answerer and the Judge. Both move from Groq's token-bound free tier to OpenRouter's paid tier so the run finishes in hours of wall clock instead of a ~2–3 week TPD-paced crawl that would need a human to nurse it. Every LLM-facing stage keeps `temperature=0`, and OpenRouter's multi-host routing is pinned to a single provider per model so the run stays reproducible.

**Tech Stack:** Python 3.12 + `uv` (`project/.venv`), `aiosqlite` (WAL), `llama-index` 0.14.x with `OpenAILike`, `openai` async SDK, `chromadb`, `fastembed`, `rank_bm25`, `pytest` + `pytest-asyncio` (asyncio_mode=auto), `matplotlib` (added in Task 10).

**Spec:**
- `resources/specs/Phase Plan.md` — Phases 6, 7, 8 (this plan implements the tail of 6, then 7 and 8 entire)
- `resources/specs/Guardrails.md` — §2 routing, §3 anti-leakage, §4 the gate, §5 concurrency, §7 throttle
- `resources/specs/Architecture.md` — §3.2 schema
- `resources/specs/Project Idea.md` — benchmark design, quadrants, tri-pillar framework

---

## Global Constraints

Every task's requirements implicitly include this section.

- **Working directory is `/Users/ojaswi/Projects/rag-techniques/project`.** Run everything through `.venv/bin/python`, never a bare `python`. Do not `pip install`; use `uv add`.
- **Branch is `automate`.** Commit after each task. **Never** merge into `main` or `dev`. **Never** push.
- **Commit messages must not contain "Claude", "Co-Authored-By", or any agent attribution.** (`CLAUDE.md`)
- **All LLM calls run at `temperature = 0`.** Each benchmark cell runs exactly once; no repeated sampling.
- **`LOCAL_TEST_THROTTLE` is defined once** in `project/llm_client/config.py` alongside `THROTTLE_LIMIT = 3`. Loop scripts apply it via `loop_template.apply_throttle()` and never declare their own cap. Every loop runs clean end-to-end at throttle before it is released to the full batch.
- **Anti-leakage (Guardrails §3):** `queries` (100 PQ) / `golden_queries` (20 GQ) / `judge_validation` (20 JEQ) stay disjoint. GQ feeds the Judge only. JEQ feeds no prompt. Pipelines receive only the query plus their own retrieved nodes.
- **Anti-self-grading (Guardrails §2):** Generator ≠ Critic family; Answerer ≠ Judge family. Llama answerer vs Qwen judge satisfies this and must stay satisfied after the provider move.
- **Resumability:** `results.UNIQUE(source_set, query_id, pipeline, k_value)` is the crash-resume key. Never delete `results` rows to "retry"; the resume path re-picks absent keys automatically.
- **`K_VALUES = (2, 3, 5)`** in `loop_executor.py`; the DB enforces `CHECK (k_value IN (2,3,5))`. The gate runs at a single `K=5`.
- **British English** in all prose. **No em dashes** — use commas or semicolons.
- **Do not modify `resources/` speculatively.** `CLAUDE.md` §2 forbids unrequested writes there, not the deliverables the Phase Plan requires. Exactly these paths are permitted, and only from the tasks named: `resources/specs/Guardrails.md` (Task 2), `resources/research/deviations.md` (Tasks 2, 3, 6, 12), `resources/research/build_progress.md` and `resources/research/token_usage.md` (Task 12), and `resources/artifacts/analysis/` (Tasks 11, 13, which is a Phase 8 deliverable folder). Any other path under `resources/` is out of bounds.
- **Baseline test suite is `339 passed, 2 skipped`.** Every task must leave it green; the count only grows.
- **Tick each checkbox to `- [x]` as its step completes**, and include this plan file in the task's commit. It is the only durable record of progress across a session halt.
- **Log every task through monitor** (`CLAUDE.md`): run `/monitor:log` after each task's commit, and `/monitor:report` as well for the tasks that changed code (1, 2, 3, 6, 7, 10, 11, 13). Doc-only tasks are logged, not reported. On a failure, log it with `status=failure` and the real error rather than skipping it.
- **Terminology, binding for this run:** the gate figure is **cross-model concordance**, never "human-judge Agreement Rate". The agent supplies both the Judge's calibration exemplars and the gate's reference scores, so the figure is internal consistency, not external validation. This wording is required in `deviations.md`, `build_progress.md`, analysis output and the results summary.

---

## Session Resume Protocol

This run is long and will be interrupted: context compaction, a session limit, a killed background job. **This plan file is the durable state.** Nothing else survives.

**Tick each checkbox to `- [x]` the moment its step completes, and include the plan file in that task's commit.** A step that ran but is still unticked will be run twice by the next session.

### A cold session's first five commands

Run these before touching anything. They reconstruct where the run stopped, from the repository rather than from memory:

```bash
cd /Users/ojaswi/Projects/rag-techniques
git log --oneline -15
grep -c "^- \[x\]" docs/superpowers/plans/2026-09-09-autonomous-project-completion.md
grep -n "LOCAL_TEST_THROTTLE" project/.env
cd project && sqlite3 -header benchmark.db "SELECT source_set, COUNT(*) AS rows, SUM(judge_score IS NULL) AS unscored, SUM(human_score IS NULL) AS unscored_ref FROM results GROUP BY source_set;"
sqlite3 benchmark.db "SELECT COUNT(*) FROM golden_queries WHERE human_reasoning = 'PENDING_HUMAN_LABEL';"
```

Read them together, in this order:

| Signal | Meaning |
|---|---|
| Last commit subject | The last task that finished cleanly. Resume at the next one. |
| Ticked-box count vs the task's steps | Which step inside that task was reached. |
| `LOCAL_TEST_THROTTLE` | **Check this before every run.** See the hazard below. |
| `golden_queries` placeholders = 0 | Task 3 is done. If it is 20, nothing may be judged yet. |
| `JEQ` rows = 60, `unscored` = 0 | Task 5 is done. |
| `JEQ` `unscored_ref` = 0 | Task 6 wrote the reference scores. |
| `PQ` rows = 900 | Task 8 is done. `unscored` = 0 means Task 9 is too. |

### Throttle-state hazard

Tasks 5, 8 and 9 set `LOCAL_TEST_THROTTLE=false` and restore it to `true` at the end. **A session that dies mid-task leaves it `false`.** A later task that expects a throttled rehearsal would then fire the full batch unthrottled.

So: never assume the flag's value, always `grep` it, and set it explicitly to what the current step needs before running anything that spends.

### Interrupted runs are safe to re-run

Every expensive loop is idempotent by design and **must be resumed by re-running the same command, never by clearing state**:

- `loop_executor.main()` reads `get_completed_keys()` and skips committed cells. The `UNIQUE(source_set, query_id, pipeline, k_value)` constraint is the resume key.
- `judge_rows()` filters `judge_score IS NULL` (added in Task 7), so it re-scores nothing.
- `write_gq_labels.py` rewrites the same values.
- `gate_reference_scores.apply_scores()` overwrites by `result_id`.

A partially finished run therefore costs nothing to resume. **Deleting rows to "start clean" throws away paid work and is forbidden.**

### Long steps

Tasks 5, 8 and 9 each run for 10 to 50 minutes. Launch them with `run_in_background: true` and never wrap them with a shell `&`; the visible shell tile is how a resumed session sees whether the job is still alive.

---

## Autonomous Failure Policy

Steps will fail. Diagnose and fix them without stopping, under these rules.

### Fix it yourself

When a step fails, do all of this before retrying:

1. **Read the actual error.** Not the summary line, the traceback and the response body.
2. **Form one hypothesis and test it** with the cheapest possible check, at throttle, on one row.
3. **Fix the cause, not the symptom.** A test that fails because the code is wrong gets a code fix, never a weakened assertion.
4. **Re-run the step's verification** and confirm the expected output, then continue.
5. **Log it.** A fix that changed a spec-level behaviour goes in `resources/research/deviations.md`. A fix that changed only code goes in the monitor log (see Global Constraints). An ordinary bug fix does not belong in `deviations.md`.

Retry an unchanged command **only** for a transient: a 429, a 5xx, a timeout, a dropped connection. Anything else, change something first. Three failed attempts with three different hypotheses means stop and report rather than continuing to guess.

### Never do these, under any pressure

These would each produce a project that looks finished and is not. They are not judgement calls.

- **Never lower `GATE_THRESHOLD`, widen `AGREEMENT_TOLERANCE`, or change `rows_agree()`.** The gate is `> 80%` on a plus-or-minus-10-point band. If the gate fails, Guardrails §4b permits exactly two remedies: revise the Judge's rubric, or swap the Judge model to one outside the Llama family. Nothing else.
- **Never drop, skip or exclude rows to make a metric pass.** `compute_agreement_rate()` raises on a missing score precisely so the denominator cannot shrink; do not catch that exception to work around it.
- **Never read `results.judge_score` before writing a reference score** in Task 6. Independence is the only property that figure retains.
- **Never delete `results` rows.** Re-run the loop instead.
- **Never delete, skip, `xfail` or weaken a test** to get a green suite. If a test is genuinely wrong, fix the test and say so in the commit message.
- **Never coerce a NULL metric to zero.** `exact_match` is NULL by design for Q2 and Q4.
- **Never change a model, provider or temperature** outside Task 2 and the gate-failure remedy above, and never so that Answerer and Judge share a family.
- **Never `git push`, and never merge into `main` or `dev`.**

### Failures that are hard stops

Stop, leave the tree clean, and report. Do not work around these:

- The gate fails after both permitted remedies have been tried.
- Projected spend exceeds $4 (Task 4 Step 4).
- `judge_score` comes back constant across all rows: the Judge has collapsed and every downstream number is meaningless.
- An API key is rejected, or a model is withdrawn mid-run.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `project/llm_client/config.py` | Modify | Add per-stage `extra_body`; repoint answerer + judge to OpenRouter |
| `project/llm_client/llm_factory.py` | Modify | Thread `extra_body` from routing entry into `OpenAILike` |
| `project/tests/test_llm_factory.py` | Modify | Cover per-stage `extra_body` threading |
| `project/dataset_generation/write_gq_labels.py` | Create | Apply the 20 calibration labels to `golden_queries` |
| `project/database_manager.py` | Modify | `update_golden_query_example_output()`, `get_pq_judging_rows()` |
| `project/tests/test_gq_calibration.py` | Create | Guard the calibration set's shape (spread, good/bad split) |
| `project/judge/async_judge.py` | Modify | Generalise `judge_jeq_rows` → `judge_rows(source_set=...)` |
| `project/score_gate_outputs.py` | Modify | Non-interactive agent scoring path; concordance wording |
| `project/gate_reference_scores.py` | Create | Agent-written reference scores, judge-blind by construction |
| `project/analysis/__init__.py` | Create | Package marker |
| `project/analysis/aggregate.py` | Create | Tri-pillar + per-quadrant aggregation from `results` alone |
| `project/analysis/figures.py` | Create | matplotlib figures for the write-up |
| `project/analysis/run_analysis.py` | Create | CLI entry: aggregate → tables → figures → summary |
| `project/tests/test_aggregate.py` | Create | Aggregation maths on synthetic rows |
| `project/groq_limits.md` | Modify | Remove stale routing (Task 12) |
| `resources/specs/Guardrails.md` | Modify | §2 routing matrix (Task 2 only) |
| `resources/research/deviations.md` | Modify | Entries 29–32 |
| `project/analysis/build_report.py` | Create | Assemble the self-contained HTML results report |
| `project/tests/test_build_report.py` | Create | Report assembly: embedding, caveats, no external refs |
| `resources/artifacts/analysis/benchmark_report.html` | Create | The final deliverable, published as an Artifact |

---

## Known Hazards (read before starting)

1. **`openai/gpt-oss-20b:free` has been withdrawn from OpenRouter.** Only the paid `openai/gpt-oss-20b` remains. This is the Critic's model. Dataset generation is **complete**, so nothing in this plan calls the Critic and nothing here is blocked. Do **not** "fix" it. It is recorded in Task 12 as a latent issue for any future regeneration.
2. **`meta-llama/llama-3.3-70b-instruct` does not support the `reasoning` parameter** (verified against `/api/v1/models/.../endpoints`). The current OpenRouter branch hardcodes `extra_body={"reasoning": {"effort": "low"}}` for *every* OpenRouter model. Task 1 exists precisely to make that per-stage before Task 2 repoints the answerer.
3. **`golden_queries` currently holds 20 placeholder labels** — `human_reasoning = 'PENDING_HUMAN_LABEL'`, `human_score = 1`, and `example_output` identical to `ground_truth_answer` for all 20. Because `_rescale_to_1_10(1)` returns `1`, the Judge is currently being taught that a perfect answer scores 1/10. Task 3 fixes this and **must** run before any judging.
4. **`judge_jeq_rows()` is JEQ-hardcoded** (`WHERE r.source_set = 'JEQ'`, joined to `judge_validation`). There is no PQ judging path. Task 7 builds it.
5. **`.env` currently has `LOCAL_TEST_THROTTLE=true`.** Tasks 5, 8 and 9 flip it to `false` for the real runs and the plan flips it back afterwards. Never leave it `false` at the end of a task.

---

## Task 1: Per-stage `extra_body` in the model routing

The OpenRouter branch of `LLMFactory` applies one hardcoded `extra_body` to every OpenRouter model. Task 2 needs to send `provider` pinning to the answerer and judge, and must not send `reasoning` to a model that rejects it. Make the payload a property of the routing entry.

**Files:**
- Modify: `project/llm_client/config.py:23-30`
- Modify: `project/llm_client/llm_factory.py:17-100`
- Test: `project/tests/test_llm_factory.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `config.MODEL_ROUTING[stage]` entries may now carry an optional `"extra_body": dict` key.
  - `LLMFactory.get_client(provider: str, model: str, callback_manager: CallbackManager | None = None, extra_body: dict | None = None) -> Any`
  - `LLMFactory.get_client_for_stage(stage: str, callback_manager: CallbackManager | None = None) -> Any` — unchanged signature; now reads `extra_body` off the routing entry.

- [ ] **Step 1: Write the failing test**

Append to `project/tests/test_llm_factory.py`:

```python
def test_get_client_for_stage_forwards_routing_extra_body(monkeypatch):
    """A stage's extra_body reaches OpenAILike.additional_kwargs verbatim."""
    monkeypatch.setitem(
        config.MODEL_ROUTING,
        "judge",
        {
            "model": "qwen/qwen3.6-27b",
            "provider": "openrouter",
            "extra_body": {"provider": {"order": ["Chutes"], "allow_fallbacks": False}},
        },
    )
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "test-key")
    llm = LLMFactory.get_client_for_stage("judge")
    assert llm.additional_kwargs["extra_body"] == {
        "provider": {"order": ["Chutes"], "allow_fallbacks": False}
    }


def test_openrouter_stage_without_extra_body_sends_none(monkeypatch):
    """No extra_body in the routing entry means none is sent.

    Llama 3.3 70B rejects `reasoning`; a hardcoded default would reach it.
    """
    monkeypatch.setitem(
        config.MODEL_ROUTING,
        "answerer",
        {"model": "meta-llama/llama-3.3-70b-instruct", "provider": "openrouter"},
    )
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "test-key")
    llm = LLMFactory.get_client_for_stage("answerer")
    assert "extra_body" not in llm.additional_kwargs
```

Check the file's existing imports; add `import llm_client.config as config` and `from llm_client.llm_factory import LLMFactory` only if they are not already there.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_llm_factory.py -q
```

Expected: both new tests FAIL. The first with a `KeyError`/assertion on `additional_kwargs`, the second because the hardcoded `reasoning` block is present.

- [ ] **Step 3: Thread `extra_body` through the factory**

In `project/llm_client/llm_factory.py`, change the `get_client` signature:

```python
    @staticmethod
    def get_client(
        provider: str,
        model: str,
        callback_manager: Optional[CallbackManager] = None,
        extra_body: Optional[dict] = None,
    ) -> Any:
```

Replace the hardcoded `additional_kwargs` in the `openrouter` branch. The old comment explaining the `reasoning` cap moves to `config.py` beside the entries that now carry it:

```python
            case "openrouter":
                openrouter_mod = importlib.import_module(".openrouter_client", package=__package__)
                raw_client = openrouter_mod.get_openrouter_client(model)

                api_base = getattr(config, "OPENROUTER_API_ENDPOINT", "https://openrouter.ai/api/v1")
                # extra_body is per-stage (config.MODEL_ROUTING) rather than
                # fixed here: reasoning-tuned models need a reasoning cap,
                # non-reasoning ones reject the parameter, and only the
                # benchmark stages need single-provider pinning.
                llm = OpenAILike(
                    model=model,
                    api_base=api_base,
                    api_key=config.OPENROUTER_API_KEY,
                    is_chat_model=True,
                    callback_manager=callback_manager,
                    temperature=0,
                    additional_kwargs=({"extra_body": extra_body} if extra_body else {}),
                )
                llm._aclient = raw_client
                return llm
```

Then have `get_client_for_stage` read it:

```python
        model = entry["model"]
        provider = entry["provider"]
        return LLMFactory.get_client(
            provider,
            model,
            callback_manager=callback_manager,
            extra_body=entry.get("extra_body"),
        )
```

- [ ] **Step 4: Give the existing OpenRouter stages their `extra_body` explicitly**

In `project/llm_client/config.py`, the generator and critic must keep the reasoning cap they relied on. Replace the two entries:

```python
# Reasoning-tuned models: without a cap, reasoning tokens exhaust the
# completion budget and leave message.content=None, crashing json.loads()
# in the caller. effort="none" is rejected by some endpoints; "low" is
# accepted everywhere tested and still bounds the spend.
_REASONING_LOW = {"reasoning": {"effort": "low"}}

MODEL_ROUTING: dict[str, dict] = {
    "generator":     {"model": "nvidia/nemotron-3-super-120b-a12b:free", "provider": "openrouter", "extra_body": _REASONING_LOW},
    "critic":        {"model": "openai/gpt-oss-20b:free", "provider": "openrouter", "extra_body": _REASONING_LOW},
    "p3_index_build":{"model": "nvidia/nemotron-3-super-120b-a12b", "provider": "nvidia"},
    "answerer":      {"model": "llama-3.3-70b-versatile","provider": "groq"},
    "judge":         {"model": "qwen/qwen3.6-27b",        "provider": "groq"},
    "debug":         {"model": "llama-3.1-8b-instant",   "provider": "groq"},
}
```

Note the answerer/judge rows are **unchanged in this task** — Task 2 moves them. This task is a pure refactor with identical runtime behaviour.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_llm_factory.py -q && .venv/bin/python -m pytest -q
```

Expected: `tests/test_llm_factory.py` all pass; full suite `341 passed, 2 skipped`.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/llm_client/config.py project/llm_client/llm_factory.py project/tests/test_llm_factory.py
git commit -m "refactor(llm_client): make OpenRouter extra_body a per-stage routing property"
```

---

## Task 2: Move Answerer and Judge to OpenRouter with pinned providers

Groq's free tier is token-bound (TPM/TPD), which forces the 900-run matrix into a multi-week paced crawl needing human intervention on quota exhaustion. OpenRouter is request-bound (20 RPM in `openrouter_client.py`), so 1,800 calls finish in roughly 95 minutes of wall clock for around $0.90–$1.55. The models stay the same family pair, preserving the Answerer ≠ Judge invariant.

**Files:**
- Modify: `project/llm_client/config.py`
- Modify: `resources/specs/Guardrails.md:20-42`
- Modify: `resources/research/deviations.md`
- Test: `project/tests/test_config.py`

**Interfaces:**
- Consumes: Task 1's `extra_body` routing key.
- Produces: `config.MODEL_ROUTING["answerer"]` and `["judge"]` both route to `provider="openrouter"` with a pinned single upstream. No function signature changes; every later task calls `LLMFactory.get_client_for_stage("answerer"|"judge")` exactly as before.

- [ ] **Step 1: Confirm both models and their endpoints are live**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
for m in "meta-llama/llama-3.3-70b-instruct" "qwen/qwen3.6-27b"; do
  echo "=== $m ==="
  curl -s "https://openrouter.ai/api/v1/models/$m/endpoints" | .venv/bin/python -c "
import json,sys
for e in json.load(sys.stdin)['data']['endpoints'][:3]:
    print(' ', e['provider_name'], '| in', e['pricing']['prompt'], '| out', e['pricing']['completion'], '| ctx', e['context_length'])
"
done
```

Expected (as verified 2026-09-09): Llama's cheapest endpoint is **DeepInfra** at `$0.10/M` in, `$0.32/M` out, 131k context. Qwen's cheapest is **Chutes** at `$0.30/M` in, `$2.00/M` out, 262k context. If either name has changed, use the cheapest listed endpoint that offers at least 128k context and record the substitution in the Step 6 deviation.

- [ ] **Step 2: Write the failing test**

Append to `project/tests/test_config.py`:

```python
def test_answerer_and_judge_route_to_openrouter_with_pinned_provider():
    """Both benchmark stages run on OpenRouter, pinned to one upstream host.

    OpenRouter load-balances across hosts that differ in quantisation, so an
    unpinned run would mix fp8 and bf16 outputs across the 900 cells and
    break the single-temp-0-run-per-cell reproducibility claim.
    """
    for stage in ("answerer", "judge"):
        entry = config.MODEL_ROUTING[stage]
        assert entry["provider"] == "openrouter", stage
        pin = entry["extra_body"]["provider"]
        assert pin["allow_fallbacks"] is False, stage
        assert len(pin["order"]) == 1, stage


def test_answerer_and_judge_remain_different_families():
    """Guardrails §2: no model may grade its own output."""
    answerer = config.MODEL_ROUTING["answerer"]["model"]
    judge = config.MODEL_ROUTING["judge"]["model"]
    assert "llama" in answerer.lower()
    assert "qwen" in judge.lower()
```

- [ ] **Step 3: Run the test to verify it fails**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_config.py -q
```

Expected: `test_answerer_and_judge_route_to_openrouter_with_pinned_provider` FAILS with `AssertionError: answerer` (still `"groq"`). The families test passes already.

- [ ] **Step 4: Repoint the two stages**

In `project/llm_client/config.py`, replace the `answerer` and `judge` entries:

```python
# Single-upstream pinning. OpenRouter load-balances across hosts whose
# quantisation differs (fp8 vs bf16), so an unpinned run would mix
# numerically different backends across the 900 cells. allow_fallbacks=False
# makes a host outage fail loudly and resume later rather than silently
# switching backend mid-run.
_PIN_DEEPINFRA = {"provider": {"order": ["DeepInfra"], "allow_fallbacks": False}}
_PIN_CHUTES = {"provider": {"order": ["Chutes"], "allow_fallbacks": False}}
```

and inside `MODEL_ROUTING`:

```python
    "answerer":      {"model": "meta-llama/llama-3.3-70b-instruct", "provider": "openrouter", "extra_body": _PIN_DEEPINFRA},
    "judge":         {"model": "qwen/qwen3.6-27b", "provider": "openrouter", "extra_body": _PIN_CHUTES},
```

Leave `debug` on Groq — it is throwaway and costs nothing.

- [ ] **Step 5: Run the tests to verify they pass, then smoke one live call per stage**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_config.py -q
```

Expected: PASS.

Then confirm the pin is actually honoured end-to-end (this spends well under a cent):

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'PY'
import asyncio
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llm_client.llm_factory import LLMFactory

async def smoke(stage):
    llm = LLMFactory.get_client_for_stage(stage)
    r = await llm.achat([ChatMessage(role=MessageRole.USER, content="Reply with the single word: ok")])
    print(stage, "->", repr((r.message.content or "")[:60]))

asyncio.run(smoke("answerer"))
asyncio.run(smoke("judge"))
PY
```

Expected: both print a non-empty reply.

**If it fails, fix it and re-run this step:**

| Symptom | Cause | Fix |
|---|---|---|
| `404` or `No allowed providers are available` | The pinned name does not match OpenRouter's slug | Use the exact `provider_name` string from Step 1's output, capitalisation included |
| `401` / `User not found` | `OPENROUTER_API_KEY` missing or stale | Read `project/.env`; if the key is absent this is a hard stop, report it |
| Reply is `None` or empty | Reasoning tokens ate the completion budget | Only affects reasoning models; confirm the answerer entry has no `reasoning` in its `extra_body` |
| `400` naming an unsupported parameter | The model rejects something in `extra_body` | Re-check the endpoint's `supported_parameters` from Step 1 and drop the offending key |
| `402` / insufficient credit | Balance exhausted | Hard stop, report it |

- [ ] **Step 6: Sync the spec and log the deviation**

In `resources/specs/Guardrails.md`, edit the two rows of the §2 ASCII matrix. **Preserve the box alignment** — every line must stay the same width, so pad with spaces to match:

```text
|  Pipeline answers (P1/P2/P3)  meta-llama/llama-3.3-70b-instruct       OpenRouter     |
|  Judge / scoring (no search)  qwen/qwen3.6-27b                        OpenRouter     |
```

Verify no line changed length:

```bash
cd /Users/ojaswi/Projects/rag-techniques
sed -n '25,42p' resources/specs/Guardrails.md | awk '{print length($0)}' | sort -u
```

Expected: a single number printed (all box lines equal width).

Then append to `resources/research/deviations.md`, matching the file's existing 5-point format:

```markdown
### 29. Answerer and Judge moved from Groq's free tier to OpenRouter's paid tier (2026-09-09)

1. **Originally proposed:** Guardrails §2 routed both the pipeline Answerer (`llama-3.3-70b-versatile`) and the Judge (`qwen/qwen3.6-27b`) to Groq's free tier, and Phase 7 budgeted a background run of roughly 2 to 3 weeks paced against Groq's tokens-per-day ceiling.
2. **Deviation:** Groq's free tier is token-bound, so the 900-cell matrix could only be run in daily slices. That schedule cannot complete without a person present to handle exhausted quota, expired keys and restarts, which conflicts with finishing the project unattended.
3. **What we did:** Moved both stages to OpenRouter's paid tier on the same two model families, pinned each to a single upstream host, and ran the whole matrix in one pass.
4. **How we did it:** `MODEL_ROUTING["answerer"]` became `meta-llama/llama-3.3-70b-instruct` and `["judge"]` became `qwen/qwen3.6-27b`, both with `provider = "openrouter"`. Each entry carries an `extra_body` of `{"provider": {"order": [<one host>], "allow_fallbacks": false}}`, threaded into `OpenAILike` by `LLMFactory.get_client()`. Guardrails §2's routing matrix was updated to match.
5. **Why we did it:** OpenRouter is request-bound rather than token-bound, so 1,800 calls complete in roughly 95 minutes at the client's 20 RPM ceiling for around $1 to $1.55 in total. The model families are unchanged, so the Answerer is not equal to Judge anti-self-grading invariant still holds. Pinning to a single host matters because OpenRouter otherwise load-balances across backends of differing quantisation, which would mix numerically different models across the 900 cells and undermine the single run per cell at temperature 0 reproducibility claim.
```

- [ ] **Step 7: Full suite, then commit**

```bash
.venv/bin/python -m pytest -q
cd /Users/ojaswi/Projects/rag-techniques
git add project/llm_client/config.py project/tests/test_config.py resources/specs/Guardrails.md resources/research/deviations.md
git commit -m "feat(llm_client): route answerer and judge to OpenRouter with pinned upstreams"
```

Expected: `343 passed, 2 skipped`.

---

## Task 3: Write the 20 golden-query calibration labels

`golden_queries` holds 20 placeholders: `human_reasoning = 'PENDING_HUMAN_LABEL'`, `human_score = 1`, and `example_output` identical to `ground_truth_answer`. `_rescale_to_1_10(1)` returns `1`, so every exemplar currently teaches the Judge that a perfect answer scores **1 out of 10**. Judging anything before this is fixed produces meaningless scores.

Two problems, one fix. First the scores are wrong. Second, even corrected, 20 exemplars that are all perfect answers give the Judge no anchor for the low end of the scale — it would learn only what a 10 looks like. Guardrails §4 already anticipates a **10-good / 10-bad split** via the `is_good` column. This task builds that split.

**This is a Path A step:** the agent writes these labels in place of the researcher. That is a deliberate, accepted trade recorded in Step 6's deviation.

**Files:**
- Create: `project/dataset_generation/write_gq_labels.py`
- Modify: `project/database_manager.py`
- Create: `project/tests/test_gq_calibration.py`
- Modify: `resources/research/deviations.md`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `database_manager.update_golden_query_example_output(db_path: str, query_id: str, example_output: str) -> None`
  - After this task, all 20 `golden_queries` rows have `human_reasoning != 'PENDING_HUMAN_LABEL'`, `human_score` spanning 0–100, and `is_good` set to exactly 10 `True` and 10 `False`. Task 5's `build_prefix()` consumes these unchanged.

- [ ] **Step 1: Write the failing test**

Create `project/tests/test_gq_calibration.py`:

```python
"""Shape guards on the Judge's calibration set.

These assert properties of the live golden_queries table rather than of a
function: a mis-calibrated exemplar set silently corrupts every judge_score
in the benchmark, and nothing else in the suite would catch it.
"""
import pytest

import database_manager as dbm

DB_PATH = "benchmark.db"


@pytest.fixture
async def golden_queries():
    return await dbm.get_golden_queries(DB_PATH)


async def test_no_placeholder_labels_remain(golden_queries):
    unlabelled = [g["query_id"] for g in golden_queries if g["human_reasoning"] == "PENDING_HUMAN_LABEL"]
    assert unlabelled == []


async def test_scores_span_the_range(golden_queries):
    """A set clustered at one end teaches the Judge only that end."""
    scores = [g["human_score"] for g in golden_queries]
    assert min(scores) <= 30
    assert max(scores) >= 90


async def test_ten_good_ten_bad(golden_queries):
    flags = [g["is_good"] for g in golden_queries]
    assert flags.count(1) == 10
    assert flags.count(0) == 10


async def test_every_quadrant_has_both_polarities(golden_queries):
    """build_prefix() shows only one quadrant's 5 exemplars, so each
    quadrant must carry a low anchor of its own."""
    by_quadrant: dict[str, list[int]] = {}
    for g in golden_queries:
        by_quadrant.setdefault(g["quadrant"], []).append(g["is_good"])
    assert len(by_quadrant) == 4
    for quadrant, flags in by_quadrant.items():
        assert 1 in flags, quadrant
        assert 0 in flags, quadrant


async def test_bad_exemplars_differ_from_ground_truth(golden_queries):
    """A 'bad' exemplar whose output equals the ground truth is incoherent."""
    for g in golden_queries:
        if g["is_good"] == 0:
            assert g["example_output"] != g["ground_truth_answer"], g["query_id"]


async def test_reasoning_is_substantive(golden_queries):
    for g in golden_queries:
        assert len(g["human_reasoning"].split()) >= 6, g["query_id"]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_gq_calibration.py -q
```

Expected: 6 FAILURES, starting with `test_no_placeholder_labels_remain` listing all 20 query ids.

- [ ] **Step 3: Add the `example_output` writer**

`update_golden_query_labels()` cannot touch `example_output`. Add this to `project/database_manager.py`, directly after `update_golden_query_labels`:

```python
async def update_golden_query_example_output(db_path: str, query_id: str, example_output: str) -> None:
    """Replace one exemplar's candidate answer.

    Separate from update_golden_query_labels because the two are written at
    different times and for different reasons: the labels are a judgement
    about a candidate, while this rewrites the candidate itself when the
    calibration set needs a deliberately imperfect example.
    """
    if not example_output or not example_output.strip():
        raise ValueError(f"{query_id}: example_output must be a non-empty string")

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            "UPDATE golden_queries SET example_output = ? WHERE query_id = ?",
            (example_output, query_id),
        )
        await conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"No golden_query found with query_id={query_id!r} -- check for a typo")
```

Add it to the module's `__all__` if one exists.

- [ ] **Step 4: Read the 20 golden queries and compose the labels**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -json benchmark.db "SELECT query_id, quadrant, query_text, ground_truth_answer, gt_citations FROM golden_queries ORDER BY quadrant, query_id;" | .venv/bin/python -m json.tool
```

For each quadrant (5 exemplars each) assign polarity so every quadrant carries both, matching the `test_every_quadrant_has_both_polarities` guard. Use this fixed allocation:

| Position in quadrant (by `query_id` order) | `is_good` | `human_score` band |
|---|---|---|
| 1st | True | 95–100 |
| 2nd | True | 85–94 |
| 3rd | False | 40–55 |
| 4th | False | 10–25 |
| 5th | True (Q1, Q3) / False (Q2, Q4) | 88–96 / 15–30 |

That yields 10 good and 10 bad overall (Q1: 3 good, Q3: 3 good, Q2: 2 good, Q4: 2 good).

**For a `True` exemplar:** leave `example_output` as it is (it already equals the ground truth), and write reasoning that names *why* it earns the score.

**For a `False` exemplar:** rewrite `example_output` into a realistic pipeline failure, then score and justify it. Use the failure mode that matches the quadrant, because these are the failures the benchmark exists to measure:

| Quadrant | Failure mode to inject |
|---|---|
| Q1_Direct_Text | Right topic, wrong specific value lifted from a neighbouring sentence |
| Q2_Implicit_Text | Only one of the two facts the question needs joining, stated confidently |
| Q3_Direct_Table | Correct row, adjacent column's figure (a classic table-alignment failure) |
| Q4_Implicit_Table | Arithmetic performed on the right rows but the sign or scale is wrong |

Two worked examples, using real rows from this database:

```python
# Q1_Direct_Text, 1st position -> good, unchanged output
{
    "query_id": "QT1_GQ_001",
    # query: "What is the date of the Annual Meeting of Shareholders
    #         referenced in the Proxy Statement?"
    # ground truth: "December 7, 2023"
    "example_output": None,  # unchanged; already equals the ground truth
    "is_good": True,
    "human_score": 100,
    "human_reasoning": (
        "States the exact date the filing gives, with no hedging and no added "
        "detail that the source does not support. For a direct-text lookup "
        "this is the whole task, so it earns full marks."
    ),
},

# Q4_Implicit_Table, 4th position -> bad, output rewritten
{
    "query_id": "QT4_GQ_001",
    # query: "...total potential loss in fair value resulting from a 100 basis
    #         point increase in U.S. treasury interest rates, a 100 basis point
    #         increase in credit spreads, and a 10% decrease in foreign
    #         exchange rates affecting investments?"
    # ground truth: "$(1,868)"
    "example_output": "$1,868 million",
    "is_good": False,
    "human_score": 20,
    "human_reasoning": (
        "Finds the right rows and adds them correctly, but drops the "
        "parentheses that mark the figure as a loss and invents a scale the "
        "table does not state. The sign is the point of the question, so a "
        "reader acting on this would take a loss for a gain."
    ),
},
```

Write all 20 entries in the same shape. `example_output = None` means "leave the existing value alone".

- [ ] **Step 5: Write the label-application script**

Create `project/dataset_generation/write_gq_labels.py`:

```python
"""Applies the Judge's calibration labels to golden_queries.

The 20 exemplars are the only thing that teaches the Judge what each score
on the 0-100 scale means, so the set deliberately spans the range and
carries a deliberately imperfect answer for every quadrant. Guardrails 4a
shows the Judge only the 5 exemplars matching the target row's quadrant,
which is why each quadrant needs its own low anchor rather than the set
merely balancing overall.

Idempotent: re-running it rewrites the same values.
"""
import asyncio

import database_manager as dbm

# example_output=None leaves the stored candidate answer untouched; a string
# replaces it with a deliberately imperfect one.
LABELS: list[dict] = [
    # ... the 20 entries composed in Step 4 ...
]


async def main(db_path: str = "benchmark.db") -> int:
    for label in LABELS:
        if label["example_output"] is not None:
            await dbm.update_golden_query_example_output(
                db_path, label["query_id"], label["example_output"]
            )
        await dbm.update_golden_query_labels(
            db_path,
            label["query_id"],
            label["human_score"],
            label["human_reasoning"],
            label["is_good"],
        )
    print(f"Applied {len(LABELS)} calibration labels")
    return len(LABELS)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 6: Back up the database, apply the labels, verify**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
cp benchmark.db "/private/tmp/claude-501/-Users-ojaswi-Projects-rag-techniques/3871fba8-cfc3-4df2-92a5-cbfc30350bb6/scratchpad/benchmark.db.pre-gq-labels.bak"
.venv/bin/python -m dataset_generation.write_gq_labels
sqlite3 -header benchmark.db "SELECT quadrant, is_good, COUNT(*), MIN(human_score), MAX(human_score) FROM golden_queries GROUP BY quadrant, is_good;"
```

Expected: `Applied 20 calibration labels`, then 8 rows (4 quadrants x 2 polarities), with the good rows in the high bands and the bad rows in the low bands.

- [ ] **Step 7: Run the tests to verify they pass**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_gq_calibration.py -q && .venv/bin/python -m pytest -q
```

Expected: `tests/test_gq_calibration.py` 6 passed; full suite `349 passed, 2 skipped`.

- [ ] **Step 8: Inspect one rendered prompt prefix by eye**

The exemplars only matter through `build_prefix()`. Read one before trusting it:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'PY'
import asyncio
import database_manager as dbm
from judge.async_judge import build_prefix

async def main():
    ex = await dbm.get_golden_queries_by_quadrant("benchmark.db", "Q4_Implicit_Table")
    print(build_prefix("Q4_Implicit_Table", ex))

asyncio.run(main())
PY
```

Expected: the rubric, then 5 blocks. Confirm the "Correct score (1-10)" lines are **not** all the same number and that the low-scoring blocks show a candidate answer that visibly differs from the ground truth.

- [ ] **Step 9: Log the deviation and commit**

Append to `resources/research/deviations.md`:

```markdown
### 30. Judge calibration exemplars written by the agent, and split 10 good / 10 bad (2026-09-09)

1. **Originally proposed:** The researcher hand-labels the 20 golden queries with a 0-100 score and a written justification, and Guardrails 4a notes `is_good` as a future 10-good/10-bad dimension that was not yet designed.
2. **Deviation:** Two gaps. The 20 rows still held placeholder labels, `human_reasoning = 'PENDING_HUMAN_LABEL'` and `human_score = 1`, which rescales to 1 out of 10 and would have taught the Judge that a perfect answer is worth the lowest score. Separately, every `example_output` was identical to its `ground_truth_answer`, so even corrected the set would show the Judge nothing but perfect answers and give it no anchor for the low end of the scale.
3. **What we did:** The agent wrote all 20 labels, and rewrote 10 of the candidate answers into realistic pipeline failures, so each quadrant carries both a high and a low anchor.
4. **How we did it:** Added `database_manager.update_golden_query_example_output()` and `dataset_generation/write_gq_labels.py`, which applies the set idempotently. `tests/test_gq_calibration.py` guards the shape: no placeholders, scores spanning the range, exactly 10 good and 10 bad, both polarities present in every quadrant, and no "bad" exemplar whose output still equals the ground truth. The injected failure matches each quadrant's characteristic weakness, a neighbouring value for direct text, a half-answer for implicit text, an adjacent column for direct table, and a sign or scale error for implicit table.
5. **Why we did it:** The project is being completed without human input, so the agent stands in for the researcher at this step. The cost is stated plainly: the exemplars are no longer an external human standard. Per-quadrant balance is required rather than merely overall balance because `build_prefix()` shows the Judge only the 5 exemplars sharing the target row's quadrant, so a quadrant with no low anchor would be judged against a ceiling-only scale.
```

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/database_manager.py project/dataset_generation/write_gq_labels.py project/tests/test_gq_calibration.py resources/research/deviations.md project/benchmark.db
git commit -m "feat(judge): write the 20 calibration exemplars with a per-quadrant good/bad split"
```

---

## Task 4: Throttled end-to-end rehearsal of the validation gate

Guardrails §7 requires every loop to run clean at throttle before the full batch. This is the first run that spends OpenRouter credit through the real pipelines, so rehearse it at `THROTTLE_LIMIT = 3` before committing to 60 rows.

**Files:**
- Modify: `project/.env` (temporary, reverted within the task)
- No source changes expected.

**Interfaces:**
- Consumes: Task 2's routing, Task 3's exemplars.
- Produces: 3 `results` rows tagged `source_set='JEQ'` carrying `pipeline_output`, `judge_score` and the deterministic metrics. These stay in the database and are picked up as already-complete by Task 5's resume path.

- [ ] **Step 1: Confirm the throttle is on**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
grep -n "LOCAL_TEST_THROTTLE" .env
```

Expected: `LOCAL_TEST_THROTTLE=true`. If it reads `false`, set it to `true` before continuing.

- [ ] **Step 2: Run the gate at throttle**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python validation_gate.py --db-path benchmark.db 2>&1 | tail -30
```

Expected: a summary dict with `generation.completed == 3`, `generation.failures == []`, and `judging.judged == 3`. Loading three retrievers takes a couple of minutes on first call because fastembed downloads and warms the embedding and rerank models.

- [ ] **Step 3: Inspect the three rows**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -header -column benchmark.db "SELECT result_id, pipeline, k_value, judge_score, recall_at_k, citation_match, ROUND(latency_sec,1) AS secs, input_tokens, output_tokens FROM results WHERE source_set='JEQ';"
sqlite3 benchmark.db "SELECT substr(pipeline_output,1,300) FROM results WHERE source_set='JEQ' LIMIT 1;"
```

Expected: 3 rows, `k_value = 5` on all of them, `judge_score` between 1 and 10 and **not** all identical to 1, non-null `input_tokens`/`output_tokens`, and a `pipeline_output` that reads as a real answer with citations rather than an error string or `None`.

**If it fails, fix it and re-run Step 2:**

| Symptom | Cause | Fix |
|---|---|---|
| `judge_score` is 1 on all three rows | Task 3's calibration did not take | Re-run Task 3 Step 8 and read the rendered prefix; the "Correct score" lines must not all read 1 |
| `pipeline_output` holds an error string or `None` | Answerer call failed but the row was still written | Read the traceback in the run output, fix the cause, then delete nothing: re-running skips only genuinely complete cells |
| `generation.failures` is non-empty | Per-cell exception, already logged | Read `exception_type`/`exception_message` in the summary dict; the failed keys were never written, so a re-run retries exactly them |
| `FileNotFoundError` naming `storage/summary_index/...` | A P3 tree is missing | Hard stop. The trees are built and verified; a missing one means the storage directory was damaged |
| First call hangs for minutes | fastembed is downloading the embedding and rerank models | Not a failure. Wait |
| `input_tokens`/`output_tokens` are NULL | Usage not returned by the pinned host | Non-blocking. Note it and carry on; it only affects the efficiency pillar's completeness |

- [ ] **Step 4: Record the observed unit cost**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 benchmark.db "SELECT AVG(input_tokens), AVG(output_tokens), AVG(latency_sec) FROM results WHERE source_set='JEQ';"
```

Multiply by 1,860 (900 answerer + 900 judge + the 60 gate rows) and check the projection against the roughly $1 to $1.55 estimate. If the projected total exceeds $4, stop and report rather than proceeding to Task 8.

- [ ] **Step 5: Commit the rehearsal state**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/benchmark.db
git commit -m "chore(gate): throttled rehearsal of the validation gate on OpenRouter"
```

---

## Task 5: Run the full 60-row validation gate

**Files:**
- Modify: `project/.env` (flipped and restored within the task)

**Interfaces:**
- Consumes: Task 4's rehearsal rows (skipped by the resume path).
- Produces: exactly 60 `results` rows with `source_set='JEQ'`, `k_value=5`, each carrying `judge_score` and the full deterministic metric vector. `human_score` stays NULL; Task 6 fills it.

- [ ] **Step 1: Turn the throttle off**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sed -i '' 's/^LOCAL_TEST_THROTTLE=true/LOCAL_TEST_THROTTLE=false/' .env
grep -n "LOCAL_TEST_THROTTLE" .env
```

Expected: `LOCAL_TEST_THROTTLE=false # Change to false when building P3 Summary Tree`.

- [ ] **Step 2: Run the gate**

Run this in the background — it makes roughly 114 sequential API calls at 20 RPM, so allow around 10 minutes:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python validation_gate.py --db-path benchmark.db 2>&1 | tee logs/validation_gate_full.log
```

Expected: `generation.outstanding == 57` (60 minus Task 4's 3), `generation.completed == 57`, `generation.failures == []`, `judging.judged == 60`.

- [ ] **Step 3: Verify all 60 rows are complete**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -header benchmark.db "
SELECT COUNT(*) AS rows,
       SUM(judge_score IS NULL) AS missing_judge,
       SUM(pipeline_output IS NULL) AS missing_output,
       COUNT(DISTINCT query_id) AS queries,
       COUNT(DISTINCT pipeline) AS pipelines,
       COUNT(DISTINCT k_value) AS k_values
FROM results WHERE source_set='JEQ';"
```

Expected exactly: `rows=60, missing_judge=0, missing_output=0, queries=20, pipelines=3, k_values=1`.

If `failures` was non-empty, re-run Step 2. The resume path skips everything already written, so a re-run only retries the gaps.

- [ ] **Step 4: Restore the throttle**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sed -i '' 's/^LOCAL_TEST_THROTTLE=false/LOCAL_TEST_THROTTLE=true/' .env
```

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/benchmark.db project/logs/validation_gate_full.log
git commit -m "feat(gate): generate and judge all 60 validation-gate rows at K=5"
```

---

## Task 6: Agent-written reference scores and the concordance gate

`score_gate_outputs.py` collects reference scores through `input()`, which no unattended run can satisfy. It also frames the result as a human-judge Agreement Rate, which is no longer what the number measures.

The one property this figure retains on Path A is **independence**: the reference score must be written without seeing `results.judge_score`. `_render_row_for_human()` already omits it, and the new path must preserve that by construction, not by discipline.

**Files:**
- Create: `project/gate_reference_scores.py`
- Modify: `project/score_gate_outputs.py`
- Modify: `project/tests/test_score_gate_outputs.py`
- Modify: `resources/research/deviations.md`

**Interfaces:**
- Consumes: Task 5's 60 judged rows.
- Produces:
  - `gate_reference_scores.render_rows_for_scoring(db_path: str) -> list[dict]` — the 60 rows with `judge_score` stripped.
  - `gate_reference_scores.apply_scores(db_path: str, scores: dict[str, int]) -> int` — writes `human_score` by `result_id`, returns the count.
  - `score_gate_outputs.compute_agreement_rate()` keeps its signature and returns the same keys; only the rendered wording changes.

- [ ] **Step 1: Write the failing test**

Append to `project/tests/test_score_gate_outputs.py`:

```python
import gate_reference_scores


async def test_rendered_rows_never_carry_the_judge_score(tmp_path):
    """Independence is the only property the gate figure retains on this
    path, so the judge_score must be absent from the rendering by
    construction rather than by the caller's restraint."""
    db_path = str(tmp_path / "t.db")
    await _seed_row(db_path, judge_score=9)
    rows = await gate_reference_scores.render_rows_for_scoring(db_path)
    assert rows
    for row in rows:
        assert "judge_score" not in row


async def test_apply_scores_writes_every_supplied_row(tmp_path):
    db_path = str(tmp_path / "t.db")
    await _seed_row(db_path, judge_score=9)
    rows = await gate_reference_scores.render_rows_for_scoring(db_path)
    written = await gate_reference_scores.apply_scores(
        db_path, {row["result_id"]: 8 for row in rows}
    )
    assert written == len(rows)
    stored = await dbm.get_results(db_path, "JEQ")
    assert all(r["human_score"] == 8 for r in stored)


async def test_apply_scores_rejects_an_unknown_result_id(tmp_path):
    db_path = str(tmp_path / "t.db")
    await _seed_row(db_path, judge_score=9)
    with pytest.raises(ValueError, match="no results row"):
        await gate_reference_scores.apply_scores(db_path, {"R_nope": 5})


def test_verdict_uses_concordance_wording():
    summary = {"agreement_rate": 91.0, "agreements": 55, "n": 60, "gate_passed": True}
    text = score_gate_outputs._render_verdict(summary)
    assert "Concordance" in text
    assert "human" not in text.lower()
```

Reuse the file's existing `_seed_row` helper; extend it with a `judge_score` keyword argument if it does not already take one.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_score_gate_outputs.py -q
```

Expected: collection error `ModuleNotFoundError: No module named 'gate_reference_scores'`.

- [ ] **Step 3: Write the module**

Create `project/gate_reference_scores.py`:

```python
"""Reference scores for the validation gate, written without the Judge's.

On this run the agent supplies the reference score in place of a human, so
the figure the gate computes is cross-model concordance rather than an
external human-agreement rate. Independence is the one property it still
carries, and this module enforces it structurally: the rows it hands out
for scoring have judge_score removed, so a scorer cannot anchor on it even
by accident.
"""
import asyncio
import logging

import database_manager as dbm

logger = logging.getLogger(__name__)

# Everything the scorer needs to judge the answer, and nothing that reveals
# what the Judge already decided.
_VISIBLE_FIELDS = (
    "result_id",
    "query_id",
    "pipeline",
    "k_value",
    "quadrant",
    "query_text",
    "ground_truth_answer",
    "gt_citations",
    "pipeline_output",
    "cited_node_ids",
)


async def render_rows_for_scoring(db_path: str) -> list[dict]:
    """The gate rows, reduced to the fields a scorer may see."""
    rows = await dbm.get_jeq_judging_rows(db_path)
    return [{k: row[k] for k in _VISIBLE_FIELDS if k in row} for row in rows]


async def apply_scores(db_path: str, scores: dict[str, int]) -> int:
    """Write one reference score per result_id; returns the count written.

    update_result_human_score raises on an unknown result_id, so a typo in
    the mapping fails loudly rather than silently leaving a row unscored and
    shrinking the gate's denominator.
    """
    for result_id, score in scores.items():
        await dbm.update_result_human_score(db_path, result_id, score)
    return len(scores)


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print(json.dumps(asyncio.run(render_rows_for_scoring("benchmark.db")), indent=2))
```

- [ ] **Step 4: Update the verdict wording**

In `project/score_gate_outputs.py`, replace `_render_verdict` and the module docstring:

```python
def _render_verdict(summary: dict) -> str:
    head = (
        f"Concordance Rate: {summary['agreement_rate']:.1f}% "
        f"({summary['agreements']}/{summary['n']} rows within +/-1) "
        f"-- gate is > {GATE_THRESHOLD:.0f}%"
    )
    if summary["gate_passed"]:
        return head + "\nGATE PASSED. Phase 7 (full 900-run benchmark) may begin."
    return (
        head + "\nGATE FAILED. Do not run the full matrix. Revise the Judge rubric "
        "and/or swap the Judge model (e.g. gpt-oss-120b, still != the Llama answerer), "
        "then re-run the gate. Do not silently retry."
    )
```

Change the module docstring's first paragraph to:

```python
"""Reference scoring and the Judge validation gate.

Collects a reference score for each of the 60 JEQ gate rows, then measures
how closely the automated Judge agrees with it. Both scores are rescaled to
0-100; a row agrees when they differ by no more than 10 points on that
scale, and the gate requires a Concordance Rate strictly above 80%. The
scorer never sees the Judge's score, keeping the two judgements
independent. On a run where the agent supplies the reference scores this
figure is cross-model concordance, not external human validation.
"""
```

Leave `prompt_human_scores`, `rows_agree` and `compute_agreement_rate` alone. The interactive path stays available.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_score_gate_outputs.py -q
```

Expected: all pass.

- [ ] **Step 6: Score the 60 rows**

Dump the rows, **read every one**, and assign a 1-10 score using the same rubric `_RUBRIC` states: does the candidate match the ground truth, and does it cite only valid sources.

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python gate_reference_scores.py > /private/tmp/claude-501/-Users-ojaswi-Projects-rag-techniques/3871fba8-cfc3-4df2-92a5-cbfc30350bb6/scratchpad/gate_rows.json
wc -l /private/tmp/claude-501/-Users-ojaswi-Projects-rag-techniques/3871fba8-cfc3-4df2-92a5-cbfc30350bb6/scratchpad/gate_rows.json
```

**Do not query `results.judge_score` at any point during this step.** Reading it first would destroy the only property this figure still has.

Write the mapping to `/private/tmp/claude-501/-Users-ojaswi-Projects-rag-techniques/3871fba8-cfc3-4df2-92a5-cbfc30350bb6/scratchpad/reference_scores.json` as `{"R_JEQ_...": 8, ...}` with all 60 keys, then apply it:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'PY'
import asyncio, json
import gate_reference_scores

SCRATCH = "/private/tmp/claude-501/-Users-ojaswi-Projects-rag-techniques/3871fba8-cfc3-4df2-92a5-cbfc30350bb6/scratchpad"
scores = json.load(open(f"{SCRATCH}/reference_scores.json"))
assert len(scores) == 60, f"expected 60 scores, got {len(scores)}"
print("written:", asyncio.run(gate_reference_scores.apply_scores("benchmark.db", scores)))
PY
```

Expected: `written: 60`.

- [ ] **Step 7: Compute the gate**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'PY'
import asyncio
import database_manager as dbm
from score_gate_outputs import compute_agreement_rate, _render_verdict

async def main():
    rows = await dbm.get_results("benchmark.db", "JEQ")
    summary = compute_agreement_rate(rows)
    print(_render_verdict(summary))
    return summary

print(asyncio.run(main()))
PY
```

Expected: a Concordance Rate and a verdict line.

**If the gate fails (<= 80%):** do **not** proceed to Task 8 and do **not** silently retry. Guardrails §4b permits exactly two remedies, in this order:

1. **Revise `_RUBRIC` in `async_judge.py`.** First diagnose *how* it disagrees, because the remedy differs:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -header -column benchmark.db "
SELECT pipeline, COUNT(*) AS n,
       ROUND(AVG(judge_score),2) AS judge, ROUND(AVG(human_score),2) AS ref,
       ROUND(AVG(judge_score - human_score),2) AS bias
FROM results WHERE source_set='JEQ' GROUP BY pipeline;"
```

A consistent one-directional `bias` is a **calibration** problem: the rubric needs a sharper description of what each band means. A near-zero mean bias with wide scatter is a **discrimination** problem: the rubric's criteria are ambiguous and need splitting into explicit checks. Fix the one you actually have.

2. **Swap the Judge model** to one still outside the Llama family. `openai/gpt-oss-120b` is live on OpenRouter at a similar price. Update `MODEL_ROUTING["judge"]`, its pin, and Guardrails §2 together.

After either remedy, re-score the gate rows only:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 benchmark.db "UPDATE results SET judge_score = NULL WHERE source_set='JEQ';"
.venv/bin/python -c "
import asyncio
from judge.async_judge import judge_jeq_rows
print(asyncio.run(judge_jeq_rows('benchmark.db')))"
```

Use `judge_jeq_rows`, not `judge_rows`: the generalised `judge_rows` is created in Task 7, one task later. With `judge_score` already cleared the two behave identically here, since there is nothing for Task 7's `IS NULL` filter to skip.

Clearing `judge_score` here is the one permitted exception to "never delete state": it is re-derived from rows that already exist, costs 60 calls, and is required because Task 7's resume filter would otherwise skip every row. **Never clear `human_score`** — those are the reference scores and re-writing them after seeing the Judge's would destroy independence.

Record every attempt in the Step 8 deviation, including the ones that failed. A gate that passed on the third rubric is a materially different claim from one that passed first time, and the write-up needs to say which.

**Do not** lower `GATE_THRESHOLD`, widen `AGREEMENT_TOLERANCE`, or exclude rows. If both remedies fail, that is a hard stop.

- [ ] **Step 8: Log the deviation and commit**

Append to `resources/research/deviations.md`:

```markdown
### 31. Validation-gate reference scores written by the agent; the figure is concordance, not human agreement (2026-09-09)

1. **Originally proposed:** Guardrails 4b and Phase Plan Phase 6 require the researcher to hand-score all 60 gate outputs, with the human-judge Agreement Rate needing to clear 80 percent before the 900-run benchmark may start.
2. **Deviation:** The project is being completed with no human in the loop, and `score_gate_outputs.py` collected those scores through `input()`, which an unattended run cannot satisfy.
3. **What we did:** The agent wrote the 60 reference scores, and the gate figure is reported throughout as cross-model concordance rather than as a human-judge Agreement Rate.
4. **How we did it:** Added `gate_reference_scores.py`, whose `render_rows_for_scoring()` returns each row reduced to a fixed whitelist of visible fields that excludes `judge_score`, so a scorer cannot anchor on the Judge's answer even by accident; `apply_scores()` then writes the scores by `result_id`. The interactive `prompt_human_scores()` path is untouched and still available. `_render_verdict()` and the module docstring now say Concordance Rate. The threshold, the plus or minus 10 point band on the 0-100 scale and the strict greater-than comparison are all unchanged.
5. **Why we did it:** The trade is stated plainly rather than hidden. Because the agent supplied both the Judge's calibration exemplars and the gate's reference scores, the figure measures internal consistency between two agent-mediated judgements, not agreement with an external human standard. Independence between the two scores is the one property it retains, which is why the whitelist enforces it structurally. Any results summary or write-up drawing on the judge_score column must carry this caveat.
```

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/gate_reference_scores.py project/score_gate_outputs.py project/tests/test_score_gate_outputs.py project/benchmark.db resources/research/deviations.md
git commit -m "feat(gate): add non-interactive reference scoring and report concordance"
```

---

## Task 7: Generalise judging from JEQ-only to any source set

`judge_jeq_rows()` hardcodes `WHERE r.source_set = 'JEQ'` and joins `judge_validation`. Phase 7 needs the same scoring over 900 PQ rows joined to `queries`. Generalise rather than duplicate.

**Files:**
- Modify: `project/database_manager.py`
- Modify: `project/judge/async_judge.py`
- Modify: `project/tests/test_database_manager_judge.py`
- Modify: `project/tests/test_async_judge.py`

**Interfaces:**
- Consumes: Task 3's exemplars.
- Produces:
  - `database_manager.get_judging_rows(db_path: str, source_set: str) -> list[dict]` — rows joined to the query table `_SOURCE_SET_TABLES[source_set]` names.
  - `database_manager.get_jeq_judging_rows(db_path)` retained as a thin alias so nothing existing breaks.
  - `judge.async_judge.judge_rows(db_path: str, source_set: str = "JEQ", judge: Judge | None = None) -> dict` returning `{"judged": int, "failures": list[dict]}`.
  - `judge.async_judge.judge_jeq_rows(db_path, judge=None)` retained as an alias.

- [ ] **Step 1: Write the failing test**

Append to `project/tests/test_database_manager_judge.py`:

```python
async def test_get_judging_rows_joins_pq_to_the_queries_table(tmp_path):
    """PQ rows must reach the Judge with the same ground-truth fields JEQ
    rows carry, joined from `queries` rather than `judge_validation`."""
    db_path = str(tmp_path / "t.db")
    await dbm.init_db(db_path)
    await dbm.insert_query(db_path, {
        "query_id": "QT1_PQ_001",
        "quadrant": "Q1_Direct_Text",
        "query_text": "What year?",
        "ground_truth_answer": "2023",
        "gt_citations": ["AAPL_2023_n1"],
        "document_id": "AAPL_2023",
    })
    await dbm.upsert_result(db_path, {
        "result_id": "R_PQ_QT1_PQ_001_P1_vector_K3",
        "source_set": "PQ",
        "query_id": "QT1_PQ_001",
        "pipeline": "P1_vector",
        "k_value": 3,
        "retrieved_node_ids": ["AAPL_2023_n1"],
        "pipeline_output": "2023 [AAPL_2023_n1]",
        "cited_node_ids": ["AAPL_2023_n1"],
    })

    rows = await dbm.get_judging_rows(db_path, "PQ")
    assert len(rows) == 1
    assert rows[0]["quadrant"] == "Q1_Direct_Text"
    assert rows[0]["ground_truth_answer"] == "2023"
    assert rows[0]["gt_citations"] == ["AAPL_2023_n1"]


async def test_get_judging_rows_rejects_an_unknown_source_set(tmp_path):
    db_path = str(tmp_path / "t.db")
    await dbm.init_db(db_path)
    with pytest.raises(ValueError, match="source_set must be one of"):
        await dbm.get_judging_rows(db_path, "GQ")
```

Append to `project/tests/test_async_judge.py`:

```python
async def test_judge_rows_scores_the_pq_source_set(tmp_path, monkeypatch):
    """judge_rows must reach PQ rows, not just the gate's JEQ rows."""
    db_path = str(tmp_path / "t.db")
    await _seed_pq_row(db_path)

    class _StubJudge:
        async def score_row(self, row, system_prompt):
            return 7

    summary = await async_judge.judge_rows(db_path, source_set="PQ", judge=_StubJudge())
    assert summary["judged"] == 1
    assert summary["failures"] == []
    stored = await dbm.get_results(db_path, "PQ")
    assert stored[0]["judge_score"] == 7
```

Add a `_seed_pq_row` helper mirroring the file's existing JEQ seeding helper, inserting into `queries` and `results` with `source_set='PQ'`, plus the 5 `golden_queries` rows the prefix build needs for that quadrant.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_database_manager_judge.py tests/test_async_judge.py -q
```

Expected: `AttributeError: module 'database_manager' has no attribute 'get_judging_rows'` and the same for `judge_rows`.

- [ ] **Step 3: Generalise the query**

In `project/database_manager.py`, replace `get_jeq_judging_rows` with:

```python
async def get_judging_rows(db_path: str, source_set: str) -> list[dict]:
    """Results rows for one source_set, joined to their ground truth.

    async_judge scores one results row at a time but needs that row's
    quadrant, ground-truth answer and gt_citations, none of which live in
    results. The join supplies them so the Judge never reaches across
    tables itself. The query table is chosen from _SOURCE_SET_TABLES, the
    same mapping get_queries() uses, so PQ and JEQ stay consistent and
    golden_queries stays unreachable from here.
    """
    try:
        table = _SOURCE_SET_TABLES[source_set]
    except KeyError as exc:
        raise ValueError(
            f"source_set must be one of {sorted(_SOURCE_SET_TABLES)}, got {source_set!r}"
        ) from exc

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"""SELECT r.*, q.quadrant, q.query_text, q.ground_truth_answer,
                       q.gt_citations, q.document_id
                FROM results r
                JOIN {table} q ON q.query_id = r.query_id
                WHERE r.source_set = ?
                ORDER BY r.result_id""",
            (source_set,),
        )
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["retrieved_node_ids"] = _loads(d["retrieved_node_ids"])
        d["cited_node_ids"] = _loads(d["cited_node_ids"])
        d["gt_citations"] = _loads(d["gt_citations"])
        result.append(d)
    return result


async def get_jeq_judging_rows(db_path: str) -> list[dict]:
    """The 60 gate rows. Kept as a named alias because the gate is a fixed,
    spec-level concept while get_judging_rows is the general mechanism."""
    return await get_judging_rows(db_path, "JEQ")
```

The `f"...{table}..."` interpolation is safe: `table` can only ever be a value from the module-level `_SOURCE_SET_TABLES` literal, never caller input.

Check the original `get_jeq_judging_rows` body for the exact decode lines it used and carry them over verbatim.

- [ ] **Step 4: Generalise the judging loop**

In `project/judge/async_judge.py`, rename `judge_jeq_rows` to `judge_rows`, add the `source_set` parameter, and swap the row read:

```python
async def judge_rows(db_path: str, source_set: str = "JEQ", judge: Judge | None = None) -> dict:
    """Scores every row in one source_set: deterministic metrics plus
    judge_score, one write each.

    Reads the rows joined to their ground truth, builds each quadrant's
    prompt prefix once, then scores the rows and writes the full metric
    vector back per row. Honours LOCAL_TEST_THROTTLE: under throttle only
    the first THROTTLE_LIMIT rows run.
    """
    if judge is None:
        judge = Judge()

    rows = await dbm.get_judging_rows(db_path, source_set)
    rows = [row for row in rows if row.get("judge_score") is None]
    rows = apply_throttle(rows)
```

Filtering already-scored rows is what makes a 900-row judging pass resumable: `update_result_scores` is an UPDATE with no uniqueness guard, so without it a re-run after a crash would re-spend on every row it had already scored.

Change the log line's `"judging %d JEQ row(s)%s"` to `"judging %d %s row(s)%s"` with `source_set` as the second argument. Leave the rest of the body unchanged.

At the end of the module add:

```python
async def judge_jeq_rows(db_path: str, judge: Judge | None = None) -> dict:
    """The gate's 60 rows. Named alias; see judge_rows."""
    return await judge_rows(db_path, source_set="JEQ", judge=judge)
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_database_manager_judge.py tests/test_async_judge.py tests/test_validation_gate.py -q && .venv/bin/python -m pytest -q
```

Expected: all pass; full suite `353 passed, 2 skipped`.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/database_manager.py project/judge/async_judge.py project/tests/test_database_manager_judge.py project/tests/test_async_judge.py
git commit -m "feat(judge): generalise judging to any source set and skip already-scored rows"
```

---

## Task 8: Execute the 900-cell benchmark

Only proceed if Task 6's gate passed. Retrieval is entirely local across all three pipelines (P3 binds a `MockLLM` deliberately), so this task's 900 API calls are all Answerer calls.

**Files:**
- Modify: `project/.env` (flipped and restored within the task)

**Interfaces:**
- Consumes: Tasks 2 and 6.
- Produces: 900 `results` rows with `source_set='PQ'`, each with `pipeline_output`, `cited_node_ids`, `latency_sec` and token counts. Score columns stay NULL; Task 9 fills them.

- [ ] **Step 1: Confirm the gate passed**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'PY'
import asyncio
import database_manager as dbm
from score_gate_outputs import compute_agreement_rate
rows = asyncio.run(dbm.get_results("benchmark.db", "JEQ"))
s = compute_agreement_rate(rows)
print(s)
assert s["gate_passed"], "Guardrails 4b: the full matrix may not run behind a failed gate"
PY
```

Expected: `gate_passed: True`. If this raises, stop and return to Task 6 Step 7.

- [ ] **Step 2: Rehearse at throttle**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
grep -n "LOCAL_TEST_THROTTLE" .env
.venv/bin/python loop_executor.py --db-path benchmark.db --source-set PQ 2>&1 | tail -20
```

Expected: `LOCAL_TEST_THROTTLE=true`, then `outstanding: 900, attempted: 3, completed: 3, failures: []`.

- [ ] **Step 3: Run the full matrix in the background**

900 calls at 20 RPM is about 45 minutes of API time, plus local retrieval. Launch it with `run_in_background: true` so the shell tile stays visible, and do not wrap it with a shell `&`:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sed -i '' 's/^LOCAL_TEST_THROTTLE=true/LOCAL_TEST_THROTTLE=false/' .env
.venv/bin/python loop_executor.py --db-path benchmark.db --source-set PQ 2>&1 | tee logs/benchmark_pq_run.log
```

Expected on completion: `outstanding: 897, completed: 897, failures: []`.

- [ ] **Step 4: Verify the matrix is complete**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -header benchmark.db "
SELECT COUNT(*) AS rows,
       COUNT(DISTINCT query_id) AS queries,
       COUNT(DISTINCT pipeline) AS pipelines,
       COUNT(DISTINCT k_value) AS ks,
       SUM(pipeline_output IS NULL) AS missing_output
FROM results WHERE source_set='PQ';"
sqlite3 -header -column benchmark.db "SELECT pipeline, k_value, COUNT(*) FROM results WHERE source_set='PQ' GROUP BY pipeline, k_value ORDER BY pipeline, k_value;"
```

Expected: `rows=900, queries=100, pipelines=3, ks=3, missing_output=0`, and nine groups of exactly 100.

**If it fails, fix it and re-run Step 3:**

| Symptom | Cause | Fix |
|---|---|---|
| Fewer than 900 rows | Run interrupted, or per-cell failures | Re-run Step 3's command verbatim. The `UNIQUE` resume key retries only the gaps and re-spends nothing |
| A group has fewer than 100 | One pipeline failed systematically at one K | Read `failures` in the summary for that pipeline; fix the cause before re-running, or it will fail identically |
| Repeated `429` | Rate limit, despite the 20 RPM client cap | Transient. Re-run; the client backs off. If it persists, lower `OPENROUTER_MAX_CONCURRENCY` in `config.py` from 5 to 2 |
| `sqlite3.OperationalError: database is locked` | Two writers on the same file | Confirm no second run is alive, then re-run. WAL mode tolerates a reader alongside a writer, not two writers |
| Run dies silently | Session halt, not a code failure | Expected on a long run. Re-run; see the Session Resume Protocol |
| Spend climbing past the Task 4 projection | Retries, or larger prompts than sampled | Stop at $4 and report. Do not let it run past that unattended |

- [ ] **Step 5: Restore the throttle and commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sed -i '' 's/^LOCAL_TEST_THROTTLE=false/LOCAL_TEST_THROTTLE=true/' .env
cd /Users/ojaswi/Projects/rag-techniques
git add project/benchmark.db project/logs/benchmark_pq_run.log
git commit -m "feat(benchmark): execute all 900 PQ cells across three pipelines and K in 2,3,5"
```

---

## Task 9: Score all 900 rows

**Files:**
- Modify: `project/.env` (flipped and restored within the task)

**Interfaces:**
- Consumes: Tasks 7 and 8.
- Produces: all 900 PQ rows carrying `judge_score`, `precision_at_k`, `recall_at_k`, `evidence_hit`, `citation_match`, `token_f1`, and `exact_match` (NULL for the Q2/Q4 implicit quadrants by design).

- [ ] **Step 1: Rehearse at throttle**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'PY'
import asyncio
from judge.async_judge import judge_rows
print(asyncio.run(judge_rows("benchmark.db", source_set="PQ")))
PY
```

Expected: `{'judged': 3, 'failures': []}`.

- [ ] **Step 2: Score the remaining rows**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sed -i '' 's/^LOCAL_TEST_THROTTLE=true/LOCAL_TEST_THROTTLE=false/' .env
.venv/bin/python - <<'PY' 2>&1 | tee logs/benchmark_pq_judging.log
import asyncio, logging
from judge.async_judge import judge_rows
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
print(asyncio.run(judge_rows("benchmark.db", source_set="PQ")))
PY
```

Expected: `{'judged': 897, 'failures': []}`. Roughly 45 minutes at 20 RPM.

- [ ] **Step 3: Verify every row is scored**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -header benchmark.db "
SELECT COUNT(*) AS rows,
       SUM(judge_score IS NULL) AS missing_judge,
       SUM(precision_at_k IS NULL) AS missing_precision,
       SUM(token_f1 IS NULL) AS missing_f1,
       MIN(judge_score) AS min_score,
       MAX(judge_score) AS max_score,
       ROUND(AVG(judge_score),2) AS mean_score
FROM results WHERE source_set='PQ';"
```

Expected: `rows=900`, all three `missing_*` at 0, and a `min_score`/`max_score` spread that is not a single constant. A constant score means the Judge collapsed; stop and report rather than proceeding to analysis.

`exact_match` is deliberately NULL for Q2 and Q4. Confirm that is what you see, and that it is populated for Q1 and Q3:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -header -column benchmark.db "
SELECT q.quadrant, COUNT(*) AS n, SUM(r.exact_match IS NULL) AS null_em
FROM results r JOIN queries q ON q.query_id = r.query_id
WHERE r.source_set='PQ' GROUP BY q.quadrant;"
```

Expected: `null_em` equals `n` for `Q2_Implicit_Text` and `Q4_Implicit_Table`, and 0 for `Q1_Direct_Text` and `Q3_Direct_Table`.

**If it fails, fix it and re-run Step 2:**

| Symptom | Cause | Fix |
|---|---|---|
| `missing_judge` above 0 | Run interrupted, or rows failed | Re-run Step 2. The `judge_score IS NULL` filter retries exactly the gaps |
| `min_score == max_score` | The Judge collapsed to one value | **Hard stop.** Every downstream number is meaningless. Report it; do not analyse the results |
| `ValueError: could not parse a 1-10 judge score` | The Judge returned prose, or an empty content | Read the raw reply. If content is `None`, the pinned host is truncating; check `max_completion_tokens` on that endpoint |
| `null_em` above 0 for Q1 or Q3 | Numeric normalisation failed on those answers | Not fatal. Inspect the affected rows in `judge/numeric_normalizer.py`; `exact_match` is a secondary metric and the judge score stands regardless |
| Mean judge score near 10 across every pipeline | Calibration ceiling: the exemplars taught only the high end | Re-check Task 3's per-quadrant good/bad split before trusting the analysis |

- [ ] **Step 4: Restore the throttle and commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sed -i '' 's/^LOCAL_TEST_THROTTLE=false/LOCAL_TEST_THROTTLE=true/' .env
cd /Users/ojaswi/Projects/rag-techniques
git add project/benchmark.db project/logs/benchmark_pq_judging.log
git commit -m "feat(benchmark): score all 900 PQ rows with the judge and code metrics"
```

---

## Task 10: The aggregation module

Phase 8 Goal 1 is the tri-pillar aggregation; Goal 2 is the per-quadrant breakdown. Evaluation 1 requires it be reproducible from `results` alone with no manual shuffling, so everything here reads the database and nothing takes a hand-prepared input.

**Files:**
- Create: `project/analysis/__init__.py`
- Create: `project/analysis/aggregate.py`
- Create: `project/tests/test_aggregate.py`

**Interfaces:**
- Consumes: Task 9's scored rows.
- Produces:
  - `analysis.aggregate.load_rows(db_path: str, source_set: str = "PQ") -> list[dict]` — results joined to their quadrant.
  - `analysis.aggregate.summarise(rows: list[dict], by: tuple[str, ...]) -> list[dict]` — one dict per group with `n` and the mean of each metric; keys are the group fields plus `mean_<metric>`.
  - `analysis.aggregate.TRI_PILLAR: dict[str, tuple[str, ...]]` — the three pillars mapped to their metric column names.
  - `analysis.aggregate.to_markdown_table(summary: list[dict], columns: tuple[str, ...]) -> str`

- [ ] **Step 1: Write the failing test**

Create `project/tests/test_aggregate.py`:

```python
"""Aggregation maths, checked on synthetic rows rather than the live table.

Live data would make these tests move whenever the benchmark is re-run; the
point here is that the grouping and the mean are right, including how NULL
metrics are handled.
"""
import pytest

from analysis import aggregate


def _row(pipeline="P1_vector", k=3, quadrant="Q1_Direct_Text", **metrics):
    base = {
        "pipeline": pipeline,
        "k_value": k,
        "quadrant": quadrant,
        "judge_score": 8,
        "token_f1": 0.5,
        "precision_at_k": 0.5,
        "recall_at_k": 1.0,
        "evidence_hit": 1,
        "citation_match": 1,
        "exact_match": 1,
        "latency_sec": 2.0,
        "input_tokens": 100,
        "output_tokens": 20,
    }
    base.update(metrics)
    return base


def test_summarise_groups_by_the_requested_fields():
    rows = [_row(pipeline="P1_vector"), _row(pipeline="P1_vector"), _row(pipeline="P2_bm25")]
    out = aggregate.summarise(rows, by=("pipeline",))
    assert {g["pipeline"] for g in out} == {"P1_vector", "P2_bm25"}
    assert {g["pipeline"]: g["n"] for g in out} == {"P1_vector": 2, "P2_bm25": 1}


def test_summarise_means_a_metric():
    rows = [_row(judge_score=6), _row(judge_score=8)]
    out = aggregate.summarise(rows, by=("pipeline",))
    assert out[0]["mean_judge_score"] == pytest.approx(7.0)


def test_summarise_ignores_nulls_in_the_mean_but_not_in_n():
    """exact_match is NULL for the implicit quadrants by design, so a NULL
    must not be read as a zero and drag the mean down."""
    rows = [_row(exact_match=1), _row(exact_match=None)]
    out = aggregate.summarise(rows, by=("pipeline",))
    assert out[0]["n"] == 2
    assert out[0]["mean_exact_match"] == pytest.approx(1.0)


def test_summarise_reports_none_when_every_value_is_null():
    rows = [_row(exact_match=None), _row(exact_match=None)]
    out = aggregate.summarise(rows, by=("pipeline",))
    assert out[0]["mean_exact_match"] is None


def test_summarise_by_pipeline_and_quadrant_crosses_them():
    rows = [
        _row(pipeline="P3_structural", quadrant="Q3_Direct_Table"),
        _row(pipeline="P3_structural", quadrant="Q1_Direct_Text"),
    ]
    out = aggregate.summarise(rows, by=("pipeline", "quadrant"))
    assert len(out) == 2


def test_summarise_is_ordered_deterministically():
    rows = [_row(pipeline="P3_structural"), _row(pipeline="P1_vector"), _row(pipeline="P2_bm25")]
    out = aggregate.summarise(rows, by=("pipeline",))
    assert [g["pipeline"] for g in out] == ["P1_vector", "P2_bm25", "P3_structural"]


def test_tri_pillar_covers_the_three_dissertation_axes():
    assert set(aggregate.TRI_PILLAR) == {"retrieval", "answer_quality", "efficiency"}
    assert "judge_score" in aggregate.TRI_PILLAR["answer_quality"]
    assert "recall_at_k" in aggregate.TRI_PILLAR["retrieval"]
    assert "latency_sec" in aggregate.TRI_PILLAR["efficiency"]


def test_to_markdown_table_renders_a_header_and_a_row():
    summary = [{"pipeline": "P1_vector", "n": 300, "mean_judge_score": 7.25}]
    table = aggregate.to_markdown_table(summary, columns=("pipeline", "n", "mean_judge_score"))
    lines = table.splitlines()
    assert lines[0].startswith("| pipeline")
    assert "7.25" in lines[2]


def test_to_markdown_table_renders_a_null_mean_as_a_dash():
    summary = [{"pipeline": "P1_vector", "n": 300, "mean_exact_match": None}]
    table = aggregate.to_markdown_table(summary, columns=("pipeline", "n", "mean_exact_match"))
    assert "| -" in table
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_aggregate.py -q
```

Expected: `ModuleNotFoundError: No module named 'analysis'`.

- [ ] **Step 3: Write the module**

Create `project/analysis/__init__.py` (empty file), then `project/analysis/aggregate.py`:

```python
"""Aggregates the results table into the tri-pillar and per-quadrant views.

Everything here reads results and the query tables and nothing else, so the
figures in the write-up can be regenerated from the database alone. NULL
metrics are excluded from a mean rather than coerced to zero: exact_match is
NULL by design for the implicit quadrants, and reading those as failures
would understate every pipeline on exactly the questions the benchmark cares
most about.
"""
import asyncio
import statistics

import database_manager as dbm

# The three axes Phase 8 Goal 1 aggregates across. Judge score is the primary
# answer-quality measure; F1 and exact match are secondary.
TRI_PILLAR: dict[str, tuple[str, ...]] = {
    "retrieval": ("precision_at_k", "recall_at_k", "evidence_hit", "citation_match"),
    "answer_quality": ("judge_score", "token_f1", "exact_match"),
    "efficiency": ("latency_sec", "input_tokens", "output_tokens"),
}

METRICS: tuple[str, ...] = tuple(m for pillar in TRI_PILLAR.values() for m in pillar)


async def load_rows(db_path: str, source_set: str = "PQ") -> list[dict]:
    """Scored rows joined to their quadrant, which lives on the query table."""
    return await dbm.get_judging_rows(db_path, source_set)


def summarise(rows: list[dict], by: tuple[str, ...]) -> list[dict]:
    """Group rows by `by` and mean every metric within each group.

    Sorted by the grouping key so a regenerated table diffs cleanly against
    the previous run rather than reordering on dict iteration.
    """
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        groups.setdefault(tuple(row[field] for field in by), []).append(row)

    summary = []
    for key in sorted(groups):
        members = groups[key]
        entry = dict(zip(by, key))
        entry["n"] = len(members)
        for metric in METRICS:
            values = [m[metric] for m in members if m.get(metric) is not None]
            entry[f"mean_{metric}"] = statistics.fmean(values) if values else None
        summary.append(entry)
    return summary


def to_markdown_table(summary: list[dict], columns: tuple[str, ...]) -> str:
    """Render one summary as a Markdown table.

    A None mean renders as "-" rather than 0 or "None", so a metric that does
    not apply to a group reads as inapplicable instead of as a zero score.
    """
    def cell(value) -> str:
        if value is None:
            return "-"
        if isinstance(value, float):
            return f"{value:.3f}"
        return str(value)

    header = "| " + " | ".join(columns) + " |"
    rule = "|" + "|".join("---" for _ in columns) + "|"
    body = [
        "| " + " | ".join(cell(row.get(c)) for c in columns) + " |"
        for row in summary
    ]
    return "\n".join([header, rule, *body])


__all__ = ["TRI_PILLAR", "METRICS", "load_rows", "summarise", "to_markdown_table"]
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_aggregate.py -q && .venv/bin/python -m pytest -q
```

Expected: 9 passed in the new file; full suite `362 passed, 2 skipped`.

- [ ] **Step 5: Sanity-check it against the live table**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python - <<'PY'
import asyncio
from analysis import aggregate

async def main():
    rows = await aggregate.load_rows("benchmark.db", "PQ")
    print("rows:", len(rows))
    print(aggregate.to_markdown_table(
        aggregate.summarise(rows, by=("pipeline",)),
        columns=("pipeline", "n", "mean_judge_score", "mean_recall_at_k", "mean_latency_sec"),
    ))

asyncio.run(main())
PY
```

Expected: `rows: 900` and a three-row table with distinguishable means per pipeline.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/analysis/__init__.py project/analysis/aggregate.py project/tests/test_aggregate.py
git commit -m "feat(analysis): add tri-pillar and per-quadrant aggregation over results"
```

---

## Task 11: Figures, tables, and the results summary

Phase 8 Deliverables 2 and 3. Evaluation 3 requires the outputs be framed with statistical honesty, and on this run that honesty must also carry Task 6's concordance caveat.

**Files:**
- Create: `project/analysis/figures.py`
- Create: `project/analysis/run_analysis.py`
- Modify: `project/pyproject.toml` (adds matplotlib)

**Interfaces:**
- Consumes: Task 10's `aggregate`.
- Produces:
  - `analysis.figures.plot_judge_score_by_pipeline_and_k(summary, out_path) -> Path`
  - `analysis.figures.plot_quadrant_heatmap(summary, out_path) -> Path`
  - `analysis.figures.plot_retrieval_vs_k(summary, out_path) -> Path`
  - `analysis.run_analysis.main(db_path, out_dir) -> dict` writing `results_summary.md` plus three PNGs into `resources/artifacts/analysis/`.

- [ ] **Step 1: Add matplotlib**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
uv add matplotlib
.venv/bin/python -c "import matplotlib; print(matplotlib.__version__)"
```

Expected: a version number. matplotlib runs locally at $0, so this does not touch the infrastructure ban in Guardrails §1.

**If it fails:** a resolver conflict against the pinned `onnxruntime==1.23.2` is the likely cause. Try `uv add "matplotlib>=3.8"`. If it still conflicts, do not unpin `onnxruntime` — that pin exists for `fastembed` on this platform. Fall back to rendering the three figures as inline SVG built by hand in `figures.py`; the report in Task 13 embeds them either way.

- [ ] **Step 2: Write the figures module**

Create `project/analysis/figures.py`:

```python
"""Figures for the write-up, rendered from aggregate summaries.

Agg backend is forced because this runs headless; without it matplotlib
picks a GUI backend and fails on a machine with no display. Typography
follows resources/assets/design/typography.md: Calibri for figure text,
with a fallback chain because Calibri is not guaranteed present.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PIPELINE_LABELS = {
    "P1_vector": "P1 semantic",
    "P2_bm25": "P2 statistical",
    "P3_structural": "P3 structural",
}
QUADRANT_LABELS = {
    "Q1_Direct_Text": "Q1 direct text",
    "Q2_Implicit_Text": "Q2 implicit text",
    "Q3_Direct_Table": "Q3 direct table",
    "Q4_Implicit_Table": "Q4 implicit table",
}

plt.rcParams["font.family"] = ["Calibri", "Helvetica", "DejaVu Sans"]
plt.rcParams["figure.dpi"] = 150


def _save(fig, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_judge_score_by_pipeline_and_k(summary: list[dict], out_path: Path) -> Path:
    """Grouped bars: mean judge score per pipeline at each K.

    Takes a summary grouped by ("pipeline", "k_value").
    """
    pipelines = sorted({row["pipeline"] for row in summary})
    ks = sorted({row["k_value"] for row in summary})
    width = 0.8 / len(ks)

    fig, ax = plt.subplots(figsize=(7, 4))
    for i, k in enumerate(ks):
        values = [
            next((r["mean_judge_score"] for r in summary
                  if r["pipeline"] == p and r["k_value"] == k), 0) or 0
            for p in pipelines
        ]
        offsets = [x - 0.4 + width / 2 + i * width for x in range(len(pipelines))]
        ax.bar(offsets, values, width, label=f"K = {k}")

    ax.set_xticks(range(len(pipelines)))
    ax.set_xticklabels([PIPELINE_LABELS.get(p, p) for p in pipelines])
    ax.set_ylabel("Mean judge score (1-10)")
    ax.set_ylim(0, 10)
    ax.set_title("Figure 1.1  Answer quality by pipeline and retrieval depth")
    ax.legend(title="Retrieval depth")
    return _save(fig, out_path)


def plot_quadrant_heatmap(summary: list[dict], out_path: Path) -> Path:
    """Pipeline x quadrant mean judge score.

    Takes a summary grouped by ("pipeline", "quadrant"). This is the figure
    that should expose P3's expected degradation on the table quadrants.
    """
    pipelines = sorted({row["pipeline"] for row in summary})
    quadrants = sorted({row["quadrant"] for row in summary})
    grid = [
        [next((r["mean_judge_score"] for r in summary
               if r["pipeline"] == p and r["quadrant"] == q), None) or 0
         for q in quadrants]
        for p in pipelines
    ]

    fig, ax = plt.subplots(figsize=(7, 3.5))
    im = ax.imshow(grid, cmap="YlGnBu", vmin=0, vmax=10, aspect="auto")
    ax.set_xticks(range(len(quadrants)))
    ax.set_xticklabels([QUADRANT_LABELS.get(q, q) for q in quadrants], rotation=20, ha="right")
    ax.set_yticks(range(len(pipelines)))
    ax.set_yticklabels([PIPELINE_LABELS.get(p, p) for p in pipelines])
    for i, row in enumerate(grid):
        for j, value in enumerate(row):
            ax.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, label="Mean judge score")
    ax.set_title("Figure 1.2  Answer quality by pipeline and question quadrant")
    return _save(fig, out_path)


def plot_retrieval_vs_k(summary: list[dict], out_path: Path) -> Path:
    """Mean recall@K against K, one line per pipeline.

    Takes a summary grouped by ("pipeline", "k_value").
    """
    pipelines = sorted({row["pipeline"] for row in summary})
    ks = sorted({row["k_value"] for row in summary})

    fig, ax = plt.subplots(figsize=(6, 4))
    for pipeline in pipelines:
        values = [
            next((r["mean_recall_at_k"] for r in summary
                  if r["pipeline"] == pipeline and r["k_value"] == k), None)
            for k in ks
        ]
        ax.plot(ks, values, marker="o", label=PIPELINE_LABELS.get(pipeline, pipeline))

    ax.set_xticks(ks)
    ax.set_xlabel("Retrieval depth K")
    ax.set_ylabel("Mean recall@K")
    ax.set_ylim(0, 1)
    ax.set_title("Figure 1.3  Retrieval recall against depth")
    ax.legend()
    return _save(fig, out_path)


__all__ = [
    "plot_judge_score_by_pipeline_and_k",
    "plot_quadrant_heatmap",
    "plot_retrieval_vs_k",
]
```

- [ ] **Step 3: Write the entry point**

Create `project/analysis/run_analysis.py`:

```python
"""Phase 8 entry point: results table in, tables and figures out.

Regenerates every analysis artefact from the database in one pass, so
nothing in the write-up depends on a value that was copied by hand.
"""
import argparse
import asyncio
import json
import logging
from pathlib import Path

from analysis import aggregate, figures
from score_gate_outputs import GATE_THRESHOLD, compute_agreement_rate
import database_manager as dbm

logger = logging.getLogger(__name__)

DEFAULT_OUT_DIR = Path(__file__).resolve().parents[2] / "resources" / "artifacts" / "analysis"

_CAVEATS = """
## How to read these numbers

- Every cell is a single run at temperature 0. There is no repeated sampling,
  so no confidence interval is available and small differences between
  pipelines should not be treated as significant.
- The judge score column is **not externally validated**. The agent supplied
  both the Judge's calibration exemplars and the gate's reference scores, so
  the gate figure below is cross-model concordance between two agent-mediated
  judgements, not agreement with a human standard. See deviations 30 and 31.
- The gate was measured on 60 samples. Guardrails 4b calls this a pragmatic
  check rather than strong proof, and that framing still applies.
- `exact_match` is undefined for the implicit quadrants (Q2, Q4) and is
  excluded from their means rather than counted as a failure.
- Retrieval for all three pipelines runs locally and calls no LLM, so the
  efficiency pillar's per-cell token counts describe answering and judging
  only. P3's one-time tree-build cost is reported separately below, because
  it is paid once per filing rather than once per cell and so cannot be
  averaged into a per-cell mean without misrepresenting it.
"""


_BUILD_COST_LOG = Path(__file__).resolve().parents[1] / "logs" / "index_build_costs.json"


def _load_index_build_cost(path: Path = _BUILD_COST_LOG) -> str:
    """P3's one-off tree-build cost, rendered as a Markdown table.

    Phase 8's efficiency pillar names index-build cost explicitly, but it is
    not a results column: it is paid once per filing at build time, not once
    per benchmark cell. It is read from the build log rather than recomputed,
    since rebuilding the trees to measure them would cost far more than the
    figure is worth.
    """
    if not path.exists():
        return "_No index-build cost log found at " + str(path) + "._"

    # The log is append-only across every build attempt (217 entries for 13
    # filings), so it holds skipped runs and repeat builds of the same
    # filing. Counting them all would multiply the corpus cost several times
    # over. Keep the last real build per filing, which is the one whose tree
    # is actually on disk and the same basis token_usage.md already uses.
    latest: dict[str, dict] = {}
    for entry in json.loads(path.read_text()):
        if entry.get("skipped") or not entry.get("input_tokens"):
            continue
        latest[entry["document_id"]] = entry

    rows = ["| document | input tokens | output tokens | wall clock (min) |", "|---|---|---|---|"]
    total_in = total_out = 0
    for doc in sorted(latest):
        entry = latest[doc]
        tin, tout = entry["input_tokens"], entry["output_tokens"]
        total_in += tin
        total_out += tout
        rows.append(f"| {doc} | {tin:,} | {tout:,} | {entry.get('wall_clock_sec', 0) / 60:.0f} |")
    rows.append(f"| **total ({len(latest)} filings)** | **{total_in:,}** | **{total_out:,}** | |")
    return "\n".join(rows)


async def main(db_path: str = "benchmark.db", out_dir: Path = DEFAULT_OUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = await aggregate.load_rows(db_path, "PQ")
    if not rows:
        raise ValueError(f"no PQ results in {db_path!r} -- run the benchmark first")

    by_pipeline = aggregate.summarise(rows, by=("pipeline",))
    by_pipeline_k = aggregate.summarise(rows, by=("pipeline", "k_value"))
    by_pipeline_quadrant = aggregate.summarise(rows, by=("pipeline", "quadrant"))

    gate_rows = await dbm.get_results(db_path, "JEQ")
    gate = compute_agreement_rate(gate_rows)
    build_cost = _load_index_build_cost()

    paths = {
        "judge_by_pipeline_k": figures.plot_judge_score_by_pipeline_and_k(
            by_pipeline_k, out_dir / "fig_1_1_judge_by_pipeline_k.png"),
        "quadrant_heatmap": figures.plot_quadrant_heatmap(
            by_pipeline_quadrant, out_dir / "fig_1_2_quadrant_heatmap.png"),
        "recall_vs_k": figures.plot_retrieval_vs_k(
            by_pipeline_k, out_dir / "fig_1_3_recall_vs_k.png"),
    }

    summary_md = "\n\n".join([
        "# Benchmark Results Summary",
        f"Generated from `{db_path}` over {len(rows)} scored PQ cells.",
        f"Cross-model concordance on the 60-row validation gate: "
        f"**{gate['agreement_rate']:.1f}%** "
        f"({gate['agreements']}/{gate['n']} rows), against a gate of "
        f"> {GATE_THRESHOLD:.0f}%.",
        "## Table 1.1  Tri-pillar summary by pipeline",
        aggregate.to_markdown_table(by_pipeline, columns=(
            "pipeline", "n", "mean_judge_score", "mean_token_f1", "mean_exact_match",
            "mean_precision_at_k", "mean_recall_at_k", "mean_evidence_hit",
            "mean_citation_match", "mean_latency_sec", "mean_input_tokens",
            "mean_output_tokens")),
        "## Table 1.2  By pipeline and retrieval depth",
        aggregate.to_markdown_table(by_pipeline_k, columns=(
            "pipeline", "k_value", "n", "mean_judge_score", "mean_recall_at_k",
            "mean_precision_at_k", "mean_citation_match")),
        "## Table 1.3  By pipeline and quadrant",
        aggregate.to_markdown_table(by_pipeline_quadrant, columns=(
            "pipeline", "quadrant", "n", "mean_judge_score", "mean_token_f1",
            "mean_exact_match", "mean_recall_at_k", "mean_evidence_hit")),
        "## Table 1.4  P3 index-build cost (one-off, per filing)",
        build_cost,
        "## Figures",
        "\n".join(f"- `{p.name}`" for p in paths.values()),
        _CAVEATS.strip(),
    ])

    summary_path = out_dir / "results_summary.md"
    summary_path.write_text(summary_md)
    logger.info("wrote %s and %d figure(s)", summary_path, len(paths))
    return {"summary": str(summary_path), "figures": {k: str(v) for k, v in paths.items()}}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default="benchmark.db")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = _parse_args()
    print(asyncio.run(main(db_path=args.db_path, out_dir=args.out_dir)))
```

- [ ] **Step 4: Run it**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m analysis.run_analysis --db-path benchmark.db
ls -la ../resources/artifacts/analysis/
```

Table 1.4 will show **11 filings, not 13**, totalling roughly 1.60M input and 0.89M output tokens. That is correct and not a bug: two of the 13 tree builds completed without logging token counts, which `resources/research/token_usage.md` already records. The per-filing mean it produces (about 146K in, 81K out) should match the measured figures in that file exactly; if it does not, the deduplication in `_load_index_build_cost()` is counting repeat builds and needs re-checking before you trust the table.

Expected: `results_summary.md` plus three PNGs. Note this writes into `resources/`, which the global constraints otherwise forbid; it is permitted here because `resources/artifacts/` is the deliverables folder and this is a Phase 8 deliverable.

- [ ] **Step 5: Read the output and check the figures render**

```bash
cd /Users/ojaswi/Projects/rag-techniques
cat resources/artifacts/analysis/results_summary.md
```

Then open each PNG with the Read tool and confirm: axes are labelled, no text is clipped, the bars and lines carry real spread rather than sitting flat, and the heatmap annotations are legible.

- [ ] **Step 6: Full suite, then commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project && .venv/bin/python -m pytest -q
cd /Users/ojaswi/Projects/rag-techniques
git add project/analysis/figures.py project/analysis/run_analysis.py project/pyproject.toml project/uv.lock resources/artifacts/analysis/
git commit -m "feat(analysis): generate results summary, comparison tables and figures"
```

---

## Task 12: Reconcile the documentation with what was actually built

This is a checkpoint, not the last task: Task 13 follows it and adds the HTML report. Write the docs to describe the benchmark and analysis as complete, and leave the report for Task 13 to announce.

**Files:**
- Modify: `project/groq_limits.md`
- Modify: `resources/research/build_progress.md`
- Modify: `resources/research/deviations.md`
- Modify: `CLAUDE.md`
- Modify: `openwiki/benchmark-design.md`

- [ ] **Step 1: Fix the stale provider notes**

`project/groq_limits.md` still lists the Generator and Critic on Groq and P3 as `llama-3.1-8b-instant`. None of that has been true since deviations 23 to 26, and after Task 2 the Answerer and Judge are off Groq too. Read it, then rewrite the routing section to describe only what still runs on Groq, which is the `debug` stage alone. Add a line at the top noting the file covers Groq's limits specifically and pointing at `resources/specs/Guardrails.md` §2 as the routing authority.

- [ ] **Step 2: Update the build progress record**

Append a Phase 6b/7/8 completion entry to `resources/research/build_progress.md`, matching the file's existing format. Read the file first to copy its heading style and section order. The entry must state, with the real measured values:

- the cross-model concordance figure and the wording **concordance**, never "human agreement";
- 60 gate rows at K=5 and 900 PQ cells, all scored, with the nine per-pipeline-per-K groups confirmed at 100 each;
- the observed OpenRouter spend against the roughly $1 to $1.55 estimate, and the wall clock the run actually took;
- the final test count from Step 5;
- a pointer to `resources/artifacts/analysis/results_summary.md` as the analysis deliverable.

- [ ] **Step 2b: Record the token cost with its reasoning**

`resources/research/token_usage.md` logs LLM token cost per operation, and every entry there carries the reasoning behind the number rather than a bare figure, because the file feeds the dissertation's cost discussion. Its header currently scopes "token usage" to "Groq/NVIDIA NIM LLM API tokens specifically", which is now incomplete.

Pull the real totals:

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
sqlite3 -header benchmark.db "
SELECT source_set,
       SUM(input_tokens) AS in_tok,
       SUM(output_tokens) AS out_tok,
       ROUND(SUM(latency_sec)/3600.0, 2) AS answer_hours
FROM results GROUP BY source_set;"
```

Note these columns cover the **Answerer** only; `judge_rows()` writes scores through `update_result_scores()`, which has no token columns, so the Judge's usage is not recorded per row. Read it from the OpenRouter activity page or state plainly that it was not instrumented, rather than inventing a figure.

Then append two sections in the file's existing style, each with an Input Token Cost, an Output Token Cost, and a Reason paragraph that explains what drove the number:

- **Phase 6 — Validation gate (60 rows, K=5)** — 60 answerer calls plus 60 judge calls. The reason should note that the judge's input is dominated by the cacheable per-quadrant prefix (rubric plus 5 exemplars) rather than by the target row.
- **Phase 7 — Full benchmark (900 cells)** — 900 answerer calls plus 900 judge calls. The reason should note that answerer input scales with K, since a K=5 cell carries roughly 2.5 times the retrieved-node text of a K=2 cell, so the mean sits between the two rather than at either end.

Also widen the file's header sentence to include OpenRouter alongside Groq and NVIDIA NIM, since deviation 29 moved the two highest-volume stages there.

- [ ] **Step 3: Log the two remaining deviations**

Append to `resources/research/deviations.md`:

```markdown
### 32. `openai/gpt-oss-20b:free` withdrawn from OpenRouter (2026-09-09)

1. **Originally proposed:** Deviation 26 moved the Critic to `openai/gpt-oss-20b:free` on OpenRouter, and Guardrails 2 records that as the Critic's fixed model.
2. **Deviation:** The `:free` variant no longer appears in OpenRouter's model list; only the paid `openai/gpt-oss-20b` remains.
3. **What we did:** Nothing. The routing entry is left as it stands and the model was not swapped.
4. **How we did it:** Confirmed against `GET /api/v1/models` that `openai/gpt-oss-20b` exists as a paid model while the `:free` slug does not.
5. **Why we did it:** The Critic runs only during dataset generation, which completed on 2026-08-11 and is not repeated in this plan, so nothing in the benchmark run touches it. Changing a model that produced the finished dataset would misrepresent how that dataset was built. This is recorded so that any future regeneration knows to expect a failure on the free slug and to price the paid one.
```

Then add a Phase 8 entry describing anything the analysis work itself deviated on, if it did. If it did not, note that explicitly in `build_progress.md` rather than padding `deviations.md`.

- [ ] **Step 4: Update the project state in CLAUDE.md and the wiki**

`CLAUDE.md` §1 says "The Judge's >80% agreement gate has not been run, the `results` table is empty, and Phase 7 (the full 900-run benchmark) is the next milestone." Replace that sentence with the true state: the gate cleared at its measured concordance figure, `results` holds 960 rows (900 PQ plus 60 JEQ), and Phase 8's analysis artefacts are in `resources/artifacts/analysis/`. Update the test count in the same sentence.

Check `openwiki/benchmark-design.md` for the same claims and correct any that have gone stale.

- [ ] **Step 5: Final verification**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest -q
grep -n "LOCAL_TEST_THROTTLE" .env
sqlite3 -header benchmark.db "SELECT source_set, COUNT(*), SUM(judge_score IS NULL) AS unscored FROM results GROUP BY source_set;"
cd /Users/ojaswi/Projects/rag-techniques && git status --short && git log --oneline -12
```

Expected: full suite green; `LOCAL_TEST_THROTTLE=true`; `PQ|900|0` and `JEQ|60|0`; a clean working tree once Step 6 commits; and twelve task commits on `automate`, none of them merged anywhere. Task 13 adds the thirteenth.

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/groq_limits.md resources/research/build_progress.md resources/research/token_usage.md resources/research/deviations.md CLAUDE.md openwiki/benchmark-design.md
git commit -m "docs: reconcile project state, routing notes and deviations with the completed run"
```

- [ ] **Step 7: Refresh the knowledge graph**

```bash
cd /Users/ojaswi/Projects/rag-techniques
graphify update .
git add graphify-out && git commit -m "chore(graphify): refresh knowledge graph after phases 6b to 8"
```

---

## Task 13: The HTML benchmark report

The final deliverable: one self-contained page carrying the whole result, published as an Artifact so it has a shareable link. This is the artefact a supervisor reads, so its honesty about what the judge scores do and do not prove matters as much as its numbers.

**Files:**
- Create: `project/analysis/build_report.py`
- Create: `project/tests/test_build_report.py`
- Create: `resources/artifacts/analysis/benchmark_report.html`

**Interfaces:**
- Consumes: Task 10's `aggregate`, Task 11's figures and `results_summary.md`.
- Produces:
  - `analysis.build_report.embed_png(path: Path) -> str` — a `data:image/png;base64,...` URI.
  - `analysis.build_report.build_html(context: dict) -> str` — the page body.
  - `analysis.build_report.main(db_path: str, out_path: Path) -> Path`.

- [ ] **Step 1: Write the failing test**

Create `project/tests/test_build_report.py`:

```python
"""Guards on the report's self-containment and its honesty caveats.

The page is published to an artifact host whose CSP blocks every external
image, stylesheet and fetch, so an external reference does not error, it
silently renders nothing. These tests catch that before publication.
"""
import base64
from pathlib import Path

import pytest

from analysis import build_report


@pytest.fixture
def png(tmp_path):
    # A 1x1 PNG, enough to exercise the embedding path.
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    path = tmp_path / "fig.png"
    path.write_bytes(data)
    return path


def test_embed_png_returns_a_data_uri(png):
    uri = build_report.embed_png(png)
    assert uri.startswith("data:image/png;base64,")
    assert len(uri) > 30


def test_embed_png_raises_on_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_report.embed_png(tmp_path / "nope.png")


def _context(png_uri="data:image/png;base64,AAAA"):
    return {
        "n_cells": 900,
        "concordance": 91.7,
        "concordance_n": 60,
        "concordance_agreements": 55,
        "gate_threshold": 80.0,
        "tables": {"Table 1.1 Tri-pillar summary": "| pipeline |\n|---|\n| P1_vector |"},
        "figures": [("Figure 1.1 Answer quality", png_uri)],
        "generated": "2026-09-09",
    }


def test_build_html_carries_no_external_references():
    html = build_report.build_html(_context())
    for marker in ("http://", "https://", "src=\"/", "@import"):
        assert marker not in html, marker


def test_build_html_omits_the_document_skeleton():
    """The artifact host wraps the file in its own doctype/head/body."""
    html = build_report.build_html(_context())
    lowered = html.lower()
    for tag in ("<!doctype", "<html", "<head>", "<body"):
        assert tag not in lowered, tag


def test_build_html_includes_title_and_style():
    html = build_report.build_html(_context())
    assert "<title>" in html
    assert "<style>" in html


def test_build_html_states_the_validation_caveat():
    """The judge column is not externally validated; the page must say so
    rather than presenting concordance as human agreement."""
    html = build_report.build_html(_context())
    assert "concordance" in html.lower()
    assert "not externally validated" in html.lower()
    assert "human agreement" not in html.lower()


def test_build_html_embeds_every_figure():
    html = build_report.build_html(_context())
    assert "data:image/png;base64," in html


def test_build_html_wraps_tables_for_horizontal_scroll():
    """Wide tables must scroll inside their own container; the page body
    must never scroll sideways."""
    html = build_report.build_html(_context())
    assert "overflow-x" in html


def test_build_html_defines_light_colours_outside_any_media_query():
    """A colour defined only inside a dark-mode block leaves the light
    theme unstyled."""
    html = build_report.build_html(_context())
    root_block = html.split(":root")[1].split("}")[0]
    assert "--" in root_block
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_build_report.py -q
```

Expected: `ImportError: cannot import name 'build_report' from 'analysis'`.

- [ ] **Step 3: Load the design skill before writing any markup**

Invoke the `artifact-design` skill now. It calibrates how much design investment this page warrants, and it must be read **before** the HTML is written, not after.

- [ ] **Step 4: Write the report builder**

Create `project/analysis/build_report.py`. It regenerates from the database, so the page can never drift from `results`:

```python
"""Builds the self-contained HTML benchmark report.

Everything the page needs is inlined: the CSS, and the figures as base64
data URIs. The artifact host serves each page from its own origin under a
CSP that blocks external images and stylesheets outright, with no visible
error, so an external reference would render as a silent blank rather than
a broken-image icon.

The page deliberately leads with what the judge scores do not prove. It is
the artefact a supervisor reads, and a results page that presents an
agent-scored concordance figure as human validation would misrepresent the
method however accurate its arithmetic.
"""
import argparse
import asyncio
import base64
import datetime as dt
import logging
from pathlib import Path

import database_manager as dbm
from analysis import aggregate
from analysis.run_analysis import DEFAULT_OUT_DIR, _load_index_build_cost
from score_gate_outputs import GATE_THRESHOLD, compute_agreement_rate

logger = logging.getLogger(__name__)


def embed_png(path: Path) -> str:
    """Inline one PNG as a data URI. Raises if it is missing, rather than
    emitting a reference that would silently render as nothing."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"figure not found: {path}")
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _md_table_to_html(markdown: str) -> str:
    """Convert one pipe-table to HTML. Only the table subset is supported,
    which is all the aggregation module emits."""
    rows = [line for line in markdown.strip().splitlines() if line.startswith("|")]
    if len(rows) < 2:
        return ""

    def cells(line: str) -> list[str]:
        return [c.strip() for c in line.strip().strip("|").split("|")]

    head = "".join(f"<th>{c}</th>" for c in cells(rows[0]))
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in cells(r)) + "</tr>"
        for r in rows[2:]
    )
    return f"<div class='scroll'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def build_html(context: dict) -> str:
    """The page body. No doctype, html, head or body tags: the artifact host
    supplies that skeleton and wraps this content at publish time."""
    tables = "\n".join(
        f"<section><h2>{title}</h2>{_md_table_to_html(md)}</section>"
        for title, md in context["tables"].items()
    )
    figures = "\n".join(
        f"<figure><img src='{uri}' alt='{caption}'><figcaption>{caption}</figcaption></figure>"
        for caption, uri in context["figures"]
    )

    return f"""<title>RAG Retrieval Benchmark</title>
<style>
  :root {{
    --bg: #faf9f7; --surface: #ffffff; --ink: #1a1f2b; --muted: #5b6472;
    --line: #dcdfe5; --accent: #1d3557; --warn-bg: #fff8e6; --warn-line: #d9a441;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #14171d; --surface: #1c2029; --ink: #e8eaed; --muted: #9aa4b2;
      --line: #2e3440; --accent: #8ab4f8; --warn-bg: #2a2418; --warn-line: #d9a441;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #14171d; --surface: #1c2029; --ink: #e8eaed; --muted: #9aa4b2;
    --line: #2e3440; --accent: #8ab4f8; --warn-bg: #2a2418; --warn-line: #d9a441;
  }}
  body {{ background: var(--bg); color: var(--ink);
         font: 16px/1.6 Garamond, "EB Garamond", Georgia, serif;
         margin: 0; padding: 2.5rem 1.25rem; }}
  main {{ max-width: 60rem; margin: 0 auto; }}
  h1, h2, h3, th, figcaption {{ font-family: Calibri, "Segoe UI", system-ui, sans-serif; }}
  h1 {{ font-size: 2rem; margin: 0 0 .25rem; color: var(--accent); }}
  h2 {{ font-size: 1.25rem; margin: 2.5rem 0 .75rem; border-bottom: 1px solid var(--line);
        padding-bottom: .35rem; }}
  .sub {{ color: var(--muted); margin: 0 0 2rem; }}
  .caveat {{ background: var(--warn-bg); border-left: 4px solid var(--warn-line);
             padding: 1rem 1.25rem; border-radius: 4px; margin: 2rem 0; }}
  .caveat h2 {{ margin-top: 0; border: 0; }}
  .scroll {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  table {{ border-collapse: collapse; width: 100%; font-family: Calibri, system-ui, sans-serif;
           font-size: .9rem; background: var(--surface); }}
  th, td {{ border: 1px solid var(--line); padding: .45rem .7rem; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ background: var(--bg); }}
  figure {{ margin: 2rem 0; }}
  img {{ max-width: 100%; border: 1px solid var(--line); border-radius: 4px;
         background: var(--surface); }}
  figcaption {{ color: var(--muted); font-size: .85rem; margin-top: .5rem; }}
  .stat {{ font-size: 1.5rem; color: var(--accent); font-family: Calibri, system-ui, sans-serif; }}
</style>

<main>
  <h1>Retrieval Paradigms in Financial RAG</h1>
  <p class="sub">Semantic, statistical and structural retrieval over SEC 10-K filings.
     {context['n_cells']} scored cells, generated {context['generated']}.</p>

  <div class="caveat">
    <h2>How to read these numbers</h2>
    <p>The judge-score column is <strong>not externally validated</strong>. The
    agent supplied both the Judge's calibration exemplars and the validation
    gate's reference scores, so the figure below is
    <strong>cross-model concordance</strong> between two agent-mediated
    judgements, not agreement with an external human standard.</p>
    <p class="stat">{context['concordance']:.1f}% concordance</p>
    <p>{context['concordance_agreements']} of {context['concordance_n']} gate rows
    agreed within one point, against a threshold of
    &gt; {context['gate_threshold']:.0f}%. Measured on 60 samples, which
    Guardrails 4b calls a pragmatic check rather than strong proof.</p>
    <p>Every cell is a single run at temperature 0. There is no repeated
    sampling, so no confidence interval is available and small differences
    between pipelines should not be read as significant. Exact match is
    undefined for the implicit quadrants and is excluded from their means
    rather than counted as a failure.</p>
  </div>

  {tables}

  <section><h2>Figures</h2>{figures}</section>
</main>"""


async def main(db_path: str = "benchmark.db", out_path: Path | None = None) -> Path:
    out_dir = DEFAULT_OUT_DIR
    out_path = out_path or (out_dir / "benchmark_report.html")

    rows = await aggregate.load_rows(db_path, "PQ")
    if not rows:
        raise ValueError(f"no PQ results in {db_path!r} -- run the benchmark first")
    gate = compute_agreement_rate(await dbm.get_results(db_path, "JEQ"))

    by_pipeline = aggregate.summarise(rows, by=("pipeline",))
    by_pipeline_k = aggregate.summarise(rows, by=("pipeline", "k_value"))
    by_quadrant = aggregate.summarise(rows, by=("pipeline", "quadrant"))

    context = {
        "n_cells": len(rows),
        "concordance": gate["agreement_rate"],
        "concordance_n": gate["n"],
        "concordance_agreements": gate["agreements"],
        "gate_threshold": GATE_THRESHOLD,
        "generated": dt.date.today().isoformat(),
        "tables": {
            "Table 1.1  Tri-pillar summary by pipeline": aggregate.to_markdown_table(
                by_pipeline, columns=("pipeline", "n", "mean_judge_score", "mean_token_f1",
                                      "mean_exact_match", "mean_precision_at_k",
                                      "mean_recall_at_k", "mean_evidence_hit",
                                      "mean_citation_match", "mean_latency_sec")),
            "Table 1.2  By pipeline and retrieval depth": aggregate.to_markdown_table(
                by_pipeline_k, columns=("pipeline", "k_value", "n", "mean_judge_score",
                                        "mean_recall_at_k", "mean_precision_at_k",
                                        "mean_citation_match")),
            "Table 1.3  By pipeline and question quadrant": aggregate.to_markdown_table(
                by_quadrant, columns=("pipeline", "quadrant", "n", "mean_judge_score",
                                      "mean_token_f1", "mean_exact_match",
                                      "mean_recall_at_k", "mean_evidence_hit")),
            "Table 1.4  P3 index-build cost (one-off, per filing)": _load_index_build_cost(),
        },
        "figures": [
            ("Figure 1.1  Answer quality by pipeline and retrieval depth",
             embed_png(out_dir / "fig_1_1_judge_by_pipeline_k.png")),
            ("Figure 1.2  Answer quality by pipeline and question quadrant",
             embed_png(out_dir / "fig_1_2_quadrant_heatmap.png")),
            ("Figure 1.3  Retrieval recall against depth",
             embed_png(out_dir / "fig_1_3_recall_vs_k.png")),
        ],
    }

    out_path.write_text(build_html(context))
    logger.info("wrote %s (%.1f KB)", out_path, out_path.stat().st_size / 1024)
    return out_path


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default="benchmark.db")
    return parser.parse_args(argv)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print(asyncio.run(main(db_path=_parse_args().db_path)))
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pytest tests/test_build_report.py -q && .venv/bin/python -m pytest -q
```

Expected: 9 passed in the new file; full suite green with the count grown by 9.

- [ ] **Step 6: Build the report and check its size**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m analysis.build_report --db-path benchmark.db
ls -lh ../resources/artifacts/analysis/benchmark_report.html
```

Expected: a file well under the 16 MB publish ceiling. Three 150-dpi PNGs base64-encode to roughly 1.3 times their byte size, so expect a few hundred KB. If it exceeds 16 MB, drop `figure.dpi` in `figures.py` from 150 to 110 and rebuild.

- [ ] **Step 7: Read the rendered page before publishing**

Open the HTML file and read it end to end. Confirm the numbers in the tables match what Task 11's `results_summary.md` reported, that the caveat block is present and reads honestly, and that no table has been mangled by the Markdown-to-HTML conversion.

- [ ] **Step 8: Publish as an Artifact**

Publish with the `Artifact` tool:

- `file_path`: `resources/artifacts/analysis/benchmark_report.html`
- `favicon`: `📊`
- `description`: one sentence naming the three pipelines and the cell count.

The `<title>` in the file supplies the name, so do not pass a `title` parameter. Keep this exact `file_path` for any later republish, so the URL stays stable.

Hand the user the returned URL.

- [ ] **Step 9: Commit and log**

```bash
cd /Users/ojaswi/Projects/rag-techniques
git add project/analysis/build_report.py project/tests/test_build_report.py resources/artifacts/analysis/benchmark_report.html docs/superpowers/plans/2026-09-09-autonomous-project-completion.md
git commit -m "feat(analysis): build and publish the self-contained HTML benchmark report"
```

Then run `/monitor:record` for this task, and confirm the plan file's checkboxes are all ticked.
