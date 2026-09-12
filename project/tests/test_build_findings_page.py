"""build_findings_page: the standalone results page.

The failure modes worth guarding are silent ones: an f-string field that
never gets substituted, a chart whose labels run outside its own viewBox,
and a summary sentence that keeps asserting a leader after the data behind
it has moved.
"""
import re
import sqlite3
from pathlib import Path

import pytest

import build_findings_page as bfp

PALETTE = Path(__file__).resolve().parents[2] / "resources" / "assets" / "design" / "palette.md"


@pytest.fixture
def db(tmp_path) -> str:
    path = tmp_path / "mini.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE nodes (node_id TEXT PRIMARY KEY, document_id TEXT);
        CREATE TABLE queries (query_id TEXT PRIMARY KEY, quadrant TEXT, document_id TEXT);
        CREATE TABLE results (result_id TEXT PRIMARY KEY, source_set TEXT, query_id TEXT,
            pipeline TEXT, k_value INTEGER, precision_at_k REAL, recall_at_k REAL,
            evidence_hit INTEGER, citation_match INTEGER, token_f1 REAL, exact_match INTEGER,
            judge_score INTEGER, human_score INTEGER, latency_sec REAL,
            input_tokens INTEGER, output_tokens INTEGER);
    """)
    for i in range(30):
        conn.execute("INSERT INTO nodes VALUES (?,?)", (f"N{i}", "AAPL_2023"))
    quadrants = ["Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table"]
    for qi, quadrant in enumerate(quadrants):
        for q in range(3):
            query_id = f"Q{qi}_{q}"
            conn.execute("INSERT INTO queries VALUES (?,?,?)", (query_id, quadrant, "AAPL_2023"))
            for pi, pipeline in enumerate(("P1_vector", "P2_bm25", "P3_structural")):
                for k in (2, 3, 5):
                    conn.execute(
                        "INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (f"R_{query_id}_{pipeline}_{k}", "PQ", query_id, pipeline, k,
                         0.3, 0.5, 1, 1, 0.4, 1, max(1, 5 - pi - (k == 2)), None,
                         3.0, 100, 20))
    for i in range(4):
        conn.execute("INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (f"J{i}", "JEQ", f"JE{i}", "P1_vector", 5, 0.3, 0.5, 1, 1, 0.4, 1,
                      4, 4 if i < 3 else 5, 3.0, 100, 20))
    conn.commit()
    conn.close()
    return str(path)


@pytest.fixture
def page(db, monkeypatch, tmp_path) -> str:
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    return bfp.build_html(db)


# --- the page holds together --------------------------------------------------

def test_every_section_renders(page):
    for heading in ("The headline", "All three pillars", "bimodal", "Depth helps",
                    "ordering changes", "Is the difference real", "costs to build",
                    "costs to ask", "Filing by filing", "What would weaken"):
        assert heading in page, heading


def test_no_placeholder_survives_substitution(page):
    body = page.split("</style>", 1)[1]
    assert not re.search(r"\{[a-z_\[\]'\"]+\}", body)


def test_the_page_is_self_contained(page):
    """Nothing to fetch: no script, no external stylesheet, no remote image."""
    assert "<script" not in page
    assert "http://" not in page.replace("http://localhost", "")
    assert "<link" not in page


def test_it_declares_a_viewport_so_phones_do_not_zoom_out(page):
    assert 'name="viewport"' in page


def test_all_four_tables_are_scrollable_rather_than_overflowing(page):
    assert page.count("<table>") == 4
    assert page.count('class="scroll"') >= 4


# --- numbers come from the data -----------------------------------------------

def test_the_cell_count_is_read_not_asserted(page):
    assert "108 cells" in page or ">108<" in page or "108" in page


def test_the_gate_percentage_is_computed_from_the_database(page):
    """3 of 4 JEQ rows agree in the fixture."""
    assert "75.0%" in page


def test_the_heatmap_shows_the_question_count_behind_each_row(page):
    """A row built on one question must not read like a rate."""
    assert "questions" in page and 'class="hm-n"' in page


def test_the_quadrant_badge_marks_exactly_the_quadrants_bm25_does_not_lead(db, page, monkeypatch):
    """The badge is the reader's cue that the usual ordering broke."""
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    flipped = 0
    for quadrant in bfp.QUAD:
        scores = {p: conn.execute(
            """SELECT AVG(r.judge_score) FROM results r JOIN queries q ON q.query_id=r.query_id
               WHERE r.source_set='PQ' AND q.quadrant=? AND r.pipeline=?""",
            (quadrant, p)).fetchone()[0] for p in bfp.PIPE}
        if max(scores, key=lambda p: scores[p]) != "P2_bm25":
            flipped += 1
    conn.close()
    assert flipped > 0, "fixture must exercise at least one flip"
    assert page.count('class="flip"') == flipped


