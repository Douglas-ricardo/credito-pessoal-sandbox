/* Ponte entre as telas do Studio e a API (/api/*). Injetada pelo servidor no lugar de `function go() {}`.
   Nada aqui guarda segredos: as credenciais ficam só no servidor. */
var BR = (function () {
  var timer = null;
  function api(method, path, body) {
    return fetch(path, { method: method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.erro || ("HTTP " + r.status)); return j; }); });
  }
  function aplicarReal() { if (S.real) { try { CET_TXT = pct(S.real.cet) + " ao ano"; } catch (e) {} } }
  // Quando a Celcoin falha, mostra o erro em vez de cair em números ou itens do protótipo.
  // Usa o mesmo texto e o mesmo botão do erro de simulação do desenho (tela de valor). A promessa nunca resolve:
  // a tela original não é desenhada.
  function erroBloqueante(titulo, detalhe) {
    shell({ header: topbar("Seu crédito"),
      main: title(titulo, "Tente de novo em instantes. Se continuar, fale com o suporte.") + alertBox("Erro ao falar com a Celcoin", String(detalhe), { destructive: true }),
      footer: btn("Tentar de novo", { act: "recarregar" }) });
    handlers.recarregar = function () { location.reload(); };
    return new Promise(function () {});
  }
  return {
    before: function (page) {
      return Promise.resolve().then(function () {
        aplicarReal();
        if (page === "solicitacoes") {
          return api("POST", "/api/solicitacoes", { cpf: (S.dados && S.dados.cpf) || "" }).then(function (l) { S.lista = l; },
            function (e) { return erroBloqueante("Não conseguimos carregar os seus créditos", e.message || e); });
        }
        if (page !== "resumo") return;
        var l = simLocal(), key = l.valor.toFixed(2) + "|" + S.n + "|" + S.venc;
        if (S.real && S.real.key === key) return;
        return api("POST", "/api/simular", { valor: l.valor, n: S.n, venc: S.venc }).then(function (r) {
          r.key = key; S.real = r; persist(); aplicarReal();
        }, function (e) { return erroBloqueante("Não conseguimos simular agora", e.message || e); });
      });
    },
    solicitar: function () {
      var l = sim();
      return api("POST", "/api/solicitar", { dados: S.dados, end: S.end, conta: S.conta, valor: l.valor, n: S.n, venc: S.venc }).then(function (r) {
        S.appId = r.appId; S.borrowerId = r.borrowerId; S.real = Object.assign({ key: l.valor.toFixed(2) + "|" + S.n + "|" + S.venc }, r.simulacao); persist();
      });
    },
    retentar: function () {
      if (retentando) return Promise.reject(new Error("Já estamos tentando de novo. Aguarde um instante."));
      retentando = true; var liberar = bloquearBotoes();            // evita duplo clique
      return api("POST", "/api/retentar", { appId: S.appId }).then(function () { S.ignoraFalhaAte = Date.now() + 25000; persist(); })
        .then(function () { retentando = false; liberar(); }, function (e) { retentando = false; liberar(); throw e; });
    },
    assinar: function () {
      if (assinandoAgora) return Promise.reject(new Error("Assinatura já em andamento."));
      assinandoAgora = true;
      return api("POST", "/api/assinar", { appId: S.appId, borrowerId: S.borrowerId }).then(function () { assinandoAgora = false; S.assinadoReal = true; persist(); },
        function (e) { assinandoAgora = false; throw e; });
    },
    watch: function (fn) {
      clearTimeout(timer);
      (function tick() {
        timer = setTimeout(function () {
          api("GET", "/api/status/" + S.appId).then(function (s) { S.statusReal = s.status; S.statusMsg = s.descricao; persist(); if (!fn(s.status, s)) tick(); }, function () { tick(); });
        }, 3500);
      })();
    }
  };
})();
// Flags só em memória (nunca persistir): impedem ações duplicadas enquanto uma chamada está em andamento.
var criandoAgora = false, assinandoAgora = false, retentando = false;
// Desabilita os botões da tela enquanto uma ação está em andamento. Retorna a função que os reabilita.
function bloquearBotoes() {
  var els = Array.prototype.slice.call(document.querySelectorAll("button, [role=button]"));
  var antes = els.map(function (b) { return b.disabled; });
  els.forEach(function (b) { b.disabled = true; b.setAttribute("aria-disabled", "true"); });
  return function () { els.forEach(function (b, i) { b.disabled = antes[i]; if (!antes[i]) b.removeAttribute("aria-disabled"); }); };
}
function go(p) {
  var destino = function (q) { persist(); location.href = "/" + (q === "index" ? "" : q); };
  if (PAGE === "preparando" && (p === "assinatura" || p === "recusada") && !S.appId) {
    if (criandoAgora) return; criandoAgora = true; bloquearBotoes();
    return BR.solicitar().then(function () { criandoAgora = false; destino("assinatura"); },
      function (e) { criandoAgora = false; S.res = /KYC_REJECTED/.test(String(e.message || e)) ? "kyc" : "recusada"; S.motivoReal = String(e.message || e); destino("recusada"); });
  }
  if (PAGE === "assinatura" && p === "acompanhamento" && S.appId && !S.assinadoReal) {
    if (assinandoAgora) return; bloquearBotoes();
    return BR.assinar().then(function () { destino(p); }, function (e) { S.res = "recusada"; S.motivoReal = String(e.message || e); destino("recusada"); });
  }
  destino(p);
}
function sim() {
  var l = simLocal();
  if (S.real && S.real.key === l.valor.toFixed(2) + "|" + S.n + "|" + S.venc) return { n: S.real.n, valor: S.real.valor, parcela: S.real.parcela, total: S.real.total };
  return l;
}
