# Validador de Qualidade de Dados com Resumo em Linguagem Natural

Ferramenta de linha de comando que roda um conjunto de regras técnicas
determinísticas sobre um dataset tabular (CSV), gera um **relatório técnico**
detalhado, e usa a API da Claude para traduzir esse relatório num **resumo
executivo em linguagem simples** — como se estivesse explicando os problemas
encontrados para alguém sem conhecimento técnico.

A validação em si **não usa IA**: é toda baseada em regras de pandas,
modulares e testáveis isoladamente. A IA entra só na etapa final, de
comunicação.

## Por que esse projeto existe

Este é um projeto de portfólio, construído para demonstrar uma habilidade
específica: **traduzir um problema técnico complexo em linguagem clara**. A
parte de validação de dados é propositalmente simples e direta — o foco real
está em como o resultado técnico é comunicado.

## Stack

- Python 3 + pandas (validação)
- SDK oficial `anthropic`, apenas na etapa de resumo
- Modelo: `claude-haiku-4-5-20251001`
- `python-dotenv` para carregar a chave de API do `.env`
- CLI via `argparse`

## Estrutura

```
data-quality-validator/
├── main.py                  # CLI: orquestra o pipeline completo
├── requirements.txt
├── .env.example
├── data/
│   └── pedidos_exemplo.csv  # dataset sintético com problemas plantados
├── src/
│   ├── generate_dataset.py  # gera o CSV de exemplo
│   ├── validators.py        # as 5 regras de validação
│   ├── report.py            # monta o relatório técnico em markdown
│   └── summarizer.py        # chama a API da Claude para o resumo executivo
├── tests/                   # pytest: regras, dataset de exemplo e API (mock)
├── .github/workflows/       # CI que roda os testes
└── output/                  # gerado ao rodar (não versionado)
    ├── relatorio_tecnico.md
    └── resumo_executivo.md
```

## Regras de validação implementadas

Cada regra é uma função isolada em `src/validators.py`, o que facilita
explicar (e testar) cada uma separadamente:

1. **`check_nulls`** — valores nulos/ausentes por coluna, com contagem e
   percentual sobre o total de linhas.
2. **`check_duplicates`** — duplicatas completas (linha idêntica repetida) e
   duplicatas por chave (mesmo `id_pedido` aparecendo mais de uma vez, mesmo
   com dados diferentes).
3. **`check_type_consistency`** — valores não numéricos numa coluna que
   deveria ser numérica (ex: texto na coluna `valor`).
4. **`check_value_ranges`** — valores fora de um intervalo plausível (ex:
   `valor` negativo, `data_pedido` fora de uma janela de datas razoável).
5. **`check_format`** — formato inválido (ex: e-mail sem `@`/domínio, data
   fora do padrão `YYYY-MM-DD`).

`check_nulls` e as duplicatas completas funcionam em qualquer CSV. As demais
regras usam os nomes de coluna definidos no topo de `src/validators.py`
(`id_pedido`, `valor`, `data_pedido`, `email`); se o CSV não tiver alguma
dessas colunas, a regra correspondente é pulada em vez de quebrar a execução.
A data máxima aceita é calculada na hora (hoje + 1 dia), então a regra não
fica desatualizada com o tempo.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # preencha com sua ANTHROPIC_API_KEY
python main.py data/pedidos_exemplo.csv
```

Para gerar só o relatório técnico, sem chamar a API (útil se você só quer
inspecionar a parte de validação, sem configurar uma chave):

```bash
python main.py data/pedidos_exemplo.csv --skip-summary
```

## Exemplo de execução

Rodando contra o dataset sintético incluído (`data/pedidos_exemplo.csv`, 30
linhas, com 9 problemas plantados deliberadamente), o comando gera o
relatório técnico em `output/relatorio_tecnico.md`. Recorte da saída real:

```markdown
# Relatório Técnico de Qualidade de Dados

- **Dataset analisado:** `pedidos_exemplo.csv`
- **Total de linhas:** 30
- **Total de tipos de problema encontrados:** 9

---

### Duplicata por chave (id_pedido repetido) — coluna `id_pedido`
- **Quantidade de ocorrências:** 1
- **Exemplos de linhas afetadas:**
  - `id_pedido=1017, ..., data_pedido=2025-02-14, valor=310.00, status=entregue`
  - `id_pedido=1017, ..., data_pedido=15/02/2025, valor=310.00, status=pago`

### Inconsistência de tipo — coluna `valor`
- **Quantidade de ocorrências:** 1
- **Exemplos de linhas afetadas:**
  - `id_pedido=1010, valor=abc`

### Valor fora do intervalo esperado — coluna `valor`
- **Quantidade de ocorrências:** 1
- **Exemplos de linhas afetadas:**
  - `id_pedido=1012, valor=-45.00`

(... demais seções: duplicata completa, valores nulos, formato inválido ...)
```

Com a chave configurada, o mesmo relatório é enviado ao Claude Haiku, que
devolve o resumo executivo em `output/resumo_executivo.md`. O `system prompt`
em `src/summarizer.py` define as regras do resumo: sem jargão técnico, problemas
em ordem de gravidade, impacto no negócio explicado em 1-2 frases com um
exemplo concreto (o número do pedido) e uma recomendação final sem alarmismo.

## Testes

```bash
pip install pytest
pytest -q
```

Os testes cobrem cada regra de validação isoladamente, o dataset de exemplo
(os 9 problemas plantados precisam ser encontrados) e a integração com a API
usando um cliente falso — nenhuma chave é necessária. O GitHub Actions roda a
suíte a cada push e pull request.

## Por que a tradução para linguagem simples importa

Um relatório técnico ("coluna `valor`, tipo `inconsistente`, 1 ocorrência")
é preciso, mas exige alguém que já sabe interpretar esse vocabulário. No
dia a dia de um time — especialmente em empresas pequenas, ou em times
multidisciplinares com PMs, pessoas de operação, financeiro ou o próprio
dono do negócio — quem toma a decisão sobre o que fazer com um dado quebrado
raramente é quem escreveu a regra de validação. Se o problema não for
explicado em termos do impacto real ("esse cliente pode ser cobrado duas
vezes"), ele tende a ser ignorado ou mal-entendido, mesmo estando
tecnicamente correto e bem documentado. Automatizar essa tradução — mantendo
a prioridade dos problemas mais graves e traduzindo cada um pro impacto de
negócio — é o que faz um relatório técnico virar, de fato, algo acionável
para quem não é técnico.
