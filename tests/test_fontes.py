import unittest

from tests.helpers import servidor, requisicao_crua
import server


class RotaDeFontes(unittest.TestCase):
    def test_caminho_valido_redireciona(self):
        with servidor() as porta:
            st, h, _ = requisicao_crua(porta, caminho='/studio-fonts/Inter.woff2')
        self.assertEqual(st, 302)
        self.assertEqual(h['location'], 'https://agents.celcoin.ai/studio-fonts/Inter.woff2')

    def test_crlf_no_caminho_responde_400_e_nao_injeta_cabecalho(self):
        with servidor() as porta:
            st, h, _ = requisicao_crua(porta, caminho='/studio-fonts/x%0d%0aX-Teste:%201')
        self.assertEqual(st, 400)
        self.assertNotIn('x-teste', h)
        self.assertNotIn('location', h)

    def test_variantes_perigosas_respondem_400(self):
        ruins = ['/studio-fonts/..%2f..%2fetc', '/studio-fonts/a/../b', '/studio-fonts/x%0aY',
                 '/studio-fonts/a b', '/studio-fonts/x%00', '/studio-fonts/x%3Fa%3Db']
        with servidor() as porta:
            for c in ruins:
                with self.subTest(caminho=c):
                    st, h, _ = requisicao_crua(porta, caminho=c)
                    self.assertEqual(st, 400)
                    self.assertNotIn('location', h)

    def test_validador_recusa_quebra_de_linha_final(self):
        self.assertTrue(server.caminho_de_fonte_valido('studio-fonts/Inter.woff2'))
        self.assertFalse(server.caminho_de_fonte_valido('studio-fonts/Inter.woff2\n'))
        self.assertFalse(server.caminho_de_fonte_valido('studio-fonts/../x'))


if __name__ == '__main__':
    unittest.main()
