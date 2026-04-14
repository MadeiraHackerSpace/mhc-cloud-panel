import os
import time
import uuid
from io import StringIO

import pytest


def _required_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Env var obrigatória ausente: {name}")
    return val


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _optional_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _load_private_key(paramiko, pem: str):
    errors: list[Exception] = []
    for key_cls in (getattr(paramiko, "Ed25519Key", None), getattr(paramiko, "RSAKey", None), getattr(paramiko, "ECDSAKey", None)):
        if key_cls is None:
            continue
        try:
            return key_cls.from_private_key(StringIO(pem))
        except Exception as exc:
            errors.append(exc)
    raise RuntimeError(f"Não foi possível carregar chave privada do jump host ({len(errors)} tentativas falharam)")


def _connect_jump_client(paramiko):
    jump_host = os.environ.get("TEST_JUMP_HOST") or os.environ.get("TEST_PROXMOX_SSH_HOST")
    if not jump_host:
        return None

    jump_port = _optional_int_env("TEST_JUMP_PORT", _optional_int_env("TEST_PROXMOX_SSH_PORT", 22))
    jump_user = os.environ.get("TEST_JUMP_USER") or os.environ.get("TEST_PROXMOX_SSH_USER") or "root"
    jump_password = os.environ.get("TEST_JUMP_PASSWORD") or os.environ.get("TEST_PROXMOX_SSH_PASSWORD")
    jump_key_pem = os.environ.get("TEST_JUMP_PRIVATE_KEY") or os.environ.get("TEST_PROXMOX_SSH_PRIVATE_KEY")

    if not jump_password and not jump_key_pem:
        raise RuntimeError("Para usar jump host, defina TEST_JUMP_PASSWORD ou TEST_JUMP_PRIVATE_KEY")

    jump = paramiko.SSHClient()
    jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    kwargs = {
        "hostname": jump_host,
        "port": jump_port,
        "username": jump_user,
        "timeout": 15,
        "banner_timeout": 15,
        "auth_timeout": 15,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if jump_password:
        kwargs["password"] = jump_password
    if jump_key_pem:
        kwargs["pkey"] = _load_private_key(paramiko, jump_key_pem)
    jump.connect(**kwargs)
    return jump


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
        cfg_deadline = time.time() + 120
        while True:
            try:
                pve.nodes(node).qemu(vmid).config.post(ciuser=ciuser, ipconfig0="ip=dhcp", sshkeys=ssh_public_key)
                break
            except Exception:
                if time.time() > cfg_deadline:
                    raise
                time.sleep(3)

        start_deadline = time.time() + 120
        while True:
            try:
                pve.nodes(node).qemu(vmid).status.start.post()
                break
            except Exception:
                if time.time() > start_deadline:
                    raise
                time.sleep(3)

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

        jump_client = None
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_deadline = time.time() + 180
        last_err: Exception | None = None
        while time.time() < ssh_deadline:
            try:
                sock = None
                if _bool_env("TEST_SSH_VIA_JUMP") or os.environ.get("TEST_JUMP_HOST") or os.environ.get("TEST_PROXMOX_SSH_HOST"):
                    jump_client = jump_client or _connect_jump_client(paramiko)
                    if jump_client is None:
                        raise RuntimeError("Jump host habilitado, mas TEST_JUMP_HOST/TEST_PROXMOX_SSH_HOST não definido")
                    transport = jump_client.get_transport()
                    if transport is None:
                        raise RuntimeError("Transporte SSH do jump host não disponível")
                    sock = transport.open_channel("direct-tcpip", (ip_addr, 22), ("127.0.0.1", 0))

                ssh.connect(
                    hostname=ip_addr,
                    username=ciuser,
                    pkey=key,
                    sock=sock,
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
        try:
            if "jump_client" in locals() and jump_client:
                jump_client.close()
        except Exception:
            pass
        if created_vmid is not None:
            try:
                pve.nodes(node).qemu(created_vmid).status.stop.post()
            except Exception:
                pass
            try:
                pve.nodes(node).qemu(created_vmid).delete()
            except Exception:
                pass
