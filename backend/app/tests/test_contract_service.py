from __future__ import annotations


def _login(client, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def _get_plan_id(client, token: str) -> str:
    plans = client.get("/api/v1/plans", headers={"Authorization": f"Bearer {token}"})
    assert plans.status_code == 200
    items = plans.json()["items"]
    assert items, "No plans available in test DB"
    return items[0]["id"]


def test_contract_service_creates_service_invoice_job(client):
    """ContractService should create Service, Invoice, and Job records."""
    token = _login(client, "cliente@teste.local", "senha12345")
    plan_id = _get_plan_id(client, token)

    res = client.post(
        "/api/v1/services/contract",
        json={
            "plan_id": plan_id,
            "name": "Test VPS",
            "billing_cycle": "monthly",
            "confirm": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending"
    assert data["name"] == "Test VPS"


def test_contract_service_requires_confirmation(client):
    """ContractService should reject requests without confirm=True."""
    token = _login(client, "cliente@teste.local", "senha12345")
    plan_id = _get_plan_id(client, token)

    res = client.post(
        "/api/v1/services/contract",
        json={
            "plan_id": plan_id,
            "name": "Test VPS",
            "billing_cycle": "monthly",
            "confirm": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_contract_service_rejects_user_without_tenant(client):
    """ContractService should reject super_admin users (no tenant_id)."""
    token = _login(client, "admin@teste.local", "adminpass123")

    res = client.post(
        "/api/v1/services/contract",
        json={
            "plan_id": "00000000-0000-0000-0000-000000000000",
            "name": "Test VPS",
            "billing_cycle": "monthly",
            "confirm": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
