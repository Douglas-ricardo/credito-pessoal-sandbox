"""A ponte (bridge.js) não tem motor JS nos testes; aqui só se garante, por inspeção de texto, que não há fallback para o protótipo.
O comportamento é verificado no navegador."""
import os
import unittest

from tests import APP


def ponte():
    with open(os.path.join(APP, 'bridge.js'), encoding='utf-8') as f:
        return f.read()


class PonteSemPrototipo(unittest.TestCase):
    def test_falha_da_celcoin_mostra_erro_em_vez_de_dados_do_prototipo(self):
        js = ponte()
        self.assertIn('function erroBloqueante', js)
        self.assertGreaterEqual(js.count('erroBloqueante('), 3)      # definição + simulação + lista de solicitações

    def test_sem_fallback_silencioso(self):
        js = ponte()
        for resquicio in ('S.lista = null', 'S.realErro', '/api/modo', 'BR.ativo', 'BR.modo'):
            with self.subTest(resquicio=resquicio):
                self.assertNotIn(resquicio, js)

    def test_chamadas_vao_para_as_rotas_da_api(self):
        js = ponte()
        for rota in ('/api/simular', '/api/solicitar', '/api/solicitacoes', '/api/assinar', '/api/retentar', '/api/status/'):
            with self.subTest(rota=rota):
                self.assertIn(rota, js)


if __name__ == '__main__':
    unittest.main()
