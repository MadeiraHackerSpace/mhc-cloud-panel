#!/bin/bash

# Setup Proxmox VE 9.0 em VM KVM no Debian WSL
# Este script cria uma VM com libvirt e instala Proxmox VE 9.0

set -e

# Configurações
PROXMOX_ISO_URL="https://enterprise.proxmox.com/iso/proxmox-ve_9.0-1.iso-20240906T120532Z"
PROXMOX_ISO_PATH="/var/lib/libvirt/images/proxmox-ve-9.0.iso"
VM_NAME="proxmox-ve"
VM_DISK_PATH="/var/lib/libvirt/images/${VM_NAME}.qcow2"
VM_DISK_SIZE="50G"
VM_RAM="4096"
VM_CPUS="4"
VM_IP="192.168.122.100"
VM_GATEWAY="192.168.122.1"
VM_NETMASK="255.255.255.0"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está rodando como root
if [[ $EUID -ne 0 ]]; then
    log_error "Este script deve ser executado como root"
    exit 1
fi

# Verificar dependências
log_info "Verificando dependências..."
for cmd in virsh qemu-system-x86_64 virt-install; do
    if ! command -v $cmd &> /dev/null; then
        log_error "$cmd não está instalado"
        exit 1
    fi
done

# Verificar se libvirtd está rodando
if ! systemctl is-active --quiet libvirtd; then
    log_info "Iniciando libvirtd..."
    systemctl start libvirtd
fi

# Verificar se a rede padrão existe
if ! virsh net-list | grep -q "default"; then
    log_info "Criando rede padrão..."
    virsh net-define /dev/stdin <<EOF
<network>
  <name>default</name>
  <forward mode='nat'/>
  <bridge name='virbr0' stp='on' delay='0'/>
  <ip address='192.168.122.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.122.2' end='192.168.122.254'/>
    </dhcp>
  </ip>
</network>
EOF
    virsh net-start default
    virsh net-autostart default
fi

# Baixar ISO se não existir
if [ ! -f "$PROXMOX_ISO_PATH" ]; then
    log_info "Baixando Proxmox VE 9.0 ISO..."
    log_warn "Isso pode levar alguns minutos (~800MB)..."
    
    mkdir -p "$(dirname "$PROXMOX_ISO_PATH")"
    
    if ! wget -q --show-progress -O "$PROXMOX_ISO_PATH" "$PROXMOX_ISO_URL"; then
        log_error "Falha ao baixar ISO"
        rm -f "$PROXMOX_ISO_PATH"
        exit 1
    fi
    log_info "ISO baixada com sucesso"
else
    log_info "ISO já existe em $PROXMOX_ISO_PATH"
fi

# Verificar se VM já existe
if virsh list --all | grep -q "$VM_NAME"; then
    log_warn "VM $VM_NAME já existe"
    read -p "Deseja remover e recriar? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        log_info "Removendo VM existente..."
        virsh destroy "$VM_NAME" 2>/dev/null || true
        virsh undefine "$VM_NAME" --remove-all-storage 2>/dev/null || true
        sleep 2
    else
        log_info "Usando VM existente"
        exit 0
    fi
fi

# Criar disco da VM
log_info "Criando disco da VM ($VM_DISK_SIZE)..."
qemu-img create -f qcow2 "$VM_DISK_PATH" "$VM_DISK_SIZE"

# Criar VM com virt-install
log_info "Criando VM Proxmox VE..."
virt-install \
    --name "$VM_NAME" \
    --memory "$VM_RAM" \
    --vcpus "$VM_CPUS" \
    --disk path="$VM_DISK_PATH",format=qcow2 \
    --cdrom "$PROXMOX_ISO_PATH" \
    --network network=default,model=virtio \
    --graphics vnc,listen=0.0.0.0 \
    --console pty,target_type=virtio \
    --boot cdrom,hd \
    --os-type linux \
    --os-variant debian12 \
    --noautoconsole \
    --wait=-1

log_info "VM criada com sucesso!"
log_info ""
log_info "Próximos passos:"
log_info "1. Conectar ao console VNC:"
log_info "   virsh vncdisplay $VM_NAME"
log_info ""
log_info "2. Ou usar virt-viewer:"
log_info "   virt-viewer $VM_NAME"
log_info ""
log_info "3. Durante a instalação, configure:"
log_info "   - Hostname: proxmox-ve"
log_info "   - IP: $VM_IP"
log_info "   - Gateway: $VM_GATEWAY"
log_info "   - Netmask: $VM_NETMASK"
log_info ""
log_info "4. Após a instalação, acesse:"
log_info "   https://$VM_IP:8006"
log_info ""
log_info "5. Para parar a VM:"
log_info "   virsh shutdown $VM_NAME"
log_info ""
log_info "6. Para iniciar a VM:"
log_info "   virsh start $VM_NAME"
