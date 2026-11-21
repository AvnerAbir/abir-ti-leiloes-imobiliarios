 
import sqlite3

ARQUIVO_BANCO = "banco/leiloes_imoveis.db"


def consultar_imoveis():

    conexao = sqlite3.connect(ARQUIVO_BANCO)
    cursor = conexao.cursor()

    cursor.execute("SELECT COUNT(*) FROM imoveis")
    total = cursor.fetchone()[0]

    print("\n====================================")
    print(" CONSULTA AO BANCO DE IMÓVEIS")
    print("====================================")
    print("Total de imóveis cadastrados:", total)

    cursor.execute("""
        SELECT codigo_lote, titulo, situacao_leilao, valor_avaliacao
        FROM imoveis
        ORDER BY codigo_lote
    """)

    registros = cursor.fetchall()

    print("\nLISTA DE IMÓVEIS:\n")

    for registro in registros:
        codigo, titulo, situacao, valor = registro

        print("------------------------------------")
        print("Código:", codigo)
        print("Título:", titulo)
        print("Situação:", situacao or "Não informada")
        print("Avaliação: R$", valor or "Não informado")

    conexao.close()


if __name__ == "__main__":
    consultar_imoveis()
