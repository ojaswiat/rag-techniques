"""Reads the filled-in golden_queries_to_label.md back into golden_queries."""
import asyncio
import re

import database_manager as dbm

_ENTRY_RE = re.compile(
    r"^## (?P<query_id>\S+)\n\n"
    r".*?"
    r"\*\*Score \(1-10\):\*\*\s*(?P<score>\S+)?\s*\n"
    r"\*\*Why this answer is good:\*\*\s*(?P<reasoning>.*?)\s*\n",
    re.DOTALL | re.MULTILINE,
)


def parse_label_markdown(markdown_text: str) -> list[dict]:
    results = []
    for match in _ENTRY_RE.finditer(markdown_text):
        score_raw = match.group("score")
        reasoning = (match.group("reasoning") or "").strip()
        if not score_raw or not reasoning:
            continue
        try:
            score = int(score_raw)
        except ValueError:
            continue
        results.append({
            "query_id": match.group("query_id"),
            "human_score": score,
            "human_reasoning": reasoning,
        })
    return results


async def main(db_path: str = "benchmark.db", in_path: str = "golden_queries_to_label.md") -> None:
    with open(in_path) as f:
        markdown_text = f.read()

    labels = parse_label_markdown(markdown_text)
    for i, label in enumerate(labels):
        try:
            await dbm.update_golden_query_labels(
                db_path, label["query_id"], label["human_score"], label["human_reasoning"]
            )
        except Exception:
            print(f"Imported {i} of {len(labels)} labels before failing on {label['query_id']!r}")
            raise
    print(f"Imported {len(labels)} human labels from {in_path}")


if __name__ == "__main__":
    asyncio.run(main())
