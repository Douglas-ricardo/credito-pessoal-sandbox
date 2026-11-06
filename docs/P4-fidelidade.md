# P4: o app está igual ao desenho? (12 telas, uma a uma)

Método: cada tela foi aberta no navegador em duas versões, com o estado inicial zerado: a **original do Studio** (`/raw/<tela>`) e a **do app** (`/<tela>`). Comparei o texto visível, a quantidade de elementos e botões, e o estilo (cor, raio da borda, fonte). Além disso, medi quantas linhas os patches mudam em cada HTML.

## Resultado

| Tela | Texto | Estrutura | Estilo | Observação |
|---|---|---|---|---|
| 00 Ofertas | igual | igual | igual | |
| 01 Valor | igual | igual | igual | |
| 02 Primeiro vencimento | igual | igual | igual | |
| 03 Resumo | **diferente** | igual | igual | Mostra a simulação real (ex.: 20.000 em 6x = R$ 3.739,96) no lugar da estimativa do protótipo (R$ 3.690,73). Intencional. |
| 04 Conferência de dados | igual | igual | igual | |
| 05 Preparando o contrato | **diferente** | igual | igual | No original os timers estão desligados (tela parada na 1ª etapa); no app ela avança. Intencional. |
| 06 Assinatura | **diferente** | 49 x 44 elementos | igual | O app usa o modo **mandato** (checkbox + confirmar); o padrão do desenho é por e-mail. Escolha minha, não do design. |
| 07 Acompanhamento | igual | igual | igual | Com solicitação real, o status vem da Celcoin. |
| 08 Crédito liberado | igual | igual | igual | Nunca exibida com dado real (desembolso falha por falta de saldo). |
| 09 Desembolso falhou | igual | igual | igual | Com solicitação real, mostra o motivo devolvido pela Celcoin. |
| 10 Proposta recusada | igual | igual | igual | |
| 11 Minhas solicitações | **diferente** | 91 x 55 elementos | igual | Lista real, no lugar dos 3 itens de exemplo. Intencional. |

Placar: **8 telas idênticas**, 4 com diferença (todas por troca de dado fictício por real, ou por escolha do modo de assinatura). Nenhuma diferença de estilo.

Os patches alteram só o JavaScript (cerca de 82 a 90 linhas por tela, a maioria é a ponte com a API). **Nenhum HTML ou CSS do desenho foi alterado.**

## Divergências que o design em si tem

1. **Branding do projeto x HTML das telas:** o Studio guarda cor secundária `#49FADE` e raio de borda 16 px. O CSS das telas usa `#F3F3FA` e 12 px (o raio renderizado fica em 9,6 px). A cor primária (`#7664FA`) e a fonte (Inter) batem. Não há logo cadastrado no projeto.
2. **Textos `<PREENCHER>` no desenho:** termos legais, provedor de assinatura, prazos da análise, data de liberação. Continuam como estão.
3. **Tela de valor:** a estimativa não inclui IOF, então difere do resumo real (ex.: 8.000 em 12x: R$ 803,22 x R$ 820,68).
4. **Tela de falha:** o design só prevê "chave Pix não encontrada"; o app troca pelo motivo real quando existe.
5. **Tela "Proposta recusada":** diz "Não foi possível aprovar o crédito agora". Num cancelamento manual isso seria inverídico, e o app a usa também para esse caso. Falta um texto próprio para cancelamento.

## O que esta comparação não cobre

- Os **cenários alternativos** do desenho (link de assinatura expirado, KYC reprovado, sem conta, qualificação, desembolso agendado, assinatura por link ou biometria) não foram exercitados. O app fixa o padrão (`variante: preaprovada`, `vencimento: sim`, `dados: sim`, `kyc: embarcado`, `cenario: feliz`) e só troca a assinatura para mandato.
- A comparação é de **texto, estrutura e estilo computado**, não de pixels. Não fiz comparação visual por captura de tela.
- Cada tela foi aberta uma vez, no estado inicial. Telas que mudam com interação (folhas de parcelas e custos, validação de campos) não foram comparadas.
