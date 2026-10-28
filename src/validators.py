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
from datetime import datetime, timedelta

import pandas as pd

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_FORMAT = "%Y-%m-%d"
DATA_MIN = datetime(2020, 1, 1)
# Datas no futuro são suspeitas; a folga de 1 dia cobre diferenças de fuso.
# Calculado na hora da validação (e não fixo) para a regra não "vencer" com o tempo.
FOLGA_FUTURO = timedelta(days=1)

# Nomes das colunas que as regras específicas esperam. Se o CSV não tiver
# alguma delas, a regra correspondente é pulada em vez de quebrar o programa.
COL_ID = "id_pedido"
COL_VALOR = "valor"
COL_DATA = "data_pedido"
COL_EMAIL = "email"


def _data_max() -> datetime:
    return datetime.now() + FOLGA_FUTURO


def _amostra(df, mask, colunas_exibir, limite=3):
    """Extrai até `limite` linhas afetadas como lista de dicts, sempre incluindo id_pedido."""
    linhas = df.loc[mask]
    colunas = [c for c in colunas_exibir if c != COL_ID]
    if COL_ID in df.columns:
        colunas = [COL_ID] + colunas
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
            "exemplos": _amostra(df, df.duplicated(keep="first"), list(df.columns)),
        })

    # Duplicatas por chave: o mesmo id_pedido com dados DIFERENTES entre as
    # linhas. Cópias idênticas já foram reportadas acima como duplicata
    # completa, então são removidas antes para não contar o mesmo problema duas vezes.
    if COL_ID in df.columns:
        sem_copias = df.drop_duplicates(keep="first")
        ids_divergentes = sem_copias.loc[
            sem_copias.duplicated(subset=[COL_ID], keep=False), COL_ID
        ].unique()
        if len(ids_divergentes) > 0:
            mask_chave = df[COL_ID].isin(ids_divergentes) & ~df.duplicated(keep="first")
            problemas.append({
                "coluna": COL_ID,
                "tipo": "duplicata_por_chave",
                "quantidade": int(len(ids_divergentes)),
                "exemplos": _amostra(df, mask_chave, list(df.columns)),
            })

    return problemas


def check_type_consistency(df: pd.DataFrame) -> list:
    """Valores não numéricos numa coluna que deveria ser numérica (valor)."""
    problemas = []
    coluna = COL_VALOR
    if coluna not in df.columns:
        return problemas

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
    if COL_VALOR not in df.columns and COL_DATA not in df.columns:
        return problemas

    # valor negativo
    def eh_negativo(v):
        try:
            return float(v) < 0
        except (TypeError, ValueError):
            return False

    mask_valor = df[COL_VALOR].apply(eh_negativo) if COL_VALOR in df.columns else pd.Series(False, index=df.index)
    qtd_valor = int(mask_valor.sum())
    if qtd_valor > 0:
        problemas.append({
            "coluna": COL_VALOR,
            "tipo": "valor_fora_do_intervalo",
            "quantidade": qtd_valor,
            "exemplos": _amostra(df, mask_valor, ["valor"]),
        })

    # Data fora de um intervalo plausível. Só considera datas que já estão no
    # formato certo; formato errado é reportado por check_format.
    data_max = _data_max()

    def data_fora_do_intervalo(v):
        try:
            d = datetime.strptime(str(v), DATE_FORMAT)
            return not (DATA_MIN <= d <= data_max)
        except (TypeError, ValueError):
            return False  # formato inválido é outro tipo de problema

    mask_data = df[COL_DATA].apply(data_fora_do_intervalo) if COL_DATA in df.columns else pd.Series(False, index=df.index)
    qtd_data = int(mask_data.sum())
    if qtd_data > 0:
        problemas.append({
            "coluna": COL_DATA,
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

    mask_email = df[COL_EMAIL].apply(email_invalido) if COL_EMAIL in df.columns else pd.Series(False, index=df.index)
    qtd_email = int(mask_email.sum())
    if qtd_email > 0:
        problemas.append({
            "coluna": COL_EMAIL,
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

    mask_data = df[COL_DATA].apply(data_formato_invalido) if COL_DATA in df.columns else pd.Series(False, index=df.index)
    qtd_data = int(mask_data.sum())
    if qtd_data > 0:
        problemas.append({
            "coluna": COL_DATA,
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
