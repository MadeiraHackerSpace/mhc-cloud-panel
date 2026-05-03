# tasks.md - MHC Cloud Panel: Backlog de Remediacao

> Organizado por fase (0-3), alinhado ao design.md. Cada task tem ID unico, passos concretos e criterios de aceite verificaveis.

---

## FASE 0 - Hotfixes de Seguranca Imediata

---

### TASK-001 - Validar JWT_SECRET e SEED_ON_STARTUP no startup

**Quick win | Lacuna critica**

Objetivo:
- Impedir que a aplicacao suba em producao com JWT_SECRET=change-me ou SEED_ON_STARTUP=true. Resolve REQ-001, REQ-002. Referencia: INIT-001.

Impacta:
- backend/app/core/config.py
- backend/app/main.py
- backend/app/tests/test_startup.py (novo)

Dependencias:
- Nenhuma.

Passos:
1. Adicionar metodo validate_for_production(self) na classe Settings em config.py que levanta RuntimeError se jwt_secret == 'change-me' e app_env not in ('local', 'test').
2. Adicionar verificacao: se seed_on_startup == True e app_env not in ('local', 'test'), levantar RuntimeError com mensagem clara.
3. Adicionar log.warning se proxmox_verify_ssl == False e app_env == 'production'.
4. Chamar settings.validate_for_production() no inicio do lifespan em main.py, antes de seed_if_enabled().
5. Adicionar teste em test_startup.py que verifica que validate_for_production() levanta RuntimeError com jwt_secret='change-me' e app_env='production'.

Criterios de aceite:
- pytest passa com os novos testes.
- Subir com JWT_SECRET=change-me e APP_ENV=production resulta em RuntimeError com mensagem legivel.
- Subir com APP_ENV=local e JWT_SECRET=change-me funciona normalmente.

Testes:
- backend/app/tests/test_startup.py (novo).

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-002 - Garantir HttpOnly e Secure no cookie de autenticacao

**Quick win**

Objetivo:
- Prevenir roubo de token via XSS garantindo que mhc_access_token seja HttpOnly=true e Secure=true em producao. Resolve REQ-003. Referencia: INIT-001.

Impacta:
- frontend/app/api/auth/login/route.ts
- .env.example

Dependencias:
- Nenhuma.

Passos:
1. Ler frontend/app/api/auth/login/route.ts e verificar como o cookie e definido atualmente.
2. Garantir que o cookie seja definido com httpOnly: true, secure: process.env.COOKIE_SECURE !== 'false', sameSite: 'lax', path: '/'.
3. Fazer o mesmo para qualquer rota que defina mhc_refresh_token.
4. Atualizar .env.example para documentar que COOKIE_SECURE=false e apenas para desenvolvimento local.
5. Adicionar NEXT_PUBLIC_APP_ENV ao .env.example.

Criterios de aceite:
- Em ambiente com COOKIE_SECURE=true, o cookie tem flag Secure na resposta HTTP.
- Em ambiente com COOKIE_SECURE=false, o cookie nao tem flag Secure.
- Cookie sempre tem HttpOnly=true.

Testes:
- Verificacao via inspecao de headers de resposta.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-003 - Remover credenciais demo da tela de login em producao

**Quick win**

Objetivo:
- Impedir que superadmin@mhc.local / admin12345 apareca na tela de login fora do ambiente local. Resolve REQ-004. Referencia: INIT-001, INIT-009.

Impacta:
- frontend/app/(auth)/login/login-form.tsx
- frontend/.env.example (adicionar NEXT_PUBLIC_APP_ENV)

Dependencias:
- Nenhuma.

Passos:
1. Adicionar variavel NEXT_PUBLIC_APP_ENV ao .env.example com valor local.
2. Em login-form.tsx, envolver o bloco de credenciais demo em {process.env.NEXT_PUBLIC_APP_ENV === 'local' && (...)}.
3. Verificar que o build de producao nao inclui o texto de credenciais quando NEXT_PUBLIC_APP_ENV !== 'local'.

Criterios de aceite:
- Com NEXT_PUBLIC_APP_ENV=local, as credenciais aparecem na tela de login.
- Com NEXT_PUBLIC_APP_ENV=production (ou ausente), as credenciais nao aparecem.
- bun run typecheck e bun run lint passam.

