"""
Gera um dataset sintético de pedidos de e-commerce (~30 linhas), com problemas
de qualidade de dados plantados deliberadamente e de forma rastreável.

Cada problema plantado está comentado no código abaixo, indicando exatamente
qual linha e qual regra de validação (em validators.py) deve pegá-lo.

Colunas:
    id_pedido    (int)    - identificador do pedido
    cliente      (str)    - nome do cliente
    email        (str)    - e-mail do cliente
    data_pedido  (str)    - data do pedido, formato esperado YYYY-MM-DD
    valor        (str)    - valor do pedido em R$ (string pra permitir sujeira proposital)
    status       (str)    - pendente / pago / cancelado / entregue
"""

import csv
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pedidos_exemplo.csv")

STATUSES = ["pendente", "pago", "cancelado", "entregue"]

# Cada item é uma linha do CSV, na ordem das colunas acima.
# Comentários marcam os problemas plantados intencionalmente.
ROWS = [
    [1001, "Marina Alves", "marina.alves@gmail.com", "2025-01-12", "189.90", "pago"],
    [1002, "João Pedro Souza", "joao.souza@hotmail.com", "2025-01-15", "45.00", "entregue"],
    [1003, "Carla Menezes", "carla.menezes@yahoo.com", "2025-01-18", "302.50", "pago"],
    [1004, "Rafael Costa", "", "2025-01-20", "78.20", "pendente"],  # PROBLEMA: email nulo
    [1005, "Beatriz Lima", "beatriz.lima@gmail.com", "2025-01-22", "150.00", "pago"],
    [1006, "", "gabriel.rocha@outlook.com", "2025-01-23", "99.99", "entregue"],  # PROBLEMA: cliente nulo
    [1007, "Thiago Fernandes", "thiago.f@gmail.com", "2025-01-25", "220.00", "cancelado"],
    [1008, "Larissa Prado", "larissa.pradoyahoo.com", "2025-01-28", "63.40", "pago"],  # PROBLEMA: email sem @
    [1009, "Eduardo Martins", "eduardo.martins@gmail.com", "2025-01-30", "410.00", "entregue"],
    [1010, "Fernanda Dias", "fernanda.dias@hotmail.com", "2025-02-02", "abc", "pago"],  # PROBLEMA: valor não numérico
    [1011, "Vinícius Ramos", "vinicius.ramos@gmail.com", "2025-02-04", "88.00", "pendente"],
    [1012, "Camila Nogueira", "camila.nogueira@gmail.com", "2025-02-05", "-45.00", "cancelado"],  # PROBLEMA: valor negativo
    [1013, "Bruno Teixeira", "bruno.teixeira@yahoo.com", "2025-02-07", "175.30", "pago"],
    [1014, "Patrícia Gomes", "patricia.gomes@gmail.com", "2025-02-09", "60.00", "entregue"],
    [1015, "Diego Barbosa", "diego.barbosa@outlook.com", "2025-02-10", "132.90", "pago"],
    [1015, "Diego Barbosa", "diego.barbosa@outlook.com", "2025-02-10", "132.90", "pago"],  # PROBLEMA: duplicata exata (id 1015)
    [1016, "Juliana Castro", "juliana.castro@gmail.com", "2025-02-12", "95.50", "pendente"],
    [1017, "Gustavo Pereira", "gustavo.pereira@gmail.com", "2025-02-14", "310.00", "entregue"],
    [1017, "Gustavo Pereira", "gustavo.pereira@gmail.com", "15/02/2025", "310.00", "pago"],  # PROBLEMA: id duplicado com dados diferentes + data fora do formato
    [1018, "Renata Almeida", "renata.almeida@yahoo.com", "2025-02-16", "58.00", "pago"],
    [1019, "Felipe Andrade", "felipe.andrade@gmail.com", "2025-02-18", "199.99", "cancelado"],
    [1020, "Aline Ribeiro", "aline.ribeiro@hotmail.com", "2025-02-19", "72.10", "entregue"],
    [1021, "Marcelo Cunha", "marcelo.cunha@gmail.com", "2025-02-21", "", "pago"],  # PROBLEMA: valor nulo
    [1022, "Isabela Rocha", "isabela.rocha@gmail.com", "2025-02-23", "245.00", "pendente"],
    [1023, "Leonardo Freitas", "leonardo.freitas@outlook.com", "2025-02-25", "112.40", "pago"],
    [1024, "Natália Correia", "natalia.correia@gmail.com", "2025-02-27", "68.90", "entregue"],
    [1025, "André Moura", "andre.moura@yahoo.com", "2025-03-01", "540.00", "pago"],
    [1026, "Simone Vieira", "simone.vieira@gmail.com", "2025-03-03", "39.90", "cancelado"],
    [1027, "Rodrigo Sales", "rodrigo.sales@hotmail.com", "2025-03-05", "128.00", "pago"],
    [1028, "Vanessa Duarte", "vanessa.duarte@gmail.com", "2025-03-07", "205.60", "entregue"],
]

HEADER = ["id_pedido", "cliente", "email", "data_pedido", "valor", "status"]


def generate():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(ROWS)
    print(f"Dataset gerado: {OUTPUT_PATH} ({len(ROWS)} linhas)")


if __name__ == "__main__":
    generate()
