#!/usr/bin/env bash
set -euo pipefail

name="${1:-${PROXMOX_VM_NAME:-pve-lab}}"
connect_uri="${PROXMOX_LIBVIRT_URI:-qemu:///system}"
net_name="${PROXMOX_LIBVIRT_NETWORK:-pve-nat}"

echo "VM: ${name}"
echo "Libvirt URI: ${connect_uri}"
echo "Rede: ${net_name}"
echo

sudo virsh -c "${connect_uri}" list --all || true
echo

echo "Display (VNC):"
sudo virsh -c "${connect_uri}" domdisplay "${name}" || true
echo

echo "Interfaces:"
sudo virsh -c "${connect_uri}" domiflist "${name}" || true
echo

echo "DHCP leases (${net_name}):"
sudo virsh -c "${connect_uri}" net-dhcp-leases "${net_name}" || true
