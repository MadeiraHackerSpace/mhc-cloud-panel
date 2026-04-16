#!/bin/bash

# Utilitários para gerenciar a VM Proxmox VE

VM_NAME="proxmox-ve"
VM_IP="192.168.122.100"

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

log_cmd() {
    echo -e "${BLUE}[CMD]${NC} $1"
}

# Verificar se está rodando como root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script deve ser executado como root"
        exit 1
    fi
}

# Verificar status da VM
status() {
    log_info "Status da VM $VM_NAME:"
    virsh list --all | grep "$VM_NAME" || log_warn "VM não encontrada"
}

# Iniciar VM
start() {
    check_root
    log_info "Iniciando VM $VM_NAME..."
    virsh start "$VM_NAME" 2>/dev/null || log_warn "VM já está rodando"
    sleep 3
    log_info "VM iniciada. Aguardando boot..."
    sleep 10
    log_info "Conecte ao console VNC:"
    log_cmd "virt-viewer $VM_NAME"
}

# Parar VM
stop() {
    check_root
    log_info "Parando VM $VM_NAME..."
    virsh shutdown "$VM_NAME" 2>/dev/null || log_error "Falha ao parar VM"
    log_info "Aguardando shutdown..."
    sleep 5
}

# Forçar parada
force_stop() {
    check_root
    log_warn "Forçando parada da VM..."
    virsh destroy "$VM_NAME" 2>/dev/null || log_error "Falha ao forçar parada"
}

# Conectar ao console VNC
vnc() {
    log_info "Conectando ao console VNC..."
    VNC_DISPLAY=$(virsh vncdisplay "$VM_NAME" 2>/dev/null)
    if [ -z "$VNC_DISPLAY" ]; then
        log_error "VM não está rodando ou não tem console VNC"
        exit 1
    fi
    log_info "VNC Display: $VNC_DISPLAY"
    log_cmd "virt-viewer $VM_NAME"
    virt-viewer "$VM_NAME" &
}

# Obter IP da VM
get_ip() {
    log_info "Obtendo IP da VM..."
    IP=$(virsh domifaddr "$VM_NAME" 2>/dev/null | grep ipv4 | awk '{print $4}' | cut -d'/' -f1)
    if [ -z "$IP" ]; then
        log_warn "IP não encontrado. Usando IP estático configurado: $VM_IP"
        echo "$VM_IP"
    else
        echo "$IP"
    fi
}

# Testar conectividade
test_connection() {
    IP=$(get_ip)
    log_info "Testando conectividade com $IP..."
    
    if ping -c 1 -W 2 "$IP" &> /dev/null; then
        log_info "✓ Ping bem-sucedido"
        
        if timeout 5 bash -c "echo > /dev/tcp/$IP/8006" 2>/dev/null; then
            log_info "✓ Porta 8006 (Proxmox) está aberta"
            log_info "Acesse: https://$IP:8006"
        else
            log_warn "Porta 8006 ainda não está respondendo"
        fi
    else
        log_error "Não conseguiu fazer ping em $IP"
        log_info "Verifique se a VM está rodando e tem IP configurado"
    fi
}

# Criar snapshot
snapshot() {
    check_root
    if [ -z "$1" ]; then
        log_error "Uso: $0 snapshot <nome>"
        exit 1
    fi
    log_info "Criando snapshot '$1'..."
    virsh snapshot-create-as "$VM_NAME" "$1" --description "Snapshot criado em $(date)" || log_error "Falha ao criar snapshot"
}

# Listar snapshots
list_snapshots() {
    log_info "Snapshots da VM $VM_NAME:"
    virsh snapshot-list "$VM_NAME" 2>/dev/null || log_warn "Nenhum snapshot encontrado"
}

# Restaurar snapshot
restore_snapshot() {
    check_root
    if [ -z "$1" ]; then
        log_error "Uso: $0 restore-snapshot <nome>"
        exit 1
    fi
    log_warn "Restaurando snapshot '$1'..."
    virsh snapshot-revert "$VM_NAME" "$1" || log_error "Falha ao restaurar snapshot"
}

# Deletar snapshot
delete_snapshot() {
    check_root
    if [ -z "$1" ]; then
        log_error "Uso: $0 delete-snapshot <nome>"
        exit 1
    fi
    log_warn "Deletando snapshot '$1'..."
    virsh snapshot-delete "$VM_NAME" "$1" || log_error "Falha ao deletar snapshot"
}

# Mostrar informações da VM
info() {
    log_info "Informações da VM $VM_NAME:"
    virsh dominfo "$VM_NAME" 2>/dev/null || log_error "VM não encontrada"
    echo ""
    log_info "Interfaces de rede:"
    virsh domifaddr "$VM_NAME" 2>/dev/null || log_warn "Nenhuma interface encontrada"
}

# Menu de ajuda
usage() {
    cat << EOF
Utilitários para gerenciar VM Proxmox VE

Uso: $0 <comando> [argumentos]

Comandos:
    status              - Mostrar status da VM
    start               - Iniciar VM
    stop                - Parar VM gracefully
    force-stop          - Forçar parada da VM
    vnc                 - Conectar ao console VNC
    get-ip              - Obter IP da VM
    test-connection     - Testar conectividade
    info                - Mostrar informações da VM
    snapshot <nome>     - Criar snapshot
    list-snapshots      - Listar snapshots
    restore-snapshot    - Restaurar snapshot
    delete-snapshot     - Deletar snapshot
    help                - Mostrar esta mensagem

Exemplos:
    sudo $0 start
    sudo $0 vnc
    sudo $0 test-connection
    sudo $0 snapshot pre-config
    sudo $0 restore-snapshot pre-config

EOF
}

# Processar comando
case "${1:-help}" in
    status)
        status
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    force-stop)
        force_stop
        ;;
    vnc)
        vnc
        ;;
    get-ip)
        get_ip
        ;;
    test-connection)
        test_connection
        ;;
    info)
        info
        ;;
    snapshot)
        snapshot "$2"
        ;;
    list-snapshots)
        list_snapshots
        ;;
    restore-snapshot)
        restore_snapshot "$2"
        ;;
    delete-snapshot)
        delete_snapshot "$2"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Comando desconhecido: $1"
        usage
        exit 1
        ;;
esac
