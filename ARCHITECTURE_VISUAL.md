# Arquitetura — MHC Cloud Panel

## Visão geral (desenvolvimento no Windows 11)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Windows 11                                                          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Debian WSL2                                                  │   │
│  │                                                               │   │
│  │  Proxmox VE 9.1 (instalado diretamente no Debian Trixie)     │   │
│  │  ├─ pvedaemon   → escuta em 127.0.0.1:85 (interno)           │   │
│  │  ├─ pveproxy    → escuta em *:8006 (HTTPS)                    │   │
│  │  ├─ pvestatd    → coleta métricas                             │   │
│  │  └─ pmxcfs      → filesystem do cluster (/etc/pve via FUSE)   │   │
│  │                                                               │   │
│  │  IP WSL: 172.30.x.x (muda a cada boot)                       │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  netsh portproxy: 0.0.0.0:8006 → <IP_WSL>:8006                      │
│  (necessário para que containers Docker alcancem o Proxmox)          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Docker Desktop                                               │   │
│  │                                                               │   │
│  │  backend (FastAPI :8000)                                      │   │
│  │    └─ PROXMOX_HOST=https://host.docker.internal:8006          │   │
│  │                                                               │   │
│  │  worker (Celery)                                              │   │
│  │  celery-beat (Celery scheduler)                               │   │
│  │  frontend (Next.js :3000)                                     │   │
│  │  db (PostgreSQL :5432)                                        │   │
│  │  redis (Redis :6379)                                          │   │
│  │  proxmox_mock (mock API :8001)                                │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Fluxo de uma requisição

```
Browser → http://localhost:3000 (Next.js)
       → http://localhost:8000/api/v1 (FastAPI)
       → https://host.docker.internal:8006/api2/json (Proxmox VE)
```

## Fluxo de provisionamento de VM

```
POST /services/contract
  → cria Service + Invoice + Job no banco
  → enfileira task Celery `provision_vm`
     → ProxmoxService.create_vm_from_template()
        → clone do template Cloud-Init
        → config (cpu, ram, network, ssh key)
        → start VM
     → atualiza status do Job e VirtualMachine
  → Celery Beat (*/5 min): sync_vm_status atualiza o estado das VMs
```

## Rede (desenvolvimento)

| Componente | Endereço | Observação |
|---|---|---|
| Frontend | http://localhost:3000 | Docker Desktop |
| Backend API | http://localhost:8000 | Docker Desktop |
| Backend OpenAPI | http://localhost:8000/docs | Swagger UI |
| Proxmox Web UI | https://localhost:8006 | Via portproxy WSL |
| Proxmox API | https://localhost:8006/api2/json | Via portproxy WSL |
| Proxmox Mock | http://localhost:8001 | Docker Desktop |
| PostgreSQL | localhost:5432 | Docker Desktop |
| Redis | localhost:6379 | Docker Desktop |

## Modelos de domínio principais

```
Tenant ─── Customer ─── User
  │
  ├── Plan ─── Service ─── VirtualMachine
  │              │
  │              └── Invoice ── Payment
  │
  └── ProxmoxNode / ProxmoxStorage / ProxmoxTemplate
```

## Isolamento multi-tenant

Todas as entidades de negócio (`Service`, `VirtualMachine`, `Invoice`, `Ticket`, etc.) carregam `tenant_id`. Queries são sempre filtradas pelo tenant do usuário autenticado. O `super_admin` e o `operador` operam sem filtro de tenant.
