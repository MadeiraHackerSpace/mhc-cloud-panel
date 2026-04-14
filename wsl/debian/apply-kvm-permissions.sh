#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root (ex.: sudo bash $0)"
  exit 1
fi

if [[ ! -e /dev/kvm ]]; then
  echo "/dev/kvm não existe. KVM pode não estar disponível neste ambiente."
  exit 2
fi

if getent group kvm >/dev/null 2>&1; then
  true
else
  groupadd -f kvm
fi

chgrp kvm /dev/kvm || true
chmod 0660 /dev/kvm || true

install -d /etc/udev/rules.d
cat > /etc/udev/rules.d/99-kvm.rules <<'EOF'
KERNEL=="kvm", GROUP="kvm", MODE="0660"
EOF

if command -v udevadm >/dev/null 2>&1; then
  udevadm control --reload-rules || true
  udevadm trigger /dev/kvm || true
fi

install -d /etc/systemd/system
cat > /etc/systemd/system/mhc-fix-kvm-perms.service <<'EOF'
[Unit]
Description=Fix /dev/kvm permissions for libvirt/qemu
After=systemd-udevd.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'if [ -e /dev/kvm ]; then chgrp kvm /dev/kvm && chmod 0660 /dev/kvm; fi'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

if command -v systemctl >/dev/null 2>&1; then
  systemctl daemon-reload || true
  systemctl enable --now mhc-fix-kvm-perms.service || true
fi

echo "OK"
