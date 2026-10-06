import time

from app.core.config import get_settings
from app.pipeline.orchestrator import PipelineError, run_pipeline

import pytest


def upload(client, kind, name, data):
    r = client.post(f"/api/v1/upload/{kind}", files={"file": (name, data)})
    assert r.status_code == 201, r.text
    return r.json()["file_id"]


def validate(client, data, name="part.jtxml"):
    fid = upload(client, "jtxml", name, data)
    r = client.post("/api/v1/validate", json={"jtxml_file_id": fid})
    assert r.status_code == 202, r.text
    job_id = r.json()["id"]
    for _ in range(50):  # background task already ran under TestClient; loop is a safety net
        job = client.get(f"/api/v1/validate/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            return job
        time.sleep(0.1)
    raise AssertionError("job did not finish")


def test_orchestrator_runs_all_stages(tmp_path, good_bytes):
    p = tmp_path / "g.jtxml"
    p.write_bytes(good_bytes)
    seen = []
    res = run_pipeline(p, get_settings(), {"job_id": "x", "filename": "g.jtxml"}, on_stage=lambda s: seen.append(s))
    assert [s["status"] for s in res.stages.values()] == ["done"] * 6
    assert res.report["verdict"] == "pass" and len(seen) >= 12


def test_orchestrator_fatal_parse_failure_skips_rest(tmp_path):
    p = tmp_path / "x.jtxml"
    p.write_bytes(b"<broken")
    with pytest.raises(PipelineError) as e:
        run_pipeline(p, get_settings())
    assert e.value.stage == "parsing"
    assert e.value.stages["parsing"]["status"] == "failed" and e.value.stages["rules"]["status"] == "skipped"


def test_good_file_passes_and_can_be_approved_and_exported(client, good_bytes):
    job = validate(client, good_bytes)
    assert job["status"] == "completed" and job["verdict"] == "pass" and job["findings"] == []

    rep = client.get(f"/api/v1/reports/{job['id']}")
    assert rep.status_code == 200 and rep.json()["part_name"] == "BRACKET FRONT LH"

    r = client.post(f"/api/v1/approval/{job['id']}", json={"decision": "approve", "reviewer": "qa1"})
    assert r.status_code == 201 and r.json()["decision"] == "approved"
    assert client.get(f"/api/v1/validate/{job['id']}").json()["approval_status"] == "approved"
    assert len(client.get(f"/api/v1/approval/{job['id']}").json()) == 1

    for fmt, magic in (("xlsx", b"PK"), ("pdf", b"%PDF")):
        d = client.get(f"/api/v1/reports/{job['id']}/download", params={"format": fmt})
        assert d.status_code == 200 and d.content.startswith(magic)
    assert client.get(f"/api/v1/reports/{job['id']}/download", params={"format": "doc"}).status_code == 422


def test_bad_file_fails_and_cannot_be_approved(client, bad_bytes):
    job = validate(client, bad_bytes)
    assert job["status"] == "completed" and job["verdict"] == "fail"
    assert "TPL001" in {f["rule"] for f in job["findings"]}
    assert client.post(f"/api/v1/approval/{job['id']}", json={"decision": "approve"}).status_code == 409
    assert client.post(f"/api/v1/approval/{job['id']}", json={"decision": "reject"}).status_code == 422  # comment required
    ok = client.post(f"/api/v1/approval/{job['id']}", json={"decision": "reject", "comment": "Beta 2 template"})
    assert ok.status_code == 201
    assert any(j["id"] == job["id"] for j in client.get("/api/v1/validate").json())


def test_unparseable_file_marks_job_failed(client):
    job = validate(client, b"<oops")
    assert job["status"] == "failed" and "parsing" in job["error"]
    assert client.get(f"/api/v1/reports/{job['id']}").status_code == 409


def test_upload_validation(client):
    assert client.post("/api/v1/upload/jtxml", files={"file": ("a.txt", b"x")}).status_code == 422
    assert client.post("/api/v1/upload/jtxml", files={"file": ("a.jtxml", b"")}).status_code == 422
    ctf = upload(client, "ctf", "c.csv", b"a,b\n1,2\n")
    assert client.post("/api/v1/validate", json={"jtxml_file_id": ctf}).status_code == 404  # wrong kind
    assert client.get("/api/v1/validate/nope").status_code == 404


def test_api_key_enforced_when_configured(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "api_key", "secret")
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/validate").status_code == 401
    assert client.get("/api/v1/validate", headers={"X-API-Key": "secret"}).status_code == 200