Testes:
- Verificacao de build com variavel de ambiente diferente.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-004 - Rate limiting no endpoint de login

**Quick win**

Objetivo:
- Prevenir brute force no endpoint POST /auth/login. Resolve REQ-020. Referencia: INIT-006.

Impacta:
- backend/requirements.txt
- backend/app/main.py
- backend/app/api/v1/routes/auth.py

Dependencias:
- Nenhuma.

Passos:
1. Adicionar slowapi==0.1.9 ao requirements.txt.
2. Em main.py, instanciar Limiter(key_func=get_remote_address), adicionar ao app.state.limiter e registrar o handler de RateLimitExceeded.
3. Em auth.py, decorar o endpoint login com @limiter.limit('10/minute').
4. Adicionar teste que faz 11 requisicoes de login em sequencia e verifica que a 11a retorna HTTP 429.

Criterios de aceite:
- 10 tentativas de login em menos de 1 minuto sao aceitas.
- A 11a tentativa retorna HTTP 429 com mensagem clara.
- Testes existentes de login continuam passando.

Testes:
- backend/app/tests/test_auth.py - adicionar teste de rate limit.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-005 - Corrigir autenticacao no WebSocket VNC (auth antes de accept)

**Lacuna critica de seguranca**

Objetivo:
- Validar token e autorizacao ANTES de websocket.accept() no endpoint VNC. Validar parametros port e vncticket. Resolve REQ-021, REQ-022. Referencia: INIT-006.

Impacta:
- backend/app/api/v1/routes/vms.py (funcao vnc_websocket_proxy)

Dependencias:
- Nenhuma.

Passos:
1. Mover a logica de extracao de requested_protocols para antes do bloco de autenticacao.
2. Adicionar validacao de port: se not (5900 <= port <= 5999), chamar await websocket.close(code=1008) e retornar.
3. Adicionar validacao de vncticket: se vazio ou len(vncticket) > 512, fechar com codigo 1008.
4. Instanciar db e chamar _get_current_user_ws e _get_vm_scoped ANTES de websocket.accept().
5. Se qualquer excecao (UnauthorizedError, ForbiddenError, NotFoundError) for levantada, chamar await websocket.close(code=1008), fechar db e retornar.
6. Somente apos autenticacao bem-sucedida, chamar await websocket.accept(...).
7. Adicionar teste que tenta conectar ao WebSocket com token invalido e verifica que a conexao e fechada com codigo 1008.

Criterios de aceite:
- Conexao com token invalido e fechada com codigo 1008 antes de ser aceita.
- Conexao com port=80 (fora do range) e fechada com codigo 1008.
- Conexao com vncticket vazio e fechada com codigo 1008.
- Conexao legitima continua funcionando.

Testes:
- backend/app/tests/test_vnc_ws.py (novo).

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-006 - Ler role do JWT em require_roles (eliminar query extra ao banco)

**Quick win**

Objetivo:
- Eliminar a query ao banco em cada request protegido por require_roles(), lendo o role diretamente do JWT payload. Resolve REQ-023. Referencia: INIT-006.

Impacta:
- backend/app/api/deps.py

Dependencias:
- Nenhuma.

Passos:
1. Modificar require_roles() para receber creds via Depends(bearer_scheme) em vez de fazer query ao banco.
2. Decodificar o token e ler payload.get('role').
3. Comparar com allowed e levantar ForbiddenError se nao estiver na lista.
4. Remover a query db.scalar(select(Role).where(Role.id == user.role_id)) do _dep.
5. Verificar que todos os testes existentes de endpoints protegidos continuam passando.

Criterios de aceite:
- require_roles('super_admin') funciona sem query ao banco.
- Usuario com role incorreto recebe HTTP 403.
- Todos os testes existentes passam.

Testes:
- Testes existentes em test_auth.py, test_admin_proxmox.py, test_contract_flow.py devem continuar passando.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

## FASE 1 - Refactors Estruturais Seguros

---

### TASK-007 - Criar TenantScopedRepository base

**Lacuna critica de arquitetura**

Objetivo:
- Criar a classe base que garante isolamento de tenant por codigo. Resolve REQ-006. Referencia: INIT-002, INIT-004.

