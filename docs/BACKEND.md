# Backend (FastAPI) — documentação por módulo

Este documento liga cada módulo do backend ao modelo de negócio do MHC Cloud Panel: revenda de VPS com multi-tenant, provisionamento assíncrono e auditoria.

## Modelo de negócio (visão curta)

Entidades principais:

- Tenant: “revenda”/organização dona dos recursos (isolamento lógico).
- Role/User: RBAC para separar permissões (super_admin, operador, cliente, etc.).
- Customer: cliente final (pertence a um Tenant).
- Plan: oferta comercial (CPU/RAM/Disco/Tráfego/recursos) e preços.
- Service: assinatura do cliente para um plano (ciclo de cobrança, status).
- VirtualMachine: instância provisionada no Proxmox (node/vmid/status).
- Invoice/Payment: cobrança e recebimento.
- Ticket/TicketMessage: suporte.
- Job/ServiceAction/AuditLog: trilha operacional (fila, ações, auditoria).
- ProxmoxNode/ProxmoxStorage/ProxmoxTemplate: metadados de infraestrutura.

Fluxo principal (cliente):

1. Cliente autentica (JWT access/refresh).
2. Cliente contrata um Plan → cria Service + Invoice + Job.
3. Worker Celery executa provisionamento via integração Proxmox (ou mock).
4. Portal exibe VM(s), status e faturas; suporte usa tickets; admin monitora jobs/auditoria.

## app/main.py

Responsabilidade: criação da aplicação FastAPI, middlewares, roteamento e inicialização.

Relação com negócio: é a “porta de entrada” do SaaS (API versionada em `/api/v1`).

## app/api/

### app/api/v1/router.py + app/api/v1/routes/*

Responsabilidade: endpoints HTTP do produto.

Relação com negócio:

- Auth (`/auth/*`): login, refresh, me.
- Planos (`/plans`): catálogo e gestão (admin).
- Serviços (`/services`): contratação, listagem por tenant/cliente.
- VMs (`/vms`): operações e status.
- Faturas (`/invoices`): cobrança e marcação como paga (financeiro).
- Tickets (`/tickets`): suporte.
- Admin: Proxmox metadata, jobs, auditoria.

### app/api/deps.py

Responsabilidade: dependências do FastAPI (DB session, autenticação, RBAC).

Relação com negócio: garante isolamento por Tenant e autorizações por Role.

## app/core/

### config.py

Responsabilidade: leitura/validação das env vars (URLs, segredos, timeouts).

Relação com negócio: configura “ambiente de operação” (ex.: Proxmox real vs mock).

### database.py

Responsabilidade: engine/sessionmaker SQLAlchemy e lifecycle do banco.

Relação com negócio: persistência de todas as entidades (tenant, cobrança, tickets…).

### security.py

Responsabilidade: hashing de senha, JWT, validação de tokens.

Relação com negócio: autenticação do portal e separação de papéis.

### errors.py

Responsabilidade: padronização de erros de domínio (status, code, details).

Relação com negócio: erros coerentes para UI e integrações (ex.: “proxmox_error”).

### logging.py

Responsabilidade: logs estruturados (sem vazar segredos).

Relação com negócio: operação/auditoria, debugging em produção e em hackerspaces.

## app/models/

Responsabilidade: modelo relacional do domínio (SQLAlchemy).

Relação com negócio: representa o “estado” do SaaS.

Mapeamento prático:

- tenant.py: revenda/organização.
- role.py + user.py: RBAC e usuários.
- customer.py: cliente final.
- plan.py + plan_feature.py: produto e opcionais.
- service.py: assinatura/contratação do plano.
- virtual_machine.py: VM provisionada (node/vmid/status).
- ip_allocation.py: IPs do serviço/VM (quando aplicável).
- invoice.py + payment.py: cobrança e pagamentos.
- ticket.py + ticket_message.py: suporte.
- job.py + service_action.py: tarefas e rastreamento operacional.
- audit_log.py: trilha de auditoria.
- proxmox_node.py + proxmox_storage.py + proxmox_template.py: inventário Proxmox.
- notification.py + api_credential.py: utilidades de plataforma.

## app/schemas/

Responsabilidade: contratos de entrada/saída da API (Pydantic).

Relação com negócio: define como o frontend consome/produz dados do domínio (ex.: `ServiceOut`, `VMOut`, `InvoiceOut`).

## app/services/

Responsabilidade: regras de negócio e orquestração síncrona (domínio).

Relação com negócio:

- auth_service.py: login, refresh, validações e emissão de tokens.
- audit_service.py: grava eventos relevantes (quem fez, o que fez, sucesso/erro).

## app/tasks/

Responsabilidade: execução assíncrona (Celery) para operações demoradas/idempotentes.

Relação com negócio: provisionar VM, sincronizar status, billing e jobs.

Arquivos típicos:

- celery_app.py: configuração do broker/backend.
- provision_vm.py: provisionamento via Proxmox (mock em dev).
- sync_vm_status.py: status e consistência do inventário.
- billing.py: rotinas de cobrança.

## app/integrations/

Responsabilidade: integrações externas.

Relação com negócio:

- proxmox/service.py: API do Proxmox (e adapter HTTP para `proxmox_mock`).
- email/: placeholder para envio de notificações.

## backend/proxmox_mock.py

Responsabilidade: servidor mock da API do Proxmox (subset do `/api2/json`).

Relação com negócio: permite rodar o produto em hackerspaces sem cluster Proxmox real (testar contratação, VM actions e status).

## app/tests/

Responsabilidade: testes automatizados (pytest).

Relação com negócio: valida fluxos críticos (auth e contratação) e garante regressão controlada.

## Roadmap (anotações para implementações futuras)

### Para completar o modelo de negócio (visão geral)

- Cobrança: integrações de pagamento, conciliação via webhooks, ciclo de renovação, suspensão/reativação por inadimplência, pró-rata, cupons/créditos, multi-moeda/impostos (se aplicável).
- Operação: onboarding de tenant/revenda (branding, regras de preço, limites), notificações (cobrança/incidentes/tickets), observabilidade e rotinas de backup/DR.
- Segurança: hardening de secrets, rate-limit, trilha de auditoria completa e RBAC mais fino por escopo/tenant.

### Foco inicial: operações de VM + acompanhamento de recursos (estilo Grafana)

- Operações de VM: resize (CPU/RAM/Disk), snapshots, backups, rebuild, console, reset senha, políticas de power/state.
- Métricas do cluster: CPU/mem/disk/net por node/storage e capacidade disponível para decisão de provisionamento.
- Scheduler de provisionamento: escolha de node/storage baseada em capacidade/afinidade e regras por tenant/plano.
- Coleta e dashboard: exportar métricas para Prometheus (ou equivalente) e montar dashboards no Grafana (overview + drill-down por VM/node/tenant).
