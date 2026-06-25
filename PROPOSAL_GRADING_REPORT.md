# Strict Grading Report: Proposal_v1.0.0.docx

**Graded against:** `docs/ProposalGuidelines.pdf` (official COMP702 CA1 brief) and `docs/ProposalTemplate.pdf` (official structure).
**Method:** full text extracted programmatically from the actual `.docx` (not from memory of what was intended), checked clause-by-clause against the guidelines' own wording.

**Important caveat before the score:** the guidelines page links to a separate **"marking guidelines"** page on Canvas (authenticated, not accessible to me) and an **"ethical guidance"** page (also Canvas-authenticated) that defines what Data/Participant Category A0 actually means. I cannot read either page. The score below is my best strict-grader estimate against the *visible* brief and template; **the Data Category A0 self-assessment in Section 0 below is unverified against the authoritative source and you should confirm it yourself before submission.**

---

## Overall estimated score: 80-84 / 100

Strong document: correctly structured, well-cited with real high-citation papers, clean Harvard referencing, professional presentation, technically coherent. It loses marks for **three objective, literal gaps against the brief's own wording** (not style opinions) and a handful of moderate softness issues. All are fixable in under an hour of editing.

| Rubric area (inferred from brief) | Estimate | Why |
|---|---|---|
| Structure & completeness | 9/10 | All required sections present, correct order, TOC included. Minor: BCS section incomplete (see Issue 1). |
| Clarity for non-specialist reader | 6/10 | Section 1 leans on unexplained jargon (RAG, BM25, "summary-tree") the brief explicitly says must be readable by "anyone with general CS background." |
| Depth/quality of literature engagement | 9/10 | 9 real, high-citation, correctly Harvard-cited papers, woven into argument rather than just listed. Best section in the document. |
| Technical design clarity (dev/implementation summary) | 7/10 | Clear *what*; missing the explicit *why these tools* and *workflow organisation* the brief asks for by name. |
| Planning & risk realism | 7/10 | Gantt is solid; risk table omits the literal example risk category the brief names ("hardware failure"). |
| BCS criteria coverage | 6/10 | 5 of 6 official outcomes addressed; one is missing entirely (see Issue 1). |
| Referencing mechanics | 10/10 | Every in-text citation has a matching reference and vice versa; no orphans; correct Harvard format throughout. |
| Presentation/polish | 10/10 | Native Word diagrams/tables, consistent palette, no em dashes, British English, clean typography. |

---

## Issue 1 (CRITICAL, ~4-6 pts): BCS Project Criteria omits one of the six required outcomes

`docs/ProposalGuidelines.pdf` states verbatim: *"They require honours year projects to demonstrate the following six outcomes"* and lists six bullets. Section 8 of the proposal currently maps only **five**:

1. Systematic understanding -> addressed
2. Comprehensive understanding of techniques -> addressed
3. Originality in application of knowledge -> addressed
4. Deal with complex issues / sound judgement -> addressed (partially; see Issue 4)
5. Self-direction -> addressed
6. **"Critical self-evaluation of the process" -> MISSING. Not mentioned anywhere in the document.**

A marker checking this section against the six bullet points in the official brief will find one entirely unaddressed. This is the single most mechanical, easy-to-lose mark in the document.

**Fix:** add a sixth bullet to Section 8, e.g.:
> "Critical self-evaluation: the Limitations framing already built into the methodology (a single temperature-0 run per cell, an ~80% judge-validation pass on only 60 samples) is treated explicitly as a pragmatic constraint rather than a strong statistical proof, and the dissertation write-up will revisit this self-assessment against the actual results obtained."

---

## Issue 2 (CRITICAL, ~2-3 pts): Risks table omits the brief's own named example risk

`docs/ProposalGuidelines.pdf`: *"Common risks for all projects include hardware failure, software failure, running out of time, and programming problems."* and explicitly flags backup loss as a textbook low-likelihood/high-impact example.

The current Table 11.01 has six rows (Groq TPD limit, LlamaParse fragmentation, judge gate failure, LlamaIndex API drift, SQLite corruption, timeline slip) but **no row for hardware failure or data/backup loss** , the exact category the guidelines name first and use as their own worked example.

**Fix:** add a row, e.g.:

| Risk | Contingency | Likelihood | Impact |
|---|---|---|---|
| Local machine failure or loss of unsynced work (no backups) | Nightly off-machine backup of `benchmark.db`, parsed nodes, and code to a second location (e.g. git remote + cloud sync); SQLite WAL files committed per-run so loss window is minutes, not days | Low | High |

---

## Issue 3 (MODERATE, ~2-3 pts): Development summary doesn't state *why* the tools were chosen, or workflow organisation

`docs/ProposalGuidelines.pdf`, verbatim: *"Provide a brief overview of your proposed development environment and implementation language, **and the reasons why you chose them**... make sure this section covers the key question of how you will implement (realise) your project, **including how your workflow will be organised**."**

Section 4 currently states *what* is used (Python, LlamaIndex, Groq, ChromaDB, SQLite, asyncio) but never says *why Python/LlamaIndex specifically* (vs. e.g. a hand-rolled retrieval stack, or LangChain), and workflow organisation is left entirely to Section 10's Gantt chart rather than addressed here as the brief asks.

