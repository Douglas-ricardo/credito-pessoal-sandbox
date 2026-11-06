"""Cliente da API de Crédito Celcoin — SOMENTE sandbox. Lê credenciais de .env.local (nunca imprime segredos)."""
import base64, json, os, time, urllib.request, urllib.error, urllib.parse

def load_env(path=None):
    path = path or os.path.join(os.path.dirname(__file__), '..', '.env.local')
    env = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1); env[k.strip()] = v.strip().strip('"\'')
    return env

ENV = load_env()
API, AUTH = ENV['CREDIT_API_URL'].rstrip('/'), ENV['CREDIT_AUTH_URL'].rstrip('/')
assert 'sandbox' in API and 'sandbox' in AUTH, 'Recusado: só URLs de sandbox'
TOKEN_PATHS = ['/oauth2/token', '/oauth/token', '/token', '/auth/token', '/connect/token']
_tok = {'v': None, 'exp': 0, 'path': None}

def _req(method, url, body=None, headers=None, form=False):
    data = None
    if body is not None:
        data = urllib.parse.urlencode(body).encode() if form else json.dumps(body).encode()
    h = {'Accept': 'application/json', 'User-Agent': 'credit-agents-sandbox-test/0.1', **(headers or {})}
    if body is not None: h['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, h, method=method), timeout=30) as r:
            raw = r.read().decode(); return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(); 
        try: return e.code, json.loads(raw)
        except Exception: return e.code, raw[:300]

def token():
    if _tok['v'] and time.time() < _tok['exp'] - 30: return _tok['v']
    basic = base64.b64encode(f"{ENV['CREDIT_CLIENT_ID']}:{ENV['CREDIT_CLIENT_SECRET']}".encode()).decode()
    full = AUTH.split('//', 1)[1].count('/') > 0  # URL já inclui o caminho do token
    for p in ([''] if full else ([_tok['path']] if _tok['path'] else TOKEN_PATHS)):
        st, js = _req('POST', AUTH + p, {'grant_type': 'client_credentials'}, {'Authorization': 'Basic ' + basic}, form=True)
        if st == 200 and isinstance(js, dict) and 'access_token' in js:
            _tok.update(v=js['access_token'], exp=time.time() + int(js.get('expires_in', 300)), path=p); return _tok['v']
    raise RuntimeError(f'Falha ao obter token (último status {st}: {str(js)[:200]})')

def call(method, path, body=None):
    return _req(method, API + path, body, {'Authorization': 'Bearer ' + token()})
