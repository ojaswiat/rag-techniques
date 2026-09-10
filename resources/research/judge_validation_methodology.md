# Judge Validation and Execution Methodology

Written 2026-09-10, covering Phase 6b. This is the paper-facing record of the methodological
decisions taken while calibrating the LLM Judge and clearing its validation gate. Numbered
deviations referenced here are recorded in full in `deviations.md`.

Everything below is intended to be usable in the methodology and limitations chapters.

---

## 1. Retrieval depth reduced to K ∈ {2, 3, 5}

The sweep was originally K ∈ {3, 5, 10}. It is now K ∈ {2, 3, 5}, keeping the matrix at
100 questions × 3 pipelines × 3 depths = 900 runs. See deviation 28.

The corpus makes small K the interesting region. Nodes are chunked finely: text nodes average
42 tokens over 16,685 nodes, table nodes average 171 over 1,612, giving a corpus-weighted mean
of 53.4 tokens. A K = 5 retrieval therefore supplies roughly 267 tokens of context. Testing
K = 10 would mostly have measured how well each pipeline tolerates padding, whereas K = 2
probes the precision the finer distinctions actually turn on.

**For the paper:** report the chunk-size distribution alongside the K sweep. The two are not
independent, and a reader cannot interpret the depth results without knowing how much text a
"passage" contains in this corpus.

---

## 2. Provider migration and determinism controls

The pipeline Answerer and the Judge were moved from Groq's free tier to OpenRouter's paid tier
on the same two model families. See deviation 29.

- Answerer: `meta-llama/llama-3.3-70b-instruct`
- Judge: `qwen/qwen3.6-27b`

The families are unchanged, so the anti-self-grading invariant (Answerer ≠ Judge family) still
holds. The move was made because Groq's free tier is token-bound, which forces the 900-cell
matrix into daily slices spread over weeks, whereas OpenRouter is request-bound and completes
it in a single pass.

**The determinism control is the part that belongs in the methodology.** OpenRouter routes
requests across multiple hosts whose quantisation differs, fp8 against bf16. Left unpinned,
the 900 cells would have been answered by numerically different backends, silently. Each stage
is therefore pinned to a single upstream with `allow_fallbacks: false`, so a host outage fails
loudly and resumes later rather than switching backend mid-run.

**For the paper:** state the pinning explicitly. "Temperature 0, one run per cell" is not a
reproducibility claim on a load-balancing gateway unless the backend is also fixed.

---

## 3. Judge calibration set

The Judge learns what each score means from 20 exemplar rows, five per question quadrant, and
sees only the five matching the row it is grading. See deviation 30.

Design decisions:

- **A 10 good / 10 bad split**, with both polarities present in **every quadrant**. Overall
  balance is insufficient because the Judge never sees the full set; a quadrant with no low
  anchor would be graded against a ceiling-only scale.
- **Injected failures match each quadrant's characteristic weakness**: a neighbouring value for
  direct text, a half-answer for implicit text, an adjacent column for direct table, and a sign
  or scale error for implicit table. Each was written against the real filing text so the wrong
  answer is one a retrieval system would plausibly produce, not an artificial error.
- **Reasoning is specific to the answer**, naming the defect and where it arose, because a
  generic "this is wrong" calibrates nothing.

---

## 4. Rubric reconciled with the exemplars

The rubric shipped with the Judge originally stated that a 10 "fully matches the ground-truth
answer and cites only valid sources". Two problems, both fixed. See deviation 31.

- **Citation grading was removed.** Guardrails §4b assigns citation checking to deterministic
  code, and `citation_audit()` already computes it into `results.citation_match`. Asking the
  Judge for it duplicated a deterministic check and invited a model's guess to override it.
  The "valid source node ids" line was also removed from both the exemplar and target prompts,
  so the Judge is never shown data it is instructed not to use.
- **The 9-versus-10 band was generalised.** An earlier revision described it as a
  supportability criterion, but real pipeline answers carry inline `[[node:<id>]]` markers that
  no exemplar has, so real answers would have evaded a deduction the exemplars were docked for.
  Inspecting the six exemplars scoring 9 showed they dock for three different reasons:
  verifiability, framing, and synthesis. The band is now described generically as correct but
  slightly short on completeness, precision, or framing, which matches all three.

