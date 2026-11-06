# Crédito Pessoal Celcoin (sandbox)

App local de teste que serve as 12 telas do projeto "Douglas Credito" (Studio) ligadas à API de Crédito do **sandbox** da Celcoin.

## Aviso: só para sandbox local

- Este app é **somente para ambiente de teste, rodando na sua máquina**. Não serve para produção.
- **Não tem autenticação** e **não verifica de quem são os dados**: qualquer pessoa que consiga falar com o servidor consegue criar solicitações, assinar e listar solicitações de qualquer CPF informado.
- Por isso ele só atende em `127.0.0.1` e recusa qualquer requisição cujo cabeçalho `Host` não seja `localhost` ou `127.0.0.1` (proteção contra DNS rebinding). Não o exponha em rede, túnel ou proxy.
- O CPF nunca vai na URL do app: `/api/solicitacoes` recebe o CPF no corpo de um POST. (A API da Celcoin, porém, recebe o CPF na querystring em `GET /banking/originator/applications?taxpayer_id=`; isso é do lado deles.)
