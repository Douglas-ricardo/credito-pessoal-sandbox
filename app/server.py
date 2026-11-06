"""Servidor local (somente biblioteca padrão). Serve as 12 telas do Studio (../concepts), ligadas à API de Crédito
do SANDBOX da Celcoin no modo real, ou com dados do protótipo no modo simulado.

Modo (variável CREDIT_MODE, do ambiente ou do .env.local):
  simulado  nenhuma chamada à Celcoin.
  real      exige configuração válida; se faltar algo o servidor NÃO inicia (não cai em simulado).
  (vazio)   sem .env.local → simulado; com .env.local → real.
"""
import datetime, json, os, re, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import credit_client as C
ConfigError = C.ConfigError
DIR = os.path.join(HERE, '..', 'concepts')
ROUTES = {'index': '00-ofertas', 'valor': '01-valor', 'vencimento': '02-vencimento', 'resumo': '03-resumo',
          'dados': '04-dados', 'preparando': '05-preparando', 'assinatura': '06-assinatura',
          'acompanhamento': '07-acompanhamento', 'liberado': '08-liberado', 'falhou': '09-falhou',
          'recusada': '10-recusada', 'solicitacoes': '11-solicitacoes'}
FUNDING_ID = 'f9405537-e99b-43d5-91fc-df23262c8cce'          # id do funding do sandbox (não é segredo)
MAGIC_PIX = '4ca519ef-0ccc-4c41-b58b-c88f1f47d8ab'            # chave Pix mágica de teste da documentação
TAXA_MES = 0.0299
MODO = 'simulado'
REAL = False


def resolver_modo(environ=None, env_file=None):
    """Decide o modo e valida a configuração. Retorna (modo, config). Levanta ConfigError, nunca cai em simulado por erro."""
    environ = os.environ if environ is None else environ
    env_file = env_file or environ.get('CREDIT_ENV_FILE') or C.ENV_FILE_PADRAO
    existe = os.path.isfile(env_file)
    arquivo = {}
    if existe:
        try:
            arquivo = C.load_env(env_file)
        except (OSError, UnicodeDecodeError) as e:
            raise ConfigError(f'Não consegui ler o arquivo de configuração ({type(e).__name__}).') from None
    pedido = (environ.get('CREDIT_MODE') or arquivo.get('CREDIT_MODE') or '').strip().lower()
    if pedido not in ('', 'real', 'simulado'):
        raise ConfigError(f'CREDIT_MODE inválido: "{pedido}". Use "real" ou "simulado".')
    if not pedido:
        pedido = 'real' if existe else 'simulado'
    if pedido == 'simulado':
        return 'simulado', {}
    cfg = {**arquivo, **{k: v for k, v in environ.items() if k.startswith('CREDIT_')}}
    try:
        C.configurar(cfg)
    except ConfigError as e:
        raise ConfigError(f'Modo real sem configuração válida: {e} (use CREDIT_MODE=simulado para rodar sem a API)') from None
    return 'real', cfg


def configurar(environ=None, env_file=None):
    """Aplica o modo ao estado do servidor. Levanta ConfigError se o modo real estiver mal configurado."""
    global MODO, REAL
    modo, _ = resolver_modo(environ, env_file)
    MODO, REAL = modo, modo == 'real'

STORE = ('var store = (function(){try{var j=sessionStorage.getItem("credito");if(j)return JSON.parse(j)}catch(e){}'
         'return{cfg:{},s:{}}})(); store.cfg=store.cfg||{}; store.s=store.s||{};')
PERSIST = 'function persist(){try{sessionStorage.setItem("credito",JSON.stringify(store))}catch(e){}}'
WATCH = ('BR.watch(function(st,x){ if(st==="ISSUED"){go("liberado");return true} '
         'if(st==="CANCELED"){S.res=(x&&x.descricao==="KYC_REJECTED")?"kyc":"recusada";go("recusada");return true} '
         'if(st==="DISBURSEMENT_ATTEMPT_FAILED"&&!(S.ignoraFalhaAte>Date.now())){go("falhou");return true} '
         'var ns=(st==="PENDING_DISBURSEMENT"||st==="PENDING_CASHOUT"||st==="SCHEDULED_DISBURSEMENT")?"desembolso":"instituicao"; '
         'if(ns!==seq[passo]&&seq.indexOf(ns)>=0){passo=seq.indexOf(ns);S.status=ns;estado();return true} return false; });')


