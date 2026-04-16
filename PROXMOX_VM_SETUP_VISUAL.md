# 🚀 Proxmox VE 9.1 em VM KVM - Guia Visual e Prático

## 📊 Resultado Visual Esperado

### Fase 1: Preparação (5-10 minutos)

```
┌─────────────────────────────────────────────────────────────┐
│ Terminal 1: Executar Setup                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ $ sudo bash scripts/quick-start-proxmox-kvm.sh              │
│                                                              │
│ Proxmox VE 9.0 em VM KVM - Quick Start                      │
│ ========================================                     │
│ 1. Criar VM Proxmox (download + setup)                      │
│ 2. Iniciar VM existente                                     │
│ 3. Conectar ao console VNC                                  │
│ 4. Testar conectividade                                     │
│ 5. Configurar para MHC Cloud Panel                          │
│ 6. Ver status da VM                                         │
│ 7. Parar VM                                                 │
│ 8. Sair                                                     │
│                                                              │
│ Escolha uma opção (1-8): 1                                  │
│                                                              │
│ [INFO] Criando VM Proxmox VE 9.0                            │
│ [INFO] Verificando dependências...                          │
│ [INFO] Iniciando libvirtd...                                │
│ [INFO] Criando rede padrão...                               │
│ [INFO] Baixando Proxmox VE 9.0 ISO...                       │
│ [WARN] Isso pode levar alguns minutos (~800MB)...           │
│                                                              │
│ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ 45% - 850MB/1.8GB - 5 min restantes                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Fase 2: Download e Criação da VM (10-15 minutos)

```
┌─────────────────────────────────────────────────────────────┐
│ Terminal 1: Continuação                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ████████████████████████████████████████████████████████████ │
│ 100% - 1.8GB/1.8GB - Download concluído!                    │
│                                                              │
│ [INFO] ISO baixada com sucesso                              │
│ [INFO] Criando disco da VM (50G)...                         │
│ [INFO] Criando VM Proxmox VE...                             │
│                                                              │
│ Starting install, retrieving kernel.img...                  │
│ Retrieving initrd.img...                                    │
│ Retrieving vmlinuz...                                       │
│ [    0.000000] Linux version 6.2.16-3-pve (root@pve)        │
│ [    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz-6.2   │
│ [    0.000000] KERNEL supported cpus:                       │
│ [    0.000000]   Intel GenuineIntel                         │
│ [    0.000000]   AMD AuthenticAMD                           │
│ [    0.000000]   Hygon HygonGenuine                         │
│ [    0.000000]   Centaur CentaurHauls                       │
│ [    0.000000]   zhaoxin   Shanghai                         │
│                                                              │
│ [INFO] VM criada com sucesso!                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Fase 3: Instalação do Proxmox (15-20 minutos)

```
┌─────────────────────────────────────────────────────────────┐
│ Terminal 2: VNC Console (virt-viewer)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 Installer                             │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  Welcome to Proxmox VE 9.1 Installer                │   │
│  │                                                      │   │
│  │  [1] Install Proxmox VE                             │   │
│  │  [2] Install Proxmox VE (Debug mode)                │   │
│  │  [3] Boot from Hard Disk                            │   │
│  │  [4] Reboot                                         │   │
│  │  [5] Halt                                           │   │
│  │                                                      │   │
│  │  Choose an option: 1                                │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 Installer - License Agreement        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  I agree to the above terms and conditions          │   │
│  │  [✓] I agree                                        │   │
│  │                                                      │   │
│  │  [ Next ]                                           │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 Installer - Location                 │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  Country: [United States ▼]                         │   │
│  │  Time zone: [America/New_York ▼]                    │   │
│  │  Keyboard Layout: [en-us ▼]                         │   │
│  │                                                      │   │
│  │  [ Next ]                                           │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 Installer - Password                 │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  Password: [••••••••••]                             │   │
│  │  Confirm: [••••••••••]                              │   │
│  │  Email: [root@proxmox.local]                        │   │
│  │                                                      │   │
│  │  [ Next ]                                           │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 Installer - Network                  │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  Hostname: [proxmox-ve]                             │   │
│  │  IP Address: [192.168.122.100]                      │   │
│  │  Netmask: [255.255.255.0]                           │   │
│  │  Gateway: [192.168.122.1]                           │   │
│  │  DNS: [8.8.8.8]                                     │   │
│  │                                                      │   │
│  │  [ Next ]                                           │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 Installer - Disk                     │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  Target Harddisk: [/dev/vda (50GB) ✓]               │   │
│  │  Filesystem: [ext4]                                 │   │
│  │                                                      │   │
│  │  [ Next ]                                           │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 Installer - Summary                  │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  Hostname: proxmox-ve                               │   │
│  │  IP: 192.168.122.100/24                             │   │
│  │  Gateway: 192.168.122.1                             │   │
│  │  Disk: /dev/vda (50GB)                              │   │
│  │  Filesystem: ext4                                   │   │
│  │                                                      │   │
│  │  [ Install ]                                        │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Installing Proxmox VE...                                   │
│  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  45% - 15 min restantes                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Fase 4: Conclusão (5 minutos)

```
┌─────────────────────────────────────────────────────────────┐
│ Terminal 1: Após Instalação                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [INFO] VM criada com sucesso!                               │
│                                                              │
│ Próximos passos:                                            │
│ 1. Conectar ao console VNC:                                 │
│    virsh vncdisplay proxmox-ve                              │
│                                                              │
│ 2. Ou usar virt-viewer:                                     │
│    virt-viewer proxmox-ve                                   │
│                                                              │
│ 3. Durante a instalação, configure:                         │
│    - Hostname: proxmox-ve                                   │
│    - IP: 192.168.122.100                                    │
│    - Gateway: 192.168.122.1                                 │
│    - Netmask: 255.255.255.0                                 │
│                                                              │
│ 4. Após a instalação, acesse:                               │
│    https://192.168.122.100:8006                             │
│                                                              │
│ 5. Para parar a VM:                                         │
│    virsh shutdown proxmox-ve                                │
│                                                              │
│ 6. Para iniciar a VM:                                       │
│    virsh start proxmox-ve                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Fase 5: Proxmox Rodando (Após reboot)

```
┌─────────────────────────────────────────────────────────────┐
│ Terminal 2: VNC Console (Proxmox Iniciado)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ proxmox-ve login: root                               │   │
│  │ Password: ••••••••••                                 │   │
│  │ Last login: Thu Apr 16 10:30:00 UTC 2026             │   │
│  │                                                      │   │
│  │ root@proxmox-ve:~# systemctl status pvedaemon        │   │
│  │ ● pvedaemon.service - Proxmox VE daemon              │   │
│  │      Loaded: loaded (/lib/systemd/system/pvedaemon)  │   │
│  │      Active: active (running) since Thu 2026-04-16   │   │
│  │                                                      │   │
│  │ root@proxmox-ve:~#                                   │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Fase 6: Acessar Web UI

```
┌─────────────────────────────────────────────────────────────┐
│ Browser: https://192.168.122.100:8006                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1                                       │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  Username: root@pam                                 │   │
│  │  Password: [••••••••••]                             │   │
│  │  Realm: [Proxmox VE authentication ▼]               │   │
│  │                                                      │   │
│  │  [ Login ]                                          │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Proxmox VE 9.1 - Dashboard                           │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  ┌─ Datacenter ─────────────────────────────────┐   │   │
│  │  │ ├─ proxmox-ve (online)                       │   │   │
│  │  │ │  CPU: 4 cores (0% used)                    │   │   │
│  │  │ │  Memory: 4GB (512MB used)                  │   │   │
│  │  │ │  Disk: 50GB (2GB used)                     │   │   │
│  │  │ │  Uptime: 5 minutes                         │   │   │
│  │  │ │                                            │   │   │
│  │  │ └─ VMs: 0                                    │   │   │
│  │  │    Containers: 0                             │   │   │
│  │  │    Storage: local (50GB available)           │   │   │
│  │  │                                              │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Fluxo Prático Passo a Passo

### Terminal 1: Executar Setup

```bash
# Abra um terminal e execute:
sudo bash scripts/quick-start-proxmox-kvm.sh

# Escolha opção 1 para criar VM
# Aguarde o download e criação (30-45 minutos)
```

### Terminal 2: Monitorar Progresso (após 5 minutos)

```bash
# Em outro terminal, monitore:
sudo virsh list --all

# Resultado esperado:
#  Id   Name         State
# ─────────────────────────────
#  1    proxmox-ve   running

# Verificar IP:
sudo virsh domifaddr proxmox-ve

# Resultado esperado:
#  Name       MAC address          IPv4 Address  IPv6 Address
# ─────────────────────────────────────────────────────────────
#  vnet0      52:54:00:12:34:56    192.168.122.100/24  -
```

### Terminal 3: Conectar VNC (após 10 minutos)

```bash
# Conectar ao console VNC:
sudo virt-viewer proxmox-ve

# Ou obter display VNC:
sudo virsh vncdisplay proxmox-ve
# Resultado: :0 (localhost:5900)
```

### Após Instalação: Testar Conectividade

```bash
# Terminal 1: Voltar ao menu
# Escolha opção 4 para testar conectividade

# Ou manual:
ping 192.168.122.100
curl -k https://192.168.122.100:8006/api2/json/version
```

### Configurar para MHC Cloud Panel

```bash
# Terminal 1: Voltar ao menu
# Escolha opção 5 para configurar MHC

# Será solicitada:
# - IP do Proxmox: 192.168.122.100
# - Senha do root: (a que você definiu na instalação)

# Resultado: arquivo .env.proxmox criado
```

### Atualizar .env e Reiniciar

```bash
# Copiar variáveis:
cat .env.proxmox >> .env

# Reiniciar containers:
docker compose restart

# Verificar:
docker compose logs -f
```

---

## 📊 Timeline Esperado

| Fase | Duração | Status |
|------|---------|--------|
| Preparação | 2-3 min | ✓ Rápido |
| Download ISO | 5-15 min | ⏳ Depende da conexão |
| Criar VM | 2-3 min | ✓ Rápido |
| Instalar Proxmox | 15-20 min | ⏳ Longo |
| Boot e Inicialização | 5 min | ✓ Rápido |
| Configurar MHC | 5 min | ✓ Rápido |
| **TOTAL** | **30-45 min** | ⏳ Planeje tempo |

---

## ✅ Checklist de Verificação

Após a instalação, verifique:

- [ ] VM está rodando: `sudo virsh list`
- [ ] IP configurado: `sudo virsh domifaddr proxmox-ve`
- [ ] Ping funciona: `ping 192.168.122.100`
- [ ] Porta 8006 aberta: `curl -k https://192.168.122.100:8006/api2/json/version`
- [ ] Web UI acessível: `https://192.168.122.100:8006`
- [ ] Login funciona: root@pam + senha
- [ ] Arquivo .env.proxmox criado
- [ ] Variáveis copiadas para .env
- [ ] Containers reiniciados: `docker compose restart`
- [ ] MHC Cloud Panel acessível: `http://localhost:3000/admin/infrastructure`

---

## 🐛 Troubleshooting Rápido

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

---

## 💡 Dicas Importantes

1. **Use snapshots**: Crie snapshot após instalação limpa
   ```bash
   sudo virsh snapshot-create-as proxmox-ve pos-instalacao
   ```

2. **Monitore recursos**: 
   ```bash
   virsh domstats proxmox-ve
   ```

3. **Backup**: Crie snapshots antes de fazer mudanças
   ```bash
   sudo virsh snapshot-create-as proxmox-ve pre-config
   ```

4. **Restaure snapshots** se algo der errado:
   ```bash
   sudo virsh snapshot-revert proxmox-ve pos-instalacao
   ```

---

## 🚀 Começar Agora

### Passo 1: Terminal 1
```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
# Escolher opção 1
```

### Passo 2: Terminal 2 (após 5 minutos)
```bash
sudo virsh list --all
sudo virsh domifaddr proxmox-ve
```

### Passo 3: Terminal 3 (após 10 minutos)
```bash
sudo virt-viewer proxmox-ve
# Seguir instalador do Proxmox
```

### Passo 4: Após instalação
```bash
# Terminal 1: Voltar ao menu
# Escolher opção 4 (testar conectividade)
# Escolher opção 5 (configurar MHC)
```

---

**Tempo estimado: 30-45 minutos**

**Pronto para começar?**

```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
```

Boa sorte! 🚀
