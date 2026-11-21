
import csv
import sqlite3
import os

ARQUIVO_CSV = "todos_imoveis_detalhados.csv"
ARQUIVO_BANCO = "banco/leiloes_imoveis.db"


def importar_imoveis():

    if not os.path.exists(ARQUIVO_CSV):
        print("ERRO: Arquivo CSV não encontrado.")
        return

    conexao = sqlite3.connect(ARQUIVO_BANCO)
    cursor = conexao.cursor()

    importados = 0
    ignorados = 0

    with open(ARQUIVO_CSV, "r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")

        for linha in leitor:

            codigo = (linha.get("Codigo_Lote") or "").strip()

            if not codigo:
                ignorados += 1
                continue

            cursor.execute("""
                INSERT INTO imoveis (
                    codigo_lote, codigo_leilao, titulo,
                    situacao_leilao, modalidade, site_origem,
                    endereco, processo, valor_avaliacao,
                    lance_inicial, incremento, primeira_praca,
                    valor_primeira_praca, segunda_praca,
                    valor_segunda_praca, link
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(codigo_lote) DO UPDATE SET
                    codigo_leilao = excluded.codigo_leilao,
                    titulo = excluded.titulo,
                    situacao_leilao = excluded.situacao_leilao,
                    modalidade = excluded.modalidade,
                    site_origem = excluded.site_origem,
                    endereco = excluded.endereco,
                    processo = excluded.processo,
                    valor_avaliacao = excluded.valor_avaliacao,
                    lance_inicial = excluded.lance_inicial,
                    incremento = excluded.incremento,
                    primeira_praca = excluded.primeira_praca,
                    valor_primeira_praca = excluded.valor_primeira_praca,
                    segunda_praca = excluded.segunda_praca,
                    valor_segunda_praca = excluded.valor_segunda_praca,
                    link = excluded.link,
                    data_atualizacao = CURRENT_TIMESTAMP
            """, (
                codigo,
                linha.get("Codigo_Leilao", ""),
                linha.get("Titulo", ""),
                linha.get("Situacao_Leilao", ""),
                linha.get("Modalidade", "Não identificada"),
                linha.get("Site_Origem", "Mega Leilões"),
                linha.get("Endereco", ""),
                linha.get("Processo", ""),
                linha.get("Valor_Avaliacao", ""),
                linha.get("Lance_Inicial", ""),
                linha.get("Incremento", ""),
                linha.get("Primeira_Praca", ""),
                linha.get("Valor_Primeira_Praca", ""),
                linha.get("Segunda_Praca", ""),
                linha.get("Valor_Segunda_Praca", ""),
                linha.get("Link", "")
            ))

            importados += 1

    conexao.commit()
    conexao.close()

    print("IMPORTAÇÃO CONCLUÍDA!")
    print("Registros processados:", importados)
    print("Registros ignorados:", ignorados)


if __name__ == "__main__":
    importar_imoveis()
