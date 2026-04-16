# 🏗️ Arquitetura Visual - Proxmox VE 9.1 em VM KVM

## 📐 Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Windows 11 / WSL2                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Debian WSL2 (Linux)                       │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │              KVM / QEMU / libvirt                      │ │  │
│  │  ├────────────────────────────────────────────────────────┤ │  │
│  │  │                                                        │ │  │
│  │  │  ┌──────────────────────────────────────────────────┐ │ │  │
│  │  │  │   Proxmox VE 9.1 (VM)                           │ │ │  │
│  │  │  │   IP: 192.168.122.100                           │ │ │  │
│  │  │  │   CPU: 4 cores | RAM: 4GB | Disk: 50GB         │ │ │  │
│  │  │  ├──────────────────────────────────────────────────┤ │ │  │
│  │  │  │                                                  │ │ │  │
│  │  │  │  ┌─ pvedaemon (API)                             │ │ │  │
│  │  │  │  │  Port: 8006                                  │ │ │  │
│  │  │  │  │  https://192.168.122.100:8006                │ │ │  │
│  │  │  │  │                                              │ │ │  │
│  │  │  │  ├─ pveproxy (Web UI)                           │ │ │  │
│  │  │  │  │  Port: 8006                                  │ │ │  │
│  │  │  │  │                                              │ │ │  │
│  │  │  │  ├─ pvestatd (Stats)                            │ │ │  │
│  │  │  │  │                                              │ │ │  │
│  │  │  │  └─ Storage                                     │ │ │  │
│  │  │  │     /var/lib/vz/images (VMs)                    │ │ │  │
│  │  │  │     /var/lib/vz/template (Templates)            │ │ │  │
│  │  │  │                                                  │ │ │  │
│  │  │  └──────────────────────────────────────────────────┘ │ │  │
│  │  │                                                        │ │  │
│  │  │  ┌──────────────────────────────────────────────────┐ │ │  │
│  │  │  │   Rede Virtual (virbr0)                         │ │ │  │
│  │  │  │   192.168.122.0/24                             │ │ │  │
│  │  │  │   Gateway: 192.168.122.1                       │ │ │  │
│  │  │  │   DHCP: 192.168.122.2 - 192.168.122.254        │ │ │  │
│  │  │  └──────────────────────────────────────────────────┘ │ │  │
│  │  │                                                        │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  │                                                              │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │         Docker Containers (MHC Cloud Panel)           │ │  │
│  │  ├────────────────────────────────────────────────────────┤ │  │
│  │  │                                                        │ │  │
│  │  │  ┌─ Backend (FastAPI)                                │ │  │
│  │  │  │  Port: 8000                                       │ │  │
│  │  │  │  Conecta a: Proxmox API (192.168.122.100:8006)   │ │  │
│  │  │  │                                                   │ │  │
│  │  │  ├─ Frontend (Next.js)                               │ │  │
│  │  │  │  Port: 3000                                       │ │  │
│  │  │  │  http://localhost:3000                           │ │  │
│  │  │  │                                                   │ │  │
│  │  │  ├─ Database (PostgreSQL)                            │ │  │
│  │  │  │  Port: 5432                                       │ │  │
│  │  │  │                                                   │ │  │
│  │  │  ├─ Redis (Cache)                                    │ │  │
│  │  │  │  Port: 6379                                       │ │  │
│  │  │  │                                                   │ │  │
│  │  │  └─ Celery (Tasks)                                   │ │  │
│  │  │     Conecta a: Proxmox API                           │ │  │
│  │  │                                                        │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔌 Fluxo de Comunicação

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Fluxo de Requisições                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Browser                                                            │
│    ↓                                                                │
│  http://localhost:3000 (Frontend Next.js)                          │
│    ↓                                                                │
│  http://localhost:8000/api (Backend FastAPI)                       │
│    ↓                                                                │
│  https://192.168.122.100:8006/api2/json (Proxmox API)              │
│    ↓                                                                │
│  Proxmox VE 9.1 (VM KVM)                                            │
│    ↓                                                                │
│  Resposta: JSON com dados de VMs, nodes, storage, etc.             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 📦 Componentes Principais

