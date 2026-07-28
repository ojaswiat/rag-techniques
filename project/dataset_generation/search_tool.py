"""Local, dependency-free keyword search the Critic uses to find evidence.

Not a retrieval pipeline (Guardrails.md's P2-purity rule is about the
benchmarked BM25 pipeline in Phase 5, not incidental tooling here) --
just simple word-overlap scoring so the Critic can locate candidate nodes
in a filing before answering.
"""
import re

_WORD_RE = re.compile(r"[a-z0-9]+")

SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_filing",
        "description": (
            "Search this filing's nodes for content matching a query. "
            "Returns up to 5 of the most relevant nodes with their node_id and content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to search for in the filing",
                },
            },
            "required": ["query"],
        },
    },
}


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def search_filing_nodes(nodes: list[dict], query: str, top_k: int = 5) -> list[dict]:
    query_tokens = _tokenize(query)
    scored = []
    for node in nodes:
        node_tokens = _WORD_RE.findall(node["content"].lower())
        # Count occurrences of query tokens in this node
        score = sum(1 for token in node_tokens if token in query_tokens)
        if score > 0:
            scored.append((score, node["node_id"], node))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [node for _, _, node in scored[:top_k]]
