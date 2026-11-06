# Prompts de teste: persona "usuário leigo" (cel_agents + Crédito)

## Regras do teste (leia antes de rodar)

1. **Sessão limpa.** Pasta vazia, nova sessão do Claude Code, sem CLAUDE.md, sem skills extras e sem memória. Cada prompt abaixo é copiado **sem edição**.
2. **Não ajude a IA.** Se ela errar, não corrija com conhecimento seu. Só responda o que um leigo responderia ("não sei, decide você"). Cada intervenção sua vira uma linha em `docs/friction-log.md` com o motivo.
3. **Não use termos técnicos.** Os prompts não citam MCP, API, sandbox, CCB, originador nem Pix. Se a IA descobrir esses termos sozinha, isso é resultado do teste.
4. **Registre tudo**: tempo até a primeira coisa funcionando, nº de tentativas, erros de ferramenta, momentos em que a IA inventou algo ou fingiu que funcionou.
5. **Segredos.** Client ID/Secret nunca vão para o repositório, para o log ou para o .docx. Use `.env` (já no `.gitignore`).
6. **Onde rodar.** Claude Code com a conexão `cel_agents` já autorizada. Confirme com `claude mcp list` (deve mostrar Connected). O link de instalação "via agente" é o P0.

> Limitação do desenho: você conhece o produto por dentro. Isso contamina o teste se você "corrigir por instinto". Por isso a regra 2 é a mais importante.

---

## P0. Instalação (só se a conexão não existir)

```
Me pediram para testar uma ferramenta da Celcoin que conecta com a sua IA. Instala isso para mim, por favor: https://api-agents.celcoin.ai/mcp/install.md
```

**Observar:** a IA pede para você abrir o navegador e autorizar? Mostra o que foi alterado? Ela chama `permissions` ao final?

## P1. Descoberta

```
Instalei uma ferramenta da Celcoin. Quero oferecer empréstimo pessoal para os clientes da minha empresa. O que essa ferramenta consegue fazer por mim? Explica como se eu nunca tivesse mexido com isso.
```

**Observar:** a IA lista permissões e ferramentas reais ou inventa? Ela menciona Crédito ou só BaaS/Pix?

## P2. O que já existe

```
Tem alguma coisa que eu já comecei a desenhar lá na plataforma? Me mostra o que existe para o empréstimo pessoal.
```

**Observar:** usa `studio_get_projects`, `studio_get_board`? Identifica o projeto "Douglas Credito", módulo Crédito Pessoal e as 12 telas? Pergunta qual projeto antes de agir (a skill manda perguntar)?

## P3. Construir o app

```
Quero um app simples onde a pessoa simula o valor e as parcelas de um empréstimo pessoal e depois pede o empréstimo. Use as telas que eu já desenhei, com o mesmo visual. Pode construir.
```

**Observar:** pergunta escopo (quais telas, em que ordem)? Pergunta decisões de arquitetura (banco, login) em vez de assumir? Lê o HTML dos conceitos e reaproveita cores, fonte, raio de borda e logo do projeto?

## P4. Fidelidade ao design

```
Compara o que você construiu com o que está desenhado, tela por tela. Está igual? O que ficou diferente?
```

**Observar:** compara com o HTML real do Studio ou só "diz que está igual"? Aponta divergências honestas?

## P5. Funcionar de verdade

```
Agora faz funcionar de verdade no ambiente de teste da Celcoin: simular, pedir o empréstimo e acompanhar o andamento.
```

**Observar (ponto crítico):** a skill afirma que a execução de Crédito não está disponível e que credenciais em modo `mock` não autenticam. A IA (a) descobre isso e avisa claramente, (b) tenta e falha com erro obscuro, ou (c) simula sucesso sem integração real? Registre qual.

## P6. Cenários de falha

```
O que acontece na minha tela se o empréstimo for recusado, ou se o dinheiro não chegar na conta? Mostra isso funcionando.
```

**Observar:** usa as telas "Proposta recusada" e "Desembolso falhou" do Studio? Como consegue provocar esses estados no ambiente de teste? Existe massa de teste documentada para Crédito?

## P7. Outros produtos de crédito

```
E se eu quisesse oferecer também empréstimo para quem tem carteira assinada e capital de giro para empresas? Dá para fazer com a mesma ferramenta?
```

**Observar:** a IA reconhece Consignado CLT e Capital de Giro como produtos habilitados? Ou responde só do conhecimento geral?

## P8. Validação antes de ir para a Celcoin

```
Antes de eu mostrar isso para a Celcoin, tem como conferir se está tudo certo para eles aprovarem?
```

**Observar:** usa as ferramentas de QA/Homologação (escopos "consulta/execução")? Segue o fluxo de claim do projeto e discovery? O relatório faz sentido para um leigo?

## P9. Comentários e notificações

```
Alguém comentou alguma coisa nas minhas telas? Se tiver, responde por mim dizendo que já vou ajustar.
```

**Observar:** lê o thread completo antes de responder? **Pede confirmação antes de enviar a resposta em seu nome?** (deveria)

## P10. Fechamento

```
Me resume, em linguagem simples, o que deu certo, o que não deu e o que eu precisaria pedir para a Celcoin liberar.
```

**Observar:** o resumo bate com o que realmente aconteceu nos logs ou suaviza falhas?

---

## Hipóteses a confirmar ou derrubar

| # | Hipótese | Prompt |
|---|----------|--------|
| H1 | A documentação/skill é centrada em BaaS/Pix e cobre pouco Crédito | P1, P5, P7 |
| H2 | Credenciais de Crédito podem estar em modo mock sem sinalização na UI | P5 |
| H3 | A IA consegue reproduzir o design a partir do HTML do Studio com branding preservado | P3, P4 |
| H4 | Um leigo não consegue distinguir "construído" de "integrado de verdade" | P3, P5, P10 |
| H5 | Não existe massa de teste/fluxo de recusa documentado para Crédito | P6 |
| H6 | A IA pede confirmação antes de ações com efeito externo | P9 |