### 1. Proxmox VE 9.1 (VM)

```
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox VE 9.1                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Serviços:                                                  │
│  ├─ pvedaemon (API REST)                                   │
│  │  └─ Porta: 8006                                         │
│  │  └─ Protocolo: HTTPS                                    │
│  │  └─ Autenticação: Token ou Username/Password            │
│  │                                                         │
│  ├─ pveproxy (Web UI)                                      │
│  │  └─ Porta: 8006                                         │
│  │  └─ Interface: Web                                      │
│  │                                                         │
│  ├─ pvestatd (Estatísticas)                                │
│  │  └─ Coleta dados de nodes e VMs                         │
│  │                                                         │
│  └─ Storage                                                │
│     ├─ Local (50GB)                                        │
│     ├─ Templates                                           │
│     └─ ISOs                                                │
│                                                             │
│  Usuários:                                                  │
│  ├─ root@pam (Admin)                                       │
│  └─ mhc@pam (API User)                                     │
│     └─ Token: mhc-token                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. MHC Cloud Panel (Docker)

```
┌─────────────────────────────────────────────────────────────┐
│                  MHC Cloud Panel                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (Next.js)                                         │
│  ├─ Port: 3000                                             │
│  ├─ Pages:                                                 │
│  │  ├─ /admin/infrastructure (Proxmox)                     │
│  │  ├─ /admin/customers                                    │
│  │  ├─ /admin/plans                                        │
│  │  └─ /admin/audit                                        │
│  │                                                         │
│  Backend (FastAPI)                                         │
│  ├─ Port: 8000                                             │
│  ├─ Endpoints:                                             │
│  │  ├─ /api/v1/proxmox/* (Proxmox integration)             │
│  │  ├─ /api/v1/customers/* (Customer management)           │
│  │  ├─ /api/v1/vms/* (VM management)                       │
│  │  └─ /api/v1/billing/* (Billing)                         │
│  │                                                         │
│  Database (PostgreSQL)                                     │
│  ├─ Port: 5432                                             │
│  ├─ Tables:                                                │
│  │  ├─ customers                                           │
│  │  ├─ vms                                                 │
│  │  ├─ plans                                               │
│  │  ├─ invoices                                            │
│  │  └─ audit_logs                                          │
│  │                                                         │
│  Cache (Redis)                                             │
│  ├─ Port: 6379                                             │
│  ├─ Uso:                                                   │
│  │  ├─ Session storage                                     │
│  │  ├─ Rate limiting                                       │
│  │  └─ Cache de dados                                      │
│  │                                                         │
│  Tasks (Celery)                                            │
│  ├─ Broker: Redis                                          │
│  ├─ Tasks:                                                 │
│  │  ├─ provision_vm (Criar VM)                             │
│  │  ├─ sync_vm_status (Sincronizar status)                 │
│  │  ├─ billing (Gerar faturas)                             │
│  │  └─ rebalance_cluster (Rebalancear)                     │
│  │                                                         │
│  └─ Integração Proxmox:                                    │
│     ├─ Host: 192.168.122.100                               │
│     ├─ Port: 8006                                          │
│     ├─ User: mhc@pam                                       │
│     └─ Token: mhc-token                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🌐 Rede

```
┌─────────────────────────────────────────────────────────────┐
│                    Rede Virtual (virbr0)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Subnet: 192.168.122.0/24                                  │
│  Gateway: 192.168.122.1 (Host WSL)                         │
│  DHCP Range: 192.168.122.2 - 192.168.122.254               │
│                                                             │
│  Dispositivos:                                              │
│  ├─ virbr0 (Bridge)                                        │
│  │  └─ IP: 192.168.122.1                                   │
│  │                                                         │
│  ├─ Proxmox VE (VM)                                        │
│  │  └─ IP: 192.168.122.100                                 │
│  │  └─ MAC: 52:54:00:12:34:56                              │
│  │                                                         │
│  └─ Outras VMs (futuras)                                   │
│     └─ IPs: 192.168.122.101+                               │
│                                                             │
│  Conectividade:                                             │
│  ├─ Proxmox ↔ Host WSL: ✓ (NAT)                            │
│  ├─ Proxmox ↔ Docker: ✓ (Host network)                     │
│  └─ Proxmox ↔ Internet: ✓ (Via host)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 💾 Storage

```
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layout                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  /var/lib/libvirt/images/ (Host WSL)                        │
│  ├─ proxmox-ve-9.0.iso (1.8GB)                             │
│  │  └─ ISO do Proxmox VE 9.1                               │
│  │                                                         │
│  └─ proxmox-ve.qcow2 (50GB)                                │
│     └─ Disco virtual da VM Proxmox                         │
│                                                             │
│  /var/lib/vz/ (Dentro da VM Proxmox)                        │
│  ├─ images/ (VMs)                                          │
│  │  └─ Discos das VMs criadas                              │
│  │                                                         │
│  ├─ template/ (Templates)                                  │
│  │  ├─ iso/ (ISOs)                                         │
│  │  └─ cache/ (Cache de templates)                         │
│  │                                                         │
│  └─ dump/ (Backups)                                        │
│     └─ Backups de VMs                                      │
│                                                             │
│  Docker Volumes                                             │
│  ├─ postgres_data (Database)                               │
│  ├─ redis_data (Cache)                                     │
│  └─ app_logs (Logs)                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Segurança

```
┌─────────────────────────────────────────────────────────────┐
│                    Segurança                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Proxmox VE:                                                │
│  ├─ HTTPS (Port 8006)                                      │
│  ├─ Self-signed certificate                                │
│  ├─ Autenticação: Token ou Username/Password               │
│  ├─ Usuário: mhc@pam (API)                                 │
│  └─ Token: mhc-token (Sem privilégios de root)             │
│                                                             │
│  MHC Cloud Panel:                                           │
│  ├─ HTTP (Port 3000) - Desenvolvimento                     │
│  ├─ HTTPS (Port 443) - Produção                            │
│  ├─ JWT tokens para autenticação                           │
│  ├─ Refresh tokens com expiração                           │
│  ├─ Rate limiting                                          │
│  └─ Audit logging                                          │
│                                                             │
│  Rede:                                                      │
│  ├─ Rede virtual isolada (virbr0)                          │
│  ├─ NAT para acesso à internet                             │
│  ├─ Firewall do host WSL                                   │
│  └─ Sem acesso direto da internet                          │
│                                                             │
│  Dados:                                                     │
│  ├─ Database: PostgreSQL com senha                         │
│  ├─ Redis: Sem autenticação (rede privada)                 │
│  ├─ Variáveis sensíveis: .env (não versionado)             │
│  └─ Logs: Auditoria de todas as ações                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                  Fluxo de Provisioning                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Usuário clica "Criar VM"                                │
│     ↓                                                       │
│  2. Frontend envia requisição                               │
│     ↓                                                       │
│  3. Backend valida dados                                    │
│     ↓                                                       │
│  4. Backend cria registro no Database                       │
│     ↓                                                       │
│  5. Backend envia task para Celery                          │
│     ↓                                                       │
│  6. Celery chama Proxmox API                                │
│     ↓                                                       │
│  7. Proxmox cria VM                                         │
│     ↓                                                       │
│  8. Celery monitora status                                  │
│     ↓                                                       │
│  9. Backend atualiza Database                               │
│     ↓                                                       │
│  10. Frontend mostra resultado                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Próximos Passos

Após setup completo:

```
┌─────────────────────────────────────────────────────────────┐
│                  Roadmap                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✓ Proxmox VE 9.1 em VM KVM                                │
│  ✓ MHC Cloud Panel integrado                               │
│  → Criar VMs de teste                                      │
│  → Testar provisioning                                     │
│  → Testar billing                                          │
│  → Testar rebalanceamento                                  │
│  → Testar failover                                         │
│  → Testar backup/restore                                   │
│  → Testar scaling                                          │
│  → Testar performance                                      │
│  → Deploy em produção                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Arquitetura pronta para começar!** 🚀
