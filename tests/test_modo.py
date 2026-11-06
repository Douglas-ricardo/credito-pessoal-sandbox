import os
import subprocess
import sys
import tempfile
import unittest

from tests import APP, RAIZ
import credit_client as C
import server

CONFIG_FICTICIA = {
    'CREDIT_CLIENT_ID': 'id-de-teste', 'CREDIT_CLIENT_SECRET': 'segredo-de-teste',
    'CREDIT_API_URL': 'https://sandbox.platform.exemplo.test', 'CREDIT_AUTH_URL': 'https://sandbox.auth.exemplo.test/oauth2/token',
    'CREDIT_PRODUCT_ID': '00000000-0000-0000-0000-000000000001',
}


def env_limpo(**extra):
    """Ambiente do subprocesso sem nenhuma variável CREDIT_* herdada (e sem apontar para o .env.local real)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('CREDIT_')}
    env.update(extra)
    return env


class ModoDoServidor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.inexistente = os.path.join(self.tmp.name, 'nao-existe.env')
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self._restaurar)

    def _restaurar(self):
        server.MODO, server.REAL = 'simulado', False
        C.API = C.AUTH = None
        C.ENV.clear()

    def _arquivo(self, conteudo):
        caminho = os.path.join(self.tmp.name, 'config.env')
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return caminho

    def test_sem_arquivo_e_sem_modo_segue_simulado(self):
        modo, _ = server.resolver_modo({}, self.inexistente)
        self.assertEqual(modo, 'simulado')

    def test_modo_simulado_explicito_ignora_arquivo(self):
        arq = self._arquivo('CREDIT_CLIENT_ID=lixo\n')
        modo, _ = server.resolver_modo({'CREDIT_MODE': 'simulado'}, arq)
        self.assertEqual(modo, 'simulado')

    def test_real_sem_configuracao_falha_em_vez_de_cair_em_simulado(self):
        with self.assertRaises(C.ConfigError) as cm:
            server.resolver_modo({'CREDIT_MODE': 'real'}, self.inexistente)
        self.assertIn('Modo real', str(cm.exception))
        self.assertIn('CREDIT_CLIENT_ID', str(cm.exception))

    def test_arquivo_presente_sem_modo_exige_real_valido(self):
        arq = self._arquivo('CREDIT_CLIENT_ID=so-um-campo\n')
        with self.assertRaises(C.ConfigError):
            server.resolver_modo({}, arq)

    def test_real_com_url_que_nao_e_sandbox_falha(self):
        cfg = dict(CONFIG_FICTICIA, CREDIT_MODE='real', CREDIT_API_URL='https://producao.exemplo.test')
        with self.assertRaises(C.ConfigError) as cm:
            server.resolver_modo(cfg, self.inexistente)
        self.assertIn('sandbox', str(cm.exception))

    def test_modo_invalido_falha(self):
        with self.assertRaises(C.ConfigError):
            server.resolver_modo({'CREDIT_MODE': 'talvez'}, self.inexistente)

    def test_real_valido_ativa_o_modo(self):
        server.configurar(dict(CONFIG_FICTICIA, CREDIT_MODE='real'), self.inexistente)
        self.assertTrue(server.REAL)
        self.assertEqual(server.MODO, 'real')

    def test_mensagem_de_erro_nao_vaza_segredo(self):
        cfg = dict(CONFIG_FICTICIA, CREDIT_MODE='real', CREDIT_API_URL='https://producao.exemplo.test')
        with self.assertRaises(C.ConfigError) as cm:
            server.resolver_modo(cfg, self.inexistente)
        self.assertNotIn('segredo-de-teste', str(cm.exception))

    def test_processo_real_sem_configuracao_nao_inicia(self):
        """CREDIT_MODE=real sem configuração: o processo sai com erro e não vira simulado."""
        r = subprocess.run([sys.executable, os.path.join(APP, 'server.py')], capture_output=True, text=True, timeout=30,
                           cwd=RAIZ, env=env_limpo(CREDIT_MODE='real', CREDIT_ENV_FILE=self.inexistente, PORT='0'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('ERRO de configuração', r.stderr)
        self.assertNotIn('modo simulado', r.stdout)

    def test_processo_sem_nada_inicia_em_simulado(self):
        p = subprocess.Popen([sys.executable, os.path.join(APP, 'server.py')], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, cwd=RAIZ, env=env_limpo(CREDIT_ENV_FILE=self.inexistente, PORT='0'))
        try:
            linha = p.stdout.readline()
        finally:
            p.kill()
            p.communicate()
        self.assertIn('modo simulado', linha)


if __name__ == '__main__':
    unittest.main()
