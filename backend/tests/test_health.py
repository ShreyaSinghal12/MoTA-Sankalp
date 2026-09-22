def test_root(client):
    assert client.get("/").status_code == 200


def test_health(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_login_rejects_bad_password(client):
    r = client.post("/api/v1/auth/login", json={"email": "admin@mota.gov.in", "password": "wrong"})
    assert r.status_code == 401


def test_me(client, auth):
    assert client.get("/api/v1/auth/me", headers=auth).json()["role"] == "ADMIN"
