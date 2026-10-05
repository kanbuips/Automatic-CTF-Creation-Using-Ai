"""Run:  cd backend && pytest -q

The model call is replaced by FakeLLM (tests/ip_switch_fixture.py) so tests need no API key.

Tests that need the real template / drawing are skipped when the files are not present:
  backend/templates/CTF_PIS_template.xlsm   (your CTF & PIS template)
  backend/tests/fixtures/drawing.pdf         (any drawing, e.g. FC00ABV93668)
"""
import os
import time
import zipfile
from pathlib import Path

import pytest

from app.evaluate import score                               # noqa: E402
from app.excel.template import load_profile, read_rows       # noqa: E402
from app.pipeline.directions import assign_directions        # noqa: E402
from app.pipeline import runner                              # noqa: E402
from app.pipeline.rows import build_rows, classify           # noqa: E402
from app.pipeline.vision import capability_from_notes        # noqa: E402
from app.settings import get_settings                        # noqa: E402
from ip_switch_fixture import CALLOUTS, TITLE, VIEWS, FakeLLM  # noqa: E402

runner.make_llm = lambda settings: FakeLLM()                 # no API calls in tests

S = get_settings()
RULES = S.rules
HERE = Path(__file__).parent
TEMPLATE = S.template_path
DRAWING = HERE / "fixtures" / "drawing.pdf"
needs_template = pytest.mark.skipif(not TEMPLATE.exists(), reason="template not present")


def _rows():
    callouts = [c.model_copy() for c in CALLOUTS]
    assign_directions(callouts, VIEWS, RULES["view_directions"])
    return build_rows(classify(callouts, RULES), TITLE, RULES)


def test_directions_follow_parent_views():
    callouts = [c.model_copy() for c in CALLOUTS]
    assign_directions(callouts, VIEWS, RULES["view_directions"])
    by_text = {c.text: c.direction for c in callouts}
    assert by_text["16.65 ±0.2"] == "U/D"            # SECTION A-A -> DETAIL Z -> REAR VIEW, vertical
    assert by_text["15.1 ±0.1"] == "C/C"             # DETAIL Z, horizontal
    assert by_text["29.62 ±0.5"] == "F/A"            # RIGHT VIEW, horizontal
    assert by_text["PROFILE 0.5 |A|B|C| (left)"] == "surface"


def test_rules_exclude_non_characteristics():
    dec = {d.callout.text: d for d in classify(CALLOUTS, RULES)}
    assert dec["26.95"].group is None                 # basic dimension
    assert dec["F2 11 ±3.5 N"].group is None          # force, not a length
    assert dec["MAX. 14.5 SLIDING STROKE"].group is None
    assert dec["PROFILE 0.5 |A|B|C| (right)"].group == "gap"


def test_rows_match_team_format():
    rows = _rows()
    assert len(rows) == 29
    assert [r.code for r in rows[:3]] == ["01A01", "01A02", "01A03"]      # datum rows first
    assert rows[9].code == "01A010"                                         # team code style after 9
    gap = [r for r in rows if r.function_l2 == "To Ensure the Gap"]
    assert [r.code for r in gap] == ["01B01", "01B02", "01B03"]
    assert all(r.lsl == -0.25 and r.usl == 0.25 and r.cp == 1.33 and r.priority == "High" for r in gap)
    four_x = [r for r in rows if "4X" in r.wording]
    assert len(four_x) == 2 and four_x[0].wording == "Size Tolerance in U/D direction 4X places"


def test_score_multiset():
    rows = _rows()
    expected = [{"direction": r.direction, "tol": r.tolerance, "count": r.count} for r in rows]
    sc = score(rows, expected)
    assert sc.recall == 1.0 and sc.precision == 1.0
    sc = score(rows, expected[:-1] + [{"direction": "F/A", "tol": 9, "count": 1}])
    assert sc.matched == 28 and sc.missing == ["F/A ±9"] and len(sc.extra) == 1


