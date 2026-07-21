"""Randomized 20-section parsing validation audit.

Samples nodes across the corpus for a human to eyeball: does the table
survive intact, is the markdown rendering clean, is anything truncated?
See resources/specs/Project Idea.md §2 -- this script surfaces the sample,
it cannot self-certify the result; a human must actually look.
"""
import random

import aiosqlite


async def sample_sections(db_path: str, n: int = 20) -> list[dict]:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM nodes")
        rows = [dict(row) for row in await cursor.fetchall()]

    if len(rows) <= n:
        return rows
    return random.sample(rows, n)


def write_audit_report(samples: list[dict], out_path: str) -> None:
    lines = ["# Parsing Validation Audit", "", f"Sampled {len(samples)} node(s) for manual review.", ""]
    for s in samples:
        lines.append(f"## {s['node_id']} ({s['node_type']})")
        lines.append(f"- Document: {s['document_id']}")
        lines.append(f"- Section: {s.get('parent_item_header') or '(none)'}")
        lines.append(f"- Token count: {s['token_count']}")
        lines.append("")
        lines.append("```")
        lines.append(s["content"])
        lines.append("```")
        lines.append("")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