def banner():
    t = ('SANDBOX CELCOIN — integração real com a API de Crédito (ambiente de teste)' if REAL
         else 'MODO SIMULADO — sem integração com a API de Crédito da Celcoin')
    return ('<div style="position:fixed;bottom:0;left:0;right:0;z-index:99999;background:#222;color:#fff;font:11px Inter,sans-serif;'
            'text-align:center;padding:3px;pointer-events:none">' + t + '</div>')


def transform(html):
    bridge = open(os.path.join(HERE, 'bridge.js'), encoding='utf-8').read()
    # a renomeação de sim() vem antes de inserir a ponte, que define o seu próprio sim()
    reps = [('function sim() {', 'function simLocal() {'),
            ('var store = { cfg: {}, s: {} };', STORE), ('function persist() {}', PERSIST), ('function go() {}', bridge),
            ('assinatura: "email"', 'assinatura: "mandato"'),
            # tela "Desembolso falhou": mostra o motivo real da Celcoin quando houver (o design só cobre "chave Pix não encontrada")
            ('alertBox("Chave Pix não encontrada", "Confira a chave cadastrada e tente de novo. Não há nova tentativa automática."',
             'alertBox(S.statusMsg ? "Falha na liberação do crédito" : "Chave Pix não encontrada", '
             'S.statusMsg ? S.statusMsg + " (retorno da Celcoin)" : "Confira a chave cadastrada e tente de novo. Não há nova tentativa automática."'),
            ('function after() { return 0; }', 'function after(ms, fn) { return setTimeout(fn, ms); }'),   # telas 05 e 07 desligam os timers
            # "Tentar de novo": retentativa real de desembolso (a Celcoin não retenta sozinha)
            ('handlers.tentar = function () { S.cenarioOk = true;',
             'handlers.tentar = function () { if (BR.ativo() && S.appId) { BR.retentar().then(function () { S.cenarioOk = true; S.status = "desembolso"; go("acompanhamento"); }, '
             'function (e) { var a = $("#aviso"); if (a) a.innerHTML = alertBox("Não foi possível tentar de novo", String(e.message || e), { destructive: true }); }); return; } S.cenarioOk = true;'),
            # "Minhas solicitações": lista real (BR.before carrega S.lista); sem integração, mantém os dados do protótipo
            ('var itens = (atual', 'var itens = S.lista ? S.lista : (atual'),
            ('handlers.next = function () {};', 'handlers.next = function () { go(nextAfterSim()); };'),
            ('handlers.back = function () {};', 'handlers.back = function () { go("index"); };'),
            ('function reset() { store.s = {}; S = store.s; }', 'function reset() { store.s = {}; S = store.s; persist(); }')]
    for old, new in reps:
        if old not in html and not old.startswith(('handlers.', 'function after', 'alertBox', 'var itens')):   # patches que só se aplicam a algumas telas
            print('padrão não encontrado:', old, file=sys.stderr)
        html = html.replace(old, new, 1)
    html = html.replace('PAGES[PAGE]();\n})();', 'BR.before(PAGE).then(function () { PAGES[PAGE](); });\n})();', 1)
    html = re.sub(r'after\(3800, function \(\) \{\s*passo\+\+;.*?\n    \}\);', lambda m: WATCH, html, count=1, flags=re.S)
    return html.replace('</body>', banner() + '<script>addEventListener("pagehide",function(){try{persist()}catch(e){}})</script></body>', 1)


def next_business_day(d):
    d += datetime.timedelta(days=1)
    while d.weekday() >= 5:
        d += datetime.timedelta(days=1)
    return d


def erro_api(st, js):
    return js if isinstance(js, str) else js.get('message', js)


