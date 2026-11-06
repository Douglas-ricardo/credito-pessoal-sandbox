import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from tests import RAIZ
from tests.helpers import servidor, requisicao_crua
import server

CONCEPTS = os.path.join(RAIZ, 'concepts')


def original(tela):
    with open(os.path.join(CONCEPTS, server.ROUTES[tela] + '.html'), encoding='utf-8') as f:
        return f.read()


def bridge():
    with open(os.path.join(server.HERE, 'bridge.js'), encoding='utf-8') as f:
        return f.read()


class PatchesFalhamAlto(unittest.TestCase):
    def test_as_12_telas_aplicam_todos_os_obrigatorios_sem_ruido(self):
        erro = io.StringIO()
        with contextlib.redirect_stderr(erro):
            for tela in server.ROUTES:
                with self.subTest(tela=tela):
                    server.transform(original(tela), tela)
        self.assertEqual(erro.getvalue(), '', 'transform() não deve escrever avisos no stderr')

    def test_obrigatorio_ausente_levanta_patcherror_com_o_nome_do_patch(self):
        for tela in server.ROUTES:
            obrigatorios, _ = server.patches_da_tela(tela)
            with self.subTest(tela=tela):
                with self.assertRaises(server.PatchError) as cm:
                    server.transform('<html><body></body></html>', tela)
                self.assertIn(f'Tela "{tela}"', str(cm.exception))
                for nome in obrigatorios - {'rodape'}:
                    self.assertIn(nome, str(cm.exception))

    def test_cada_patch_especifico_e_exigido_na_sua_tela(self):
        for tela, nomes in server.PATCHES_OBRIGATORIOS_POR_TELA.items():
            for nome in nomes:
                defs = dict(server._definicoes(bridge()))
                html = original(tela)
                antigo = {'after': 'function after() { return 0; }', 'next': 'handlers.next = function () {};',
                          'back': 'handlers.back = function () {};', 'itens': 'var itens = (atual',
                          'tentar': 'handlers.tentar = function () { S.cenarioOk = true;'}.get(nome)
                with self.subTest(tela=tela, patch=nome):
                    if antigo is None:                      # alerta_falha e watch: padrões longos, testados por trecho
                        antigo = {'alerta_falha': 'alertBox("Chave Pix não encontrada"', 'watch': 'after(3800, function () {'}[nome]
                    self.assertIn(antigo, html, 'a lista de obrigatórios diz que este trecho existe na tela')
                    quebrado = html.replace(antigo, 'TRECHO-REMOVIDO', 1)
                    with self.assertRaises(server.PatchError) as cm:
                        server.transform(quebrado, tela)
                    self.assertIn(nome, str(cm.exception))
                    self.assertIn(nome, defs)

    def test_opcional_ausente_nao_quebra(self):
        for tela in ('index', 'resumo', 'liberado'):
            _, opcionais = server.patches_da_tela(tela)
            self.assertEqual(opcionais, {'after', 'next', 'back'})
            server.transform(original(tela), tela)          # nenhum dos três existe nestas telas e não deve quebrar

    def test_listas_batem_com_o_html_atual_do_studio(self):
        """Patch que não é obrigatório nem opcional numa tela não pode ter o seu trecho lá (senão o design mudou)."""
        defs = server._definicoes(bridge())
        for tela in server.ROUTES:
            obrigatorios, opcionais = server.patches_da_tela(tela)
            html = original(tela)
            for nome, aplicar in defs:
                if nome in obrigatorios or nome in opcionais or nome == 'go':
                    continue
                with self.subTest(tela=tela, patch=nome):
                    self.assertFalse(aplicar(html)[1], f'o trecho do patch "{nome}" apareceu em "{tela}" sem estar na lista')

    def test_servidor_responde_500_claro_quando_o_html_do_studio_mudou(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, server.ROUTES['valor'] + '.html'), 'w', encoding='utf-8') as f:
                f.write('<html><body>sem os trechos esperados</body></html>')
            with mock.patch.object(server, 'DIR', tmp), contextlib.redirect_stderr(io.StringIO()), servidor() as porta:
                st, _, corpo = requisicao_crua(porta, caminho='/valor')
        self.assertEqual(st, 500)
        self.assertIn('Erro nos patches', corpo.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
