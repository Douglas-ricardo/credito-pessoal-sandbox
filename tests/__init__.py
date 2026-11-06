"""Testes (unittest, só biblioteca padrão). Rode na raiz do repositório: python -m unittest"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(RAIZ, 'app')
if APP not in sys.path:
    sys.path.insert(0, APP)
