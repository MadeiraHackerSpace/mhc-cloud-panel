# requirements.md — MHC Cloud Panel: Plano de Remediação

## Contexto

O MHC Cloud Panel é uma plataforma SaaS multi-tenant para revenda e gestão de VPS sobre Proxmox VE. O modelo de negócio envolve um operador central (super_admin/operador) que provisiona e gerencia infraestrutura Proxmox, e múltiplos clientes (tenants) que consomem VPS de forma isolada via painel web. Cada tenant possui seus próprios usuários, serviços, faturas e tickets, com isolamento lógico garantido por `tenant_id` em todas as entidades do banco de dados.

O sistema está em estágio de MVP funcional: autenticação JWT com refresh token rotativo está bem implementada, o NodeScheduler inspirado no ProxLB seleciona nodes automaticamente, e o CI cobre lint, typecheck e testes básicos. No entanto, existem riscos críticos que impedem uso comercial seguro: o `JWT_SECRET` padrão pode ser usado em produção sem nenhuma validação de startup; o cancelamento de serviço não remove a VM no Proxmox (desperdício de infraestrutura e potencial cobrança dupla); o billing é 100% manual; e o isolamento de tenant depende de cada desenvolvedor lembrar de adicionar o filtro `tenant_id` em cada nova query — sem nenhuma camada centralizada que garanta isso.

No frontend, o dashboard do cliente mostra apenas contadores sem contexto útil (sem status de faturas, sem alertas, sem KPIs reais). Ações de VM como desligar e reiniciar não pedem confirmação e usam `window.location.reload()` como feedback. O link "Admin" aparece no menu de todos os usuários independente de role. A cobertura de testes é insuficiente para fluxos críticos como billing, cancelamento e isolamento de tenant.

---

## Objetivos

### Segurança
- Impedir que a aplicação suba em produção com segredos padrão (`JWT_SECRET=change-me`, `SEED_ON_STARTUP=true` fora de `local`)
- Garantir que cookies de autenticação sejam `HttpOnly` e `Secure` em produção
- Implementar rate limiting no endpoint de login para prevenir brute force
- Corrigir autenticação no WebSocket VNC (validar token antes de `websocket.accept()`)
- Implementar fluxo completo de MFA/TOTP (ativação, verificação, desativação)
- Remover ou condicionar credenciais demo expostas na tela de login

### Arquitetura / Manutenibilidade
- Introduzir camada de repositórios (`repositories/`) com filtro automático de tenant
- Extrair lógica de negócio dos route handlers para uma service layer (`ContractService`, `ServiceService`, etc.)
- Centralizar o isolamento de tenant para eliminar dependência de "lembrar do filtro" em cada query
- Corrigir o cancelamento de serviço para remover ou tratar adequadamente a VM no Proxmox
- Alinhar o gerenciador de pacotes do frontend: o projeto usa bun, mas o CI usa npm
- Remover dependências desnecessárias de produção (`paramiko`)

### UX / Usabilidade
- Dashboard do cliente com KPIs reais: status de VMs, próxima fatura, alertas de jobs em falha
- Feedback adequado em ações de VM (sem `window.location.reload()` abrupto)
- Confirmação antes de ações destrutivas (desligar, reiniciar, cancelar serviço)
- Ocultar links de admin para usuários sem permissão
- Estados vazios com CTAs acionáveis
- Página de infraestrutura admin com visualização de capacidade do cluster

### Qualidade / Testes
- Testes de isolamento de tenant (garantir que tenant A não acessa dados do tenant B)
- Testes para billing (suspensão automática, reativação após pagamento)
- Testes para cancelamento de serviço/VM
- Testes para fluxos de autenticação inválida e IDOR attempts

---

## Iniciativas de Alto Nível

| ID | Nome | Descrição |
|---|---|---|
| INIT-001 | Segurança de Segredos e Startup | Validação de JWT_SECRET, SEED_ON_STARTUP, COOKIE_SECURE no startup |
| INIT-002 | Isolamento de Tenant Centralizado | Repositório base com filtro automático de tenant_id |
| INIT-003 | MFA/TOTP | Implementação completa do fluxo de autenticação de dois fatores |
| INIT-004 | Camada de Repositórios e Services | Mover queries e lógica de negócio para repositories/ e services/ |
| INIT-005 | Cancelamento de Serviço e VM | Corrigir cancel_service para tratar VM no Proxmox |
| INIT-006 | Rate Limiting e Segurança de Endpoints | Rate limit no login, auth antes de accept() no WebSocket VNC |
| INIT-007 | UX Dashboard e Feedback | KPIs reais, feedback de ações, estados vazios, links condicionais |
| INIT-008 | Qualidade e Testes | Cobertura de testes para billing, cancelamento, tenant isolation |
| INIT-009 | Limpeza e Padronização | CI usando bun (alinhado ao Dockerfile), paramiko, tsconfig.tsbuildinfo, credenciais demo |

---

## Requisitos Funcionais

### INIT-001 — Segurança de Segredos e Startup