Impacta:
- backend/app/repositories/base.py (novo)
- backend/app/repositories/__init__.py

Dependencias:
- Nenhuma.

Passos:
1. Criar backend/app/repositories/base.py com classe generica TenantScopedRepository[T].
2. O construtor recebe db: Session e tenant_id: uuid.UUID | None (None = super_admin, sem filtro).
3. Implementar metodo _apply_tenant_filter(q, model) que adiciona .where(model.tenant_id == self.tenant_id) quando tenant_id is not None.
4. Implementar _get_by_id(model, id) que aplica o filtro de tenant automaticamente.
5. Implementar _list(model, limit, offset) que aplica filtro de tenant e retorna items + total.
6. Escrever testes unitarios para TenantScopedRepository com mocks de Session.

Criterios de aceite:
- TenantScopedRepository com tenant_id=uuid_A nunca retorna registros com tenant_id=uuid_B.
- TenantScopedRepository com tenant_id=None retorna todos os registros.
- Testes unitarios passam.

Testes:
- backend/app/tests/test_repositories.py (novo).

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-008 - Implementar ServiceRepository e VMRepository

**Pode rodar em paralelo com TASK-009**

Objetivo:
- Encapsular queries de Service e VirtualMachine em repositorios concretos. Resolve REQ-013, REQ-014. Referencia: INIT-004.

Impacta:
- backend/app/repositories/service_repository.py (novo)
- backend/app/repositories/vm_repository.py (novo)

Dependencias:
- TASK-007.

Passos:
1. Criar ServiceRepository(TenantScopedRepository[Service]) com metodos: list(limit, offset), get_by_id(id), create(...), update_status(id, status).
2. Criar VMRepository(TenantScopedRepository[VirtualMachine]) com metodos: list(limit, offset, include_deleted), get_by_id(id), get_by_service_id(service_id), create(...).
3. Adicionar testes de integracao para cada repositorio usando o banco real.
4. Verificar que get_by_id retorna None quando o ID pertence a outro tenant.

Criterios de aceite:
- ServiceRepository(db, tenant_id=tenant_A).get_by_id(service_id_de_tenant_B) retorna None.
- VMRepository(db, tenant_id=tenant_A).list() nao retorna VMs de tenant_B.
- Testes de integracao passam.

Testes:
- backend/app/tests/test_repositories.py - adicionar testes de integracao com dois tenants.

Risco: baixo
Esforco: medio
Pode ser executada por agente sem revisao humana? sim

---

### TASK-009 - Implementar InvoiceRepository e TicketRepository

**Pode rodar em paralelo com TASK-008**

Objetivo:
- Encapsular queries de Invoice e Ticket em repositorios concretos. Referencia: INIT-004.

Impacta:
- backend/app/repositories/invoice_repository.py (novo)
- backend/app/repositories/ticket_repository.py (novo)

Dependencias:
- TASK-007.

Passos:
1. Criar InvoiceRepository(TenantScopedRepository[Invoice]) com metodos: list(limit, offset, status_filter), get_by_id(id), create(...), mark_paid(id, paid_at).
2. Criar TicketRepository(TenantScopedRepository[Ticket]) com metodos: list(limit, offset), get_by_id(id), create(...).
3. Adicionar testes de integracao para cada repositorio.

Criterios de aceite:
- Isolamento de tenant verificado em testes para ambos os repositorios.
- Testes passam.

Testes:
- backend/app/tests/test_repositories.py - adicionar secoes para Invoice e Ticket.

Risco: baixo
Esforco: medio
Pode ser executada por agente sem revisao humana? sim

---

### TASK-010 - Extrair ContractService de services.py

**Exige revisao humana antes do merge**

Objetivo:
- Mover a logica de ~60 linhas do endpoint contract_plan para ContractService. Resolve REQ-015, REQ-016. Referencia: INIT-004.

Impacta:
- backend/app/services/contract_service.py (novo)
- backend/app/api/v1/routes/services.py

Dependencias:
- TASK-008, TASK-009.

