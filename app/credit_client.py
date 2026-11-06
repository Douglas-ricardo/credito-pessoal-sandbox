"""Cliente da API de Crédito Celcoin — SOMENTE sandbox.

Não faz nada no import: a configuração é carregada de forma explícita com `configurar()`.
Nunca imprime segredos.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

ENV_FILE_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env.local')
TOKEN_PATHS = ['/oauth2/token', '/oauth/token', '/token', '/auth/token', '/connect/token']

# Estado do módulo, preenchido por configurar().
ENV = {}
API = AUTH = None
_tok = {'v': None, 'exp': 0, 'path': None}


class ConfigError(Exception):
    """Configuração ausente ou inválida."""


def load_env(path=None):
    """Lê um arquivo KEY=VALUE. Não imprime nem retorna nada além do dicionário."""
    path = path or ENV_FILE_PADRAO
    env = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"\'')
    return env


def validar_url_sandbox(nome, url):
    """Aceita apenas https cujo hostname tenha o label "sandbox" como parte do domínio.

    Levanta ConfigError com mensagem clara. Não usa `assert`, então continua valendo com `python -O`.
    Limitação conhecida: o label "sandbox" sozinho não impede um domínio de terceiros como
    sandbox.exemplo.com. TODO: decidir com a Celcoin uma lista de domínios permitidos.
    """
    if not url or not isinstance(url, str):
        raise ConfigError(f'{nome} ausente ou vazio.')
    try:
        partes = urllib.parse.urlsplit(url.strip())
        host = partes.hostname
    except ValueError as e:
        raise ConfigError(f'{nome} não é uma URL válida: {e}') from None
    if partes.scheme != 'https':
        raise ConfigError(f'{nome} precisa usar https (recebido: {partes.scheme or "sem esquema"}).')
    if not host:
        raise ConfigError(f'{nome} não tem hostname.')
    if partes.username is not None or partes.password is not None:
        raise ConfigError(f'{nome} não pode conter usuário ou senha na URL.')
    if 'sandbox' not in host.lower().split('.'):
        raise ConfigError(f'{nome} recusada: o hostname "{host}" não tem o label "sandbox". '
                          'Este cliente só fala com o ambiente de teste.')
    return url.strip().rstrip('/')


CAMPOS_OBRIGATORIOS = ('CREDIT_CLIENT_ID', 'CREDIT_CLIENT_SECRET', 'CREDIT_API_URL', 'CREDIT_AUTH_URL', 'CREDIT_PRODUCT_ID')


def configurar(env):
    """Valida `env` (dict) e ativa a configuração do cliente. Levanta ConfigError se algo faltar."""
    ausentes = [k for k in CAMPOS_OBRIGATORIOS if not (env.get(k) or '').strip()]
    if ausentes:
        raise ConfigError('Configuração ausente: ' + ', '.join(ausentes))
    global API, AUTH
    api = validar_url_sandbox('CREDIT_API_URL', env['CREDIT_API_URL'])
    auth = validar_url_sandbox('CREDIT_AUTH_URL', env['CREDIT_AUTH_URL'])
    ENV.clear()
    ENV.update(env)
    API, AUTH = api, auth
    _tok.update(v=None, exp=0, path=None)


def _req(method, url, body=None, headers=None, form=False):
    data = None
    if body is not None:
        data = urllib.parse.urlencode(body).encode() if form else json.dumps(body).encode()
    h = {'Accept': 'application/json', 'User-Agent': 'credit-agents-sandbox-test/0.1', **(headers or {})}
    if body is not None:
        h['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, h, method=method), timeout=30) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:300]


def token():
    if API is None:
        raise ConfigError('Cliente não configurado: chame configurar() antes.')
    if _tok['v'] and time.time() < _tok['exp'] - 30:
        return _tok['v']
    basic = base64.b64encode(f"{ENV['CREDIT_CLIENT_ID']}:{ENV['CREDIT_CLIENT_SECRET']}".encode()).decode()
    full = AUTH.split('//', 1)[1].count('/') > 0  # URL já inclui o caminho do token
    st = js = None
    for p in ([''] if full else ([_tok['path']] if _tok['path'] else TOKEN_PATHS)):
        st, js = _req('POST', AUTH + p, {'grant_type': 'client_credentials'}, {'Authorization': 'Basic ' + basic}, form=True)
        if st == 200 and isinstance(js, dict) and 'access_token' in js:
            _tok.update(v=js['access_token'], exp=time.time() + int(js.get('expires_in', 300)), path=p)
            return _tok['v']
    raise RuntimeError(f'Falha ao obter token (último status {st}: {str(js)[:200]})')


def call(method, path, body=None):
    return _req(method, API + path, body, {'Authorization': 'Bearer ' + token()})
