# MHC Cloud Panel

Plataforma SaaS multi-tenant para revenda e gestão de VPS sobre Proxmox VE (tratado como backend de infraestrutura), com portal do cliente, painel administrativo, provisionamento assíncrono, billing básico, tickets e auditoria.

## Licença

Apache-2.0. Veja [LICENSE](file:///c:/Users/fabio/Documents/trae_projects/MHC_Cloud_Panel/LICENSE).

## Stack

- Backend: FastAPI + SQLAlchemy 2.x + Alembic
- Banco: PostgreSQL
- Filas: Celery + Redis
- Frontend: Next.js + TypeScript + Tailwind (dark/light)
- Integração Proxmox: `ProxmoxService` (adaptador `proxmoxer`)
- Testes: pytest

## Subir com Docker Compose

1. Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

2. Edite `.env` com as credenciais do Proxmox (veja “Conectar ao Proxmox”).

3. Suba os serviços:

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend (OpenAPI): http://localhost:8000/docs

## Conectar ao Proxmox (API token)

Recomendação: criar um usuário dedicado no Proxmox com privilégios mínimos e um API Token.

Preencha no `.env`:

- `PROXMOX_HOST` (ex.: `https://pve.seudominio:8006`)
- `PROXMOX_USER` (sem realm, ex.: `api-user`)
- `PROXMOX_REALM` (ex.: `pam` ou `pve`)
- `PROXMOX_TOKEN_NAME`
- `PROXMOX_TOKEN_SECRET`
- `PROXMOX_VERIFY_SSL` (`true`/`false`)

Notas:

- O token e o secret ficam apenas no backend (env vars).
- Logs não registram secrets.
- Timeouts e retries são configuráveis via env.

## Seeds (dados fictícios)

Por padrão, o backend pode criar tabelas e seed na inicialização quando `SEED_ON_STARTUP=true`.

Credenciais demo:

- `superadmin@mhc.local` / `admin12345`
- `operador@mhc.local` / `admin12345`
- `cliente@mhc.local` / `admin12345`

Templates demo (ajuste para o seu cluster):

- `Ubuntu 22.04 Cloud-Init` vmid `9000`
- `Debian 12 Cloud-Init` vmid `9001`

## Migrations (Alembic)

Para usar Alembic:

```bash
docker compose exec backend alembic upgrade head
```

## Fluxos implementados (MVP)

- Auth: login, refresh token, logout, perfil (`/auth/me`)
- RBAC: `super_admin`, `operador`, `financeiro`, `suporte`, `cliente`
- Clientes (admin): criar e listar
- Planos (admin): criar e listar
- Contratar plano (cliente): cria Service + Invoice + Job e dispara provisionamento assíncrono
- VMs: listar/detalhar, start/stop/reboot, consultar status no Proxmox
- Billing básico: listar faturas, marcar como paga (financeiro)
- Tickets: abrir ticket e comentar
- Auditoria e jobs: listagem no admin

## Endpoints principais

Todos versionados em `/api/v1`.

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /plans`
- `POST /plans` (admin)
- `POST /services/contract`
- `GET /vms`
- `POST /vms/{vm_id}/start|stop|reboot`
- `GET /vms/{vm_id}/status`
- `GET /invoices`
- `POST /invoices/{invoice_id}/mark-paid` (financeiro)
- `GET/POST /tickets`
- `GET /admin/proxmox/nodes`
- `GET /admin/jobs`
- `GET /admin/audit`

## Testes

Os testes usam o `DATABASE_URL` para conectar no Postgres.

Exemplo (com o Postgres do compose rodando):

```bash
docker compose exec backend pytest
```

## Estrutura de pastas (backend)

`backend/app`:

- `api/`
- `core/`
- `models/`
- `schemas/`
- `services/`
- `tasks/`
- `integrations/proxmox/`
- `integrations/email/`
- `utils/`
- `tests/`

## Estrutura de pastas (frontend)

`frontend/`:

- `app/`
- `components/`
- `lib/api/`
- `lib/types/`
- `styles/`