Passos:
1. Criar backend/app/services/contract_service.py com classe ContractService.
2. Mover toda a logica de criacao de Service, Invoice, Job, selecao de node e disparo de provision_vm.delay() para ContractService.contract_plan(...).
3. O metodo deve retornar tuple[Service, Invoice, Job].
4. Atualizar o endpoint contract_plan em services.py para instanciar ContractService e chamar o metodo.
5. Criar Depends para injetar ProxmoxService: def get_proxmox_service() -> ProxmoxService.
6. Verificar que todos os testes de test_contract_flow.py continuam passando.
7. Adicionar testes unitarios para ContractService com mocks.

Criterios de aceite:
- O endpoint POST /services/contract continua funcionando com o mesmo contrato de API.
- test_contract_flow.py passa sem modificacao.
- O route handler tem no maximo 20 linhas.

Testes:
- backend/app/tests/test_contract_service.py (novo).
- backend/app/tests/test_contract_flow.py - deve continuar passando.

Risco: medio
Esforco: medio
Pode ser executada por agente sem revisao humana? nao

---

### TASK-011 - Testes de isolamento de tenant (IDOR prevention)

**Lacuna critica de seguranca**

Objetivo:
- Garantir por testes que nenhum endpoint retorna dados de outro tenant. Resolve REQ-007, REQ-008. Referencia: INIT-002, INIT-008.

Impacta:
- backend/app/tests/test_tenant_isolation.py (novo)
- backend/app/tests/conftest.py (adicionar fixture de segundo tenant)

Dependencias:
- TASK-007, TASK-008, TASK-009.

Passos:
1. Adicionar fixture client_tenant_b ao conftest.py que cria um segundo tenant com usuario e dados proprios.
2. Criar test_tenant_isolation.py com testes para cada endpoint principal:
   - GET /vms/{vm_id_de_tenant_B} com token de tenant_A -> deve retornar 403 ou 404.
   - POST /vms/{vm_id_de_tenant_B}/start com token de tenant_A -> deve retornar 403 ou 404.
   - GET /services/{service_id_de_tenant_B} com token de tenant_A -> deve retornar 403 ou 404.
   - GET /invoices/{invoice_id_de_tenant_B} com token de tenant_A -> deve retornar 403 ou 404.
   - GET /tickets/{ticket_id_de_tenant_B} com token de tenant_A -> deve retornar 403 ou 404.
3. Verificar que GET /vms com token de tenant_A nao retorna VMs de tenant_B na lista.

Criterios de aceite:
- Todos os testes de isolamento passam.
- Nenhum endpoint retorna dados de outro tenant.

Testes:
- backend/app/tests/test_tenant_isolation.py (novo).

Risco: baixo
Esforco: medio
Pode ser executada por agente sem revisao humana? sim

---

### TASK-012 - Corrigir cancel_service para deletar VM no Proxmox

**Lacuna critica de funcionalidade**

Objetivo:
- Quando um servico e cancelado, parar e deletar a VM no Proxmox. Falhas no Proxmox nao devem impedir o cancelamento no banco. Resolve REQ-017, REQ-018. Referencia: INIT-005.

Impacta:
- backend/app/api/v1/routes/vms.py (funcao cancel_service)

Dependencias:
- Nenhuma.

Passos:
1. No endpoint cancel_service, apos validar a VM e o servico, adicionar bloco try/except para:
   a. Chamar proxmox.stop_vm() - ignorar erro se VM ja estiver parada.
   b. Chamar proxmox.delete_vm().
   c. Marcar vm.status = VMStatus.deleted.
2. Se qualquer excecao ocorrer no bloco Proxmox, logar com log.error e continuar.
3. Independente do resultado Proxmox, marcar service.status = ServiceStatus.cancelled.
4. Registrar resultado no ServiceAction.details: {'proxmox_deleted': True/False, 'proxmox_error': str(exc) or None}.
5. Injetar ProxmoxService via Depends(get_proxmox_service).
6. Adicionar testes: cancelamento com Proxmox funcionando, cancelamento com Proxmox falhando.

Criterios de aceite:
- Apos cancelamento bem-sucedido, a VM nao existe mais no Proxmox.
- Se o Proxmox falhar, o servico ainda e marcado como cancelled no banco.
- ServiceAction registra o resultado correto em ambos os casos.

Testes:
- backend/app/tests/test_cancel_service.py (novo).

