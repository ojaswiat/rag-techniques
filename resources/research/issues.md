# Research Issues Log

Known issues and limitations relevant to the research, not resolved in the
codebase because they don't affect the validity of the P1/P2/P3 comparison.
For actual deviations from the original plan, see `deviations.md`.

## Format

Each entry:

1. **Issue:** short title.
2. **Description:** what the issue is, in plain terms.
3. **Scope:** how much of the data/corpus it affects.
4. **Impact on research:** does it bias the P1/P2/P3 comparison or the
   dataset/results, or is it neutral.
5. **Resolution:** fixed, or documented-only (with reasoning for leaving it
   unfixed).

---

## 1. LlamaParse table header misalignment

1. **Issue:** LlamaParse table header misalignment.
2. **Description:** In some parsed 10-K tables, the units caption (e.g.
   "(In millions)") is merged into the table's header row as the first
   column's label, instead of sitting on its own caption line above the
   table. The column-1 header text is wrong; all other headers, and every
   data row/value in the table, are correct and correctly aligned.
3. **Scope:** Found in 31 tables across 5 of the original 9 filings audited
   (Microsoft's three filings, and two of Tesla's three). Not yet re-checked
   on the later-added filings (JPMorgan, Johnson & Johnson). Walmart was
   dropped from the corpus before this re-check happened -- see
   `deviations.md` entry 20 -- so no re-check is needed there.
4. **Impact on research:** Neutral. The defect originates in LlamaParse's
   own PDF-to-Markdown conversion, upstream of all three retrieval
   pipelines equally -- every pipeline sees the same parsed text, so it
   cannot bias a comparison between them. It also only affects one header
   cell's label, not any data value, and language models read a table as
   plain text rather than a structured schema, so it does not affect
   question answering either. This is a known, widely-reported LlamaParse
   behaviour, not specific to this project's data or pipeline.
5. **Resolution:** Documented only, left unfixed. A fix would require
   pattern-matching and rewriting already-parsed table structure, which
   risks introducing new corruption for a defect with no measurable effect
   on retrieval or answer correctness.
