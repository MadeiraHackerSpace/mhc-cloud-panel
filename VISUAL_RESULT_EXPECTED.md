# 🎨 Resultado Visual Esperado - Proxmox VE 9.1 em VM KVM

## 📺 Terminal 1: Execução do Script

```
$ sudo bash scripts/quick-start-proxmox-kvm.sh

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

Escolha uma opção (1-8): 1

[INFO] Criando VM Proxmox VE 9.0
[INFO] Verificando dependências...
[INFO] Iniciando libvirtd...
[INFO] Criando rede padrão...
[INFO] Baixando Proxmox VE 9.0 ISO...
[WARN] Isso pode levar alguns minutos (~800MB)...

████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
45% - 850MB/1.8GB - 5 min restantes

████████████████████████████████████████████████████████████████
100% - 1.8GB/1.8GB - Download concluído!

[INFO] ISO baixada com sucesso
[INFO] Criando disco da VM (50G)...
[INFO] Criando VM Proxmox VE...

Starting install, retrieving kernel.img...
Retrieving initrd.img...
Retrieving vmlinuz...

[INFO] VM criada com sucesso!

Próximos passos:
1. Conectar ao console VNC:
   virsh vncdisplay proxmox-ve

2. Ou usar virt-viewer:
   virt-viewer proxmox-ve

3. Durante a instalação, configure:
   - Hostname: proxmox-ve
   - IP: 192.168.122.100
   - Gateway: 192.168.122.1
   - Netmask: 255.255.255.0

4. Após a instalação, acesse:
   https://192.168.122.100:8006

5. Para parar a VM:
   virsh shutdown proxmox-ve

6. Para iniciar a VM:
   virsh start proxmox-ve
```

---

## 🖥️ Terminal 2: Console VNC (Instalador Proxmox)

```
┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 Installer                                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Welcome to Proxmox VE 9.1 Installer                         │
│                                                              │
│  [1] Install Proxmox VE                                      │
│  [2] Install Proxmox VE (Debug mode)                         │
│  [3] Boot from Hard Disk                                     │
│  [4] Reboot                                                  │
│  [5] Halt                                                    │
│                                                              │
│  Choose an option: 1                                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 Installer - License Agreement                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  PROXMOX VE LICENSE AGREEMENT                                │
│                                                              │
│  [Scroll down to read more...]                               │
│                                                              │
│  I agree to the above terms and conditions                   │
│  [✓] I agree                                                 │
│                                                              │
│  [ Next ]                                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 Installer - Location                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Country: [United States ▼]                                  │
│  Time zone: [America/New_York ▼]                             │
│  Keyboard Layout: [en-us ▼]                                  │
│                                                              │
│  [ Next ]                                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 Installer - Password                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Password: [••••••••••]                                      │
│  Confirm: [••••••••••]                                       │
│  Email: [root@proxmox.local]                                 │
│                                                              │
│  [ Next ]                                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 Installer - Network                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Hostname: [proxmox-ve]                                      │
│  IP Address: [192.168.122.100]                               │
│  Netmask: [255.255.255.0]                                    │
│  Gateway: [192.168.122.1]                                    │
│  DNS: [8.8.8.8]                                              │
│                                                              │
│  [ Next ]                                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 Installer - Disk                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Target Harddisk: [/dev/vda (50GB) ✓]                        │
│  Filesystem: [ext4]                                          │
│                                                              │
│  [ Next ]                                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 Installer - Summary                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Hostname: proxmox-ve                                        │
│  IP: 192.168.122.100/24                                      │
│  Gateway: 192.168.122.1                                      │
│  Disk: /dev/vda (50GB)                                       │
│  Filesystem: ext4                                            │
│                                                              │
│  [ Install ]                                                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Installing Proxmox VE...
████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
45% - 15 min restantes

████████████████████████████████████████████████████████████████
100% - Instalação concluída!

Rebooting...
```

---

## 📊 Terminal 2: Após Reboot (Proxmox Iniciado)

```
┌──────────────────────────────────────────────────────────────┐
│ proxmox-ve login: root                                       │
│ Password: ••••••••••                                         │
│ Last login: Thu Apr 16 10:30:00 UTC 2026                     │
│                                                              │
│ root@proxmox-ve:~# systemctl status pvedaemon                │
│ ● pvedaemon.service - Proxmox VE daemon                      │
│      Loaded: loaded (/lib/systemd/system/pvedaemon.service)  │
│      Active: active (running) since Thu 2026-04-16 10:35:00  │
│      Docs: man:pvedaemon(8)                                  │
│    Process: 1234 ExecStart=/usr/bin/pvedaemon (code=exited)  │
│   Main PID: 1235 (pvedaemon)                                 │
│      Tasks: 5 (limit: 4915)                                  │
│     Memory: 45.2M                                            │
│     CGroup: /system.slice/pvedaemon.service                  │
│              └─1235 /usr/bin/pvedaemon                       │
│                                                              │
│ root@proxmox-ve:~# curl -k https://localhost:8006/api2/json/ │
│ version                                                      │
│ {"data":{"version":"9.1-1","release":"1","repoid":"proxmox" │
│ ,"keyboard":"en-us"}}                                        │
│                                                              │
│ root@proxmox-ve:~#                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🌐 Browser: Proxmox Web UI

```
URL: https://192.168.122.100:8006

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1                                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Username: [root@pam                                  ] │ │
│  │ Password: [••••••••••                                ] │ │
│  │ Realm: [Proxmox VE authentication ▼]                 │ │
│  │                                                        │ │
│  │                                [ Login ]              │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Proxmox VE 9.1 - Dashboard                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Datacenter ─────────────────────────────────────────┐  │
│  │                                                      │  │
│  │  ├─ proxmox-ve (online)                             │  │
│  │  │  ├─ CPU: 4 cores (0% used)                       │  │
│  │  │  ├─ Memory: 4GB (512MB used)                     │  │
│  │  │  ├─ Disk: 50GB (2GB used)                        │  │
│  │  │  ├─ Uptime: 5 minutes                            │  │
│  │  │  └─ Status: online                               │  │
│  │  │                                                   │  │
│  │  ├─ VMs: 0                                          │  │
│  │  ├─ Containers: 0                                   │  │
│  │  └─ Storage: local (50GB available)                 │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Tasks ───────────────────────────────────────────────┐  │
│  │ No tasks                                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 📋 Terminal 1: Após Instalação (Menu)

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

