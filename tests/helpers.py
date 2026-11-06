"""Apoio dos testes: servidor local em thread e requisições HTTP cruas.

Os testes nunca chamam a Celcoin e nunca leem o .env.local: usam CONFIG_FICTICIA (URLs de sandbox falsas,
sem rede) e `mock.patch` nas chamadas à API.
"""
import contextlib
import socket
import threading
from http.server import ThreadingHTTPServer

import credit_client as C
import server

CONFIG_FICTICIA = {
    'CREDIT_CLIENT_ID': 'id-de-teste', 'CREDIT_CLIENT_SECRET': 'segredo-de-teste',
    'CREDIT_API_URL': 'https://sandbox.platform.exemplo.test', 'CREDIT_AUTH_URL': 'https://sandbox.auth.exemplo.test/oauth2/token',
    'CREDIT_PRODUCT_ID': '00000000-0000-0000-0000-000000000001',
}


def limpar_cliente():
    C.API = C.AUTH = None
    C.ENV.clear()


@contextlib.contextmanager
def servidor():
    """Sobe o servidor numa porta livre, com configuração fictícia válida (o cliente da API fica configurado, sem rede)."""
    C.configurar(dict(CONFIG_FICTICIA))
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.H)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()
        limpar_cliente()


def requisicao_crua(porta, metodo='GET', caminho='/', host='localhost', corpo=b'', headers_extra=None):
    """Envia a requisição sem normalizar nada (o caminho vai exatamente como passado).

    Retorna (status, {header_minusculo: valor}, corpo_bytes).
    """
    extra = ''.join(f'{k}: {v}\r\n' for k, v in (headers_extra or {}).items())
    req = (f'{metodo} {caminho} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n'
           f'Content-Length: {len(corpo)}\r\n{extra}\r\n').encode('latin-1') + corpo
    s = socket.create_connection(('127.0.0.1', porta), timeout=10)
    try:
        s.sendall(req)
        dados = b''
        while True:
            d = s.recv(65536)
            if not d:
                break
            dados += d
    finally:
        s.close()
    cab, _, resto = dados.partition(b'\r\n\r\n')
    linhas = cab.decode('latin-1').split('\r\n')
    status = int(linhas[0].split()[1])
    headers = {}
    for l in linhas[1:]:
        k, _, v = l.partition(':')
        headers[k.strip().lower()] = v.strip()
    return status, headers, resto
