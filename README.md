# MHC Cloud Panel

Plataforma SaaS multi-tenant para revenda e gestão de VPS sobre Proxmox VE. Inclui portal do cliente, painel administrativo, provisionamento assíncrono via Celery, billing básico, tickets de suporte e auditoria.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.x + Alembic |
| Banco | PostgreSQL 16 |
| Filas | Celery + Redis 7 |
| Frontend | Next.js + TypeScript + Tailwind CSS |
| Infra | Proxmox VE (via `proxmoxer`) |
| Testes | pytest |

## Subir com Docker Compose

**Pré-requisitos:** Git, Docker com Compose V2.

```bash
# 1. Copie o .env de exemplo
cp .env.example .env          # Linux/macOS/WSL
# Copy-Item .env.example .env  # PowerShell

# 2. Suba os serviços
docker compose up --build
```

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend (OpenAPI) | http://localhost:8000/docs |
| Proxmox Mock | http://localhost:8001/api2/json/nodes |

Por padrão o `.env.example` aponta para o mock do Proxmox (`PROXMOX_HOST=http://proxmox_mock:8001`). Para usar um Proxmox real, veja a seção abaixo.

## Credenciais padrão (seed)

Criadas automaticamente na primeira inicialização quando `SEED_ON_STARTUP=true`:

| Usuário | Senha | Papel |
|---|---|---|
| `superadmin@mhc.local` | `admin12345` | Super Admin |
| `operador@mhc.local` | `admin12345` | Operador |
| `cliente@mhc.local` | `admin12345` | Cliente Demo |

## Conectar ao Proxmox real

O backend aceita qualquer Proxmox VE acessível via HTTPS com token de API. Configure no `.env`:

```env
PROXMOX_HOST=https://<IP_DO_PROXMOX>:8006
PROXMOX_USER=mhc
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mhc-token
PROXMOX_TOKEN_SECRET=<uuid-do-token>
PROXMOX_VERIFY_SSL=false
```

Para criar o usuário e token no Proxmox:

```bash
pveum user add mhc@pam --comment "MHC Cloud Panel"
pveum role add MHC_API -privs "VM.Allocate,VM.Clone,VM.Config.Disk,VM.Config.CPU,VM.Config.Memory,VM.Config.Network,VM.Config.Options,VM.Audit,VM.PowerMgmt,Datastore.AllocateSpace,Datastore.Audit"
pveum aclmod / -user mhc@pam -role MHC_API
pveum user token add mhc@pam mhc-token --privsep 0
```

### Setup com Proxmox no Debian WSL (desenvolvimento)

Se você instalou o Proxmox VE diretamente no Debian WSL2 (seguindo o [guia oficial](https://pve.proxmox.com/wiki/Install_Proxmox_VE_on_Debian_13_Trixie)):

1. Corrija o `/etc/hosts` para o `pmxcfs` resolver o hostname:

```bash
# Substitua pelo IP real mostrado por: ip addr show eth0
sudo sed -i 's/127.0.1.1/172.30.x.x/' /etc/hosts
```

2. Desabilite a geração automática do `/etc/hosts` pelo WSL — adicione ao `/etc/wsl.conf`:

```ini
[network]
generateHosts = false
```

3. Crie um port proxy no Windows (PowerShell como Administrador) para os containers Docker alcançarem o Proxmox:

```powershell
# Substitua pelo IP real do WSL (ip addr show eth0)
netsh interface portproxy add v4tov4 listenport=8006 listenaddress=0.0.0.0 connectport=8006 connectaddress=<IP_WSL>
```

4. No `.env`, use `host.docker.internal:8006` como host:

```env
PROXMOX_HOST=https://host.docker.internal:8006
```

O script `scripts/setup-proxmox-portforward.ps1` automatiza o passo 3 (execute como Administrador).

## Variáveis de ambiente relevantes

```env
# Proxmox
PROXMOX_HOST=https://host:8006      # URL completa com esquema e porta
PROXMOX_VERIFY_SSL=false            # false para certificados self-signed
PROXMOX_TIMEOUT_SECONDS=30

# Node Scheduler (seleção de node para provisionamento)
SCHEDULER_METHOD=memory             # memory | cpu | disk
SCHEDULER_RESERVE_PCT=10            # % de buffer antes de considerar node cheio

# Rebalanceamento de cluster
REBALANCE_THRESHOLD_PCT=20          # delta % entre node mais/menos carregado
REBALANCE_ENABLED=false             # false = dry-run (só loga, não migra)
```

## Desenvolvimento sem Docker

Veja o guia completo em [docs/SETUP.md](docs/SETUP.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/SETUP.md](docs/SETUP.md) | Setup completo (Docker, local, WSL, testes) |
| [docs/BACKEND.md](docs/BACKEND.md) | Arquitetura do backend por módulo |
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | O que está implementado e o que falta |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guia de contribuição |

## Licença

Apache-2.0. Veja [LICENSE](LICENSE).
