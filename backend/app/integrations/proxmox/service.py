from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.errors import AppError


class ProxmoxError(AppError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message, details=details)
        self.code = "proxmox_error"
        self.status_code = 502


class ProxmoxAdapter(Protocol):
    def list_nodes(self) -> list[dict[str, Any]]: ...

    def list_storages(self, *, node: str) -> list[dict[str, Any]]: ...

    def list_qemu(self, *, node: str) -> list[dict[str, Any]]: ...

    def next_vmid(self) -> int: ...

    def clone_vm(self, *, node: str, template_vmid: int, new_vmid: int, name: str, storage: str | None) -> str | None: ...

    def config_vm(self, *, node: str, vmid: int, config: dict[str, Any]) -> None: ...

    def start_vm(self, *, node: str, vmid: int) -> None: ...

    def stop_vm(self, *, node: str, vmid: int) -> None: ...

    def reboot_vm(self, *, node: str, vmid: int) -> None: ...

    def current_status(self, *, node: str, vmid: int) -> dict[str, Any]: ...

    def delete_vm(self, *, node: str, vmid: int) -> None: ...


@dataclass(frozen=True)
class ProxmoxVMCreateSpec:
    name: str
    vcpu: int
    ram_mb: int
    disk_gb: int
    node: str
    template_vmid: int
    storage: str | None = None
    ipconfig0: str | None = None
    ciuser: str | None = None
    ssh_public_key: str | None = None
    tags: list[str] | None = None


class ProxmoxService:
    def __init__(self, adapter: ProxmoxAdapter):
        self.adapter = adapter
        self.settings = get_settings()

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "ProxmoxService":
        s = settings or get_settings()
        host = str(s.proxmox_host)
        if host.startswith("http://"):
            return cls(adapter=HttpMockAdapter(base_url=host, timeout_seconds=s.proxmox_timeout_seconds))
        return cls(adapter=ProxmoxerAdapter.from_settings(s))

    @retry(stop=stop_after_attempt(get_settings().proxmox_retry_total), wait=wait_exponential(min=1, max=8), reraise=True)
    def list_nodes(self) -> list[dict[str, Any]]:
        return self.adapter.list_nodes()

    @retry(stop=stop_after_attempt(get_settings().proxmox_retry_total), wait=wait_exponential(min=1, max=8), reraise=True)
    def list_storages(self, *, node: str) -> list[dict[str, Any]]:
        return self.adapter.list_storages(node=node)

    @retry(stop=stop_after_attempt(get_settings().proxmox_retry_total), wait=wait_exponential(min=1, max=8), reraise=True)
    def list_templates(self, *, node: str) -> list[dict[str, Any]]:
        all_qemu = self.adapter.list_qemu(node=node)
        return [x for x in all_qemu if int(x.get("template") or 0) == 1]

    @retry(stop=stop_after_attempt(get_settings().proxmox_retry_total), wait=wait_exponential(min=1, max=8), reraise=True)
    def create_vm_from_template(self, *, spec: ProxmoxVMCreateSpec) -> int:
        new_vmid = self.adapter.next_vmid()
        self.adapter.clone_vm(
            node=spec.node,
            template_vmid=spec.template_vmid,
            new_vmid=new_vmid,
            name=spec.name,
            storage=spec.storage,
        )
        config: dict[str, Any] = {
            "cores": spec.vcpu,
            "memory": spec.ram_mb,
        }
        if spec.ipconfig0:
            config["ipconfig0"] = spec.ipconfig0
        if spec.ciuser:
            config["ciuser"] = spec.ciuser
        if spec.ssh_public_key:
            config["sshkeys"] = spec.ssh_public_key
        if spec.tags:
            config["tags"] = ",".join(spec.tags)

        self.adapter.config_vm(node=spec.node, vmid=new_vmid, config=config)
        return new_vmid

    def start_vm(self, *, node: str, vmid: int) -> None:
        self.adapter.start_vm(node=node, vmid=vmid)

    def stop_vm(self, *, node: str, vmid: int) -> None:
        self.adapter.stop_vm(node=node, vmid=vmid)

    def reboot_vm(self, *, node: str, vmid: int) -> None:
        self.adapter.reboot_vm(node=node, vmid=vmid)

    def current_status(self, *, node: str, vmid: int) -> dict[str, Any]:
        return self.adapter.current_status(node=node, vmid=vmid)

    def delete_vm(self, *, node: str, vmid: int) -> None:
        self.adapter.delete_vm(node=node, vmid=vmid)


