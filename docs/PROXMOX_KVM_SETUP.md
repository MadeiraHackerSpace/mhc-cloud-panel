# Setup Proxmox VE 9.0 em VM KVM no Debian WSL

Este guia descreve como configurar uma máquina virtual Proxmox VE 9.0 usando KVM/libvirt no Debian WSL, em vez de instalar diretamente no host.

## Pré-requisitos

- Debian Trixie (13) rodando no WSL
- KVM habilitado (verificado com `test -r /dev/kvm`)
- libvirt instalado
- ~50GB de espaço em disco disponível
- ~4GB de RAM disponível para a VM

## Verificar KVM

```bash
# Verificar se KVM está disponível
sudo -u libvirt-qemu test -r /dev/kvm && echo "✓ KVM disponível para leitura"
sudo -u libvirt-qemu test -w /dev/kvm && echo "✓ KVM disponível para escrita"

# Verificar se libvirtd está rodando
sudo systemctl status libvirtd
```

## Instalação de Dependências

```bash
# Instalar libvirt e ferramentas
sudo apt-get update
sudo apt-get install -y \
    libvirt-daemon-system \
    libvirt-clients \
    qemu-system-x86 \
    qemu-utils \
    virt-manager \
    virt-viewer \
    virt-install \
    wget

# Iniciar libvirtd
sudo systemctl start libvirtd
sudo systemctl enable libvirtd

# Adicionar usuário ao grupo libvirt (opcional, para não usar sudo)
sudo usermod -aG libvirt $USER
newgrp libvirt
```

## Criar VM Proxmox

### Opção 1: Usar o script automatizado

```bash
# Tornar script executável
chmod +x scripts/setup-proxmox-vm-kvm.sh

# Executar script (requer sudo)
sudo scripts/setup-proxmox-vm-kvm.sh
```

O script irá:
1. Baixar a ISO do Proxmox VE 9.0 (~800MB)
2. Criar um disco virtual de 50GB
3. Criar a VM com 4 CPUs e 4GB RAM
4. Iniciar a instalação

### Opção 2: Criar manualmente

```bash
# Baixar ISO
sudo mkdir -p /var/lib/libvirt/images
sudo wget -O /var/lib/libvirt/images/proxmox-ve-9.0.iso \
    https://enterprise.proxmox.com/iso/proxmox-ve_9.0-1.iso-20240906T120532Z

# Criar disco
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/proxmox-ve.qcow2 50G

# Criar VM
sudo virt-install \
    --name proxmox-ve \
    --memory 4096 \
    --vcpus 4 \
    --disk path=/var/lib/libvirt/images/proxmox-ve.qcow2,format=qcow2 \
    --cdrom /var/lib/libvirt/images/proxmox-ve-9.0.iso \
    --network network=default,model=virtio \
    --graphics vnc,listen=0.0.0.0 \
    --console pty,target_type=virtio \
    --boot cdrom,hd \
    --os-type linux \
    --os-variant debian12 \
    --noautoconsole
```

## Instalar Proxmox VE

### Conectar ao console VNC

```bash
# Opção 1: Usar virt-viewer (recomendado)
sudo virt-viewer proxmox-ve

# Opção 2: Obter display VNC
sudo virsh vncdisplay proxmox-ve
# Resultado: :0 (significa localhost:5900)
# Conectar com VNC client em localhost:5900
```

### Configuração durante a instalação

1. **Idioma**: Selecionar idioma (ex: English)
2. **Localização**: Selecionar localização
3. **Timezone**: Selecionar timezone
4. **Keyboard**: Selecionar layout de teclado
5. **Senha**: Definir senha para root
6. **Email**: Definir email para notificações
7. **Hostname**: `proxmox-ve`
8. **Network**:
   - IP Address: `192.168.122.100/24`
   - Gateway: `192.168.122.1`
   - DNS: `8.8.8.8` (ou seu DNS)
9. **Storage**: Selecionar disco (geralmente `/dev/vda`)
10. **Confirmar**: Revisar configurações e confirmar

A instalação levará ~10-15 minutos.

## Gerenciar VM

### Usar script de utilitários

```bash
# Tornar script executável
chmod +x scripts/proxmox-vm-utils.sh

# Exemplos de uso
sudo scripts/proxmox-vm-utils.sh status           # Ver status
sudo scripts/proxmox-vm-utils.sh start            # Iniciar VM
sudo scripts/proxmox-vm-utils.sh stop             # Parar VM
sudo scripts/proxmox-vm-utils.sh vnc              # Conectar VNC
sudo scripts/proxmox-vm-utils.sh get-ip           # Obter IP
sudo scripts/proxmox-vm-utils.sh test-connection  # Testar conectividade
sudo scripts/proxmox-vm-utils.sh info             # Ver informações
```

### Comandos virsh diretos

```bash
# Ver status
sudo virsh list --all

# Iniciar VM
sudo virsh start proxmox-ve

# Parar VM
sudo virsh shutdown proxmox-ve

# Forçar parada
sudo virsh destroy proxmox-ve

# Conectar console
sudo virsh console proxmox-ve

# Ver informações
sudo virsh dominfo proxmox-ve

# Ver IP
sudo virsh domifaddr proxmox-ve
```

