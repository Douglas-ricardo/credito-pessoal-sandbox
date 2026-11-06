"""Servidor local (somente biblioteca padrão). Serve as 12 telas do Studio (../concepts)
com navegação entre telas e estado em sessionStorage.
Modo atual: SIMULADO. Integração com a API de Crédito: ver credit_client.py (precisa de .env)."""
import os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

DIR = os.path.join(os.path.dirname(__file__), '..', 'concepts')
ROUTES = {'index': '00-ofertas', 'valor': '01-valor', 'vencimento': '02-vencimento', 'resumo': '03-resumo',
          'dados': '04-dados', 'preparando': '05-preparando', 'assinatura': '06-assinatura',
          'acompanhamento': '07-acompanhamento', 'liberado': '08-liberado', 'falhou': '09-falhou',
          'recusada': '10-recusada', 'solicitacoes': '11-solicitacoes'}
STORE = ('var store = (function(){try{var j=sessionStorage.getItem("credito");if(j)return JSON.parse(j)}catch(e){}'
         'return{cfg:{},s:{}}})(); store.cfg=store.cfg||{}; store.s=store.s||{};')
PERSIST = 'function persist(){try{sessionStorage.setItem("credito",JSON.stringify(store))}catch(e){}}'
GO = 'function go(p){persist();location.href="/"+(p==="index"?"":p)}'
BANNER = ('<div style="position:fixed;bottom:0;left:0;right:0;z-index:99999;background:#222;color:#fff;font:11px Inter,sans-serif;'
          'text-align:center;padding:3px">MODO SIMULADO — sem integração com a API de Crédito da Celcoin</div>')

def transform(html):
    for old, new in (('var store = { cfg: {}, s: {} };', STORE), ('function persist() {}', PERSIST), ('function go() {}', GO),
                     ('function reset() { store.s = {}; S = store.s; }', 'function reset() { store.s = {}; S = store.s; persist(); }')):
        if old not in html:
            print('padrão não encontrado:', old, file=sys.stderr)
        html = html.replace(old, new, 1)
    return html.replace('</body>', BANNER + '<script>addEventListener("pagehide",function(){try{persist()}catch(e){}})</script></body>', 1)

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = unquote(urlsplit(self.path).path).strip('/') or 'index'
        if p == 'reset':
            return self.send(200, b'<script>sessionStorage.clear();location.href="/"</script>')
        if p.startswith('studio-fonts/'):
            self.send_response(302); self.send_header('Location', 'https://agents.celcoin.ai/' + p); self.end_headers(); return
        f = ROUTES.get(p)
        if not f:
            return self.send(404, 'Tela não encontrada'.encode())
        with open(os.path.join(DIR, f + '.html'), encoding='utf-8') as fh:
            self.send(200, transform(fh.read()).encode('utf-8'))
    def send(self, code, body):
        self.send_response(code); self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f'http://localhost:{port}'); ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
