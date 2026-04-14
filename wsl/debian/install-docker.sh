#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute como root (ex.: sudo bash $0)"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get -y install ca-certificates curl

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

if getent group docker >/dev/null 2>&1; then
  true
else
  groupadd docker
fi

target_user="${SUDO_USER:-}"
if [[ -n "${target_user}" ]]; then
  usermod -aG docker "${target_user}"
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl enable docker
  systemctl restart docker
else
  if command -v service >/dev/null 2>&1; then
    service docker start || true
  fi
fi
