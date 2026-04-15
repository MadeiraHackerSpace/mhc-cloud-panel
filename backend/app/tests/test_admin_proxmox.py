"""Tests for new Admin Proxmox endpoints.

Covers:
  - GET /admin/proxmox/capacity — cluster capacity with balanciness
  - GET /admin/proxmox/best-node — best node for a given resource profile
  - POST /admin/proxmox/nodes/{node}/maintenance — set/clear maintenance mode

Uses the super_admin user created in conftest.py to test real RBAC end-to-end.
"""

from __future__ import annotations


def _admin_token(client) -> str:
    """Login as super_admin and return the access token."""
    res = client.post("/api/v1/auth/login", json={"email": "admin@teste.local", "password": "adminpass123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _client_token(client) -> str:
    res = client.post("/api/v1/auth/login", json={"email": "cliente@teste.local", "password": "senha12345"})
    assert res.status_code == 200
    return res.json()["access_token"]


# ── GET /admin/proxmox/capacity ───────────────────────────────────────────────

class TestClusterCapacity:
    def test_returns_capacity_structure(self, client):
        token = _admin_token(client)
        res = client.get("/api/v1/admin/proxmox/capacity?method=memory", headers=_auth(token))
        assert res.status_code == 200, res.text
        data = res.json()

        assert "nodes" in data
        assert "balanciness" in data
        assert "method" in data
        assert data["method"] == "memory"
        assert data["total_count"] == 2
        assert data["online_count"] == 2

    def test_nodes_have_expected_fields(self, client):
        token = _admin_token(client)
        res = client.get("/api/v1/admin/proxmox/capacity", headers=_auth(token))
        assert res.status_code == 200
        nodes = res.json()["nodes"]
        assert len(nodes) == 2

        for node in nodes:
            assert "node" in node
            assert "mem_free_gb" in node
            assert "cpu_usage_pct" in node
            assert "mem_free_pct" in node
            assert node["status"] == "online"

    def test_balanciness_is_numeric(self, client):
        token = _admin_token(client)
        res = client.get("/api/v1/admin/proxmox/capacity", headers=_auth(token))
        assert res.status_code == 200
        assert isinstance(res.json()["balanciness"], float)

    def test_requires_auth(self, client):
        res = client.get("/api/v1/admin/proxmox/capacity")
        assert res.status_code == 401

    def test_cliente_role_is_forbidden(self, client):
        token = _client_token(client)
        res = client.get("/api/v1/admin/proxmox/capacity", headers=_auth(token))
        assert res.status_code == 403


# ── GET /admin/proxmox/best-node ─────────────────────────────────────────────

class TestBestNodeEndpoint:
    def test_returns_best_node(self, client):
        token = _admin_token(client)
        res = client.get(
            "/api/v1/admin/proxmox/best-node?ram_mb=512&vcpu=1&method=memory",
            headers=_auth(token),
        )
        assert res.status_code == 200, res.text
        data = res.json()

        assert "node" in data
        # pve2 has 62GB free vs pve with 28GB free — should prefer pve2
        assert data["node"] == "pve2"
        assert "mem_free_gb" in data
        assert "cpu_usage_pct" in data
        assert data["method"] == "memory"

    def test_insufficient_capacity_returns_507(self, client):
        token = _admin_token(client)
        # Request 999TB of RAM — no node will have that
        res = client.get(
            "/api/v1/admin/proxmox/best-node?ram_mb=999999999",
            headers=_auth(token),
        )
        assert res.status_code == 507

    def test_requires_auth(self, client):
        res = client.get("/api/v1/admin/proxmox/best-node")
        assert res.status_code == 401

    def test_cliente_role_is_forbidden(self, client):
        token = _client_token(client)
        res = client.get("/api/v1/admin/proxmox/best-node", headers=_auth(token))
        assert res.status_code == 403


# ── POST /admin/proxmox/nodes/{node}/maintenance ──────────────────────────────

class TestMaintenanceEndpoint:
    def test_enable_maintenance(self, client, monkeypatch):
        from app.tasks import maintenance_drain as drain_module

        class DummyResult:
            id = "dummy-drain-task-id"

        # Prevent actual Celery task dispatch
        monkeypatch.setattr(drain_module.maintenance_drain, "delay", lambda *a, **k: DummyResult())

        token = _admin_token(client)
        res = client.post(
            "/api/v1/admin/proxmox/nodes/pve/maintenance",
            json={"enable": True, "notes": "Test maintenance", "drain": True},
            headers=_auth(token),
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["ok"] is True
        assert data["is_maintenance"] is True
        assert data["node"] == "pve"
        assert data["drain_task_id"] == "dummy-drain-task-id"

    def test_disable_maintenance(self, client):
        token = _admin_token(client)
        res = client.post(
            "/api/v1/admin/proxmox/nodes/pve/maintenance",
            json={"enable": False, "drain": False},
            headers=_auth(token),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_maintenance"] is False
        assert data["drain_task_id"] is None

    def test_drain_not_triggered_when_disabled(self, client):
        token = _admin_token(client)
        res = client.post(
            "/api/v1/admin/proxmox/nodes/pve2/maintenance",
            json={"enable": True, "drain": False},  # drain=False
            headers=_auth(token),
        )
        assert res.status_code == 200
        assert res.json()["drain_task_id"] is None

    def test_requires_auth(self, client):
        res = client.post(
            "/api/v1/admin/proxmox/nodes/pve/maintenance",
            json={"enable": True},
        )
        assert res.status_code == 401

    def test_cliente_role_is_forbidden(self, client):
        token = _client_token(client)
        res = client.post(
            "/api/v1/admin/proxmox/nodes/pve/maintenance",
            json={"enable": True},
            headers=_auth(token),
        )
        assert res.status_code == 403