def test_capability_note():
    assert capability_from_notes(["MEASUREMENT POINT ... MUST BE CAPABLE OF PPK>1.33"]) == 1.33
    assert capability_from_notes(["CPK >= 1,67 REQUIRED"]) == 1.67
    assert capability_from_notes(["NO NOTE"]) is None


@needs_template
def test_template_profile():
    p = load_profile(TEMPLATE, RULES)
    assert p.header_row == 29 and p.first_row == 30
    assert p.columns["code"] == "F" and p.columns["usl"] == "R"
    assert {"S", "T"} <= p.formula_columns
    assert "Urgent" in p.enums["priority"] and "CTF" in p.enums["type"]
    assert not p.missing_fields


@needs_template
def test_writer_keeps_package_and_formulas(tmp_path):
    from app.excel.writer import write_workbook

    p = load_profile(TEMPLATE, RULES)
    rows = _rows()
    out = write_workbook(p, rows, TITLE, tmp_path / "out.xlsm")
    a, b = zipfile.ZipFile(TEMPLATE), zipfile.ZipFile(out)
    assert set(a.namelist()) == set(b.namelist())                         # nothing dropped
    changed = {n for n in a.namelist() if a.read(n) != b.read(n)}
    assert changed <= {"xl/workbook.xml", "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"}
    back = read_rows(out, p)
    assert len(back) == 29 and back[0]["code"] == "01A01" and back[-1]["wording"] == "Surface Tolerance"
    import openpyxl

    ws = openpyxl.load_workbook(out)["CTF & PIS"]
    assert str(ws["S30"].value).startswith("=")                          # formula untouched


@needs_template
def test_full_run_through_vision_code(tmp_path):
    if not DRAWING.exists():
        pytest.skip("fixtures/drawing.pdf not present")
    res = runner.run(DRAWING, tmp_path / "out.xlsm", S)
    assert len(res.views) == 10 and len(res.rows) == 29
    assert res.title.capability_target == 1.33
    assert res.llm_calls >= 5                                  # 1 layout + one call per sheet tile
    assert len(res.callouts) == len(CALLOUTS)                  # overlapping tiles de-duplicated, none lost
    by_text = {c.text: c.view for c in res.callouts}
    assert by_text["13.9 ±0.1"] == "DETAIL Z"                  # assigned to its view by position
    assert any("S31" in i for i in res.issues)                 # template formula anomaly is reported


@needs_template
def test_api_end_to_end():
    if not DRAWING.exists():
        pytest.skip("fixtures/drawing.pdf not present")
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    assert c.get("/api/health").json()["template_ok"]
    r = c.post("/api/jobs", files={"drawing": ("drawing.pdf", DRAWING.read_bytes(), "application/pdf")},
               data={"project_code": "30 DV"})
    assert r.status_code == 201
    jid = r.json()["id"]
    for _ in range(60):
        job = c.get(f"/api/jobs/{jid}").json()
        if job["state"] in ("done", "failed"):
            break
        time.sleep(0.5)
    assert job["state"] == "done", job.get("error")
    assert job["row_count"] == 29
    assert c.get(f"/api/jobs/{jid}/rows").json()["rows"][0]["code"] == "01A01"
    dl = c.get(f"/api/jobs/{jid}/download")
    assert dl.status_code == 200 and dl.content[:2] == b"PK"
    sc = c.post(f"/api/jobs/{jid}/score", files={"answer_key": ("key.xlsm", TEMPLATE.read_bytes())}).json()
    assert sc["expected"] == 29 and sc["matched"] >= 25
    assert c.delete(f"/api/jobs/{jid}").status_code == 204


