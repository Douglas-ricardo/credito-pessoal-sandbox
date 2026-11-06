# Crédito Pessoal Celcoin (sandbox)

App local de teste que serve as 12 telas do módulo **Crédito Pessoal** do projeto "Douglas Credito" (Studio, cel_agents) ligadas à API de Crédito do **sandbox** da Celcoin: simular, pedir o empréstimo, assinar, acompanhar o status e tentar de novo quando o desembolso falha.

## Aviso: só para sandbox local

- Este app é **somente para ambiente de teste, rodando na sua máquina**. Não serve para produção.
- **Não tem autenticação** e **não verifica de quem são os dados**: qualquer pessoa que consiga falar com o servidor consegue criar solicitações, assinar e listar solicitações de qualquer CPF informado.
- Por isso ele só atende em `127.0.0.1` e recusa qualquer requisição cujo cabeçalho `Host` não seja `localhost` ou `127.0.0.1` (proteção contra DNS rebinding). Não o exponha em rede, túnel ou proxy.
- O cliente da API só aceita URLs `https` cujo hostname tenha o label `sandbox`. Mesmo assim, **não aponte para produção** e **não use dados reais de pessoas**.
- O CPF nunca vai na URL do app: `/api/solicitacoes` recebe o CPF no corpo de um POST. (A API da Celcoin, porém, recebe o CPF na querystring em `GET /banking/originator/applications?taxpayer_id=`; isso é do lado deles.)

## Requisitos

- **Python 3.8 ou superior**, apenas biblioteca padrão (nenhum `pip install`). Testado somente em **Python 3.12.10** no Windows; as versões 3.8 a 3.11 não foram testadas.

## Como rodar

### Modo simulado (sem credenciais)

```
python app/server.py
```

Abra `http://localhost:3000`. Sem `.env.local` e sem `CREDIT_MODE`, o app abre em modo simulado: as telas usam os dados do protótipo e nenhuma chamada externa é feita. Uma faixa preta no rodapé informa o modo.

### Modo real (sandbox da Celcoin)

1. Copie `.env.example` para `.env.local` e preencha todas as variáveis (`CREDIT_CLIENT_ID`, `CREDIT_CLIENT_SECRET`, `CREDIT_API_URL`, `CREDIT_AUTH_URL`, `CREDIT_PRODUCT_ID`, `CREDIT_FUNDING_ID`, `CREDIT_INTEREST_MONTHLY`). Nunca commite o `.env.local`.
2. Rode `python app/server.py` (ou `CREDIT_MODE=real python app/server.py`).
3. Se algo estiver ausente ou inválido, o servidor **não inicia** e diz o que falta; ele nunca cai sozinho em modo simulado. Para rodar sem a API, use `CREDIT_MODE=simulado`.

Para zerar a jornada no navegador: `http://localhost:3000/reset`.

### Testes

```
python -m unittest
```

Os testes não leem o `.env.local` nem chamam a Celcoin (usam arquivos temporários e chamadas simuladas).

## Estrutura

| Caminho | O que é |
|---|---|
| `concepts/` | HTML original das 12 telas exportado do Studio. **Não editar**: é o desenho de referência. |
| `app/server.py` | Servidor HTTP, modo (`CREDIT_MODE`), rotas `/api/*` e patches aplicados ao HTML em tempo de resposta. |
| `app/bridge.js` | Código injetado nas telas: navegação, estado, chamadas à API, travas de duplo clique. |
| `app/credit_client.py` | Cliente OAuth e HTTP da API de Crédito, validação de configuração e trava de sandbox. |
| `tests/` | Testes `unittest`. |
| `docs/` | Roteiro de teste (`PROMPTS.md`), registro de atritos (`friction-log.md`), `RESUMO.md`, `P1-descoberta.md`, `P4-fidelidade.md`. |
| `.env.example` | Modelo de configuração, sem valores. |

As telas do Studio são protótipos isolados (navegação e timers desligados). O servidor aplica patches só em JavaScript, com listas obrigatórias e opcionais por tela, e falha com erro claro se o HTML do Studio mudar. Os blocos `<style>` saem idênticos aos de `concepts/` (há teste para isso).

## Limitações conhecidas

- **Saldo do funding:** no sandbox usado, a conta de funding está sem saldo, então o desembolso falha ("Conta com saldo insuficiente") e nenhuma solicitação chegou a "Crédito liberado". Isso não foi testado de ponta a ponta.
- **Proposta recusada:** a tela aparece quando a solicitação vira `CANCELED` (inclusive `KYC_REJECTED`), mas uma reprovação real não foi provocada: não há massa de teste documentada. O texto da tela não distingue cancelamento manual de reprovação.
- **Solicitação duplicada:** a documentação da Celcoin não traz chave de idempotência para a API de Crédito. O app deduplica sozinho por (CPF, valor, parcelas, vencimento), **em memória e por 120 s** após o sucesso. Reiniciar o servidor ou rodar duas instâncias volta a permitir duplicidade.
- **Trava de sandbox:** exige https e o label `sandbox` no hostname, mas não restringe a uma lista de domínios da Celcoin (um domínio de terceiros com label `sandbox` passaria).
- **Assinatura:** usa cláusula mandato (a confirmação na tela assina pelo cliente). O texto jurídico da autorização está como `<PREENCHER>`, vindo do desenho.
- **Chave Pix:** o cadastro usa sempre a chave mágica de teste do sandbox, não a informada na tela.
- **Valores diferentes entre telas:** a tela de valor mostra uma estimativa sem IOF; o resumo mostra o valor real da simulação.
- **Cenários alternativos do desenho** (link expirado, KYC reprovado, sem conta, qualificação, desembolso agendado, assinatura por link ou biometria) não são exercitados.
- **Front sem testes automáticos:** não há motor JavaScript no ambiente de testes; `bridge.js` só é verificado por inspeção de texto e no navegador.
- **Polling do acompanhamento** no navegador tem intervalo fixo de 3,5 s.
