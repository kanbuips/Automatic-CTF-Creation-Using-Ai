"""Test fixture: what a correct vision model returns for drawing FC00ABV93668 (IP switch bank),
transcribed by hand from the drawing. Used ONLY by the tests through FakeLLM, so every stage after the
model call (directions, rules, rows, template writing, API) is tested without an API key.
The application itself always calls OpenAI.
"""
import re

from app.pipeline.llm import LLM
from app.schemas import Callout, TitleBlock, View

VIEWS = [
    View(name="SECTION A-A", kind="section", parent_view="DETAIL Z", bbox=[0.015, 0.40, 0.12, 0.61]),
    View(name="REAR VIEW", kind="rear", parent_view=None, bbox=[0.145, 0.42, 0.315, 0.58]),
    View(name="RIGHT VIEW", kind="right", parent_view=None, bbox=[0.315, 0.42, 0.40, 0.60]),
    View(name="DETAIL Z", kind="detail", parent_view="REAR VIEW", bbox=[0.025, 0.60, 0.16, 0.73]),
    View(name="BOTTOM VIEW", kind="bottom", parent_view=None, bbox=[0.18, 0.58, 0.30, 0.68]),
    View(name="FRONT VIEW", kind="front", parent_view=None, bbox=[0.29, 0.63, 0.43, 0.78]),
    View(name="FRONT VIEW (STROKE)", kind="front", parent_view=None, bbox=[0.17, 0.69, 0.30, 0.81]),
    View(name="SLIDING BUTTON [P3]", kind="chart", parent_view=None, bbox=[0.02, 0.74, 0.16, 0.82]),
    View(name="GENERAL NOTES", kind="notes", parent_view=None, bbox=[0.28, 0.86, 0.48, 0.98]),
    View(name="MEASUREMENT POINTS", kind="table", parent_view=None, bbox=[0.42, 0.45, 0.63, 0.55]),
]

TITLE = TitleBlock(
    part_name="IP SWITCH BANK",
    drawing_reference="FC00ABV93668",
    general_notes=[
        "UNLESS OTHERWISE SPECIFIED: 1. PROFILE 1 |A|B|C| ALL FORM WITH BLENDED UNIFORMITY. "
        "2. PROFILE 1 |A|B|C| ALL TRIM EDGES. 3. ØSIZE ±0.25, POSITION Ø1 |A|B|C| ALL CIRCULAR FEATURES OF SIZE. "
        "4. SIZE ±0.2, POSITION 1 |A|B|C| ALL NON-CIRCULAR FEATURES OF SIZE.",
        "MEASUREMENT POINT THAT PERTAIN TO BUILD OBJECTIVES MUST BE CAPABLE OF PPK>1.33",
    ],
    capability_target=1.33,
)


def _c(view, kind, text, nominal=None, tol=None, count=1, orientation="none", datum_feature=None,
       geo=None, datums=(), unit="mm", conf=0.9):
    return Callout(view=view, kind=kind, text=text, nominal=nominal,
                   tol_plus=tol, tol_minus=-tol if tol is not None else None, geo_tol=geo,
                   datums=list(datums), count=count, orientation=orientation, datum_feature=datum_feature,
                   unit=unit, confidence=conf)


