# Typography — COMP702 Proposal / Dissertation / Slides

Type system for Word/PDF deliverables in this project, per `palette.md`'s
"Oxford Ink" identity. This reflects the scheme actually built into
`artifacts/Proposal_v1.0.0.docx`: a classic academic serif for reading text,
with a clean sans reserved for tabular and structural elements so data stays
easy to scan against the prose.

## Fonts

| Role | Font | Rationale |
|---|---|---|
| Body text, all headings (H1/H2), title page, references | **Garamond** | Classic academic book serif; reads as a dissertation, not a corporate deck. |
| Tables, diagrams, captions, header, footer, page numbers | **Calibri** | Clean sans for data/structure, deliberately contrasted against the serif prose. |
| Code / monospace (if needed) | Consolas | Unchanged from prior convention; not used in the proposal body. |

## Sizes (Word / PDF, A4, 2.5cm margins)

| Element | Font | Size | Weight | Colour |
|---|---|---|---|---|
| Title (cover page) | Garamond | 32pt | Bold | Blue 900 `#0A1F33` |
| Subtitle (cover page) | Garamond | 13pt | Italic | Blue 700 `#15406B` |
| Cover page labels ("Submitted by", "under the supervision of") | Garamond | 11.5pt | Italic | Neutral 700 `#44494F` |
| Cover page names (author, supervisor) | Garamond | 13.5pt | Bold | Neutral 900 `#1A1D21` |
| Institution lines (school, university) | Garamond | 11.5pt | Bold, all caps | Blue 900 `#0A1F33` |
| H1 / section (numbered, e.g. "3. Key Literature...") | Garamond | 20pt | Bold | Blue 900 `#0A1F33`, with a 1pt Blue 700 rule beneath |
| H1 / unnumbered top-level (Ethics, Table of Contents, References) | Garamond | 20pt | Bold | Same rule treatment as numbered H1, for one coherent hierarchy |
| H2 / sub-section | Garamond | 15pt | Bold, italic | Blue 700 `#15406B` |
| Body text | Garamond | 12pt | Regular | Neutral 900 `#1A1D21` |
| Bullet list items | Garamond | 12pt | Regular | Neutral 900 |
| Callout box ("Key point" gold accent) | Garamond | 11.5pt | Regular, lead-in bold italic | Blue 900 on Gold 100 wash |
| Reference list entries | Garamond | 11pt | Regular | Neutral 900, 0.18cm hanging indent |
| Table header row | Calibri | 10pt | Bold | White on Blue 700 |
| Table body | Calibri | 9.5pt | Regular | Neutral 900 |
| Diagram / flow-cell labels | Calibri | 9.5pt | Bold | White or Blue 900, per fill |
| Figure / table caption | Calibri | 10pt | Italic | Neutral 700 `#44494F` |
| Header (running title, all caps) | Calibri | 9pt | Regular, all caps | Neutral 500 `#767C84` |
| Footer (page X of Y) | Calibri | 9pt | Regular | Neutral 500 `#767C84` |

## Slide deck (PowerPoint — carried forward proportionally; not yet built/verified in an actual deck)

| Element | Font | Size | Weight |
|---|---|---|---|
| Title slide title | Garamond | 36pt | Bold |
| Section divider title | Garamond | 28pt | Bold |
| Slide title | Garamond | 24pt | Bold |
| Slide body | Garamond | 16pt | Regular |
| Chart/diagram label | Calibri | 12pt | Regular |
| Footer / slide number | Calibri | 10pt | Regular |

## Paragraph and layout rules

- Body paragraphs: justified alignment, 1.2 line spacing (288 twentieths-of-a-point
  line height), 9pt space-after, block spacing rather than first-line indent.
- H1: 22pt space-before, 11pt space-after, a 1pt Blue 700 bottom-border rule
  directly under the heading text, page-break-aware (keep-with-next).
- H2: 13pt space-before, 7pt space-after.
- Bullets: 5.5pt space-after, same 1.2 line spacing as body, 0.4cm hanging indent.
- Cover page: a 1.25pt Blue 700 rule beneath the title, and a 0.5pt Gold 500
  rule above the institution block, both full content-width; spacing tuned so
  the whole cover page fits a single A4 page.
- Callout boxes: Gold 100 fill, 3.5pt Gold 500 left border only (thin Gold 100
  hairlines on the other three sides), used sparingly (one per relevant
  section) for a single load-bearing fact, never for routine content.
- Do **not** rely on document-wide auto-hyphenation: it breaks short bold
  labels and centred cover-page titles unattractively (e.g. "Struc-tural").
  Leave hyphenation off and let justified text wrap on word boundaries.
- The Word Table of Contents field is left `dirty` with `updateFields`
  enabled in `settings.xml`, so Word populates it automatically on open; it
  will render empty under headless LibreOffice conversion, which is a known
  LibreOffice limitation, not a document fault.
- No em dashes or en dashes anywhere; use commas, semicolons, or plain
  hyphens for ranges (e.g. "157-173", not "157–173").
- British English spelling throughout.
