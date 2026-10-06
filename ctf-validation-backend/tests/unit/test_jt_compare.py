
import pytest

from app.core.exceptions import UnprocessableError
from app.pipeline.parsing.ctf_parser import parse_ctf
from app.pipeline.parsing.plmxml_parser import parse_plmxml_bytes
from app.pipeline.rules.jt_rules import compare, summarize
from tests.unit.test_tolerance_transfer import make_ctf

PLMXML = b"""<?xml version="1.0" encoding="utf-8"?>
<PLMXML xmlns="http://www.plmxml.org/Schemas/PLMXMLSchema" schemaVersion="6">
<ProductDef id="id1"><UserData id="id2" type="__TCC-VIS_MONIKER_INFO">
<UserValue title="PLMItemIdStr" value="FC00AAV44383"></UserValue>
<UserValue title="PLMRevisionStr" value="015.0005"></UserValue>
<UserValue title="PLMObjectName" value="FC00AAV44383.015.0005.GEO_FIN_JT001.JT"></UserValue></UserData>
<InstanceGraph id="id3"><ProductInstance id="inst6" name="FC00AAV44383_015_0005-GUIDE PARKING BRAKE CABLE__PART"/>
<ProductRevisionView id="id5"><Bound id="id8" values="1 2 3 4 5 6"/></ProductRevisionView></InstanceGraph></ProductDef></PLMXML>"""
ROW = [("CTF", "01A01", "Size tolerance of the Datum A", 0, -0.1, 0.1)]


def by_id(checks):
    return {c.id: c for c in checks}


def test_plmxml_parse():
    m = parse_plmxml_bytes(PLMXML)
    assert (m.item_id, m.revision, m.product_name) == ("FC00AAV44383", "015.0005", "GUIDE PARKING BRAKE CABLE")
    assert m.bounds == [1, 2, 3, 4, 5, 6]


@pytest.mark.parametrize("data", [b"<broken", b"<Other/>", b'<PLMXML xmlns="x"/>'])
def test_plmxml_rejects_bad_input(data):
    with pytest.raises(UnprocessableError):
        parse_plmxml_bytes(data)


def test_matching_ctf_passes(tmp_path):
    ctf = parse_ctf(make_ctf(tmp_path / "a.xlsx", ROW, drawing="FC00AAV44383", indice="015.0005", name="Guide parking-brake cable"))
    checks = by_id(compare(ctf, parse_plmxml_bytes(PLMXML)))
    assert (checks["JT001"].status, checks["JT003"].status, checks["JT004"].status) == ("pass", "pass", "pass")
    assert "JT002" not in checks and summarize(list(checks.values()))["verdict"] == "pass"


def test_different_part_fails_and_flags_stale_psa_ref(tmp_path):
    ctf = parse_ctf(make_ctf(tmp_path / "b.xlsx", ROW, drawing="68341437AG_FC00ACE32298", indice="AA", name="MODULE AUXILIARY LIGHTING"))
    ctf.front["part_ref"] = "68789063AA"
    checks = by_id(compare(ctf, parse_plmxml_bytes(PLMXML)))
    assert checks["JT001"].status == "fail" and "FC00ACE32298" in checks["JT001"].message
    assert checks["JT002"].status == "warn" and "68341437AG" in checks["JT002"].message
    assert checks["JT003"].status == "fail" and checks["JT004"].status == "info"
    assert summarize(list(checks.values()))["verdict"] == "fail"


def test_missing_values_are_reported(tmp_path):
    ctf = parse_ctf(make_ctf(tmp_path / "c.xlsx", ROW, drawing="FC00AAV44383"))
    checks = by_id(compare(ctf, parse_plmxml_bytes(PLMXML)))
    assert checks["JT004"].status == "warn"  # no indice
    ctf.front["drawing_ref"] = FRONT = None
    assert by_id(compare(ctf, parse_plmxml_bytes(PLMXML)))["JT001"].status == "fail"


def test_compare_api(client, tmp_path):
    ctf = make_ctf(tmp_path / "ctf.xlsx", ROW, drawing="FC00AAV44383", indice="015.0005", name="GUIDE PARKING BRAKE CABLE")
    c = client.post("/api/v1/upload/ctf", files={"file": ("ctf.xlsx", ctf.read_bytes())}).json()["file_id"]
    j = client.post("/api/v1/upload/jtxml", files={"file": ("part.plmxml", PLMXML)})
    assert j.status_code == 201
    r = client.post("/api/v1/compare", json={"ctf_file_id": c, "jtxml_file_id": j.json()["file_id"]})
    assert r.status_code == 200 and r.json()["summary"]["verdict"] == "pass"
    assert client.post("/api/v1/compare", json={"ctf_file_id": j.json()["file_id"], "jtxml_file_id": c}).status_code == 404
