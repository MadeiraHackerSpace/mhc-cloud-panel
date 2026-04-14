#!/usr/bin/env bash
set -euo pipefail

url="${1:-}"
out="${2:-$HOME/isos/proxmox.iso}"

if [[ -z "${url}" ]]; then
  echo "Uso: $0 <URL_DO_ISO_PROXMOX> [caminho_saida]"
  echo "Exemplo: $0 https://enterprise.proxmox.com/iso/proxmox-ve_9.1-1.iso"
  exit 2
fi

dir="$(dirname -- "${out}")"
mkdir -p "${dir}"

tmp="${out}.partial"
rm -f "${tmp}"

echo "Baixando ISO..."
echo "URL: ${url}"
echo "Destino: ${out}"

curl -fL --retry 5 --retry-delay 2 --connect-timeout 15 -o "${tmp}" "${url}"
mv -f "${tmp}" "${out}"

echo "OK"
