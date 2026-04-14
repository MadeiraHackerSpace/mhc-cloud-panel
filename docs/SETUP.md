# Setup (independente de ambiente)

Este projeto roda de forma consistente via Docker Compose (recomendado) ou em modo “local dev” (sem Docker). As instruções abaixo cobrem Linux, macOS e Windows 11 com WSL (Debian).

## Opção A (recomendada): Docker Compose

Pré-requisitos:

- Git
- Docker + Docker Compose (Compose V2)

Passos:

1. Crie o arquivo `.env` a partir do exemplo:

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

Linux/macOS/WSL:

```bash
cp .env.example .env
```

2. Suba os serviços:

```bash
docker compose up --build
```

Serviços e URLs:

- Frontend: http://localhost:3000
- Backend (OpenAPI): http://localhost:8000/docs
- Proxmox Mock (API): http://localhost:8001/api2/json/nodes

Notas:

- Por padrão, o `.env.example` já aponta para o mock do Proxmox: `PROXMOX_HOST=http://proxmox_mock:8001`.
- O backend escolhe automaticamente o mock quando `PROXMOX_HOST` começa com `http://` (em vez de `https://`).

## Windows 11 + WSL2 (Debian)

### 1) Instalar WSL e Debian

No PowerShell (Administrador):

```powershell
wsl --install
wsl --set-default-version 2
wsl --install -d Debian
```

Depois, abra o Debian no menu iniciar e finalize:

- criação do usuário/senha Linux
- atualização do sistema:

```bash
sudo apt update
sudo apt -y upgrade
```

### 2) Recomendações de workspace (performance)

Para melhor performance (Node, hot reload, I/O), mantenha o repositório dentro do filesystem Linux do WSL, por exemplo:

```bash
mkdir -p ~/code
cd ~/code
git clone <URL_DO_REPO> mhc-cloud-panel
cd mhc-cloud-panel
```

Evite rodar o projeto a partir de `/mnt/c/...` quando possível.

### 3) Docker no Windows + WSL

Duas formas comuns:

- Docker Desktop (recomendado): instale no Windows e habilite WSL Integration para a distro “Debian”.
- Docker Engine dentro do WSL: instale `docker-ce` no Debian e use o daemon no próprio WSL.

Com Docker Desktop, você normalmente consegue rodar `docker compose ...` direto no Debian (WSL) e acessar via `localhost` no Windows.

Para instalar o Docker Engine dentro do Debian, este repositório inclui os arquivos em `wsl/debian/`:

- `wsl/debian/setup-docker.ps1`: roda no Windows (PowerShell) e executa a instalação dentro do Debian via `wsl -d Debian -- ...`
- `wsl/debian/setup-docker.sh`: roda dentro do Debian (WSL)
- `wsl/debian/daemon.json`: configuração do daemon
- `wsl/debian/wsl.conf`: habilita `systemd=true` (necessário para `systemctl` no WSL)

Execução recomendada (Windows / PowerShell):

```powershell
.\wsl\debian\setup-docker.ps1
```

Alternativa (dentro do Debian / WSL):

```bash
sudo bash wsl/debian/setup-docker.sh
```

Bootstrap completo de ambiente (Docker + Python + Node + dependencias do projeto):

```bash
sudo bash wsl/debian/bootstrap-mhc-env.sh
```

Se quiser informar o caminho do projeto manualmente:

```bash
sudo bash wsl/debian/bootstrap-mhc-env.sh /mnt/c/Dev/mhc-cloud-panel
```

Passos manuais (Debian / WSL), equivalentes ao instalador:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
sudo systemctl enable docker
sudo systemctl restart docker
```

## Opção B: Rodar sem Docker (Linux/WSL)

Use esta opção quando você quiser controlar cada processo localmente. Você vai precisar de Postgres e Redis rodando no sistema.

Pré-requisitos (recomendado):

- Python 3.12
- Node.js 20+ (ou a versão LTS instalada no seu ambiente)
- PostgreSQL 16
- Redis 7

### 1) Dependências do sistema (Debian/Ubuntu)

```bash
sudo apt update
sudo apt -y install python3.12 python3.12-venv python3-pip build-essential libpq-dev \
  postgresql redis-server
```

### 2) Banco e variáveis de ambiente

Crie `.env` e ajuste hosts/portas para “localhost”:

```bash
cp .env.example .env
```

No `.env`, use valores como:

- `POSTGRES_HOST=localhost`
- `REDIS_URL=redis://localhost:6379/0`
- `API_BASE_URL=http://localhost:8000`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

Crie o banco e usuário (exemplo):

