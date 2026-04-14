#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root (ex.: sudo bash $0)"
  exit 1
fi

name="${PROXMOX_VM_NAME:-pve-lab}"
memory_mb="${PROXMOX_VM_MEMORY_MB:-8192}"
vcpus="${PROXMOX_VM_VCPUS:-4}"
disk_gb="${PROXMOX_VM_DISK_GB:-64}"
user_home="${HOME}"
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  sudo_user_home="$(getent passwd "${SUDO_USER}" | cut -d: -f6 || true)"
  if [[ -n "${sudo_user_home}" ]]; then
    user_home="${sudo_user_home}"
  fi
fi
iso_path="${PROXMOX_ISO_PATH:-${user_home}/isos/proxmox.iso}"
disk_path="${PROXMOX_VM_DISK_PATH:-/var/lib/libvirt/images/${name}.qcow2}"
vnc_listen="${PROXMOX_VNC_LISTEN:-127.0.0.1}"
vnc_port="${PROXMOX_VNC_PORT:-5901}"
connect_uri="${PROXMOX_LIBVIRT_URI:-qemu:///system}"
net_name="${PROXMOX_LIBVIRT_NETWORK:-default}"

if [[ ! -f "${iso_path}" ]]; then
  echo "ISO não encontrado em: ${iso_path}"
  echo "Baixe primeiro com:"
  echo "  bash wsl/debian/download-proxmox-iso.sh"
  exit 2
fi

for bin in virsh virt-install qemu-img; do
  if ! command -v "${bin}" >/dev/null 2>&1; then
    echo "Comando ausente: ${bin}"
    echo "Instale com:"
    echo "  sudo apt update && sudo apt install -y libvirt-clients virtinst qemu-utils libvirt-daemon-system qemu-system"
    exit 2
  fi
done

if [[ ! -e /dev/kvm ]]; then
  echo "/dev/kvm não encontrado. KVM pode não estar disponível neste ambiente."
else
  current_group="$(stat -c %G /dev/kvm 2>/dev/null || true)"
  if [[ -n "${current_group}" && "${current_group}" != "kvm" ]]; then
    if getent group kvm >/dev/null 2>&1; then
      true
    else
      groupadd -f kvm
    fi
    chgrp kvm /dev/kvm || true
    chmod 0660 /dev/kvm || true
  fi
fi

systemctl enable --now libvirtd >/dev/null 2>&1 || true

if ! virsh -c "${connect_uri}" net-info "${net_name}" >/dev/null 2>&1; then
  echo "Rede libvirt '${net_name}' não encontrada em ${connect_uri}."
  exit 2
fi

ensure_network_started() {
  local name="$1"
  local start_err
  start_err="$({ virsh -c "${connect_uri}" net-start "${name}" 2>&1 >/dev/null; } || true)"
  if [[ -z "${start_err}" ]]; then
    return 0
  fi

  if echo "${start_err}" | grep -qi "network is already active"; then
    return 0
  fi

  if echo "${start_err}" | grep -qi "already in use by interface virbr0"; then
    ip link show virbr0 >/dev/null 2>&1 || true
    ip link set virbr0 down >/dev/null 2>&1 || true
    ip link delete virbr0 type bridge >/dev/null 2>&1 || true
    start_err="$({ virsh -c "${connect_uri}" net-start "${name}" 2>&1 >/dev/null; } || true)"
    [[ -z "${start_err}" ]] && return 0
  fi

  echo "${start_err}" >&2
  return 1
}

