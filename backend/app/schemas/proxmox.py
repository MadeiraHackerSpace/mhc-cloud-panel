from __future__ import annotations

from pydantic import BaseModel


class ProxmoxNodeInfo(BaseModel):
    node: str
    status: str | None = None
    maxcpu: int | None = None
    maxmem: int | None = None
    mem: int | None = None


class ProxmoxStorageInfo(BaseModel):
    storage: str
    content: str | None = None
    active: int | None = None
    total: int | None = None
    used: int | None = None


class ProxmoxTemplateInfo(BaseModel):
    node: str
    vmid: int
    name: str
