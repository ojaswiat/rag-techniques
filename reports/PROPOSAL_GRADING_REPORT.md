# Strict Grading Report V2: Proposal_v1.0.0.docx

**Graded against:** `docs/ProposalGuidelines.pdf` (official COMP702 CA1 brief, read in full, verbatim quotes below) and `docs/ProposalTemplate.pdf` (official structure/example).
**Method:** full text extracted programmatically from the *current* `.docx` (post the fixes already applied since `reports/PROPOSAL_GRADING_REPORT.md` was written), checked clause-by-clause against the guidelines' own wording. This is a fresh, independent pass, not a re-statement of the v1 report.

**Status of the v1 report's five fixable issues:** all five have been resolved in the current document — BCS Section 8 now lists all six outcomes including "Critical self-evaluation of the process"; the Risks table now has a hardware/backup-loss row; Section 4 now states *why* Python/LlamaIndex and names workflow organisation; Section 1 now glosses semantic/statistical/structural in plain language; Section 9 now describes day-to-day researcher usage, not just the final results view. This report does not re-list those — it looks for what is *still* missing.

**Same caveat as v1:** the brief links to an authenticated Canvas "marking guidelines" page and an "ethical guidance" page I cannot read. The Data Category **A0** self-assessment is internally consistent (public SEC filings, no participants) but unverified against the authoritative category table — confirm it yourself before submission.

---

## Overall estimated score: 91-94 / 100

This is now a strong, complete, professionally executed document. Every required section from the brief is present, in the right order, with a populated Table of Contents. What remains are smaller, literal-wording gaps against the brief's own checklist items — the kind a strict marker working through the brief line by line would still tick off, but none of them structural.

| Rubric area (inferred from brief) | Estimate | Why |
|---|---|---|
| Structure & completeness | 10/10 | All 12 required sections present, correct order, populated TOC, title page matches template fields exactly. |
| Clarity for non-specialist reader | 9/10 | Section 1 now glosses semantic/statistical/structural retrieval in plain language; reads cleanly for a "general CS background" second marker. |
| Depth/quality of literature engagement | 10/10 | 9 real, high-citation, correctly Harvard-cited papers, woven into the argument; every in-text citation has exactly one matching reference and vice versa. |
| Technical design clarity (dev/implementation summary) | 9/10 | States *what*, *why these tools specifically*, and *how workflow is organised* — all three things the brief names. |
| Data sources | 7/10 | Describes data and source well; doesn't explicitly state the *permission* basis the brief asks for in as many words (see Issue 1). |
| Planning & risk realism | 8/10 | Gantt is detailed and phase-accurate; omits an explicit time allocation for "presenting the project" (see Issue 2); risks table doesn't name a generic "programming problems" bucket (see Issue 3). |
| BCS criteria coverage | 10/10 | All six official outcomes addressed, each tied to a concrete project decision. |
| Referencing mechanics | 10/10 | Correct Harvard format throughout; no orphaned citations either direction. |
| Presentation/polish | 10/10 | Native Word diagrams/tables, consistent Oxford Ink palette, no em dashes, British English, no split tables or stranded headings. |

---

## Issue 1 (MODERATE, ~2-3 pts): Data Sources section doesn't explicitly state the *permission* basis

`docs/ProposalGuidelines.pdf`, verbatim: *"You should describe the data you will be using, state how it will be obtained, **confirm you are using it with permission**, and explain how you will ensure confidentiality and anonymity of any personal information."*

Section 5 currently states the data is public, contains no personal information, and is parsed via LlamaParse — but it never explicitly asserts the *permission* clause the brief asks for by name. For US SEC filings this permission is essentially automatic (they are public-domain government regulatory records), but the brief wants that confirmed in the document, not left implicit.

**Fix:** add one sentence to Section 5, e.g.:
> "SEC EDGAR filings are public-domain US federal regulatory records with no copyright restriction on access or reuse, so no licence, consent, or data-sharing agreement is required to use them in this project."

