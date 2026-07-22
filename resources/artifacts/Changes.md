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
