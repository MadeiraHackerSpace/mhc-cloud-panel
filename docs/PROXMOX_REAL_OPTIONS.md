# Opções para Testar com Proxmox Real

O MHC Cloud Panel já está funcionando com o **mock do Proxmox** que simula a API completa. Para testar com Proxmox real, você tem estas opções:

## Opção 1: VirtualBox/VMware (Recomendado para testes)

### Passo 1: Baixar ISO do Proxmox

```bash
# Download da ISO oficial
https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso
```

### Passo 2: Criar VM no VirtualBox

- **CPU:** 2 cores (habilitar VT-x/AMD-V)
- **RAM:** 4GB mínimo
- **Disco:** 32GB
- **Rede:** Bridge ou NAT com port forwarding

### Passo 3: Instalar Proxmox

1. Boot pela ISO
2. Instalar Proxmox VE
3. Configurar IP estático
4. Anotar IP (ex: 192.168.1.100)

### Passo 4: Configurar API

Acesse via browser: `https://192.168.1.100:8006`

```bash
# Via SSH ou console
pveum user add mhc@pam
pveum passwd mhc@pam
# Senha: mhc123

pveum role add MHC_API -privs "VM.Allocate VM.Clone VM.Config.Disk VM.Config.CPU VM.Config.Memory VM.Config.Network VM.Config.Options VM.Monitor VM.Audit VM.PowerMgmt Datastore.AllocateSpace Datastore.Audit"

pveum aclmod / -user mhc@pam -role MHC_API

pveum user token add mhc@pam mhc-token --privsep 0
# Anote o token!
```

### Passo 5: Atualizar .env

```bash
PROXMOX_HOST=https://192.168.1.100:8006
PROXMOX_USER=mhc
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mhc-token
PROXMOX_TOKEN_SECRET=<token-gerado>
PROXMOX_VERIFY_SSL=false
NEXT_PUBLIC_PROXMOX_HOST=192.168.1.100
```

### Passo 6: Criar Template Cloud-Init

```bash
# No Proxmox
cd /var/lib/vz/template/cache
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

qm create 9000 --name ubuntu-22.04-cloudinit --memory 2048 --net0 virtio,bridge=vmbr0
qm importdisk 9000 jammy-server-cloudimg-amd64.img local-lvm
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0
qm set 9000 --ide2 local-lvm:cloudinit
qm set 9000 --boot c --bootdisk scsi0
qm set 9000 --serial0 socket --vga serial0
qm set 9000 --agent enabled=1
qm template 9000
```

## Opção 2: Hetzner Cloud (Produção)

### Vantagens
- ✅ Proxmox pré-instalado
- ✅ Hardware real com KVM
- ✅ ~€5/mês (CX22)
- ✅ IP público

### Passos

1. Criar conta em https://www.hetzner.com/cloud
2. Criar servidor com Proxmox (Apps)
3. Anotar IP público
4. Configurar firewall (porta 8006)
5. Seguir passos 4-6 da Opção 1

## Opção 3: Proxmox em Servidor Físico

Se você tem um servidor/PC antigo:

1. Boot pela ISO do Proxmox
2. Instalar em disco dedicado
3. Configurar rede
4. Seguir passos 4-6 da Opção 1

## Opção 4: Continuar com Mock (Desenvolvimento)

O mock já implementa:
- ✅ Todos os endpoints da API
- ✅ 2 nodes (pve, pve2)
- ✅ Templates mockados
- ✅ Status de VMs
- ✅ Operações (start/stop/reboot)
- ✅ Clone e provisionamento

**Limitações do mock:**
- ❌ VMs não são criadas de verdade
- ❌ Console VNC não conecta
- ❌ Sem métricas reais de CPU/RAM

## Comparação

| Opção | Custo | Complexidade | VMs Reais | Recomendado Para |
|-------|-------|--------------|-----------|------------------|
| Mock | Grátis | Baixa | ❌ | Desenvolvimento |
| VirtualBox | Grátis | Média | ✅ | Testes locais |
| Hetzner | €5/mês | Baixa | ✅ | Produção/Demo |
| Servidor Físico | Hardware | Alta | ✅ | Produção |

## Status Atual

Você já tem o mock funcionando! Para testar:

1. Acesse `http://localhost:3000/admin/infrastructure`
2. Veja os 2 nodes mockados
3. Crie um plano em `/admin/plans`
4. Contrate em `/dashboard/planos`
5. Acompanhe em `/admin/jobs`

## Próximos Passos Recomendados

1. **Agora:** Testar fluxo completo com mock
2. **Depois:** Instalar Proxmox em VirtualBox para testes reais
3. **Produção:** Migrar para Hetzner ou servidor dedicado

## Referências

- [Proxmox VE ISO Download](https://www.proxmox.com/en/downloads)
- [Proxmox VE Documentation](https://pve.proxmox.com/pve-docs/)
- [Hetzner Cloud](https://www.hetzner.com/cloud)
- [VirtualBox](https://www.virtualbox.org/)
