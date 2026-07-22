from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import json

import pytest

import pipelines.structural.build_summary_index as bsi


@pytest.mark.asyncio
async def test_build_index_for_document_skips_if_final_dir_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)
    (tmp_path / "AAPL_2025").mkdir()

    result = await bsi.build_index_for_document("AAPL_2025")

    assert result == {"document_id": "AAPL_2025", "skipped": True}


@pytest.mark.asyncio
async def test_build_index_for_document_builds_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)

    fake_nodes = [{"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
                   "parent_item_header": None, "node_type": "text",
                   "source_page_num": None, "content": "hello", "token_count": 1}]

    fake_index = MagicMock()

    def fake_persist(persist_dir):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        (Path(persist_dir) / "docstore.json").write_text("{}")

    fake_index.storage_context.persist.side_effect = fake_persist

    with patch.object(bsi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)), \
         patch.object(bsi, "TreeIndex", return_value=fake_index) as mock_tree, \
         patch.object(bsi, "Groq"):
        result = await bsi.build_index_for_document("AAPL_2025")

    assert result["document_id"] == "AAPL_2025"
    assert result["skipped"] is False
    assert (tmp_path / "AAPL_2025" / "docstore.json").exists()
    assert not (tmp_path / "AAPL_2025.tmp").exists()
    mock_tree.assert_called_once()


@pytest.mark.asyncio
async def test_build_index_for_document_crash_leaves_only_temp_dir(tmp_path, monkeypatch):
    """A crash between persist() and the atomic rename must never leave a
    false-positive cache hit -- the final dir must stay absent."""
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)

    fake_nodes = [{"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
                   "parent_item_header": None, "node_type": "text",
                   "source_page_num": None, "content": "hello", "token_count": 1}]

    fake_index = MagicMock()

    def fake_persist(persist_dir):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

    fake_index.storage_context.persist.side_effect = fake_persist

    with patch.object(bsi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)), \
         patch.object(bsi, "TreeIndex", return_value=fake_index), \
         patch.object(bsi, "Groq"), \
         patch.object(bsi.os, "rename", side_effect=OSError("simulated crash")):
        with pytest.raises(OSError):
            await bsi.build_index_for_document("AAPL_2025")

    assert (tmp_path / "AAPL_2025.tmp").exists()
    assert not (tmp_path / "AAPL_2025").exists()
    assert bsi.is_built("AAPL_2025") is False


@pytest.mark.asyncio
async def test_build_index_for_document_cleans_stale_temp_dir_before_retry(tmp_path, monkeypatch):
    """A leftover temp dir from a prior crashed build must not break the next attempt."""
    monkeypatch.setattr(bsi, "STORAGE_ROOT", tmp_path)
    stale_temp = tmp_path / "AAPL_2025.tmp"
    stale_temp.mkdir()
    (stale_temp / "leftover.json").write_text("{}")

    fake_nodes = [{"node_id": "AAPL_2025_n0001", "document_id": "AAPL_2025",
                   "parent_item_header": None, "node_type": "text",
                   "source_page_num": None, "content": "hello", "token_count": 1}]

    fake_index = MagicMock()

    def fake_persist(persist_dir):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        (Path(persist_dir) / "docstore.json").write_text("{}")

    fake_index.storage_context.persist.side_effect = fake_persist

    with patch.object(bsi.dbm, "get_nodes_by_document", new=AsyncMock(return_value=fake_nodes)), \
         patch.object(bsi, "TreeIndex", return_value=fake_index), \
         patch.object(bsi, "Groq"):
        result = await bsi.build_index_for_document("AAPL_2025")

    assert result["skipped"] is False
    assert (tmp_path / "AAPL_2025" / "docstore.json").exists()
    assert not (tmp_path / "AAPL_2025.tmp").exists()


def test_append_cost_log_creates_and_appends(tmp_path):
    log_path = tmp_path / "logs" / "index_build_costs.json"
    bsi.append_cost_log(
        {"document_id": "AAPL_2025", "skipped": False, "wall_clock_sec": 1.0,
         "input_tokens": 10, "output_tokens": 5},
        log_path=log_path,
    )
    bsi.append_cost_log({"document_id": "AAPL_2024", "skipped": True}, log_path=log_path)

    rows = json.loads(log_path.read_text())
    assert len(rows) == 2
    assert rows[0]["document_id"] == "AAPL_2025"
    assert rows[1]["skipped"] is True