R, RV, Z, S, F = "REAR VIEW", "RIGHT VIEW", "DETAIL Z", "SECTION A-A", "FRONT VIEW"
CALLOUTS = [
    # rear view
    _c(R, "profile", "PROFILE 0.5 |A|B|C| (left)", geo=0.5, datums="ABC"),
    _c(R, "profile", "PROFILE 0.5 |A|B|C| (right)", geo=0.5, datums="ABC"),
    _c(R, "dimension", "23.8 ±0.3 (left)", 23.8, 0.3, orientation="horizontal"),
    _c(R, "dimension", "23.8 ±0.3 (right)", 23.8, 0.3, orientation="horizontal"),
    _c(R, "dimension", "24.22 ±0.3", 24.22, 0.3, orientation="vertical"),
    _c(R, "dimension", "10.31 ±0.3", 10.31, 0.3, orientation="vertical"),
    _c(R, "dimension", "9.45 ±0.3", 9.45, 0.3, orientation="vertical", datum_feature="B2", conf=0.7),
    _c(R, "dimension", "2.2 ±0.1 (2X)", 2.2, 0.1, count=2, orientation="vertical", datum_feature="B1",
       conf=0.55),
    _c(R, "dimension", "2.65 ±0.3", 2.65, 0.3, orientation="horizontal"),
    _c(R, "dimension", "1.5 ±0.1", 1.5, 0.1, orientation="horizontal", datum_feature="C"),
    _c(R, "basic", "26.95", 26.95),
    _c(R, "basic", "37.02", 37.02),
    # right view
    _c(RV, "dimension", "3.1 ±0.1 (2X) upper", 3.1, 0.1, count=2, orientation="horizontal"),
    _c(RV, "dimension", "3.1 ±0.1 (2X) lower", 3.1, 0.1, count=2, orientation="horizontal"),
    _c(RV, "dimension", "37.3 ±0.3", 37.3, 0.3, orientation="vertical"),
    _c(RV, "dimension", "18.85 ±0.25", 18.85, 0.25, orientation="horizontal"),
    _c(RV, "dimension", "29.62 ±0.5", 29.62, 0.5, orientation="horizontal"),
    # detail Z (2:1)
    _c(Z, "dimension", "15.1 ±0.1", 15.1, 0.1, orientation="horizontal"),
    _c(Z, "dimension", "12.1 ±0.1", 12.1, 0.1, orientation="horizontal"),
    _c(Z, "dimension", "5.08 ±0.1 (4X)", 5.08, 0.1, count=4, orientation="vertical"),
    _c(Z, "dimension", "2.54 ±0.1 (4X)", 2.54, 0.1, count=4, orientation="vertical"),
    _c(Z, "dimension", "13.9 ±0.1", 13.9, 0.1, orientation="vertical"),
    _c(Z, "dimension", "0.22 ±0.1 (5X)", 0.22, 0.1, count=5, orientation="horizontal"),
    _c(Z, "dimension", "2.32 ±0.1 (5X)", 2.32, 0.1, count=5, orientation="horizontal"),
    _c(Z, "dimension", "0.64 ±0.05 (10X) horizontal", 0.64, 0.05, count=10, orientation="horizontal"),
    _c(Z, "dimension", "0.64 ±0.05 (10X) vertical", 0.64, 0.05, count=10, orientation="vertical"),
    # section A-A
    _c(S, "dimension", "16.65 ±0.2", 16.65, 0.2, orientation="vertical"),
    _c(S, "dimension", "14.7 ±0.2", 14.7, 0.2, orientation="vertical"),
    _c(S, "dimension", "12.8 ±0.2", 12.8, 0.2, orientation="vertical"),
    _c(S, "dimension", "7.65 ±0.2", 7.65, 0.2, orientation="vertical"),
    # front view
    _c(F, "profile", "PROFILE 0.5 |A|B|C| (measurement points S9224M001-009)", geo=0.5, datums="ABC"),
    # items that must NOT become rows
    _c("SLIDING BUTTON [P3]", "dimension", "F2 11 ±3.5 N", 11, 3.5, unit="N"),
    _c("FRONT VIEW (STROKE)", "note", "MAX. 14.5 SLIDING STROKE", 14.5),
]
for _i, _c_ in enumerate(CALLOUTS, 1):
    _c_.id = f"C{_i:03d}"


# Real callout positions, read off 0-1000 rulers over these sheet regions (see with_ruler()).
_REGIONS = {"REAR VIEW": [0.14, 0.42, 0.32, 0.62], "RIGHT VIEW": [0.31, 0.42, 0.40, 0.62],
            "DETAIL Z": [0.02, 0.60, 0.17, 0.74], "SECTION A-A": [0.01, 0.42, 0.12, 0.61],
            "FRONT VIEW": [0.28, 0.63, 0.43, 0.78]}
