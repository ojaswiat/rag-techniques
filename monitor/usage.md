# monitor — companion skills in this project

Probed at init from `.claude/settings.json` `enabledPlugins` and `~/.claude/plugins/cache/`.

| Skill | Status | How monitor uses it here |
|---|---|---|
| **ui-ux-pro-max** | PRESENT | Designs the report and Logs template plus palette. This project already has a house visual identity in `resources/assets/design/palette.md` ("Oxford Ink") and `typography.md` — pull report colours and type from those rather than a generic palette, so monitor pages match the dissertation deliverables. |
| **superpowers** | PRESENT | `verification-before-completion` gates reports on real build/test output. This repo has **no build or test command yet** (see below), so until Phase 1 lands there is nothing to verify — reports must be marked **unverified** rather than implying a green run. |
| **graphify** | PRESENT | Orientation only: `graphify query/path/explain` against `graphify-out/graph.json` to find related material before a change. Never use it for Files Touched — it has no diff capability; that always comes from `git diff --name-only` or explicit `--files`. |
| **openwiki** | PRESENT | Doc sync after commits. `openwiki/` is initialised (quickstart + 3 pages, last run at `8bc8ba7`). After a commit that changes design or structure, run `/openwiki:wiki update` and note it in the report's Follow-ups. |
| **find-skills** | PRESENT | Improves skill discovery when a task needs capability this table does not cover. |
| **copywriting** | ABSENT | Report prose is written plainly. Optional; no high-fit gap here, since the project already mandates a house style (British English, no em dashes, simple punctuation) in `CLAUDE.md` that report prose should follow anyway. |

Also installed but outside monitor's companion table: **caveman** (output compression). If caveman mode is active, monitor's log summaries and report prose stay normal — the caveman rule itself scopes code, commits, and PRs to normal writing, and reports are deliverables.

## Project-specific notes

- **No build or test command was detected.** `profile.json` `commands` is empty, which is correct: the repository is currently specs and documents only, with an empty `src/`. The Tests KPI has nothing to report until Phase 1 of `resources/specs/Phase Plan.md` stands up `requirements.txt` and `tests/`.
- **Report only on code changes.** Most activity in this repo right now is document and spec work. Per the monitor skill, those get logged, not reported.
- Re-run `/monitor:update` after Phase 1 so the detected build/test commands land in the profile.
