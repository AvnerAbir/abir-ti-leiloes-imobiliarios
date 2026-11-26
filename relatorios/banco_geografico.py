from pathlib import Path
import sqlite3

PASTA = Path(__file__).parent
BANCO = PASTA / "base_geografica.db"

def conectar():
    con = sqlite3.connect(BANCO)
    con.execute("""
        CREATE TABLE IF NOT EXISTS geolocalizacao (
            codigo_imovel TEXT PRIMARY KEY,
            endereco TEXT,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'PENDENTE',
            fonte TEXT,
            atualizado_em TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS pontos_interesse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_imovel TEXT NOT NULL,
            categoria TEXT,
            nome TEXT,
            latitude REAL,
            longitude REAL,
            distancia_m REAL,
            fonte TEXT,
            consultado_em TEXT,
            UNIQUE(codigo_imovel, categoria, nome, latitude, longitude)
        )
    """)
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_geo_status
        ON geolocalizacao(status)
    """)
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_poi_imovel
        ON pontos_interesse(codigo_imovel)
    """)
    con.commit()
    return con

if __name__ == "__main__":
    con = conectar()
    print("Banco geografico criado:", BANCO)
    print("Tabelas:", [
        x[0] for x in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    ])
    con.close()
