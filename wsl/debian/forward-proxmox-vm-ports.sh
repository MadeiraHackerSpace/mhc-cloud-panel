#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root (ex.: sudo bash $0)"
  exit 1
fi

vm_ip="${1:-}"
connect_uri="${PROXMOX_LIBVIRT_URI:-qemu:///system}"
net_name="${PROXMOX_LIBVIRT_NETWORK:-pve-nat}"
listen_host="${PROXMOX_FORWARD_LISTEN_HOST:-127.0.0.1}"
port_web="${PROXMOX_FORWARD_WEB_PORT:-8006}"
port_ssh="${PROXMOX_FORWARD_SSH_PORT:-2222}"
target_web_port="${PROXMOX_TARGET_WEB_PORT:-8006}"
target_ssh_port="${PROXMOX_TARGET_SSH_PORT:-22}"

if [[ -z "${vm_ip}" ]]; then
  vm_ip="$(virsh -c "${connect_uri}" net-dhcp-leases "${net_name}" 2>/dev/null | awk 'NR>2 && $4 ~ /^[0-9]+\./ {sub(/\\/.*/,\"\",$4); print $4; exit}')"
fi

if [[ -z "${vm_ip}" ]]; then
  echo "IP da VM não encontrado."
  echo "Informe manualmente: sudo bash $0 <IP_DA_VM>"
  echo "Ou aguarde DHCP e verifique:"
  echo "  sudo virsh -c ${connect_uri} net-dhcp-leases ${net_name}"
  exit 2
fi

if ! command -v socat >/dev/null 2>&1; then
  apt-get update
  apt-get -y install socat
fi

systemctl stop mhc-proxmox-forward.service >/dev/null 2>&1 || true

install -d /etc/systemd/system
cat > /etc/systemd/system/mhc-proxmox-forward.service <<EOF
[Unit]
Description=Forward Proxmox VM ports to localhost (${listen_host})
After=network.target libvirtd.service

[Service]
Type=simple
ExecStart=/bin/sh -c 'exec socat TCP-LISTEN:${port_web},fork,reuseaddr,bind=${listen_host} TCP:${vm_ip}:${target_web_port} & socat TCP-LISTEN:${port_ssh},fork,reuseaddr,bind=${listen_host} TCP:${vm_ip}:${target_ssh_port} && wait'
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload || true
systemctl enable --now mhc-proxmox-forward.service

echo "OK"
echo "Proxmox Web (via forward): https://${listen_host}:${port_web}"
echo "SSH (via forward): ssh -p ${port_ssh} root@${listen_host}"