Risco: medio
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-013 - Implementar MFA/TOTP (ativacao, verificacao, desativacao)

**Lacuna critica | Exige revisao humana antes do merge**

Objetivo:
- Implementar o fluxo completo de MFA/TOTP que ja esta declarado no modelo User. Resolve REQ-009, REQ-010, REQ-011, REQ-012. Referencia: INIT-003.

Impacta:
- backend/requirements.txt (adicionar pyotp==2.9.0)
- backend/app/api/v1/routes/auth.py
- backend/app/services/auth_service.py
- backend/app/schemas/auth.py
- frontend/app/(auth)/login/login-form.tsx

Dependencias:
- Nenhuma (pode ser feita em paralelo com TASK-010).

Passos:
1. Adicionar pyotp==2.9.0 ao requirements.txt.
2. Criar endpoint POST /auth/totp/enable: gera totp_secret com pyotp.random_base32(), salva no user.totp_secret, retorna otpauth_uri e secret.
3. Criar endpoint POST /auth/totp/verify: recebe code, verifica com pyotp.TOTP(user.totp_secret).verify(code), se valido marca user.totp_enabled=True.
4. Criar endpoint POST /auth/totp/disable: recebe password e code, verifica senha e codigo TOTP, marca totp_enabled=False e limpa totp_secret.
5. Modificar AuthService.login(): se user.totp_enabled, retornar {'mfa_required': true, 'mfa_token': '<jwt de 5 min com type=mfa_pending>'}.
6. Criar endpoint POST /auth/totp/login: recebe mfa_token e code, valida e emite par access/refresh final.
7. Atualizar login-form.tsx para lidar com resposta mfa_required=true.
8. Adicionar testes para todo o fluxo.

Criterios de aceite:
- Usuario sem MFA faz login normalmente.
- Usuario com MFA ativo recebe mfa_required=true no login.
- Codigo TOTP invalido retorna HTTP 401.
- Desativacao exige senha + codigo TOTP valido.

Testes:
- backend/app/tests/test_mfa.py (novo).

Risco: medio
Esforco: medio
Pode ser executada por agente sem revisao humana? nao

---

## FASE 2 - UX e Produto

---

### TASK-014 - Dashboard do cliente com KPIs reais

**Pode rodar em paralelo com TASK-015**

Objetivo:
- Substituir os contadores sem contexto por KPIs uteis: status de VMs com badge colorido, proxima fatura com valor e data, alerta de fatura vencida. Resolve REQ-024. Referencia: INIT-007.

Impacta:
- frontend/app/dashboard/page.tsx
- frontend/lib/types/api.ts

Dependencias:
- Nenhuma (usa endpoints ja existentes).

Passos:
1. Adicionar fetch de faturas ao DashboardPage: backendFetch('/api/v1/invoices?limit=5&offset=0').
2. Calcular a proxima fatura em aberto (status=open, due_date mais proxima).
3. Adicionar card 'Proxima fatura' com: numero, valor formatado em BRL, data de vencimento, badge de status.
4. Adicionar alerta visual se houver fatura com status=overdue.
5. Na lista de VMs, adicionar badge colorido: verde para running, vermelho para error, cinza para stopped, amarelo para provisioning.
6. Substituir o card 'Status' (texto fixo inutil) pelo card de fatura.

Criterios de aceite:
- Dashboard exibe proxima fatura com valor e data.
- VMs tem badge colorido de status.
- Fatura vencida exibe alerta visual.
- Build limpo sem erros de tipo.

Testes:
- bun run typecheck e bun run build passam.

Risco: baixo
Esforco: medio
Pode ser executada por agente sem revisao humana? sim

---

### TASK-015 - Feedback de acoes de VM sem location.reload()

**Pode rodar em paralelo com TASK-014**

Objetivo:
- Substituir window.location.reload() por atualizacao de estado local com polling de status. Adicionar confirmacao antes de acoes destrutivas. Resolve REQ-025, REQ-026. Referencia: INIT-007.

Impacta:
- frontend/components/vm-actions.tsx

Dependencias:
- Nenhuma.

