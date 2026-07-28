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


## Comments and answers
Commit the current changes and push. Then branch out with a proper branching name and fix things as instructed:

4. Make sure that the agent records what quadrant question it asked so that if fails, the questions can be pulled from the appropriate quadrant.
5. Use a simple JSON-based logger to record all the tries, find the suitable question again to replace it with a question from the same quadrant, in case of failing.
Purpose: We will generate 240 queries, but as originally planned, only 100 queries accross 4 quadrants, spread evenly will be used.

/superpowers:brainstorming **Enhance the results schema to track more data and metadata.**

### 5 retries
1. Use a simple queue to queue failed questions to the back of the queue.
2. One try means - asking the same question to P1, P2, and P3.
3. If a question fails at any pipeline P1, P2, or P3, add it to the back of the queue and proceed with the next question.
4. In any case, ensure that P1, P2, P3, get the same questions asked.
5. The queue should start with all 280 queries and take the next question after completing a "try".
6. 140 successful runs are recorded for evaluation.
7. In case the question is failing again and again. Discard the query and replace it with a query of same quadrant. You need to store stats somewhere, which query failed, why, on which pipeline, etc and if replaced, what query was it replaced with.

### Questions get grouped by companies by accident
1. We are not checking which pipeline is better, we are just evaluating the correctness and retrieval of each pipeline and comparing them.
2. The grouping of companies by accident shouldn't matter here. After all, we're ensuring same questions for each pipeline and checking their retrieval metrics and correctness.
3. No one's saying the Tesla questions were hard or stuff like that. We are comparing 3 pipelines with same set of queries across 4 different quadrants.
4. If companies are grouped by accident it doesn't matter.

> P3 is expected to be weakest on the table-heavy quadrants (Q3/Q4).

No, we don't know yet. That is why we are experimenting. Remove this line and all such lines.

Your explanation:
```
What's actually still worth fixing, separate from the confound argument: the content mismatch — Q3/Q4 are supposed to be table-extraction/table-math questions, but fill-order could hand the Generator a pure-prose section and ask it to invent a table question anyway. That's a data-quality problem (can you even write a good "extract this cell" question from a passage with no table?), independent of any statistical confound. That part I'd still fix — content-aware routing (table sections → Q3/Q4)
```

- No, make sure that we are generating correct types of question for each quadrant, doesn't matter from which company it belongs to. We aren't comparing pipeline on the basis of companies. We are just comparing them on the basis of their retrieval and accuracy.
- But make sure the questions are generated uniformly from all the companies.

### Asking the same question the same way and expecting a different answer.
1. Let the temperature be 0, but ensure that 
2. Given that the questions were formulated using a fixed small dataset like this, I don't think it should fail.
3. Even if they should fail, ensure that same questions were asked to all the pipelines as instructed above.
4. After more dataset download and ingestion, this issue should be fixed.

### Grading too strict. The checker compares numbers between two robots' answers. If one says "$100 million" and other says "$100 million in 2025," it counts the extra year as an extra number and marks it WRONG, even though the actual answer matches. Too picky.
The whole point of using LLM-as-a-judge to evaluate the pipeline's responses in a contextual, factual and a cited manner. So if this types of answers come up, the judge should be able to pick up the citations and match the claims and then generate its verdict. After the verdict, the query data, performance query, answers, metrics, everything is recorded for each pipeline.

Record every decision.

## Research
Use /superpowers:brainstorming and /monitor (especially the search) skills to

### Plan a code base search
1. Search for initial drift from proposals. Search in the entire project what was initially proposed, and then what was finally done. This is important in mentioning the report.
2. Search for numbers, quantifiers, etc. Every number you think can contribute to the details of the research. For example, TREE STRUCTURE CONSISTENCY: AAPL_2023: OK  (docstore=795, tree_nodes=795, roots=8).
3. Search for techniques, processes, decisions, categories, project history using git and monitor, etc.
4. Search in the entire project whatever is necessary.
5. Search in superpowers plans directory, docs, directory and other directory.

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