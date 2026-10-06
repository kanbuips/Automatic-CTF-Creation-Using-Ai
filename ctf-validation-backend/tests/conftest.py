import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="ctf-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(_tmp / "uploads")
os.environ["REPORT_DIR"] = str(_tmp / "reports")
os.environ["ARTIFACT_DIR"] = str(_tmp / "no-artifacts")
os.environ["API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def good_bytes() -> bytes:
    return (FIXTURES / "good.jtxml").read_bytes()


@pytest.fixture(scope="session")
def bad_bytes() -> bytes:
    return (FIXTURES / "bad.jtxml").read_bytes()


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c
