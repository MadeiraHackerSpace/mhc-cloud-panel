# MHC Cloud Panel — Reconhecimento do Projeto

> Gerado em: 2026-04-14  
> Objetivo: Mapear o modelo de negócio, o que foi implementado e o que ainda falta.

---

## Modelo de Negócio

O **MHC Cloud Panel** é uma plataforma **SaaS multi-tenant** para **revenda e gestão de VPS** hospedadas sobre **Proxmox VE**. O modelo opera em três camadas:

| Camada | Quem | O quê |
|---|---|---|
| **Infraestrutura** | Operador/Hackerspace | Gerencia o cluster Proxmox, templates, nodes e storage |
| **Revenda (Tenant)** | Revendedores | Cria e gerencia planos, clientes e faturas |
| **Cliente final** | Usuário final | Contrata planos, opera VMs e abre tickets de suporte |

**Fluxo de receita principal:**

1. Tenant define planos com preço (CPU/RAM/Disco/Tráfego)
2. Cliente contrata → sistema cria `Service` + `Invoice` + `Job`
3. Worker Celery provisiona a VM no Proxmox via clone de template Cloud-Init
4. Cliente paga fatura → serviço permanece ativo; inadimplência → suspensão automática + stop da VM

---

## O que está implementado

### ✅ Backend — Core & Infraestrutura

| Componente | Status | Detalhes |
|---|---|---|
| FastAPI app + CORS + versionamento `/api/v1` | ✅ Completo | `main.py` configurado |
| PostgreSQL + SQLAlchemy 2.x + Alembic | ✅ Completo | Engine, sessões, migrações |
| Redis + Celery | ✅ Completo | `celery_app.py` com broker/backend |
| Docker Compose (postgres, redis, backend, frontend) | ✅ Completo | Stack completa orquestrada |
| Logs estruturados (structlog, sem vazar secrets) | ✅ Completo | `core/logging.py` |
| Tratamento de erros padronizado | ✅ Completo | `core/errors.py` |
| Seed de dados fictícios | ✅ Completo | 3 usuários demo + templates |
| Mock da API Proxmox | ✅ Completo | `proxmox_mock.py` para dev sem cluster real |

### ✅ Backend — Domínio / Modelos

Todos os 26 models de domínio estão criados:

`Tenant`, `Role`, `User`, `Customer`, `Plan`, `PlanFeature`, `Service`, `VirtualMachine`, `IpAllocation`, `Invoice`, `Payment`, `Coupon`, `Ticket`, `TicketMessage`, `Job`, `ServiceAction`, `AuditLog`, `ProxmoxNode`, `ProxmoxStorage`, `ProxmoxTemplate`, `Notification`, `ApiCredential`, `RefreshToken`

### ✅ Backend — Endpoints API

