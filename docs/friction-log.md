# Friction log: preencher durante a execução

Uma linha por evento. Severidade: **B** bloqueou, **A** atrapalhou, **M** menor. Tipo: `UI`, `Docs`, `MCP`, `IA`, `Design`, `Permissão`.

## Resumo por prompt

| Prompt | Resultado (ok / parcial / falhou) | Tempo | Intervenções suas | Erros de ferramenta | A IA inventou algo? |
|--------|-----------------------------------|-------|-------------------|---------------------|---------------------|
| P0 | ok (conexão já existia) | - | 0 | 0 | não |
| P1 | não executado (partiu direto para o projeto) | - | 0 | 0 | - |
| P2 | ok: projeto Douglas Credito, 12 telas | - | 0 | 0 | não |
| P3 | ok: app com as 12 telas navegáveis | - | 0 | 3 (go/persist/timers vazios) | não |
| P4 | parcial: divergências apontadas (parcela sem IOF, texto da falha) | - | 0 | 0 | não |
| P5 | parcial: jornada real até o desembolso; sem saldo no funding | - | 3 | 6 | não |
| P6 | parcial: falha de desembolso e retentativa reais; recusa não provocada | - | 0 | 1 | não |
| P7 | ok: 3 produtos instalados; só Pessoal testado | - | 0 | 0 | não |
| P8 | parcial: catálogo de QA não tem Crédito Pessoal | - | 0 | 0 | não |
| P9 | ok: sem comentários; notificações não liberadas | - | 0 | 0 | não |
| P10 | ok: docs/RESUMO.md | - | 0 | 0 | não |

## Eventos

| Hora | Prompt | Tipo | Sev. | O que aconteceu | Resultado esperado por um leigo | Evidência (print/trecho mascarado) |
|------|--------|------|------|-----------------|---------------------------------|------------------------------------|
| 2026-11-06 | P3 | Design | A | Os HTML do Studio são protótipos isolados: `go()` e `persist()` vazios, `handlers.next` vazio na tela de valor, e `after()` desativado nas telas "Preparando" e "Acompanhamento" (timers off) | Telas exportadas serem navegáveis ou documentarem o que falta ligar | Patches em `app/server.py` |
| 2026-11-06 | P4 | Design | A | Tela de valor estima parcela sem IOF (8.000 em 12x = R$ 803,22, CET 45,60%); a simulação real devolve R$ 820,68 e CET 48,41% | Mesmo número do início ao fim da jornada | Tela de valor x resumo |
| 2026-11-06 | P6 | Design | M | Tela "Desembolso falhou" só cobre "Chave Pix não encontrada"; o erro real do sandbox foi "saldo insuficiente" (problema do lado do funding, não do cliente) | Mensagem coerente com a causa real | Retorno da Celcoin na tela |
| 2026-11-06 | P5 | Permissão | B | `execute_cel_credit_sandbox_action` retornou "A execução no sandbox Celcoin está desativada" com cel_credit_sandbox_execute concedido em `permissions` | Permissão concedida deveria funcionar, ou `permissions` deveria indicar o desligamento | Mensagem do proxy |
| 2026-11-06 | P5 | Docs | A | Chamada direta bloqueada pelo Cloudflare (erro 1010) com o User-Agent padrão do Python; passou com User-Agent próprio | Doc avisar que o UA padrão é bloqueado | HTTP 403 "Error 1010" |
| 2026-11-06 | P5 | Docs | A | Doc de autenticação v5 exige mTLS e IP fixo; no sandbox bastou client_credentials com Basic em `/oauth2/token`, caminho que não aparece nas páginas lidas | Doc dizer qual é o fluxo do sandbox | Token obtido sem certificado |
| 2026-11-06 | P5 | Docs | A | `/preview` exige campos fora do exemplo da doc (`iof_type`, `schedule_type`, `num_payments`, `requested_amount`); `tac_rate` e `tac_amount` não coexistem; `interest_rate` é mensal, a doc diz anual | Exemplo da doc funcionar como está | Erros 400 de validação |
| 2026-11-06 | P5 | Docs | A | `/preview` devolve o id da simulação em `id`; `simulation_id` vem nulo, mas a criação da solicitação pede `simulation_id` | Campo com o nome documentado | Resposta do preview |
| 2026-11-06 | P5 | MCP | A | Solicitação com ZAPSIGN foi para `SIGNATURE_ERROR` no sandbox; CELCOIN e CLICKSIGN chegaram a `PENDING_SIGNATURE` | Doc indicar provedor funcional no sandbox | status da solicitação |
| 2026-11-06 | P5/P6 | MCP | A | Desembolso terminou em `DISBURSEMENT_ATTEMPT_FAILED`: "Conta com saldo insuficiente" (funding do sandbox sem saldo). Serve para a tela "Desembolso falhou", mas impede o caminho feliz | Funding com saldo ou instrução para carregar | disbursement_attempts da solicitação |

## O que funcionou bem

- App abre as 12 telas do Studio com o visual original e roda contra o sandbox real.
- Retentativa e lista de solicitações reais funcionam.

## Hipóteses (H1 a H6): confirmada / derrubada / inconclusiva

| # | Veredito | Evidência |
|---|----------|-----------|
| H1 | Confirmada | Índice do MCP e docs de Crédito cobrem pouco; QA sem Crédito Pessoal; endpoints só nas páginas públicas. |
| H2 | Derrubada | `mode` veio `live`, não mock. O bloqueio real foi a execução desativada no servidor, sinalizada só na hora de executar. |
| H3 | Confirmada | HTML do Studio reproduzido com branding preservado (cor, fonte Inter, raio); faltou só ligar navegação e timers. |
| H4 | Confirmada | Sem o aviso no rodapé, um leigo não distingue protótipo de integração real (a tela é idêntica nos dois modos). |
| H5 | Confirmada | Sem massa documentada para recusa de Crédito Pessoal; a única falha provocada foi por falta de saldo no funding. |
| H6 | Inconclusiva | Nenhum comentário para responder; não houve ação com efeito externo além do sandbox autorizado. |