## Configurar Proxmox para MHC Cloud Panel

### Opção 1: Script automatizado

```bash
# Tornar script executável
chmod +x scripts/configure-proxmox-vm.sh

# Executar (será solicitada a senha do root)
sudo scripts/configure-proxmox-vm.sh 192.168.122.100

# Ou fornecer senha como argumento
sudo scripts/configure-proxmox-vm.sh 192.168.122.100 sua-senha
```

O script irá:
1. Verificar conectividade
2. Autenticar no Proxmox
3. Criar token de API
4. Gerar arquivo `.env.proxmox`

### Opção 2: Configuração manual

#### 1. Acessar Proxmox Web UI

```
https://192.168.122.100:8006
```

- Username: `root@pam`
- Password: (senha definida na instalação)

#### 2. Criar token de API

1. Ir para **Datacenter** → **Permissions** → **API Tokens**
2. Clicar em **Add**
3. Configurar:
   - User: `root@pam`
   - Token ID: `mhc-token`
   - Privilege Separation: `0` (sem separação)
4. Clicar **Add**
5. Copiar o token exibido (será mostrado apenas uma vez)

#### 3. Configurar .env

Adicionar ao arquivo `.env`:

```bash
# Proxmox Configuration
PROXMOX_HOST=https://192.168.122.100:8006
PROXMOX_USER=root
PROXMOX_REALM=pam
PROXMOX_TOKEN_NAME=mhc-token
PROXMOX_TOKEN_SECRET=<token-copiado-acima>
PROXMOX_VERIFY_SSL=false

# Frontend
NEXT_PUBLIC_PROXMOX_HOST=192.168.122.100
```

## Testar Conexão

```bash
# Testar conectividade básica
ping 192.168.122.100

# Testar porta 8006
curl -k https://192.168.122.100:8006/api2/json/version

# Testar autenticação (substituir TOKEN)
curl -k -X POST https://192.168.122.100:8006/api2/json/access/ticket \
    -d "username=root@pam&password=sua-senha"
```

## Reiniciar Containers

Após configurar o `.env`:

```bash
# Reiniciar containers
docker compose restart

# Verificar logs
docker compose logs -f backend
```

## Snapshots

Criar snapshots para facilitar testes:

```bash
# Criar snapshot após instalação
sudo scripts/proxmox-vm-utils.sh snapshot pos-instalacao

# Criar snapshot após configuração
sudo scripts/proxmox-vm-utils.sh snapshot pos-configuracao

# Listar snapshots
sudo scripts/proxmox-vm-utils.sh list-snapshots

# Restaurar snapshot
sudo scripts/proxmox-vm-utils.sh restore-snapshot pos-instalacao
```

## Troubleshooting

### VM não inicia

```bash
# Verificar logs
sudo virsh log proxmox-ve

# Verificar espaço em disco
df -h /var/lib/libvirt/images

# Verificar permissões
ls -la /var/lib/libvirt/images/proxmox-ve.qcow2
```

### Sem conectividade de rede

```bash
# Verificar rede padrão
sudo virsh net-list

# Reiniciar rede
sudo virsh net-destroy default
sudo virsh net-start default

# Verificar interfaces
sudo virsh domifaddr proxmox-ve
```

### Proxmox não responde na porta 8006

```bash
# Conectar ao console e verificar serviços
sudo virsh console proxmox-ve

# Dentro da VM:
systemctl status pvedaemon
systemctl status pveproxy
systemctl status pvestatd
```

### Erro de autenticação

```bash
# Verificar credenciais
# Conectar ao console e resetar senha:
sudo virsh console proxmox-ve

# Dentro da VM:
passwd root
```

## Performance

Para melhor performance, considere:

1. **Aumentar RAM**: Editar VM para 8GB
   ```bash
   sudo virsh setmem proxmox-ve 8388608 --config
   ```

2. **Aumentar CPUs**: Editar VM para 8 CPUs
   ```bash
   sudo virsh setvcpus proxmox-ve 8 --config
   ```

3. **Usar storage rápido**: Colocar disco em SSD se possível

4. **Habilitar nested virtualization** (se suportado):
   ```bash
   sudo virsh edit proxmox-ve
   # Adicionar: <cpu mode='host-passthrough'/>
   ```

## Próximos Passos

1. ✅ VM Proxmox criada e rodando
2. ✅ Configuração de rede completa
3. ✅ Token de API criado
4. ⏭️ Testar integração com MHC Cloud Panel
5. ⏭️ Criar templates de VM
6. ⏭️ Configurar storage
7. ⏭️ Configurar backup

## Referências

- [Proxmox VE Documentation](https://pve.proxmox.com/wiki/Main_Page)
- [libvirt Documentation](https://libvirt.org/docs.html)
- [KVM/QEMU Documentation](https://www.qemu.org/documentation/)
