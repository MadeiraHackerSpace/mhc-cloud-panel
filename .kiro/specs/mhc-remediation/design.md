# design.md — MHC Cloud Panel: Plano de Remediação

## Visão Arquitetural

### Estratégia geral: remediação incremental, não reescrita

O projeto tem uma base sólida — o modelo de domínio está bem definido, o adapter do Proxmox é testável via Protocol, e o CI já cobre lint/typecheck/build. A estratégia é **corrigir sem quebrar**: cada fase entrega valor independente e é retrocompatível com a fase anterior.

A ordem de execução reflete o risco:

1. **Fase 0 — Hotfixes de segurança imediata:** Mudanças de baixo risco e alto impacto que podem ser feitas em horas. Nenhuma mudança de API, nenhuma migração de banco.
2. **Fase 1 — Refactors estruturais seguros:** Introdução de repositórios e services sem alterar contratos de API. Os endpoints continuam funcionando, mas a lógica migra para camadas testáveis.
3. **Fase 2 — UX e produto:** Melhorias no frontend que não dependem de mudanças de backend (exceto REQ-023 que já estará pronto na Fase 1).
4. **Fase 3 — Endurecimento operacional:** Testes adicionais, limpeza de dependências, observabilidade, documentação.

---

## Decisões Técnicas por Iniciativa

### INIT-001 — Segurança de Segredos e Startup

**Problema atual:** `config.py` define `jwt_secret: str = "change-me"` sem nenhuma validação. O `.env.example` tem `COOKIE_SECURE=false` e `SEED_ON_STARTUP=true`. Não há nenhuma barreira que impeça subir em produção com esses valores.

**Decisão proposta:** Adicionar um método `validate_for_production()` na classe `Settings` que é chamado no `lifespan` do FastAPI, antes de `seed_if_enabled()`. O método verifica:
- `jwt_secret != "change-me"` se `app_env not in ("local", "test")`
- `seed_on_startup == False` se `app_env not in ("local", "test")`
- Emite `log.warning` se `proxmox_verify_ssl == False` e `app_env == "production"`

```python
# app/core/config.py
def validate_for_production(self) -> None:
    if self.app_env not in ("local", "test"):
        if self.jwt_secret == "change-me":
            raise RuntimeError(
                "JWT_SECRET must be changed before running outside local environment. "
                "Set a strong random value in your .env file."
            )
        if self.seed_on_startup:
            raise RuntimeError(
                "SEED_ON_STARTUP=true is not allowed outside local environment. "
                "This would create users with default passwords."
            )
```

**Impacto esperado:** Elimina o risco de produção com segredo padrão sem nenhuma mudança de API ou banco.

**Riscos / trade-offs:** Nenhum. É uma validação de startup que falha rápido com mensagem clara.

---

**Problema atual (cookies):** A rota Next.js `/api/auth/login/route.ts` define o cookie `mhc_access_token`. Não está claro se `HttpOnly` e `Secure` estão sendo definidos corretamente.

**Decisão proposta:** Garantir que o cookie seja definido com:
```typescript
cookies().set("mhc_access_token", access_token, {
  httpOnly: true,
  secure: process.env.COOKIE_SECURE !== "false",
  sameSite: "lax",
  path: "/",
  maxAge: 60 * 15, // 15 min, alinhado com JWT_ACCESS_TOKEN_EXPIRES_MINUTES
});
```

**Impacto esperado:** Previne roubo de token via XSS.

---

**Problema atual (credenciais demo):** `login-form.tsx` exibe `superadmin@mhc.local / admin12345` hardcoded.

**Decisão proposta:** Condicionar ao `NEXT_PUBLIC_APP_ENV`:
```tsx
{process.env.NEXT_PUBLIC_APP_ENV === "local" && (
  <div className="mt-6 text-xs text-muted">
    Demo: superadmin@mhc.local / admin12345
  </div>
)}
```

---

### INIT-002 — Isolamento de Tenant Centralizado

**Problema atual:** O filtro de tenant é aplicado manualmente em cada endpoint com `if current.tenant_id is not None: q = q.where(...)`. Se um desenvolvedor esquecer em um novo endpoint, dados vazam entre tenants. Não há teste que garanta isso.

**Decisão proposta:** Criar uma classe base `TenantScopedRepository` em `backend/app/repositories/base.py`:

