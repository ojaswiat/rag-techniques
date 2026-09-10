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
   on the later-added filings (JPMorgan, Johnson & Johnson).
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

---

## 2. Filing-to-markdown conversion artefacts in the node corpus

1. **Issue:** Filing-to-markdown conversion artefacts in the node corpus.
2. **Description:** Three distinct artefacts survive into `nodes.content`.
   First, four nodes carry a bare run of ten or more digits where a
   financial figure should sit: `JNJ_2023_n0162`, `JNJ_2023_n0359`,
   `JNJ_2023_n1152` and `JNJ_2023_n1157`. The values are sequential-looking
   internal identifiers leaking through the HTML-to-markdown step rather
   than figures, so `JNJ_2023_n0359` reports a cost of products sold of
   12,094,627,945,450, roughly 12 trillion dollars, against a true figure
   near 27 billion. Second, 1,089 nodes contain unescaped HTML character
   entities, almost always `&#x26;` where an ampersand belongs. Third,
   seven nodes contain a raw HTML tag. A scan of all 18,297 nodes found no
   mojibake and no empty or whitespace-only nodes.
3. **Scope:** The digit-run corruption is confined to four nodes, 0.02% of
   the corpus, all in `JNJ_2023`. The entity encoding affects 1,089 nodes,
   about 6%, concentrated in `JPM_2024` (376), `JPM_2023` (336),
   `JNJ_2023` (140) and `JNJ_2024` (138). Raw tags affect seven nodes.
   Exactly one benchmark query, `QT3_PQ_009`, cites a corrupted node. No
   ground-truth answer in any of the three query sets contains an HTML
   entity or a raw tag, so the answer keys are clean.
4. **Impact on research:** Neutral, and arguably useful. All three
   pipelines index and retrieve the identical corpus, so no architecture
   sees a cleaner filing than another. For `QT3_PQ_009` specifically the
   answer key faithfully records what its node actually says, so the row
   grades extraction fidelity: a pipeline reporting the corrupted value it
   retrieved is marked correct, while one substituting a plausible figure
   from model knowledge is marked wrong. That is the correct direction for
   a retrieval benchmark. Real 10-K filings convert imperfectly, and that
   messiness is part of the problem domain rather than an accident of this
   build.
5. **Resolution:** Documented only. Repairing the corpus would remove a
   genuine faithfulness probe and would mean the reported results no longer
   describe the corpus that was actually indexed. The one cosmetic cost is
   that an examiner reading `QT3_PQ_009` in isolation sees an absurd figure
   without the explanation, which this entry supplies. Note that an earlier
   pass reported this as a single corrupted node; a wider scan found four.

---

## 3. Redundant questions and answer restatement within the 100-query set

1. **Issue:** Redundant questions and answer restatement within the 100-query set.
2. **Description:** Two pairs of primary queries ask the same question of
   the same filing and carry the same answer: `QT1_PQ_002` and
   `QT1_PQ_010` both ask Apple's full-time equivalent headcount at 30
   September 2023, and `QT1_PQ_005` and `QT1_PQ_023` both ask the date
   JPMorgan acquired First Republic Bank. A third pair, `QT1_PQ_003` and
   `QT2_PQ_017`, covers the same fact about unresolved SEC staff comments
   in `MSFT_2023` but is split across two quadrants, which additionally
   makes the Q2 member a weak instance of its quadrant, since Q2 is meant
   to require synthesis across passages and this fact sits in one sentence.
   Separately, three questions restate most of their own answer inside the
   question text: `QT1_PQ_021` (28 of 32 answer tokens already present),
   `QT2_PQ_005` (24 of 29) and `QT2_PQ_007` (17 of 20).
3. **Scope:** Three near-duplicate pairs and three restatement cases, so at
   most six of 100 primary queries.
4. **Impact on research:** Small and common-mode, but not perfectly
   neutral. The duplicates reduce the effective question count from 100 to
   about 98, costing a little precision on every reported mean. The three
   restatement cases are answerable with no useful retrieval at all, so all
   three pipelines score near the ceiling on them; that compresses the
   measured gap between architectures very slightly rather than shifting
   the ranking. Neither effect favours any one pipeline.
5. **Resolution:** Documented only. Removing questions after the answer
   keys were corrected, and after retrieval behaviour on them is partly
   known, risks selecting the benchmark toward a preferred outcome. Keeping
   the full 100 and disclosing the redundancy is the more defensible
   position, and the effect size is well below the differences being
   reported.

---

## 4. Construct concentration within the Q4_Implicit_Table quadrant

1. **Issue:** Construct concentration within the Q4_Implicit_Table quadrant.
2. **Description:** Q4 is specified as requiring a calculation or a
   cross-row or footnote inference over a table. Four of its 25 questions
   are the same task shape, counting the individuals who signed the filing
   (`QT4_PQ_001`, `QT4_PQ_002`, `QT4_PQ_010`, `QT4_PQ_022`), and two more
   ask for the sum of the page numbers listed in an index
   (`QT4_PQ_005`, `QT4_PQ_018`). The latter is arithmetic over a table
   whose result carries no financial meaning.
3. **Scope:** Six of 25 Q4 questions, so six of the 100 primary queries.
4. **Impact on research:** Neutral for the comparison, and the questions
   are valid tests despite appearing trivial. Counting signatories requires
   retrieving an intact tabular block; chunk-based retrieval can split that
   block while tree summarisation may preserve or destroy it differently,
   which is exactly the structural-versus-semantic contrast the study
   measures. Summing index page numbers is a genuine multi-cell extraction
   and arithmetic task regardless of the semantic emptiness of its result.
   The real limitation is coverage rather than validity: 24% of the
   quadrant probes a narrow band of one sub-skill, so Q4 tests table
   reasoning less broadly than its definition implies.
5. **Resolution:** Documented only, as a construct-coverage limitation of
   the Q4 quadrant rather than a defect in any row. Separately, all ten
   re-derived Q4 answers were independently reproduced from their evidence
   nodes during the citation fix recorded in deviation 35, by summation,
   subset sum, pairwise difference, quantity-by-price product or element
   count. **No arithmetic error was found in any Q4 ground-truth answer.**
