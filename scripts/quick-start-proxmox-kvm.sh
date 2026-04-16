#!/bin/bash

# Quick Start: Proxmox VE 9.0 em VM KVM
# Este script automatiza todo o processo de setup

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

# Verificar se está rodando como root
if [[ $EUID -ne 0 ]]; then
    log_error "Este script deve ser executado com sudo"
    exit 1
fi

# Menu
show_menu() {
    echo ""
    echo -e "${BLUE}Proxmox VE 9.0 em VM KVM - Quick Start${NC}"
    echo "========================================"
    echo "1. Criar VM Proxmox (download + setup)"
    echo "2. Iniciar VM existente"
    echo "3. Conectar ao console VNC"
    echo "4. Testar conectividade"
    echo "5. Configurar para MHC Cloud Panel"
    echo "6. Ver status da VM"
    echo "7. Parar VM"
    echo "8. Sair"
    echo ""
    read -p "Escolha uma opção (1-8): " choice
}

# Criar VM
create_vm() {
    log_step "Criando VM Proxmox VE 9.0"
    
    if ! command -v virt-install &> /dev/null; then
        log_error "virt-install não está instalado"
        log_info "Execute: sudo apt-get install -y virt-install"
        return 1
    fi
    
    # Verificar se VM já existe
    if virsh list --all | grep -q "proxmox-ve"; then
        log_warn "VM proxmox-ve já existe"
        read -p "Deseja remover e recriar? (s/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            log_info "Removendo VM existente..."
            virsh destroy proxmox-ve 2>/dev/null || true
            virsh undefine proxmox-ve --remove-all-storage 2>/dev/null || true
            sleep 2
        else
            return 0
        fi
    fi
    
    # Executar script de setup
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$SCRIPT_DIR/setup-proxmox-vm-kvm.sh" ]; then
        "$SCRIPT_DIR/setup-proxmox-vm-kvm.sh"
    else
        log_error "Script setup-proxmox-vm-kvm.sh não encontrado"
        return 1
    fi
}

# Iniciar VM
start_vm() {
    log_step "Iniciando VM Proxmox VE"
    
    if ! virsh list --all | grep -q "proxmox-ve"; then
        log_error "VM proxmox-ve não existe"
        return 1
    fi
    
    if virsh list | grep -q "proxmox-ve"; then
        log_warn "VM já está rodando"
        return 0
    fi
    
    log_info "Iniciando VM..."
    virsh start proxmox-ve
    
    log_info "Aguardando boot (30 segundos)..."
    sleep 30
    
    log_info "✓ VM iniciada"
    log_info "Conecte ao console VNC com: virt-viewer proxmox-ve"
}

# Conectar VNC
connect_vnc() {
    log_step "Conectando ao console VNC"
    
    if ! virsh list | grep -q "proxmox-ve"; then
        log_error "VM não está rodando"
        return 1
    fi
    
    if ! command -v virt-viewer &> /dev/null; then
        log_error "virt-viewer não está instalado"
        log_info "Execute: sudo apt-get install -y virt-viewer"
        
        # Mostrar alternativa
        VNC_DISPLAY=$(virsh vncdisplay proxmox-ve 2>/dev/null)
        log_info "Conecte manualmente ao VNC: localhost:5900"
        return 1
    fi
    
    log_info "Abrindo virt-viewer..."
    virt-viewer proxmox-ve &
}

# Testar conectividade
test_connection() {
    log_step "Testando conectividade"
    
    PROXMOX_HOST="192.168.122.100"
    
    log_info "Testando ping em $PROXMOX_HOST..."
    if ping -c 1 -W 2 "$PROXMOX_HOST" &> /dev/null; then
        log_info "✓ Ping bem-sucedido"
    else
        log_warn "Ping falhou - VM pode não estar pronta"
        return 1
    fi
    
    log_info "Testando porta 8006..."
    if timeout 5 bash -c "echo > /dev/tcp/$PROXMOX_HOST/8006" 2>/dev/null; then
        log_info "✓ Porta 8006 aberta"
        log_info "Acesse: https://$PROXMOX_HOST:8006"
    else
        log_warn "Porta 8006 não respondendo - Proxmox ainda está iniciando"
        return 1
    fi
}

# Configurar para MHC Cloud Panel
configure_mhc() {
    log_step "Configurando para MHC Cloud Panel"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ ! -f "$SCRIPT_DIR/configure-proxmox-vm.sh" ]; then
        log_error "Script configure-proxmox-vm.sh não encontrado"
        return 1
    fi
    
    read -p "IP do Proxmox (padrão: 192.168.122.100): " proxmox_ip
    proxmox_ip=${proxmox_ip:-192.168.122.100}
    
    read -sp "Senha do root do Proxmox: " proxmox_pass
    echo
    
    "$SCRIPT_DIR/configure-proxmox-vm.sh" "$proxmox_ip" "$proxmox_pass"
    
    log_info ""
    log_info "✓ Configuração concluída"
    log_info "Arquivo .env.proxmox foi criado"
    log_info "Copie as variáveis para seu .env principal"
}

# Ver status
show_status() {
    log_step "Status da VM Proxmox VE"
    
    if virsh list --all | grep -q "proxmox-ve"; then
        virsh list --all | grep "proxmox-ve"
        
        if virsh list | grep -q "proxmox-ve"; then
            log_info "VM está rodando"
            
            IP=$(virsh domifaddr proxmox-ve 2>/dev/null | grep ipv4 | awk '{print $4}' | cut -d'/' -f1)
            if [ -n "$IP" ]; then
                log_info "IP: $IP"
            fi
        else
            log_warn "VM está parada"
        fi
    else
        log_error "VM não existe"
    fi
}

# Parar VM
stop_vm() {
    log_step "Parando VM Proxmox VE"
    
    if ! virsh list | grep -q "proxmox-ve"; then
        log_warn "VM não está rodando"
        return 0
    fi
    
    log_info "Enviando comando de shutdown..."
    virsh shutdown proxmox-ve
    
    log_info "Aguardando parada (30 segundos)..."
    for i in {1..30}; do
        if ! virsh list | grep -q "proxmox-ve"; then
            log_info "✓ VM parada"
            return 0
        fi
        sleep 1
    done
    
    log_warn "VM não parou gracefully, forçando parada..."
    virsh destroy proxmox-ve
    log_info "✓ VM parada"
}

# Loop principal
while true; do
    show_menu
    
    case $choice in
        1)
            create_vm
            ;;
        2)
            start_vm
            ;;
        3)
            connect_vnc
            ;;
        4)
            test_connection
            ;;
        5)
            configure_mhc
            ;;
        6)
            show_status
            ;;
        7)
            stop_vm
            ;;
        8)
            log_info "Saindo..."
            exit 0
            ;;
        *)
            log_error "Opção inválida"
            ;;
    esac
done