```python
class TenantScopedRepository(Generic[T]):
    def __init__(self, db: Session, *, tenant_id: uuid.UUID | None):
        self.db = db
        self.tenant_id = tenant_id  # None = super_admin (sem filtro)

    def _apply_tenant_filter(self, q: Select, model: type[T]) -> Select:
        if self.tenant_id is not None:
            q = q.where(model.tenant_id == self.tenant_id)
        return q
```

Todos os repositórios concretos herdam de `TenantScopedRepository` e chamam `_apply_tenant_filter` automaticamente. O `tenant_id` é injetado no repositório a partir do usuário autenticado, não passado em cada chamada de método.

**Impacto esperado:** Isolamento garantido por código. Um desenvolvedor que esqueça de filtrar ainda assim terá o filtro aplicado pelo repositório base.

**Riscos / trade-offs:** Requer refatoração dos endpoints existentes para usar os repositórios. A migração pode ser feita endpoint por endpoint sem quebrar nada.

---

### INIT-003 — MFA/TOTP

**Problema atual:** O modelo `User` tem `totp_enabled` e `totp_secret` mas não há nenhum endpoint de MFA. A funcionalidade está declarada mas não implementada.

**Decisão proposta:** Usar a biblioteca `pyotp` (adicionar ao `requirements.txt`) para gerar e verificar códigos TOTP. O fluxo é:

1. `POST /auth/totp/enable` — gera `totp_secret`, salva criptografado no banco, retorna QR code URI
2. `POST /auth/totp/verify` — verifica código, marca `totp_enabled=true`
3. `POST /auth/totp/disable` — exige senha + código TOTP, marca `totp_enabled=false`, limpa `totp_secret`
4. Modificar `AuthService.login()` — se `totp_enabled=true`, retornar token intermediário `{"mfa_required": true, "mfa_token": "<short_lived_jwt>"}` em vez do par access/refresh
5. `POST /auth/totp/login` — recebe `mfa_token` + código TOTP, emite par access/refresh final

O `totp_secret` deve ser armazenado criptografado no banco (usando `cryptography.fernet` ou similar), não em plaintext.

**Impacto esperado:** Implementa a funcionalidade que já está declarada no modelo. Crítico para uso comercial.

**Riscos / trade-offs:** Adiciona uma dependência (`pyotp`). O fluxo de login muda para usuários com MFA ativo — o frontend precisa ser atualizado para lidar com `mfa_required`. Implementar como opt-in (não obrigatório) para não quebrar usuários existentes.

---

### INIT-004 — Camada de Repositórios e Services

**Problema atual:** `services.py` tem ~60 linhas de lógica de negócio no endpoint `contract_plan`. `vms.py` tem ~350 linhas com múltiplas responsabilidades. A pasta `repositories/` está vazia.

**Decisão proposta — Repositórios:**

Criar repositórios concretos em `backend/app/repositories/`:
- `service_repository.py` — `ServiceRepository(TenantScopedRepository[Service])`
- `vm_repository.py` — `VMRepository(TenantScopedRepository[VirtualMachine])`
- `invoice_repository.py` — `InvoiceRepository(TenantScopedRepository[Invoice])`
- `ticket_repository.py` — `TicketRepository(TenantScopedRepository[Ticket])`

Cada repositório expõe métodos tipados: `list(limit, offset)`, `get_by_id(id)`, `create(...)`, `update(...)`.

**Decisão proposta — Services:**

Criar `backend/app/services/contract_service.py` com `ContractService`:
```python
class ContractService:
    def __init__(self, db: Session, *, proxmox: ProxmoxService):
        self.db = db
        self.proxmox = proxmox

    def contract_plan(self, *, tenant_id, customer_id, plan_id, ...) -> tuple[Service, Invoice, Job]:
        # toda a lógica atual do endpoint contract_plan
```

Os route handlers ficam com ~10-15 linhas: validam input, instanciam o service, chamam o método, retornam o schema.

**Decisão proposta — Injeção de ProxmoxService:**

Em vez de `ProxmoxService.from_settings()` inline nos endpoints, criar um `Depends`:
```python
def get_proxmox_service() -> ProxmoxService:
    return ProxmoxService.from_settings()

ProxmoxDep = Annotated[ProxmoxService, Depends(get_proxmox_service)]
```

Isso permite substituir o ProxmoxService em testes sem monkeypatch global.

**Impacto esperado:** Endpoints finos e testáveis. Lógica de negócio testável sem servidor HTTP.

**Riscos / trade-offs:** Refatoração significativa mas não destrutiva. Os contratos de API (schemas de request/response) não mudam. Pode ser feito endpoint por endpoint.

