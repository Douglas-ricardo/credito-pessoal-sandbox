"""Configuração do servidor: não existe modo simulado; sem configuração válida o servidor não inicia."""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest

from tests import APP, RAIZ
from tests.helpers import CONFIG_FICTICIA, limpar_cliente
import credit_client as C
import server


def env_limpo(**extra):
    """Ambiente do subprocesso sem nenhuma variável CREDIT_* herdada (e sem apontar para o .env.local real)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('CREDIT_')}
    env.update(extra)
    return env


class ConfiguracaoDoServidor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.inexistente = os.path.join(self.tmp.name, 'nao-existe.env')
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(limpar_cliente)

    def _arquivo(self, conteudo):
        caminho = os.path.join(self.tmp.name, 'config.env')
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return caminho

    def test_nao_ha_mais_modo_simulado_no_codigo(self):
        for nome in ('MODO', 'REAL', 'resolver_modo'):
            self.assertFalse(hasattr(server, nome), f'server.{nome} não deveria existir')

    def test_sem_arquivo_e_sem_variaveis_falha(self):
        with self.assertRaises(C.ConfigError) as cm:
            server.configurar({}, self.inexistente)
        self.assertIn('CREDIT_CLIENT_ID', str(cm.exception))
        self.assertIn('.env.local', str(cm.exception))

    def test_arquivo_incompleto_falha(self):
        arq = self._arquivo('CREDIT_CLIENT_ID=so-um-campo\n')
        with self.assertRaises(C.ConfigError) as cm:
            server.configurar({}, arq)
        self.assertIn('CREDIT_CLIENT_SECRET', str(cm.exception))

    def test_url_que_nao_e_sandbox_falha(self):
        cfg = dict(CONFIG_FICTICIA, CREDIT_API_URL='https://producao.exemplo.test')
        with self.assertRaises(C.ConfigError) as cm:
            server.configurar(cfg, self.inexistente)
        self.assertIn('sandbox', str(cm.exception))

    def test_configuracao_so_por_variaveis_de_ambiente_funciona(self):
        server.configurar(dict(CONFIG_FICTICIA), self.inexistente)
        self.assertEqual(C.ENV['CREDIT_PRODUCT_ID'], CONFIG_FICTICIA['CREDIT_PRODUCT_ID'])

    def test_ambiente_tem_prioridade_sobre_o_arquivo(self):
        arq = self._arquivo('\n'.join(f'{k}={v}' for k, v in CONFIG_FICTICIA.items()) + '\n')
        outro = '00000000-0000-0000-0000-0000000000ff'
        server.configurar({'CREDIT_PRODUCT_ID': outro}, arq)
        self.assertEqual(C.ENV['CREDIT_PRODUCT_ID'], outro)

    def test_credit_mode_e_ignorada_com_aviso_e_nao_liga_simulado(self):
        erro = io.StringIO()
        with contextlib.redirect_stderr(erro):
            server.configurar(dict(CONFIG_FICTICIA, CREDIT_MODE='simulado'), self.inexistente)
        self.assertIn('CREDIT_MODE foi removida', erro.getvalue())
        self.assertIsNotNone(C.API)                      # o cliente da API continua ativo: nada de protótipo

    def test_credit_mode_simulado_sem_configuracao_continua_falhando(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(C.ConfigError):
                server.configurar({'CREDIT_MODE': 'simulado'}, self.inexistente)

    def test_mensagem_de_erro_nao_vaza_segredo(self):
        cfg = dict(CONFIG_FICTICIA, CREDIT_API_URL='https://producao.exemplo.test')
        with self.assertRaises(C.ConfigError) as cm:
            server.configurar(cfg, self.inexistente)
        self.assertNotIn('segredo-de-teste', str(cm.exception))

    def test_processo_sem_configuracao_nao_inicia(self):
        r = subprocess.run([sys.executable, os.path.join(APP, 'server.py')], capture_output=True, text=True, timeout=30,
                           cwd=RAIZ, env=env_limpo(CREDIT_ENV_FILE=self.inexistente, PORT='0'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('ERRO de configuração', r.stderr)
        self.assertNotIn('http://', r.stdout)

    def test_processo_com_credit_mode_simulado_e_sem_configuracao_nao_inicia(self):
        r = subprocess.run([sys.executable, os.path.join(APP, 'server.py')], capture_output=True, text=True, timeout=30,
                           cwd=RAIZ, env=env_limpo(CREDIT_MODE='simulado', CREDIT_ENV_FILE=self.inexistente, PORT='0'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('ERRO de configuração', r.stderr)

    def test_processo_com_configuracao_valida_inicia_no_sandbox(self):
        p = subprocess.Popen([sys.executable, os.path.join(APP, 'server.py')], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, cwd=RAIZ, env=env_limpo(CREDIT_ENV_FILE=self.inexistente, PORT='0', **CONFIG_FICTICIA))
        try:
            linha = p.stdout.readline()
        finally:
            p.kill()
            p.communicate()
        self.assertIn('SANDBOX da Celcoin', linha)


if __name__ == '__main__':
    unittest.main()
