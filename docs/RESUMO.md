# Resumo do teste: Crédito Pessoal com a Celcoin (sandbox)

Data: 2026-11-06. Tudo foi feito no **ambiente de teste** da Celcoin. Nenhum dinheiro real foi movimentado.

## Como rodar

1. Copie suas credenciais do sandbox de Crédito para `.env.local` (esse arquivo não vai para o git):
   `CREDIT_CLIENT_ID`, `CREDIT_CLIENT_SECRET`, `CREDIT_API_URL`, `CREDIT_AUTH_URL`, `CREDIT_PRODUCT_ID`.
2. Rode `python app/server.py` e abra `http://localhost:3000`.
3. Sem configuração válida o servidor **não inicia** (não existe mais modo simulado); a faixa preta no rodapé lembra que é o sandbox.
4. Para zerar a jornada: `http://localhost:3000/reset`.

## O que deu certo

- As 12 telas do Studio rodam com a navegação ligada e o visual original.
- **Simulação real:** o resumo mostra parcela, total e CET calculados pela Celcoin (ex.: R$ 8.000 em 12x = R$ 820,68; CET 48,41% ao ano).
- **Pedido real:** o app cadastra o tomador, cria a solicitação e espera o contrato ficar pronto (cerca de 15 s).
- **Assinatura:** por cláusula mandato, com o aceite do cliente na tela.
- **Acompanhamento:** a tela segue o status real da solicitação.
- **Falha de desembolso:** a tela "Desembolso falhou" aparece de verdade, mostrando o motivo devolvido pela Celcoin.
- **Tentar de novo:** chama a retentativa de pagamento real (a Celcoin não retenta sozinha).
- **Minhas solicitações:** lista as solicitações reais do tomador.

## O que não deu certo (ou está pendente)

- **O dinheiro não chega:** a conta de funding do sandbox está sem saldo ("Conta com saldo insuficiente"). Por isso nenhuma solicitação chegou a "Crédito liberado". É preciso pedir à Celcoin para colocar saldo.
- **O MCP não executa em Crédito:** a ferramenta de execução está desativada no servidor, mesmo com a permissão concedida. Usamos a chamada direta à API do sandbox, com sua autorização.
- **Proposta recusada:** a tela aparece quando a solicitação vira `CANCELED` (testado cancelando uma solicitação de teste; o KYC reprovado também cai aqui). Uma **reprovação real não foi provocada**: não há CPF de teste documentado para isso. O texto da tela diz "não foi possível aprovar", o que não vale para cancelamento manual.
- **Parcela na tela de valor:** é uma estimativa sem IOF (R$ 803,22 para 8.000 em 12x). O resumo mostra o valor real (R$ 820,68).
- **Texto legal:** a autorização do mandato na tela de assinatura ainda está como `<PREENCHER>` (vem do design).
- **ZAPSIGN** deu erro de assinatura no sandbox. Usamos o provedor CELCOIN.
- **Notificações:** a ferramenta `get_notifications` não está liberada, então não foi possível ler notificações. Não há comentários nas telas.

## Documentos desta rodada

- `docs/P1-descoberta.md`: explicação da ferramenta para um leigo.
- `docs/P4-fidelidade.md`: comparação das 12 telas com o Studio.

## Outros produtos de crédito (P7)

O sandbox tem três produtos instalados: **Crédito Pessoal (CCB)**, **Crédito PJ (CCB)** e **Crédito do Trabalhador** (consignado CLT). Ou seja, dá para oferecer carteira assinada e capital de giro PJ com a mesma conexão, mas só o Crédito Pessoal foi testado aqui.

## Validação antes de mostrar à Celcoin (P8)

- O catálogo de QA tem 13 produtos e **nenhum é Crédito Pessoal**. O único de crédito é "Crédito do Trabalhador sem leilão". Logo, o roteiro oficial de QA não valida este produto.
- Não há projetos de QA abertos. Não criei nenhum, porque isso é uma ação que envia dados à Celcoin.

## O que pedir para a Celcoin liberar

1. Saldo na conta de funding do sandbox, para o desembolso concluir.
2. Reativar a execução de Crédito no MCP (`cel_credit_sandbox_execute`).
3. Um roteiro de QA para Crédito Pessoal (CCB) e massa de teste para proposta recusada.
4. Documentar o fluxo de autenticação do sandbox (`/oauth2/token`, sem mTLS) e os campos obrigatórios da simulação.

## Segurança

As credenciais apareceram uma vez no contexto da sessão (consulta ao MCP). Recomendo rotacioná-las ao terminar os testes.
