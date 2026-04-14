# Contribuindo

Este projeto é voltado para uso e colaboração em hackerspaces/labs: foco em simplicidade, segurança e documentação prática.

## Princípios

- Não comite segredos (`.env`, tokens, senhas, chaves). Versione apenas `.env.example`.
- Mantenha endpoints versionados em `/api/v1`.
- Prefira mudanças pequenas e revisáveis (PRs curtos).
- Evite acoplamento forte com Proxmox real: use o `proxmox_mock` em desenvolvimento.

## Setup (Docker Compose)

1. Copie o exemplo:

```bash
copy .env.example .env
```

2. Suba tudo:

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend (OpenAPI): http://localhost:8000/docs
- Proxmox Mock: http://localhost:8001/api2/json/nodes

## Seed (usuários demo)

- `superadmin@mhc.local` / `admin12345`
- `operador@mhc.local` / `admin12345`
- `cliente@mhc.local` / `admin12345`

## Testes

Backend:

```bash
docker compose exec backend pytest
```

Frontend:

```bash
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
docker compose exec frontend npm run build
```

## Padrões de código

- Backend: FastAPI + SQLAlchemy 2.x; evitar SQL “raw” sem necessidade; manter erros como `AppError`.
- Frontend: Next.js App Router; UI em pt-BR; evitar lógica de auth no cliente (cookies httpOnly).
- Logs: nunca imprimir tokens/secrets.

## Pull Requests

- Descreva o impacto no modelo de negócio (Cliente/Plano/Serviço/VM/Fatura/Ticket).
- Inclua instruções de teste manual quando aplicável.
