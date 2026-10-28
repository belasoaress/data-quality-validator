"""Testa a integração com a API sem fazer chamadas reais (cliente falso)."""

import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import summarizer  # noqa: E402


class _Bloco:
    def __init__(self, tipo, texto=""):
        self.type = tipo
        self.text = texto


class _ClienteFalso:
    ultima_chamada = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.messages = self

    def create(self, **kwargs):
        _ClienteFalso.ultima_chamada = kwargs
        return types.SimpleNamespace(
            content=[_Bloco("text", "  Resumo em linguagem simples.  ")]
        )


@pytest.fixture
def anthropic_falso(monkeypatch):
    modulo = types.ModuleType("anthropic")
    modulo.Anthropic = _ClienteFalso
    monkeypatch.setitem(sys.modules, "anthropic", modulo)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-teste")


def test_envia_relatorio_e_system_prompt(anthropic_falso):
    resumo = summarizer.generate_summary("# Relatório\nvalor nulo em 1021")
    chamada = _ClienteFalso.ultima_chamada
    assert resumo == "Resumo em linguagem simples."
    assert chamada["model"] == summarizer.MODEL
    assert chamada["system"] == summarizer.SYSTEM_PROMPT
    assert "valor nulo em 1021" in chamada["messages"][0]["content"]


def test_sem_chave_da_erro_claro(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        summarizer.load_api_key()
