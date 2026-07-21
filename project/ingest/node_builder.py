"""Splits parsed Markdown into atomic TextNode-shaped dicts.

A Markdown table is one atomic node -- never bisected. Section headers
("Item 1A. Risk Factors") are tracked and attached to every node that
follows until the next header, per resources/specs/Project Idea.md §2.

source_page_num is always None: SEC filings are native HTML with no
intrinsic pages (Project Idea.md §2) -- this is a display-only field with
nothing reliable to populate it from at this stage.
"""
import re

_HEADER_RE = re.compile(r"^#{1,3}\s*(Item\s+\d+[A-Za-z]?\.?\s*.+?)\s*$", re.IGNORECASE)


def _is_table_block(block: str) -> bool:
    lines = [line for line in block.splitlines() if line.strip()]
    if not lines:
        return False
    return lines[0].strip().startswith("|")


def build_nodes(document_id: str, ticker: str, fiscal_year: int, markdown_text: str) -> list[dict]:
    blocks = [b for b in markdown_text.split("\n\n") if b.strip()]

    nodes = []
    current_header = None
    counter = 1

    for block in blocks:
        stripped = block.strip()
        header_match = _HEADER_RE.match(stripped)
        if header_match:
            current_header = header_match.group(1).strip()
            continue

        node_type = "table" if _is_table_block(stripped) else "text"
        node_id = f"{document_id}_n{counter:04d}"
        nodes.append({
            "node_id": node_id,
            "document_id": document_id,
            "parent_item_header": current_header,
            "node_type": node_type,
            "source_page_num": None,
            "content": stripped,
            "token_count": len(stripped.split()),
        })
        counter += 1

    return nodes
