import csv
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


COLUNAS = [
    "Site_Origem",
    "Modalidade",
    "Codigo_Imovel",
    "Codigo_Leilao",
    "Numero_Lote",
    "Tipo_Imovel",
    "Estado",
    "Municipio",
    "Bairro",
    "Endereco",
    "Area_Terreno",
    "Area_Construida",
    "Valor_Avaliacao",
    "Data_Primeira_Praca",
    "Valor_Primeira_Praca",
    "Data_Segunda_Praca",
    "Valor_Segunda_Praca",
    "Lance_Inicial",
    "Data_Lance_Inicial",
    "Incremento",
    "Matricula",
    "Processo",
    "Ocupacao",
    "Link",
    "Link_Relacao_Leilao",
    "Situacao_Extracao",
    "Classificacao",
]


def normalizar_texto(valor):
    texto = str(valor or "").strip().casefold()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


def normalizar_url(valor):
    url = str(valor or "").strip()

    if not url:
        return ""

    partes = urlsplit(url)
    caminho = partes.path.rstrip("/")

    parametros_rastreamento = {
        "fbclid", "gclid", "dclid", "msclkid"
    }

    consulta = [
        (chave, valor)
        for chave, valor in parse_qsl(
            partes.query, keep_blank_values=True
        )
        if not chave.casefold().startswith("utm_")
        and chave.casefold() not in parametros_rastreamento
    ]

    return urlunsplit((
        partes.scheme.casefold(),
        partes.netloc.casefold(),
        caminho,
        urlencode(consulta, doseq=True),
        ""
    ))


def classificar_registro(valor):
    valor = normalizar_texto(valor)

    if valor in ("valido", "valida", "válido", "válida"):
        return "Valido"

    if valor == "parcial":
        return "Parcial"

    if valor == "erro":
        return "Erro"

    return "Parcial"


def padronizar_registro(registro):
    resultado = {
        coluna: str(registro.get(coluna) or "").strip()
        for coluna in COLUNAS
    }

    resultado["Classificacao"] = classificar_registro(
        resultado["Classificacao"]
    )

    if not resultado["Situacao_Extracao"]:
        resultado["Situacao_Extracao"] = "Não informado"

    return resultado


def assinaturas_confirmadas(registro):
    assinaturas = set()

    origem = normalizar_texto(registro.get("Site_Origem"))
    codigo = normalizar_texto(registro.get("Codigo_Imovel"))

    if origem and codigo:
        assinaturas.add(("CODIGO", origem, codigo))

    link = normalizar_url(registro.get("Link"))

    if link:
        assinaturas.add(("LINK", link))

    return assinaturas


def possiveis_duplicidades(a, b):
    motivos = []

    matricula_a = normalizar_texto(a.get("Matricula"))
    matricula_b = normalizar_texto(b.get("Matricula"))
    uf_a = normalizar_texto(a.get("Estado"))
    uf_b = normalizar_texto(b.get("Estado"))

    if (
        matricula_a
        and matricula_b
        and matricula_a == matricula_b
        and uf_a
        and uf_b
        and uf_a == uf_b
    ):
        motivos.append("Matrícula e UF coincidentes")

    endereco_a = normalizar_texto(a.get("Endereco"))
    endereco_b = normalizar_texto(b.get("Endereco"))
    cidade_a = normalizar_texto(a.get("Municipio"))
    cidade_b = normalizar_texto(b.get("Municipio"))

    if (
        endereco_a
        and endereco_b
        and endereco_a == endereco_b
        and cidade_a
        and cidade_b
        and cidade_a == cidade_b
        and uf_a
        and uf_b
        and uf_a == uf_b
    ):
        motivos.append("Endereço, município e UF coincidentes")

    return motivos


def carregar_base(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        return []

    with caminho.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:
        leitor = csv.DictReader(arquivo)
        return [
            padronizar_registro(linha)
            for linha in leitor
        ]


def salvar_base(caminho, registros):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    temporario = caminho.with_name(caminho.name + ".tmp")

    try:
        with temporario.open(
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as arquivo:
            escritor = csv.DictWriter(
                arquivo,
                fieldnames=COLUNAS,
                extrasaction="ignore"
            )
            escritor.writeheader()
            escritor.writerows(registros)

        temporario.replace(caminho)

    finally:
        if temporario.exists():
            temporario.unlink()


def integrar_registros(caminho, novos_registros):
    existentes = carregar_base(caminho)

    assinaturas = set()

    for registro in existentes:
        assinaturas.update(assinaturas_confirmadas(registro))

    novos = 0
    duplicados = 0
    possiveis = 0
    rejeitados = 0
    alertas = []

    for original in novos_registros:
        registro = padronizar_registro(original)

        if not registro["Site_Origem"] or not registro["Link"]:
            rejeitados += 1
            continue

        chaves = assinaturas_confirmadas(registro)

        if not chaves:
            rejeitados += 1
            continue

        if chaves.intersection(assinaturas):
            duplicados += 1
            continue

        encontrados = []

        for anterior in existentes:
            motivos = possiveis_duplicidades(registro, anterior)

            if motivos:
                encontrados.append({
                    "motivos": motivos,
                    "origem_existente": anterior["Site_Origem"],
                    "origem_nova": registro["Site_Origem"],
                    "link_existente": anterior["Link"],
                    "link_novo": registro["Link"],
                })

        if encontrados:
            possiveis += 1
            alertas.extend(encontrados)

        existentes.append(registro)
        assinaturas.update(chaves)
        novos += 1

    if novos:
        salvar_base(caminho, existentes)

    return {
        "total_anterior": len(existentes) - novos,
        "novos": novos,
        "duplicados_confirmados": duplicados,
        "possiveis_duplicidades": possiveis,
        "rejeitados": rejeitados,
        "total_final": len(existentes),
        "alertas": alertas,
    }
