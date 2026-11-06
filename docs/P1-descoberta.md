# O que essa ferramenta da Celcoin faz por você (explicação para quem nunca mexeu com isso)

Resposta ao prompt P1, baseada no que a conexão `cel_agents` mostrou de verdade em `permissions`, e não em suposição.

## Em uma frase

É uma ponte entre a sua IA e a plataforma da Celcoin, em **ambiente de teste**. Ela deixa a IA ver e editar as telas que você desenhou, ler a documentação da Celcoin e simular um empréstimo de mentira, sem mexer em dinheiro real.

## O que ela consegue fazer

| Quero... | Ferramenta | Liberada? |
|---|---|---|
| Ver os projetos e telas que desenhei | `studio_get_projects`, `studio_get_board` | Sim |
| Ler ou alterar o HTML de uma tela | `studio_get_board_concept_html`, `studio_replace_board_concept_html` | Sim |
| Ver comentários nas telas e responder | `studio_get_*_comments`, `studio_reply_to_comment` | Sim |
| Ler a documentação oficial da Celcoin | `search_` e `fetch_celcoin_documentation` | Sim |
| Pegar as chaves de teste de Crédito | `get_cel_credit_sandbox_credentials` | Sim |
| Executar chamadas de Crédito no teste | `execute_cel_credit_sandbox_action` | Concedida, **mas desativada no servidor** |
| Usar o sandbox de Pix, contas e outros produtos | `execute_celcoin_sandbox_action` | Sim |
| Validar o projeto antes de mostrar à Celcoin | ferramentas `qa_*` | Leitura e execução liberadas; criar roteiros exige perfil admin (não liberado) |
| Ler notificações da plataforma | `get_notifications` | **Não** |

## Sobre empréstimo pessoal

- A ferramenta **cobre Crédito**, não só Pix: o seu ambiente de teste tem instalados **Crédito Pessoal (CCB)**, **Crédito PJ (CCB)** e **Crédito do Trabalhador** (consignado CLT).
- Um empréstimo passa por: simular, cadastrar a pessoa, criar a solicitação, assinar o contrato (CCB) e receber o dinheiro por Pix.
- Você já tem um projeto desenhado: **Douglas Credito**, módulo **Crédito Pessoal**, com 12 telas (9 obrigatórias e 3 opcionais).

## O que ela não faz (ainda)

- Não movimenta dinheiro real: tudo é teste.
- A execução de Crédito pelo conector está desligada no servidor. Foi preciso chamar a API de teste diretamente, com a sua autorização.
- O desembolso (dinheiro na conta) depende de saldo na conta de funding do teste, que está vazio.
- O roteiro de validação (QA) da Celcoin não tem Crédito Pessoal; só o Crédito do Trabalhador.

## Termos, em português simples

- **Sandbox:** ambiente de testes da Celcoin, com dados de mentira.
- **CCB:** o contrato do empréstimo (Cédula de Crédito Bancário).
- **CET:** o custo total do empréstimo ao ano, com juros e impostos.
- **Funding:** a conta de onde sai o dinheiro emprestado.
- **Desembolso:** o momento em que o dinheiro cai na conta do cliente.
