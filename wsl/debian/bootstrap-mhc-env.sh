#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root (ex.: sudo bash $0)"
  exit 1
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
project_root="${1:-${repo_root}}"

if [[ ! -d "${project_root}" ]]; then
  echo "Diretorio do projeto nao encontrado: ${project_root}"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "[1/7] Instalando pacotes base..."
apt-get update
apt-get -y install ca-certificates curl gnupg lsb-release git jq unzip zip build-essential pkg-config python3 python3-venv python3-pip libpq-dev

if [[ "${INSTALL_LIBVIRT:-0}" == "1" ]]; then
  echo "[1/7] Instalando KVM/libvirt (opcional)..."
  apt-get -y install qemu-system libvirt-daemon-system libvirt-clients virtinst qemu-utils
  systemctl enable --now libvirtd || true
fi

echo "[2/7] Instalando Docker no Debian WSL..."
bash "${script_dir}/setup-docker.sh"

echo "[3/7] Instalando Node.js LTS..."
install -m 0755 -d /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/nodesource.gpg ]]; then
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
fi
chmod a+r /etc/apt/keyrings/nodesource.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list
apt-get update
apt-get -y install nodejs

target_user="${SUDO_USER:-}"
if [[ -z "${target_user}" ]]; then
  target_user="$(awk -F: '$3 >= 1000 && $1 != "nobody" {print $1; exit}' /etc/passwd)"
fi

if [[ -n "${target_user}" ]] && id -u "${target_user}" >/dev/null 2>&1; then
  usermod -aG docker "${target_user}" || true
  if [[ "${INSTALL_LIBVIRT:-0}" == "1" ]]; then
    usermod -aG libvirt "${target_user}" || true
    usermod -aG kvm "${target_user}" || true
  fi
fi

run_as_target_user() {
  local cmd="$1"
  if [[ -n "${target_user}" ]] && id -u "${target_user}" >/dev/null 2>&1; then
    su - "${target_user}" -c "${cmd}"
  else
    bash -lc "${cmd}"
  fi
}

echo "[4/7] Instalando dependencias Python do backend..."
if [[ -f "${project_root}/backend/requirements.txt" ]]; then
  run_as_target_user "set -euo pipefail; cd '${project_root}/backend'; if [[ -d .venv && ! -x .venv/bin/python3 ]]; then rm -rf .venv; fi; python3 -m venv .venv; source .venv/bin/activate; python -m pip install --upgrade pip; pip install -r requirements.txt"
else
  echo "Arquivo backend/requirements.txt nao encontrado; pulando etapa."
fi

echo "[5/7] Instalando dependencias Node do frontend..."
if [[ -f "${project_root}/frontend/package-lock.json" ]]; then
  run_as_target_user "set -euo pipefail; cd '${project_root}/frontend'; npm ci"
else
  echo "Arquivo frontend/package-lock.json nao encontrado; pulando etapa."
fi

echo "[6/7] Validando ferramentas instaladas..."
docker --version
docker compose version
python3 --version
node --version
npm --version

echo "[7/7] Ambiente pronto."
echo "Projeto: ${project_root}"
if [[ -n "${target_user}" ]]; then
  echo "Usuario para uso do Docker sem sudo: ${target_user}"
  echo "Reabra o terminal Debian para aplicar o grupo docker."
fi
