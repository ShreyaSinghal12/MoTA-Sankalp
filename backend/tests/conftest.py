import os
import shutil
import tempfile

import pytest

_TMP = tempfile.mkdtemp(prefix="mota_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db").replace("\\", "/")
os.environ["UPLOAD_DIR"] = os.path.join(_TMP, "uploads")
os.environ["GENERATED_DIR"] = os.path.join(_TMP, "generated")
os.environ["OCR_ENGINE"] = "fallback"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture(scope="session")
def auth(client):
    r = client.post("/api/v1/auth/login", json={"email": "admin@mota.gov.in", "password": "admin123"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}
