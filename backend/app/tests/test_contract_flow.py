def _login(client):
    res = client.post("/api/v1/auth/login", json={"email": "cliente@teste.local", "password": "senha12345"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_contract_plan_creates_service_and_job(client):
    token = _login(client)
    plans = client.get("/api/v1/plans?limit=10&offset=0", headers={"Authorization": f"Bearer {token}"})
    assert plans.status_code == 200
    plan_id = plans.json()["items"][0]["id"]

    res = client.post(
        "/api/v1/services/contract",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "plan_id": plan_id,
            "name": "Minha VPS",
            "billing_cycle": "monthly",
            "proxmox_node": "pve",
            "confirm": True,
        },
    )
    assert res.status_code == 200
    service = res.json()
    assert service["status"] == "pending"

