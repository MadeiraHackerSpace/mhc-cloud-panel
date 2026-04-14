from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_engine, get_sessionmaker
from app.core.security import hash_password
from app.models.base import Base
from app.models.customer import Customer
from app.models.enums import InvoiceStatus, RoleName, ServiceStatus, VMStatus
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.proxmox_template import ProxmoxTemplate
from app.models.role import Role
from app.models.service import Service
from app.models.tenant import Tenant
from app.models.user import User
from app.models.virtual_machine import VirtualMachine


def seed_if_enabled() -> None:
    settings = get_settings()
    if not settings.seed_on_startup:
        return
    Base.metadata.create_all(bind=get_engine())
    seed()


def seed() -> None:
    db = get_sessionmaker()()
    try:
        roles_by_name: dict[str, Role] = {}
        for name in RoleName:
            existing = db.scalar(select(Role).where(Role.name == name))
            if existing:
                roles_by_name[name.value] = existing
                continue
            role = Role(name=name, description=name.value)
            db.add(role)
            db.commit()
            db.refresh(role)
            roles_by_name[name.value] = role

        def ensure_user(email: str, full_name: str, role_name: str, tenant_id=None) -> User:
            existing = db.scalar(select(User).where(User.email == email))
            if existing:
                return existing
            user = User(
                tenant_id=tenant_id,
                role_id=roles_by_name[role_name].id,
                email=email,
                full_name=full_name,
                password_hash=hash_password("admin12345"),
                is_active=True,
                is_email_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        ensure_user("superadmin@mhc.local", "Super Admin", "super_admin", None)
        ensure_user("operador@mhc.local", "Operador", "operador", None)

        tenant = db.scalar(select(Tenant).where(Tenant.slug == "cliente-demo"))
        if not tenant:
            tenant = Tenant(name="Cliente Demo", slug="cliente-demo", is_active=True)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        customer = db.scalar(select(Customer).where(Customer.tenant_id == tenant.id, Customer.deleted_at.is_(None)))
        if not customer:
            customer = Customer(tenant_id=tenant.id, display_name="Cliente Demo", email="cliente@mhc.local")
            db.add(customer)
            db.commit()
            db.refresh(customer)

        ensure_user("cliente@mhc.local", "Cliente Demo", "cliente", tenant.id)

        def ensure_plan(name: str, price: Decimal, vcpu: int, ram_mb: int, disk_gb: int) -> Plan:
            existing = db.scalar(select(Plan).where(Plan.name == name, Plan.deleted_at.is_(None)))
            if existing:
                return existing
            plan = Plan(
                name=name,
                price_monthly=price,
                price_quarterly=price * Decimal("2.85"),
                vcpu=vcpu,
                ram_mb=ram_mb,
                disk_gb=disk_gb,
                traffic_gb=2000,
                ipv4_count=1,
                ipv6_enabled=True,
                snapshots_enabled=False,
                backups_enabled=False,
                upgrade_downgrade_allowed=True,
                is_active=True,
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)
            return plan

        bronze = ensure_plan("Bronze", Decimal("29.90"), 1, 1024, 25)
        silver = ensure_plan("Silver", Decimal("49.90"), 2, 2048, 50)
        gold = ensure_plan("Gold", Decimal("89.90"), 4, 4096, 100)

        t1 = db.scalar(select(ProxmoxTemplate).where(ProxmoxTemplate.name == "Ubuntu 22.04 Cloud-Init"))
        if not t1:
            t1 = ProxmoxTemplate(name="Ubuntu 22.04 Cloud-Init", node="pve", vmid=9000, storage="local-lvm", is_enabled=True)
            db.add(t1)
        t2 = db.scalar(select(ProxmoxTemplate).where(ProxmoxTemplate.name == "Debian 12 Cloud-Init"))
        if not t2:
            t2 = ProxmoxTemplate(name="Debian 12 Cloud-Init", node="pve", vmid=9001, storage="local-lvm", is_enabled=True)
            db.add(t2)
        db.commit()

        existing_service = db.scalar(select(Service).where(Service.tenant_id == tenant.id, Service.name == "VPS Demo"))
        if not existing_service:
            service = Service(
                tenant_id=tenant.id,
                customer_id=customer.id,
                plan_id=silver.id,
                name="VPS Demo",
                status=ServiceStatus.active,
                billing_cycle="monthly",
                started_at=datetime.now(UTC) - timedelta(days=10),
            )
            db.add(service)
            db.commit()
            db.refresh(service)
            vm = VirtualMachine(
                tenant_id=tenant.id,
                service_id=service.id,
                proxmox_node="pve",
                proxmox_vmid=110,
                name="VPS Demo",
                status=VMStatus.stopped,
                template_id=t1.id,
            )
            db.add(vm)
            inv = Invoice(
                tenant_id=tenant.id,
                customer_id=customer.id,
                service_id=service.id,
                number=f"INV-{datetime.now(UTC).strftime('%Y%m%d')}-DEMO",
                status=InvoiceStatus.paid,
                amount_total=silver.price_monthly,
                due_date=datetime.now(UTC) - timedelta(days=3),
                paid_at=datetime.now(UTC) - timedelta(days=2),
                currency="BRL",
            )
            db.add(inv)
            inv2 = Invoice(
                tenant_id=tenant.id,
                customer_id=customer.id,
                service_id=service.id,
                number=f"INV-{datetime.now(UTC).strftime('%Y%m%d')}-DEMO2",
                status=InvoiceStatus.open,
                amount_total=silver.price_monthly,
                due_date=datetime.now(UTC) + timedelta(days=3),
                currency="BRL",
            )
            db.add(inv2)
            db.commit()
    finally:
        db.close()
