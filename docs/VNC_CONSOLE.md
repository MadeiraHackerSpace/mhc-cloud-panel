# Console Web VNC — Implementação

## Status: Backend completo ✅ | Frontend pendente ⏳

### O que foi implementado (Backend)

**1. Proxmox Service**
- Adicionado método `create_vnc_proxy(node, vmid)` que retorna `{ticket, port, upid}`
- Implementado em `ProxmoxerAdapter` (Proxmox real) e `HttpMockAdapter` (mock)

**2. API Endpoint**
- `GET /api/v1/vms/{vm_id}/vnc` → retorna `VNCProxyOut`
- Requer autenticação JWT
- Valida acesso por tenant
- Registra auditoria da ação

**3. Mock**
- Endpoint `/api2/json/nodes/{node}/qemu/{vmid}/vncproxy` no `proxmox_mock.py`
- Retorna ticket e porta mockados para testes

**4. Schema**
```python
class VNCProxyOut(APIModel):
    ticket: str
    port: int
    upid: str
```

### Como funciona o VNC no Proxmox

1. Cliente chama `GET /api/v1/vms/{vm_id}/vnc`
2. Backend chama Proxmox API `/nodes/{node}/qemu/{vmid}/vncproxy?websocket=1`
3. Proxmox retorna:
   - `ticket`: token de autenticação temporário
   - `port`: porta WebSocket do VNC (ex: 5900)
   - `upid`: ID da task
4. Cliente usa noVNC para conectar via WebSocket:
   - URL: `wss://{proxmox_host}:{port}/?vncticket={ticket}`
   - noVNC renderiza o console no browser

### Próximos passos (Frontend)

**1. Instalar noVNC**
```bash
npm install @novnc/novnc
```

**2. Criar componente `VNCConsole.tsx`**
- Recebe `vmId` como prop
- Chama `/api/v1/vms/{vmId}/vnc` para obter ticket
- Inicializa noVNC RFB client
- Conecta via WebSocket ao Proxmox

**3. Adicionar rota**
- `/dashboard/vps/{id}/console` → página com o console fullscreen
- Botão "Console" na página de detalhes da VM

**4. Configuração**
- Adicionar `NEXT_PUBLIC_PROXMOX_HOST` no `.env` para o frontend saber onde conectar
- Em produção, usar proxy reverso (nginx) para evitar CORS

### Exemplo de uso do noVNC

```typescript
import RFB from '@novnc/novnc/core/rfb';

const vnc = new RFB(
  canvasRef.current,
  `wss://${proxmoxHost}:${port}/?vncticket=${encodeURIComponent(ticket)}`
);

vnc.scaleViewport = true;
vnc.resizeSession = true;
```

### Considerações de segurança

- O ticket VNC expira rapidamente (padrão: 2 horas)
- Conexão é autenticada via ticket único
- WebSocket usa TLS (wss://) em produção
- Auditoria registra quem acessou o console

### Referências

- [Proxmox VE API - VNC Proxy](https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/vncproxy)
- [noVNC GitHub](https://github.com/novnc/noVNC)
- [noVNC npm package](https://www.npmjs.com/package/@novnc/novnc)
