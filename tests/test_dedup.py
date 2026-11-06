import json
import os
import threading
import time
import unittest
from unittest import mock

from tests import APP
from tests.helpers import servidor, requisicao_crua
import server

CORPO = {'dados': {'cpf': '000.000.000-00'}, 'valor': 1000, 'n': 6, 'venc': '2030-01-10'}


class RecuoProgressivo(unittest.TestCase):
    def _relogio(self):
        t = {'v': 0.0}
        return t, (lambda: t['v']), (lambda s: t.__setitem__('v', t['v'] + s))

    def test_espera_cresce_e_tem_teto(self):
        _, relogio, avancar = self._relogio()
        esperas = []
        respostas = iter([{'status': 'AGREEMENT_RENDERING'}] * 6 + [{'status': 'PENDING_SIGNATURE'}])

        def dormir(s):
            esperas.append(s)
            avancar(s)

        g = server.aguardar_contrato(lambda: next(respostas), dormir=dormir, relogio=relogio)
        self.assertEqual(g['status'], 'PENDING_SIGNATURE')
        self.assertEqual(esperas, [1.0, 1.5, 2.25, 3.375, 5.0, 5.0, 5.0])

    def test_para_assim_que_o_status_muda(self):
        _, relogio, avancar = self._relogio()
        consultas = []

        def consultar():
            consultas.append(1)
            return {'status': 'CANCELED', 'status_description': 'KYC_REJECTED'}

        g = server.aguardar_contrato(consultar, dormir=avancar, relogio=relogio)
        self.assertEqual(len(consultas), 1)
        self.assertEqual(g['status'], 'CANCELED')

    def test_estoura_o_tempo_total(self):
        _, relogio, avancar = self._relogio()
        with self.assertRaises(ValueError) as cm:
            server.aguardar_contrato(lambda: {'status': 'AGREEMENT_RENDERING'}, timeout=10, dormir=avancar, relogio=relogio)
        self.assertIn('Tempo esgotado', str(cm.exception))


class DeduplicacaoDeSolicitacao(unittest.TestCase):
    def setUp(self):
        server._dedup.clear()
        self.addCleanup(server._dedup.clear)

    def test_chamadas_simultaneas_iguais_criam_uma_so_solicitacao(self):
        chamadas = []
        liberar = threading.Event()

        def lenta(b):
            chamadas.append(1)
            liberar.wait(5)
            return {'appId': 'app-unico'}

        resultados, erros = [], []

        def cliente():
            try:
                resultados.append(server.solicitar_unico(dict(CORPO)))
            except Exception as e:
                erros.append(e)

        with mock.patch.object(server, 'solicitar', side_effect=lenta):
            ts = [threading.Thread(target=cliente) for _ in range(6)]
            for t in ts:
                t.start()
            time.sleep(0.3)
            liberar.set()
            for t in ts:
                t.join(10)
        self.assertEqual(erros, [])
        self.assertEqual(len(chamadas), 1)
        self.assertEqual([r['appId'] for r in resultados], ['app-unico'] * 6)

    def test_cpf_com_ou_sem_pontuacao_e_a_mesma_chave(self):
        with mock.patch.object(server, 'solicitar', return_value={'appId': 'a'}) as s:
            server.solicitar_unico(dict(CORPO, dados={'cpf': '000.000.000-00'}))
            server.solicitar_unico(dict(CORPO, dados={'cpf': '00000000000'}))
        self.assertEqual(s.call_count, 1)

    def test_parametros_diferentes_sao_solicitacoes_diferentes(self):
        with mock.patch.object(server, 'solicitar', return_value={'appId': 'a'}) as s:
            server.solicitar_unico(dict(CORPO))
            server.solicitar_unico(dict(CORPO, valor=2000))
            server.solicitar_unico(dict(CORPO, n=12))
            server.solicitar_unico(dict(CORPO, venc='2030-02-10'))
            server.solicitar_unico(dict(CORPO, dados={'cpf': '111.111.111-11'}))
        self.assertEqual(s.call_count, 5)

    def test_falha_nao_fica_em_cache(self):
        with mock.patch.object(server, 'solicitar', side_effect=[ValueError('falhou'), {'appId': 'ok'}]) as s:
            with self.assertRaises(ValueError):
                server.solicitar_unico(dict(CORPO))
            self.assertEqual(server.solicitar_unico(dict(CORPO))['appId'], 'ok')
        self.assertEqual(s.call_count, 2)

    def test_depois_da_janela_permite_nova_solicitacao(self):
        t = {'v': 1000.0}
        with mock.patch.object(server, 'solicitar', side_effect=[{'appId': 'a'}, {'appId': 'b'}]) as s:
            primeiro = server.solicitar_unico(dict(CORPO), agora=lambda: t['v'])
            t['v'] += server.JANELA_DEDUP - 1
            repetido = server.solicitar_unico(dict(CORPO), agora=lambda: t['v'])
            t['v'] += 2
            novo = server.solicitar_unico(dict(CORPO), agora=lambda: t['v'])
        self.assertEqual((primeiro['appId'], repetido['appId'], novo['appId']), ('a', 'a', 'b'))
        self.assertEqual(s.call_count, 2)

    def test_duplo_clique_via_http_cria_uma_so_solicitacao(self):
        chamadas = []

        def lenta(b):
            chamadas.append(1)
            time.sleep(0.4)
            return {'appId': 'app-http'}

        respostas = []

        def post(porta):
            respostas.append(requisicao_crua(porta, 'POST', '/api/solicitar', corpo=json.dumps(CORPO).encode(),
                                             headers_extra={'Content-Type': 'application/json'}))

        with mock.patch.object(server, 'solicitar', side_effect=lenta), servidor(modo_real=True) as porta:
            ts = [threading.Thread(target=post, args=(porta,)) for _ in range(2)]
            for t in ts:
                t.start()
            for t in ts:
                t.join(10)
        self.assertEqual(len(chamadas), 1)
        self.assertEqual([r[0] for r in respostas], [200, 200])
        self.assertEqual({json.loads(r[2])['appId'] for r in respostas}, {'app-http'})


class TravasNoFront(unittest.TestCase):
    """Sem motor JS no ambiente, só garantimos que as travas existem na ponte (o comportamento é verificado no navegador)."""

    def test_ponte_tem_travas_de_duplo_clique(self):
        with open(os.path.join(APP, 'bridge.js'), encoding='utf-8') as f:
            js = f.read()
        for trecho in ('criandoAgora', 'assinandoAgora', 'retentando', 'function bloquearBotoes'):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, js)


if __name__ == '__main__':
    unittest.main()
