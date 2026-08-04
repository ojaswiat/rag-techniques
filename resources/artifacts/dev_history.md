# Development History

Archive of development-process history (bug fixes, code-review findings,
regression narratives) removed from source/test file comments and
docstrings, kept here only where relevant to the dissertation. This is a
dev-facing log, not a research narrative -- see `resources/research/` for
the research-facing equivalents.

## Format

Each entry:

1. **Issue:** what was wrong.
2. **Fix:** what changed.
3. **Dissertation relevance:** why this matters (or doesn't) for the write-up.

---

### 1. Empty filing-list argument silently meant "use all filings"

1. **Issue:** `document_ids = document_ids or _ALL_FILINGS` treated an
   explicitly empty tuple (`()`, meaning "restrict to zero filings") the
   same as `None` ("not provided"), because an empty tuple is falsy in
   Python -- both collapsed to "use all filings".
2. **Fix:** Changed to an explicit `document_ids = _ALL_FILINGS if
   document_ids is None else document_ids`, so only the true "not provided"
   case defaults to all filings.
3. **Dissertation relevance:** Directly affects corpus-scope control for
   dataset generation runs -- a silent "use everything" default when zero
   filings was intended could produce a dataset run against the wrong
   scope without any error or warning.

### 2. No duplicate-question check before acceptance

1. **Issue:** Nothing stopped two near-identical questions, generated from
   different sections/documents, from both being accepted into the final
   140-query set.
2. **Fix:** Added `database_manager.get_all_query_texts()` (pulls
   `(query_id, query_text)` across all three quadrant-fill tables) and a
   duplicate check in the acceptance path: a candidate scoring >= 0.92
   embedding similarity against any already-accepted query is rejected as
   a duplicate and the attempt retried with feedback naming the duplicate.
3. **Dissertation relevance:** Directly affects dataset quality/validity --
   duplicate questions in the evaluation set would inflate or bias
   pipeline comparison results.

### 3. Questions clustered by company by accident

1. **Issue:** Sections were processed and filled into quadrants in
   whatever order they were encountered, so one company's filings could
   dominate a quadrant just because they were processed first --
   conflating "quadrant difficulty" with "which company" in the resulting
   dataset.
2. **Fix:** Sections are now interleaved round-robin across companies
   within each content pool (table-type -> Q3/Q4, text-type -> Q1/Q2),
   instead of exhausted one document at a time.
3. **Dissertation relevance:** Directly relevant to internal validity --
   without this, an observed "pipeline X struggles on hard questions"
   result could actually just be "pipeline X struggles on Company Y's
   filings", with no way to separate the two explanations.

### 4. Silent shortfall -- no warning if the dataset came up short

1. **Issue:** If the generation run couldn't fill all 140 target
   questions, it stopped quietly with no indication of how far short it
   fell.
2. **Fix:** Added `format_underfill_summary()`, printed and durably logged
   at the end of every run, reporting per-quadrant/per-table fill counts
   against target.
3. **Dissertation relevance:** Affects whether a reported dataset size of
   "140 questions" can be trusted at face value, or whether the actual
   run silently under-delivered -- relevant to methodology reporting and
   any limitations discussion.