```bash
sudo -u postgres psql -c "CREATE USER mhc WITH PASSWORD 'mhc';"
sudo -u postgres psql -c "CREATE DATABASE mhc_cloud_panel OWNER mhc;"
```

### 3) Backend (FastAPI)

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Worker (Celery)

Em outro terminal:

```bash
cd backend
source .venv/bin/activate
celery -A app.tasks.celery_app worker -l INFO -Q default
```

### 5) Frontend (Next.js)

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

Frontend: http://localhost:3000

## Proxmox Mock (Python)

O mock simula um subset da API do Proxmox VE em `/api2/json/*` e permite testar listagem de nodes/templates, provisionamento (clone/config) e ações (start/stop/reboot/status).

### Via Docker Compose

O `docker-compose.yml` já inclui o serviço `proxmox_mock` na porta `8001`.

Garanta no `.env`:

- `PROXMOX_HOST=http://proxmox_mock:8001`

E suba:

```bash
docker compose up --build
```

Teste rápido:

```bash
curl http://localhost:8001/api2/json/nodes
```

### Rodando standalone (sem Docker)

1. Instale dependências do backend (FastAPI/uvicorn) em um venv:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Suba o mock:

```bash
uvicorn proxmox_mock:app --reload --host 0.0.0.0 --port 8001
```

3. Configure o backend para usar o mock:

- `PROXMOX_HOST` precisa começar com `http://` (ex.: `http://localhost:8001`)

Teste rápido:

```bash
curl http://localhost:8001/api2/json/nodes
curl http://localhost:8001/api2/json/nodes/pve/qemu
curl http://localhost:8001/api2/json/cluster/nextid
```

## Testes com Proxmox real (criação de VM + DHCP + SSH)

Este modo valida o fluxo completo: clonar template Cloud-Init, aplicar `ciuser`, injetar `sshkeys`, subir a VM, obter IP via `qemu-guest-agent` e testar login por SSH.

Pré-requisitos no Proxmox (lab/staging):

- Template Cloud-Init (Ubuntu/Debian) com:
  - `openssh-server` ativo
  - `qemu-guest-agent` instalado e ativo
- Rede com DHCP
- API Token com permissões no escopo de testes (node/pool/storage)

### Rodar o teste de integração (via container do backend)

Defina as variáveis de ambiente e rode o pytest dentro do container:

```bash
export REAL_PROXMOX=true
export PROXMOX_HOST="https://IP_DO_PVE:8006"
export PROXMOX_USER="api-user"
export PROXMOX_REALM="pve"
export PROXMOX_TOKEN_NAME="token"
export PROXMOX_TOKEN_SECRET="secret"
export PROXMOX_VERIFY_SSL="false"
export TEST_PROXMOX_NODE="pve"
export TEST_TEMPLATE_VMID="9000"
export TEST_CIUSER="mendsec"

docker compose exec -T backend pytest -q -k real_proxmox
```

Observações:

- O teste está em `backend/app/tests/test_real_proxmox_ssh.py` e é skipado quando `REAL_PROXMOX` não está habilitado.
- O IP da VM é obtido via `qemu-guest-agent`. Se falhar, revise o template.

### Proxmox rodando atrás do NAT do libvirt (WSL + KVM)

Se o Proxmox estiver como uma VM no libvirt com NAT, é comum que a VM criada pelo Proxmox não seja acessível diretamente do host. Nesse caso, o teste pode conectar via “jump host” (SSH no Proxmox e tunnel até a VM).

Habilite o modo jump e informe credenciais de SSH para o Proxmox:

```bash
export TEST_SSH_VIA_JUMP=true
export TEST_JUMP_HOST="IP_DO_PROXMOX_VM_NO_LIBVIRT"
export TEST_JUMP_USER="root"
export TEST_JUMP_PASSWORD="SENHA_DO_ROOT_NO_PROXMOX_VM"
```

Alternativa (chave privada em PEM via env):

```bash
export TEST_SSH_VIA_JUMP=true
export TEST_JUMP_HOST="IP_DO_PROXMOX_VM_NO_LIBVIRT"
export TEST_JUMP_USER="root"
export TEST_JUMP_PRIVATE_KEY="$(cat ~/.ssh/id_rsa)"
```

### KVM/libvirt no Debian (WSL)

Exemplo de instalação do KVM/libvirt no Debian (WSL):

```bash
sudo apt update && sudo apt install qemu-system libvirt-daemon-system libvirt-clients
sudo adduser $USER libvirt
sudo adduser $USER kvm
lsmod | grep kvm
sudo systemctl enable --now libvirtd
```
