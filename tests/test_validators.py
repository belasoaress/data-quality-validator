"""Testes das regras de validação (não chamam a API)."""

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import validators as v  # noqa: E402

DATASET = os.path.join(os.path.dirname(__file__), "..", "data", "pedidos_exemplo.csv")


def df_de(linhas):
    colunas = ["id_pedido", "cliente", "email", "data_pedido", "valor", "status"]
    return pd.DataFrame(linhas, columns=colunas, dtype=str)


LINHA_OK = ["1", "Ana", "ana@ex.com", "2025-01-10", "10.00", "pago"]


def tipos(problemas):
    return sorted((p["tipo"], p["coluna"]) for p in problemas)


def test_dataset_limpo_nao_gera_problemas():
    df = df_de([LINHA_OK, ["2", "Bia", "bia@ex.com", "2025-01-11", "20.00", "pago"]])
    assert v.run_all_checks(df) == []


def test_nulos_contam_vazio_e_espacos():
    df = df_de([LINHA_OK, ["2", "  ", None, "2025-01-11", "20.00", "pago"]])
    problemas = v.check_nulls(df)
    assert tipos(problemas) == [("valor_nulo", "cliente"), ("valor_nulo", "email")]
    assert problemas[0]["percentual"] == 50.0


def test_duplicata_completa_nao_conta_como_duplicata_por_chave():
    df = df_de([LINHA_OK, LINHA_OK])
    assert tipos(v.check_duplicates(df)) == [("duplicata_completa", "todas")]


def test_duplicata_por_chave_so_quando_dados_divergem():
    divergente = ["1", "Ana", "ana@ex.com", "2025-01-10", "99.00", "cancelado"]
    df = df_de([LINHA_OK, divergente])
    problemas = v.check_duplicates(df)
    assert tipos(problemas) == [("duplicata_por_chave", "id_pedido")]
    assert problemas[0]["quantidade"] == 1


def test_tipo_inconsistente_ignora_nulos():
    df = df_de([LINHA_OK, ["2", "Bia", "bia@ex.com", "2025-01-11", "abc", "pago"],
                ["3", "Caio", "caio@ex.com", "2025-01-12", None, "pago"]])
    problemas = v.check_type_consistency(df)
    assert problemas[0]["quantidade"] == 1
    assert problemas[0]["exemplos"][0]["id_pedido"] == "2"


def test_valor_negativo_e_data_futura():
    futuro = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    df = df_de([LINHA_OK, ["2", "Bia", "bia@ex.com", futuro, "-5", "pago"]])
    assert tipos(v.check_value_ranges(df)) == [
        ("valor_fora_do_intervalo", "data_pedido"),
        ("valor_fora_do_intervalo", "valor"),
    ]


def test_data_de_hoje_e_valida():
    hoje = datetime.now().strftime("%Y-%m-%d")
    df = df_de([["1", "Ana", "ana@ex.com", hoje, "10.00", "pago"]])
    assert v.check_value_ranges(df) == []


@pytest.mark.parametrize("email", ["semarroba.com", "a@b", "a @b.com"])
def test_email_invalido(email):
    df = df_de([["1", "Ana", email, "2025-01-10", "10.00", "pago"]])
    assert tipos(v.check_format(df)) == [("formato_invalido", "email")]


def test_data_fora_do_formato():
    df = df_de([["1", "Ana", "ana@ex.com", "10/01/2025", "10.00", "pago"]])
    assert tipos(v.check_format(df)) == [("formato_invalido", "data_pedido")]


def test_csv_com_outras_colunas_nao_quebra():
    df = pd.DataFrame({"produto": ["x", None], "preco": ["1", "2"]}, dtype=str)
    problemas = v.run_all_checks(df)
    assert tipos(problemas) == [("valor_nulo", "produto")]


def test_dataset_de_exemplo_tem_os_9_problemas_plantados():
    df = pd.read_csv(DATASET, dtype=str, keep_default_na=True, na_values=[""])
    assert tipos(v.run_all_checks(df)) == [
        ("duplicata_completa", "todas"),
        ("duplicata_por_chave", "id_pedido"),
        ("formato_invalido", "data_pedido"),
        ("formato_invalido", "email"),
        ("tipo_inconsistente", "valor"),
        ("valor_fora_do_intervalo", "valor"),
        ("valor_nulo", "cliente"),
        ("valor_nulo", "email"),
        ("valor_nulo", "valor"),
    ]
