#!/bin/bash

# Configurar Proxmox VE após instalação
# Este script configura o Proxmox com usuário, role e token de API para o MHC Cloud Panel

set -e

# Configurações
PROXMOX_HOST="${1:-192.168.122.100}"
PROXMOX_USER="root"
PROXMOX_REALM="pam"
PROXMOX_TOKEN_NAME="mhc-token"
PROXMOX_PASSWORD="${2:-}"

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

# Verificar conectividade
check_connectivity() {
    log_info "Verificando conectividade com $PROXMOX_HOST..."
    
    if ! ping -c 1 -W 2 "$PROXMOX_HOST" &> /dev/null; then
        log_error "Não conseguiu fazer ping em $PROXMOX_HOST"
        exit 1
    fi
    
    if ! timeout 5 bash -c "echo > /dev/tcp/$PROXMOX_HOST/8006" 2>/dev/null; then
        log_error "Porta 8006 não está respondendo em $PROXMOX_HOST"
        log_info "Aguarde alguns minutos para o Proxmox iniciar completamente"
        exit 1
    fi
    
    log_info "✓ Conectividade OK"
}

# Obter ticket de autenticação
get_ticket() {
    if [ -z "$PROXMOX_PASSWORD" ]; then
        read -sp "Digite a senha do root do Proxmox: " PROXMOX_PASSWORD
        echo
    fi
    
    log_info "Obtendo ticket de autenticação..."
    
    TICKET_RESPONSE=$(curl -s -k -X POST \
        "https://$PROXMOX_HOST:8006/api2/json/access/ticket" \
        -d "username=$PROXMOX_USER@$PROXMOX_REALM&password=$PROXMOX_PASSWORD")
    
    TICKET=$(echo "$TICKET_RESPONSE" | grep -o '"ticket":"[^"]*' | cut -d'"' -f4)
    CSRF=$(echo "$TICKET_RESPONSE" | grep -o '"CSRFPreventionToken":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$TICKET" ]; then
        log_error "Falha ao autenticar. Verifique a senha."
        exit 1
    fi
    
    log_info "✓ Autenticação bem-sucedida"
}

# Criar token de API
create_api_token() {
    log_info "Criando token de API..."
    
    TOKEN_RESPONSE=$(curl -s -k -X POST \
        "https://$PROXMOX_HOST:8006/api2/json/access/users/$PROXMOX_USER@$PROXMOX_REALM/tokens/$PROXMOX_TOKEN_NAME" \
        -H "Cookie: PVEAuthCookie=$TICKET" \
        -H "CSRFPreventionToken: $CSRF" \
        -d "privsep=0")
    
    TOKEN_VALUE=$(echo "$TOKEN_RESPONSE" | grep -o '"value":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$TOKEN_VALUE" ]; then
        log_warn "Token pode já existir ou houve erro"
        log_info "Tentando obter token existente..."
        
        # Listar tokens
        TOKENS=$(curl -s -k -X GET \
            "https://$PROXMOX_HOST:8006/api2/json/access/users/$PROXMOX_USER@$PROXMOX_REALM/tokens" \
            -H "Cookie: PVEAuthCookie=$TICKET" \
            -H "CSRFPreventionToken: $CSRF")
        
        TOKEN_VALUE=$(echo "$TOKENS" | grep -o '"value":"[^"]*' | head -1 | cut -d'"' -f4)
        
        if [ -z "$TOKEN_VALUE" ]; then
            log_error "Não foi possível criar ou obter token"
            exit 1
        fi
    fi
    
    log_info "✓ Token criado/obtido com sucesso"
    echo "$TOKEN_VALUE"
}

# Obter informações do cluster
get_cluster_info() {
    log_info "Obtendo informações do cluster..."
    
    CLUSTER_INFO=$(curl -s -k -X GET \
        "https://$PROXMOX_HOST:8006/api2/json/cluster/resources" \
        -H "Cookie: PVEAuthCookie=$TICKET" \
        -H "CSRFPreventionToken: $CSRF")
    
    echo "$CLUSTER_INFO" | grep -o '"node":"[^"]*' | head -1 | cut -d'"' -f4
}

# Gerar arquivo .env
generate_env() {
    local token_value="$1"
    local node_name="$2"
    
    log_info "Gerando arquivo .env..."
    
    cat > .env.proxmox << EOF
# Configuração Proxmox VE para o MHC Cloud Panel

# Proxmox Host
PROXMOX_HOST=https://$PROXMOX_HOST:8006
PROXMOX_USER=$PROXMOX_USER
PROXMOX_REALM=$PROXMOX_REALM
PROXMOX_TOKEN_NAME=$PROXMOX_TOKEN_NAME
PROXMOX_TOKEN_SECRET=$token_value
PROXMOX_VERIFY_SSL=false

# Frontend
NEXT_PUBLIC_PROXMOX_HOST=$PROXMOX_HOST

# Node padrão
PROXMOX_DEFAULT_NODE=$node_name

EOF
    
    log_info "✓ Arquivo .env.proxmox criado"
    log_info ""
    log_info "Conteúdo do arquivo:"
    cat .env.proxmox
}

# Main
main() {
    log_info "Configurando Proxmox VE em $PROXMOX_HOST"
    log_info ""
    
    check_connectivity
    get_ticket
    TOKEN=$(create_api_token)
    NODE=$(get_cluster_info)
    
    log_info ""
    log_info "Configuração concluída!"
    log_info ""
    log_info "Token de API: $TOKEN"
    log_info "Node padrão: $NODE"
    log_info ""
    
    generate_env "$TOKEN" "$NODE"
    
    log_info ""
    log_info "Próximos passos:"
    log_info "1. Revisar o arquivo .env.proxmox"
    log_info "2. Copiar as variáveis para seu .env principal"
    log_info "3. Reiniciar os containers Docker:"
    log_cmd "docker compose restart"
    log_info ""
    log_info "4. Testar a conexão via:"
    log_cmd "curl -k https://$PROXMOX_HOST:8006/api2/json/version"
}

# Mostrar uso
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    cat << EOF
Configurar Proxmox VE após instalação

Uso: $0 [host] [senha]

Argumentos:
    host    - IP ou hostname do Proxmox (padrão: 192.168.122.100)
    senha   - Senha do root (será solicitada se não fornecida)

Exemplos:
    $0
    $0 192.168.122.100
    $0 192.168.122.100 minha-senha

EOF
    exit 0
fi

main