def preview(valor, n, venc, borrower_id=None):
    body = {'interest_rate': TAXA_MES, 'first_payment_date': venc,
            'disbursement_date': next_business_day(datetime.date.today()).isoformat(),
            'finance_fee': 0, 'tac_amount': 0, 'requested_amount': round(float(valor), 2), 'num_payments': int(n),
            'schedule_type': 'MONTHLY', 'iof_type': 'PERSON'}
    if borrower_id:
        body['borrower_id'] = borrower_id
    st, js = C.call('POST', f"/banking/originator/products/{C.ENV['CREDIT_PRODUCT_ID']}/preview", body)
    if st != 200:
        raise ValueError(f'Simulação recusada ({st}): {erro_api(st, js)}')
    return js


def resumo_sim(js):
    return {'id': js['id'], 'valor': js['requested_amount'], 'n': js['num_periods'], 'parcela': js['payment_amount'],
            'total': js['total_amount_owed'], 'iof': js['iof_amount'],
            'cet': round(js['annual_effective_interest_rate'] * 100, 2), 'primeiroVenc': js['first_payment_date']}


STATUS_TELA = {'ISSUED': 'Liberado', 'CANCELED': 'Cancelada', 'DISBURSEMENT_ATTEMPT_FAILED': 'Desembolso falhou',
               'SIGNATURE_ERROR': 'Erro na assinatura', 'PENDING_SIGNATURE': 'Aguardando assinatura'}


def lista_item(a):
    d = a.get('loan_details') or {}
    return {'nome': 'Crédito Pessoal', 'valor': a['requested_amount'], 'n': a['num_payments'], 'parcela': d.get('payment_amount', 0),
            'status': STATUS_TELA.get(a['status'], 'Em andamento'), 'venc': a.get('first_payment_date'),
            'atual': a['status'] == 'ISSUED'}


def digits(s):
    return re.sub(r'\D', '', s or '')


def ensure_person(d):
    tel = digits(d.get('tel'))
    nasc = d.get('nasc', '').split('/')
    p = {'full_name': d['nome'], 'taxpayer_id': digits(d['cpf']), 'nationality': 'Brasileiro', 'email_address': d['email'],
         'occupation': d.get('prof') or 'Analista', 'birth_date': f'{nasc[2]}-{nasc[1]}-{nasc[0]}',
         'phone': {'country_code': '+55', 'area_code': tel[:2], 'number': tel[2:]},
         'pix': {'key': MAGIC_PIX, 'key_type': 'ALEATORY_KEY'}}           # sandbox: sempre a chave mágica
    if d.get('mae'):
        p['mothers_name'] = d['mae']
    if d.get('sexo') in ('MALE', 'FEMALE'):
        p['sex'] = d['sexo']
    st, js = C.call('POST', '/banking/originator/persons', p)
    if st in (200, 201):
        return js['id']
    st2, js2 = C.call('GET', f"/banking/originator/persons?taxpayer_id={p['taxpayer_id']}")
    items = js2 if isinstance(js2, list) else ((js2.get('content') or js2.get('items') or []) if isinstance(js2, dict) else [])
    if st2 == 200 and items:
        return items[0]['id']
    raise ValueError(f'Cadastro do tomador recusado ({st}): {erro_api(st, js)}')


def solicitar(b):
    preview(b['valor'], b['n'], b['venc'])                                # valida antes de cadastrar
    bid = ensure_person(b['dados'])
    sim = preview(b['valor'], b['n'], b['venc'], bid)
    st, a = C.call('POST', '/banking/originator/applications', {
        'product': {'id': C.ENV['CREDIT_PRODUCT_ID']}, 'borrower': {'id': bid}, 'funding': {'id': FUNDING_ID},
        'simulation_id': sim['id'], 'signature_provider': 'CELCOIN', 'signature_collect_method': 'NONE'})
    if st != 201:
        raise ValueError(f'Solicitação recusada ({st}): {erro_api(st, a)}')
    g = a
    for _ in range(20):                                                   # espera o contrato ser gerado
        time.sleep(2)
        st, g = C.call('GET', f"/banking/originator/applications/{a['id']}")
        if g['status'] != 'AGREEMENT_RENDERING':
            break
    if g['status'] == 'CANCELED':                                         # KYC embarcado reprovou (ou cancelada) → tela de recusa
        raise ValueError('KYC_REJECTED' if g.get('status_description') == 'KYC_REJECTED' else 'CANCELED')
    if g['status'] != 'PENDING_SIGNATURE':
        raise ValueError(f"Contrato não ficou pronto para assinatura (status {g['status']})")
    return {'appId': a['id'], 'borrowerId': bid, 'status': g['status'], 'simulacao': resumo_sim(sim)}


