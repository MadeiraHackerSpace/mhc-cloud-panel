#!/bin/bash
# check-status.sh — Verifica o estado do Proxmox VE instalado no Debian WSL
# Execute: bash scripts/check-status.sh (não precisa de sudo para a maioria das verificações)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail() { echo -e "${RED}[FAIL]${NC}  $*"; }

echo ""
echo "=== Status do Proxmox VE no Debian WSL ==="
echo ""

# 1. Serviços principais do Proxmox
echo "--- Serviços Proxmox ---"
for svc in pve-cluster pvedaemon pveproxy pvestatd; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        ok "$svc: ativo"
    else
        fail "$svc: inativo — sudo systemctl restart $svc"
    fi
done

# 2. /etc/pve montado
echo ""
echo "--- Filesystem do cluster ---"
if mountpoint -q /etc/pve 2>/dev/null; then
    ok "/etc/pve montado (pmxcfs OK)"
else
    fail "/etc/pve não montado — pve-cluster precisa estar rodando"
fi

# 3. IP do WSL (relevante para o portproxy)
echo ""
echo "--- Rede ---"
WSL_IP=$(ip addr show eth0 2>/dev/null | awk '/inet / {print $2}' | cut -d/ -f1)
if [ -n "$WSL_IP" ]; then
    ok "IP do WSL (eth0): $WSL_IP"
else
    warn "Não foi possível obter o IP do eth0"
fi

# 4. /etc/hosts correto
echo ""
echo "--- /etc/hosts ---"
HOSTNAME=$(hostname)
if grep -q "$WSL_IP" /etc/hosts 2>/dev/null && ! grep -q "127\.0\.1\.1.*$HOSTNAME" /etc/hosts 2>/dev/null; then
    ok "/etc/hosts: hostname '$HOSTNAME' resolve para IP real"
elif grep -q "127\.0\.1\.1.*$HOSTNAME" /etc/hosts 2>/dev/null; then
    fail "/etc/hosts: hostname aponta para loopback (127.0.1.1) — pmxcfs vai falhar"
    echo "       Corrija: sudo sed -i 's/127\.0\.1\.1/$WSL_IP/' /etc/hosts"
else
    warn "/etc/hosts: entrada para '$HOSTNAME' não encontrada"
fi

# 5. API respondendo
echo ""
echo "--- API Proxmox ---"
if curl -sk --max-time 8 https://127.0.0.1:8006/api2/json/version -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q "401\|200"; then
    ok "pveproxy respondendo em https://127.0.0.1:8006 (HTTP 401 = autenticação necessária, OK)"
else
    fail "pveproxy não está respondendo em 127.0.0.1:8006"
    echo "       Verifique: sudo journalctl -u pveproxy -n 20"
fi

# 6. pvesh funciona
echo ""
echo "--- pvesh (cliente local) ---"
if sudo pvesh get /version &>/dev/null 2>&1; then
    VERSION=$(sudo pvesh get /version 2>/dev/null | awk '/version/{print $3}' | head -1)
    ok "pvesh OK — Proxmox VE $VERSION"
else
    warn "pvesh não respondeu (pode precisar de sudo)"
fi

# 7. Token mhc@pam
echo ""
echo "--- Token de API ---"
if sudo pveum user token list mhc@pam 2>/dev/null | grep -q "mhc-token"; then
    ok "Token mhc@pam!mhc-token existe"
else
    warn "Token mhc@pam!mhc-token não encontrado"
    echo "       Crie com: sudo pveum user token add mhc@pam mhc-token --privsep 0"
fi

echo ""
echo "=== Resumo ==="
echo ""
if systemctl is-active --quiet pveproxy 2>/dev/null && mountpoint -q /etc/pve 2>/dev/null; then
    echo "  Proxmox VE está rodando."
    echo "  Web UI: https://127.0.0.1:8006 (com netsh portproxy ativo no Windows)"
    echo ""
    echo "  Para verificar/criar o portproxy (PowerShell como Admin):"
    echo "  .\\scripts\\setup-proxmox-portforward.ps1 -WslIp $WSL_IP"
else
    echo "  Alguns serviços estão com problema. Veja os erros acima."
    echo "  Guia de troubleshooting: PROXMOX_START.md"
fi
echo ""
