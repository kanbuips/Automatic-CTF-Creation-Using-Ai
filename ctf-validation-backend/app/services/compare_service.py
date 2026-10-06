"""CTF vs JT validation."""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import CtfRecord
from app.pipeline.parsing.ctf_parser import parse_ctf
from app.pipeline.parsing.plmxml_parser import parse_plmxml
from app.pipeline.rules import jt_rules


def _file(db: Session, file_id: str, kind: str) -> CtfRecord:
    rec = db.get(CtfRecord, file_id)
    if rec is None or rec.kind != kind:
        raise NotFoundError(f"{kind} file {file_id} not found")
    return rec


def compare(db: Session, ctf_file_id: str, jt_file_id: str) -> dict:
    ctf_rec, jt_rec = _file(db, ctf_file_id, "ctf"), _file(db, jt_file_id, "jtxml")
    ctf, jt = parse_ctf(ctf_rec.path), parse_plmxml(jt_rec.path)
    checks = jt_rules.compare(ctf, jt)
    return {
        "ctf_file": ctf_rec.filename,
        "jt_file": jt_rec.filename,
        "ctf": {k: ctf.front.get(k) for k in ("part_name", "part_ref", "drawing_ref", "drawing_indice", "project", "template_version")},
        "jt": {"item_id": jt.item_id, "revision": jt.revision, "product_name": jt.product_name, "object_name": jt.object_name},
        "characteristics_in_ctf": len(ctf.rows),
        "summary": jt_rules.summarize(checks),
        "checks": [c.as_dict() for c in checks],
    }
