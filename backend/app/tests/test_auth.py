def test_login_and_me(client):
    res = client.post("/api/v1/auth/login", json={"email": "cliente@teste.local", "password": "senha12345"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["email"] == "cliente@teste.local"


def test_login_rate_limit(client):
    """Login endpoint should return 429 after 10 failed attempts.

    Note: slowapi uses in-memory rate limiting by default (per-process).
    This is acceptable for MVP.
    """
    for i in range(10):
        client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "wrong"})

    resp = client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "wrong"})
    assert resp.status_code == 429
