"""Local, dependency-free keyword search the Critic uses to find evidence.

Not a retrieval pipeline (Guardrails.md's P2-purity rule is about the
benchmarked BM25 pipeline in Phase 5, not incidental tooling here) --
just simple word-overlap scoring so the Critic can locate candidate nodes
in a filing before answering.

Scoring is plain length-normalized term frequency (raw query-term hit
count divided by node token length, floored at a minimum length so
degenerate tiny nodes cannot game the ratio -- see
_MIN_NODE_LENGTH_FOR_SCORING below) -- not raw hit count (biases toward
long/wordy nodes over short precise ones) and deliberately not TF-IDF/
BM25. IDF was considered and rejected: it is BM25's core differentiator,
and adding it here would meaningfully re-derive P2's real BM25 scoring
inside a tool the Critic uses to independently verify Generator queries
before they enter the benchmark dataset -- any resemblance to BM25 here
would bias which queries survive into the dataset toward ones P2's real
pipeline scores well, an unearned advantage for P2 in Phase 5. For the
same reason this stays a hand-rolled formula rather than a library
(`rank_bm25` or any TF-IDF package).
"""
import re

_WORD_RE = re.compile(r"[a-z0-9]+")

# Floor for the length-normalization denominator. Plain division by node
# token length lets a
# degenerate tiny node (e.g. a 1-token block like "Revenue") score close to
# 1.0 and beat a longer, substantive node containing the same term with real
# context -- node_builder.py splits filing markdown on blank lines with no
# minimum block-length check, so real 10-K filings contain many such tiny
# blocks (table headers, stray captions, isolated lines). 24 is not
# arbitrary: it is the median token_count across the live corpus (queried
# benchmark.db's nodes table, restricted to the 13-filing manifest, 18,297
# real nodes: min=1, p5=2, p10=3, p25=5, median=24, p75=75, max=1243). Using
# the median means any node shorter than "typical" is scored as if it were
# typical-length, so it must compete on the same denominator as a
# normal-sized node rather than getting an inflated score just by being
# tiny. p25 (5) was rejected as too small to meaningfully dent the bug; p75
# (75) was rejected as too aggressive, since it would flatten scoring for
# legitimate short-but-real nodes toward zero.
_MIN_NODE_LENGTH_FOR_SCORING = 24

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
        if not node_tokens:
            continue
        # Count occurrences of query tokens in this node, normalized by node length
        raw_count = sum(1 for token in node_tokens if token in query_tokens)
        if raw_count > 0:
            score = raw_count / max(len(node_tokens), _MIN_NODE_LENGTH_FOR_SCORING)
            scored.append((score, node["node_id"], node))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [node for _, _, node in scored[:top_k]]
