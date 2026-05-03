"""
TASK-011 — Tenant isolation tests (IDOR prevention).

Verifies that no endpoint returns data from another tenant.
All cross-tenant access attempts must return 403 or 404, never 200 with data.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_token(user_id: str, tenant_id: str | None, role: str = "cliente") -> str:
    """Create a JWT token directly without going through the login endpoint.

    This avoids hitting the rate limiter during tests.
    """
    from app.core.security import create_access_token
    return create_access_token(subject=user_id, tenant_id=tenant_id, role=role)


# ---------------------------------------------------------------------------
# Fixture: tenant A user info (from conftest)
# ---------------------------------------------------------------------------

@pytest.fixture()
def tenant_a_token(client):
    """Return a JWT token for tenant A's user (cliente@teste.local).

    Reads the user from the DB to get the user ID and tenant ID.
    """
    from app.core.database import get_sessionmaker
    from app.models.user import User
    from sqlalchemy import select

    db = get_sessionmaker()()
    try:
        user_a = db.scalar(select(User).where(User.email == "cliente@teste.local"))
        assert user_a is not None, "Tenant A user not found"
        return _make_token(str(user_a.id), str(user_a.tenant_id))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fixture: tenant B data
# ---------------------------------------------------------------------------

@pytest.fixture()
def tenant_b_data(client):
    """Create tenant B with its own user, service, VM, invoice, and ticket.

    Uses the same DB as the ``client`` fixture (which already has tenant A).
    Yields a dict with tenant B's resource IDs and a pre-built JWT token.
    """
    from app.core.database import get_sessionmaker
    from app.core.security import hash_password
    from app.models.customer import Customer
    from app.models.enums import (
        InvoiceStatus,
        RoleName,
        ServiceStatus,
        TicketPriority,
        TicketStatus,
        VMStatus,
    )
    from app.models.invoice import Invoice
    from app.models.plan import Plan
    from app.models.role import Role
    from app.models.service import Service
    from app.models.tenant import Tenant
    from app.models.ticket import Ticket
    from app.models.user import User
    from app.models.virtual_machine import VirtualMachine
    from sqlalchemy import select

    db = get_sessionmaker()()
    try:
        plan = db.scalar(select(Plan).where(Plan.name == "Bronze"))
        cliente_role = db.scalar(select(Role).where(Role.name == RoleName.cliente))

        # --- Tenant B ---
        tenant_b = Tenant(name="Tenant B", slug="tenant-b-isolation", is_active=True)
        db.add(tenant_b)
        db.commit()
        db.refresh(tenant_b)

        customer_b = Customer(
            tenant_id=tenant_b.id,
            display_name="Cliente B",
            email="cliente-b@teste.local",
        )
        db.add(customer_b)
        db.commit()
        db.refresh(customer_b)

        user_b = User(
            tenant_id=tenant_b.id,
            role_id=cliente_role.id,
            email="cliente-b@teste.local",
            full_name="Cliente B",
            password_hash=hash_password("senhaB12345"),
            is_active=True,
            is_email_verified=True,
        )
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

        service_b = Service(
            tenant_id=tenant_b.id,
            customer_id=customer_b.id,
            plan_id=plan.id,
            name="Service B",
            status=ServiceStatus.active,
            billing_cycle="monthly",
        )
        db.add(service_b)
        db.commit()
        db.refresh(service_b)

        vm_b = VirtualMachine(
            tenant_id=tenant_b.id,
            service_id=service_b.id,
            proxmox_node="pve",
            proxmox_vmid=200,
            name="VM B",
            status=VMStatus.running,
        )
        db.add(vm_b)
        db.commit()
        db.refresh(vm_b)

        invoice_b = Invoice(
            tenant_id=tenant_b.id,
            customer_id=customer_b.id,
            service_id=service_b.id,
            number="INV-B-001",
            status=InvoiceStatus.open,
            currency="BRL",
            amount_total=Decimal("29.90"),
            due_date=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(invoice_b)
        db.commit()
        db.refresh(invoice_b)

        ticket_b = Ticket(
            tenant_id=tenant_b.id,
            customer_id=customer_b.id,
            opened_by_user_id=user_b.id,
            subject="Ticket B",
            status=TicketStatus.open,
            priority=TicketPriority.normal,
        )
        db.add(ticket_b)
        db.commit()
        db.refresh(ticket_b)

        # Build a JWT token for tenant B's user directly (no login endpoint needed)
        token_b = _make_token(str(user_b.id), str(tenant_b.id))

        yield {
            "tenant_id": str(tenant_b.id),
            "user_id": str(user_b.id),
            "token": token_b,
            "service_id": str(service_b.id),
            "vm_id": str(vm_b.id),
            "invoice_id": str(invoice_b.id),
            "ticket_id": str(ticket_b.id),
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Cross-tenant VM access tests
# ---------------------------------------------------------------------------

def test_get_vm_of_other_tenant_is_denied(client, tenant_a_token, tenant_b_data):
    """GET /vms/{vm_id_of_B} with tenant A token → 403 or 404."""
    res = client.get(f"/api/v1/vms/{tenant_b_data['vm_id']}", headers=_auth(tenant_a_token))
    assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}: {res.json()}"


def test_start_vm_of_other_tenant_is_denied(client, tenant_a_token, tenant_b_data):
    """POST /vms/{vm_id_of_B}/start with tenant A token → 403 or 404."""
    with patch("app.integrations.proxmox.service.ProxmoxService.start_vm"):
        res = client.post(
            f"/api/v1/vms/{tenant_b_data['vm_id']}/start",
            headers=_auth(tenant_a_token),
            json={"confirm": True},
        )
    assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}: {res.json()}"


def test_stop_vm_of_other_tenant_is_denied(client, tenant_a_token, tenant_b_data):
    """POST /vms/{vm_id_of_B}/stop with tenant A token → 403 or 404."""
    with patch("app.integrations.proxmox.service.ProxmoxService.stop_vm"):
        res = client.post(
            f"/api/v1/vms/{tenant_b_data['vm_id']}/stop",
            headers=_auth(tenant_a_token),
            json={"confirm": True},
        )
    assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}: {res.json()}"


def test_reboot_vm_of_other_tenant_is_denied(client, tenant_a_token, tenant_b_data):
    """POST /vms/{vm_id_of_B}/reboot with tenant A token → 403 or 404."""
    with patch("app.integrations.proxmox.service.ProxmoxService.reboot_vm"):
        res = client.post(
            f"/api/v1/vms/{tenant_b_data['vm_id']}/reboot",
            headers=_auth(tenant_a_token),
            json={"confirm": True},
        )
    assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}: {res.json()}"


def test_status_vm_of_other_tenant_is_denied(client, tenant_a_token, tenant_b_data):
    """GET /vms/{vm_id_of_B}/status with tenant A token → 403 or 404."""
    with patch(
        "app.integrations.proxmox.service.ProxmoxService.current_status",
        return_value={"status": "running"},
    ):
        res = client.get(
            f"/api/v1/vms/{tenant_b_data['vm_id']}/status",
            headers=_auth(tenant_a_token),
        )
    assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}: {res.json()}"


# ---------------------------------------------------------------------------
# Cross-tenant ticket access tests
# ---------------------------------------------------------------------------

def test_get_ticket_of_other_tenant_is_denied(client, tenant_a_token, tenant_b_data):
    """GET /tickets/{ticket_id_of_B} with tenant A token → 403 or 404."""
    res = client.get(f"/api/v1/tickets/{tenant_b_data['ticket_id']}", headers=_auth(tenant_a_token))
    assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}: {res.json()}"


def test_get_ticket_messages_of_other_tenant_is_denied(client, tenant_a_token, tenant_b_data):
    """GET /tickets/{ticket_id_of_B}/messages with tenant A token → 403 or 404."""
    res = client.get(f"/api/v1/tickets/{tenant_b_data['ticket_id']}/messages", headers=_auth(tenant_a_token))
    assert res.status_code in (403, 404), f"Expected 403/404, got {res.status_code}: {res.json()}"


# ---------------------------------------------------------------------------
# Cross-tenant invoice access test
# ---------------------------------------------------------------------------

def test_invoice_list_does_not_contain_other_tenant_invoice(client, tenant_a_token, tenant_b_data):
    """GET /invoices with tenant A token → tenant B's invoice must NOT appear."""
    res = client.get("/api/v1/invoices", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    invoice_ids = [inv["id"] for inv in res.json()["items"]]
    assert tenant_b_data["invoice_id"] not in invoice_ids, (
        "Tenant A's invoice list contains tenant B's invoice — IDOR vulnerability!"
    )


# ---------------------------------------------------------------------------
# List-scoping tests: each list endpoint must only return the current tenant's data
# ---------------------------------------------------------------------------

def test_vm_list_is_scoped_to_tenant(client, tenant_a_token, tenant_b_data):
    """GET /vms with tenant A token → only tenant A's VMs are returned."""
    res = client.get("/api/v1/vms", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    vm_ids = [vm["id"] for vm in res.json()["items"]]
    assert tenant_b_data["vm_id"] not in vm_ids, (
        "Tenant A's VM list contains tenant B's VM — IDOR vulnerability!"
    )


def test_service_list_is_scoped_to_tenant(client, tenant_a_token, tenant_b_data):
    """GET /services with tenant A token → only tenant A's services are returned."""
    res = client.get("/api/v1/services", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    service_ids = [svc["id"] for svc in res.json()["items"]]
    assert tenant_b_data["service_id"] not in service_ids, (
        "Tenant A's service list contains tenant B's service — IDOR vulnerability!"
    )


def test_invoice_list_is_scoped_to_tenant(client, tenant_a_token, tenant_b_data):
    """GET /invoices with tenant A token → only tenant A's invoices are returned."""
    res = client.get("/api/v1/invoices", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    invoice_ids = [inv["id"] for inv in res.json()["items"]]
    assert tenant_b_data["invoice_id"] not in invoice_ids, (
        "Tenant A's invoice list contains tenant B's invoice — IDOR vulnerability!"
    )


def test_ticket_list_is_scoped_to_tenant(client, tenant_a_token, tenant_b_data):
    """GET /tickets with tenant A token → only tenant A's tickets are returned."""
    res = client.get("/api/v1/tickets", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    ticket_ids = [t["id"] for t in res.json()["items"]]
    assert tenant_b_data["ticket_id"] not in ticket_ids, (
        "Tenant A's ticket list contains tenant B's ticket — IDOR vulnerability!"
    )


# ---------------------------------------------------------------------------
# Symmetry: tenant B cannot access tenant A's resources either
# ---------------------------------------------------------------------------

def test_tenant_b_cannot_access_tenant_a_vm(client, tenant_b_data):
    """Verify isolation is symmetric: tenant B also cannot access tenant A's VMs."""
    token_b = tenant_b_data["token"]
    res = client.get("/api/v1/vms", headers=_auth(token_b))
    assert res.status_code == 200
    # Tenant B should only see its own VM
    vm_ids = [vm["id"] for vm in res.json()["items"]]
    assert tenant_b_data["vm_id"] in vm_ids, "Tenant B's own VM should be visible"
    # And the list should only contain tenant B's VM (no cross-tenant leakage)
    assert len(vm_ids) == 1, f"Tenant B should see exactly 1 VM, got {len(vm_ids)}: {vm_ids}"
