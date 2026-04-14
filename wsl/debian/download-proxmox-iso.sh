#!/usr/bin/env bash
set -euo pipefail

default_url="https://enterprise.proxmox.com/iso/proxmox-ve_9.1-1.iso"
url="${1:-$default_url}"
out="${2:-$HOME/isos/proxmox.iso}"

force="${FORCE:-0}"

dir="$(dirname -- "${out}")"
mkdir -p "${dir}"

tmp="${out}.partial"

if [[ -f "${out}" && "${force}" != "1" ]]; then
  echo "ISO já existe em: ${out}"
  echo "Para baixar novamente, rode com FORCE=1"
  exit 0
fi

echo "Baixando ISO..."
echo "URL: ${url}"
echo "Destino: ${out}"

curl -fL -C - --retry 5 --retry-delay 2 --connect-timeout 15 -o "${tmp}" "${url}"
mv -f "${tmp}" "${out}"

echo "OK"