class ProxmoxerAdapter:
    def __init__(self, proxmox: Any, timeout_seconds: int):
        self.proxmox = proxmox
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "ProxmoxerAdapter":
        if not settings.proxmox_host:
            raise ProxmoxError("PROXMOX_HOST não configurado")
        if not settings.proxmox_user or not settings.proxmox_token_name or not settings.proxmox_token_secret:
            raise ProxmoxError("Credenciais do Proxmox não configuradas")

        try:
            from proxmoxer import ProxmoxAPI
        except Exception as exc:
            raise ProxmoxError("Dependência proxmoxer não disponível") from exc

        user = f"{settings.proxmox_user}@{settings.proxmox_realm}"
        host = str(settings.proxmox_host)
        proxmox = ProxmoxAPI(
            host,
            user=user,
            token_name=settings.proxmox_token_name,
            token_value=settings.proxmox_token_secret,
            verify_ssl=settings.proxmox_verify_ssl,
            timeout=settings.proxmox_timeout_seconds,
        )

        return cls(proxmox=proxmox, timeout_seconds=settings.proxmox_timeout_seconds)

    def list_nodes(self) -> list[dict[str, Any]]:
        return list(self.proxmox.nodes.get())

    def list_storages(self, *, node: str) -> list[dict[str, Any]]:
        return list(self.proxmox.nodes(node).storage.get())

    def list_qemu(self, *, node: str) -> list[dict[str, Any]]:
        return list(self.proxmox.nodes(node).qemu.get())

    def next_vmid(self) -> int:
        vmid = self.proxmox.cluster.nextid.get()
        return int(vmid)

    def clone_vm(self, *, node: str, template_vmid: int, new_vmid: int, name: str, storage: str | None) -> str | None:
        payload: dict[str, Any] = {
            "newid": new_vmid,
            "name": name,
            "full": 1,
        }
        if storage:
            payload["storage"] = storage
        res = self.proxmox.nodes(node).qemu(template_vmid).clone.post(**payload)
        return res

    def config_vm(self, *, node: str, vmid: int, config: dict[str, Any]) -> None:
        self.proxmox.nodes(node).qemu(vmid).config.post(**config)

    def start_vm(self, *, node: str, vmid: int) -> None:
        self.proxmox.nodes(node).qemu(vmid).status.start.post()

    def stop_vm(self, *, node: str, vmid: int) -> None:
        self.proxmox.nodes(node).qemu(vmid).status.stop.post()

    def reboot_vm(self, *, node: str, vmid: int) -> None:
        self.proxmox.nodes(node).qemu(vmid).status.reboot.post()

    def current_status(self, *, node: str, vmid: int) -> dict[str, Any]:
        return dict(self.proxmox.nodes(node).qemu(vmid).status.current.get())

    def delete_vm(self, *, node: str, vmid: int) -> None:
        self.proxmox.nodes(node).qemu(vmid).delete()


class HttpMockAdapter:
    def __init__(self, *, base_url: str, timeout_seconds: int):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _get(self, path: str) -> Any:
        resp = self.session.get(self._url(path), timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json().get("data")

    def _post(self, path: str, *, data: dict[str, Any] | None = None) -> Any:
        resp = self.session.post(self._url(path), data=data or {}, timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json().get("data")

    def _delete(self, path: str) -> Any:
        resp = self.session.delete(self._url(path), timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json().get("data")

    def list_nodes(self) -> list[dict[str, Any]]:
        return list(self._get("/api2/json/nodes") or [])

    def list_storages(self, *, node: str) -> list[dict[str, Any]]:
        return list(self._get(f"/api2/json/nodes/{node}/storage") or [])

    def list_qemu(self, *, node: str) -> list[dict[str, Any]]:
        return list(self._get(f"/api2/json/nodes/{node}/qemu") or [])

    def next_vmid(self) -> int:
        return int(self._get("/api2/json/cluster/nextid"))

    def clone_vm(self, *, node: str, template_vmid: int, new_vmid: int, name: str, storage: str | None) -> str | None:
        payload: dict[str, Any] = {"newid": str(new_vmid), "name": name, "full": "1"}
        if storage:
            payload["storage"] = storage
        return self._post(f"/api2/json/nodes/{node}/qemu/{template_vmid}/clone", data=payload)

    def config_vm(self, *, node: str, vmid: int, config: dict[str, Any]) -> None:
        self._post(f"/api2/json/nodes/{node}/qemu/{vmid}/config", data=config)

    def start_vm(self, *, node: str, vmid: int) -> None:
        self._post(f"/api2/json/nodes/{node}/qemu/{vmid}/status/start")

    def stop_vm(self, *, node: str, vmid: int) -> None:
        self._post(f"/api2/json/nodes/{node}/qemu/{vmid}/status/stop")

    def reboot_vm(self, *, node: str, vmid: int) -> None:
        self._post(f"/api2/json/nodes/{node}/qemu/{vmid}/status/reboot")

    def current_status(self, *, node: str, vmid: int) -> dict[str, Any]:
        return dict(self._get(f"/api2/json/nodes/{node}/qemu/{vmid}/status/current") or {})

    def delete_vm(self, *, node: str, vmid: int) -> None:
        self._delete(f"/api2/json/nodes/{node}/qemu/{vmid}")
