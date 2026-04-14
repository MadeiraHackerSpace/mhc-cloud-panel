#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root (ex.: sudo bash $0)"
  exit 1
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

install -d /etc/docker
install -m 0644 "${script_dir}/daemon.json" /etc/docker/daemon.json

if command -v systemctl >/dev/null 2>&1; then
  systemctl restart docker
else
  if command -v service >/dev/null 2>&1; then
    service docker restart || true
  fi
fi
