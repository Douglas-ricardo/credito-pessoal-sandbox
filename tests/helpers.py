"""Apoio dos testes: servidor local em thread (modo simulado) e requisições HTTP cruas."""
import contextlib
import socket
import threading
from http.server import ThreadingHTTPServer

import server


@contextlib.contextmanager
def servidor(modo_real=False):
    """Sobe o servidor numa porta livre. Por padrão em modo simulado (nenhuma chamada externa)."""
    antes = (server.MODO, server.REAL)
    server.MODO, server.REAL = ('real', True) if modo_real else ('simulado', False)
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.H)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()
        server.MODO, server.REAL = antes


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
