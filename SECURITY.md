# Política de Segurança

O MHC Cloud Panel leva a segurança a sério. Como este projeto é voltado para gerenciamento de infraestrutura (Proxmox VE) em ambientes de hackerspaces e laboratórios, é fundamental garantir que vulnerabilidades sejam tratadas de forma responsável.

## Versões Suportadas

Apenas a versão principal atual (`main` / última tag) recebe atualizações de segurança.

| Versão | Suportada          |
| -------| ------------------ |
| v0.1.x | :white_check_mark: |

## Como relatar uma vulnerabilidade

**Por favor, não abra uma issue pública para relatar uma vulnerabilidade de segurança.**

Se você encontrou uma falha crítica (ex: bypass de autenticação, vazamento de credenciais do Proxmox, injeção de SQL ou RCE no painel), siga estes passos:

1. Envie um e-mail para os mantenedores (verifique o perfil da organização no GitHub ou envie para `security@seudominio.local` - *ajuste este e-mail*).
2. Forneça uma descrição detalhada do problema, incluindo passos para reproduzir.
3. Aguarde nossa resposta. Tentaremos confirmar o recebimento em até 48 horas e fornecer um prazo para a correção.

## Práticas de Segurança do Projeto

- **Nunca** commitamos arquivos `.env` ou segredos (senhas, tokens de API).
- O token do Proxmox deve ter privilégios mínimos necessários (Role `PVEVMAdmin` ou similar) e nunca ser o usuário `root@pam`.
- Utilizamos JWT com expiração curta para Access Tokens e Refresh Tokens HTTP-only (em produção, sempre com a flag `Secure`).
- As rotas da API validam rigorosamente o escopo do usuário (RBAC) via dependências no FastAPI.
