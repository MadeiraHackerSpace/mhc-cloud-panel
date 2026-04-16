# Proxmox VE no WSL2 (Debian) - Guia de Instalação

## Pré-requisitos

- Windows 10/11 com WSL2 habilitado
- Debian instalado no WSL2
- Pelo menos 4GB RAM disponível para o WSL
- Acesso de administrador no Windows

## Passo 1: Preparar o Debian no WSL

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y wget curl gnupg2 software-properties-common apt-transport-https ca-certificates
```

## Passo 2: Adicionar Repositório do Proxmox

```bash
# Adicionar chave GPG do Proxmox
wget https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg

# Adicionar repositório (versão no-subscription)
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" | sudo tee /etc/apt/sources.list.d/pve-install-repo.list

# Atualizar lista de pacotes
sudo apt update
```

## Passo 3: Instalar Proxmox VE (modo container)

**IMPORTANTE:** O Proxmox completo não roda no WSL devido a limitações do kernel. Vamos instalar apenas os componentes necessários para a API:

```bash
# Instalar componentes essenciais
sudo apt install -y proxmox-ve postfix open-iscsi

# Durante a instalação do postfix, escolha "Local only"
```

## Passo 4: Configurar Proxmox API

```bash
# Criar usuário para API
sudo pveum user add mhc@pam
sudo pveum passwd mhc@pam
# Digite uma senha (ex: mhc123)

# Criar role com permissões necessárias
sudo pveum role add MHC_API -privs "VM.Allocate VM.Clone VM.Config.Disk VM.Config.CPU VM.Config.Memory VM.Config.Network VM.Config.Options VM.Monitor VM.Audit VM.PowerMgmt Datastore.AllocateSpace Datastore.Audit"

# Atribuir role ao usuário
sudo pveum aclmod / -user mhc@pam -role MHC_API

# Criar token de API
sudo pveum user token add mhc@pam mhc-token --privsep 0
# Anote o token gerado!
```

## Passo 5: Configurar Storage e Templates

```bash
# Criar storage local para VMs
sudo mkdir -p /var/lib/vz/template/iso
sudo mkdir -p /var/lib/vz/template/cache

# Baixar template Cloud-Init (Ubuntu 22.04)
cd /var/lib/vz/template/cache
sudo wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# Criar VM template
sudo qm create 9000 --name ubuntu-22.04-cloudinit --memory 2048 --net0 virtio,bridge=vmbr0
sudo qm importdisk 9000 jammy-server-cloudimg-amd64.img local-lvm
sudo qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0
sudo qm set 9000 --ide2 local-lvm:cloudinit
sudo qm set 9000 --boot c --bootdisk scsi0
sudo qm set 9000 --serial0 socket --vga serial0
sudo qm set 9000 --agent enabled=1
sudo qm template 9000
```

## Passo 6: Iniciar Serviços

```bash
# Iniciar serviços do Proxmox
sudo systemctl start pvedaemon
sudo systemctl start pveproxy
sudo systemctl start pvestatd

# Verificar status
sudo systemctl status pvedaemon
sudo systemctl status pveproxy
```

## Passo 7: Configurar MHC Cloud Panel

### 7.1 Descobrir IP do WSL

```bash
# No WSL
ip addr show eth0 | grep inet
# Anote o IP (ex: 172.x.x.x)
```

### 7.2 Atualizar .env

No Windows, edite `C:\Kiro\mhc-cloud-panel\.env`:

```bash
# Proxmox Real (WSL)
PROXMOX_HOST=https://172.x.x.x:8006
PROXMOX_USER=mhc
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mhc-token
PROXMOX_TOKEN_SECRET=<token-gerado-no-passo-4>
PROXMOX_VERIFY_SSL=false
PROXMOX_TIMEOUT_SECONDS=30
PROXMOX_RETRY_TOTAL=3

# Frontend
NEXT_PUBLIC_PROXMOX_HOST=172.x.x.x
```

### 7.3 Reiniciar containers

```powershell
docker compose down
docker compose up -d
```

## Passo 8: Testar Conexão

### 8.1 Testar API do Proxmox

```bash
# No WSL
curl -k https://localhost:8006/api2/json/version
```

### 8.2 Testar do MHC Cloud Panel

```bash
# No Windows
docker compose exec backend python -c "
from app.integrations.proxmox.service import ProxmoxService
svc = ProxmoxService.from_settings()
print(svc.list_nodes())
"
```

## Troubleshooting

### Erro: "Connection refused"

```bash
# Verificar se pveproxy está rodando
sudo systemctl status pveproxy

# Verificar firewall
sudo iptables -L -n | grep 8006
```

### Erro: "SSL certificate verify failed"

Certifique-se de que `PROXMOX_VERIFY_SSL=false` está no `.env`

### Erro: "Authentication failure"

```bash
# Verificar token
sudo pveum user token list mhc@pam

# Recriar token se necessário
sudo pveum user token remove mhc@pam mhc-token
sudo pveum user token add mhc@pam mhc-token --privsep 0
```

### WSL não consegue acessar internet

```powershell
# No PowerShell (Windows)
wsl --shutdown
# Reinicie o WSL
```

## Limitações do Proxmox no WSL

⚠️ **O que NÃO funciona:**
- KVM/virtualização aninhada (VMs reais)
- Clustering
- Ceph storage
- HA (High Availability)

✅ **O que funciona:**
- API REST completa
- Gerenciamento de containers LXC
- Interface web (limitada)
- Autenticação e RBAC
- Storage local

## Alternativa: Usar Proxmox em VM

Se precisar de VMs reais, considere:

1. **VirtualBox/VMware:** Instalar Proxmox em VM com virtualização aninhada
2. **Proxmox em servidor físico:** Melhor opção para produção
3. **Hetzner Cloud:** Proxmox pré-instalado (~€5/mês)

## Próximos Passos

Após configurar o Proxmox:

1. Acesse `http://localhost:3000/admin/infrastructure`
2. Verifique se os nodes aparecem
3. Crie um plano em `/admin/plans`
4. Contrate um serviço em `/dashboard/planos`
5. Acompanhe o provisionamento em `/admin/jobs`

## Referências

- [Proxmox VE Documentation](https://pve.proxmox.com/pve-docs/)
- [Proxmox API Viewer](https://pve.proxmox.com/pve-docs/api-viewer/)
- [Cloud-Init Documentation](https://cloudinit.readthedocs.io/)
