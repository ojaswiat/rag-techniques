# Phase 5/7 Loop Executor: Retry-Queue Design (for future implementation)

Not yet built. `loop_executor.py` and the P1/P2/P3 pipeline modules don't
exist yet (Phase 5, per `Phase Plan.md`). This document captures a design
for that future orchestrator's failure handling, proposed during a Phase 4
doubt-resolution discussion but scoped to the wrong phase (see
`resources/artifacts/Changes.md` / monitor log for that correction). Filed
here so it isn't lost before Phase 5 starts.

## Problem it solves

Running 140 queries x 3 pipelines (P1/P2/P3) x 3 K-values = up to 900
`results` rows. A naive loop that fails hard on the first pipeline error
would waste all prior progress and free-tier Groq/embedding spend. Need
per-attempt failure isolation without breaking the "same query set across
all three pipelines" invariant that the comparison depends on.

## Design

1. **Queue-based execution.** Start with all outstanding `(query, pipeline)`
   pairs in a queue -- not a fixed 280; the real count follows from the
   spec's 140 queries x 3 pipelines (x however many K-values run in the same
   pass). Confirm the exact target count against `Architecture.md` §3.2 /
   `Project Idea.md` before implementing -- "280" as originally suggested
   didn't match any spec number and needs verifying, not assuming.
2. **One "try" = one query asked of P1, P2, and P3.** All three pipelines
   must answer the same query before the queue advances, preserving the
   anti-confound, same-query-across-pipelines design already validated for
   Phase 4's dataset (see `docs/superpowers/notes/2026-07-28-phase4-design-discussion.md`
   §2).
3. **Per-pipeline failure isolation.** If a query fails at any one pipeline
   (P1, P2, or P3), do not abort the whole try: log the failure (which
   query, which pipeline, why), requeue that `(query, pipeline)` pair to the
   back of the queue, and continue with the next query for the other
   pipelines.
4. **Retry-to-back-of-queue, not immediate retry.** A failed pair goes to
   the back, giving transient issues (rate limits, momentary API errors)
   time to clear before the retry, rather than hammering the same failure
   repeatedly.
5. **Cap and replace on repeated failure.** If a specific query keeps
   failing across multiple retries, discard it and replace it with another
   query from the same quadrant, so the 25/5/5-per-quadrant strata stays
   intact. Record: which query failed, why, which pipeline, and (if
   replaced) what query it was replaced with -- this is the audit trail the
   dissertation's methodology section needs.
6. **Resumability stays row-level**, per the existing
   `results.UNIQUE(source_set, query_id, pipeline, k_value)` constraint
   (`Architecture.md` §3.2) -- a crash never re-spends quota on an
   already-recorded result.

## Open question before implementation

Confirm the exact total query x pipeline (x K-value) count against the
spec at Phase 5 kickoff -- do not assume 280 or any other number without
checking `Project Idea.md` / `Architecture.md` first.
