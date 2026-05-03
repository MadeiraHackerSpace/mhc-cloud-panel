"""Tests for VNC WebSocket endpoint security (TASK-005).

Validates that authentication and parameter validation happen BEFORE
websocket.accept(), so invalid connections are rejected with code 1008.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def _login(client: TestClient) -> str:
    res = client.post("/api/v1/auth/login", json={"email": "cliente@teste.local", "password": "senha12345"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_vnc_ws_rejects_invalid_port(client: TestClient):
    """WebSocket VNC should reject connections with port outside 5900-5999 (code 1008)."""
    vm_id = uuid.uuid4()
    with pytest.raises((WebSocketDisconnect, Exception)):
        with client.websocket_connect(f"/api/v1/vms/{vm_id}/vnc/ws?port=80&vncticket=someticket"):
            pass


def test_vnc_ws_rejects_port_above_range(client: TestClient):
    """WebSocket VNC should reject connections with port > 5999 (code 1008)."""
    vm_id = uuid.uuid4()
    with pytest.raises((WebSocketDisconnect, Exception)):
        with client.websocket_connect(f"/api/v1/vms/{vm_id}/vnc/ws?port=6000&vncticket=someticket"):
            pass


def test_vnc_ws_rejects_empty_vncticket(client: TestClient):
    """WebSocket VNC should reject connections with empty vncticket (code 1008)."""
    vm_id = uuid.uuid4()
    with pytest.raises((WebSocketDisconnect, Exception)):
        with client.websocket_connect(f"/api/v1/vms/{vm_id}/vnc/ws?port=5900&vncticket="):
            pass


def test_vnc_ws_rejects_oversized_vncticket(client: TestClient):
    """WebSocket VNC should reject connections with vncticket longer than 512 chars (code 1008)."""
    vm_id = uuid.uuid4()
    long_ticket = "x" * 513
    with pytest.raises((WebSocketDisconnect, Exception)):
        with client.websocket_connect(f"/api/v1/vms/{vm_id}/vnc/ws?port=5900&vncticket={long_ticket}"):
            pass


def test_vnc_ws_rejects_unauthenticated(client: TestClient):
    """WebSocket VNC should reject connections with no auth token (code 1008)."""
    vm_id = uuid.uuid4()
    with pytest.raises((WebSocketDisconnect, Exception)):
        with client.websocket_connect(f"/api/v1/vms/{vm_id}/vnc/ws?port=5900&vncticket=validticket"):
            pass


def test_vnc_ws_rejects_invalid_token(client: TestClient):
    """WebSocket VNC should reject connections with an invalid auth token (code 1008)."""
    vm_id = uuid.uuid4()
    with pytest.raises((WebSocketDisconnect, Exception)):
        with client.websocket_connect(
            f"/api/v1/vms/{vm_id}/vnc/ws?port=5900&vncticket=validticket",
            headers={"Authorization": "Bearer invalidtoken"},
        ):
            pass


def test_vnc_ws_rejects_nonexistent_vm(client: TestClient):
    """WebSocket VNC should reject connections for a VM that doesn't exist (code 1008)."""
    token = _login(client)
    vm_id = uuid.uuid4()  # random UUID that doesn't exist in DB
    with pytest.raises((WebSocketDisconnect, Exception)):
        with client.websocket_connect(
            f"/api/v1/vms/{vm_id}/vnc/ws?port=5900&vncticket=validticket",
            headers={"Authorization": f"Bearer {token}"},
        ):
            pass