create_fallback_network() {
  local fallback_name="${PROXMOX_LIBVIRT_FALLBACK_NETWORK:-pve-nat}"
  if virsh -c "${connect_uri}" net-info "${fallback_name}" >/dev/null 2>&1; then
    net_name="${fallback_name}"
    return 0
  fi

  for octet in 230 231 232 233 234 235 236 237 238 239; do
    local bridge="virbr${octet}"
    local ip="192.168.${octet}.1"
    local xml
    xml="$(mktemp)"
    cat > "${xml}" <<EOF
<network>
  <name>${fallback_name}</name>
  <forward mode='nat'/>
  <bridge name='${bridge}' stp='on' delay='0'/>
  <ip address='${ip}' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.${octet}.2' end='192.168.${octet}.254'/>
    </dhcp>
  </ip>
</network>
EOF
    if virsh -c "${connect_uri}" net-define "${xml}" >/dev/null 2>&1; then
      rm -f "${xml}"
      if ensure_network_started "${fallback_name}"; then
        virsh -c "${connect_uri}" net-autostart "${fallback_name}" >/dev/null 2>&1 || true
        net_name="${fallback_name}"
        return 0
      fi
      virsh -c "${connect_uri}" net-undefine "${fallback_name}" >/dev/null 2>&1 || true
    fi
    rm -f "${xml}"
  done

  return 1
}

if [[ "$(virsh -c "${connect_uri}" net-info "${net_name}" | awk -F': ' '/Active:/ {print $2}')" != "yes" ]]; then
  if ! ensure_network_started "${net_name}"; then
    if ! create_fallback_network; then
      echo "Falha ao iniciar rede '${net_name}' e falha ao criar rede NAT alternativa." >&2
      exit 2
    fi
  fi
fi
virsh -c "${connect_uri}" net-autostart "${net_name}" >/dev/null || true

if virsh -c "${connect_uri}" dominfo "${name}" >/dev/null 2>&1; then
  echo "VM já existe no libvirt: ${name}"
  echo "Lista:"
  virsh -c "${connect_uri}" list --all
  exit 0
fi

mkdir -p "$(dirname -- "${disk_path}")"
if [[ ! -f "${disk_path}" ]]; then
  qemu-img create -f qcow2 "${disk_path}" "${disk_gb}G" >/dev/null
fi

iso_for_vm="${iso_path}"
if id libvirt-qemu >/dev/null 2>&1; then
  if ! runuser -u libvirt-qemu -- test -r "${iso_path}" >/dev/null 2>&1; then
    boot_dir="/var/lib/libvirt/boot"
    mkdir -p "${boot_dir}"
    iso_for_vm="${boot_dir}/proxmox.iso"
    if [[ ! -f "${iso_for_vm}" ]]; then
      cp -f "${iso_path}" "${iso_for_vm}"
    fi
  fi
fi

echo "Criando VM do Proxmox no libvirt..."
echo "Nome: ${name}"
echo "CPU: ${vcpus}"
echo "RAM: ${memory_mb} MB"
echo "Disco: ${disk_path} (${disk_gb}G)"
echo "ISO: ${iso_for_vm}"
echo "VNC: ${vnc_listen}:${vnc_port}"
echo "Rede: ${net_name}"

virt_type="${PROXMOX_VIRT_TYPE:-auto}"
if [[ "${virt_type}" == "auto" ]]; then
  if [[ -e /dev/kvm ]]; then
    virt_type="kvm"
  else
    virt_type="qemu"
  fi
fi

run_install() {
  local vt="$1"
  virt-install \
    --connect "${connect_uri}" \
    --virt-type "${vt}" \
    --name "${name}" \
    --memory "${memory_mb}" \
    --vcpus "${vcpus}" \
    --cpu host-passthrough \
    --disk "path=${disk_path},bus=virtio" \
    --cdrom "${iso_for_vm}" \
    --network "network=${net_name},model=virtio" \
    --os-variant generic \
    --graphics "vnc,listen=${vnc_listen},port=${vnc_port}" \
    --noautoconsole
}

if ! run_install "${virt_type}"; then
  if [[ "${virt_type}" == "kvm" ]]; then
    echo "KVM indisponível. Tentando novamente com emulação (qemu)..."
    run_install "qemu"
  else
    exit 1
  fi
fi

echo "OK"
echo "Verifique:"
echo "  virsh -c ${connect_uri} list --all"
