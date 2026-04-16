# 🚀 Proxmox VE 9.1 em VM KVM - Setup Completo

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║          🚀 Proxmox VE 9.1 em VM KVM - Pronto para Começar!          ║
║                                                                       ║
║  Status: ✅ Pronto                                                    ║
║  Tempo: ⏱️  30-45 minutos                                             ║
║  Dificuldade: 🟢 Fácil                                                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

## 📊 O Que Você Tem

```
✅ KVM ativo no Debian WSL
✅ libvirtd rodando
✅ Dependências instaladas
✅ Scripts prontos
✅ Documentação completa
✅ ISO pronta para download
```

## 🎯 Começar em 3 Passos

### Passo 1️⃣: Abra um Terminal

```bash
# Terminal 1: Setup (principal)
sudo bash scripts/quick-start-proxmox-kvm.sh
```

### Passo 2️⃣: Escolha Opção 1

```
Proxmox VE 9.0 em VM KVM - Quick Start
========================================
1. Criar VM Proxmox (download + setup)  ← ESCOLHA ESTA
2. Iniciar VM existente
3. Conectar ao console VNC
4. Testar conectividade
5. Configurar para MHC Cloud Panel
6. Ver status da VM
7. Parar VM
8. Sair

Escolha uma opção (1-8): 1
```

### Passo 3️⃣: Aguarde 30-45 Minutos

```
[INFO] Verificando dependências...
[INFO] Baixando Proxmox VE 9.0 ISO...
████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
45% - 850MB/1.8GB - 5 min restantes

[INFO] Criando VM Proxmox VE...
[INFO] VM criada com sucesso!

Console VNC abrirá automaticamente
Siga o instalador do Proxmox
```

## 📚 Documentação

### 🚀 Para Começar Agora
- **[QUICK_START_NOW.md](QUICK_START_NOW.md)** - 5 minutos de leitura

### 📊 Para Entender o Processo
- **[PROXMOX_VM_SETUP_VISUAL.md](PROXMOX_VM_SETUP_VISUAL.md)** - Guia visual completo
- **[ARCHITECTURE_VISUAL.md](ARCHITECTURE_VISUAL.md)** - Diagramas de arquitetura

### 📋 Para Referência Rápida
- **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** - Resumo executivo
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Índice completo

### 📖 Para Aprender Profundamente
- **[START_PROXMOX_SETUP.md](START_PROXMOX_SETUP.md)** - Guia completo
- **[docs/PROXMOX_KVM_SETUP.md](docs/PROXMOX_KVM_SETUP.md)** - Guia técnico

## ⏱️ Timeline

| Fase | Duração | Status |
|------|---------|--------|
| Preparação | 2-3 min | ✓ Rápido |
| Download ISO | 5-15 min | ⏳ Depende da conexão |
| Criar VM | 2-3 min | ✓ Rápido |
| Instalar Proxmox | 15-20 min | ⏳ Longo |
| Boot | 5 min | ✓ Rápido |
| Configurar MHC | 5 min | ✓ Rápido |
| **TOTAL** | **30-45 min** | ⏳ Planeje tempo |

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows 11 / WSL2                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Debian WSL2 (Linux)                     │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  KVM / QEMU / libvirt                          │ │  │
│  │  ├────────────────────────────────────────────────┤ │  │
│  │  │                                                │ │  │
│  │  │  ┌──────────────────────────────────────────┐ │ │  │
│  │  │  │  Proxmox VE 9.1 (VM)                    │ │ │  │
│  │  │  │  IP: 192.168.122.100                    │ │ │  │
│  │  │  │  CPU: 4 | RAM: 4GB | Disk: 50GB        │ │ │  │
│  │  │  │  API: https://192.168.122.100:8006      │ │ │  │
│  │  │  └──────────────────────────────────────────┘ │ │  │
│  │  │                                                │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  Docker Containers (MHC Cloud Panel)          │ │  │
│  │  ├────────────────────────────────────────────────┤ │  │
│  │  │  Frontend: http://localhost:3000              │ │  │
│  │  │  Backend: http://localhost:8000               │ │  │
│  │  │  Database: PostgreSQL                         │ │  │
│  │  │  Cache: Redis                                 │ │  │
│  │  │  Tasks: Celery                                │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Checklist

- [ ] Leia [QUICK_START_NOW.md](QUICK_START_NOW.md)
- [ ] Execute: `sudo bash scripts/quick-start-proxmox-kvm.sh`
- [ ] Escolha opção 1
- [ ] Aguarde 30-45 minutos
- [ ] Console VNC abrirá automaticamente
- [ ] Siga o instalador do Proxmox
- [ ] Após instalação, volte ao menu
- [ ] Escolha opção 4 (testar conectividade)
- [ ] Escolha opção 5 (configurar MHC)
- [ ] Copie variáveis: `cat .env.proxmox >> .env`
- [ ] Reinicie: `docker compose restart`
- [ ] Acesse: `http://localhost:3000/admin/infrastructure`

## 🐛 Troubleshooting Rápido

### "virt-install: command not found"
```bash
sudo apt-get install -y virt-install
```

### "VM não inicia"
```bash
sudo systemctl restart libvirtd
```

### "Sem conectividade"
```bash
sudo virsh net-destroy default
sudo virsh net-start default
```

### "Proxmox não responde"
- Aguarde 5-10 minutos após boot
- Conecte ao console VNC: `sudo virt-viewer proxmox-ve`
- Verifique serviços: `systemctl status pvedaemon`

## 💡 Dicas

1. **Use 3 terminais**: Um para setup, um para monitorar, um para VNC
2. **Não feche o terminal**: O script continua rodando
3. **Paciência**: Download e instalação são lentos
4. **Snapshots**: Crie snapshot após instalação limpa
5. **Backup**: Crie snapshots antes de fazer mudanças

## 🎯 Próximos Passos

Após tudo funcionando:

1. ✓ Proxmox VE 9.1 rodando em VM KVM
2. ✓ Integrado com MHC Cloud Panel
3. → Criar VMs de teste
4. → Testar provisioning
5. → Testar billing
6. → Testar rebalanceamento

## 📞 Documentação Completa

- [QUICK_START_NOW.md](QUICK_START_NOW.md) - ⚡ Comece aqui!
- [PROXMOX_VM_SETUP_VISUAL.md](PROXMOX_VM_SETUP_VISUAL.md) - 📊 Guia visual
- [SETUP_SUMMARY.md](SETUP_SUMMARY.md) - 📋 Resumo
- [ARCHITECTURE_VISUAL.md](ARCHITECTURE_VISUAL.md) - 🏗️ Arquitetura
- [START_PROXMOX_SETUP.md](START_PROXMOX_SETUP.md) - 📖 Referência completa
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - 📚 Índice completo

## 🚀 Começar Agora!

```bash
# Leia o guia rápido (5 minutos):
cat QUICK_START_NOW.md

# Depois execute (30-45 minutos):
sudo bash scripts/quick-start-proxmox-kvm.sh

# Escolha opção 1 e aguarde
```

---

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    ✅ Pronto para Começar!                           ║
║                                                                       ║
║              Tempo: 30-45 minutos | Dificuldade: Fácil               ║
║                                                                       ║
║                  Próximo passo: Leia QUICK_START_NOW.md              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

Boa sorte! 🚀
