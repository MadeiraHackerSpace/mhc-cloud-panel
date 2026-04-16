# Proxmox VE 9.0 em VM KVM - Visão Geral

## 📋 Arquivos Criados

### Scripts

#### 1. `scripts/setup-proxmox-vm-kvm.sh`
**Propósito**: Criar VM Proxmox do zero
- ✅ Baixa ISO do Proxmox VE 9.0 (~800MB)
- ✅ Cria disco virtual de 50GB
- ✅ Cria VM com 4 CPUs e 4GB RAM
- ✅ Configura rede padrão do libvirt
- ✅ Inicia instalação

**Uso**:
```bash
sudo bash scripts/setup-proxmox-vm-kvm.sh
```

#### 2. `scripts/proxmox-vm-utils.sh`
**Propósito**: Gerenciar VM Proxmox
- ✅ Status da VM
- ✅ Iniciar/parar VM
- ✅ Conectar console VNC
- ✅ Obter IP
- ✅ Testar conectividade
- ✅ Criar/restaurar snapshots
- ✅ Ver informações

**Uso**:
```bash
sudo bash scripts/proxmox-vm-utils.sh <comando>
```

**Comandos**:
```
status              - Status da VM
start               - Iniciar VM
stop                - Parar VM
force-stop          - Forçar parada
vnc                 - Conectar VNC
get-ip              - Obter IP
test-connection     - Testar conectividade
info                - Informações
snapshot <nome>     - Criar snapshot
list-snapshots      - Listar snapshots
restore-snapshot    - Restaurar snapshot
delete-snapshot     - Deletar snapshot
```

#### 3. `scripts/configure-proxmox-vm.sh`
**Propósito**: Configurar Proxmox após instalação
- ✅ Verifica conectividade
- ✅ Autentica no Proxmox
- ✅ Cria token de API
- ✅ Gera arquivo `.env.proxmox`

**Uso**:
```bash
sudo bash scripts/configure-proxmox-vm.sh [host] [senha]
```

**Exemplo**:
```bash
sudo bash scripts/configure-proxmox-vm.sh 192.168.122.100
```

#### 4. `scripts/quick-start-proxmox-kvm.sh`
**Propósito**: Menu interativo para setup completo
- ✅ Criar VM
- ✅ Iniciar VM
- ✅ Conectar VNC
- ✅ Testar conectividade
- ✅ Configurar para MHC
- ✅ Ver status
- ✅ Parar VM

**Uso**:
```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
```

### Documentação

#### 1. `docs/PROXMOX_KVM_SETUP.md`
**Conteúdo**: Guia completo e detalhado
- Pré-requisitos
- Instalação de dependências
- Criar VM (automatizado e manual)
- Instalar Proxmox
- Gerenciar VM
- Configurar para MHC
- Testar conexão
- Troubleshooting
- Performance
- Referências

#### 2. `docs/PROXMOX_KVM_QUICKSTART.md`
**Conteúdo**: Guia rápido e prático
- TL;DR (3 linhas)
- Pré-requisitos
- Opção 1: Quick Start Interativo
- Opção 2: Passo a Passo Manual
- Gerenciar VM
- Acessar Proxmox
- Testar Integração
- Troubleshooting

#### 3. `docs/PROXMOX_KVM_OVERVIEW.md`
**Conteúdo**: Este arquivo - visão geral do projeto

## 🚀 Fluxo de Uso

### Cenário 1: Primeira Vez (Recomendado)

```
1. sudo bash scripts/quick-start-proxmox-kvm.sh
   ↓
2. Escolher opção 1 (Criar VM)
   ↓
3. Aguardar download da ISO (~10 min)
   ↓
4. Escolher opção 3 (Conectar VNC)
   ↓
5. Instalar Proxmox (15-20 min)
   ↓
6. Escolher opção 5 (Configurar MHC)
   ↓
7. Copiar .env.proxmox para .env
   ↓
8. docker compose restart
```

### Cenário 2: Usar VM Existente

```
1. sudo bash scripts/proxmox-vm-utils.sh start
   ↓
2. sudo bash scripts/proxmox-vm-utils.sh test-connection
   ↓
3. sudo bash scripts/configure-proxmox-vm.sh
   ↓
4. docker compose restart
```

### Cenário 3: Desenvolvimento Iterativo

```
1. sudo bash scripts/proxmox-vm-utils.sh snapshot pre-config
   ↓
2. Fazer testes/configurações
   ↓
3. Se algo der errado:
   sudo bash scripts/proxmox-vm-utils.sh restore-snapshot pre-config
   ↓
4. Tentar novamente
```

## 📊 Arquitetura

