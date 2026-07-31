# Doubt #11 Impact Assessment: `query_id` Naming Format

Two independent read-only subagents assessed blast radius: one over DB/code,
one over docs (excluding internal process docs — `docs/superpowers/`,
`monitor/`, `graphify-out/`, agent-tooling configs).

## Current state (fact, not fix)

**Code** (`run_dataset_generation.py:462`, single construction site):
```python
query_id = f"{generated['quadrant']}_{table}_{next_seq:04d}"
```
Produces e.g. `Q1_Direct_Text_queries_0001`, `Q3_Direct_Table_golden_queries_0007`.

**Docs already show THREE OTHER, mutually different short formats — none of
which match the code:**

| Source | Example | Shape |
|---|---|---|
| Code (actual behavior) | `Q1_Direct_Text_queries_0001` | `{full_quadrant}_{full_table}_{seq:04d}` |
| `Architecture.md` (`queries`/`results` example rows) | `Q3_017` | `{quadrant}_{3-digit-seq}` |
| `Architecture.md` (`golden_queries` example row) | `G_Q4_03` | `G_{quadrant}_{2-digit-seq}` |
| `Architecture.md` (`judge_validation` example row) | `V_Q1_02` | `V_{quadrant}_{2-digit-seq}` |
| `Project Idea.md` (JSON example) | `Q4_087` | `{quadrant}_{3-digit-seq}` |

**This is a pre-existing doc/code mismatch, independent of Doubt #11.** The
docs were never updated to match what `_accept_query()` actually produces —
this predates any naming-cleanup decision and is worth fixing regardless of
whether the ID format itself changes.

## Code blast radius (critical analysis)

**Real dependency surface is small.** Exactly one construction site and one
test that encodes it exactly:
- `run_dataset_generation.py:462` — the format string itself. Must change.
- `tests/test_run_dataset_generation.py:126,177` — one docstring comment +
  one exact-string assertion (`Q1_Direct_Text_queries_0003`). Must change.

**Everything else treats `query_id` as a fully opaque string — zero parsing
dependency found anywhere:**
- `database_manager.py` — `TEXT PRIMARY KEY` / `TEXT NOT NULL` / unique
  index, no length/format constraint, no string manipulation anywhere
  (`insert_query`, `insert_golden_query`, `insert_judge_validation`,
  `upsert_result`, `update_golden_query_labels`, `get_golden_queries`,
  `get_completed_keys()` — all pass/compare it as-is).
- `gq_label_export.py` / `gq_label_import.py` — the markdown regex captures
  `query_id` as "whatever token follows `## `", no internal structure
  assumed.
- `cross_check.py`, `async_critic.py`, `async_generator.py`,
  `section_grouper.py` — no `query_id` references at all (they work with
  `document_id`/`node_id`; `query_id` is only assembled after acceptance).
- `test_database_manager.py` (9 literals) and `test_gq_labeling.py` (8
  literals) already use ad hoc fixture strings (`Q1_001`, `Q1_GQ_001`,
  `Q1_TEST_001`, etc.) that never matched the production format to begin
  with — a rename doesn't touch these.

**No `split_and_label.py` exists** in this repo (`Architecture.md` §6
mentions it as a planned module; it was never built — dataset splitting into
the three tables happens directly inside `run_dataset_generation.py`).

## Verdict

- **Code risk: low.** One real construction site, one test to update. No
  hidden parsing logic anywhere else — every other consumer is provably
  opaque (verified by grep across the whole `dataset_generation/` and
  `database_manager.py`, not assumed).
- **Doc risk: this is actually the bigger finding.** Three specs already
  disagree with the code AND with each other on what a short `query_id`
  should look like. Deciding a real convention now would need to reconcile
  4-5 different formats, not introduce a clean first one.
- **Data risk: none.** `queries`/`golden_queries`/`judge_validation` all
  have 0 real rows (confirmed earlier this session) — no migration, no
  real IDs to reissue.

## Recommendation

Doubt #11 was correctly triaged as cosmetic/low-priority — this assessment
confirms it's genuinely low-risk to fix whenever convenient, since the code
change is contained to 2 files. But the more valuable finding here is the
**doc/code format mismatch**, which is a real, separate defect (docs
describing a system that doesn't match what the code does) independent of
whether Doubt #11's cosmetic rename ever happens. Worth deciding a single
canonical format and fixing both the code AND reconciling all doc examples
to it in the same pass, rather than treating this as a code-only rename.
