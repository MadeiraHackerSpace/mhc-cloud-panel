# ⚡ Começar Agora - Proxmox VE 9.1 em VM KVM

## 🎯 Resumo Executivo

Você já tem:
- ✅ KVM ativo no Debian WSL
- ✅ libvirtd rodando
- ✅ Scripts prontos
- ✅ ISO pronta para download

**Tempo total: 30-45 minutos**

---

## 🚀 Começar em 3 Passos

### Passo 1: Abra 3 Terminais

```
Terminal 1: Setup (principal)
Terminal 2: Monitorar (opcional)
Terminal 3: VNC (após 10 min)
```

### Passo 2: Terminal 1 - Execute o Menu

```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
```

Você verá:
```
Proxmox VE 9.0 em VM KVM - Quick Start
========================================
1. Criar VM Proxmox (download + setup)
2. Iniciar VM existente
3. Conectar ao console VNC
4. Testar conectividade
5. Configurar para MHC Cloud Panel
6. Ver status da VM
7. Parar VM
8. Sair

Escolha uma opção (1-8): 
```

**Digite: 1** (Enter)

### Passo 3: Aguarde

O script irá:
1. ✓ Verificar dependências (1 min)
2. ⏳ Baixar ISO (5-15 min) - depende da conexão
3. ✓ Criar VM (2-3 min)
4. ⏳ Instalar Proxmox (15-20 min) - você verá o console VNC

---

## 📊 O Que Acontece

### Minutos 0-5: Preparação
```
[INFO] Verificando dependências...
[INFO] Iniciando libvirtd...
[INFO] Criando rede padrão...
[INFO] Baixando Proxmox VE 9.0 ISO...
[WARN] Isso pode levar alguns minutos (~800MB)...
```

### Minutos 5-20: Download
```
████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
45% - 850MB/1.8GB - 5 min restantes
```

### Minutos 20-25: Criar VM
```
[INFO] Criando disco da VM (50G)...
[INFO] Criando VM Proxmox VE...
Starting install, retrieving kernel.img...
```

### Minutos 25-45: Instalar Proxmox
```
Console VNC abrirá automaticamente
Você verá o instalador do Proxmox
Configure conforme solicitado
```

---

## 🖥️ Durante a Instalação (Console VNC)

O instalador pedirá:

1. **Idioma**: English (padrão)
2. **Localização**: Sua localização
3. **Timezone**: Seu timezone
4. **Senha**: Defina uma senha forte
5. **Hostname**: `proxmox-ve` (padrão)
6. **IP**: `192.168.122.100` (padrão)
7. **Gateway**: `192.168.122.1` (padrão)
8. **Disco**: `/dev/vda` (padrão)

**Dica**: Deixe os padrões, apenas mude a senha se quiser.

---

## ✅ Após a Instalação (Minuto 45)

### Terminal 1: Volte ao Menu

```
Escolha uma opção (1-8): 4
```

Isso testa a conectividade:
```
[INFO] Testando conectividade
[INFO] Testando ping em 192.168.122.100...
✓ Ping bem-sucedido
[INFO] Testando porta 8006...
✓ Porta 8006 aberta
[INFO] Acesse: https://192.168.122.100:8006
```

### Terminal 1: Configure para MHC

```
Escolha uma opção (1-8): 5
```

Será solicitado:
```
IP do Proxmox (padrão: 192.168.122.100): [Enter]
Senha do root do Proxmox: [sua senha]
```

Resultado:
```
✓ Configuração concluída
Arquivo .env.proxmox foi criado
Copie as variáveis para seu .env principal
```

---

## 🔧 Integrar com MHC Cloud Panel

### Passo 1: Copiar Variáveis

```bash
cat .env.proxmox >> .env
```

### Passo 2: Reiniciar Containers

```bash
docker compose restart
```

### Passo 3: Verificar

```bash
docker compose logs -f
```

Procure por:
```
backend-1  | [INFO] Proxmox API conectado com sucesso
```

### Passo 4: Acessar MHC

```
http://localhost:3000/admin/infrastructure
```

---

## 📋 Checklist Rápido

- [ ] Terminal 1: `sudo bash scripts/quick-start-proxmox-kvm.sh`
- [ ] Escolher opção 1
- [ ] Aguardar 30-45 minutos
- [ ] Console VNC abrirá automaticamente
- [ ] Seguir instalador do Proxmox
- [ ] Após instalação, voltar ao menu
- [ ] Escolher opção 4 (testar)
- [ ] Escolher opção 5 (configurar MHC)
- [ ] Copiar variáveis: `cat .env.proxmox >> .env`
- [ ] Reiniciar: `docker compose restart`
- [ ] Verificar: `http://localhost:3000/admin/infrastructure`

---

## 🐛 Se Algo Dar Errado

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

---

## 💡 Dicas

1. **Não feche o terminal**: O script continua rodando
2. **Use 3 terminais**: Um para setup, um para monitorar, um para VNC
3. **Paciência**: Download e instalação são lentos
4. **Snapshots**: Crie snapshot após instalação limpa
5. **Backup**: Crie snapshots antes de fazer mudanças

---

## 🎯 Próximos Passos

Após tudo funcionando:

1. Criar VMs no Proxmox
2. Testar provisioning via MHC Cloud Panel
3. Configurar templates
4. Testar billing
5. Testar rebalanceamento

---

## 📞 Documentação Completa

- [PROXMOX_VM_SETUP_VISUAL.md](PROXMOX_VM_SETUP_VISUAL.md) - Guia visual detalhado
- [START_PROXMOX_SETUP.md](START_PROXMOX_SETUP.md) - Guia completo
- [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) - Resumo executivo
- [docs/PROXMOX_KVM_SETUP.md](docs/PROXMOX_KVM_SETUP.md) - Guia técnico

---

## 🚀 Começar Agora!

```bash
sudo bash scripts/quick-start-proxmox-kvm.sh
```

**Escolha opção 1 e aguarde 30-45 minutos.**

Boa sorte! 🚀