Passos:
1. Adicionar prop currentStatus: string ao componente VMActionButtons.
2. Adicionar estado local vmStatus inicializado com currentStatus.
3. Para acoes stop e reboot, exibir window.confirm() antes de executar.
4. Apos executar a acao, iniciar polling: a cada 2 segundos, chamar GET /api/vms/{vmId}/status por ate 20 segundos.
5. Quando o status mudar, atualizar vmStatus e parar o polling.
6. Se o polling expirar sem mudanca, exibir mensagem informativa.
7. Remover window.location.reload().
8. Exibir erros da API usando data?.error?.message em vez de 'Falha' generico.

Criterios de aceite:
- Nenhum window.location.reload() no componente.
- Acoes stop e reboot pedem confirmacao.
- Status da VM atualiza visualmente apos a acao sem reload de pagina.
- bun run typecheck passa.

Testes:
- bun run typecheck e bun run lint passam.

Risco: baixo
Esforco: medio
Pode ser executada por agente sem revisao humana? sim

---

### TASK-016 - Ocultar link Admin para usuarios sem permissao

**Quick win**

Objetivo:
- O link 'Admin' no menu do dashboard nao deve aparecer para usuarios com role cliente. Resolve REQ-027. Referencia: INIT-007.

Impacta:
- frontend/app/dashboard/layout.tsx
- frontend/app/api/auth/login/route.ts

Dependencias:
- TASK-002.

Passos:
1. Na rota de login do Next.js, apos receber os tokens do backend, decodificar o JWT payload para extrair o role.
2. Definir um cookie nao-sensivel mhc_role com o valor do role.
3. Em dashboard/layout.tsx, ler o cookie mhc_role via cookies() e filtrar o item 'Admin' do array nav quando role === 'cliente'.
4. Garantir que a protecao real continua sendo feita pelo middleware e pelo backend.

Criterios de aceite:
- Usuario com role cliente nao ve o link 'Admin' no menu.
- Usuario com role super_admin ou operador ve o link 'Admin'.
- Mesmo sem o link, a rota /admin continua protegida pelo middleware.
- bun run typecheck passa.

Testes:
- Verificacao manual ou teste de snapshot do layout.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-017 - Estados vazios com CTAs acionaveis

**Quick win**

Objetivo:
- Substituir textos de estado vazio simples por mensagens com CTA relevante. Resolve REQ-028. Referencia: INIT-007.

Impacta:
- frontend/app/dashboard/page.tsx
- frontend/app/dashboard/vps/page.tsx (se existir)
- frontend/app/dashboard/invoices/page.tsx (se existir)
- frontend/app/dashboard/tickets/page.tsx (se existir)

Dependencias:
- Nenhuma.

Passos:
1. Identificar todos os estados vazios com texto simples.
2. Substituir por componente com texto descritivo e botao/link de CTA:
   - VMs vazias: 'Nenhuma VPS ainda. [Contratar seu primeiro plano]' (link para /dashboard/plans).
   - Tickets vazios: 'Nenhum ticket aberto. [Abrir ticket de suporte]'.
3. Garantir que os CTAs levam para paginas existentes.

Criterios de aceite:
- Nenhum estado vazio exibe apenas texto simples sem contexto.
- CTAs levam para paginas funcionais.
- bun run build passa.

Testes:
- bun run build passa.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-018 - Pagina de infraestrutura com capacidade do cluster

**Pode rodar em paralelo com outras tasks de Fase 2**

Objetivo:
- Substituir a exibicao de bytes brutos na pagina de infraestrutura por barras de uso de CPU e RAM. Resolve REQ-029. Referencia: INIT-007.

Impacta:
- frontend/app/admin/infrastructure/page.tsx

Dependencias:
- Nenhuma (endpoint ja existe no backend).

Passos:
1. Alterar o fetch para usar /api/v1/admin/proxmox/capacity em vez de /api/v1/admin/proxmox/nodes.
2. Para cada node, exibir: nome, status, barra de progresso de RAM (X GB / Y GB), barra de progresso de CPU (%).
3. Implementar barras de progresso com Tailwind puro.
4. Formatar bytes em GB com funcao utilitaria formatBytes(bytes: number): string.

Criterios de aceite:
- Pagina exibe uso de RAM e CPU por node em formato legivel.
- Nenhum valor em bytes brutos visivel ao usuario.
- bun run typecheck e bun run build passam.

