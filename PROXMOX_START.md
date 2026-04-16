# 🚀 Começar com Proxmox VE 9.0 em VM KVM

## Resumo Executivo

Você agora tem um conjunto completo de scripts para rodar Proxmox VE 9.0 em uma VM KVM no Debian WSL, em vez de usar o mock.

**Tempo estimado**: 30-45 minutos (incluindo download da ISO)

## ⚡ Quick Start (3 passos)

### 1️⃣ Executar o menu interativo

```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
```

### 2️⃣ Escolher opção 1 (Criar VM)

O script irá:
- Baixar ISO do Proxmox VE 9.0 (~800MB)
- Criar disco virtual de 50GB
- Criar VM com 4 CPUs e 4GB RAM
- Iniciar a instalação

### 3️⃣ Instalar Proxmox

```bash
# Escolher opção 3 (Conectar VNC)
# Isso abrirá o console da VM
```

Durante a instalação:
- **Hostname**: `proxmox-ve`
- **IP**: `192.168.122.100/24`
- **Gateway**: `192.168.122.1`
- **Disco**: `/dev/vda`
- **Senha**: Defina uma senha segura

## 📋 Pré-requisitos

Verificar se tudo está pronto:

```bash
# 1. KVM habilitado?
sudo -u libvirt-qemu test -r /dev/kvm && echo "✓ KVM OK"

# 2. Dependências instaladas?
which virt-install qemu-system-x86_64 virsh

# 3. libvirtd rodando?
sudo systemctl status libvirtd
```

Se algo faltar:

```bash
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

sudo systemctl start libvirtd
sudo systemctl enable libvirtd
```

## 🎯 Fluxo Completo

### Fase 1: Criar VM (10-15 min)

```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
# Escolher: 1 (Criar VM)
```

Aguardar:
- Download da ISO (~5-10 min)
- Criação do disco
- Inicialização da VM

### Fase 2: Instalar Proxmox (15-20 min)

```bash
# No menu, escolher: 3 (Conectar VNC)
```

Isso abrirá o console VNC. Seguir o instalador:
1. Selecionar idioma
2. Configurar localização/timezone
3. Definir senha do root
4. Configurar rede (IP: 192.168.122.100)
5. Selecionar disco
6. Confirmar e instalar

Aguardar conclusão (~15 min).

### Fase 3: Configurar para MHC (5 min)

```bash
# No menu, escolher: 5 (Configurar MHC)
```

Será solicitada a senha do root do Proxmox (definida na instalação).

Isso irá:
- Criar token de API
- Gerar arquivo `.env.proxmox`

### Fase 4: Atualizar Configuração (2 min)

```bash
# Copiar variáveis para .env
cat .env.proxmox >> .env

# Ou editar manualmente
nano .env
```

### Fase 5: Reiniciar Containers (1 min)

```bash
docker compose restart
```

## ✅ Verificar Tudo Funcionando

```bash
# 1. Verificar status da VM
sudo bash scripts/proxmox-vm-utils.sh status

# 2. Testar conectividade
sudo bash scripts/proxmox-vm-utils.sh test-connection

# 3. Acessar Proxmox Web UI
# https://192.168.122.100:8006
# Username: root@pam
# Password: (senha definida na instalação)

# 4. Verificar integração com MHC
curl -k https://192.168.122.100:8006/api2/json/version
```

## 📚 Documentação

- **Quick Start**: [docs/PROXMOX_KVM_QUICKSTART.md](docs/PROXMOX_KVM_QUICKSTART.md)
- **Setup Completo**: [docs/PROXMOX_KVM_SETUP.md](docs/PROXMOX_KVM_SETUP.md)
- **Visão Geral**: [docs/PROXMOX_KVM_OVERVIEW.md](docs/PROXMOX_KVM_OVERVIEW.md)

## 🔧 Scripts Disponíveis

| Script | Propósito |
|--------|-----------|
| `quick-start-proxmox-kvm.sh` | Menu interativo (recomendado) |
| `setup-proxmox-vm-kvm.sh` | Criar VM do zero |
| `proxmox-vm-utils.sh` | Gerenciar VM (start, stop, snapshots) |
| `configure-proxmox-vm.sh` | Configurar após instalação |

## 🎮 Gerenciar VM

```bash
# Status
sudo bash scripts/proxmox-vm-utils.sh status

# Iniciar
sudo bash scripts/proxmox-vm-utils.sh start

# Parar
sudo bash scripts/proxmox-vm-utils.sh stop

# Conectar VNC
sudo bash scripts/proxmox-vm-utils.sh vnc

# Criar snapshot
sudo bash scripts/proxmox-vm-utils.sh snapshot pre-config

# Restaurar snapshot
sudo bash scripts/proxmox-vm-utils.sh restore-snapshot pre-config
```

## 🐛 Problemas Comuns

### "virt-install: command not found"
```bash
sudo apt-get install -y virt-install
```

### "VM não inicia"
```bash
# Verificar espaço
df -h /var/lib/libvirt/images

# Reiniciar libvirtd
sudo systemctl restart libvirtd
```

### "Sem conectividade de rede"
```bash
# Reiniciar rede
sudo virsh net-destroy default
sudo virsh net-start default
```

### "Proxmox não responde na porta 8006"
- Aguardar 5-10 minutos após boot
- Conectar ao console VNC para verificar status
- Verificar serviços: `systemctl status pvedaemon`

## 💡 Dicas

1. **Use snapshots**: Crie snapshot após instalação limpa para facilitar testes
2. **Monitore recursos**: `virsh domstats proxmox-ve`
3. **Backup**: Crie snapshots antes de fazer mudanças importantes
4. **Performance**: Aumentar RAM/CPUs se necessário

## 🎯 Próximos Passos

1. ✅ Executar `sudo bash scripts/quick-start-proxmox-kvm.sh`
2. ✅ Instalar Proxmox via VNC
3. ✅ Configurar para MHC
4. ⏭️ Testar integração com MHC Cloud Panel
5. ⏭️ Criar templates de VM
6. ⏭️ Configurar storage
7. ⏭️ Configurar backup

## 📞 Suporte

Para mais detalhes:
- Consulte a documentação em `docs/`
- Verifique logs: `docker compose logs -f backend`
- Conecte ao console Proxmox: `sudo virsh console proxmox-ve`

---

**Pronto para começar?**

```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
```

Boa sorte! 🚀
