import pytest

from app.core.exceptions import UnprocessableError
from app.pipeline.parsing.jtxml_parser import parse_jtxml_bytes


def test_parses_header_and_characteristics(good_bytes):
    p = parse_jtxml_bytes(good_bytes)
    assert (p.part_name, p.model_name, p.template_version) == ("BRACKET FRONT LH", "MODEL-X1", "Beta 3")
    assert len(p.characteristics) == 3
    c = p.characteristics[0]
    assert (c.id, c.nominal, c.upper_tol, c.lower_tol, c.direction) == ("C1", 10.0, 0.2, -0.2, "X")


def test_root_version_attribute_is_not_template_version():
    p = parse_jtxml_bytes(b'<JTXML version="1.0"><Characteristic id="a"/></JTXML>')
    assert p.template_version is None


def test_non_numeric_nominal_is_none_but_raw_kept(bad_bytes):
    c = parse_jtxml_bytes(bad_bytes).characteristics[0]
    assert c.nominal is None and c.raw_nominal == "abc"


def test_attribute_style_comma_decimal_and_plus_minus():
    xml = b'<R><Feature id="1" nominal="10,5" tol="x" upper="\xc2\xb10,2"/></R>'
    c = parse_jtxml_bytes(xml).characteristics[0]
    assert c.nominal == 10.5 and (c.upper_tol, c.lower_tol) == (0.2, -0.2)


def test_invalid_xml_and_empty_raise():
    with pytest.raises(UnprocessableError):
        parse_jtxml_bytes(b"<not-closed")
    with pytest.raises(UnprocessableError):
        parse_jtxml_bytes(b"<JTXML/>")


def test_external_entities_not_resolved():
    xml = b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r><Characteristic id="a"><Description>&x;</Description></Characteristic></r>'
    c = parse_jtxml_bytes(xml).characteristics[0]
    assert "root:" not in (c.description or "")
