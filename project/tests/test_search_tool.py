from dataset_generation.search_tool import SEARCH_TOOL_SCHEMA, search_filing_nodes


def _node(node_id, content):
    return {"node_id": node_id, "content": content}


def test_ranks_by_keyword_overlap():
    nodes = [
        _node("n1", "Total revenue increased due to strong iPhone sales"),
        _node("n2", "The board of directors met quarterly"),
        _node("n3", "Total revenue and total operating expenses both rose"),
    ]
    results = search_filing_nodes(nodes, "total revenue", top_k=5)
    assert [r["node_id"] for r in results] == ["n3", "n1"]


def test_excludes_zero_overlap_nodes():
    nodes = [
        _node("n1", "unrelated content about employees"),
    ]
    results = search_filing_nodes(nodes, "total revenue", top_k=5)
    assert results == []


def test_respects_top_k():
    nodes = [_node(f"n{i}", "revenue revenue revenue") for i in range(10)]
    results = search_filing_nodes(nodes, "revenue", top_k=3)
    assert len(results) == 3


def test_ties_broken_by_node_id():
    nodes = [
        _node("n9", "revenue figures"),
        _node("n2", "revenue figures"),
    ]
    results = search_filing_nodes(nodes, "revenue", top_k=5)
    assert [r["node_id"] for r in results] == ["n2", "n9"]


def test_tool_schema_shape():
    assert SEARCH_TOOL_SCHEMA["type"] == "function"
    assert SEARCH_TOOL_SCHEMA["function"]["name"] == "search_filing"
    assert "query" in SEARCH_TOOL_SCHEMA["function"]["parameters"]["properties"]
