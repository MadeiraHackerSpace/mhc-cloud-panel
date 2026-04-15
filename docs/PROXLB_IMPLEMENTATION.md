# MHC Cloud Panel — Implementações ProxLB-Inspired

> Implementado em: 2026-04-14  
> Referência: [ProxLB](https://github.com/credativ/ProxLB) — Advanced resource scheduler and load balancer for Proxmox clusters  
> Contexto: [docs/PROXLB_IMPROVEMENTS.md](PROXLB_IMPROVEMENTS.md)

---

## Resumo Executivo

Implementação de 7 melhorias inspiradas no projeto ProxLB, trazendo **scheduling inteligente de provisionamento**, **rebalanceamento automático de carga**, **modo de manutenção de nodes** e **proteção contra overprovisioning** ao MHC Cloud Panel — com total rastreabilidade via `AuditLog` e `ServiceAction`.

---

## Arquivos Criados

### `backend/app/services/node_scheduler.py` ⭐ Principal

**NodeScheduler** — motor de seleção inteligente de nodes.

Responsabilidades:
- Coleta métricas reais de CPU/RAM/Disco de todos os nodes via `ProxmoxService.list_nodes()`
- Calcula o **"balanciness"** do cluster (delta % entre o node mais e o menos carregado) — conceito central do ProxLB
- Seleciona o melhor node respeitando:
  - **Política de placement do Plano** (`none`, `affinity`, `anti_affinity`, `pinned`)
  - **Nodes em manutenção** (filtrados automaticamente)
  - **Proteção contra overprovisioning** (buffer configurável via `SCHEDULER_RESERVE_PCT`)
- Expõe `ClusterCapacity` e `NodeCapacity` como data classes para uso na API e tasks

Classes e exceções:
```
NodeCapacity       — snapshot de recursos de um node
ClusterCapacity    — visão agregada do cluster + balanciness()
NodeScheduler      — best_node(), get_cluster_capacity()
InsufficientCapacityError — nenhum node tem RAM suficiente
NoAvailableNodeError      — nenhum node online disponível
```

---

### `backend/app/tasks/rebalance_cluster.py`

**Task Celery de rebalanceamento periódico** — agendada via Celery Beat a cada 30 minutos.

Fluxo:
1. Calcula balanciness do cluster pelo método configurado (memória/CPU/disco)
2. Se `balanciness > REBALANCE_THRESHOLD_PCT` → identifica o node mais carregado
3. Encontra a VM em execução nesse node mais adequada para migração
4. Executa `proxmox.migrate_vm()` (live migration)
5. Atualiza `VirtualMachine.proxmox_node` no banco
6. Registra cada migração em `ServiceAction` (auditável no painel admin)
7. Repete até o cluster estar balanceado ou atingir o limite de iterações

> Por padrão opera em **dry-run** (`REBALANCE_ENABLED=false`) — loga o que faria sem mover nada. Ative com `REBALANCE_ENABLED=true`.

---

### `backend/app/tasks/maintenance_drain.py`

**Task Celery de drenagem de node em manutenção** — disparada pelo endpoint `POST /admin/proxmox/nodes/{node}/maintenance`.

Fluxo:
1. Confirma que o node ainda está marcado como `is_maintenance=True` no banco
2. Lista todas as VMs `running` nesse node
3. Para cada VM, chama `NodeScheduler.best_node()` excluindo o node em manutenção
4. Executa live migration para o melhor node disponível
5. Registra cada migração em `ServiceAction`
6. Retorna sumário de VMs migradas e erros

---

## Arquivos Modificados

### `backend/app/models/proxmox_node.py`

| Campo | Tipo | Descrição |
|---|---|---|
| `is_maintenance` | `Boolean` (default `False`) | Quando `True`, o NodeScheduler exclui este node de novos provisionamentos e o `maintenance_drain` migra suas VMs |
| `notes` | `Text` (nullable) | Observações do operador sobre o estado do node |

Novo índice: `ix_proxmox_nodes_is_maintenance`

---

### `backend/app/models/plan.py`

Novo enum `PlacementPolicy` no modelo:

| Valor | Comportamento |
|---|---|
| `none` | NodeScheduler escolhe livremente o melhor node (padrão) |
| `affinity` | VMs do mesmo tenant preferem ficar no mesmo node (menor latência intra-serviço) |
| `anti_affinity` | VMs do mesmo tenant são distribuídas em nodes diferentes (alta disponibilidade) |
| `pinned` | VMs fixadas em nodes de alta performance (fornecidos via `preferred_nodes`) |

---

### `backend/app/core/config.py`

Novas configurações via variáveis de ambiente:

| Variável | Padrão | Descrição |
|---|---|---|
| `SCHEDULER_METHOD` | `memory` | Critério de seleção do node: `memory` \| `cpu` \| `disk` |
| `SCHEDULER_RESERVE_PCT` | `10` | Buffer de reserva (%): o scheduler não usa os últimos N% de RAM do node |
| `REBALANCE_THRESHOLD_PCT` | `20` | Delta (%) máximo tolerado entre o node mais e menos carregado antes de rebalancear |
| `REBALANCE_ENABLED` | `false` | `true` = migra VMs de fato; `false` = dry-run (apenas loga) |

---

### `backend/app/integrations/proxmox/service.py`

Adicionado `migrate_vm()` em todos os adapters:

| Adapter | Implementação |
|---|---|
| `ProxmoxAdapter` (Protocol) | `def migrate_vm(*, node, vmid, target_node) -> None` |
| `ProxmoxerAdapter` | `proxmox.nodes(node).qemu(vmid).migrate.post(target=target_node, online=1)` |
| `HttpMockAdapter` | `POST /api2/json/nodes/{node}/qemu/{vmid}/migrate` |

---

### `backend/app/tasks/celery_app.py`

**Celery Beat schedule** configurado — as tasks agora rodam automaticamente:

| Task | Schedule | Descrição |
|---|---|---|
| `sync_vm_status` | A cada **5 minutos** | Sincroniza status real das VMs com o Proxmox |
| `mark_overdue_and_suspend` | A cada **hora** (no minuto 0) | Verifica faturas vencidas, suspende serviços e para VMs de inadimplentes |
| `rebalance_cluster` | A cada **30 minutos** | Rebalanceia carga do cluster (dry-run por padrão) |

Novos módulos registrados em `include`:
- `app.tasks.rebalance_cluster`
- `app.tasks.maintenance_drain`

---

### `backend/app/tasks/provision_vm.py`

Substituído `raise RuntimeError("node_not_selected")` por chamada ao `NodeScheduler.best_node()`:

```python
# Antes: operador obrigado a informar o node manualmente
if not node:
    raise RuntimeError("node_not_selected")

# Depois: scheduling automático com todas as proteções
if not node:
    node = scheduler.best_node(
        ram_mb=plan.ram_mb,
        vcpu=plan.vcpu,
        disk_gb=plan.disk_gb,
        placement_policy=plan.placement_policy,
        tenant_id=service.tenant_id,
    )
```

---

### `backend/app/api/v1/routes/admin_proxmox.py`

Três novos endpoints adicionados (restritos a `super_admin` e `operador`):

#### `GET /api/v1/admin/proxmox/capacity`

Retorna métricas de recursos em tempo real de todos os nodes, incluindo o **balanciness** do cluster.

```json
{
  "nodes": [
    {
      "node": "pve2",
      "status": "online",
      "mem_used_gb": 1.87,
      "mem_total_gb": 64.0,
      "mem_free_gb": 62.13,
      "mem_free_pct": 97.1,
      "cpu_usage_pct": 2.0,
      "maxcpu": 16,
      "disk_used_gb": 46.57,
      "disk_total_gb": 931.32,
      "vms_running": 0
    }
  ],
  "balanciness": 12.5,
  "method": "memory",
  "online_count": 2,
  "total_count": 2
}
```

Query param: `?method=memory|cpu|disk`

---

#### `GET /api/v1/admin/proxmox/best-node`

Retorna o melhor node para um perfil de VM — **equivalente ao `--best-node` do ProxLB**, útil para Terraform/Ansible.

Query params: `?ram_mb=2048&vcpu=2&disk_gb=40&method=memory`

```json
{
  "node": "pve2",
  "method": "memory",
  "mem_free_gb": 62.13,
  "cpu_usage_pct": 2.0
}
```

Códigos de erro:
- `503` — nenhum node online disponível
- `507` — nenhum node com capacidade suficiente para o perfil solicitado

---

#### `POST /api/v1/admin/proxmox/nodes/{node_name}/maintenance`

Ativa ou desativa modo de manutenção em um node. Com `drain: true`, dispara a task `maintenance_drain` que migra todas as VMs via live migration.

```json
// Request
{ "enable": true, "notes": "Atualização de firmware", "drain": true }

// Response
{
  "ok": true,
  "node": "pve",
  "is_maintenance": true,
  "drain_task_id": "abc-123-..."
}
```

---

### `backend/app/schemas/proxmox.py`

Novos schemas Pydantic:
- `NodeCapacityOut` — snapshot de recursos de um node
- `ClusterCapacityOut` — visão completa do cluster com balanciness
- `BestNodeOut` — resposta do endpoint best-node
- `MaintenanceRequest` — payload para ativar/desativar manutenção

---

### `backend/app/schemas/plan.py`

`PlacementPolicy` exposto em `PlanOut` (resposta da API) e `PlanCreate` (criação de planos pelo admin).

---

### `backend/proxmox_mock.py`

- **Segundo node `pve2`** adicionado com 64GB RAM e 1TB disco (mais folga que o `pve`) para que o `NodeScheduler` tenha escolha real em dev/testes
- **Métricas de disco** (`disk`, `maxdisk`) adicionadas a ambos os nodes
- **Endpoint `POST /api2/json/nodes/{node}/qemu/{vmid}/migrate`** implementado (registra o novo node no estado da VM mock)

---

### `docker-compose.yml`

Novo serviço `celery-beat`:

```yaml
celery-beat:
  build:
    context: ./backend
  command: ["celery", "-A", "app.tasks.celery_app", "beat", "-l", "INFO",
            "--scheduler", "celery.beat:PersistentScheduler"]
```

---

### `.env.example`

Novas variáveis documentadas:

```env
SCHEDULER_METHOD=memory
SCHEDULER_RESERVE_PCT=10
REBALANCE_THRESHOLD_PCT=20
REBALANCE_ENABLED=false
```

---

## Diagrama do Fluxo de Provisionamento (antes vs. depois)

```
ANTES:
Cliente contrata → Job criado → provision_vm → node_not_selected ERROR
                                               ↑ (operador tinha que informar o node)

DEPOIS:
Cliente contrata → Job criado → provision_vm
                                    ↓
                              NodeScheduler.best_node()
                                    ↓ consulta API Proxmox
                                    ↓ verifica manutenção (DB)
                                    ↓ aplica PlacementPolicy do Plano
                                    ↓ protege contra overprovisioning
                                    ↓
                              node selecionado automaticamente
                                    ↓
                              clone + Cloud-Init + start
```

---

## Como Ativar o Rebalanceamento Efetivo

Por padrão o rebalanceamento roda em **dry-run** (apenas loga). Para ativar migrações reais:

```env
# No .env
REBALANCE_ENABLED=true
REBALANCE_THRESHOLD_PCT=20   # Rebalanceia quando delta > 20%
SCHEDULER_METHOD=memory      # Critério: memória livre
```

O serviço `celery-beat` já está no `docker-compose.yml` e iniciará automaticamente.

---

## Pendências Derivadas

> Estas tarefas ficaram fora do escopo desta implementação e precisam de migration Alembic:

- [ ] Gerar migração Alembic para `is_maintenance` + `notes` em `proxmox_nodes`
- [ ] Gerar migração Alembic para `placement_policy` em `plans`
- [ ] Melhorar `_find_best_vm_to_migrate()` no `rebalance_cluster.py` para usar uso real de RAM por VM (via Proxmox API) em vez de selecionar a primeira VM do node
- [ ] Adicionar `ServiceActionType.migrate` ao enum de ações (hoje usa `reboot` como proxy)
- [ ] Página de infraestrutura no frontend (`/admin/infrastructure`) consumindo `GET /capacity`
