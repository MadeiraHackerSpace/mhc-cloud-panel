#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root (ex.: sudo bash $0)"
  exit 1
fi

install -m 0644 "${script_dir}/wsl.conf" /etc/wsl.conf

bash "${script_dir}/install-docker.sh"
bash "${script_dir}/apply-docker-config.sh"
