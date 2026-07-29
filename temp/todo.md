

Change the models and build summary again refer to model-selection.md file.
Build the node tables again.
Full corpus ingestion required before any data related development.

- Phase 3 reads it to build P3's summary tree (a separate, one-time step).
- Phase 4 reads it to write benchmark questions and cite exact pieces of evidence.

## Doubts
1. One hiccup kills everything. If the Critic robot ever gets stuck (can't answer in 5 tries) or sends back broken text, the whole program crashes instead of just skipping that one question and moving to the next. Imagine your dishwasher stopping forever because one plate was dirty, instead of just re-washing that plate.
2. Questions get grouped by company by accident. Because of how the code picks questions, "hard math questions" mostly end up coming from Tesla, "simple fact questions" mostly from Apple. So later, when the dissertation says "Tesla questions were harder," nobody can tell if that's true because they're hard questions, or just because they're Tesla. Two things got mixed together that need to stay separate.

Important (should fix, real problems but not run-killing):

3. Asking the same question the same way and expecting a different answer. When a question gets rejected, the code just asks the robot again with the exact same information, same "creativity setting" (temperature 0 = no randomness). Like asking a calculator "2+2" again after it said 5 — it'll say 5 again. Wastes tries.
4. Grading too strict. The checker compares numbers between two robots' answers. If one says "$100 million" and other says "$100 million in 2025," it counts the extra year as an extra number and marks it WRONG, even though the actual answer matches. Too picky.

5. Might not make enough questions and nobody would know. There's only enough raw material (sections) to maybe get 65 out of 100 questions if things go well. If it comes up short, the program just quietly stops without telling you "hey, I only got 90 out of 140."
6. No progress updates at all. While it's running for possibly hours and spending your free API credits, it prints literally nothing. No "working on question 5 of 140," no "this one got rejected." You're flying blind.
7. The robot-to-robot "tool calling" handshake was never actually tested for real. The tests use fake stand-in objects, not real robot responses, so nobody's proven the actual message-passing works when it's the real AI talking.
8. Some sections are huge and might get rejected outright. A couple sections are ~29,000 words worth of tokens. If Groq's free plan has a smaller per-question limit than that, those sections would just fail with an error the code doesn't even try to recover from (since it's not the "try again" kind of error).

Minor (nice-to-have, not urgent):

9. Typo protection missing. If you mistype a question's ID while filling in your 20 hand-graded examples, the program silently updates nothing and still says "success!" — you'd never know your grade didn't save.
10. No sanity check on your 1-10 score. You could accidentally type "99" as a score and it'd just accept it, even though scores should only be 1 through 10.
11. Naming is a little clunky — the ID names are longer than they need to be, just cosmetic.
12. Search tool slightly biased toward wordy answers. The "find the right paragraph" helper counts how many times a word repeats, so a long paragraph that says "revenue" five times beats a short paragraph that's actually more relevant. Minor.
13. Empty list treated as "give me everything." If you pass in zero filings by accident, the code treats that the same as "use all 9 filings" instead of "use none." Surprising behavior.
14. No duplicate-question check. Nothing stops two very similar questions both getting into the final set, though it's unlikely given how the sections are split up.






## Research
**In a fresh session**
Use /superpowers:brainstorming and /monitor (especially the search) skills to

### Plan a code base search
1. Search for initial drift from proposals. Search in the entire project what was initially proposed, and then what was finally done. This is important in mentioning the report.
2. Search for numbers, quantifiers, etc. Every number you think can contribute to the details of the research. For example, TREE STRUCTURE CONSISTENCY: AAPL_2023: OK  (docstore=795, tree_nodes=795, roots=8).
3. Search for techniques, processes, decisions, categories, project history using git and monitor, etc.
4. Search in the entire project whatever is necessary.
5. Search in superpowers plans directory, docs, directory and other directory.
---
Create an HTML canvas mind map for me so that I can understand the project easily

Include directories, folders, files, scripts, functions inside the files, etc.
Add proper description to each thing.
- Use /superpowers:brainstorm and /superpowers:writing-plans to plan it out.
- Use /graphify skills traverse the codebase faster.
- Use /ui-ux-pro-max skils to design and plan out the UI first after your analysis.
- Give me the html canvas file in temp directory.


### Organise information
1. Plan a storage mechanism to store all the information in a contextual manner - don't mess up. Spawn sub-agents if you have to.
2. Create a new directory called `./research/information` and store all the information in different standalone html files linked to each other and give me a report. Use ui-ux-pro-max skills to generate the report - minimal, modern, no rounded corners.
3. Create a skill in this project for claude and opencode to tell an AI agent how to use this information (your way of oranising reports in different files and linking them will be the key here).

### Using information
Plan a IEEE level research paper for this project using the information you just gathered with references.

Constraints:
1. Only use the project as the primary source of truth.
2. Do not introduce any imaginary, online blog material, artificial claims, etc.
3. Only use what happend in this project, and what was done in this project only.
4. We need to present the research level information exactly as we encountered.

Search for high-quality research papers for reference in this project.
- Good publication
- Good number of citations.
- Keep number of reference papers limit to 30 - only highly relevant papers.
This doesn't mean to search only for 30 papers but to search many papers and come up with highly relevant ones.

## Planning Research
1. Validate the references as per the information generated in the `./research/information/index.html` file.
2. Validate the claims made in the information using database queries, generated text-nodes, findings, results, outputs, etc.