# Judge Scoring Criteria (1 to 5)

Binding rubric for anyone, human or agent, assigning a **reference score** to a
pipeline answer in the Judge validation gate. It expands the compressed rubric
held in `project/judge/async_judge.py::_RUBRIC` into a per-band guide, without
changing what that rubric means. If the two ever disagree, `_RUBRIC` and the 20
calibration exemplars in `golden_queries` are authoritative and this file is the
document that must be corrected.

The project previously scored on a 1 to 10 scale. It was collapsed to 1 to 5; see
`resources/research/deviations.md` entry 33 for the reasoning.

---

## 1. How the scale is anchored

The Judge is few-shot calibrated on 20 exemplars drawn from `golden_queries`,
five per quadrant, ten labelled good and ten labelled bad. Their stored labels
are on a 0 to 100 scale and are mapped onto 1 to 5 by
`async_judge._rescale_to_1_5()` using explicit band floors, not arithmetic
rounding:

| Band | Native 0 to 100 range | Exemplars landing here |
|---|---|---|
| 5 | 90 to 100 | 9 |
| 4 | 75 to 89 | 1 |
| 3 | 50 to 74 | 2 |
| 2 | 25 to 49 | 3 |
| 1 | 0 to 24 | 5 |

**Every band carries at least one exemplar.** This was not true on the old 1 to
10 scale, where the rescaled exemplars only ever took the values 10, 9, 5, 4 and
2, leaving five bands the Judge had never seen demonstrated. Those empty bands
were the main source of reference-versus-Judge disagreement, because a scorer
using an unanchored band could not be matched by a Judge that never emitted it.

Band floors are used rather than `round(score / 20)` because Python's `round()`
is banker's rounding, which sends the two "half the question answered" exemplars
at 50 into band 2, where they would read as wrong-value answers rather than the
partially correct answers they are.

**Agreement is exact band match.** Scores are rescaled to 0 to 100 by
multiplying by 20, and the tolerance is 10 points, so adjacent bands never
agree. The old plus-or-minus-one-band rule was not carried over: on five bands it
would have widened the acceptance window from 30% of the scale to 60%, inflating
the Concordance Rate without the Judge improving. The gate threshold remains
strictly above 80%.

---

## 2. The six factors, applied in this order

1. **Correctness.** Is the value or fact right?
2. **Selection.** Right row, column, cell, fiscal year, ordinal, scope?
3. **Completeness.** Is every part of a multi-part question answered?
4. **Precision.** Exact digits, wording, units, scale and sign convention?
5. **Grounding.** Is anything asserted that the ground truth does not support?
6. **Directness.** Does it answer the question asked, or a neighbouring one?

Correctness and selection dominate. A wrong value cannot be rescued by good
coverage, and complete coverage of the wrong figure is still wrong.

---

## 3. The bands

### Score 5, correct and complete
- Value matches the ground truth exactly, digit for digit.
- Every part of a multi-part question is answered.
- Conventions preserved: parentheses for negatives, "up to", thousands separators.
- Nothing material is dropped and nothing unsupported is added.
- Minor differences of presentation or phrasing do not cost the band.
- A derived figure within 0.1 percentage points of the ground truth stays here;
  the miss is rounding, not extraction.
- Exemplar precedents: exact date returned for a direct-text lookup; correct
  120-day window with its fiscal-year clause kept; three sensitivity rows summed
  and reported in the table's own parenthesised convention.

### Score 4, correct value, real shortfall
- The value is right, but one substantive element is dropped or blurred.
- Or the answer is right and carries unsupported extra material around it.
- Larger than a presentational difference, still with no factual error.
- Typical case: both halves answered but a qualifying carve-out compressed away.
- Exemplar precedent: incorporation by reference and the furnished-not-filed
  distinction both carried, with the framing loose enough to cost a band.

### Score 3, partially correct
- Exactly one half of a two-part question is right, the other half absent.
- Or the right row and the right endpoints, with a scale error in the result.
- Everything stated is true; the failure is coverage, not accuracy.
- Exemplar precedents: a precisely dated effectiveness conclusion that never
  reaches the inherent-limitations half of the question; the correct S and P 500
  row and endpoints reported at the wrong scale.

