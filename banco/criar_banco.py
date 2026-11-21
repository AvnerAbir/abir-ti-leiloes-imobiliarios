
import sqlite3

ARQUIVO_BANCO = "banco/leiloes_imoveis.db"


def criar_banco():

    conexao = sqlite3.connect(ARQUIVO_BANCO)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imoveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_lote TEXT UNIQUE,
            codigo_leilao TEXT,
            titulo TEXT,
            situacao_leilao TEXT,
            modalidade TEXT DEFAULT 'Não identificada',
            site_origem TEXT DEFAULT 'Mega Leilões',
            endereco TEXT,
            processo TEXT,
            valor_avaliacao TEXT,
            lance_inicial TEXT,
            incremento TEXT,
            primeira_praca TEXT,
            valor_primeira_praca TEXT,
            segunda_praca TEXT,
            valor_segunda_praca TEXT,
            link TEXT,
            data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Atualiza bancos que ja existiam
    colunas = [
        coluna[1]
        for coluna in cursor.execute(
            "PRAGMA table_info(imoveis)"
        ).fetchall()
    ]

    if "modalidade" not in colunas:
        cursor.execute("""
            ALTER TABLE imoveis
            ADD COLUMN modalidade TEXT DEFAULT 'Não identificada'
        """)

    if "site_origem" not in colunas:
        cursor.execute("""
            ALTER TABLE imoveis
            ADD COLUMN site_origem TEXT DEFAULT 'Mega Leilões'
        """)

    conexao.commit()
    conexao.close()

    print("BANCO DE DADOS ATUALIZADO COM SUCESSO!")
    print("Novos campos: modalidade e site_origem")
    print("Arquivo:", ARQUIVO_BANCO)


if __name__ == "__main__":
    criar_banco()