_RULER = {
    "PROFILE 0.5 |A|B|C| (left)": (142, 202),
    "PROFILE 0.5 |A|B|C| (right)": (818, 198),
    "23.8 ±0.3 (left)": (442, 148),
    "23.8 ±0.3 (right)": (555, 148),
    "24.22 ±0.3": (276, 383),
    "10.31 ±0.3": (322, 540),
    "9.45 ±0.3": (719, 376),
    "2.2 ±0.1 (2X)": (748, 417),
    "2.65 ±0.3": (568, 604),
    "1.5 ±0.1": (568, 646),
    "26.95": (437, 768),
    "37.02": (585, 768),
    "3.1 ±0.1 (2X) upper": (298, 125),
    "3.1 ±0.1 (2X) lower": (319, 608),
    "37.3 ±0.3": (840, 327),
    "18.85 ±0.25": (532, 669),
    "29.62 ±0.5": (596, 732),
    "15.1 ±0.1": (501, 174),
    "12.1 ±0.1": (501, 251),
    "5.08 ±0.1 (4X)": (105, 329),
    "2.54 ±0.1 (4X)": (175, 609),
    "13.9 ±0.1": (636, 503),
    "0.22 ±0.1 (5X)": (341, 867),
    "2.32 ±0.1 (5X)": (520, 925),
    "0.64 ±0.05 (10X) horizontal": (527, 812),
    "0.64 ±0.05 (10X) vertical": (668, 300),
    "16.65 ±0.2": (118, 264),
    "14.7 ±0.2": (173, 229),
    "12.8 ±0.2": (242, 211),
    "7.65 ±0.2": (308, 300),
    "PROFILE 0.5 |A|B|C| (measurement points S9224M001-009)": (231, 208),
}
_SHEET = {"F2 11 ±3.5 N": (0.12, 0.76), "MAX. 14.5 SLIDING STROKE": (0.262, 0.70)}


def _positions():
    pos = {}
    for c in CALLOUTS:
        if c.text in _SHEET:
            pos[c.id] = _SHEET[c.text]
        else:
            b = _REGIONS[c.view]
            u, v = _RULER[c.text]
            pos[c.id] = (b[0] + u / 1000 * (b[2] - b[0]), b[1] + v / 1000 * (b[3] - b[1]))
    return pos


POSITIONS = _positions()


class FakeLLM(LLM):
    """Stand-in for the OpenAI client: answers the two real prompts from the fixture above,
    including tile geometry, so overlap de-duplication and view assignment are exercised."""

    def __init__(self):
        self.model, self.calls = "fixture", 0

    def json(self, *, system, prompt, schema, name, images=None, retries=3):
        self.calls += 1
        assert images, "the pipeline must always send an image"
        if name == "layout":
            tb = TITLE.model_dump(include={"part_name", "part_reference", "part_index", "drawing_reference",
                                           "drawing_index"})
            return {"views": [v.model_dump() for v in VIEWS], "title_block": tb, "notes": TITLE.general_notes}
        if name == "callouts":
            x0, y0, x1, y1 = map(float, re.search(r"tile region: \[([^\]]+)\]", prompt).group(1).split(","))
            keep = {"kind", "text", "nominal", "tol_plus", "tol_minus", "geo_tol", "datums", "count",
                    "orientation", "datum_feature", "unit", "confidence"}
            out = []
            for c in CALLOUTS:
                x, y = POSITIONS[c.id]
                if x0 <= x <= x1 and y0 <= y <= y1:
                    bx, by = (x - x0) / (x1 - x0) * 1000, (y - y0) / (y1 - y0) * 1000
                    # realistic text size: ~12 x 3.5 mm dimension text, ~22 mm feature control frame
                    sx, sy = (120, 22) if c.kind == "profile" else (65, 20) if c.orientation != "vertical" else (20, 65)
                    kx, ky = sx / 2 * 185 / ((x1 - x0) * 1195), sy / 2 * 185 / ((y1 - y0) * 847)
                    out.append(c.model_dump(include=keep) | {"view_hint": None,
                                                              "bbox": [bx - kx, by - ky, bx + kx, by + ky]})
            return {"callouts": out}
        raise ValueError(name)
