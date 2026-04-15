import os
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _test_env():
    os.environ.setdefault("SEED_ON_STARTUP", "false")
    if "DATABASE_URL" not in os.environ:
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db = os.environ.get("POSTGRES_DB", "mhc_cloud_panel")
        user = os.environ.get("POSTGRES_USER", "mhc")
        password = os.environ.get("POSTGRES_PASSWORD", "mhc")
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture()
def client(monkeypatch):
    from app.core.config import get_settings
    import app.core.database as dbmod

    get_settings.cache_clear()
    dbmod._engine = None
    dbmod._sessionmaker = None

    from app.core.database import get_engine, get_sessionmaker
    from app.core.security import hash_password
    from app.main import create_app
    from app.models.base import Base
    from app.models.customer import Customer
    from app.models.enums import RoleName
    from app.models.plan import Plan
    from app.models.proxmox_template import ProxmoxTemplate
    from app.models.role import Role
    from app.models.tenant import Tenant
    from app.models.user import User

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = get_sessionmaker()()
    try:
        roles = {}
        for r in RoleName:
            role = Role(name=r, description=r.value)
            db.add(role)
            db.commit()
            db.refresh(role)
            roles[r.value] = role

        tenant = Tenant(name="Tenant Teste", slug="tenant-teste", is_active=True)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        customer = Customer(tenant_id=tenant.id, display_name="Cliente Teste", email="cliente@teste.local")
        db.add(customer)
        db.commit()

        user = User(
            tenant_id=tenant.id,
            role_id=roles["cliente"].id,
            email="cliente@teste.local",
            full_name="Cliente Teste",
            password_hash=hash_password("senha12345"),
            is_active=True,
            is_email_verified=True,
        )
        db.add(user)
        db.commit()

        # Super-admin user for admin endpoint tests
        admin_user = User(
            tenant_id=None,  # global super admin has no tenant
            role_id=roles["super_admin"].id,
            email="admin@teste.local",
            full_name="Admin Teste",
            password_hash=hash_password("adminpass123"),
            is_active=True,
            is_email_verified=True,
        )
        db.add(admin_user)
        db.commit()

        plan = Plan(
            name="Bronze",
            price_monthly=Decimal("29.90"),
            price_quarterly=Decimal("79.90"),
            vcpu=1,
            ram_mb=1024,
            disk_gb=25,
            traffic_gb=500,
            ipv4_count=1,
            ipv6_enabled=True,
            snapshots_enabled=False,
            backups_enabled=False,
            upgrade_downgrade_allowed=True,
            is_active=True,
            # placement_policy uses the default ('none') — no explicit field needed
        )
        db.add(plan)
        template = ProxmoxTemplate(name="Ubuntu", node="pve", vmid=9000, storage="local-lvm", is_enabled=True)
        db.add(template)
        db.commit()
    finally:
        db.close()

    class DummyAsyncResult:
        id = "dummy-task-id"

    from app.tasks import provision_vm as task_module

    monkeypatch.setattr(task_module.provision_vm, "delay", lambda *_args, **_kwargs: DummyAsyncResult())

    # Mock ProxmoxService.list_nodes so NodeScheduler works without a real cluster
    _mock_nodes = [
        {
            "node": "pve",
            "status": "online",
            "mem": 4 * 1024 * 1024 * 1024,
            "maxmem": 32 * 1024 * 1024 * 1024,
            "cpu": 0.05,
            "maxcpu": 8,
            "disk": 100 * 1024 * 1024 * 1024,
            "maxdisk": 500 * 1024 * 1024 * 1024,
        },
        {
            "node": "pve2",
            "status": "online",
            "mem": 2 * 1024 * 1024 * 1024,
            "maxmem": 64 * 1024 * 1024 * 1024,
            "cpu": 0.02,
            "maxcpu": 16,
            "disk": 50 * 1024 * 1024 * 1024,
            "maxdisk": 1000 * 1024 * 1024 * 1024,
        },
    ]
    monkeypatch.setattr(
        "app.integrations.proxmox.service.ProxmoxService.list_nodes",
        lambda self: _mock_nodes,
    )

    app = create_app()
    with TestClient(app) as c:
        yield c
