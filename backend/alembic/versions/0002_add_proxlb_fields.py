"""add_proxlb_fields

Revision ID: 0002_add_proxlb_fields
Revises: 0001_initial
Create Date: 2026-04-14

Adds fields introduced by the ProxLB-inspired improvements:

  proxmox_nodes:
    - is_maintenance  (BOOLEAN, default False) — maintenance mode flag
    - notes           (TEXT, nullable)          — operator notes
    - Index ix_proxmox_nodes_is_maintenance

  plans:
    - placement_policy (ENUM placement_policy, default 'none') — affinity rules

  service_action_type (PG ENUM):
    - ADD VALUE 'migrate' — live migration between nodes
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_add_proxlb_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ── 1. proxmox_nodes: is_maintenance + notes ─────────────────────────────
    existing_cols = {c["name"] for c in inspector.get_columns("proxmox_nodes")}

    if "is_maintenance" not in existing_cols:
        op.add_column(
            "proxmox_nodes",
            sa.Column("is_maintenance", sa.Boolean(), nullable=False, server_default="false"),
        )

    if "notes" not in existing_cols:
        op.add_column(
            "proxmox_nodes",
            sa.Column("notes", sa.Text(), nullable=True),
        )

    existing_indexes = {i["name"] for i in inspector.get_indexes("proxmox_nodes")}
    if "ix_proxmox_nodes_is_maintenance" not in existing_indexes:
        op.create_index(
            "ix_proxmox_nodes_is_maintenance",
            "proxmox_nodes",
            ["is_maintenance"],
        )

    # ── 2. plans: placement_policy ────────────────────────────────────────────
    placement_policy = sa.Enum(
        "none",
        "affinity",
        "anti_affinity",
        "pinned",
        name="placement_policy",
    )
    placement_policy.create(bind, checkfirst=True)

    existing_plan_cols = {c["name"] for c in inspector.get_columns("plans")}
    if "placement_policy" not in existing_plan_cols:
        op.add_column(
            "plans",
            sa.Column(
                "placement_policy",
                sa.Enum("none", "affinity", "anti_affinity", "pinned", name="placement_policy"),
                nullable=False,
                server_default="none",
            ),
        )

    # ── 3. service_action_type: ADD VALUE 'migrate' ───────────────────────────
    # Check current enum values before adding to avoid error if already present
    result = bind.execute(
        sa.text("SELECT enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'service_action_type'")
    )
    existing_values = {row[0] for row in result}
    if "migrate" not in existing_values:
        bind.execute(
            sa.text("ALTER TYPE service_action_type ADD VALUE IF NOT EXISTS 'migrate'")
        )


def downgrade() -> None:
    bind = op.get_bind()

    # Remove placement_policy column and type
    op.drop_column("plans", "placement_policy")
    sa.Enum(name="placement_policy").drop(bind, checkfirst=True)

    # Remove proxmox_nodes fields
    op.drop_index("ix_proxmox_nodes_is_maintenance", table_name="proxmox_nodes")
    op.drop_column("proxmox_nodes", "is_maintenance")
    op.drop_column("proxmox_nodes", "notes")

    # NOTE: PostgreSQL does not support removing enum values (ALTER TYPE … DROP VALUE).
    # To fully revert service_action_type, a manual recreation of the type is required.
    # This downgrade leaves 'migrate' in the enum intentionally to avoid data loss.
