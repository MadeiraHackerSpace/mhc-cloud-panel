def test_login_and_me(client):
    res = client.post("/api/v1/auth/login", json={"email": "cliente@teste.local", "password": "senha12345"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["email"] == "cliente@teste.local"