@needs_template
def test_picture_sheet_rebuilt(tmp_path):
    if not DRAWING.exists():
        pytest.skip("fixtures/drawing.pdf not present")
    from lxml import etree

    res = runner.run(DRAWING, tmp_path / "out.xlsm", S)
    z = zipfile.ZipFile(res.output)
    media = [n for n in z.namelist() if "ctf_studio_" in n]
    assert len(media) == 3                                     # Rear+Right, Front, Detail Z+Section A-A
    drawing = etree.fromstring(z.read("xl/drawings/drawing5.xml"))
    texts = [t.text for t in drawing.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t")]
    codes = {r.code for r in res.rows}
    assert codes <= set(texts)                                 # every CTF code has a yellow label
    assert "Creation of a tolerance frame" in texts            # macro buttons kept
    assert "Search an identification code" in texts
    assert not any(n.startswith("Picture 4") for n in
                   (e.get("name") or "" for e in drawing.iter(
                       "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}cNvPr")))


@needs_template
def test_picture_pages_follow_template_layout():
    from lxml import etree

    from app.excel.writer import pages_from_sheet

    z = zipfile.ZipFile(TEMPLATE)
    sheet = z.read("xl/worksheets/sheet6.xml")
    drawing = etree.fromstring(z.read("xl/drawings/drawing5.xml"))
    # IP template: print area A1:R55 = one page, repeated over the used range
    assert pages_from_sheet(z, "xl/worksheets/sheet6.xml", sheet, drawing)[0] == [1, 5, 18, 55]
    # a template with manual page breaks (solid lines in Page Break Preview) uses the breaks
    broken = sheet.replace(b"<drawing ", b'<rowBreaks count="1" manualBreakCount="1"><brk id="55" max="16383" '
                           b'man="1"/></rowBreaks><colBreaks count="1" manualBreakCount="1"><brk id="18" '
                           b'max="1048575" man="1"/></colBreaks><drawing ', 1)
    pages = pages_from_sheet(z, "xl/worksheets/sheet6.xml", broken, drawing)
    assert len(pages) == 4 and pages[1][1] > 55                 # down, then over


@needs_template
def test_harvest_training_data_from_approved_file(tmp_path):
    """The approved file's #Picture sheet is turned into labelled training data."""
    if not DRAWING.exists():
        pytest.skip("fixtures/drawing.pdf not present")
    from tools.harvest import harvest, norm_code

    assert norm_code("01A10") == norm_code("01A010") == "01A10"
    res = runner.run(DRAWING, tmp_path / "run.xlsm", S)
    callouts = [c.model_dump() for c in res.callouts]
    data = harvest(TEMPLATE, DRAWING, tmp_path / "h", callouts)
    assert data["labels_found"] >= 27 and data["codes_with_row"] >= 25
    assert all(p["on_drawing"] and p["on_drawing"][1] > 0.7 for p in data["pictures"]
               if p["name"] in ("Picture 464", "Picture 472"))              # crops found on the drawing
    by = {l["label"]: l.get("callout", {}).get("text") for l in data["labels"]}
    assert by["01A16"] == "5.08 ±0.1 (4X)" and by["01A20"] == "2.32 ±0.1 (5X)"
    assert by["01B03"].startswith("PROFILE 0.5")
    assert data["codes_paired_to_callout"] >= 20
    assert (tmp_path / "h" / "yolo" / "data.yaml").exists()


@needs_template
def test_replay_and_picture_score(tmp_path):
    """A saved run can be replayed offline, and its #Picture scored against the approved sheet."""
    if not DRAWING.exists():
        pytest.skip("fixtures/drawing.pdf not present")
    from tools.evaluate_pictures import evaluate

    first = runner.run(DRAWING, tmp_path / "a.xlsm", S)
    saved = {"views": [v.model_dump() for v in first.views], "title": first.title.model_dump(),
             "callouts": [c.model_dump() for c in first.callouts]}
    runner.make_llm = lambda s: (_ for _ in ()).throw(AssertionError("replay must not call the model"))
    try:
        again = runner.run(DRAWING, tmp_path / "b.xlsm", S, replay=saved)
    finally:
        runner.make_llm = lambda settings: FakeLLM()
    assert len(again.rows) == len(first.rows)
    sc = evaluate(again.output, TEMPLATE, DRAWING)
    assert sc["team_codes_inside_our_crops"] == "27/27"