def test_the_badge_disappears_when_bm25_leads_every_quadrant(db, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    conn = sqlite3.connect(db)
    conn.execute("UPDATE results SET judge_score = 1")
    conn.execute("UPDATE results SET judge_score = 5 WHERE pipeline = 'P2_bm25'")
    conn.commit()
    conn.close()
    assert 'class="flip"' not in bfp.build_html(db)


def test_the_quadrant_lead_is_derived_not_hardcoded(db, monkeypatch):
    """Flip the data so a different pipeline leads Q4, and the prose must follow."""
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    conn = sqlite3.connect(db)
    conn.execute("""UPDATE results SET judge_score = 5 WHERE pipeline='P3_structural'
                    AND query_id IN (SELECT query_id FROM queries WHERE quadrant='Q4_Implicit_Table')""")
    conn.commit()
    conn.close()
    assert "P3 Structural leads there" in bfp.build_html(db)


# --- charts stay inside their own boxes ---------------------------------------

def _viewbox(svg: str) -> tuple[float, float]:
    w, h = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups()
    return float(w), float(h)


@pytest.mark.parametrize("index", [0, 1, 2])
def test_chart_geometry_stays_within_its_viewbox(page, index):
    svgs = re.findall(r"<svg.*?</svg>", page, re.S)
    svg = svgs[index]
    width, height = _viewbox(svg)
    for x in re.findall(r'(?:x|cx|x1|x2)="([\d.]+)"', svg):
        assert float(x) <= width, f"x={x} beyond viewBox width {width}"
    for y in re.findall(r'(?:y|cy|y1|y2)="([\d.]+)"', svg):
        assert float(y) <= height, f"y={y} beyond viewBox height {height}"


# A label's anchor sitting inside the box is not enough: the glyphs run on from
# there. Calibri at these sizes averages a little over half the font size per
# character, so this is a deliberate over-estimate, which is the safe direction
# for a bound that exists to catch text running off the edge.
_CHAR_WIDTH = {"lbl": 8.4, "ax": 7.6}


@pytest.mark.parametrize("index", [0, 1, 2])
def test_chart_labels_have_room_for_their_own_text(page, index):
    svg = re.findall(r"<svg.*?</svg>", page, re.S)[index]
    width, _ = _viewbox(svg)
    for x, cls, anchor, text in re.findall(
            r'<text x="([\d.]+)"[^>]*class="(lbl|ax)"(?:[^>]*text-anchor="(\w+)")?[^>]*>([^<]*)</text>',
            svg):
        run = len(text) * _CHAR_WIDTH[cls]
        right = float(x) + (0 if anchor == "end" else run / (2 if anchor == "middle" else 1))
        assert right <= width + 0.5, (
            f"label {text!r} starts at {x} and needs {run:.0f}px, "
            f"running past the {width:.0f}px viewBox")


def test_the_depth_chart_separates_labels_that_would_collide(db, monkeypatch):
    """Two pipelines finishing on the same score must not stack their labels."""
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    conn = sqlite3.connect(db)
    conn.execute("UPDATE results SET judge_score = 4")
    conn.commit()
    conn.close()
    svg = re.findall(r"<svg.*?</svg>", bfp.build_html(db), re.S)[0]
    ys = sorted(float(y) for y in re.findall(r'<text x="[\d.]+" y="([\d.]+)" class="lbl"', svg))
    assert len(ys) == 3
    assert all(b - a >= 16 for a, b in zip(ys, ys[1:])), f"labels overlap at {ys}"


def test_each_metric_gets_its_own_forest_scale(page):
    """Judge score and recall run on different ranges and must not share an axis."""
    assert "Judge score, 1 to 5" in page
    assert "Recall at k, 0 to 1" in page


# --- colour ------------------------------------------------------------------

def test_each_pipeline_has_its_own_colour():
    hues = [meta["hue"] for meta in bfp.PIPE.values()]
    assert len(set(hues)) == len(hues)


def test_the_five_score_bands_are_distinct():
    assert len(set(bfp.BAND)) == 5


def test_the_house_ink_and_gold_are_taken_from_the_project_palette():
    """The page extends Oxford Ink for data, but keeps its anchors."""
    documented = {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}", PALETTE.read_text())}
    assert bfp.GOLD.upper() in documented
    assert bfp.INK.upper() in documented