| Módulo | Endpoints | Status |
|---|---|---|
| **Auth** | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` | ✅ |
| **Usuários** | `GET /users`, `POST /users` | ✅ |
| **Planos** | `GET /plans`, `POST /plans` | ✅ |
| **Clientes** | `GET /customers`, `POST /customers` | ✅ |
| **Serviços** | `POST /services/contract`, `GET /services` | ✅ |
| **VMs** | `GET /vms`, `GET /vms/{id}`, `GET /vms/{id}/status` | ✅ |
| **VM Actions** | `POST /vms/{id}/start\|stop\|reboot\|cancel` | ✅ |
| **Faturas** | `GET /invoices`, `POST /invoices/{id}/mark-paid` | ✅ |
| **Tickets** | `GET /tickets`, `POST /tickets`, `GET /tickets/{id}`, `POST /tickets/{id}/messages` | ✅ |
| **Admin — Jobs** | `GET /admin/jobs` | ✅ |
| **Admin — Auditoria** | `GET /admin/audit` | ✅ |
| **Admin — Proxmox** | `GET /admin/proxmox/nodes`, templates, storage | ✅ |

### ✅ Backend — Tasks Assíncronas (Celery)

| Task | Status | Detalhes |
|---|---|---|
| `provision_vm` | ✅ Completo | Clone de template Cloud-Init, network, SSH key, IP |
| `sync_vm_status` | ✅ Completo | Atualiza status VM via Proxmox |
| `mark_overdue_and_suspend` | ✅ Completo | Marca inadimplentes, suspende serviço, para VM |

### ✅ Backend — Integrações

| Integração | Status | Detalhes |
|---|---|---|
| `ProxmoxService` | ✅ Completo | Clone, start/stop/reboot, status, nodes, templates |
| Proxmox Cloud-Init | ✅ Completo | ciuser, ipconfig, SSH key injection |
| Teste real SSH | ✅ Completo | Valida clone + Cloud-Init + acesso SSH real |
| Email | ⚠️ Placeholder | Pasta criada, `__init__.py` vazio |

### ✅ Backend — Segurança / RBAC

| Feature | Status |
|---|---|
| JWT access + refresh tokens | ✅ |
| RBAC: `super_admin`, `operador`, `financeiro`, `suporte`, `cliente` | ✅ |
| Isolamento por Tenant | ✅ |
| Auditoria de ações | ✅ |

### ✅ Frontend — Estrutura (Next.js + Tailwind)

| Área | Rota | Status |
|---|---|---|
| Login | `/login` | ✅ |
| Dashboard do cliente | `/dashboard` | ✅ |
| Lista de VPS | `/dashboard/vps` | ✅ |
| Detalhe/ações de VPS | `/dashboard/vps/[id]` | ✅ |
| Planos (catálogo + contratar) | `/dashboard/planos` | ✅ |
| Faturas | `/dashboard/invoices` | ✅ |
| Tickets | `/dashboard/tickets` | ✅ |
| Admin — visão geral | `/admin` | ✅ |
| Admin — Customers | `/admin/customers` | ✅ |
| Admin — Plans | `/admin/plans` | ✅ |
| Admin — Jobs | `/admin/jobs` | ✅ |
| Admin — Auditoria | `/admin/audit` | ✅ |
| Admin — Infraestrutura | `/admin/infrastructure` | ✅ |
| Dark/Light mode | global | ✅ |
| Autenticação via middleware Next.js | `middleware.ts` | ✅ |

### ✅ Testes

| Teste | Status |
|---|---|
| `test_auth.py` — login e JWT | ✅ |
| `test_contract_flow.py` — contratação end-to-end | ✅ |
| `test_real_proxmox_ssh.py` — integração real (skipado por padrão) | ✅ |

---

## O que está incompleto / falta implementar

### 🔴 Alta Prioridade — Para fechar o modelo de negócio

| O que falta | Impacto |
|---|---|
| **Integração de pagamento real** (ex.: Stripe, PagSeguro, Mercado Pago) | Sem isso o billing é 100% manual (`mark-paid`). Inviável para escala. |
| **Webhooks de pagamento** (confirmação automática) | Sem conciliação automática de faturas |
| **Ciclo de renovação de faturamento** | `mark_overdue_and_suspend` existe mas **não há `Celery Beat` configurado** — a task nunca roda automaticamente. |
| **Reativação automática pós-pagamento** | `mark-paid` reativa o serviço no banco, mas o start da VM no Proxmox é manual. |
| **Cancelamento e exclusão da VM no Proxmox** | `cancel` muda status do serviço mas **não destroi a VM** no Proxmox (`proxmox.delete_vm` não é chamado). |
| **Notificações por email** | Integração de email é um placeholder vazio. Sem alertas de vencimento, provisionamento ou tickets. |

### 🟡 Média Prioridade — Operação e Self-Service

| O que falta | Detalhes |
|---|---|
| **Console web da VM** (noVNC/SPICE) | Essencial para o cliente acessar a VM sem SSH |
| **Reset de senha da VM** | `ServiceActionType.reset_password` existe no enum, mas sem endpoint/task |
| **Rebuild da VM** | `ServiceActionType.rebuild` existe no enum, sem implementação |
| **Snapshots e backups** | Definidos no roadmap, não iniciados |
| **Resize de recursos** (CPU/RAM/Disco) | Roadmap item, não iniciado |
| **Onboarding de Tenant via UI** | Cadastro de revendedor não existe; só via seed/admin direto |
| **Pró-rata e cupons** | Model `Coupon` existe no banco, sem lógica de aplicação |
| **Multi-moeda e impostos** | Não iniciado |

### 🟡 Média Prioridade — Admin e Observabilidade

| O que falta | Detalhes |
|---|---|
| **Scheduler Celery Beat** | `mark_overdue_and_suspend` e `sync_vm_status` precisam de agendamento periódico |
| **Métricas do cluster** | CPU/mem/disk/net por node/storage em tempo real (estilo Grafana) |
| **Dashboard de capacidade** | Scheduler de provisionamento por capacidade disponível; hoje o node é passado manualmente |
| **Prometheus exporter** | Métricas para coleta externa |
| **IP allocation gerenciado** | Model `IpAllocation` existe, sem lógica para alocar/liberar IPs de um pool |

### 🟠 Baixa Prioridade / Hardening

| O que falta | Detalhes |
|---|---|
| **Rate limiting** | Nenhum rate limit nos endpoints públicos |
| **Repositories pattern** | Pasta `repositories/` criada mas vazia — lógica de DB está nos routes diretamente |
| **Testes de cobertura ampla** | Apenas 3 arquivos de teste; falta billing, tickets, admin, VMs |
| **Branding por tenant** | Logo, cores e domínio customizado por revenda |
| **RBAC mais granular** | Escopo de ações por tenant/plano mais fino |
| **2FA** | Não implementado |

---

## Resumo Executivo

```
Backend core/RBAC    ████████████████████  100%
Modelos de domínio   ███████████████████░  ~95%
Integração Proxmox   ███████████████░░░░░  ~75%
API / endpoints      ██████████████░░░░░░  ~70%
Frontend / UI        █████████████░░░░░░░  ~65%
Tasks assíncronas    ██████████░░░░░░░░░░  ~50%
Billing              ██████░░░░░░░░░░░░░░  ~30%
Testes               █████░░░░░░░░░░░░░░░  ~25%
Observabilidade      ██░░░░░░░░░░░░░░░░░░  ~10%
Notificações email   █░░░░░░░░░░░░░░░░░░░  ~5%

TOTAL ESTIMADO       ████████████░░░░░░░░  ~60%
```

> **Para tornar o produto comercialmente viável**, os próximos passos críticos são:
> 1. Configurar **Celery Beat** com schedule para `mark_overdue_and_suspend` e `sync_vm_status`
> 2. Implementar **gateway de pagamento** com webhook de confirmação
> 3. Implementar **delete da VM no Proxmox** ao cancelar o serviço
> 4. Implementar **envio de email** (cobrança, provisionamento, tickets)