Testes:
- bun run typecheck e bun run build passam.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

## FASE 3 - Endurecimento Operacional

---

### TASK-019 - Testes de billing (suspensao e reativacao)

**Pode rodar em paralelo com TASK-020**

Objetivo:
- Cobrir os fluxos criticos de billing com testes de integracao. Resolve REQ-030. Referencia: INIT-008.

Impacta:
- backend/app/tests/test_billing.py (novo)

Dependencias:
- TASK-012.

Passos:
1. Criar test_billing.py com fixture que cria servico ativo com fatura vencida.
2. Testar mark_overdue_and_suspend(): verificar que fatura muda para overdue, servico muda para suspended, stop_vm e chamado no mock.
3. Testar que servico ja suspenso nao e suspenso novamente (idempotencia).
4. Testar reativacao: chamar POST /invoices/{id}/mark-paid e verificar que servico volta para active.
5. Testar que servico sem VM associada e suspenso sem erro.

Criterios de aceite:
- Todos os testes passam.
- mark_overdue_and_suspend() e idempotente para servicos ja suspensos.
- Reativacao via mark-paid funciona corretamente.

Testes:
- backend/app/tests/test_billing.py (novo).

Risco: baixo
Esforco: medio
Pode ser executada por agente sem revisao humana? sim

---

### TASK-020 - Testes de cancelamento de servico/VM

**Pode rodar em paralelo com TASK-019**

Objetivo:
- Cobrir os dois cenarios de cancelamento: Proxmox funcionando e Proxmox com erro. Resolve REQ-031. Referencia: INIT-008.

Impacta:
- backend/app/tests/test_cancel_service.py (novo ou expandir)

Dependencias:
- TASK-012.

Passos:
1. Cenario 1 - Proxmox OK: mock de delete_vm que retorna sem erro. Verificar que VM fica com status=deleted, servico com status=cancelled, ServiceAction.success=True.
2. Cenario 2 - Proxmox com erro: mock de delete_vm que levanta excecao. Verificar que servico ainda fica com status=cancelled, ServiceAction.success=False.
3. Cenario 3 - Cancelamento sem confirmacao (confirm=False): verificar que retorna HTTP 403.

Criterios de aceite:
- Todos os tres cenarios passam.
- Falha no Proxmox nao impede cancelamento no banco.

Testes:
- backend/app/tests/test_cancel_service.py.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-021 - Corrigir CI para usar bun em vez de npm

**Quick win**

Objetivo:
- Alinhar o CI com o ambiente de producao (bun), eliminando a divergencia entre npm ci no CI e bun install no Dockerfile. Resolve REQ-033. Referencia: INIT-009.

Impacta:
- .github/workflows/ci.yml
- frontend/package-lock.json (remover do repositorio)
- .gitignore (adicionar package-lock.json)

Dependencias:
- Nenhuma.

Passos:
1. No job frontend do ci.yml, substituir actions/setup-node por oven/setup-bun@v2.
2. Remover cache: npm e cache-dependency-path: frontend/package-lock.json.
3. Adicionar cache de bun: cache: true na action setup-bun.
4. Substituir npm ci por bun install --frozen-lockfile.
5. Substituir npm run lint, npm run typecheck, npm run build por bun run lint, bun run typecheck, bun run build.
6. Remover frontend/package-lock.json do repositorio (git rm frontend/package-lock.json).
7. Adicionar package-lock.json ao .gitignore do frontend.

Criterios de aceite:
- CI passa usando bun.
- package-lock.json nao esta mais no repositorio.
- bun.lock esta commitado e e a unica fonte de verdade de dependencias.

Testes:
- CI verde apos o push.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-022 - Remover paramiko de requirements.txt

**Quick win**

Objetivo:
- Remover dependencia desnecessaria de producao. Resolve REQ-034. Referencia: INIT-009.

Impacta:
- backend/requirements.txt

Dependencias:
- Nenhuma.

Passos:
1. Verificar que paramiko nao e importado em nenhum arquivo em backend/app/.
2. Remover a linha paramiko==3.5.1 de requirements.txt.
3. Se necessario para scripts, criar requirements-dev.txt.
4. Verificar que pytest continua passando.

