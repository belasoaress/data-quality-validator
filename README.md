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
└── output/
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
linhas, com 9 problemas plantados deliberadamente), o comando gera dois
arquivos em `output/`. Abaixo, um recorte de cada um, lado a lado:

### Relatório técnico (`output/relatorio_tecnico.md`)

```markdown
# Relatório Técnico de Qualidade de Dados

- **Dataset analisado:** `pedidos_exemplo.csv`
- **Total de linhas:** 30
- **Total de tipos de problema encontrados:** 9

---

### Duplicata por chave (id_pedido repetido) — coluna `id_pedido`
- **Quantidade de ocorrências:** 2
- **Exemplos de linhas afetadas:**
  - `id_pedido=1015, cliente=Diego Barbosa, ...`
  - `id_pedido=1017, cliente=Gustavo Pereira, status=entregue`
  - `id_pedido=1017, cliente=Gustavo Pereira, status=pago, data_pedido=15/02/2025`

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

### Resumo executivo (`output/resumo_executivo.md`)

> **Nota:** este projeto não teve acesso à internet durante seu
> desenvolvimento, então o trecho abaixo é um **exemplo ilustrativo** do
> formato de saída esperado — escrito manualmente seguindo exatamente as
> regras do `system prompt` usado em `summarizer.py` — e não uma resposta
> real gerada pela API. Ao rodar o projeto localmente com sua chave, o
> conteúdo real será gerado pelo Claude Haiku a partir do relatório técnico
> acima.

```
Encontramos alguns pontos que merecem atenção antes de fechar os números do
período.

O mais importante: o pedido 1017 aparece duas vezes com informações
diferentes entre si (uma versão diz que foi entregue, outra que só foi pago,
e as datas também não batem). Isso é um risco real, porque não dá pra saber
qual das duas versões está correta, e relatórios de vendas ou de entrega
podem sair errados por causa disso.

Também identificamos um pedido (1010) em que o valor cobrado não é um número
válido — está registrado como texto. Isso pode travar qualquer cálculo de
faturamento que inclua esse pedido. Já o pedido 1012 tem um valor negativo,
o que normalmente não faz sentido para uma venda e vale conferir se não foi
um erro de digitação ou um estorno mal lançado.

Um pedido (1015) foi registrado duas vezes de forma idêntica, o que pode
inflar artificialmente o total de vendas se ninguém remover a duplicata.

Por fim, alguns registros têm campos em branco (nome do cliente, e-mail ou
valor faltando), e um e-mail está com o formato errado (sem o símbolo @),
o que pode impedir o envio de notificações pra esse cliente.

Recomendamos revisar esses casos, especialmente o pedido 1017, antes de usar
esses dados para relatórios ou faturamento. Nenhum desses problemas exige uma
ação de emergência, mas quanto antes forem corrigidos, menor o risco de
propagarem erro para outras áreas do negócio.
```

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
