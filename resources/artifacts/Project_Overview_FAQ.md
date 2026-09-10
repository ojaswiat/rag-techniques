# Project Overview and FAQ

*A plain-English guide for explaining this dissertation to my supervisor.*

---

## What is this project about?

- We are comparing three ways of doing RAG (Retrieval-Augmented Generation).
- RAG means: find relevant text, then let an AI answer using that text.
- We test the three ways on SEC 10-K filings (US company annual financial reports).
- These filings are hard: long, mix of prose and dense tables.

## Why SEC 10-K filings specifically?

- They mix two very different content types: narrative text and financial tables.
- This lets us see where each retrieval method wins or fails.
- Tables are known to break many RAG systems, so they are a good stress test.

## What is the core research question?

- Which retrieval method works best: by meaning, by exact words, or by document structure?
- Where does each method break down, and why?
- The sharpest comparison is meaning vs exact words. Structure is a third method added for contrast.

## What are the three pipelines?

**P1 — Vector RAG (retrieval by meaning)**
- Turns text into number vectors (embeddings) and finds similar meaning.
- Uses a small local embedding model, plus a re-ranker to sharpen results.
- Good at understanding paraphrased or implied questions.

**P2 — Keyword RAG (retrieval by exact words)**
- Classic search: matches exact words and their frequency (BM25 algorithm).
- No AI involved in retrieval itself, fully deterministic.
- Good at pinpoint fact lookups, weak at paraphrased questions.

**P3 — Structural RAG (retrieval by document structure)**
- Builds a summary tree of the document first (like a table of contents with AI summaries).
- Retrieval walks down the tree from general summary to specific detail.
- Expected to struggle with tables, since summarising often drops exact numbers.

## How do the three pipelines differ architecturally?

| | P1 Vector | P2 Keyword | P3 Structural |
|---|---|---|---|
| Basis | Meaning (embeddings) | Exact words | Summary tree |
| Needs AI to build index? | No | No | Yes, one-time |
| Deterministic? | Mostly | Fully | Less so |
| Best at | Implied questions | Exact facts | Broad narrative |
| Expected weak point | Rare/unusual wording | Meaning-based questions | Table detail |

## Why include a weaker method like P3 on purpose?

- It shows the boundaries of hierarchical summarisation, not just the strengths.
- A dissertation is stronger when it explains failure, not only success.

## How do we test them fairly?

- Every pipeline gets the exact same 100 test questions.
- Each pipeline runs at three retrieval depths, K = 2, 3, 5 (how many chunks it retrieves).
- Pipelines never see the correct answer, only the question and their own retrieved text.
- Total: 3 pipelines times 3 depths times 100 questions equals 900 test runs.

## Where do the test questions come from?

- 140 questions total, split into three separate groups that never overlap.
- 100 questions test the pipelines.
- 20 questions teach the AI judge what a good answer looks like.
- 20 questions check that the AI judge grades fairly, compared to a human.
- Keeping these groups separate avoids cheating or bias in the results.

## What are the four question types?

- Direct text: a fact stated plainly in a paragraph.
- Implicit text: needs joining ideas across different parts of the text.
- Direct table: pulling one exact number from a table.
- Implicit table: needs maths or comparison across table rows.

## How are the questions generated and checked?

- One AI model writes each question and its correct answer, from the real filing text.
- A second, different AI model independently checks the answer without being told it.
- Only questions both AIs agree on are kept, the rest are discarded and redone.
- Using two different AI "families" avoids one model simply agreeing with itself.

## How do we grade the pipeline answers?

- An AI judge scores each answer from 1 to 5 against the correct answer.
- We also run automatic checks: did it retrieve the right passages, did it cite the right source.
- A human manually scores a small sample first, to confirm the AI judge is trustworthy.
- The AI judge must agree with the human over 80% of the time before it is trusted for the full test.

## Why bother validating the judge before the full run?

- Grading 900 answers by hand is not realistic in the time available.
- But an unchecked AI judge could grade unfairly and quietly ruin the whole result.
- So we prove the judge is reliable on a small batch first, before trusting it at scale.

## What is "coincidental correctness" and why does it matter?

- Sometimes a pipeline retrieves the wrong passage, but it happens to contain the right-looking number.
- The answer looks correct, but the retrieval process actually failed.
- We catch this by checking whether the cited source actually matches the true source.

## What does "cost" mean in this project?

- Everything runs on free tiers of AI services, so there is no real money cost.
- The real constraint is throughput: how many requests per minute we are allowed.
- All local computation (embeddings, keyword search) costs nothing and has no such limit.

## What stage is the project at right now?

- Document processing is done: 13 filings, over 18,000 text chunks.
- All 140 test questions are written and verified.
- All three pipelines and the AI judge are built and working.
- Next step: confirm the judge is reliable, then run the full 900-question benchmark.

## What is the expected contribution of this dissertation?

- A clear, evidence-based answer to "which RAG method suits financial documents, and why."
- A documented account of exactly where each method succeeds or fails, and by how much.
- A reusable benchmarking method others could apply to other document types.