Criterios de aceite:
- paramiko nao esta em requirements.txt.
- Todos os testes passam.

Testes:
- pytest passa apos a remocao.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-023 - Remover tsconfig.tsbuildinfo do git

**Quick win**

Objetivo:
- Arquivo gerado automaticamente pelo TypeScript nao deve estar versionado. Resolve REQ-035. Referencia: INIT-009.

Impacta:
- frontend/.gitignore
- frontend/tsconfig.tsbuildinfo (remover do tracking)

Dependencias:
- Nenhuma.

Passos:
1. Adicionar tsconfig.tsbuildinfo ao .gitignore do frontend.
2. Executar git rm --cached frontend/tsconfig.tsbuildinfo para remover do tracking.
3. Verificar que o arquivo nao aparece mais em git status apos o commit.

Criterios de aceite:
- tsconfig.tsbuildinfo nao esta mais rastreado pelo git.
- .gitignore contem a entrada.

Testes:
- git status nao mostra o arquivo apos commit.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

### TASK-024 - Substituir dados demo inline em backend.ts

**Exige revisao humana antes do merge**

Objetivo:
- Remover os ~120 linhas de dados mockados hardcoded em frontend/lib/api/backend.ts. Referencia: INIT-009.

Impacta:
- frontend/lib/api/backend.ts
- frontend/lib/api/demo-data.ts (novo, se mantiver modo demo)

Dependencias:
- Nenhuma.

Passos:
1. Avaliar se o modo demo (mhc_demo cookie ou MHC_FORCE_DEMO=true) ainda e necessario.
2. Se sim: extrair os dados mockados para frontend/lib/api/demo-data.ts separado.
3. Se nao: remover completamente o bloco demoResponse e a logica de deteccao de demo.
4. Garantir que bun run typecheck e bun run build passam.

Criterios de aceite:
- backend.ts nao tem mais dados mockados inline.
- bun run build passa.

Testes:
- bun run typecheck e bun run build passam.

Risco: medio
Esforco: baixo
Pode ser executada por agente sem revisao humana? nao

---

### TASK-025 - Documentar variaveis de ambiente obrigatorias

**Quick win**

Objetivo:
- Garantir que operadores saibam quais variaveis sao obrigatorias em producao. Referencia: INIT-001, INIT-009.

Impacta:
- .env.example
- README.md

Dependencias:
- TASK-001.

Passos:
1. Adicionar comentarios no .env.example marcando variaveis como OBRIGATORIO EM PRODUCAO ou Apenas para desenvolvimento local.
2. Marcar: JWT_SECRET, PROXMOX_TOKEN_SECRET, POSTGRES_PASSWORD, COOKIE_SECURE, SEED_ON_STARTUP, PROXMOX_VERIFY_SSL.
3. Adicionar secao 'Configuracao para Producao' no README.md.
4. Adicionar NEXT_PUBLIC_APP_ENV ao .env.example com documentacao.

Criterios de aceite:
- .env.example tem comentarios claros sobre variaveis obrigatorias.
- README tem secao de configuracao de producao.

Testes:
- Revisao manual.

Risco: baixo
Esforco: baixo
Pode ser executada por agente sem revisao humana? sim

---

## Resumo por Fase

| Fase | Tasks | Foco | Paralelismo |
|---|---|---|---|
| 0 | TASK-001 a TASK-006 | Seguranca imediata | TASK-002 a TASK-006 podem rodar em paralelo |
| 1 | TASK-007 a TASK-013 | Arquitetura + MFA + Cancelamento | TASK-008 e TASK-009 em paralelo; TASK-013 em paralelo com TASK-010 |
| 2 | TASK-014 a TASK-018 | UX e produto | Todas podem rodar em paralelo |
| 3 | TASK-019 a TASK-025 | Testes, limpeza, docs | TASK-019 e TASK-020 em paralelo; demais independentes |

## Tasks que exigem revisao humana antes do merge

- TASK-010 - ContractService (refactor de logica critica de negocio)
- TASK-013 - MFA/TOTP (mudanca de fluxo de autenticacao)
- TASK-024 - Remocao de dados demo (decisao de produto sobre modo demo)