**For the paper:** this is a worked example of a real hazard in LLM-as-judge designs. A rubric
and its few-shot exemplars are two separate artefacts that can drift apart, and the drift is
invisible at runtime because the model simply produces plausible numbers either way.

---

## 5. The blinding protocol for gate scoring

This is the most methodologically significant decision in Phase 6b and should be described in
full.

The gate compares the Judge's scores against an independent set of reference scores over the
same 60 outputs. On this project the reference scores were written by an agent rather than a
researcher, so **independence is the only property the figure retains**, and it was enforced
structurally rather than by instruction.

The scorer receives exactly four fields: `quadrant`, `query_text`, `ground_truth_answer`,
`pipeline_output`. Three exclusions matter:

1. **`judge_score` is excluded by whitelist, not blocklist.** A whitelist keeps working when
   the underlying query later gains columns; a blocklist silently begins leaking them.
2. **Citation columns are excluded** so the scorer sees exactly the evidence the Judge sees.
   Otherwise disagreements would partly measure an information gap rather than the Judge's
   quality.
3. **Pipeline identity is withheld, including indirectly.** This required two rounds. Removing
   the `pipeline` field was insufficient because `result_id` encodes it
   (`R_JEQ_QT1_JEQ_001_P1_vector_K5`), so rows are addressed by opaque tokens. Positional
   tokens were then also insufficient: assigned over `ORDER BY result_id` they produced a
   perfect P1, P2, P3 cycle, so `token_index mod 3` recovered the pipeline exactly. Tokens are
   now assigned over a fixed-seed shuffle, reproducible without being persisted.

**Why this matters for the results, not just the gate.** A scorer that knows an answer came
from P3, the pipeline this dissertation predicts will perform worst, can shade its score toward
the expected outcome. That would contaminate the very comparison the project exists to produce.

**For the paper:** report the blinding as a designed control, and report that the ordering leak
was found and closed. A reviewer who spots that ordering can encode identity will ask.

---

## 6. Gate result

Threshold: concordance strictly above 80%. Scores are stored on a 1 to 5 scale and rescaled to
0-100 by multiplying by 20; the tolerance is 10 points, so adjacent bands never agree and the
rule is **exact band match**.

**Result: 86.7%, 52 of 60 rows. The gate passed.**

### The scale, and why the tolerance rule is load-bearing

Scoring originally ran on a 1 to 10 scale with agreement counted within one native point. That
scale was never anchored across its range: the 20 calibration exemplars rescaled onto only five
distinct values (10, 9, 5, 4 and 2), so the Judge had never seen an exemplar scored 1, 3, 6, 7
or 8. Half the scale was undemonstrated, both score distributions were bimodal, and
disagreements clustered on exactly that gap. Collapsing to five bands, each backed by at least
one exemplar, removed the artefact. See `resources/research/deviations.md` entry 33.

Tightening the tolerance at the same time was deliberate, and the numbers show why it mattered.
Carrying the old plus-or-minus-one-band rule onto a five-band scale would have widened the
acceptance window from 30% of the scale to 60%. Against the final data:

| Agreement rule | Window | Concordance |
|---|---|---|
| Exact band match (used) | 20% of scale | **86.7%**, 52/60 |
| Plus or minus one band (rejected) | 60% of scale | 100.0%, 60/60 |

A rule that returns 60 out of 60 is not measuring the Judge. Reporting the looser figure would
have been an artefact of band width, not evidence. The exact-match window is also slightly
stricter than the retired 1-10 gate's, so the ">80%" threshold did not quietly become easier.

### Disagreement structure

**All eight disagreements are exactly one band.** There is no row where the two graders differ
by two bands or more, on either the strong or the weak end. Their aggregate agreement is closer
still: per-pipeline mean scores differ by at most 0.05.

- Five rows: the Judge is one band more generous.
- Three rows: the reference is one band more generous, and these are the same question
  (`QT4_JEQ_001`) disagreeing across all three pipelines, so that cluster is one ambiguous item
  rather than scattered noise. It is a derived percentage differing from the ground truth by
  0.05 percentage points; the rubric's 0.1-point rounding allowance puts it at 5 while the Judge
  read it as a precision shortfall at 4.