**REQ-001** — O sistema DEVE rejeitar a inicialização quando `JWT_SECRET == "change-me"` e `APP_ENV != "local"`, lançando um erro claro com instrução de correção.
> Referência: INIT-001

**REQ-002** — O sistema DEVE rejeitar a inicialização quando `SEED_ON_STARTUP=true` e `APP_ENV != "local"`, com mensagem de erro explicando o risco.
> Referência: INIT-001

**REQ-003** — O cookie `mhc_access_token` DEVE ser definido com `HttpOnly=true` e `Secure=true` quando `APP_ENV != "local"`. O valor de `COOKIE_SECURE` DEVE ser derivado automaticamente de `APP_ENV` se não configurado explicitamente.
> Referência: INIT-001

**REQ-004** — Credenciais de demo (`superadmin@mhc.local / admin12345`) NÃO DEVEM aparecer na tela de login quando `APP_ENV != "local"`.
> Referência: INIT-001, INIT-009

**REQ-005** — O sistema DEVE validar que `PROXMOX_VERIFY_SSL=false` não está ativo em `APP_ENV=production`, emitindo pelo menos um warning estruturado no startup.
> Referência: INIT-001

### INIT-002 — Isolamento de Tenant Centralizado

**REQ-006** — DEVE existir uma classe base `TenantScopedRepository` (ou equivalente) que aplique automaticamente o filtro `tenant_id` em todas as queries de listagem e busca por ID, sem depender de código manual em cada endpoint.
> Referência: INIT-002, INIT-004

**REQ-007** — Qualquer tentativa de acessar um recurso de outro tenant (VM, serviço, fatura, ticket) DEVE retornar HTTP 403 ou 404, nunca expor o recurso.
> Referência: INIT-002

**REQ-008** — DEVE existir pelo menos um teste de integração que tente acessar recursos de tenant B com credenciais de tenant A e verifique que o acesso é negado em todos os endpoints principais (VMs, serviços, faturas, tickets).
> Referência: INIT-002, INIT-008

### INIT-003 — MFA/TOTP

**REQ-009** — O sistema DEVE oferecer endpoint para ativar MFA/TOTP (`POST /auth/totp/enable`), retornando QR code e secret para configuração no autenticador.
> Referência: INIT-003

**REQ-010** — O sistema DEVE oferecer endpoint para verificar e confirmar a ativação do TOTP (`POST /auth/totp/verify`), exigindo um código válido antes de marcar `totp_enabled=true`.
> Referência: INIT-003

**REQ-011** — O sistema DEVE oferecer endpoint para desativar MFA (`POST /auth/totp/disable`), exigindo senha atual e código TOTP válido.
> Referência: INIT-003

**REQ-012** — Quando `totp_enabled=true`, o login DEVE retornar um token intermediário (`mfa_required`) em vez do par access/refresh, e exigir um segundo passo com o código TOTP antes de emitir os tokens finais.
> Referência: INIT-003

### INIT-004 — Camada de Repositórios e Services

**REQ-013** — DEVE existir `ServiceRepository` com métodos `list_by_tenant`, `get_by_id_scoped`, e `create`, encapsulando todas as queries de `Service`.
> Referência: INIT-004

**REQ-014** — DEVE existir `VMRepository` com métodos `list_by_tenant`, `get_by_id_scoped`, encapsulando todas as queries de `VirtualMachine`.
> Referência: INIT-004

**REQ-015** — DEVE existir `ContractService` (ou `ServiceService`) que encapsule toda a lógica de `POST /services/contract`: criação de Service, Invoice, Job, seleção de node e disparo do Celery task.
> Referência: INIT-004

**REQ-016** — Os route handlers DEVEM ter no máximo ~20 linhas de lógica, delegando para repositories e services.
> Referência: INIT-004

### INIT-005 — Cancelamento de Serviço e VM

**REQ-017** — Quando um serviço é cancelado via `POST /vms/{vm_id}/cancel`, o sistema DEVE tentar parar e deletar a VM no Proxmox, registrando o resultado (sucesso ou falha) no `ServiceAction`.
> Referência: INIT-005

**REQ-018** — Se a deleção da VM no Proxmox falhar, o serviço DEVE ser marcado como `cancelled` no banco mesmo assim, e o erro DEVE ser registrado no log estruturado e no `ServiceAction.details` para ação manual posterior.
> Referência: INIT-005

**REQ-019** — O billing task `mark_overdue_and_suspend` DEVE verificar se a VM já está parada antes de tentar parar novamente, evitando erros desnecessários.
> Referência: INIT-005

### INIT-006 — Rate Limiting e Segurança de Endpoints

**REQ-020** — O endpoint `POST /auth/login` DEVE ter rate limiting de no máximo 10 tentativas por IP por minuto, retornando HTTP 429 quando excedido.
> Referência: INIT-006

**REQ-021** — O WebSocket VNC (`/vms/{vm_id}/vnc/ws`) DEVE validar e autenticar o usuário ANTES de chamar `websocket.accept()`, fechando a conexão com código 1008 (Policy Violation) se inválido.
> Referência: INIT-006

