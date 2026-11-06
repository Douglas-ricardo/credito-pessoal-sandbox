import json
import os
import unittest
from unittest import mock

from tests import APP
from tests.helpers import servidor, requisicao_crua
import credit_client as C
import server

ITEM = {'requested_amount': 1000, 'num_payments': 6, 'status': 'ISSUED', 'first_payment_date': '2030-01-10',
        'loan_details': {'payment_amount': 190.5}}


class HostPermitido(unittest.TestCase):
    def test_aceita_localhost_e_127(self):
        with servidor() as porta:
            for host in ('localhost', 'localhost:3000', '127.0.0.1', '127.0.0.1:8080', 'LOCALHOST'):
                with self.subTest(host=host):
                    self.assertEqual(requisicao_crua(porta, caminho='/valor', host=host)[0], 200)

    def test_recusa_outros_hosts_em_get(self):
        ruins = ['evil.test', 'localhost.evil.test', '127.0.0.1.evil.test', '[::1]', 'localhost:abc', 'localhost@evil.test',
                 'evil.test:3000', '0.0.0.0', '']
        with servidor() as porta:
            for host in ruins:
                with self.subTest(host=host):
                    self.assertEqual(requisicao_crua(porta, caminho='/valor', host=host)[0], 403)

    def test_recusa_outros_hosts_em_post_e_nas_rotas_de_api(self):
        with servidor(modo_real=True) as porta:
            for caminho in ('/api/solicitar', '/api/solicitacoes', '/api/simular', '/api/assinar', '/api/retentar'):
                with self.subTest(caminho=caminho):
                    st, _, _ = requisicao_crua(porta, 'POST', caminho, host='evil.test', corpo=b'{}')
                    self.assertEqual(st, 403)
            self.assertEqual(requisicao_crua(porta, caminho='/api/modo', host='evil.test')[0], 403)
            self.assertEqual(requisicao_crua(porta, caminho='/studio-fonts/Inter.woff2', host='evil.test')[0], 403)


class CpfForaDaUrl(unittest.TestCase):
    def setUp(self):
        C.configurar({'CREDIT_CLIENT_ID': 'a', 'CREDIT_CLIENT_SECRET': 'b', 'CREDIT_API_URL': 'https://sandbox.exemplo.test',
                      'CREDIT_AUTH_URL': 'https://sandbox.exemplo.test/token', 'CREDIT_PRODUCT_ID': '00000000-0000-0000-0000-000000000001',
                      'CREDIT_FUNDING_ID': '00000000-0000-0000-0000-000000000002', 'CREDIT_INTEREST_MONTHLY': '0.0299'})
        self.addCleanup(lambda: (setattr(C, 'API', None), setattr(C, 'AUTH', None), C.ENV.clear()))

    def test_post_com_cpf_no_corpo_lista_solicitacoes(self):
        with mock.patch.object(C, 'call', return_value=(200, {'content': [ITEM]})) as chamada, servidor(modo_real=True) as porta:
            st, _, corpo = requisicao_crua(porta, 'POST', '/api/solicitacoes', corpo=json.dumps({'cpf': '529.982.247-25'}).encode(),
                                           headers_extra={'Content-Type': 'application/json'})
        self.assertEqual(st, 200)
        lista = json.loads(corpo)
        self.assertEqual(lista[0]['status'], 'Liberado')
        self.assertEqual(lista[0]['parcela'], 190.5)
        self.assertIn('taxpayer_id=52998224725', chamada.call_args.args[1])

    def test_get_com_cpf_na_url_e_recusado(self):
        with servidor(modo_real=True) as porta:
            st, _, _ = requisicao_crua(porta, 'GET', '/api/solicitacoes?cpf=52998224725')
        self.assertEqual(st, 405)

    def test_cpf_invalido_responde_400_sem_chamar_a_api(self):
        with mock.patch.object(C, 'call') as chamada, servidor(modo_real=True) as porta:
            for cpf in ('', '123', 'abc'):
                with self.subTest(cpf=cpf):
                    st, _, _ = requisicao_crua(porta, 'POST', '/api/solicitacoes', corpo=json.dumps({'cpf': cpf}).encode())
                    self.assertEqual(st, 400)
        chamada.assert_not_called()

    def test_ponte_nao_monta_url_com_cpf(self):
        with open(os.path.join(APP, 'bridge.js'), encoding='utf-8') as f:
            js = f.read()
        self.assertNotIn('?cpf=', js)
        self.assertIn('"/api/solicitacoes", { cpf:', js)


if __name__ == '__main__':
    unittest.main()
