"""
CLI do Validador de Qualidade de Dados.

Uso:
    python main.py caminho/para/dados.csv

Fluxo:
    1. Lê o CSV.
    2. Roda as 5 regras de validação (src/validators.py).
    3. Monta o relatório técnico em markdown (src/report.py) -> output/relatorio_tecnico.md
    4. Chama a API da Claude pra gerar o resumo executivo (src/summarizer.py) -> output/resumo_executivo.md
    5. Imprime os dois relatórios no terminal, em sequência.
"""

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from validators import run_all_checks
from report import generate_report
from summarizer import generate_summary

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def main():
    parser = argparse.ArgumentParser(
        description="Valida a qualidade de um CSV e gera um relatório técnico + resumo executivo."
    )
    parser.add_argument("csv_path", help="Caminho para o arquivo CSV a ser validado")
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help="Pula a chamada à API da Claude (só gera o relatório técnico). Útil sem chave de API configurada.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.csv_path):
        print(f"Erro: arquivo não encontrado: {args.csv_path}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Ler o CSV (tudo como string, pra preservar sujeira nos dados: "abc", "-45.00", email malformado etc.)
    df = pd.read_csv(args.csv_path, dtype=str, keep_default_na=True, na_values=[""])

    # 2. Rodar as validações
    problemas = run_all_checks(df)

    # 3. Gerar relatório técnico
    nome_dataset = os.path.basename(args.csv_path)
    relatorio_tecnico = generate_report(problemas, total_linhas=len(df), nome_dataset=nome_dataset)
    caminho_tecnico = os.path.join(OUTPUT_DIR, "relatorio_tecnico.md")
    with open(caminho_tecnico, "w", encoding="utf-8") as f:
        f.write(relatorio_tecnico)

    print("=" * 70)
    print("RELATÓRIO TÉCNICO")
    print("=" * 70)
    print(relatorio_tecnico)
    print(f"\n(salvo em {caminho_tecnico})\n")

    # 4. Gerar resumo executivo via API da Claude
    if args.skip_summary:
        print("(--skip-summary usado: pulando a geração do resumo executivo)")
        return

    if not problemas:
        print("Nenhum problema encontrado — resumo executivo não é necessário.")
        return

    try:
        resumo = generate_summary(relatorio_tecnico)
    except Exception as e:
        print(f"Erro ao gerar o resumo executivo: {e}")
        print("Dica: rode com --skip-summary se só quiser o relatório técnico.")
        sys.exit(1)

    caminho_resumo = os.path.join(OUTPUT_DIR, "resumo_executivo.md")
    with open(caminho_resumo, "w", encoding="utf-8") as f:
        f.write(resumo)

    print("=" * 70)
    print("RESUMO EXECUTIVO (linguagem simples)")
    print("=" * 70)
    print(resumo)
    print(f"\n(salvo em {caminho_resumo})")


if __name__ == "__main__":
    main()
