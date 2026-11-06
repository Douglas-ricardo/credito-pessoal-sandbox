# Friction log: preencher durante a execução

Uma linha por evento. Severidade: **B** bloqueou, **A** atrapalhou, **M** menor. Tipo: `UI`, `Docs`, `MCP`, `IA`, `Design`, `Permissão`.

## Resumo por prompt

| Prompt | Resultado (ok / parcial / falhou) | Tempo | Intervenções suas | Erros de ferramenta | A IA inventou algo? |
|--------|-----------------------------------|-------|-------------------|---------------------|---------------------|
| P0 |  |  |  |  |  |
| P1 |  |  |  |  |  |
| P2 |  |  |  |  |  |
| P3 |  |  |  |  |  |
| P4 |  |  |  |  |  |
| P5 | parcial: API real funciona por chamada direta; telas ainda não ligadas a ela | - | 3 (autorizar a chamada direta; preencher .env.local; corrigir AUTH_URL) | 6 (ver eventos) | não |
| P6 |  |  |  |  |  |
| P7 |  |  |  |  |  |
| P8 |  |  |  |  |  |
| P9 |  |  |  |  |  |
| P10 |  |  |  |  |  |

## Eventos

| Hora | Prompt | Tipo | Sev. | O que aconteceu | Resultado esperado por um leigo | Evidência (print/trecho mascarado) |
|------|--------|------|------|-----------------|---------------------------------|------------------------------------|
| 2026-11-06 | P5 | Permissão | B | `execute_cel_credit_sandbox_action` retornou "A execução no sandbox Celcoin está desativada" com cel_credit_sandbox_execute concedido em `permissions` | Permissão concedida deveria funcionar, ou `permissions` deveria indicar o desligamento | Mensagem do proxy |
| 2026-11-06 | P5 | Docs | A | Chamada direta bloqueada pelo Cloudflare (erro 1010) com o User-Agent padrão do Python; passou com User-Agent próprio | Doc avisar que o UA padrão é bloqueado | HTTP 403 "Error 1010" |
| 2026-11-06 | P5 | Docs | A | Doc de autenticação v5 exige mTLS e IP fixo; no sandbox bastou client_credentials com Basic em `/oauth2/token`, caminho que não aparece nas páginas lidas | Doc dizer qual é o fluxo do sandbox | Token obtido sem certificado |
| 2026-11-06 | P5 | Docs | A | `/preview` exige campos fora do exemplo da doc (`iof_type`, `schedule_type`, `num_payments`, `requested_amount`); `tac_rate` e `tac_amount` não coexistem; `interest_rate` é mensal, a doc diz anual | Exemplo da doc funcionar como está | Erros 400 de validação |
| 2026-11-06 | P5 | Docs | A | `/preview` devolve o id da simulação em `id`; `simulation_id` vem nulo, mas a criação da solicitação pede `simulation_id` | Campo com o nome documentado | Resposta do preview |
| 2026-11-06 | P5 | MCP | A | Solicitação com ZAPSIGN foi para `SIGNATURE_ERROR` no sandbox; CELCOIN e CLICKSIGN chegaram a `PENDING_SIGNATURE` | Doc indicar provedor funcional no sandbox | status da solicitação |
| 2026-11-06 | P5/P6 | MCP | A | Desembolso terminou em `DISBURSEMENT_ATTEMPT_FAILED`: "Conta com saldo insuficiente" (funding do sandbox sem saldo). Serve para a tela "Desembolso falhou", mas impede o caminho feliz | Funding com saldo ou instrução para carregar | disbursement_attempts da solicitação |

## O que funcionou bem

-

## Hipóteses (H1 a H6): confirmada / derrubada / inconclusiva

| # | Veredito | Evidência |
|---|----------|-----------|
| H1 |  |  |
| H2 |  |  |
| H3 |  |  |
| H4 |  |  |
| H5 |  |  |
| H6 |  |  |
