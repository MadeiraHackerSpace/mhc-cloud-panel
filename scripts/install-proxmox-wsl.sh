#!/usr/bin/env bash
# install-proxmox-wsl.sh — Instala Proxmox VE API no Debian WSL2
# Execute: sudo bash scripts/install-proxmox-wsl.sh

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Verificar se está rodando no WSL
if ! grep -qi microsoft /proc/version; then
    error "Este script deve ser executado no WSL2 (Debian)"
fi

# Verificar se é root
if [[ "$EUID" -ne 0 ]]; then
    error "Execute como root: sudo bash $0"
fi

info "Instalando Proxmox VE API no WSL2..."

# Atualizar sistema
info "Atualizando sistema..."
apt update -qq
apt upgrade -y -qq

# Instalar dependências
info "Instalando dependências..."
apt install -y -qq wget curl gnupg2 software-properties-common apt-transport-https ca-certificates

# Detectar versão do Debian
DEBIAN_VERSION=$(lsb_release -cs)
info "Debian detectado: $DEBIAN_VERSION"

# Adicionar repositório Proxmox
info "Adicionando repositório Proxmox..."
if [[ "$DEBIAN_VERSION" == "bookworm" ]]; then
    wget -q https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg \
        -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg
    echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
        > /etc/apt/sources.list.d/pve-install-repo.list
elif [[ "$DEBIAN_VERSION" == "bullseye" ]]; then
    wget -q https://enterprise.proxmox.com/debian/proxmox-release-bullseye.gpg \
        -O /etc/apt/trusted.gpg.d/proxmox-release-bullseye.gpg
    echo "deb http://download.proxmox.com/debian/pve bullseye pve-no-subscription" \
        > /etc/apt/sources.list.d/pve-install-repo.list
else
    error "Versão do Debian não suportada: $DEBIAN_VERSION"
fi

apt update -qq

# Instalar Proxmox (apenas componentes essenciais)
info "Instalando componentes do Proxmox..."
DEBIAN_FRONTEND=noninteractive apt install -y -qq \
    proxmox-ve \
    postfix \
    open-iscsi

# Configurar usuário e token
info "Configurando usuário mhc@pam..."
pveum user add mhc@pam --comment "MHC Cloud Panel API User" 2>/dev/null || true

# Definir senha
info "Definindo senha para mhc@pam..."
echo "mhc:mhc123" | chpasswd

# Criar role
info "Criando role MHC_API..."
pveum role add MHC_API \
    -privs "VM.Allocate VM.Clone VM.Config.Disk VM.Config.CPU VM.Config.Memory VM.Config.Network VM.Config.Options VM.Monitor VM.Audit VM.PowerMgmt Datastore.AllocateSpace Datastore.Audit" \
    2>/dev/null || true

# Atribuir role
info "Atribuindo permissões..."
pveum aclmod / -user mhc@pam -role MHC_API

# Criar token
info "Criando token de API..."
TOKEN_OUTPUT=$(pveum user token add mhc@pam mhc-token --privsep 0 2>&1 || echo "")
if [[ "$TOKEN_OUTPUT" =~ value:\ ([a-f0-9-]+) ]]; then
    TOKEN="${BASH_REMATCH[1]}"
    info "Token criado: $TOKEN"
else
    warn "Token já existe ou erro ao criar. Use: pveum user token list mhc@pam"
fi

# Criar diretórios de storage
info "Criando estrutura de storage..."
mkdir -p /var/lib/vz/template/iso
mkdir -p /var/lib/vz/template/cache
mkdir -p /var/lib/vz/images

# Iniciar serviços
info "Iniciando serviços do Proxmox..."
systemctl start pvedaemon || warn "pvedaemon falhou ao iniciar"
systemctl start pveproxy || warn "pveproxy falhou ao iniciar"
systemctl start pvestatd || warn "pvestatd falhou ao iniciar"

# Verificar status
info "Verificando serviços..."
systemctl is-active pvedaemon && info "✓ pvedaemon: ativo" || warn "✗ pvedaemon: inativo"
systemctl is-active pveproxy && info "✓ pveproxy: ativo" || warn "✗ pveproxy: inativo"

# Obter IP do WSL
WSL_IP=$(ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
info "IP do WSL: $WSL_IP"

# Testar API
info "Testando API do Proxmox..."
sleep 2
if curl -k -s https://localhost:8006/api2/json/version >/dev/null 2>&1; then
    info "✓ API do Proxmox está respondendo"
else
    warn "✗ API do Proxmox não está respondendo. Verifique os logs: journalctl -u pveproxy"
fi

# Exibir informações finais
echo ""
info "=========================================="
info "Proxmox VE API instalado com sucesso!"
info "=========================================="
echo ""
info "Configurações para o .env do MHC Cloud Panel:"
echo ""
echo "PROXMOX_HOST=https://${WSL_IP}:8006"
echo "PROXMOX_USER=mhc"
echo "PROXMOX_REALM=pam"
echo "PROXMOX_TOKEN_NAME=mhc-token"
echo "PROXMOX_TOKEN_SECRET=${TOKEN:-<execute: pveum user token list mhc@pam>}"
echo "PROXMOX_VERIFY_SSL=false"
echo "NEXT_PUBLIC_PROXMOX_HOST=${WSL_IP}"
echo ""
info "Próximos passos:"
info "1. Copie as configurações acima para o .env"
info "2. Reinicie os containers: docker compose restart"
info "3. Acesse http://localhost:3000/admin/infrastructure"
echo ""
warn "LIMITAÇÃO: VMs reais não funcionam no WSL (sem KVM)"
warn "Use containers LXC ou teste apenas a API"