- `QT1_JEQ_001` accounts for three more, again the same question across all three pipelines.

Two of the eight disagreements are therefore really two ambiguous questions, not eight
independent grader failures.

Nine rows are flat refusals of the form "the sources do not contain the answer" where a ground
truth exists. Both graders treat an unsupported refusal as a failure rather than as mid-range
partial credit.

---

## 7. Gate outputs at K = 5, all three pipelines

Scores are on the 1 to 5 scale.

| Pipeline | mean judge score | mean reference score | mean recall@5 | citation_match |
|---|---|---|---|---|
| P1_vector | 4.30 | 4.30 | 0.62 | 15/20 |
| P2_bm25 | 4.10 | 4.05 | 0.68 | 16/20 |
| P3_structural | 3.70 | 3.65 | 0.45 | 9/20 |

Three observations worth carrying into the results chapter:

- **P3 degrades as predicted**, on both answer quality and retrieval, and its citation
  behaviour is markedly worse (9/20 against 15 and 16). This is consistent with the expectation
  that hierarchical summarisation loses exact detail.
- **The metrics disagree in ordering between P1 and P2.** BM25 retrieves better (0.68 against
  0.62) while the vector pipeline answers better (4.30 against 4.10). That tension is precisely
  the semantic-versus-statistical contrast the project is built to expose, and it should not be
  flattened into a single ranking.
- **The Judge and the reference scorer rank the three pipelines identically**, and their means
  differ by at most 0.05. Whatever disagreement exists at row level does not propagate to the
  comparison the dissertation actually reports.

These are 20 questions at one depth and are indicative only. The 900-run matrix is the evidence.

---

## 8. Limitations to state explicitly

1. **The judge-score column is not externally validated.** The agent supplied both the Judge's
   calibration exemplars and the gate's reference scores, so the figure is cross-model
   concordance between two agent-mediated judgements, not agreement with a human standard.
   It must be reported as concordance throughout and never as a human agreement rate. The 60
   gate rows persist in the database, so hand-scoring them later would upgrade the claim
   without repeating any paid work.
2. **Both score distributions are strongly bimodal.** The Judge produced 40 tens and 11 ones
   with only 9 rows in between; the reference scorer produced 37 tens and 8 ones. Despite a
   calibration set teaching a five-point gradient, both graders behave close to binary. This is
   defensible for factual 10-K questions, which usually are simply right or wrong, but it means
   the reported means function closer to **pass rates than to graded quality**, and must be
   described that way.
3. **60 samples.** Guardrails §4b already frames the gate as a pragmatic check rather than
   strong proof, and that framing stands.
4. **One run per cell at temperature 0.** No repeated sampling, so no confidence intervals are
   available and small differences between pipelines should not be read as significant.
5. **Corpus is 13 filings, not the 18 originally planned** (deviation 20), fixed at what the
   P3 tree index had actually been built for.

---

## 9. Reproducibility hazard found in the harness

A concurrency defect in the shared rate limiter is worth a line in the limitations or the
implementation chapter, because it affected measured throughput rather than results.

The OpenRouter and NIM clients held their pacing lock across the network call itself. Two
consequences: the concurrency semaphore had no effect, so requests were fully serialised; and
one slow request blocked every other waiter. Combined with a missing reasoning cap on the
Judge, this stalled the first full gate run for fifteen minutes after a single call, with no
error raised. See deviation 32.

Request starts are now paced at the rate ceiling while calls proceed concurrently under a
timeout. The fix changed run time, not any recorded score.

---

## 10. Cost model, measured rather than estimated

Judge prompt size was measured from the rendered prompt with `tiktoken`: an 895-token
quadrant prefix plus a 151-token target message, 1,046 tokens per call. Answerer figures come
from the recorded token columns.

Projected total for the remaining 957 answerer and 960 judge calls:

| Assumption | Projected |
|---|---|
| Measured at rehearsal | $0.52 |
| Corpus-weighted | $0.55 |
| Pessimistic, all-table K = 5 | $0.69 |

The whole benchmark therefore costs well under a pound, against a design that originally
targeted strict $0 free-tier operation. Worth stating: the $0 constraint was relaxed
deliberately, and the sum involved is trivial next to the weeks of wall-clock time it buys back.
