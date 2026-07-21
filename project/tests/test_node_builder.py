import ingest.node_builder as node_builder

SAMPLE_MARKDOWN = """# Item 1A. Risk Factors

Our business faces intense competition from other companies.

Weather conditions could adversely affect our operations.

# Item 8. Financial Statements

| Year | Net Sales |
|------|-----------|
| 2025 | 394328    |
| 2024 | 383285    |

Some closing narrative after the table.
"""


def test_build_nodes_returns_correct_keys():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    assert len(nodes) > 0
    expected_keys = {"node_id", "document_id", "parent_item_header", "node_type", "source_page_num", "content", "token_count"}
    for node in nodes:
        assert set(node.keys()) == expected_keys


def test_build_nodes_assigns_sequential_node_ids():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    ids = [n["node_id"] for n in nodes]
    assert ids[0] == "AAPL_2025_n0001"
    assert ids[1] == "AAPL_2025_n0002"
    assert ids == sorted(ids)


def test_build_nodes_tracks_parent_item_header():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    risk_nodes = [n for n in nodes if "competition" in n["content"]]
    assert len(risk_nodes) == 1
    assert risk_nodes[0]["parent_item_header"] == "Item 1A. Risk Factors"

    financial_nodes = [n for n in nodes if "closing narrative" in n["content"]]
    assert len(financial_nodes) == 1
    assert financial_nodes[0]["parent_item_header"] == "Item 8. Financial Statements"


def test_build_nodes_keeps_table_atomic():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    table_nodes = [n for n in nodes if n["node_type"] == "table"]
    assert len(table_nodes) == 1
    assert "394328" in table_nodes[0]["content"]
    assert "383285" in table_nodes[0]["content"]
    assert "Year" in table_nodes[0]["content"]


def test_build_nodes_classifies_text_vs_table():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    types = {n["node_type"] for n in nodes}
    assert types == {"text", "table"}


def test_build_nodes_document_id_and_page_num():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    for node in nodes:
        assert node["document_id"] == "AAPL_2025"
        assert node["source_page_num"] is None


def test_build_nodes_token_count_is_positive():
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, SAMPLE_MARKDOWN)
    for node in nodes:
        assert node["token_count"] > 0
        assert node["token_count"] == len(node["content"].split())


CAPTIONED_TABLE_MARKDOWN = """# Item 15. Exhibit and Financial Statement Schedules

Incorporated by Reference
| Exhibit Number | Exhibit Description |
|-----------------|----------------------|
| 3.1             | Articles of Incorporation |
| 3.2             | Bylaws |
"""


def test_build_nodes_classifies_captioned_table_as_table():
    """A real AAPL_2025 filing node was found with a caption line directly
    above a table's rows (no blank line separating them) -- the original
    first-line-only check misclassified this as text. Confirmed live in
    Phase 2 Task 6; see resources/artifacts/Changes.md."""
    nodes = node_builder.build_nodes("AAPL_2025", "AAPL", 2025, CAPTIONED_TABLE_MARKDOWN)
    table_nodes = [n for n in nodes if n["node_type"] == "table"]
    assert len(table_nodes) == 1
    assert "Incorporated by Reference" in table_nodes[0]["content"]
    assert "Articles of Incorporation" in table_nodes[0]["content"]