**REQ-022** — O parâmetro `port` no WebSocket VNC DEVE ser validado como inteiro no range 5900–5999. O parâmetro `vncticket` DEVE ser validado como string não-vazia com comprimento máximo de 512 caracteres.
> Referência: INIT-006

**REQ-023** — O role do usuário DEVE ser lido do payload JWT em `require_roles()`, eliminando a query extra ao banco em cada request protegido.
> Referência: INIT-006

### INIT-007 — UX Dashboard e Feedback

**REQ-024** — O dashboard do cliente (`/dashboard`) DEVE exibir: (a) status atual de cada VM com badge colorido, (b) próxima fatura com valor e data de vencimento, (c) alerta se houver fatura vencida.
> Referência: INIT-007

**REQ-025** — As ações de VM (desligar, reiniciar) DEVEM exibir um dialog de confirmação antes de executar.
> Referência: INIT-007

**REQ-026** — Após ações de VM, o feedback DEVE ser feito via atualização de estado local ou polling de status, sem `window.location.reload()`.
> Referência: INIT-007

**REQ-027** — O link "Admin" no menu do dashboard NÃO DEVE ser exibido para usuários com role `cliente`.
> Referência: INIT-007

**REQ-028** — Estados vazios em listas (VMs, faturas, tickets) DEVEM incluir CTA relevante (ex.: "Nenhuma VPS ainda. [Contratar seu primeiro plano →]").
> Referência: INIT-007

**REQ-029** — A página `/admin/infrastructure` DEVE exibir uso de CPU e RAM por node em formato legível (ex.: "2 GB / 32 GB", barra de progresso), consumindo o endpoint `/admin/proxmox/capacity` já existente.
> Referência: INIT-007

### INIT-008 — Qualidade e Testes

**REQ-030** — DEVE existir suite de testes cobrindo: suspensão automática por inadimplência, reativação após pagamento manual, e tentativa de suspender serviço já suspenso.
> Referência: INIT-008

**REQ-031** — DEVE existir suite de testes cobrindo: cancelamento de serviço com VM ativa, cancelamento com falha no Proxmox (mock de erro), e verificação de que o serviço é cancelado mesmo com falha no Proxmox.
> Referência: INIT-008

**REQ-032** — DEVE existir suite de testes de isolamento de tenant cobrindo todos os endpoints principais com tentativa de acesso cruzado.
> Referência: INIT-008

### INIT-009 — Limpeza e Padronização

**REQ-033** — O frontend DEVE usar exclusivamente `bun` como gerenciador de pacotes. O CI (`ci.yml`) DEVE ser atualizado para usar `bun` em vez de `npm ci`, e o `package-lock.json` DEVE ser removido do repositório para evitar divergências com o `bun.lock`.
> Referência: INIT-009

**REQ-034** — `paramiko` DEVE ser removido de `requirements.txt` (não é usado pela aplicação).
> Referência: INIT-009

**REQ-035** — `tsconfig.tsbuildinfo` DEVE ser adicionado ao `.gitignore` do frontend.
> Referência: INIT-009

---

## Requisitos Não Funcionais

**RNF-001 — Segurança:** Nenhum segredo (JWT_SECRET, PROXMOX_TOKEN_SECRET, senhas) deve aparecer em logs estruturados ou respostas de API. Tokens de autenticação não devem ser expostos em query strings de URLs logadas.

**RNF-002 — Isolamento de Tenant:** Nenhuma query de listagem ou busca por ID deve retornar dados de outro tenant. O isolamento deve ser garantido por código (repositório base), não por convenção.

**RNF-003 — Observabilidade:** Todas as operações críticas (login, provisão, cancelamento, billing, migração) devem gerar logs estruturados com `structlog` incluindo `tenant_id`, `user_id`, `action` e resultado.

**RNF-004 — Performance:** A adição da camada de repositórios não deve introduzir queries adicionais ao banco. A leitura de role do JWT (REQ-023) deve eliminar uma query por request.

**RNF-005 — Testabilidade:** Toda lógica de negócio extraída para services deve ser testável sem instanciar o servidor FastAPI (testes unitários puros com mocks de repositório).

**RNF-006 — Rollout sem downtime:** Todas as mudanças devem ser compatíveis com deploys incrementais. Nenhuma migração de banco deve ser destrutiva. Mudanças de API devem ser retrocompatíveis ou versionadas.

**RNF-007 — Manutenção incremental:** O trabalho deve ser executado em fases, com cada fase entregando valor independente e não quebrando o que já funciona.

---

## Fora de Escopo

Os itens abaixo **não** serão cobertos nesta rodada de trabalho:

- Integração com gateway de pagamento (Stripe, PagSeguro, etc.) — requer decisão de produto e contrato comercial
- Sistema de notificações por e-mail (a infraestrutura de `Notification` existe mas a implementação completa é uma feature separada)
- Reescrita de arquitetura (microserviços, event sourcing, etc.)
- Internacionalização (i18n) do frontend
- Backup e snapshot de VMs
- Portal de revenda white-label (customização por tenant)
- Métricas de uso em tempo real via WebSocket (além do status básico já existente)
- Integração com outros hypervisors além do Proxmox VE
