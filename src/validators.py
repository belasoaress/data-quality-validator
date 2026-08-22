"""
Regras de validação de qualidade de dados.

Cada função recebe um DataFrame (lido com todas as colunas como string, pra
preservar sujeira nos dados) e devolve uma lista de "problemas" no formato:

    {
        "coluna": str,
        "tipo": str,            # nome curto do tipo de problema
        "quantidade": int,
        "exemplos": [dict, ...] # até 3 linhas afetadas, como dicts (id_pedido + colunas relevantes)
    }

Se uma regra não encontrar nada, ela devolve lista vazia — quem monta o
relatório final decide o que fazer com isso (ex: omitir a seção).
"""

import re
from datetime import datetime

import pandas as pd

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_FORMAT = "%Y-%m-%d"
DATA_MIN = datetime(2020, 1, 1)
DATA_MAX = datetime(2026, 12, 31)


def _amostra(df, mask, colunas_exibir, limite=3):
    """Extrai até `limite` linhas afetadas como lista de dicts, sempre incluindo id_pedido."""
    linhas = df.loc[mask]
    colunas = ["id_pedido"] + [c for c in colunas_exibir if c != "id_pedido"]
    return linhas[colunas].head(limite).to_dict(orient="records")


def check_nulls(df: pd.DataFrame) -> list:
    """Valores nulos/ausentes por coluna: contagem e percentual."""
    problemas = []
    total_linhas = len(df)
    for coluna in df.columns:
        mask = df[coluna].isna() | (df[coluna].astype(str).str.strip() == "")
        qtd = int(mask.sum())
        if qtd > 0:
            percentual = round((qtd / total_linhas) * 100, 1)
            problemas.append({
                "coluna": coluna,
                "tipo": "valor_nulo",
                "quantidade": qtd,
                "percentual": percentual,
                "exemplos": _amostra(df, mask, [coluna]),
            })
    return problemas


def check_duplicates(df: pd.DataFrame) -> list:
    """Linhas duplicadas: completas e por chave (id_pedido)."""
    problemas = []

    # Duplicatas completas (todas as colunas idênticas)
    mask_completa = df.duplicated(keep=False)
    if mask_completa.any():
        qtd = int(df.duplicated(keep="first").sum())  # conta só as "extras"
        problemas.append({
            "coluna": "todas",
            "tipo": "duplicata_completa",
            "quantidade": qtd,
            "exemplos": _amostra(df, mask_completa, list(df.columns)),
        })

    # Duplicatas por chave (id_pedido repetido, mesmo com dados diferentes)
    mask_chave = df.duplicated(subset=["id_pedido"], keep=False)
    if mask_chave.any():
        qtd_chaves = int(df.loc[mask_chave, "id_pedido"].nunique())
        problemas.append({
            "coluna": "id_pedido",
            "tipo": "duplicata_por_chave",
            "quantidade": qtd_chaves,
            "exemplos": _amostra(df, mask_chave, list(df.columns)),
        })

    return problemas


def check_type_consistency(df: pd.DataFrame) -> list:
    """Valores não numéricos numa coluna que deveria ser numérica (valor)."""
    problemas = []
    coluna = "valor"

    def eh_numerico(v):
        if pd.isna(v) or str(v).strip() == "":
            return True  # nulo é tratado por check_nulls, não aqui
        try:
            float(v)
            return True
        except (TypeError, ValueError):
            return False

    mask = ~df[coluna].apply(eh_numerico)
    qtd = int(mask.sum())
    if qtd > 0:
        problemas.append({
            "coluna": coluna,
            "tipo": "tipo_inconsistente",
            "quantidade": qtd,
            "exemplos": _amostra(df, mask, [coluna]),
        })
    return problemas


def check_value_ranges(df: pd.DataFrame) -> list:
    """Valores fora do intervalo esperado: valor negativo, data fora de intervalo plausível."""
    problemas = []

    # valor negativo
    def eh_negativo(v):
        try:
            return float(v) < 0
        except (TypeError, ValueError):
            return False

    mask_valor = df["valor"].apply(eh_negativo)
    qtd_valor = int(mask_valor.sum())
    if qtd_valor > 0:
        problemas.append({
            "coluna": "valor",
            "tipo": "valor_fora_do_intervalo",
            "quantidade": qtd_valor,
            "exemplos": _amostra(df, mask_valor, ["valor"]),
        })

    # data fora de um intervalo plausível (mas só considera datas que já
    # estão no formato certo; formato errado é pego por check_email_format... 
    # -> na verdade por uma checagem própria de formato, ver função abaixo)
    def data_fora_do_intervalo(v):
        try:
            d = datetime.strptime(str(v), DATE_FORMAT)
            return not (DATA_MIN <= d <= DATA_MAX)
        except (TypeError, ValueError):
            return False  # formato inválido é outro tipo de problema

    mask_data = df["data_pedido"].apply(data_fora_do_intervalo)
    qtd_data = int(mask_data.sum())
    if qtd_data > 0:
        problemas.append({
            "coluna": "data_pedido",
            "tipo": "valor_fora_do_intervalo",
            "quantidade": qtd_data,
            "exemplos": _amostra(df, mask_data, ["data_pedido"]),
        })

    return problemas


def check_format(df: pd.DataFrame) -> list:
    """Formato inválido: e-mail sem '@'/domínio, data fora do formato YYYY-MM-DD."""
    problemas = []

    # e-mail malformado
    def email_invalido(v):
        if pd.isna(v) or str(v).strip() == "":
            return False  # nulo é tratado por check_nulls
        return not bool(EMAIL_REGEX.match(str(v)))

    mask_email = df["email"].apply(email_invalido)
    qtd_email = int(mask_email.sum())
    if qtd_email > 0:
        problemas.append({
            "coluna": "email",
            "tipo": "formato_invalido",
            "quantidade": qtd_email,
            "exemplos": _amostra(df, mask_email, ["email"]),
        })

    # data fora do formato esperado
    def data_formato_invalido(v):
        if pd.isna(v) or str(v).strip() == "":
            return False
        try:
            datetime.strptime(str(v), DATE_FORMAT)
            return False
        except ValueError:
            return True

    mask_data = df["data_pedido"].apply(data_formato_invalido)
    qtd_data = int(mask_data.sum())
    if qtd_data > 0:
        problemas.append({
            "coluna": "data_pedido",
            "tipo": "formato_invalido",
            "quantidade": qtd_data,
            "exemplos": _amostra(df, mask_data, ["data_pedido"]),
        })

    return problemas


def run_all_checks(df: pd.DataFrame) -> list:
    """Roda todas as regras e devolve uma lista única de problemas encontrados."""
    problemas = []
    problemas += check_nulls(df)
    problemas += check_duplicates(df)
    problemas += check_type_consistency(df)
    problemas += check_value_ranges(df)
    problemas += check_format(df)
    return problemas
