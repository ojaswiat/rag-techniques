"""Writes golden_queries_to_label.md so the researcher can hand-write the
'why this answer is good' note + 0-100 score for each of the 20 GQ
(Phase Plan.md Phase 4 Goal 5). This is the only manual step in Phase 4."""
import asyncio

import database_manager as dbm


def render_label_markdown(golden_queries: list[dict]) -> str:
    parts = ["# Golden Queries -- Human Labeling\n"]
    for gq in golden_queries:
        parts.append(
            f"## {gq['query_id']}\n\n"
            f"**Quadrant:** {gq['quadrant']}\n"
            f"**Document:** {gq['document_id']}\n"
            f"**Query:** {gq['query_text']}\n"
            f"**Ground truth:** {gq['ground_truth_answer']}\n\n"
            f"**Score (0-100):** \n"
            f"**Good Example (yes/no):** \n"
            f"**Why this answer is good:** \n\n"
            f"---\n"
        )
    return "\n".join(parts)


async def main(db_path: str = "benchmark.db", out_path: str = "golden_queries_to_label.md") -> None:
    golden_queries = await dbm.get_golden_queries(db_path)
    markdown = render_label_markdown(golden_queries)
    with open(out_path, "w") as f:
        f.write(markdown)
    print(f"Wrote {len(golden_queries)} golden queries to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
