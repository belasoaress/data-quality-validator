"""
Gera o resumo executivo em linguagem natural, a partir do relatório técnico,
usando a API da Claude (modelo Haiku).

A validação em si (validators.py, report.py) é 100% determinística e não usa
IA. A IA entra só aqui, para traduzir o relatório técnico — cheio de nomes de
coluna, contagens e jargão de dados — numa explicação clara para alguém sem
conhecimento técnico (ex: o dono de uma loja online).

Requer ANTHROPIC_API_KEY setada (via .env ou variável de ambiente).
"""

import os

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """\
Você traduz relatórios técnicos de qualidade de dados para uma explicação em \
linguagem simples, destinada a alguém sem nenhum conhecimento técnico (por \
exemplo, o dono de uma loja online que não entende de banco de dados, \
programação ou estatística).

Regras:
- Não use jargão técnico (nada de "nulo", "duplicata por chave", "tipo \
inconsistente", "dataset", "coluna" — descreva o problema em termos do \
negócio: pedidos, clientes, valores, datas).
- Comece pelos problemas mais graves (os que aparecem primeiro no relatório \
já estão ordenados por gravidade — mantenha essa ordem).
- Para cada problema, explique em 1-2 frases: o que está errado, por que \
isso importa pro negócio (ex: "pode fazer você cobrar duas vezes o mesmo \
cliente" ou "esse pedido não vai aparecer certo nos relatórios de vendas"), \
e cite 1 exemplo concreto (o número do pedido é suficiente).
- Termine com um parágrafo curto de recomendação geral (ex: revisar esses \
casos antes de fechar o mês, mas sem soar alarmista).
- Tom: direto, claro, respeitoso — como um analista explicando pra um colega \
de outra área, não como um professor ou como um sistema genérico de alertas.
- Responda em português do Brasil.
- Não use markdown (nada de #, **, listas com -), apenas parágrafos corridos, \
já que isso vai ser lido como texto simples.
"""


def load_api_key() -> str:
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY não encontrada. Copie .env.example para .env "
            "e preencha com sua chave da API da Anthropic."
        )
    return api_key


def generate_summary(relatorio_tecnico_md: str) -> str:
    """Chama a API da Claude e devolve o resumo executivo em texto simples."""
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise RuntimeError(
            "Biblioteca 'anthropic' não instalada. Rode: pip install -r requirements.txt"
        ) from e

    api_key = load_api_key()
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Aqui está o relatório técnico de qualidade de dados. "
                    "Traduza para linguagem simples, seguindo as regras do "
                    "seu system prompt:\n\n" + relatorio_tecnico_md
                ),
            }
        ],
    )

    # response.content é uma lista de blocos (normalmente só um bloco de texto)
    texto = "".join(bloco.text for bloco in response.content if bloco.type == "text")
    return texto.strip()
