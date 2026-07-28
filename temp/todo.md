## Ingest the data before page 4

Try to run for TSLA first instead of MSFT.

Run this from the project directory:

cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pipelines.structural.build_summary_index

That's the same command that was already run — it'll skip the 3 cached AAPL filings (AAPL_2023, AAPL_2024, AAPL_2025) automatically and resume from MSFT_2023 onward once Groq's daily token quota has reset.

## Prompts
Use /superpowers:brainstorming and /monitor (especially the search) skills to

### Plan a code base search
1. Search for initial drift from proposals. Search in the entire project what was initially proposed, and then what was finally done. This is important in mentioning the report.
2. Search for numbers, quantifiers, etc. Every number you think can contribute to the details of the research. For example, TREE STRUCTURE CONSISTENCY: AAPL_2023: OK  (docstore=795, tree_nodes=795, roots=8).
3. Search for techniques, processes, decisions, etc.
4. Search in the entire project whatever is necessary.

### Organise information
1. Plan a storage mechanism to store all the information in a contextual manner - don't mess up. Spawn sub-agents if you have to.
2. Create a new directory called `./research/information` and store all the information in different standalone html files linked to each other and give me a report. Use ui-ux-pro-max skills to generate the report - minimal, modern, no rounded corners.
3. Create a skill in this project for claude and opencode to tell an AI agent how to use this information (your way of oranising reports in different files and linking them will be the key here).

### Using information
Plan a IEEE level research paper for this project using the information you just gathered with references.

Constraints:
1. Only use the project as the primary source of truth.
2. DO not introduce any imaginary, online blog material, artificial claims, etc.
3. Only use what happend in this project, and what was done in this project only.

Search for high-quality research papers for reference in this project.
- Good publication
- Good number of citations.
- Keep number of reference papers limit to 30 - only highly relevant papers.
This doesn't mean to search only for 30 papers but to search many papers and come up with highly relevant ones.

## Planning Research
1. Validate the references as per the information generated in the `./research/information/index.html` file.
2. Validate the claims made in the information using database queries, generated text-nodes, findings, results, outputs, etc.