(Section 5 already contains a near-identical sentence in the ethics statement on the title page — "requires no licence, consent, or data-sharing agreement" — this fix is simply pulling that same assurance into Section 5 itself, where the brief's checklist expects to find it.)

---

## Issue 2 (MODERATE, ~2-3 pts): Project Plan doesn't carve out time for "presenting the project"

`docs/ProposalGuidelines.pdf`, verbatim: *"Remember to include time for presenting the project and writing the dissertation."*

Table 10.1's final phase is "8. Results Analysis & Write-up" — this covers the dissertation write-up half of that sentence but not the presentation half. There is no row, sub-task, or even a parenthetical for preparing/delivering the project presentation or viva.

**Fix:** either add a 9th phase row (e.g. "9. Presentation Preparation", overlapping the final week alongside write-up), or fold it explicitly into phase 8's label/description, e.g. "8. Results Analysis, Dissertation Write-up & Presentation Prep."

---

## Issue 3 (MINOR, ~1-2 pts): Risks table doesn't name a generic "programming problems" risk

`docs/ProposalGuidelines.pdf` names four common-risk categories verbatim: *"hardware failure, software failure, running out of time, and programming problems."* Table 11.1 now covers hardware/backup failure, several specific software-failure modes (Groq limits, LlamaParse fragmentation, judge gate failure, API drift, SQLite corruption), and timeline slip — but every row is tied to a specific named tool or process. There is no row for the generic case the brief names explicitly: ordinary coding bugs/defects discovered during implementation that aren't tied to a third-party dependency or service.

**Fix:** add a row such as:

| Risk | Contingency | Likelihood | Impact |
|---|---|---|---|
| Implementation bugs found late in a pipeline (e.g. a retrieval or scoring logic error) | Each phase is run end-to-end under the three-item local throttle before release at full scale (Section 4), so defects are caught against a small sample before they can consume free-tier quota or corrupt a full run | Medium | Medium |

---

## Issue 4 (MINOR, ~1 pt): Data Sources doesn't cross-reference that the project's own evaluation activity generates data

`docs/ProposalGuidelines.pdf`, verbatim: *"Remember that requirements gathering and evaluation activities will generate data."* The two manual researcher-only steps (labelling 20 teaching exemplars, hand-scoring 60 judge-validation outputs) are described in Section 7 (Project Ethics) but Section 5 (Data Sources) never mentions that these evaluation activities themselves are also a data source, which is precisely the thing this sentence in the brief is flagging.

**Fix:** add a one-line cross-reference at the end of Section 5, e.g.:
> "The hand-labelled teaching exemplars and hand-scored judge-validation outputs produced during evaluation (Section 7) are also project-generated data, authored solely by the researcher rather than collected from others."

---

## Minor polish notes (no/low point impact, listed for completeness)

- **Aims (Section 2.1)** are still phrased as method/action statements ("Design and implement...", "Construct...") rather than the brief's literal definition of aims as outcome statements ("what you expect to have achieved"). This was already flagged in v1 as a no-impact polish note; the content is complete and the meaning is clear, so this remains cosmetic only.
- **BM25 acronym** in Section 1 is named but never expanded (Best Matching 25). Trivial; the surrounding gloss already explains the mechanism in plain words, so this costs nothing.
- **Page count**: roughly 7 pages of body content (Sections 1-12) versus the brief's "aim for about 5" — explicitly not a hard limit ("not a fixed limit... no penalties for going over or under"), so no action required.
- **Submission format**: Canvas accepts PDF only. `artifacts/Proposal_v1.0.0.pdf` already exists and was regenerated from the current `.docx` in this session — confirm it is the file actually uploaded, not the `.docx`.
- **Ethics category code (A0)**: still unverified against the authenticated Canvas ethical-guidance page (Issue 6 in the v1 report, carried forward, cannot be resolved by me).

---

## Fix checklist to close the remaining gap

1. [ ] Add one sentence to Section 5 explicitly confirming the permission/licence-free basis for using SEC EDGAR data (Issue 1).
2. [ ] Add an explicit time allocation for project presentation in the Gantt chart / Table 10.1 (Issue 2).
3. [ ] Add a generic "implementation bugs / programming problems" row to the Risks table (Issue 3).
4. [ ] Cross-reference in Section 5 that the evaluation activity itself generates project data (Issue 4).
5. [ ] Personally verify the A0 ethics code against the authoritative Canvas ethical-guidance page (cannot be done by me).
6. [ ] Confirm the file uploaded to Canvas is the PDF, not the docx.

Items 1-4 are short, additive text edits inside the existing structure — no restructuring needed — and collectively should recover roughly 7-9 of the estimated points still on the table, putting the document at approximately 98-100/100 on this rubric. Say the word and I will apply these edits directly to `Proposal_v1.0.0.docx`.
