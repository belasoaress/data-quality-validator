"""
Monta o relatório técnico (markdown) a partir da lista de problemas
devolvida por validators.run_all_checks().

O relatório é ordenado por gravidade aproximada:
    1. duplicata_por_chave      (dados de um mesmo pedido divergindo — risco alto)
    2. tipo_inconsistente        (quebra cálculos e agregações)
    3. valor_fora_do_intervalo   (valores negativos, datas impossíveis)
    4. duplicata_completa        (infla contagens/métricas)
    5. valor_nulo                (dados faltando)
    6. formato_invalido          (cosmético/integração, mas não quebra números)
"""

from datetime import datetime

ORDEM_GRAVIDADE = [
    "duplicata_por_chave",
    "tipo_inconsistente",
    "valor_fora_do_intervalo",
    "duplicata_completa",
    "valor_nulo",
    "formato_invalido",
]

NOMES_AMIGAVEIS = {
    "duplicata_por_chave": "Duplicata por chave (id_pedido repetido)",
    "tipo_inconsistente": "Inconsistência de tipo",
    "valor_fora_do_intervalo": "Valor fora do intervalo esperado",
    "duplicata_completa": "Duplicata completa",
    "valor_nulo": "Valor nulo/ausente",
    "formato_invalido": "Formato inválido",
}


def _formatar_exemplo(ex: dict) -> str:
    def fmt(v):
        if v is None or (isinstance(v, float) and str(v) == "nan"):
            return "(vazio)"
        return v

    partes = [f"{k}={fmt(v)}" for k, v in ex.items()]
    return "`" + ", ".join(partes) + "`"


def _secao_para_problema(p: dict) -> str:
    linhas = [f"### {NOMES_AMIGAVEIS.get(p['tipo'], p['tipo'])} — coluna `{p['coluna']}`"]
    linhas.append(f"- **Quantidade de ocorrências:** {p['quantidade']}")
    if "percentual" in p:
        linhas.append(f"- **Percentual do dataset:** {p['percentual']}%")
    linhas.append("- **Exemplos de linhas afetadas:**")
    for ex in p["exemplos"]:
        linhas.append(f"  - {_formatar_exemplo(ex)}")
    linhas.append("")
    return "\n".join(linhas)


def generate_report(problemas: list, total_linhas: int, nome_dataset: str = "pedidos_exemplo.csv") -> str:
    problemas_ordenados = sorted(
        problemas,
        key=lambda p: ORDEM_GRAVIDADE.index(p["tipo"]) if p["tipo"] in ORDEM_GRAVIDADE else 999,
    )

    partes = [
        "# Relatório Técnico de Qualidade de Dados",
        "",
        f"- **Dataset analisado:** `{nome_dataset}`",
        f"- **Total de linhas:** {total_linhas}",
        f"- **Total de tipos de problema encontrados:** {len(problemas_ordenados)}",
        f"- **Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]

    if not problemas_ordenados:
        partes.append("Nenhum problema de qualidade de dados foi encontrado.")
    else:
        for p in problemas_ordenados:
            partes.append(_secao_para_problema(p))

    return "\n".join(partes)
