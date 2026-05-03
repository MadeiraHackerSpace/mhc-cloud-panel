"""Integration tests for the repository layer.

Tests verify:
- TenantScopedRepository base behavior (tenant isolation, super_admin access)
- ServiceRepository, VMRepository, InvoiceRepository, TicketRepository
  with two tenants — tenant_A data never leaks to tenant_B queries.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

# ---------------------------------------------------------------------------
# DB setup helpers (reuse the same pattern as conftest.py)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _repo_env():
    """Ensure DATABASE_URL is set before importing DB modules."""
    os.environ.setdefault("SEED_ON_STARTUP", "false")
    if "DATABASE_URL" not in os.environ:
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db = os.environ.get("POSTGRES_DB", "mhc_cloud_panel")
        user = os.environ.get("POSTGRES_USER", "mhc")
        password = os.environ.get("POSTGRES_PASSWORD", "mhc")
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture()
def db_session(_repo_env):
    """Provide a fresh DB session with a clean schema for each test."""
    from app.core.config import get_settings
    import app.core.database as dbmod

    get_settings.cache_clear()
    dbmod._engine = None
    dbmod._sessionmaker = None

    from app.core.database import get_engine, get_sessionmaker
    from app.models.base import Base

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Fixtures: two tenants with their own data
# ---------------------------------------------------------------------------


@pytest.fixture()
def two_tenants(db_session):
    """Create two tenants, each with a customer, service, VM, invoice, and ticket.

    Returns a dict with keys 'tenant_a' and 'tenant_b', each containing:
      - tenant, customer, service, vm, invoice, ticket objects
    """
    from app.models.customer import Customer
    from app.models.enums import (
        InvoiceStatus,
        ServiceStatus,
        TicketPriority,
        TicketStatus,
        VMStatus,
        RoleName,
    )
    from app.models.invoice import Invoice
    from app.models.plan import Plan
    from app.models.role import Role
    from app.models.service import Service
    from app.models.tenant import Tenant
    from app.models.ticket import Ticket
    from app.models.user import User
    from app.models.virtual_machine import VirtualMachine
    from app.core.security import hash_password

    db = db_session

    # Create roles (needed for User FK)
    roles = {}
    for r in RoleName:
        role = Role(name=r, description=r.value)
        db.add(role)
    db.commit()
    for r in RoleName:
        from sqlalchemy import select
        from app.models.role import Role as R
        role = db.scalar(select(R).where(R.name == r))
        roles[r.value] = role

    # Shared plan (no tenant_id on Plan)
    plan = Plan(
        name="Test Plan",
        price_monthly=Decimal("29.90"),
        vcpu=1,
        ram_mb=1024,
        disk_gb=25,
        traffic_gb=500,
        ipv4_count=1,
        ipv6_enabled=False,
        snapshots_enabled=False,
        backups_enabled=False,
        upgrade_downgrade_allowed=True,
        is_active=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    result = {}

    for label, slug in [("tenant_a", "tenant-a-repo"), ("tenant_b", "tenant-b-repo")]:
        tenant = Tenant(name=f"Tenant {label}", slug=slug, is_active=True)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        customer = Customer(
            tenant_id=tenant.id,
            display_name=f"Customer {label}",
            email=f"{label}@test.local",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        user = User(
            tenant_id=tenant.id,
            role_id=roles["cliente"].id,
            email=f"user-{label}@test.local",
            full_name=f"User {label}",
            password_hash=hash_password("senha12345"),
            is_active=True,
            is_email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = Service(
            tenant_id=tenant.id,
            customer_id=customer.id,
            plan_id=plan.id,
            name=f"Service {label}",
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
            proxmox_vmid=100 if label == "tenant_a" else 101,
            name=f"VM {label}",
            status=VMStatus.running,
        )
        db.add(vm)
        db.commit()
        db.refresh(vm)

        invoice = Invoice(
            tenant_id=tenant.id,
            customer_id=customer.id,
            service_id=service.id,
            number=f"INV-{label.upper()}-001",
            status=InvoiceStatus.open,
            currency="BRL",
            amount_total=Decimal("29.90"),
            due_date=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        ticket = Ticket(
            tenant_id=tenant.id,
            customer_id=customer.id,
            opened_by_user_id=user.id,
            subject=f"Ticket {label}",
            status=TicketStatus.open,
            priority=TicketPriority.normal,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        result[label] = {
            "tenant": tenant,
            "customer": customer,
            "user": user,
            "service": service,
            "vm": vm,
            "invoice": invoice,
            "ticket": ticket,
        }

    return result


# ===========================================================================
# TenantScopedRepository base tests
# ===========================================================================


class TestTenantScopedRepositoryBase:
    """Tests for the base class behavior using ServiceRepository as a concrete example."""

    def test_super_admin_sees_all_tenants(self, db_session, two_tenants):
        """tenant_id=None (super_admin) returns records from all tenants."""
        from app.repositories.service_repository import ServiceRepository

        repo = ServiceRepository(db_session, tenant_id=None)
        items, total = repo.list(limit=100, offset=0)

        tenant_ids = {str(item.tenant_id) for item in items}
        assert str(two_tenants["tenant_a"]["tenant"].id) in tenant_ids
        assert str(two_tenants["tenant_b"]["tenant"].id) in tenant_ids
        assert total >= 2

    def test_tenant_a_never_sees_tenant_b_records(self, db_session, two_tenants):
        """tenant_id=A never returns records belonging to tenant_id=B."""
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        tenant_b_id = two_tenants["tenant_b"]["tenant"].id

        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0)

        returned_tenant_ids = {item.tenant_id for item in items}
        assert tenant_b_id not in returned_tenant_ids
        assert tenant_a_id in returned_tenant_ids

    def test_get_by_id_wrong_tenant_returns_none(self, db_session, two_tenants):
        """get_by_id with a valid ID but wrong tenant returns None."""
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        service_b_id = two_tenants["tenant_b"]["service"].id

        # Tenant A tries to fetch Tenant B's service
        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        result = repo.get_by_id(service_b_id)
        assert result is None

    def test_get_by_id_correct_tenant_returns_record(self, db_session, two_tenants):
        """get_by_id with correct tenant returns the record."""
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        service_a_id = two_tenants["tenant_a"]["service"].id

        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        result = repo.get_by_id(service_a_id)
        assert result is not None
        assert result.id == service_a_id

    def test_get_by_id_super_admin_can_access_any_tenant(self, db_session, two_tenants):
        """Super admin (tenant_id=None) can fetch records from any tenant."""
        from app.repositories.service_repository import ServiceRepository

        service_b_id = two_tenants["tenant_b"]["service"].id

        repo = ServiceRepository(db_session, tenant_id=None)
        result = repo.get_by_id(service_b_id)
        assert result is not None
        assert result.id == service_b_id

    def test_nonexistent_id_returns_none(self, db_session, two_tenants):
        """get_by_id with a non-existent UUID returns None."""
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        result = repo.get_by_id(uuid.uuid4())
        assert result is None


# ===========================================================================
# ServiceRepository tests
# ===========================================================================


class TestServiceRepository:
    def test_list_tenant_a_excludes_tenant_b(self, db_session, two_tenants):
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        tenant_b_id = two_tenants["tenant_b"]["tenant"].id

        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0)

        returned_tenant_ids = {item.tenant_id for item in items}
        assert tenant_b_id not in returned_tenant_ids
        assert total >= 1

    def test_list_tenant_b_excludes_tenant_a(self, db_session, two_tenants):
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        tenant_b_id = two_tenants["tenant_b"]["tenant"].id

        repo = ServiceRepository(db_session, tenant_id=tenant_b_id)
        items, total = repo.list(limit=100, offset=0)

        returned_tenant_ids = {item.tenant_id for item in items}
        assert tenant_a_id not in returned_tenant_ids
        assert total >= 1

    def test_get_by_id_cross_tenant_returns_none(self, db_session, two_tenants):
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        service_b_id = two_tenants["tenant_b"]["service"].id

        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        assert repo.get_by_id(service_b_id) is None

    def test_update_status(self, db_session, two_tenants):
        from app.models.enums import ServiceStatus
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        service = two_tenants["tenant_a"]["service"]

        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        updated = repo.update_status(service, ServiceStatus.suspended)
        assert updated.status == ServiceStatus.suspended

    def test_list_excludes_soft_deleted(self, db_session, two_tenants):
        """Services with deleted_at set should not appear in list()."""
        from app.repositories.service_repository import ServiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        service = two_tenants["tenant_a"]["service"]

        # Soft-delete the service
        service.deleted_at = datetime.now(UTC)
        db_session.commit()

        repo = ServiceRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0)

        assert all(item.deleted_at is None for item in items)

        # Restore for other tests
        service.deleted_at = None
        db_session.commit()


# ===========================================================================
# VMRepository tests
# ===========================================================================


class TestVMRepository:
    def test_list_tenant_a_excludes_tenant_b_vms(self, db_session, two_tenants):
        from app.repositories.vm_repository import VMRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        tenant_b_id = two_tenants["tenant_b"]["tenant"].id

        repo = VMRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0)

        returned_tenant_ids = {item.tenant_id for item in items}
        assert tenant_b_id not in returned_tenant_ids
        assert total >= 1

    def test_get_by_id_cross_tenant_returns_none(self, db_session, two_tenants):
        from app.repositories.vm_repository import VMRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        vm_b_id = two_tenants["tenant_b"]["vm"].id

        repo = VMRepository(db_session, tenant_id=tenant_a_id)
        assert repo.get_by_id(vm_b_id) is None

    def test_get_by_service_id_cross_tenant_returns_none(self, db_session, two_tenants):
        from app.repositories.vm_repository import VMRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        service_b_id = two_tenants["tenant_b"]["service"].id

        repo = VMRepository(db_session, tenant_id=tenant_a_id)
        assert repo.get_by_service_id(service_b_id) is None

    def test_get_by_service_id_correct_tenant(self, db_session, two_tenants):
        from app.repositories.vm_repository import VMRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        service_a_id = two_tenants["tenant_a"]["service"].id
        vm_a_id = two_tenants["tenant_a"]["vm"].id

        repo = VMRepository(db_session, tenant_id=tenant_a_id)
        result = repo.get_by_service_id(service_a_id)
        assert result is not None
        assert result.id == vm_a_id

    def test_list_excludes_deleted_by_default(self, db_session, two_tenants):
        from app.models.enums import VMStatus
        from app.repositories.vm_repository import VMRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        vm = two_tenants["tenant_a"]["vm"]

        # Mark VM as deleted
        original_status = vm.status
        vm.status = VMStatus.deleted
        db_session.commit()

        repo = VMRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0)
        assert all(item.status != VMStatus.deleted for item in items)

        # include_deleted=True should include it
        items_all, total_all = repo.list(limit=100, offset=0, include_deleted=True)
        assert any(item.id == vm.id for item in items_all)

        # Restore
        vm.status = original_status
        db_session.commit()

    def test_super_admin_sees_all_vms(self, db_session, two_tenants):
        from app.repositories.vm_repository import VMRepository

        repo = VMRepository(db_session, tenant_id=None)
        items, total = repo.list(limit=100, offset=0)

        tenant_ids = {item.tenant_id for item in items}
        assert two_tenants["tenant_a"]["tenant"].id in tenant_ids
        assert two_tenants["tenant_b"]["tenant"].id in tenant_ids


# ===========================================================================
# InvoiceRepository tests
# ===========================================================================


class TestInvoiceRepository:
    def test_list_tenant_a_excludes_tenant_b_invoices(self, db_session, two_tenants):
        from app.repositories.invoice_repository import InvoiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        tenant_b_id = two_tenants["tenant_b"]["tenant"].id

        repo = InvoiceRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0)

        returned_tenant_ids = {item.tenant_id for item in items}
        assert tenant_b_id not in returned_tenant_ids
        assert total >= 1

    def test_get_by_id_cross_tenant_returns_none(self, db_session, two_tenants):
        from app.repositories.invoice_repository import InvoiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        invoice_b_id = two_tenants["tenant_b"]["invoice"].id

        repo = InvoiceRepository(db_session, tenant_id=tenant_a_id)
        assert repo.get_by_id(invoice_b_id) is None

    def test_list_with_status_filter(self, db_session, two_tenants):
        from app.models.enums import InvoiceStatus
        from app.repositories.invoice_repository import InvoiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id

        repo = InvoiceRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0, status_filter=InvoiceStatus.open)
        assert all(item.status == InvoiceStatus.open for item in items)

        items_paid, total_paid = repo.list(limit=100, offset=0, status_filter=InvoiceStatus.paid)
        assert total_paid == 0  # No paid invoices yet

    def test_mark_paid(self, db_session, two_tenants):
        from app.models.enums import InvoiceStatus
        from app.repositories.invoice_repository import InvoiceRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        invoice = two_tenants["tenant_a"]["invoice"]

        repo = InvoiceRepository(db_session, tenant_id=tenant_a_id)
        paid_invoice = repo.mark_paid(invoice)

        assert paid_invoice.status == InvoiceStatus.paid
        assert paid_invoice.paid_at is not None

    def test_super_admin_sees_all_invoices(self, db_session, two_tenants):
        from app.repositories.invoice_repository import InvoiceRepository

        repo = InvoiceRepository(db_session, tenant_id=None)
        items, total = repo.list(limit=100, offset=0)

        tenant_ids = {item.tenant_id for item in items}
        assert two_tenants["tenant_a"]["tenant"].id in tenant_ids
        assert two_tenants["tenant_b"]["tenant"].id in tenant_ids


# ===========================================================================
# TicketRepository tests
# ===========================================================================


class TestTicketRepository:
    def test_list_tenant_a_excludes_tenant_b_tickets(self, db_session, two_tenants):
        from app.repositories.ticket_repository import TicketRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        tenant_b_id = two_tenants["tenant_b"]["tenant"].id

        repo = TicketRepository(db_session, tenant_id=tenant_a_id)
        items, total = repo.list(limit=100, offset=0)

        returned_tenant_ids = {item.tenant_id for item in items}
        assert tenant_b_id not in returned_tenant_ids
        assert total >= 1

    def test_get_by_id_cross_tenant_returns_none(self, db_session, two_tenants):
        from app.repositories.ticket_repository import TicketRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        ticket_b_id = two_tenants["tenant_b"]["ticket"].id

        repo = TicketRepository(db_session, tenant_id=tenant_a_id)
        assert repo.get_by_id(ticket_b_id) is None

    def test_get_by_id_correct_tenant(self, db_session, two_tenants):
        from app.repositories.ticket_repository import TicketRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        ticket_a_id = two_tenants["tenant_a"]["ticket"].id

        repo = TicketRepository(db_session, tenant_id=tenant_a_id)
        result = repo.get_by_id(ticket_a_id)
        assert result is not None
        assert result.id == ticket_a_id

    def test_list_tenant_b_excludes_tenant_a_tickets(self, db_session, two_tenants):
        from app.repositories.ticket_repository import TicketRepository

        tenant_a_id = two_tenants["tenant_a"]["tenant"].id
        tenant_b_id = two_tenants["tenant_b"]["tenant"].id

        repo = TicketRepository(db_session, tenant_id=tenant_b_id)
        items, total = repo.list(limit=100, offset=0)

        returned_tenant_ids = {item.tenant_id for item in items}
        assert tenant_a_id not in returned_tenant_ids
        assert total >= 1

    def test_super_admin_sees_all_tickets(self, db_session, two_tenants):
        from app.repositories.ticket_repository import TicketRepository

        repo = TicketRepository(db_session, tenant_id=None)
        items, total = repo.list(limit=100, offset=0)

        tenant_ids = {item.tenant_id for item in items}
        assert two_tenants["tenant_a"]["tenant"].id in tenant_ids
        assert two_tenants["tenant_b"]["tenant"].id in tenant_ids

    def test_pagination(self, db_session, two_tenants):
        from app.repositories.ticket_repository import TicketRepository

        # Super admin sees all; test pagination
        repo = TicketRepository(db_session, tenant_id=None)
        items_page1, total = repo.list(limit=1, offset=0)
        items_page2, _ = repo.list(limit=1, offset=1)

        assert len(items_page1) == 1
        assert len(items_page2) == 1
        assert items_page1[0].id != items_page2[0].id
        assert total >= 2
