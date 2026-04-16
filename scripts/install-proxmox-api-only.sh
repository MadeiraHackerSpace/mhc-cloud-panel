#!/usr/bin/env bash
# install-proxmox-api-only.sh — Instala apenas a API do Proxmox (sem VMs)
# Para testar integração do MHC Cloud Panel
# Execute: sudo bash scripts/install-proxmox-api-only.sh

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
    warn "Este script foi feito para WSL2, mas pode funcionar em outros ambientes"
fi

# Verificar se é root
if [[ "$EUID" -ne 0 ]]; then
    error "Execute como root: sudo bash $0"
fi

info "=========================================="
info "Instalação Simplificada - Proxmox Mock API"
info "=========================================="
echo ""
warn "NOTA: Esta instalação NÃO instala o Proxmox real"
warn "Apenas configura o ambiente para usar o mock do MHC Cloud Panel"
echo ""

# Obter IP do WSL
WSL_IP=$(ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1 || echo "localhost")
info "IP do WSL: $WSL_IP"

# Criar arquivo de configuração
CONFIG_FILE="/tmp/mhc-proxmox-config.env"

cat > "$CONFIG_FILE" <<EOF
# Configuração para usar o Proxmox Mock do MHC Cloud Panel
# Copie estas linhas para o arquivo .env do projeto

# Mock do Proxmox (padrão - já está funcionando)
PROXMOX_HOST=http://proxmox_mock:8001
PROXMOX_USER=mock
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mock
PROXMOX_TOKEN_SECRET=mock
PROXMOX_VERIFY_SSL=false
PROXMOX_TIMEOUT_SECONDS=15
PROXMOX_RETRY_TOTAL=3

# Frontend (para console VNC - usar localhost)
NEXT_PUBLIC_PROXMOX_HOST=localhost
EOF

info "=========================================="
info "Configuração gerada!"
info "=========================================="
echo ""
cat "$CONFIG_FILE"
echo ""
info "O arquivo foi salvo em: $CONFIG_FILE"
echo ""
info "PRÓXIMOS PASSOS:"
info "1. O mock do Proxmox já está rodando no Docker"
info "2. Acesse http://localhost:3000/admin/infrastructure"
info "3. Você verá 2 nodes mockados (pve e pve2)"
info "4. Crie um plano e teste a contratação"
echo ""
warn "PARA USAR PROXMOX REAL:"
info "1. Instale Proxmox VE em uma VM ou servidor físico"
info "2. Configure usuário e token de API"
info "3. Atualize o .env com as credenciais reais"
info "4. Reinicie os containers: docker compose restart"
echo ""
info "Documentação completa: docs/PROXMOX_WSL_SETUP.md"