---

### INIT-005 — Cancelamento de Serviço e VM

**Problema atual:** `cancel_service` em `vms.py` marca o serviço como `cancelled` no banco mas **não remove nem para a VM no Proxmox**. A VM continua consumindo recursos no cluster.

**Decisão proposta:**

```python
# Novo fluxo em cancel_service (ou CancellationService):
def cancel_service(vm_id, current, db, proxmox):
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    service = ...

    # 1. Tentar parar a VM
    proxmox_error = None
    try:
        proxmox.stop_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
        proxmox.delete_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
        vm.status = VMStatus.deleted
    except Exception as exc:
        proxmox_error = str(exc)
        log.error("cancel_service.proxmox_delete_failed", vm_id=str(vm.id), error=proxmox_error)
        # VM fica com status=error para ação manual

    # 2. Cancelar o serviço no banco independente do resultado Proxmox
    service.status = ServiceStatus.cancelled
    service.cancelled_at = datetime.now(UTC)

    # 3. Registrar resultado no ServiceAction
    db.add(ServiceAction(
        action=ServiceActionType.cancel,
        success=proxmox_error is None,
        details={"proxmox_error": proxmox_error} if proxmox_error else {},
    ))
    db.commit()
```

**Impacto esperado:** VMs canceladas são removidas do Proxmox. Falhas no Proxmox não impedem o cancelamento no banco. Erros ficam rastreáveis no `ServiceAction`.

**Riscos / trade-offs:** A deleção de VM é irreversível. Adicionar `payload.confirm=True` como já existe é suficiente. Considerar um período de grace (ex.: 24h) antes da deleção física — mas isso é feature, não correção.

---

### INIT-006 — Rate Limiting e Segurança de Endpoints

**Problema atual (rate limiting):** Não há rate limiting no login. Brute force irrestrito.

**Decisão proposta:** Usar `slowapi` (wrapper de `limits` para FastAPI):
```python
# requirements.txt: slowapi==0.1.9
# main.py:
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# auth.py:
@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, ...):
```

**Impacto esperado:** Previne brute force sem complexidade adicional.

**Riscos / trade-offs:** `slowapi` usa memória local por padrão — em múltiplas instâncias, o limite é por instância. Para produção com múltiplas réplicas, configurar com Redis backend. Aceitável para MVP.

---

**Problema atual (WebSocket VNC):** `vnc_websocket_proxy` chama `websocket.accept()` antes de autenticar o usuário.

**Decisão proposta:**
```python
@router.websocket("/{vm_id}/vnc/ws")
async def vnc_websocket_proxy(websocket: WebSocket, vm_id: uuid.UUID, port: int, vncticket: str):
    # 1. Validar parâmetros ANTES de accept()
    if not (5900 <= port <= 5999):
        await websocket.close(code=1008)
        return
    if not vncticket or len(vncticket) > 512:
        await websocket.close(code=1008)
        return

    # 2. Autenticar ANTES de accept()
    db = get_sessionmaker()()
    try:
        current = _get_current_user_ws(websocket, db=db)
        vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    except (UnauthorizedError, ForbiddenError, NotFoundError):
        await websocket.close(code=1008)
        db.close()
        return

    # 3. Só então aceitar a conexão
    await websocket.accept(subprotocol="binary" if "binary" in requested_protocols else None)
    # ... resto do proxy
```

**Impacto esperado:** Fecha IDOR no console VNC. Conexões não autorizadas são rejeitadas antes de serem estabelecidas.

---

**Problema atual (require_roles):** Faz query ao banco para buscar o role em cada request protegido, mesmo que o role já esteja no JWT payload.

**Decisão proposta:**
```python
def require_roles(*allowed: str) -> Callable[[User], User]:
    def _dep(
        user: CurrentUser,
        creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    ) -> User:
        # Ler role do JWT payload em vez de query ao banco
        payload = decode_token(creds.credentials)
        role_name = payload.get("role")
        if role_name not in allowed:
            raise ForbiddenError("Sem permissão")
        return user
    return _dep
```

**Impacto esperado:** Elimina uma query ao banco em cada endpoint protegido. Melhora latência e reduz carga no banco.

**Riscos / trade-offs:** Se o role de um usuário mudar, o token antigo ainda terá o role anterior até expirar (15 min). Aceitável dado o TTL curto do access token.

---

### INIT-007 — UX Dashboard e Feedback

