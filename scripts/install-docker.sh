#!/usr/bin/env bash
# install-docker.sh — instala Docker Engine + Docker Compose Plugin
# Suporte: Ubuntu/Debian, Fedora/RHEL/CentOS, macOS (via Homebrew)

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Verifica se já está instalado ────────────────────────────────────────────
if command -v docker &>/dev/null; then
  info "Docker já está instalado: $(docker --version)"
  if docker compose version &>/dev/null; then
    info "Docker Compose já está disponível: $(docker compose version)"
  fi
  exit 0
fi

OS="$(uname -s)"

# ── macOS ─────────────────────────────────────────────────────────────────────
if [[ "$OS" == "Darwin" ]]; then
  if ! command -v brew &>/dev/null; then
    error "Homebrew não encontrado. Instale em https://brew.sh e tente novamente."
  fi
  info "Instalando Docker Desktop via Homebrew..."
  brew install --cask docker
  info "Abra o Docker Desktop para concluir a configuração e tente novamente."
  exit 0
fi

# ── Linux ─────────────────────────────────────────────────────────────────────
if [[ "$OS" != "Linux" ]]; then
  error "Sistema operacional não suportado: $OS. Use o script .ps1 no Windows."
fi

if [[ "$EUID" -ne 0 ]]; then
  error "Execute como root ou com sudo: sudo bash $0"
fi

# Detecta distro
if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  DISTRO="${ID:-unknown}"
else
  error "Não foi possível detectar a distribuição Linux."
fi

info "Distribuição detectada: $DISTRO"

install_debian_ubuntu() {
  info "Instalando dependências..."
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg lsb-release

  info "Adicionando repositório oficial do Docker..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL "https://download.docker.com/linux/${DISTRO}/gpg" \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/${DISTRO} $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
}

install_fedora_rhel() {
  info "Instalando dependências..."
  dnf -y install dnf-plugins-core

  info "Adicionando repositório oficial do Docker..."
  dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

  dnf -y install docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
}

case "$DISTRO" in
  ubuntu|debian|linuxmint|pop)
    install_debian_ubuntu ;;
  fedora|rhel|centos|rocky|almalinux)
    install_fedora_rhel ;;
  *)
    error "Distribuição '$DISTRO' não suportada automaticamente. Consulte https://docs.docker.com/engine/install/" ;;
esac

# ── Inicia e habilita o serviço ───────────────────────────────────────────────
info "Iniciando serviço Docker..."
systemctl enable --now docker

# ── Adiciona usuário atual ao grupo docker (evita sudo) ───────────────────────
if [[ -n "${SUDO_USER:-}" ]]; then
  usermod -aG docker "$SUDO_USER"
  warn "Usuário '$SUDO_USER' adicionado ao grupo 'docker'."
  warn "Faça logout/login ou execute 'newgrp docker' para aplicar sem reiniciar."
fi

info "Docker instalado com sucesso!"
info "  $(docker --version)"
info "  $(docker compose version)"
