import os
import subprocess
import sys
import unittest

from tests import APP
import credit_client as C


class TravaSandbox(unittest.TestCase):
    def test_aceita_urls_de_sandbox(self):
        for url in ('https://sandbox.platform.flowfinance.com.br',
                    'https://sandbox.auth.flowfinance.com.br/oauth2/token',
                    'https://sandbox.platform.credit.celcoin.com.br/'):
            with self.subTest(url=url):
                self.assertTrue(C.validar_url_sandbox('X', url).startswith('https://'))

    def test_rejeita_o_que_nao_e_sandbox(self):
        ruins = {
            'sandbox só no caminho': 'https://evil.com/sandbox',
            'sandbox só na query': 'https://evil.com/?x=sandbox.exemplo.com',
            'http sem TLS': 'http://sandbox.platform.flowfinance.com.br',
            'sem esquema': 'sandbox.platform.flowfinance.com.br',
            'produção': 'https://platform.flowfinance.com.br',
            'label parecido, não igual': 'https://sandboxevil.com',
            'esquema ftp': 'ftp://sandbox.exemplo.com',
            'usuário na URL': 'https://sandbox.exemplo.com@producao.com',
            'vazia': '',
            'nula': None,
        }
        for nome, url in ruins.items():
            with self.subTest(caso=nome):
                with self.assertRaises(C.ConfigError):
                    C.validar_url_sandbox('CREDIT_API_URL', url)

    def test_mensagem_cita_o_campo(self):
        with self.assertRaises(C.ConfigError) as cm:
            C.validar_url_sandbox('CREDIT_AUTH_URL', 'https://evil.com/sandbox')
        self.assertIn('CREDIT_AUTH_URL', str(cm.exception))
        self.assertIn('sandbox', str(cm.exception))

    def test_configurar_rejeita_url_de_producao_e_campos_ausentes(self):
        base = {k: 'x' for k in C.CAMPOS_OBRIGATORIOS}
        base['CREDIT_API_URL'] = 'https://platform.flowfinance.com.br'
        base['CREDIT_AUTH_URL'] = 'https://sandbox.auth.flowfinance.com.br/oauth2/token'
        with self.assertRaises(C.ConfigError):
            C.configurar(base)
        with self.assertRaises(C.ConfigError) as cm:
            C.configurar({})
        self.assertIn('CREDIT_CLIENT_ID', str(cm.exception))

    def test_trava_continua_valendo_com_python_O(self):
        """O assert antigo sumia com -O; a validação nova levanta exceção de verdade."""
        codigo = ("import sys; sys.path.insert(0, sys.argv[1]); import credit_client as C\n"
                  "try:\n C.validar_url_sandbox('X','https://evil.com/sandbox'); print('ACEITOU')\n"
                  "except C.ConfigError: print('REJEITOU')")
        r = subprocess.run([sys.executable, '-O', '-c', codigo, APP], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), 'REJEITOU', r.stderr)


if __name__ == '__main__':
    unittest.main()
