import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = "coleta/lance_novo_progressivo.csv"

def executar():
    subprocess.run(
        ["git", "add", ARQUIVO],
        cwd=RAIZ,
        check=True
    )

    resultado = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", ARQUIVO],
        cwd=RAIZ
    )

    if resultado.returncode == 0:
        print("Nenhum dado novo para enviar.")
        return

    if resultado.returncode != 1:
        raise RuntimeError("Falha ao verificar alteracoes.")

    subprocess.run(
        ["git", "commit", "--only", "-m",
         "Atualiza dados coletados do Lance", "--", ARQUIVO],
        cwd=RAIZ,
        check=True
    )

    subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=RAIZ,
        check=True
    )

    print("CSV enviado ao GitHub com sucesso.")

if __name__ == "__main__":
    try:
        executar()
    except Exception as erro:
        print("ERRO NO ENVIO:", erro)
        sys.exit(1)
