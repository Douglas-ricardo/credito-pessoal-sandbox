import unittest
from unittest import mock

import credit_client as C
import server
from tests.test_modo import CONFIG_FICTICIA


class Configuracao(unittest.TestCase):
    def tearDown(self):
        C.API = C.AUTH = None
        C.ENV.clear()

    def test_campos_obrigatorios_sao_so_credenciais_urls_e_produto(self):
        self.assertEqual(set(C.CAMPOS_OBRIGATORIOS), {'CREDIT_CLIENT_ID', 'CREDIT_CLIENT_SECRET', 'CREDIT_API_URL',
                                                      'CREDIT_AUTH_URL', 'CREDIT_PRODUCT_ID'})
        C.configurar(dict(CONFIG_FICTICIA))      # sem funding nem taxa na configuração

    def test_id_de_produto_invalido(self):
        with self.assertRaises(C.ConfigError) as cm:
            C.configurar(dict(CONFIG_FICTICIA, CREDIT_PRODUCT_ID='123'))
        self.assertIn('CREDIT_PRODUCT_ID', str(cm.exception))

    def test_simulacao_usa_a_taxa_constante_do_desenho(self):
        C.configurar(dict(CONFIG_FICTICIA))
        resposta = {'id': 'x', 'requested_amount': 1000, 'num_periods': 6, 'payment_amount': 1, 'total_amount_owed': 6,
                    'iof_amount': 0, 'annual_effective_interest_rate': 0.1, 'first_payment_date': '2030-01-10'}
        with mock.patch.object(C, 'call', return_value=(200, resposta)) as chamada:
            server.preview(1000, 6, '2030-01-10')
        self.assertEqual(chamada.call_args.args[2]['interest_rate'], 0.0299)
        self.assertEqual(server.TAXA_MES, 0.0299)

    def test_solicitacao_usa_o_funding_do_sandbox(self):
        C.configurar(dict(CONFIG_FICTICIA))
        sim = {'id': 'sim', 'requested_amount': 1000, 'num_periods': 6, 'payment_amount': 1, 'total_amount_owed': 6,
               'iof_amount': 0, 'annual_effective_interest_rate': 0.1, 'first_payment_date': '2030-01-10'}
        enviados = []

        def falso(metodo, caminho, corpo=None):
            enviados.append((metodo, caminho, corpo))
            if caminho.endswith('/preview'):
                return 200, sim
            if caminho == '/banking/originator/persons':
                return 201, {'id': 'pessoa'}
            if caminho == '/banking/originator/applications':
                return 201, {'id': 'app'}
            return 200, {'status': 'PENDING_SIGNATURE'}

        dados = {'nome': 'Fulana', 'cpf': '000.000.000-00', 'nasc': '01/01/1990', 'email': 'f@x.test', 'tel': '(11) 90000-0000'}
        with mock.patch.object(C, 'call', side_effect=falso), mock.patch.object(server.time, 'sleep'):
            server.solicitar({'dados': dados, 'valor': 1000, 'n': 6, 'venc': '2030-01-10'})
        criacao = [c for c in enviados if c[1] == '/banking/originator/applications' and c[0] == 'POST'][0]
        self.assertEqual(criacao[2]['funding']['id'], server.FUNDING_ID)


if __name__ == '__main__':
    unittest.main()
