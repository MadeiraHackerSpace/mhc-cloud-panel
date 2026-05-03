from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest


def _setup_vm_and_service(client):
    """Helper: create a VM and service for tenant A."""
    from app.core.database import get_sessionmaker
    from app.core.security import create_access_token
    from app.models.customer import Customer
    from app.models.enums import ServiceStatus, VMStatus
    from app.models.plan import Plan
    from app.models.service import Service
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.virtual_machine import VirtualMachine
    from sqlalchemy import select

    db = get_sessionmaker()()
    try:
        user = db.scalar(select(User).where(User.email == "cliente@teste.local"))
        tenant = db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
        customer = db.scalar(select(Customer).where(Customer.tenant_id == tenant.id))
        plan = db.scalar(select(Plan).where(Plan.name == "Bronze"))

        service = Service(
            tenant_id=tenant.id,
            customer_id=customer.id,
            plan_id=plan.id,
            name="Cancel Test VPS",
            status=ServiceStatus.active,
            billing_cycle="monthly",
        )
        db.add(service)
        db.commit()
        db.refresh(service)

        vm = VirtualMachine(
            tenant_id=tenant.id,
            service_id=service.id,
            proxmox_node="pve",
            proxmox_vmid=999,
            name="Cancel Test VM",
            status=VMStatus.running,
        )
        db.add(vm)
        db.commit()
        db.refresh(vm)

        token = create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id),
            role="cliente",
        )
        return str(vm.id), str(service.id), token
    finally:
        db.close()


def _make_proxmox_mock(**kwargs):
    """Create a MagicMock ProxmoxService with configurable method side effects."""
    mock = MagicMock()
    for method, side_effect in kwargs.items():
        getattr(mock, method).side_effect = side_effect
    return mock


def test_cancel_service_deletes_vm_in_proxmox(client):
    """When cancelling a service, the VM should be deleted in Proxmox."""
    from app.api.deps import get_proxmox_service
    from app.main import create_app

    vm_id, service_id, token = _setup_vm_and_service(client)

    mock_proxmox = _make_proxmox_mock()

    # Override the dependency on the running app
    client.app.dependency_overrides[get_proxmox_service] = lambda: mock_proxmox

    try:
        res = client.post(
            f"/api/v1/vms/{vm_id}/cancel",
            json={"confirm": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        client.app.dependency_overrides.pop(get_proxmox_service, None)

    assert res.status_code == 200
    assert res.json()["ok"] is True

    # Verify Proxmox delete was called
    mock_proxmox.delete_vm.assert_called_once()

    # Verify DB state
    from app.core.database import get_sessionmaker
    from app.models.enums import ServiceStatus, VMStatus
    from app.models.service import Service
    from app.models.virtual_machine import VirtualMachine
    from sqlalchemy import select

    db = get_sessionmaker()()
    try:
        service = db.scalar(select(Service).where(Service.id == uuid.UUID(service_id)))
        vm = db.scalar(select(VirtualMachine).where(VirtualMachine.id == uuid.UUID(vm_id)))
        assert service.status == ServiceStatus.cancelled
        assert service.cancelled_at is not None
        assert vm.status == VMStatus.deleted
    finally:
        db.close()


def test_cancel_service_cancels_db_even_when_proxmox_fails(client):
    """If Proxmox delete fails, the service should still be cancelled in the DB."""
    from app.api.deps import get_proxmox_service

    vm_id, service_id, token = _setup_vm_and_service(client)

    mock_proxmox = _make_proxmox_mock(
        delete_vm=Exception("Proxmox connection refused"),
    )

    client.app.dependency_overrides[get_proxmox_service] = lambda: mock_proxmox

    try:
        res = client.post(
            f"/api/v1/vms/{vm_id}/cancel",
            json={"confirm": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        client.app.dependency_overrides.pop(get_proxmox_service, None)

    assert res.status_code == 200
    assert res.json()["ok"] is True

    # Service must be cancelled in DB even though Proxmox failed
    from app.core.database import get_sessionmaker
    from app.models.enums import ServiceStatus
    from app.models.service import Service
    from sqlalchemy import select

    db = get_sessionmaker()()
    try:
        service = db.scalar(select(Service).where(Service.id == uuid.UUID(service_id)))
        assert service.status == ServiceStatus.cancelled
        assert service.cancelled_at is not None
    finally:
        db.close()


def test_cancel_service_requires_confirmation(client):
    """cancel_service should return 403 when confirm=False."""
    from app.api.deps import get_proxmox_service

    vm_id, _, token = _setup_vm_and_service(client)

    mock_proxmox = _make_proxmox_mock()
    client.app.dependency_overrides[get_proxmox_service] = lambda: mock_proxmox

    try:
        res = client.post(
            f"/api/v1/vms/{vm_id}/cancel",
            json={"confirm": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        client.app.dependency_overrides.pop(get_proxmox_service, None)

    assert res.status_code == 403


def test_cancel_service_records_proxmox_error_in_service_action(client):
    """ServiceAction should record proxmox_error when Proxmox delete fails."""
    from app.api.deps import get_proxmox_service

    vm_id, service_id, token = _setup_vm_and_service(client)

    mock_proxmox = _make_proxmox_mock(
        delete_vm=Exception("timeout"),
    )

    client.app.dependency_overrides[get_proxmox_service] = lambda: mock_proxmox

    try:
        res = client.post(
            f"/api/v1/vms/{vm_id}/cancel",
            json={"confirm": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        client.app.dependency_overrides.pop(get_proxmox_service, None)

    assert res.status_code == 200

    from app.core.database import get_sessionmaker
    from app.models.service_action import ServiceAction
    from sqlalchemy import select

    db = get_sessionmaker()()
    try:
        action = db.scalar(
            select(ServiceAction)
            .where(ServiceAction.service_id == uuid.UUID(service_id))
            .order_by(ServiceAction.created_at.desc())
        )
        assert action is not None
        assert action.success is False
        assert "proxmox_error" in action.details
        assert action.details["proxmox_deleted"] is False
    finally:
        db.close()
