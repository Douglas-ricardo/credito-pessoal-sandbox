import unittest
from unittest import mock

import credit_client as C
import server
from tests.test_modo import CONFIG_FICTICIA


class ConfiguracaoObrigatoria(unittest.TestCase):
    def tearDown(self):
        C.API = C.AUTH = None
        C.ENV.clear()

    def test_funding_e_taxa_sao_obrigatorios(self):
        for campo in ('CREDIT_FUNDING_ID', 'CREDIT_INTEREST_MONTHLY'):
            with self.subTest(campo=campo):
                cfg = {k: v for k, v in CONFIG_FICTICIA.items() if k != campo}
                with self.assertRaises(C.ConfigError) as cm:
                    C.configurar(cfg)
                self.assertIn(campo, str(cm.exception))

    def test_valores_invalidos(self):
        ruins = [('CREDIT_INTEREST_MONTHLY', 'abc'), ('CREDIT_INTEREST_MONTHLY', '0'), ('CREDIT_INTEREST_MONTHLY', '2.99'),
                 ('CREDIT_FUNDING_ID', 'nao-e-uuid'), ('CREDIT_PRODUCT_ID', '123')]
        for campo, valor in ruins:
            with self.subTest(campo=campo, valor=valor):
                with self.assertRaises(C.ConfigError) as cm:
                    C.configurar(dict(CONFIG_FICTICIA, **{campo: valor}))
                self.assertIn(campo, str(cm.exception))

    def test_aceita_virgula_decimal(self):
        self.assertAlmostEqual(C.taxa_mensal({'CREDIT_INTEREST_MONTHLY': '0,0299'}), 0.0299)

    def test_simulacao_usa_a_taxa_configurada(self):
        C.configurar(dict(CONFIG_FICTICIA, CREDIT_INTEREST_MONTHLY='0.0123'))
        resposta = {'id': 'x', 'requested_amount': 1000, 'num_periods': 6, 'payment_amount': 1, 'total_amount_owed': 6,
                    'iof_amount': 0, 'annual_effective_interest_rate': 0.1, 'first_payment_date': '2030-01-10'}
        with mock.patch.object(C, 'call', return_value=(200, resposta)) as chamada:
            server.preview(1000, 6, '2030-01-10')
        corpo = chamada.call_args.args[2]
        self.assertEqual(corpo['interest_rate'], 0.0123)

    def test_solicitacao_usa_o_funding_configurado(self):
        C.configurar(dict(CONFIG_FICTICIA, CREDIT_FUNDING_ID='11111111-1111-1111-1111-111111111111'))
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
        self.assertEqual(criacao[2]['funding']['id'], '11111111-1111-1111-1111-111111111111')


if __name__ == '__main__':
    unittest.main()
