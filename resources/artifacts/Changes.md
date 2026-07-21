# Changes

Simple running list of changes made to the project after the proposal was submitted.

- 2026-07-21: Swapped Critic/Judge model from `Qwen3-32b` to `qwen/qwen3.6-27b`.
  Reason: Groq's free tier no longer hosts `qwen/qwen3-32b` (confirmed via live
  `models.list()` call and a 404 on all Critic/Judge routes). `qwen/qwen3.6-27b`
  is the closest available Qwen model on the account. Updated everywhere:
  `project/config.py`, `CLAUDE.md`, `resources/specs/Guardrails.md`,
  `resources/specs/Architecture.md`, `resources/specs/Budget.md`,
  `resources/specs/Project Idea.md`, `resources/specs/Phase Plan.md`,
  `openwiki/benchmark-design.md`, `openwiki/system-architecture.md`,
  `temp/directory-structure.md`. Role-separation invariants unaffected
  (Critic/Judge still a different model family from Generator/Answerer).

- 2026-07-21: `ingest/parse_filing.py`'s `LlamaParse(...)` call used the
  `parsing_instruction` parameter (as drafted in the Phase 2 plan), which
  triggers a deprecation warning in the installed `llama-parse==0.6.94`.
  Swapped to `system_prompt` (the parameter's replacement) — same effect,
  warning gone. Verified via the mocked unit tests and a live LlamaParse
  smoke test.

  Bigger, unresolved finding surfaced during that live smoke test: the
  entire `llama-parse` PyPI package is itself deprecated in favour of a new
  unified SDK (`llama-cloud`, currently v2.11.0). Its own printed
  deprecation notice says it will be "maintained until May 1, 2026" —
  already past as of today (2026-07-21). The package is still installable
  and fully functional (confirmed live), so Task 3 was not blocked on this,
  but a full migration to `llama-cloud`'s API is a non-trivial rewrite
  (different client shape, not a drop-in replacement) and was judged out of
  scope for a mid-task fix. Flagged for a human decision in
  `temp/phase2-human-actions.md` rather than silently deferred or silently
  migrated.
