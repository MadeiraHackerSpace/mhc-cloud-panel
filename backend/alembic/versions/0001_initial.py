"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-12

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    role_name = sa.Enum("super_admin", "operador", "financeiro", "suporte", "cliente", name="role_name")
    service_status = sa.Enum(
        "pending",
        "active",
        "suspended",
        "cancelled",
        "pending_removal",
        "failed",
        name="service_status",
    )
    vm_status = sa.Enum("provisioning", "running", "stopped", "error", "deleted", name="vm_status")
    invoice_status = sa.Enum("draft", "open", "paid", "overdue", "void", name="invoice_status")
    payment_status = sa.Enum("pending", "confirmed", "cancelled", name="payment_status")
    ticket_status = sa.Enum("open", "pending", "resolved", "closed", name="ticket_status")
    ticket_priority = sa.Enum("low", "normal", "high", "urgent", name="ticket_priority")
    job_status = sa.Enum("queued", "running", "succeeded", "failed", "cancelled", name="job_status")
    service_action_type = sa.Enum(
        "provision",
        "start",
        "stop",
        "reboot",
        "rebuild",
        "reset_password",
        "cancel",
        "suspend",
        "reactivate",
        name="service_action_type",
    )

    for enum_type in [
        role_name,
        service_status,
        vm_status,
        invoice_status,
        payment_status,
        ticket_status,
        ticket_priority,
        job_status,
        service_action_type,
    ]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", role_name, nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_quarterly", sa.Numeric(10, 2), nullable=True),
        sa.Column("vcpu", sa.Integer(), nullable=False),
        sa.Column("ram_mb", sa.Integer(), nullable=False),
        sa.Column("disk_gb", sa.Integer(), nullable=False),
        sa.Column("traffic_gb", sa.Integer(), nullable=False),
        sa.Column("ipv4_count", sa.Integer(), nullable=False),
        sa.Column("ipv6_enabled", sa.Boolean(), nullable=False),
        sa.Column("snapshots_enabled", sa.Boolean(), nullable=False),
        sa.Column("backups_enabled", sa.Boolean(), nullable=False),
        sa.Column("upgrade_downgrade_allowed", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_plans_is_active", "plans", ["is_active"])

    op.create_table(
        "proxmox_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("name", name="uq_proxmox_nodes_name"),
    )
    op.create_index("ix_proxmox_nodes_is_enabled", "proxmox_nodes", ["is_enabled"])

    op.create_table(
        "proxmox_storages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("content", sa.String(length=255), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("name", name="uq_proxmox_storages_name"),
    )
    op.create_index("ix_proxmox_storages_is_enabled", "proxmox_storages", ["is_enabled"])

    op.create_table(
        "proxmox_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("node", sa.String(length=64), nullable=False),
        sa.Column("vmid", sa.Integer(), nullable=False),
        sa.Column("storage", sa.String(length=64), nullable=True),
        sa.Column("cloud_init_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("name", name="uq_proxmox_templates_name"),
    )
    op.create_index("ix_proxmox_templates_is_enabled", "proxmox_templates", ["is_enabled"])

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("document", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.UniqueConstraint("tenant_id", name="uq_customers_tenant_id"),
    )
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False),
        sa.Column("totp_secret", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_role_id", "users", ["role_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("jti", name="uq_refresh_tokens_jti"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", service_status, nullable=False),
        sa.Column("billing_cycle", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pending_removal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_services_tenant_id", "services", ["tenant_id"])
    op.create_index("ix_services_customer_id", "services", ["customer_id"])
    op.create_index("ix_services_status", "services", ["status"])

    op.create_table(
        "virtual_machines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("proxmox_node", sa.String(length=64), nullable=False),
        sa.Column("proxmox_vmid", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", vm_status, nullable=False),
        sa.Column("primary_ipv4", sa.String(length=45), nullable=True),
        sa.Column("primary_ipv6", sa.String(length=64), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proxmox_templates.id"), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("service_id", name="uq_virtual_machines_service_id"),
    )
    op.create_index("ix_virtual_machines_tenant_id", "virtual_machines", ["tenant_id"])
    op.create_index("ix_virtual_machines_proxmox_node", "virtual_machines", ["proxmox_node"])
    op.create_index("ix_virtual_machines_proxmox_vmid", "virtual_machines", ["proxmox_vmid"])

    op.create_table(
        "ip_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("virtual_machine_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("virtual_machines.id"), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("ip_address", name="uq_ip_allocations_ip_address"),
    )
    op.create_index("ix_ip_allocations_tenant_id", "ip_allocations", ["tenant_id"])
    op.create_index("ix_ip_allocations_service_id", "ip_allocations", ["service_id"])

    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("status", invoice_status, nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("amount_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_customer_id", "invoices", ["customer_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_due_date", "invoices", ["due_date"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])
    op.create_index("ix_payments_status", "payments", ["status"])

    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("opened_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("status", ticket_status, nullable=False),
        sa.Column("priority", ticket_priority, nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tickets_tenant_id", "tickets", ["tenant_id"])
    op.create_index("ix_tickets_customer_id", "tickets", ["customer_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_priority", "tickets", ["priority"])

    op.create_table(
        "ticket_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_staff", sa.Boolean(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
    )
    op.create_index("ix_ticket_messages_ticket_id", "ticket_messages", ["ticket_id"])
    op.create_index("ix_ticket_messages_created_at", "ticket_messages", ["created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_notifications_tenant_id", "notifications", ["tenant_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("job_key", sa.String(length=120), nullable=False),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("celery_task_id", sa.String(length=120), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_tenant_id", "jobs", ["tenant_id"])
    op.create_index("ix_jobs_service_id", "jobs", ["service_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_job_key", "jobs", ["job_key"])

    op.create_table(
        "api_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("secret_ciphertext", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_api_credentials_tenant_id", "api_credentials", ["tenant_id"])
    op.create_index("ix_api_credentials_provider", "api_credentials", ["provider"])
    op.create_index("ix_api_credentials_is_active", "api_credentials", ["is_active"])

    op.create_table(
        "coupons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("percent_off", sa.Numeric(5, 2), nullable=True),
        sa.Column("amount_off", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("code", name="uq_coupons_code"),
    )
    op.create_index("ix_coupons_is_active", "coupons", ["is_active"])

    op.create_table(
        "service_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("virtual_machine_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("virtual_machines.id"), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", service_action_type, nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("ix_service_actions_tenant_id", "service_actions", ["tenant_id"])
    op.create_index("ix_service_actions_service_id", "service_actions", ["service_id"])
    op.create_index("ix_service_actions_action", "service_actions", ["action"])
    op.create_index("ix_service_actions_created_at", "service_actions", ["created_at"])

    op.create_table(
        "plan_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("plan_id", "key", name="uq_plan_features_plan_id_key"),
    )
    op.create_index("ix_plan_features_plan_id", "plan_features", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_plan_features_plan_id", table_name="plan_features")
    op.drop_table("plan_features")
    op.drop_index("ix_service_actions_created_at", table_name="service_actions")
    op.drop_index("ix_service_actions_action", table_name="service_actions")
    op.drop_index("ix_service_actions_service_id", table_name="service_actions")
    op.drop_index("ix_service_actions_tenant_id", table_name="service_actions")
    op.drop_table("service_actions")
    op.drop_index("ix_coupons_is_active", table_name="coupons")
    op.drop_table("coupons")
    op.drop_index("ix_api_credentials_is_active", table_name="api_credentials")
    op.drop_index("ix_api_credentials_provider", table_name="api_credentials")
    op.drop_index("ix_api_credentials_tenant_id", table_name="api_credentials")
    op.drop_table("api_credentials")
    op.drop_index("ix_jobs_job_key", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_service_id", table_name="jobs")
    op.drop_index("ix_jobs_tenant_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_tenant_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_ticket_messages_created_at", table_name="ticket_messages")
    op.drop_index("ix_ticket_messages_ticket_id", table_name="ticket_messages")
    op.drop_table("ticket_messages")
    op.drop_index("ix_tickets_priority", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_customer_id", table_name="tickets")
    op.drop_index("ix_tickets_tenant_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_invoice_id", table_name="payments")
    op.drop_index("ix_payments_tenant_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_invoices_due_date", table_name="invoices")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_customer_id", table_name="invoices")
    op.drop_index("ix_invoices_tenant_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_ip_allocations_service_id", table_name="ip_allocations")
    op.drop_index("ix_ip_allocations_tenant_id", table_name="ip_allocations")
    op.drop_table("ip_allocations")
    op.drop_index("ix_virtual_machines_proxmox_vmid", table_name="virtual_machines")
    op.drop_index("ix_virtual_machines_proxmox_node", table_name="virtual_machines")
    op.drop_index("ix_virtual_machines_tenant_id", table_name="virtual_machines")
    op.drop_table("virtual_machines")
    op.drop_index("ix_services_status", table_name="services")
    op.drop_index("ix_services_customer_id", table_name="services")
    op.drop_index("ix_services_tenant_id", table_name="services")
    op.drop_table("services")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_customers_tenant_id", table_name="customers")
    op.drop_table("customers")
    op.drop_index("ix_proxmox_templates_is_enabled", table_name="proxmox_templates")
    op.drop_table("proxmox_templates")
    op.drop_index("ix_proxmox_storages_is_enabled", table_name="proxmox_storages")
    op.drop_table("proxmox_storages")
    op.drop_index("ix_proxmox_nodes_is_enabled", table_name="proxmox_nodes")
    op.drop_table("proxmox_nodes")
    op.drop_index("ix_plans_is_active", table_name="plans")
    op.drop_table("plans")
    op.drop_table("tenants")
    op.drop_table("roles")

    bind = op.get_bind()
    for enum_type in [
        sa.Enum(name="service_action_type"),
        sa.Enum(name="job_status"),
        sa.Enum(name="ticket_priority"),
        sa.Enum(name="ticket_status"),
        sa.Enum(name="payment_status"),
        sa.Enum(name="invoice_status"),
        sa.Enum(name="vm_status"),
        sa.Enum(name="service_status"),
        sa.Enum(name="role_name"),
    ]:
        enum_type.drop(bind, checkfirst=True)