**Fix:** add 1-2 sentences such as:
> "Python is the natural choice because the entire required ecosystem, LlamaIndex, the Groq SDK, `rank_bm25`, ChromaDB, and the HuggingFace BGE models, is Python-native; reimplementing any of this in another language would mean rebuilding mature retrieval and embedding infrastructure from scratch. LlamaIndex specifically is chosen over a lower-level alternative such as LangChain because its `TextNode`/`NodeWithScore` abstractions already match the project's own node-centric data model (Section 5), so the three pipelines can share one retriever interface without an adapter layer. Work is organised phase-by-phase as in Section 10, with each phase's code committed and tested under a three-item local throttle (Guardrails §7) before being released at full scale, so a failure in one phase never risks the free-tier quota consumed by an earlier one."

---

## Issue 4 (MODERATE, ~2-3 pts): Project Description assumes specialist vocabulary the brief says it shouldn't

`docs/ProposalGuidelines.pdf`: *"the document should provide sufficient detail using non-specialist language, so anyone with a general computer science background would know what your project involves"* , and Project Description specifically is for *"a reader who isn't an expert in the topic area... most useful for the second marker, who might have no prior knowledge of the project."*

Section 1 uses "RAG", "retriever", "dense vector retriever", "BM25", "hierarchical summary-tree retriever" with no gloss. A second marker outside NLP/IR would not necessarily know what BM25 is or why a "summary tree" is a retrieval mechanism at all.

**Fix:** add brief in-line glosses, e.g. change:
> "...a semantic (dense vector) retriever, a statistical (BM25) retriever, and a structural (hierarchical summary-tree) retriever..."

to:

> "...a semantic retriever (which finds evidence by meaning, using numeric representations of text), a statistical retriever (which finds evidence by matching exact words and their frequency, the decades-old BM25 algorithm), and a structural retriever (which navigates a tree of AI-generated summaries built once over each document)..."

This costs almost nothing in word count and directly answers the brief's own accessibility test.

---

## Issue 5 (MINOR, ~1-2 pts): UI/UX Mockup section is thin relative to what the brief asks for

`docs/ProposalGuidelines.pdf`: *"This section should answer the key question of what your project will look like... It just needs to be enough to show that you have thought about what the software will look like **and how it will be used**."*

Section 9 is 57 words plus one results table. It correctly explains *why* there is no traditional UI, but never actually describes *how the researcher will use the system day to day* (e.g. running `run_benchmark.py`, reading `logs/index_build_costs.json`, querying `results` directly via SQLite), which is the "how it will be used" half of the brief's question.

**Fix:** add 2-3 sentences before the wireframe table describing the actual researcher-facing surface, e.g. a CLI invocation and a log/results-file glance, in addition to the final comparison view.

---

## Issue 6 (MINOR, process risk, not yet verified): Ethics category A0 is asserted, not verified against the authoritative source

The "A0" classification (Data Category A: publicly available, non-personal; Participant Category 0: no participants) is *consistent* with everything else in the document (SEC EDGAR public filings, no human subjects), but I have not been able to read the University's actual ethical-guidance category table (it sits behind Canvas authentication), so I cannot independently confirm "A0" is the literal category code the module uses for "public non-personal data, no participants."

**Fix (action item for you, not something I can resolve):** open the "ethical guidance" link referenced in `docs/ProposalGuidelines.pdf` on Canvas and confirm the A0 code against the actual category table before submitting. If it differs, the fix is a one-line change to the Statement of Ethical Compliance heading and body.

---

## Minor polish notes (no point impact, but a strict marker may flag them in comments)

- **Aims (Section 2.1)** read as method steps ("design and implement...", "construct...") rather than the brief's definition of aims as *"broad statements of intent... what you expect to have achieved after completing the work."* Consider rephrasing the verbs to outcome form, e.g. "A working, side-by-side comparison of three retrieval paradigms..." rather than "Design and implement three pipelines..." Cosmetic, not a content gap.
- **Body word count** (prose only, excluding tables/diagrams/references) is **1,497 words**; including the reference list it is **1,795 words**. The brief's 1,500-2,000 target is explicitly "not a fixed limit," so this is compliant, just sitting at the low edge. No action required, noted for awareness only.
- **Page count**: body content (Sections 1-12) runs to roughly 7 pages versus the brief's "aim for about 5"; again explicitly not a hard limit, but a strict marker valuing conciseness could comment on it. No action required unless you want to tighten Sections 3-4.
- **Submission format**: Canvas "Note that only pdf file will be accepted." The current deliverable is `.docx`. Remember to export/print to PDF as the final step before uploading; this report does not re-check PDF fidelity after that export.

---

## Fix checklist to reach 90+

1. [ ] Add the missing 6th BCS outcome ("critical self-evaluation of the process") to Section 8 (Issue 1).
2. [ ] Add a hardware-failure/backup-loss row to the Risks table (Issue 2).
3. [ ] Add 2-3 sentences to Section 4 justifying Python/LlamaIndex specifically, and naming workflow organisation explicitly (Issue 3).
4. [ ] Add brief in-line glosses for RAG/BM25/summary-tree in Section 1 (Issue 4).
5. [ ] Add 2-3 sentences to Section 9 on day-to-day researcher usage, not just the final results view (Issue 5).
6. [ ] Personally verify the A0 ethics code against the authoritative Canvas ethical-guidance page (Issue 6, cannot be done by me).
7. [ ] Export the final `.docx` to PDF before Canvas submission.

Items 1-5 are direct text edits inside the existing structure, no new sections or restructuring needed, and collectively should recover roughly 13-17 of the estimated points lost, putting the document at 93-97/100 on this rubric. Say the word and I will apply edits 1-5 directly to `Proposal_v1.0.0.docx`.
