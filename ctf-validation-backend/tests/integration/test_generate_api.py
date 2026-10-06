from tests.unit.test_tolerance_transfer import make_ctf  # noqa: E402


def up(client, path):
    r = client.post("/api/v1/upload/ctf", files={"file": (path.name, path.read_bytes())})
    assert r.status_code == 201, r.text
    return r.json()["file_id"]


def test_generate_and_download(client, tmp_path):
    new = make_ctf(tmp_path / "new.xlsx", [("CTF", "01A01", "Size Tolerance of the datum C in C/C direction", 0, -0.1, 0.1)])
    old = make_ctf(tmp_path / "old.xlsx", [("CTF", "01A03", "Size tolerance of the Datum C Clamping Width", 0, -0.3, 0.3)])
    r = client.post("/api/v1/generate", json={"template_file_id": up(client, new), "source_file_id": up(client, old)})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["template_version"] == "BETA_V003" and body["summary"]["updated"] == 1
    assert body["rows"][0]["new"] == [0.0, -0.3, 0.3] and body["filename"] == "new_generated.xlsx"
    d = client.get(f"/api/v1/generate/{body['file_id']}/download")
    assert d.status_code == 200 and d.content.startswith(b"PK")


def test_generate_unknown_files_and_bad_override(client, tmp_path):
    assert client.post("/api/v1/generate", json={"template_file_id": "x", "source_file_id": "y"}).status_code == 404
    new = make_ctf(tmp_path / "n.xlsx", [("CTF", "01A01", "Size tolerance of the Datum A", 0, -0.1, 0.1)])
    fid = up(client, new)
    r = client.post("/api/v1/generate", json={"template_file_id": fid, "source_file_id": fid, "overrides": {"01A01": "ZZ"}})
    assert r.status_code == 422
    assert client.get("/api/v1/generate/nope/download").status_code == 404
