# Proxmox VE no Debian WSL — Quick Start

Este guia cobre a abordagem atual do projeto: Proxmox VE **instalado diretamente no Debian WSL2** (não em VM KVM), seguindo o [guia oficial da Proxmox para Debian 13 Trixie](https://pve.proxmox.com/wiki/Install_Proxmox_VE_on_Debian_13_Trixie).

## Pré-requisitos

- Windows 11 com WSL2 habilitado
- Debian Trixie (13) como distro WSL
- Proxmox VE já instalado no Debian WSL (seguindo o guia oficial)

## Verificar o estado atual

```bash
# No terminal do Debian WSL
wsl -d Debian -- bash scripts/check-status.sh
```

## Problemas comuns após instalação

### `pmxcfs` não inicia (`pve-cluster` falha)

Sintoma: `systemctl status pve-cluster` mostra `failed`.

Causa: o WSL gera `/etc/hosts` com o hostname apontando para `127.0.1.1` (loopback), mas o `pmxcfs` exige um IP não-loopback.

Correção:

```bash
# 1. Descobrir o IP real da interface eth0
ip addr show eth0 | grep 'inet '
# Exemplo de saída: inet 172.30.170.157/20

# 2. Corrigir o /etc/hosts (substitua pelo IP real)
sudo sed -i 's/127\.0\.1\.1/172.30.170.157/' /etc/hosts

# 3. Desabilitar geração automática do /etc/hosts pelo WSL
sudo bash -c "echo '[network]' >> /etc/wsl.conf"
sudo bash -c "echo 'generateHosts = false' >> /etc/wsl.conf"

# 4. Reiniciar o pve-cluster
sudo systemctl restart pve-cluster pvedaemon pveproxy
```

### `pveproxy` workers falham com erro de certificado SSL

Causa: os certificados ainda não foram gerados (ou foram gerados antes do `pve-cluster` estar saudável).

Correção:

```bash
sudo pvecm updatecerts --force
sudo systemctl restart pveproxy
```

### Testar se a API responde

```bash
# Dentro do WSL
curl -sk --max-time 10 https://127.0.0.1:8006/api2/json/version
# Esperado: HTTP 401 (precisa de autenticação) — é o comportamento correto

# Via pvesh (cliente local, não precisa de TLS)
sudo pvesh get /version
sudo pvesh get /nodes
```

## Criar usuário e token de API para o MHC

```bash
# Criar usuário
sudo pveum user add mhc@pam --comment "MHC Cloud Panel"

# Criar role com permissões
sudo pveum role add MHC_API -privs "VM.Allocate,VM.Clone,VM.Config.Disk,VM.Config.CPU,VM.Config.Memory,VM.Config.Network,VM.Config.Options,VM.Audit,VM.PowerMgmt,Datastore.AllocateSpace,Datastore.Audit"

# Atribuir role ao usuário
sudo pveum aclmod / -user mhc@pam -role MHC_API

# Criar token (anote o valor retornado)
sudo pveum user token add mhc@pam mhc-token --privsep 0
```

## Expor o Proxmox para os containers Docker

Os containers Docker rodam no Docker Desktop (Windows) em uma rede isolada e não alcançam o WSL diretamente. A solução é criar um port proxy no Windows que redireciona `0.0.0.0:8006` para o IP do WSL.

**Execute o PowerShell como Administrador:**

```powershell
# Substitua pelo IP real do WSL
.\scripts\setup-proxmox-portforward.ps1 -WslIp 172.30.170.157
```

Ou manualmente:

```powershell
netsh interface portproxy add v4tov4 listenport=8006 listenaddress=0.0.0.0 connectport=8006 connectaddress=<IP_WSL>
```

> **Nota:** o IP do WSL muda a cada boot. Execute o script novamente após reiniciar o Windows.

## Configurar o `.env`

Após criar o token, atualize o `.env` do projeto:

```env
PROXMOX_HOST=https://host.docker.internal:8006
PROXMOX_USER=mhc
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mhc-token
PROXMOX_TOKEN_SECRET=<uuid-do-token>
PROXMOX_VERIFY_SSL=false
PROXMOX_TIMEOUT_SECONDS=30
```

Reinicie os containers:

```bash
docker compose up -d
```

## Verificar integração

```bash
# Autenticar e testar o endpoint de nodes
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@mhc.local","password":"admin12345"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/proxmox/nodes
# Esperado: [{"node":"<hostname>","status":"online",...}]
```

Ou acesse http://localhost:3000/admin/infrastructure no navegador.

## Web UI do Proxmox

Com o port proxy ativo, a interface web está disponível em:

```
https://127.0.0.1:8006
Username: root@pam
```