**Problema atual:** Dashboard mostra contadores sem contexto. Ações de VM usam `window.location.reload()`. Link "Admin" visível para todos.

**Decisão proposta — Dashboard KPIs:**

Adicionar ao `DashboardPage` (Server Component):
1. Buscar faturas abertas/vencidas: `backendFetch("/api/v1/invoices?status=open&limit=1")`
2. Exibir card "Próxima fatura" com valor, data de vencimento e badge de status
3. Exibir badge colorido de status nas VMs (verde=running, vermelho=error, cinza=stopped)
4. Exibir alerta se houver fatura vencida

**Decisão proposta — Feedback de ações de VM:**

Substituir `window.location.reload()` por polling de status:
```typescript
async function run(action: "start" | "stop" | "reboot") {
    setLoading(action);
    await fetch(`/api/vms/${vmId}/${action}`, { method: "POST" });
    // Poll status até mudar ou timeout
    let attempts = 0;
    while (attempts < 10) {
        await new Promise(r => setTimeout(r, 2000));
        const status = await fetch(`/api/vms/${vmId}/status`).then(r => r.json());
        if (status.status !== currentStatus) {
            setVmStatus(status.status);
            break;
        }
        attempts++;
    }
    setLoading(null);
}
```

**Decisão proposta — Links condicionais:**

O frontend não tem acesso ao role do usuário no layout (Server Component). Solução: criar um endpoint `GET /auth/me` (já existe) e usar o campo `role` retornado para condicionar a renderização. Alternativamente, armazenar o role em um cookie não-sensível (`mhc_role`) definido no login, lido pelo middleware/layout.

**Decisão proposta — Infraestrutura com capacidade:**

A página `/admin/infrastructure` deve consumir `GET /admin/proxmox/capacity` (já implementado) em vez de apenas `/admin/proxmox/nodes`. Exibir barras de progresso de CPU e RAM por node usando apenas Tailwind (sem biblioteca de gráficos).

---

### INIT-009 — Limpeza e Padronização

**Problema atual (bun vs npm no CI):** O projeto usa `bun` como padrão — o `Dockerfile` usa `oven/bun:1-alpine` e `bun install`, e o `bun.lock` está commitado. Porém o CI (`ci.yml`) usa `actions/setup-node`, `cache: npm`, `cache-dependency-path: frontend/package-lock.json` e `npm ci`. Isso significa que o CI instala dependências com npm enquanto produção usa bun, podendo causar divergências de versões resolvidas.

**Decisão proposta:** Padronizar o CI em **bun**, que é o gerenciador de pacotes do projeto:
- Substituir `actions/setup-node` por `oven/setup-bun@v2` no job `frontend` do CI
- Substituir `npm ci` por `bun install --frozen-lockfile`
- Substituir `npm run lint`, `npm run typecheck`, `npm run build` por `bun run lint`, `bun run typecheck`, `bun run build`
- Remover `package-lock.json` do repositório (manter apenas `bun.lock`)
- Atualizar `.gitignore` para ignorar `package-lock.json`

Justificativa: o Dockerfile e o ambiente de desenvolvimento já usam bun. O CI deve espelhar o ambiente de produção.

**Problema atual (paramiko):** `paramiko==3.5.1` está em `requirements.txt` mas não é usado pela aplicação (apenas pelos scripts de setup em `scripts/`).

**Decisão proposta:** Remover de `requirements.txt`. Se necessário para scripts de desenvolvimento, mover para um `requirements-dev.txt` separado.

---

## Fases de Rollout

### Fase 0 — Hotfixes de Segurança Imediata

**Objetivo:** Eliminar riscos críticos que podem ser explorados em produção hoje, sem nenhuma mudança de API ou banco de dados.

**Tipo de mudança:** Configuração, validação de startup, ajustes de cookie, condicionais de UI.

**Inclui:**
- Validação de `JWT_SECRET` e `SEED_ON_STARTUP` no startup (INIT-001)
- Garantir `HttpOnly` + `Secure` no cookie de auth (INIT-001)
- Credenciais demo condicionais ao `APP_ENV` (INIT-001, INIT-009)
- Auth antes de `accept()` no WebSocket VNC (INIT-006)
- Validação de `port` e `vncticket` no WebSocket (INIT-006)
- Rate limiting no login (INIT-006)
- Leitura de role do JWT em `require_roles` (INIT-006)

**Critério de conclusão:** Nenhum dos riscos da tabela de segurança da auditoria está presente. CI verde.

---

