# MHC Cloud Panel — Melhorias inspiradas no ProxLB

> Referência: [ProxLB](https://github.com/credativ/ProxLB) — Advanced resource scheduler and load balancer for Proxmox clusters  
> Gerado em: 2026-04-14

---

## O que o ProxLB resolve que o MHC Cloud Panel ignora hoje

O ProxLB é um **scheduler e balanceador de carga de recursos** para clusters Proxmox. Ele coleta métricas reais de CPU/memória/disco de todos os nodes via API Proxmox e distribui as VMs de forma inteligente, com suporte a regras de afinidade, modo de manutenção, dry-run e integração com CI/CD.

O MHC Cloud Panel, atualmente, **escolhe o node de provisionamento de forma manual**: o cliente ou o operador informam `proxmox_node` no payload da contratação. Não existe nenhuma inteligência de scheduling. Isso gera:

- **Overprovisioning silencioso** — um node pode ficar saturado enquanto outros ficam ociosos
- **Decisão humana sujeita a erro** — operador precisa saber de cabeça qual node tem capacidade
- **Sem visibilidade de capacidade** — o painel não exibe métricas do cluster em tempo real

---

## Melhorias propostas (do mais simples ao mais complexo)

### 🟢 1. Smart Node Selector — Escolha automática de node no provisionamento

**Problema atual:** `provision_vm.py` exige `proxmox_node` no payload. Se não fornecido, lança `RuntimeError("node_not_selected")`.

**Melhoria:** Criar um `NodeScheduler` que consulta `ProxmoxService.list_nodes()` e retorna o node com **mais memória livre** (ou menor uso de CPU) para receber a nova VM — exatamente o que o ProxLB faz na sua função `--best-node`.

**Onde implementar:**

```python
# backend/app/services/node_scheduler.py  [NOVO]

class NodeScheduler:
    def __init__(self, proxmox: ProxmoxService):
        self.proxmox = proxmox

    def best_node(self, *, method: str = "memory") -> str:
        """Retorna o node com mais recurso livre segundo o método escolhido."""
        nodes = self.proxmox.list_nodes()
        # Filtra nodes online e ordena por recurso livre (mem, cpu, disk)
        available = [n for n in nodes if n.get("status") == "online"]
        if method == "memory":
            return max(available, key=lambda n: n.get("maxmem", 0) - n.get("mem", 0))["node"]
        elif method == "cpu":
            return min(available, key=lambda n: n.get("cpu", 1.0))["node"]
        raise ValueError(f"método desconhecido: {method}")
```

**Impacto em `provision_vm.py`:** remover o `raise RuntimeError("node_not_selected")` e chamar `NodeScheduler.best_node()` quando `node` não for fornecido.

---

### 🟢 2. Expor métricas de capacidade do cluster na API Admin

**Problema atual:** `GET /admin/proxmox/nodes` existe, mas retorna dados brutos do Proxmox sem interpretação de capacidade.

**Melhoria:** Adicionar um endpoint `GET /admin/proxmox/capacity` que retorna para cada node:

| Campo | Descrição |
|---|---|
| `node` | Nome do node |
| `mem_used_gb` | Memória usada |
| `mem_total_gb` | Memória total |
| `mem_free_pct` | % livre |
| `cpu_usage_pct` | % CPU em uso |
| `vms_running` | Quantidade de VMs ativas |
| `status` | `online` / `offline` |

Isso permite ao operador visualizar no painel admin **qual node tem capacidade** antes de provisionar ou rebalancear — equivalente ao dashboard visual do ProxLB.

---

### 🟡 3. Rebalanceamento de VMs — Tarefa Celery periódica

**Problema atual:** Não existe nenhuma lógica para mover VMs entre nodes quando um node fica saturado.

**Melhoria:** Criar uma task Celery `rebalance_cluster` (agendada via Celery Beat) que:

1. Coleta uso de memória/CPU de todos os nodes via `ProxmoxService.list_nodes()`
2. Calcula o **"balanciness"** (delta entre node mais carregado e mais ocioso) — conceito diretamente do ProxLB
3. Se o delta exceder um threshold configurável (`REBALANCE_THRESHOLD_PCT`), identifica a VM de maior uso no node saturado
4. Dispara migração live (`proxmox.migrate_vm(node_origem, node_destino, vmid)`) — requer adicionar `migrate_vm` ao `ProxmoxAdapter`
5. Registra no `AuditLog` e `ServiceAction`

**Onde implementar:**

```
backend/app/tasks/rebalance_cluster.py   [NOVO]
backend/app/integrations/proxmox/service.py  [MODIFICAR — adicionar migrate_vm()]
backend/app/tasks/celery_app.py  [MODIFICAR — adicionar beat_schedule]
```

---

### 🟡 4. Regras de Afinidade e Anti-Afinidade por Plano/Tenant

**Problema atual:** O MHC já aplica tags `tenant:{id}` e `service:{id}` nas VMs no Proxmox via `ProxmoxVMCreateSpec.tags`. Porém, essas tags não são usadas para nenhuma decisão de placement.

**Melhoria inspirada no ProxLB:** Usar as tags (ou um campo de metadata no `Plan`) para definir regras de afinidade:

| Regra | Comportamento |
|---|---|
| **Affinity** | VMs do mesmo tenant ficam no mesmo node (melhor latência interna) |
| **Anti-Affinity** | VMs de planos "HA" são distribuídas em nodes diferentes (resiliência) |
| **Pinning** | VMs de planos premium são fixadas em nodes de alta performance |

**Onde implementar:**
- Adicionar campo `placement_policy: enum(none, affinity, anti_affinity, pinned)` no model `Plan`
- `NodeScheduler.best_node()` recebe as regras e filtra/prioriza nodes

---

### 🟡 5. Modo de Manutenção de Node via Painel Admin

**Problema atual:** Não existe forma de colocar um node em manutenção pelo painel. O operador precisaria fazer isso diretamente no Proxmox.

**Melhoria:** Endpoint `POST /admin/proxmox/nodes/{node}/maintenance` que:

1. Marca o node como `maintenance` na tabela `ProxmoxNode`
2. Dispara uma task Celery que lista todas as VMs no node (via `list_qemu`)
3. Para cada VM, executa `migrate_vm()` para o melhor node disponível (usando o `NodeScheduler`)
4. Exibe progresso no admin via jobs

Isso replica exatamente o **Maintenance Mode** do ProxLB — mas integrado ao modelo de dados do MHC Cloud Panel, com auditoria e visibilidade no painel.

**Onde implementar:**
```
backend/app/models/proxmox_node.py     [MODIFICAR — adicionar campo is_maintenance]
backend/app/api/v1/routes/admin_proxmox.py  [MODIFICAR — novo endpoint]
backend/app/tasks/maintenance_drain.py  [NOVO]
```

---

### 🟠 6. Proteção contra Overprovisioning

**Problema atual:** Nada impede que um node receba mais VMs do que sua memória suporta. O Proxmox aceita o clone, e a VM pode não iniciar ou degradar o node.

**Melhoria:** No `NodeScheduler.best_node()`, antes de selecionar um node, verificar se a RAM disponível é suficiente para o plano contratado (`plan.ram_mb`). Se nenhum node tiver capacidade, lançar `InsufficientCapacityError` e marcar o `Job` como `failed` com mensagem clara.

```python
# Verificação antes de provisionar
free_mb = node["maxmem"] - node["mem"]
if free_mb < plan.ram_mb * 1.1:  # 10% de buffer (como o node_resource_reserve do ProxLB)
    raise InsufficientCapacityError(f"Node {node['node']} sem RAM suficiente")
```

---

### 🟠 7. API `best-node` exposta para integração externa

**Inspirado em:** o flag `--best-node` do ProxLB, que permite integração com Terraform/Ansible.

**Melhoria:** Endpoint `GET /admin/proxmox/best-node?ram_mb=2048&vcpu=2` que retorna o melhor node disponível em formato JSON — permitindo que automações externas (scripts, Terraform, Ansible) consultem o MHC Cloud Panel antes de provisionar recursos fora do fluxo padrão.

---

## Resumo das melhorias por esforço

| # | Melhoria | Esforço | Impacto | Arquivos afetados |
|---|---|---|---|---|
| 1 | Smart Node Selector (melhor node automático) | 🟢 Baixo | 🔴 Alto | `node_scheduler.py` [NEW], `provision_vm.py` |
| 2 | API de capacidade do cluster | 🟢 Baixo | 🟡 Médio | `admin_proxmox.py` |
| 3 | Rebalanceamento automático (Celery Beat) | 🟡 Médio | 🔴 Alto | `rebalance_cluster.py` [NEW], `celery_app.py`, `service.py` |
| 4 | Regras Affinity/Anti-Affinity por Plano | 🟡 Médio | 🟡 Médio | `plan.py`, `node_scheduler.py` |
| 5 | Modo Manutenção de Node no Admin | 🟡 Médio | 🟡 Médio | `proxmox_node.py`, `admin_proxmox.py`, `maintenance_drain.py` [NEW] |
| 6 | Proteção contra Overprovisioning | 🟢 Baixo | 🔴 Alto | `node_scheduler.py`, `provision_vm.py` |
| 7 | Endpoint `best-node` para integração externa | 🟢 Baixo | 🟠 Baixo | `admin_proxmox.py` |

---

## Ponto de atenção: ProxLB como serviço paralelo

Uma alternativa mais rápida à implementação nativa seria **rodar o ProxLB como um serviço externo** no `docker-compose.yml`, apontado para o mesmo cluster Proxmox. Nesse cenário:

- O ProxLB cuidaria do **rebalanceamento periódico** e do **modo manutenção**
- O MHC Cloud Panel precisaria apenas implementar o **Smart Node Selector** (#1) e a **API de capacidade** (#2), consultando os nodes via Proxmox API como já faz

```yaml
# Adição ao docker-compose.yml
proxlb:
  image: ghcr.io/credativ/proxlb:latest
  container_name: proxlb
  restart: unless-stopped
  volumes:
    - ./proxlb.yaml:/etc/proxlb/proxlb.yaml:ro
```

> **Vantagem:** zero código novo para rebalanceamento.  
> **Desvantagem:** o MHC Cloud Panel não teria visibilidade das migrações feitas pelo ProxLB (não aparecem no `AuditLog`, `ServiceAction` ou nos Jobs do painel).

A abordagem **nativa integrada** (#3 acima) é superior para o modelo SaaS, pois mantém toda a rastreabilidade dentro do próprio painel.