Escolha uma opção (1-8): 4

[INFO] Testando conectividade
[INFO] Testando ping em 192.168.122.100...
✓ Ping bem-sucedido
[INFO] Testando porta 8006...
✓ Porta 8006 aberta
[INFO] Acesse: https://192.168.122.100:8006

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

Escolha uma opção (1-8): 5

[INFO] Configurando para MHC Cloud Panel
IP do Proxmox (padrão: 192.168.122.100): 
Senha do root do Proxmox: ••••••••••

[INFO] Conectando ao Proxmox...
[INFO] Criando usuário mhc@pam...
[INFO] Criando token de API...
[INFO] Testando token...
✓ Token funcionando

[INFO] Configuração concluída
Arquivo .env.proxmox foi criado
Copie as variáveis para seu .env principal

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

Escolha uma opção (1-8): 8

[INFO] Saindo...
```

---

## 📄 Arquivo .env.proxmox Criado

```
# Proxmox VE Configuration
PROXMOX_HOST=https://192.168.122.100:8006
PROXMOX_USER=mhc
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mhc-token
PROXMOX_TOKEN_SECRET=a1b2c3d4-e5f6-7890-abcd-ef1234567890
PROXMOX_VERIFY_SSL=false
NEXT_PUBLIC_PROXMOX_HOST=192.168.122.100
```

---

## 🐳 Docker Containers: Reiniciados

```
$ docker compose restart

Restarting mhc-cloud-panel-backend-1 ... done
Restarting mhc-cloud-panel-frontend-1 ... done
Restarting mhc-cloud-panel-postgres-1 ... done
Restarting mhc-cloud-panel-redis-1 ... done
Restarting mhc-cloud-panel-celery-1 ... done

$ docker compose logs -f

backend-1  | [INFO] Starting FastAPI server...
backend-1  | [INFO] Proxmox API conectado com sucesso
backend-1  | [INFO] Listening on 0.0.0.0:8000
frontend-1 | ▲ Next.js 14.0.0
frontend-1 | - Local: http://localhost:3000
frontend-1 | ✓ Ready in 2.5s
postgres-1 | [INFO] PostgreSQL started
redis-1    | [INFO] Redis started
celery-1   | [INFO] Celery worker started
```

---

## 🌐 Browser: MHC Cloud Panel

```
URL: http://localhost:3000/admin/infrastructure

┌──────────────────────────────────────────────────────────────┐
│ MHC Cloud Panel - Infrastructure                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Proxmox Nodes ───────────────────────────────────────┐  │
│  │                                                        │  │
│  │  Node: proxmox-ve                                     │  │
│  │  Status: ✓ Online                                     │  │
│  │  CPU: 4 cores (0% used)                               │  │
│  │  Memory: 4GB (512MB used)                             │  │
│  │  Disk: 50GB (2GB used)                                │  │
│  │  Uptime: 5 minutes                                    │  │
│  │                                                        │  │
│  │  [ Create VM ]  [ View Details ]                      │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Virtual Machines ────────────────────────────────────┐  │
│  │                                                        │  │
│  │  No VMs created yet                                   │  │
│  │                                                        │  │
│  │  [ Create VM ]                                        │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Storage ────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  Storage: local                                       │  │
│  │  Type: dir                                            │  │
│  │  Size: 50GB                                           │  │
│  │  Used: 2GB                                            │  │
│  │  Available: 48GB                                      │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ Resultado Final

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                  ✅ Setup Completo!                           ║
║                                                                ║
║  ✓ Proxmox VE 9.1 rodando em VM KVM                           ║
║  ✓ IP: 192.168.122.100                                        ║
║  ✓ Web UI: https://192.168.122.100:8006                       ║
║  ✓ API: Funcionando                                           ║
║  ✓ MHC Cloud Panel integrado                                  ║
║  ✓ Frontend: http://localhost:3000                            ║
║  ✓ Backend: http://localhost:8000                             ║
║  ✓ Database: PostgreSQL                                       ║
║  ✓ Cache: Redis                                               ║
║  ✓ Tasks: Celery                                              ║
║                                                                ║
║              Pronto para criar VMs!                           ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

**Parabéns! Você completou o setup!** 🎉

Próximos passos:
1. Criar VMs de teste
2. Testar provisioning
3. Testar billing
4. Testar rebalanceamento
5. Deploy em produção