### Fase 1 — Refactors Estruturais Seguros

**Objetivo:** Introduzir camada de repositórios e services sem alterar contratos de API. Corrigir o cancelamento de serviço/VM. Implementar MFA/TOTP.

**Tipo de mudança:** Refatoração interna (sem mudança de API externa), nova funcionalidade (MFA), correção de bug crítico (cancelamento).

**Inclui:**
- `TenantScopedRepository` base (INIT-002)
- `ServiceRepository`, `VMRepository`, `InvoiceRepository`, `TicketRepository` (INIT-004)
- `ContractService` extraído de `services.py` (INIT-004)
- Injeção de `ProxmoxService` via `Depends` (INIT-004)
- Correção do `cancel_service` para deletar VM no Proxmox (INIT-005)
- Implementação completa de MFA/TOTP (INIT-003)
- Testes de isolamento de tenant (INIT-008)

**Critério de conclusão:** Todos os endpoints existentes continuam funcionando (testes de integração passam). Novos testes de isolamento de tenant passam. MFA funcional end-to-end.

---

### Fase 2 — UX e Produto

**Objetivo:** Melhorar a experiência do cliente e do operador no painel, sem dependências de mudanças de backend não feitas nas fases anteriores.

**Tipo de mudança:** Frontend apenas (exceto REQ-029 que pode precisar de ajuste no schema de resposta do `/capacity`).

**Inclui:**
- Dashboard com KPIs reais (INIT-007)
- Feedback de ações de VM sem `location.reload()` (INIT-007)
- Confirmação antes de ações destrutivas (INIT-007)
- Links de admin condicionais ao role (INIT-007)
- Estados vazios com CTAs (INIT-007)
- Página de infraestrutura com capacidade do cluster (INIT-007)
- Formatação de bytes em unidades legíveis

**Critério de conclusão:** Typecheck e lint passam. Nenhum `window.location.reload()` em ações de VM. Dashboard exibe pelo menos fatura pendente e status de VMs.

---

### Fase 3 — Endurecimento Operacional

**Objetivo:** Aumentar cobertura de testes, limpar dependências, melhorar observabilidade e documentação.

**Tipo de mudança:** Testes, limpeza, documentação.

**Inclui:**
- Testes de billing (suspensão, reativação) (INIT-008)
- Testes de cancelamento de VM (INIT-008)
- Remoção de `paramiko` de `requirements.txt` (INIT-009)
- Padronização npm vs bun (INIT-009)
- Remoção de `tsconfig.tsbuildinfo` do git (INIT-009)
- Substituição dos dados demo inline em `backend.ts` por fixtures ou remoção
- Documentação de variáveis de ambiente obrigatórias no README

**Critério de conclusão:** Cobertura de testes inclui billing, cancelamento e tenant isolation. Nenhuma dependência desnecessária em `requirements.txt`. CI verde.

---

## Estratégia de Testes

### Fase 0
- **Tipos:** Testes de integração existentes devem continuar passando. Adicionar teste que verifica que o startup falha com `JWT_SECRET=change-me` em `app_env=production`.
- **Critério de merge:** CI verde, nenhum teste existente quebrado.

### Fase 1
- **Tipos:**
  - Testes unitários para `ContractService` (mock de repositórios e ProxmoxService)
  - Testes de integração para repositórios (com banco real, como já feito no conftest)
  - Testes de autorização multi-tenant: para cada endpoint principal, testar com usuário de tenant diferente e verificar 403/404
  - Testes de MFA: ativação, verificação, login com MFA, desativação
  - Teste de cancelamento: com mock de Proxmox que falha, verificar que serviço é cancelado mesmo assim
- **Critério de merge:** Todos os testes de isolamento de tenant passam. MFA funcional. Cancelamento correto.

### Fase 2
- **Tipos:**
  - Typecheck TypeScript (`npm run typecheck`) deve passar
  - Lint (`npm run lint`) deve passar
  - Build de produção (`npm run build`) deve passar
  - Revisão manual de UX (não automatizável)
- **Critério de merge:** Build limpo, sem erros de tipo, sem `window.location.reload()` em ações de VM.

### Fase 3
- **Tipos:**
  - Testes de integração para billing (usando `TestClient` + banco real)
  - Verificação de que `paramiko` não está mais em `requirements.txt`
  - Verificação de que `package-lock.json` não está mais no repositório (substituído por `bun.lock`)
- **Critério de merge:** CI verde, cobertura de testes aumentada para billing e cancelamento.
