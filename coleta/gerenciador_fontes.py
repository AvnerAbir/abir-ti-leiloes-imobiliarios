import json
from pathlib import Path


ARQUIVO_PADRAO = Path(__file__).with_name("fontes.json")


def carregar_cadastro(caminho=None):
    arquivo = Path(caminho) if caminho else ARQUIVO_PADRAO

    if not arquivo.exists():
        raise FileNotFoundError(f"Cadastro não encontrado: {arquivo}")

    with arquivo.open("r", encoding="utf-8") as f:
        dados = json.load(f)

    validar_cadastro(dados)
    return dados


def validar_cadastro(dados):
    if "fontes" not in dados or "politica_global" not in dados:
        raise ValueError("Estrutura principal do cadastro incompleta")

    fontes = dados["fontes"]
    politica = dados["politica_global"]

    if not isinstance(fontes, list):
        raise ValueError("'fontes' precisa ser uma lista")

    ids = []

    for fonte in fontes:
        obrigatorios = [
            "id", "nome", "categoria",
            "situacao", "intervalo_segundos",
            "coleta_automatica"
        ]

        for campo in obrigatorios:
            if campo not in fonte:
                raise ValueError(
                    f"Campo '{campo}' ausente em uma fonte"
                )

        ids.append(fonte["id"])

        if not isinstance(fonte["intervalo_segundos"], int):
            raise ValueError(
                f"Intervalo inválido: {fonte['id']}"
            )

        if fonte["intervalo_segundos"] < 1:
            raise ValueError(
                f"Intervalo precisa ser positivo: {fonte['id']}"
            )

        if not isinstance(fonte["coleta_automatica"], bool):
            raise ValueError(
                f"Configuração automática inválida: {fonte['id']}"
            )

    if len(ids) != len(set(ids)):
        raise ValueError("Existem IDs de fontes repetidos")

    if politica.get("requisicoes_simultaneas") != 1:
        raise ValueError("O sistema deve permitir apenas uma requisição")

    if not politica.get("respeitar_robots_txt"):
        raise ValueError("A política deve respeitar o robots.txt")

    if politica.get("contornar_bloqueios") is not False:
        raise ValueError("Contorno de bloqueios precisa estar desativado")

    if not politica.get("pausar_em_captcha"):
        raise ValueError("A pausa diante de CAPTCHA é obrigatória")

    codigos_pausa = politica.get("pausar_http", [])

    if 403 not in codigos_pausa or 429 not in codigos_pausa:
        raise ValueError("É obrigatório pausar em HTTP 403 e 429")

    return True


def listar_fontes():
    return carregar_cadastro()["fontes"]


def obter_fontes_habilitadas():
    fontes = listar_fontes()

    return [
        fonte for fonte in fontes
        if fonte["coleta_automatica"] is True
        and fonte["situacao"] == "autorizada"
        and fonte.get("url")
    ]


def resumo_fontes():
    fontes = listar_fontes()
    habilitadas = obter_fontes_habilitadas()

    return {
        "total": len(fontes),
        "habilitadas": len(habilitadas),
        "desabilitadas": len(fontes) - len(habilitadas)
    }