class H(BaseHTTPRequestHandler):
    def json(self, code, obj):
        self.send(code, json.dumps(obj, ensure_ascii=False).encode(), 'application/json; charset=utf-8')

    def send(self, code, body, ctype='text/html; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n) or b'{}')

    def do_GET(self):
        p = unquote(urlsplit(self.path).path).strip('/') or 'index'
        if p == 'api/modo':
            return self.json(200, {'real': REAL})
        if p.startswith('api/status/') and REAL:
            try:
                st, g = C.call('GET', f"/banking/originator/applications/{p.split('/')[-1]}")
                if st != 200:
                    return self.json(502, {'erro': f'HTTP {st}'})
                return self.json(200, {'status': g['status'], 'descricao': g.get('status_description')})
            except Exception as e:
                return self.json(502, {'erro': str(e)})
        if p == 'api/solicitacoes' and REAL:
            try:
                cpf = digits(parse_qs(urlsplit(self.path).query).get('cpf', [''])[0])
                st, g = C.call('GET', f'/banking/originator/applications?taxpayer_id={cpf}')
                if st != 200:
                    return self.json(502, {'erro': f'HTTP {st}'})
                return self.json(200, [lista_item(a) for a in g.get('content', [])][:10])
            except Exception as e:
                return self.json(502, {'erro': str(e)})
        if p.startswith('raw/') and p[4:] in ROUTES:          # HTML original do Studio, sem patches (usado na comparação de fidelidade)
            with open(os.path.join(DIR, ROUTES[p[4:]] + '.html'), encoding='utf-8') as fh:
                return self.send(200, fh.read().encode('utf-8'))
        if p == 'reset':
            return self.send(200, b'<script>sessionStorage.clear();location.href="/"</script>')
        if p.startswith('studio-fonts/'):
            self.send_response(302)
            self.send_header('Location', 'https://agents.celcoin.ai/' + p)
            self.end_headers()
            return
        f = ROUTES.get(p)
        if not f:
            return self.send(404, 'Tela não encontrada'.encode())
        with open(os.path.join(DIR, f + '.html'), encoding='utf-8') as fh:
            self.send(200, transform(fh.read()).encode('utf-8'))

    def do_POST(self):
        p = urlsplit(self.path).path.strip('/')
        if not REAL:
            return self.json(503, {'erro': 'Modo simulado'})
        try:
            b = self.body()
            if p == 'api/simular':
                return self.json(200, resumo_sim(preview(b['valor'], b['n'], b['venc'])))
            if p == 'api/solicitar':
                return self.json(200, solicitar(b))
            if p == 'api/retentar':
                st, r = C.call('POST', f"/banking/originator/applications/{b['appId']}/disbursement-attempts", {})
                if st not in (200, 201, 202):
                    return self.json(502, {'erro': f'Retentativa recusada ({st}): {erro_api(st, r)}'})
                return self.json(200, {'status': r.get('status')})
            if p == 'api/assinar':
                st, s = C.call('POST', f"/banking/originator/applications/{b['appId']}/signatures", {
                    'ip_address': self.client_address[0],
                    'signed_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'user_agent': self.headers.get('User-Agent', 'desconhecido'), 'person': {'id': b['borrowerId']}})
                if st != 200:
                    return self.json(502, {'erro': f'Assinatura recusada ({st})'})
                return self.json(200, {'ok': True})
            self.json(404, {'erro': 'rota inexistente'})
        except Exception as e:
            self.json(400, {'erro': str(e)})

    def log_message(self, *a):
        pass


def main():
    try:
        configurar()
    except ConfigError as e:
        print(f'ERRO de configuração: {e}', file=sys.stderr)
        sys.exit(2)
    port = int(os.environ.get('PORT', 3000))
    print(f'http://localhost:{port}  (modo {"SANDBOX real" if REAL else "simulado"})', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()


if __name__ == '__main__':
    main()
