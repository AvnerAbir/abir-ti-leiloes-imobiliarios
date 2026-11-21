 
import sqlite3

ARQUIVO_BANCO = "banco/leiloes_imoveis.db"


def pesquisar():

    conexao = sqlite3.connect(ARQUIVO_BANCO)
    cursor = conexao.cursor()

    print("\n====================================")
    print("     PESQUISA DE IMÓVEIS")
    print("====================================")

    print("\nDigite os filtros desejados.")
    print("Deixe em branco aquilo que não quiser filtrar.\n")

    cidade = input("Cidade: ").strip()
    estado = input("Estado (UF): ").strip().upper()
    tipo = input("Tipo de imóvel: ").strip()
    situacao = input("Situação do leilão: ").strip()

    valor_maximo = input("Valor máximo de avaliação (ex: 500000): ").strip()

    consulta = """
        SELECT codigo_lote, titulo, endereco,
               situacao_leilao, valor_avaliacao, link
        FROM imoveis
        WHERE 1=1
    """

    parametros = []

    if cidade:
        consulta += " AND endereco LIKE ?"
        parametros.append(f"%{cidade}%")

    if estado:
        consulta += " AND endereco LIKE ?"
        parametros.append(f"%{estado}%")

    if tipo:
        consulta += " AND titulo LIKE ?"
        parametros.append(f"%{tipo}%")

    if situacao:
        consulta += " AND situacao_leilao LIKE ?"
        parametros.append(f"%{situacao}%")

    if valor_maximo:
        try:
            valor = float(
                valor_maximo.replace(".", "").replace(",", ".")
            )

            consulta += """
                AND CAST(
                    REPLACE(
                        REPLACE(valor_avaliacao, '.', ''),
                        ',', '.'
                    ) AS REAL
                ) <= ?
            """
            parametros.append(valor)

        except ValueError:
            print("\nValor máximo inválido. Filtro de valor ignorado.")

    consulta += " ORDER BY titulo"

    cursor.execute(consulta, parametros)
    resultados = cursor.fetchall()

    print("\n====================================")
    print("RESULTADO DA PESQUISA")
    print("====================================")
    print("Imóveis encontrados:", len(resultados))

    for codigo, titulo, endereco, situacao, valor, link in resultados:

        print("\n------------------------------------")
        print("Código:", codigo)
        print("Imóvel:", titulo)
        print("Endereço:", endereco or "Não informado")
        print("Situação:", situacao or "Não informada")
        print("Avaliação: R$", valor or "Não informado")
        print("Link:", link or "Não informado")

    conexao.close()


if __name__ == "__main__":
    pesquisar()
