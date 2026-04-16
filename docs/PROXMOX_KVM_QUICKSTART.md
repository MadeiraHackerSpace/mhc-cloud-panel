# Proxmox VE 9.0 em VM KVM - Quick Start

Guia rápido para rodar Proxmox em uma VM KVM no Debian WSL.

## TL;DR

```bash
# 1. Executar quick-start interativo
sudo bash scripts/quick-start-proxmox-kvm.sh

# 2. Escolher opção 1 (Criar VM)
# 3. Escolher opção 3 (Conectar VNC) para instalar
# 4. Escolher opção 5 (Configurar para MHC)
# 5. Copiar variáveis do .env.proxmox para .env
# 6. Reiniciar containers
docker compose restart
```

## Pré-requisitos

```bash
# Verificar KVM
sudo -u libvirt-qemu test -r /dev/kvm && echo "✓ KVM OK"

# Instalar dependências
sudo apt-get update
sudo apt-get install -y \
    libvirt-daemon-system \
    libvirt-clients \
    qemu-system-x86 \
    qemu-utils \
    virt-manager \
    virt-viewer \
    virt-install \
    wget

# Iniciar libvirtd
sudo systemctl start libvirtd
sudo systemctl enable libvirtd
```

## Opção 1: Quick Start Interativo (Recomendado)

```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
```

Menu com opções:
1. **Criar VM** - Download ISO + setup
2. **Iniciar VM** - Ligar VM existente
3. **Conectar VNC** - Abrir console
4. **Testar conectividade** - Verificar se está respondendo
5. **Configurar MHC** - Criar token e gerar .env
6. **Ver status** - Status da VM
7. **Parar VM** - Desligar VM

## Opção 2: Passo a Passo Manual

### 1. Criar VM

```bash
sudo bash scripts/setup-proxmox-vm-kvm.sh
```

Isso irá:
- Baixar ISO do Proxmox VE 9.0 (~800MB)
- Criar disco virtual de 50GB
- Criar VM com 4 CPUs e 4GB RAM
- Iniciar a instalação

### 2. Instalar Proxmox

```bash
# Conectar ao console VNC
sudo virt-viewer proxmox-ve
```

Durante a instalação:
- **Hostname**: `proxmox-ve`
- **IP**: `192.168.122.100/24`
- **Gateway**: `192.168.122.1`
- **Disco**: `/dev/vda`

### 3. Configurar para MHC

```bash
sudo bash scripts/configure-proxmox-vm.sh 192.168.122.100
```

Será solicitada a senha do root do Proxmox.

Isso irá:
- Criar token de API
- Gerar arquivo `.env.proxmox`

### 4. Atualizar .env

```bash
# Copiar variáveis de .env.proxmox para .env
cat .env.proxmox >> .env

# Ou editar manualmente
nano .env
```

### 5. Reiniciar containers

```bash
docker compose restart
```

## Gerenciar VM

### Usar script de utilitários

```bash
# Status
sudo bash scripts/proxmox-vm-utils.sh status

# Iniciar
sudo bash scripts/proxmox-vm-utils.sh start

# Parar
sudo bash scripts/proxmox-vm-utils.sh stop

# Conectar VNC
sudo bash scripts/proxmox-vm-utils.sh vnc

# Testar conexão
sudo bash scripts/proxmox-vm-utils.sh test-connection

# Criar snapshot
sudo bash scripts/proxmox-vm-utils.sh snapshot pre-config

# Listar snapshots
sudo bash scripts/proxmox-vm-utils.sh list-snapshots
```

### Comandos virsh diretos

```bash
# Ver VMs
sudo virsh list --all

# Iniciar
sudo virsh start proxmox-ve

# Parar
sudo virsh shutdown proxmox-ve

# Forçar parada
sudo virsh destroy proxmox-ve

# Console
sudo virsh console proxmox-ve

# IP
sudo virsh domifaddr proxmox-ve
```

## Acessar Proxmox

```
https://192.168.122.100:8006
```

- Username: `root@pam`
- Password: (senha definida na instalação)

## Testar Integração

```bash
# Verificar conectividade
curl -k https://192.168.122.100:8006/api2/json/version

# Testar autenticação
curl -k -X POST https://192.168.122.100:8006/api2/json/access/ticket \
    -d "username=root@pam&password=sua-senha"
```

## Troubleshooting

### VM não inicia

```bash
# Verificar espaço
df -h /var/lib/libvirt/images

# Verificar logs
sudo virsh log proxmox-ve

# Reiniciar libvirtd
sudo systemctl restart libvirtd
```

### Sem conectividade

```bash
# Verificar rede
sudo virsh net-list

# Reiniciar rede
sudo virsh net-destroy default
sudo virsh net-start default

# Verificar interface
sudo virsh domifaddr proxmox-ve
```

### Proxmox não responde

```bash
# Conectar ao console
sudo virsh console proxmox-ve

# Dentro da VM, verificar serviços
systemctl status pvedaemon
systemctl status pveproxy
```

## Documentação Completa

Para mais detalhes, ver: [PROXMOX_KVM_SETUP.md](./PROXMOX_KVM_SETUP.md)

## Próximos Passos

1. ✅ VM Proxmox criada
2. ✅ Configuração de rede
3. ✅ Token de API
4. ⏭️ Testar integração com MHC Cloud Panel
5. ⏭️ Criar templates de VM
6. ⏭️ Configurar storage