```
┌─────────────────────────────────────────┐
│         Windows (WSL Host)              │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Debian Trixie (WSL)           │   │
│  │                                 │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │  KVM/libvirt              │  │   │
│  │  │                           │  │   │
│  │  │  ┌─────────────────────┐  │  │   │
│  │  │  │ Proxmox VE 9.0 VM   │  │  │   │
│  │  │  │                     │  │  │   │
│  │  │  │ IP: 192.168.122.100 │  │  │   │
│  │  │  │ Port: 8006          │  │  │   │
│  │  │  │ 4 CPUs, 4GB RAM     │  │  │   │
│  │  │  │ 50GB Disk           │  │  │   │
│  │  │  └─────────────────────┘  │  │   │
│  │  │                           │  │   │
│  │  └───────────────────────────┘  │   │
│  │                                 │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │  Docker Containers        │  │   │
│  │  │  - Frontend (3000)        │  │   │
│  │  │  - Backend (8000)         │  │   │
│  │  │  - Database               │  │   │
│  │  │  - Redis                  │  │   │
│  │  └───────────────────────────┘  │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

## 🔧 Configuração de Rede

```
Rede padrão libvirt:
├─ Bridge: virbr0
├─ Network: 192.168.122.0/24
├─ Gateway: 192.168.122.1
├─ DHCP: 192.168.122.2 - 192.168.122.254
└─ Proxmox VM: 192.168.122.100
```

## 📝 Variáveis de Ambiente

Após configuração, o arquivo `.env.proxmox` contém:

```bash
# Proxmox Host
PROXMOX_HOST=https://192.168.122.100:8006
PROXMOX_USER=root
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mhc-token
PROXMOX_TOKEN_SECRET=<token-gerado>
PROXMOX_VERIFY_SSL=false

# Frontend
NEXT_PUBLIC_PROXMOX_HOST=192.168.122.100

# Node padrão
PROXMOX_DEFAULT_NODE=proxmox-ve

# Storage
PROXMOX_VM_STORAGE=local
PROXMOX_VM_TEMPLATE_STORAGE=local
```

## ✅ Checklist de Setup

- [ ] KVM habilitado (`test -r /dev/kvm`)
- [ ] Dependências instaladas (libvirt, qemu, virt-install)
- [ ] libvirtd rodando (`systemctl status libvirtd`)
- [ ] VM Proxmox criada (`virsh list --all`)
- [ ] VM Proxmox rodando (`virsh list`)
- [ ] Conectividade testada (`ping 192.168.122.100`)
- [ ] Proxmox respondendo (`curl -k https://192.168.122.100:8006`)
- [ ] Token de API criado
- [ ] `.env.proxmox` gerado
- [ ] Variáveis copiadas para `.env`
- [ ] Containers reiniciados (`docker compose restart`)
- [ ] Integração testada

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| VM não inicia | `df -h` para verificar espaço; `systemctl restart libvirtd` |
| Sem conectividade | `virsh net-destroy default; virsh net-start default` |
| Proxmox não responde | Conectar ao console e verificar serviços |
| Erro de autenticação | Resetar senha: `passwd root` no console |
| Porta 8006 fechada | Aguardar boot completo (5-10 min) |

## 📚 Documentação Relacionada

- [PROXMOX_KVM_SETUP.md](./PROXMOX_KVM_SETUP.md) - Guia completo
- [PROXMOX_KVM_QUICKSTART.md](./PROXMOX_KVM_QUICKSTART.md) - Guia rápido
- [BACKEND.md](./BACKEND.md) - Backend API
- [SETUP.md](./SETUP.md) - Setup geral do projeto

## 🎯 Próximos Passos

1. ✅ Scripts de setup criados
2. ✅ Documentação completa
3. ⏭️ Executar `sudo bash scripts/quick-start-proxmox-kvm.sh`
4. ⏭️ Instalar Proxmox via VNC
5. ⏭️ Configurar para MHC Cloud Panel
6. ⏭️ Testar integração
7. ⏭️ Criar templates de VM
8. ⏭️ Configurar storage e backup

## 💡 Dicas

- Use snapshots para facilitar testes
- Crie snapshot após instalação limpa
- Crie snapshot após configuração
- Restaure snapshots para voltar a estado anterior
- Use `virt-viewer` para melhor experiência VNC
- Monitore recursos com `virsh domstats proxmox-ve`

## 🔗 Referências

- [Proxmox VE Documentation](https://pve.proxmox.com/wiki/Main_Page)
- [libvirt Documentation](https://libvirt.org/docs.html)
- [KVM/QEMU Documentation](https://www.qemu.org/documentation/)
- [Debian WSL Setup](https://learn.microsoft.com/en-us/windows/wsl/install)
