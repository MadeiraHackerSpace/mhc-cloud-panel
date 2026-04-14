## O que esse PR resolve?

Descreva de forma clara e concisa o que esse PR altera no sistema.
- Fixes #<issue_number>
- Qual o impacto no modelo de negócio ou no fluxo de infraestrutura?

## Tipo de Mudança

- [ ] Correção de bug (mudança que não quebra compatibilidade e resolve um problema)
- [ ] Nova Funcionalidade (mudança que adiciona uma feature)
- [ ] Breaking change (correção ou feature que faria com que o comportamento existente não funcionasse mais como esperado, como mudanças na API)
- [ ] Refatoração/Documentação (apenas melhorias de código/docs, sem mudança de comportamento)

## Como isso foi testado?

Por favor, descreva os testes realizados localmente. Note que as automações do CI vão rodar os testes unitários (`pytest`), o `lint` e `typecheck` do Frontend.

- [ ] Provisionamento com Mock Server
- [ ] Provisionamento com Proxmox Real
- [ ] Teste via Postman / Bruno
- [ ] Teste via Navegador (Portal do Cliente / Painel Admin)

## Checklist para Revisão:

- [ ] Meu código segue o estilo do projeto (`npm run lint` / `flake8` / `black`).
- [ ] Realizei uma revisão do meu próprio código (self-review).
- [ ] Comentei meu código em áreas difíceis de entender.
- [ ] Adicionei ou atualizei a documentação correspondente (`docs/BACKEND.md`, etc.).
- [ ] Meus testes cobrem a mudança e passam localmente (`pytest`).
- [ ] Nenhuma credencial, token ou `.env` foi comitado acidentalmente.
