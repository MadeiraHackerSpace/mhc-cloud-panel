# Console VNC Web

## Como usar

1. Acesse a lista de VMs em `/dashboard/vps`
2. Clique em uma VM para ver os detalhes
3. Na seção "Console", clique em "Abrir Console VNC"
4. O console será aberto em tela cheia

## Configuração

### Variáveis de ambiente

Adicione no `.env`:

```bash
NEXT_PUBLIC_PROXMOX_HOST=localhost
```

Para produção, use o IP ou hostname do Proxmox:

```bash
NEXT_PUBLIC_PROXMOX_HOST=proxmox.example.com
```

### Desenvolvimento com Mock

O mock do Proxmox (`proxmox_mock.py`) retorna credenciais VNC mockadas. O console não funcionará de verdade, mas a interface será renderizada.

### Produção com Proxmox Real

1. Configure `PROXMOX_HOST` no backend para apontar para o Proxmox real
2. Configure `NEXT_PUBLIC_PROXMOX_HOST` no frontend com o mesmo host
3. Certifique-se de que o Proxmox está acessível via WebSocket na porta retornada pela API

## Arquitetura

```
Frontend (Browser)
  ↓ GET /api/vms/{id}/vnc
Next.js API Route
  ↓ GET /api/v1/vms/{id}/vnc (com JWT)
Backend (FastAPI)
  ↓ POST /nodes/{node}/qemu/{vmid}/vncproxy
Proxmox API
  ↓ retorna {ticket, port, upid}
Backend → Frontend
  ↓
noVNC Client (Browser)
  ↓ WebSocket wss://{proxmox_host}:{port}/?vncticket={ticket}
Proxmox VNC Server
```

## Segurança

- O ticket VNC expira em 2 horas (padrão do Proxmox)
- Cada acesso ao console gera um novo ticket
- A conexão WebSocket é autenticada via ticket
- Auditoria registra quem acessou o console

## Troubleshooting

### Console não conecta

1. Verifique se `NEXT_PUBLIC_PROXMOX_HOST` está correto
2. Verifique se o Proxmox está acessível na porta retornada
3. Verifique o console do navegador para erros WebSocket
4. Verifique se a VM está rodando

### Erro de CORS

Se estiver usando Proxmox em um domínio diferente, configure um proxy reverso (nginx) para evitar problemas de CORS.

### Ticket inválido

O ticket expira rapidamente. Se demorar muito para conectar, recarregue a página para obter um novo ticket.

## Componentes

- `components/VNCConsole.tsx` - Componente React com noVNC
- `app/dashboard/vps/[id]/console/page.tsx` - Página do console
- `app/api/vms/[vmId]/vnc/route.ts` - Proxy da API
- Backend: `app/api/v1/routes/vms.py` - Endpoint VNC

## Dependências

- `@novnc/novnc` - Cliente VNC para browser
- Proxmox VE com suporte a WebSocket VNC
