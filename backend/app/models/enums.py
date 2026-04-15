from __future__ import annotations

import enum


class RoleName(str, enum.Enum):
    super_admin = "super_admin"
    operador = "operador"
    financeiro = "financeiro"
    suporte = "suporte"
    cliente = "cliente"


class ServiceStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
    cancelled = "cancelled"
    pending_removal = "pending_removal"
    failed = "failed"


class VMStatus(str, enum.Enum):
    provisioning = "provisioning"
    running = "running"
    stopped = "stopped"
    error = "error"
    deleted = "deleted"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    paid = "paid"
    overdue = "overdue"
    void = "void"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class TicketStatus(str, enum.Enum):
    open = "open"
    pending = "pending"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class ServiceActionType(str, enum.Enum):
    provision = "provision"
    start = "start"
    stop = "stop"
    reboot = "reboot"
    rebuild = "rebuild"
    reset_password = "reset_password"
    cancel = "cancel"
    suspend = "suspend"
    reactivate = "reactivate"
    migrate = "migrate"  # Live migration between Proxmox nodes (rebalancing/maintenance)
