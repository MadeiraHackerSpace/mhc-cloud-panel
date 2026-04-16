#!/bin/bash
# check-status.sh — Verifica o estado atual do ambiente KVM/Proxmox

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail() { echo -e "${RED}[FAIL]${NC}  $*"; }

echo ""
echo "=== Status do Ambiente KVM/Proxmox ==="
echo ""

# 1. KVM
if [ -r /dev/kvm ]; then
    ok "/dev/kvm acessível"
else
    fail "/dev/kvm não acessível"
fi

# 2. libvirtd
if systemctl is-active --quiet libvirtd 2>/dev/null; then
    ok "libvirtd rodando"
else
    warn "libvirtd não está rodando — tente: sudo systemctl start libvirtd"
fi

# 3. Dependências
for cmd in virsh virt-install qemu-img qemu-system-x86_64; do
    if command -v "$cmd" &>/dev/null; then
        ok "$cmd instalado"
    else
        fail "$cmd NÃO instalado"
    fi
done

# 4. Rede default
echo ""
echo "--- Rede libvirt ---"
if virsh net-list 2>/dev/null | grep -q "default"; then
    ok "Rede 'default' ativa"
else
    warn "Rede 'default' não encontrada — será criada pelo script de setup"
fi

# 5. VM proxmox-ve
echo ""
echo "--- VM proxmox-ve ---"
VM_STATE=$(virsh list --all 2>/dev/null | grep "proxmox-ve" | awk '{print $3}')
if [ -z "$VM_STATE" ]; then
    warn "VM 'proxmox-ve' não existe ainda — execute o script de setup"
else
    ok "VM 'proxmox-ve' encontrada — estado: $VM_STATE"
    if [ "$VM_STATE" = "running" ]; then
        IP=$(virsh domifaddr proxmox-ve 2>/dev/null | grep ipv4 | awk '{print $4}' | cut -d'/' -f1)
        [ -n "$IP" ] && ok "IP da VM: $IP" || warn "IP ainda não atribuído (VM pode estar iniciando)"
    fi
fi

# 6. ISO
echo ""
echo "--- ISO Proxmox ---"
ISO_PATH="/var/lib/libvirt/images/proxmox-ve-9.0.iso"
if [ -f "$ISO_PATH" ]; then
    SIZE=$(du -sh "$ISO_PATH" 2>/dev/null | cut -f1)
    ok "ISO encontrada: $ISO_PATH ($SIZE)"
else
    warn "ISO não encontrada — será baixada pelo script de setup (~1.8GB)"
fi

# 7. Espaço em disco
echo ""
echo "--- Espaço em disco ---"
AVAIL=$(df -h /var/lib/libvirt/images 2>/dev/null | awk 'NR==2{print $4}')
if [ -n "$AVAIL" ]; then
    ok "Espaço disponível em /var/lib/libvirt/images: $AVAIL"
else
    warn "Não foi possível verificar espaço em /var/lib/libvirt/images"
fi

echo ""
echo "=== Próximo passo ==="
echo ""
if [ -z "$VM_STATE" ]; then
    echo "  Execute para criar a VM:"
    echo "  sudo bash scripts/quick-start-proxmox-kvm.sh"
elif [ "$VM_STATE" = "running" ]; then
    echo "  VM está rodando! Conecte ao console VNC:"
    echo "  sudo virt-viewer proxmox-ve"
    echo ""
    echo "  Ou teste a conectividade:"
    echo "  sudo bash scripts/proxmox-vm-utils.sh test-connection"
else
    echo "  VM existe mas está parada. Para iniciar:"
    echo "  sudo virsh start proxmox-ve"
fi
echo ""
