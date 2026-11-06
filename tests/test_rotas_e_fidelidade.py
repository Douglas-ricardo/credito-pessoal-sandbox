import contextlib
import io
import json
import os
import re
import unittest

from tests import RAIZ
from tests.helpers import servidor, requisicao_crua
import server

CONCEPTS = os.path.join(RAIZ, 'concepts')
ESTILOS = re.compile(r'<style\b[^>]*>.*?</style>', re.DOTALL | re.IGNORECASE)


def original(tela):
    with open(os.path.join(CONCEPTS, server.ROUTES[tela] + '.html'), encoding='utf-8') as f:
        return f.read()


class RotasEmModoSimulado(unittest.TestCase):
    def test_as_12_rotas_respondem_200_sem_avisos_de_patch(self):
        erro = io.StringIO()
        with contextlib.redirect_stderr(erro), servidor() as porta:
            self.assertEqual(len(server.ROUTES), 12)
            for tela in server.ROUTES:
                with self.subTest(tela=tela):
                    st, h, corpo = requisicao_crua(porta, caminho='/' if tela == 'index' else '/' + tela)
                    self.assertEqual(st, 200)
                    self.assertIn('text/html', h['content-type'])
                    self.assertIn('<div id="app">', corpo.decode('utf-8'))
        self.assertEqual(erro.getvalue(), '', 'nenhum padrão de patch deve faltar (nada no stderr)')

    def test_modo_simulado_e_avisado_na_tela_e_na_api(self):
        with servidor() as porta:
            self.assertEqual(json.loads(requisicao_crua(porta, caminho='/api/modo')[2]), {'real': False})
            html = requisicao_crua(porta, caminho='/valor')[2].decode('utf-8')
            self.assertIn('MODO SIMULADO', html)
            self.assertNotIn('SANDBOX CELCOIN', html)

    def test_modo_simulado_nao_chama_a_api(self):
        with servidor() as porta:
            for caminho in ('/api/solicitar', '/api/simular', '/api/solicitacoes', '/api/assinar', '/api/retentar'):
                with self.subTest(caminho=caminho):
                    self.assertEqual(requisicao_crua(porta, 'POST', caminho, corpo=b'{}')[0], 503)

    def test_rota_inexistente_responde_404(self):
        with servidor() as porta:
            self.assertEqual(requisicao_crua(porta, caminho='/nao-existe')[0], 404)


class FidelidadeDoDesenho(unittest.TestCase):
    def test_blocos_style_identicos_ao_original_em_todas_as_telas(self):
        """Prova que nenhum CSS do desenho foi alterado: os blocos <style> saem exatamente como entraram."""
        for tela in server.ROUTES:
            with self.subTest(tela=tela):
                antes = original(tela)
                depois = server.transform(antes, tela)
                blocos_antes, blocos_depois = ESTILOS.findall(antes), ESTILOS.findall(depois)
                self.assertGreater(len(blocos_antes), 0, 'o desenho deveria ter blocos <style>')
                self.assertEqual(blocos_antes, blocos_depois)

    def test_blocos_style_identicos_tambem_na_resposta_http(self):
        with servidor() as porta:
            for tela in server.ROUTES:
                with self.subTest(tela=tela):
                    servido = requisicao_crua(porta, caminho='/' if tela == 'index' else '/' + tela)[2].decode('utf-8')
                    self.assertEqual(ESTILOS.findall(original(tela)), ESTILOS.findall(servido))

    def test_o_html_do_desenho_servido_em_raw_e_identico_ao_arquivo(self):
        with servidor() as porta:
            for tela in server.ROUTES:
                with self.subTest(tela=tela):
                    self.assertEqual(requisicao_crua(porta, caminho='/raw/' + tela)[2].decode('utf-8'), original(tela))

    def test_markup_fora_do_script_nao_e_alterado(self):
        """Fora dos <script>, só o rodapé de aviso é acrescentado; o resto do HTML do desenho fica igual."""
        script = re.compile(r'<script\b[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE)
        banner = re.compile(r'<div style="position:fixed;bottom:0.*?</div>', re.DOTALL)
        for tela in server.ROUTES:
            with self.subTest(tela=tela):
                antes = script.sub('<script/>', original(tela))
                depois = banner.sub('', script.sub('<script/>', server.transform(original(tela), tela)), count=1)
                depois = depois.replace('<script/></body>', '</body>', 1)     # script do rodapé (salva o estado ao sair)
                self.assertEqual(antes, depois)


if __name__ == '__main__':
    unittest.main()
