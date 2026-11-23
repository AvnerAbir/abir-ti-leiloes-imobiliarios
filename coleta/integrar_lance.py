import csv
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
BASE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PASTA / "base_consolidada_com_caixa.csv"
ORIGEM = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else PASTA / "lance_novo_progressivo.csv"

def ler_csv(caminho, delimitador):
    with caminho.open("r", newline="", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=delimitador)
        return leitor.fieldnames, list(leitor)

def chave_url(url):
    return (url or "").strip().rstrip("/").lower()

def integrar():
    if not BASE.exists():
        raise FileNotFoundError(f"Base não encontrada: {BASE}")
    if not ORIGEM.exists():
        raise FileNotFoundError(f"Arquivo do Lance não encontrado: {ORIGEM}")

    colunas_base, existentes = ler_csv(BASE, ",")
    colunas_origem, coletados = ler_csv(ORIGEM, ";")

    if not colunas_base or len(colunas_base) != 35:
        raise ValueError("A base não apresenta as 35 colunas esperadas.")

    obrigatorias = {"Site_Origem", "Codigo_Imovel", "Link"}
    if not obrigatorias.issubset(colunas_base):
        raise ValueError("A base não contém os campos essenciais.")

    if not obrigatorias.issubset(colunas_origem or []):
        raise ValueError("O arquivo do Lance não contém os campos essenciais.")

    codigos = {
        (r.get("Site_Origem", "").strip(), r.get("Codigo_Imovel", "").strip())
        for r in existentes
    }
    urls = {chave_url(r.get("Link")) for r in existentes if r.get("Link")}

    novos = []
    duplicados = 0
    rejeitados = 0

    for registro in coletados:
        origem = (registro.get("Site_Origem") or "").strip()
        codigo = (registro.get("Codigo_Imovel") or "").strip()
        url = chave_url(registro.get("Link"))

        if not origem or not codigo or not url:
            rejeitados += 1
            continue

        if (origem, codigo) in codigos or url in urls:
            duplicados += 1
            continue

        novo = {coluna: "" for coluna in colunas_base}
        for coluna in colunas_base:
            if coluna in registro:
                novo[coluna] = registro[coluna]

        novos.append(novo)
        codigos.add((origem, codigo))
        urls.add(url)

    if novos:
        temporario = BASE.with_name(BASE.name + ".tmp")
        backup = BASE.with_name(BASE.name + ".bak_antes_lance")

        if not backup.exists():
            backup.write_bytes(BASE.read_bytes())

        try:
            with temporario.open("w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.DictWriter(
                    arquivo,
                    fieldnames=colunas_base,
                    delimiter=",",
                    extrasaction="ignore"
                )
                escritor.writeheader()
                escritor.writerows(existentes)
                escritor.writerows(novos)

            temporario.replace(BASE)
        finally:
            if temporario.exists():
                temporario.unlink()

    print("====================================")
    print("INTEGRACAO LANCE CONCLUIDA")
    print("====================================")
    print("Registros anteriores:", len(existentes))
    print("Registros coletados:", len(coletados))
    print("Novos registros:", len(novos))
    print("Duplicados confirmados:", duplicados)
    print("Rejeitados:", rejeitados)
    print("Total final:", len(existentes) + len(novos))
    print("Colunas preservadas:", len(colunas_base))
    print("Base:", BASE)

if __name__ == "__main__":
    integrar()
