import os
import time
import uuid

import pytest


def _required_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Env var obrigatória ausente: {name}")
    return val


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


@pytest.mark.skipif(not _bool_env("REAL_PROXMOX"), reason="REAL_PROXMOX não habilitado")
def test_real_proxmox_clone_and_ssh():
    proxmox_host = _required_env("PROXMOX_HOST")
    proxmox_user = _required_env("PROXMOX_USER")
    proxmox_realm = os.environ.get("PROXMOX_REALM", "pve")
    token_name = _required_env("PROXMOX_TOKEN_NAME")
    token_secret = _required_env("PROXMOX_TOKEN_SECRET")
    node = _required_env("TEST_PROXMOX_NODE")
    template_vmid = int(_required_env("TEST_TEMPLATE_VMID"))
    ciuser = os.environ.get("TEST_CIUSER", "mendsec")

    try:
        from proxmoxer import ProxmoxAPI
    except Exception as exc:
        raise RuntimeError("Dependência proxmoxer não disponível") from exc

    try:
        import paramiko
    except Exception as exc:
        raise RuntimeError("Dependência paramiko não disponível") from exc

    pve = ProxmoxAPI(
        proxmox_host,
        user=f"{proxmox_user}@{proxmox_realm}",
        token_name=token_name,
        token_value=token_secret,
        verify_ssl=os.environ.get("PROXMOX_VERIFY_SSL", "true").lower() in {"1", "true", "yes", "on"},
        timeout=int(os.environ.get("PROXMOX_TIMEOUT_SECONDS", "30")),
    )

    key = paramiko.RSAKey.generate(bits=2048)
    ssh_public_key = f"{key.get_name()} {key.get_base64()} test@mhc-cloud-panel"

    name = f"mhc-it-{uuid.uuid4().hex[:8]}"
    vmid = int(pve.cluster.nextid.get())

    created_vmid: int | None = None
    try:
        pve.nodes(node).qemu(template_vmid).clone.post(newid=vmid, name=name, full=1)
        created_vmid = vmid
        pve.nodes(node).qemu(vmid).config.post(ciuser=ciuser, ipconfig0="ip=dhcp", sshkeys=ssh_public_key)
        pve.nodes(node).qemu(vmid).status.start.post()

        ip_addr: str | None = None
        deadline = time.time() + 300
        while time.time() < deadline and not ip_addr:
            try:
                res = pve.nodes(node).qemu(vmid).agent("network-get-interfaces").get()
                for iface in res.get("result") or []:
                    for addr in iface.get("ip-addresses") or []:
                        if addr.get("ip-address-type") != "ipv4":
                            continue
                        ip = str(addr.get("ip-address") or "")
                        if not ip or ip.startswith("127.") or ip.startswith("169.254."):
                            continue
                        ip_addr = ip
                        break
                    if ip_addr:
                        break
            except Exception:
                ip_addr = None
            if not ip_addr:
                time.sleep(5)

        if not ip_addr:
            raise RuntimeError("Não foi possível obter IP via qemu-guest-agent (confira se o template tem qemu-guest-agent ativo)")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_deadline = time.time() + 180
        last_err: Exception | None = None
        while time.time() < ssh_deadline:
            try:
                ssh.connect(
                    hostname=ip_addr,
                    username=ciuser,
                    pkey=key,
                    timeout=10,
                    banner_timeout=10,
                    auth_timeout=10,
                    look_for_keys=False,
                    allow_agent=False,
                )
                _, stdout, _ = ssh.exec_command("whoami")
                assert stdout.read().decode().strip() == ciuser
                ssh.close()
                last_err = None
                break
            except Exception as exc:
                last_err = exc
                time.sleep(5)

        if last_err:
            raise RuntimeError(f"Falha ao conectar via SSH em {ciuser}@{ip_addr}: {last_err}") from last_err
    finally:
        if created_vmid is not None:
            try:
                pve.nodes(node).qemu(created_vmid).status.stop.post()
            except Exception:
                pass
            try:
                pve.nodes(node).qemu(created_vmid).delete()
            except Exception:
                pass