### Score 2, right area, wrong value, partial credit remains
- Retrieval landed correctly and some genuinely correct component survives.
- The asked-for value is wrong, but it is not the whole of what was asked.
- Typical cases: right table, row and direction with the figure read one column
  across; right location and right "where" with the wrong caption quoted; an
  over-broad scope that still contains the correct item inside a wider set.
- Exemplar precedents: currency-drag row correct with the figure taken from the
  2023 comparative column; Proxy Statement destination right with one caption
  accurate and the others silently dropped.

### Score 1, wrong, or the whole task failed
- Wrong, fabricated, or unsupported by the ground truth.
- Empty, a refusal, or a statement that the information cannot be found.
- Answers a different question entirely.
- Or the single thing the question asked for is wrong, and that thing was the
  entire task: the wrong ordinal when ordering was the question, a count that
  overruns or undercounts, a derived figure computed on the wrong base, the
  wrong fiscal year with nothing else correct.
- Exemplar precedents: the last of three listed captions returned when the first
  was asked for; a footnote counted as an eighth facility; the leased
  international cell divided by the international subtotal instead of total
  facilities.

**Distinguishing 2 from 1.** Ask whether anything the answer got right is worth
partial credit against the question that was asked. If a genuinely correct
component survives beyond merely finding the right page, score 2. If the one
value the question turned on is wrong, score 1, however close the retrieval was.

---

## 4. Explicit non-factors

Do **not** raise or lower a score for any of these:

- `[[node:AAPL_2023_n0680]]` style citation markers embedded in the answer.
  Ignore them entirely. They are an artefact of the answerer's output format and
  the calibration exemplars do not contain them.
- Which nodes the answer cites, or how many. Citation validity is measured
  deterministically by `citation_audit()` in `project/judge/metrics.py`, per
  Guardrails section 4b. Scoring it here would duplicate that check and let a
  model's guess override a deterministic one.
- Verbosity, tone, formatting, or restating the question before answering.
- Showing intermediate arithmetic. Component figures offered as working are not
  unsupported extra material, provided the final value is correct.
- Outside knowledge of Apple, Tesla, of SEC filings, or of the wider corpus.
  Grade only against the ground-truth text supplied with the row.
- The identity of the pipeline that produced the answer. Under the blinding
  protocol the scorer is not shown it; see section 5 of
  `resources/research/judge_validation_methodology.md`.

---

## 5. Tie-breaker

Resolve a hesitant row by asking the questions in this order:

1. Is the core value correct?
   - Yes, and nothing material is missing, score 5.
   - Yes, but a substantive element is dropped or added, score 4.
2. Is half the question answered correctly and the rest absent?
   - Yes, score 3.
3. Is the area right but the value wrong?
   - Yes, and partial credit genuinely survives, score 2.
   - Yes, but the wrong value was the whole task, score 1.
4. Is anything salvageable at all?
   - No, score 1.

---

## 6. Independence rules for the gate

These are binding whenever a reference score feeds the validation gate.

- Never read `results.judge_score` before scoring. Independence is the only
  property the gate figure retains when the agent supplies both sides.
- Score from the blinded rendering produced by
  `project/gate_reference_scores.py::render_rows_for_scoring()`, which exposes
  only quadrant, query text, ground-truth answer and pipeline output.
- Score each row absolutely against its own ground truth. Never score a row by
  comparing it with another row, even where two rows share a question.
- Do not attempt to infer the pipeline from answer style, length or token order.
- Where the agent rather than the researcher supplies these scores, the gate
  figure must be reported as **cross-model concordance**, never as a human
  agreement rate.

---

## 7. Known ground-truth defects

Some ground truths were generated from a single retrieved node and inherited
that node's narrow scope, so a pipeline answer can be more complete than the
ground truth it is graded against. `QT1_JEQ_005` is the known instance: the
ground truth names only Item 12, while the Tesla filing incorporates Items 10
through 14, which is what the pipelines returned.

Score against the ground truth as written, because the Judge does the same and
the gate measures agreement between the two. Record the defect rather than
correcting for it silently.
