from app.core.config import get_settings
from app.pipeline.parsing.jtxml_parser import Characteristic, ParsedJtxml, parse_jtxml_bytes
from app.pipeline.rules import (
    direction_rules,
    naming_rules,
    nominal_rules,
    template_rules,
    tolerance_rules,
    wording_rules,
)
from app.pipeline.rules.engine import run_rules


def P(*chars, part="PART A", model="M1", template="Beta 3"):
    return ParsedJtxml(part, model, template, list(chars))


def C(**kw):
    base = dict(id="C1", name="n", nominal=10.0, upper_tol=0.2, lower_tol=-0.2, unit="mm", direction="X", description="CHECK IT")
    base.update(kw)
    return Characteristic(**base)


def codes(findings):
    return {f.rule for f in findings}


def test_clean_input_has_no_findings(good_bytes):
    assert run_rules(parse_jtxml_bytes(good_bytes), get_settings()) == []


def test_template_beta3_ok_beta2_rejected_missing_unknown():
    assert template_rules.check(P(C())) == []
    f = template_rules.check(P(C(), template="Beta 2"))
    assert codes(f) == {"TPL001"} and f[0].severity == "critical"
    assert codes(template_rules.check(P(C(), template="beta-3"))) == set()
    assert codes(template_rules.check(P(C(), template=None))) == {"TPL002"}
    assert codes(template_rules.check(P(C(), template="Beta 4"))) == {"TPL003"}


def test_tolerance_rules():
    assert codes(tolerance_rules.check(P(C(upper_tol=None)))) == {"TOL001"}
    assert codes(tolerance_rules.check(P(C(upper_tol=-0.1, lower_tol=-0.3)))) == {"TOL002"}
    assert codes(tolerance_rules.check(P(C(upper_tol=0.3, lower_tol=0.1)))) == {"TOL003"}
    assert codes(tolerance_rules.check(P(C(upper_tol=0, lower_tol=0)))) == {"TOL004"}
    assert codes(tolerance_rules.check(P(C(upper_tol=0.3, lower_tol=-0.1)))) == {"TOL005"}
    assert codes(tolerance_rules.check(P(C(nominal=1.0, upper_tol=0.5, lower_tol=-0.5)))) == {"TOL006"}
    assert tolerance_rules.check(P(C(upper_tol=0.3, lower_tol=0.0))) == []


def test_nominal_rules():
    assert codes(nominal_rules.check(P(C(nominal=None, raw_nominal="abc")))) == {"NOM001"}
    assert codes(nominal_rules.check(P(C(), C()))) == {"NOM002"}
    assert codes(nominal_rules.check(P(C(id=None)))) == {"NOM004"}
    assert codes(nominal_rules.check(P(C(id="a"), C(id="b", nominal=11.0)))) == {"NOM003"}


def test_wording_rules():
    assert codes(wording_rules.check(P(C(description="")))) == {"WRD001"}
    assert codes(wording_rules.check(P(C(description="TBD")))) == {"WRD002"}
    assert codes(wording_rules.check(P(C(description="ok")))) == {"WRD004"}
    assert codes(wording_rules.check(P(C(description="CHECK  IT ")))) == {"WRD003"}


def test_direction_rules():
    assert codes(direction_rules.check(P(C(direction=None)))) == {"DIR001"}
    assert codes(direction_rules.check(P(C(direction="Q")))) == {"DIR002"}
    assert codes(direction_rules.check(P(C(direction="x")))) == {"DIR003"}
    assert direction_rules.check(P(C(direction="XYZ"))) == []


def test_naming_rules():
    assert codes(naming_rules.check(P(C(), part=None))) == {"NAMP1"}
    assert codes(naming_rules.check(P(C(), model=""))) == {"NAMM1"}
    assert codes(naming_rules.check(P(C(), part="BAD<NAME>"))) == {"NAMP2"}


def test_engine_sorts_by_severity(bad_bytes):
    findings = run_rules(parse_jtxml_bytes(bad_bytes), get_settings())
    order = ["critical", "error", "warning", "info"]
    assert [order.index(f.severity) for f in findings] == sorted(order.index(f.severity) for f in findings)
    assert findings[0].rule == "TPL001"
