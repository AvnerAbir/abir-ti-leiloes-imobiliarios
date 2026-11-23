
import csv
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


# ==========================================================
# CONFIGURACOES
# ==========================================================

URL_BASE = (
    "https://www.lancenoleilao.com.br/"
    "pesquisa.php?classificacao=&uf=&cidade=&bairro="
)

PASTA = Path("coleta")

ARQUIVO_SAIDA = PASTA / "lance_novo_progressivo.csv"
ARQUIVO_ERROS = PASTA / "lance_novo_erros.csv"

LIMITE_TESTE = 510
MAX_PAGINAS = 100

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
]


# ==========================================================
# FUNCOES AUXILIARES
# ==========================================================

def normalizar(texto):
    texto = str(texto or "").lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )


def limpar(texto):
    return re.sub(r"\s+", " ", str(texto or "")).strip()



def _localizar_marcador(linha, marcador):
    original = str(linha or "")
    normalizado = normalizar(original)
    alvo = normalizar(marcador)

    posicao = normalizado.find(alvo)
    if posicao < 0:
        return None

    mapa = []
    for indice, caractere in enumerate(original):
        convertido = normalizar(caractere)
        mapa.extend([indice] * len(convertido))

    if not mapa or posicao + len(alvo) > len(mapa):
        return None

    inicio_original = mapa[posicao]
    fim_original = mapa[posicao + len(alvo) - 1] + 1
    return inicio_original, fim_original


def obter_linha(texto, prefixo):
    for linha in texto.splitlines():
        linha_limpa = limpar(linha)
        if _localizar_marcador(linha_limpa, prefixo) is not None:
            return linha_limpa
    return ""


def valor_apos_prefixo(texto, prefixo):
    for linha in texto.splitlines():
        linha_limpa = limpar(linha)
        posicoes = _localizar_marcador(linha_limpa, prefixo)

        if posicoes is not None:
            return limpar(linha_limpa[posicoes[1]:])

    return ""


def extrair_endereco(texto):
    endereco = valor_apos_prefixo(texto, "Localização:")
    if endereco:
        return endereco

    endereco = valor_apos_prefixo(texto, "Ampliar o mapa para:")
    if endereco:
        return endereco

    return ""


def extrair_valor(texto, padrao):
    resultado = re.search(
        padrao,
        texto,
        re.IGNORECASE
    )

    return resultado.group(1).strip() if resultado else ""


def extrair_valor_praca(texto, numero):
    for linha in texto.splitlines():
        linha_normalizada = normalizar(linha)

        identificador = (
            f"lance minimo para arrematacao em {numero}"
        )

        if identificador in linha_normalizada:
            resultado = re.search(
                r"([\d.]+,\d{2})",
                linha
            )

            if resultado:
                return resultado.group(1)

    return ""


def extrair_proxima_linha(texto, prefixo):
    linhas = [limpar(x) for x in texto.splitlines()]

    for i, linha in enumerate(linhas):
        if normalizar(linha).startswith(normalizar(prefixo)):
            if i + 1 < len(linhas):
                return linhas[i + 1]

    return ""



def identificar_tipo(descricao):
    texto = normalizar(descricao)

    regras = [
        ("Apartamento", "apartamento"),
        ("Casa", "casa"),
        ("Casa", "residencia"),
        ("Terreno", "terreno"),
        ("Galpao", "galpao"),
        ("Sala Comercial", "sala comercial"),
        ("Sala Comercial", "sala n"),
        ("Sala Comercial", "sala "),
        ("Predio", "predio"),
        ("Fazenda", "fazenda"),
        ("Sitio", "sitio"),
        ("Chacara", "chacara"),
        ("Vaga de Garagem", "vaga de garagem"),
        ("Box de Garagem", "box de garagem"),
        ("Unidade Habitacional", "unidade habitacional"),
    ]

    for tipo, palavra in regras:
        if palavra in texto:
            return tipo

    return ""






def extrair_localizacao(endereco, texto):
    resultado = {"Estado": "", "Municipio": "", "Bairro": ""}

    # Separa o endereço em trechos.
    partes = [limpar(p) for p in endereco.split(",") if limpar(p)]

    # Procura o trecho que termina em município-UF ou município/UF.
    for i, parte in enumerate(partes):
        correspondencia = re.search(r"[-/]([A-Z]{2})$", parte.strip())

        if not correspondencia:
            continue

        uf = correspondencia.group(1)
        nome = parte[:correspondencia.start()].strip()

        # Endereço de mapa: número - bairro - município/UF.
        subpartes = [
            limpar(p) for p in re.split(r"\s+-\s+", nome)
            if limpar(p)
        ]

        if subpartes:
            resultado["Municipio"] = subpartes[-1]
            resultado["Estado"] = uf

            if len(subpartes) >= 2:
                resultado["Bairro"] = subpartes[-2]
            elif i > 0:
                resultado["Bairro"] = partes[i - 1]

            break

    # Alternativa: município/UF na linha Nº DO BEM.
    if not resultado["Municipio"]:
        linha_bem = obter_linha(texto, "Nº DO BEM:")
        padrao_bem = re.search(
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s.'’-]+?)\s*\(([A-Z]{2})\)?",
            linha_bem
        )

        if padrao_bem:
            resultado["Municipio"] = limpar(padrao_bem.group(1))
            resultado["Estado"] = padrao_bem.group(2)

    return resultado



def extrair_data_praca(texto, numero):
    linhas = [limpar(x) for x in texto.splitlines()]

    prefixo = f"{numero}ª Praça:"

    for i, linha in enumerate(linhas):
        if normalizar(linha).startswith(normalizar(prefixo)):
            bloco = [linha]

            if i + 1 < len(linhas):
                bloco.append(linhas[i + 1])

            combinado = " ".join(bloco)

            encerramento = re.search(
                r"Encerramento:\s*(.*?)(?=\s+\d+[ªº]|\s*$)",
                combinado,
                re.IGNORECASE
            )

            if encerramento:
                return limpar(encerramento.group(1))

    return ""


def extrair_ocupacao(texto):
    linhas = [
        limpar(x)
        for x in texto.splitlines()
    ]

    observacoes = [
        linha for linha in linhas
        if normalizar(linha).startswith("obs.")
    ]

    conteudo = normalizar(" ".join(observacoes))

    if "desocupado" in conteudo:
        return "Desocupado"

    if "ocupado" in conteudo:
        return "Ocupado"

    return ""


def extrair_area(descricao, tipo):
    descricao_norm = normalizar(descricao)

    area_construida = ""
    area_terreno = ""

    padroes_construida = [
        r"area construida\s+de\s*([\d.,]+)\s*m",
        r"area privativa\s+de\s*([\d.,]+)\s*m",
        r"area\s+de\s*([\d.,]+)\s*m",
    ]

    for padrao in padroes_construida:
        resultado = re.search(padrao, descricao_norm)

        if resultado:
            area_construida = resultado.group(1)
            break

    resultado = re.search(
        r"area total\s+de\s*([\d.,]+)\s*m",
        descricao_norm
    )

    if resultado:
        area_terreno = resultado.group(1)

    return area_terreno, area_construida


# EXTRACAO DE UM IMOVEL
# ==========================================================

def extrair_imovel(pagina, lote):

    codigo = lote["Codigo_Lote"]
    link = lote["Link"]

    resposta = pagina.goto(
        link,
        wait_until="domcontentloaded",
        timeout=60000
    )

    if not resposta or resposta.status != 200:
        raise Exception("Página não respondeu com HTTP 200.")

    pagina.wait_for_timeout(800)

    texto = pagina.locator("body").inner_text()

    if len(texto.strip()) < 300:
        raise Exception("Página retornou conteúdo insuficiente.")

    descricao = valor_apos_prefixo(texto, "Descrição:")
    endereco = extrair_endereco(texto)

    codigo_leilao = valor_apos_prefixo(texto, "Código:")
    codigo_leilao = re.sub(r"\D", "", codigo_leilao)

    numero_lote = extrair_valor(
        texto,
        r"\bLOTE\s*(\d+)"
    )

    modalidade = valor_apos_prefixo(texto, "Tipo:")

    matricula = extrair_valor(
        descricao,
        r"MATR[IÍ]CULA\s+(\d+)"
    )

    valor_primeira = extrair_valor_praca(texto, 1)
    valor_segunda = extrair_valor_praca(texto, 2)

    lance_inicial = extrair_proxima_linha(
        texto,
        "Lance Mínimo:"
    )

    incremento = extrair_proxima_linha(
        texto,
        "Incremento mínimo:"
    )

    data_primeira = extrair_data_praca(texto, 1)
    data_segunda = extrair_data_praca(texto, 2)

    localizacao = extrair_localizacao(
        endereco,
        texto
    )

    area_terreno, area_construida = extrair_area(
        descricao,
        identificar_tipo(descricao)
    )

    registro = {
        "Site_Origem": "Lance no Leilão",
        "Modalidade": modalidade,
        "Codigo_Imovel": f"LNL-{codigo}",
        "Codigo_Leilao": codigo_leilao,
        "Numero_Lote": numero_lote,
        "Tipo_Imovel": identificar_tipo(descricao),
        "Estado": localizacao["Estado"],
        "Municipio": localizacao["Municipio"],
        "Bairro": localizacao["Bairro"],
        "Endereco": endereco,
        "Area_Terreno": area_terreno,
        "Area_Construida": area_construida,
        "Valor_Avaliacao": "",
        "Data_Primeira_Praca": data_primeira,
        "Valor_Primeira_Praca": valor_primeira,
        "Data_Segunda_Praca": data_segunda,
        "Valor_Segunda_Praca": valor_segunda,
        "Lance_Inicial": lance_inicial,
        "Data_Lance_Inicial": "",
        "Incremento": incremento,
        "Matricula": matricula,
        "Processo": "",
        "Ocupacao": extrair_ocupacao(texto),
        "Link": link,
        "Link_Relacao_Leilao": (
            "https://www.lancenoleilao.com.br/"
            f"leilao.php?idLeilao={codigo_leilao}"
            if codigo_leilao else ""
        ),
        "Situacao_Extracao": "OK",

    }

    if not registro["Codigo_Leilao"]:
        raise Exception("Código do leilão não identificado.")

    if not registro["Endereco"]:
        raise Exception("Endereço não identificado.")

    return registro


# ==========================================================
# COLETA DA LISTAGEM
# ==========================================================

def gerar_lista(pagina):

    lotes = {}
    pagina_numero = 1

    while pagina_numero <= MAX_PAGINAS:

        if pagina_numero == 1:
            url = URL_BASE
        else:
            url = f"{URL_BASE}&pagina={pagina_numero}"

        print(f"\nConsultando listagem página {pagina_numero}...")

        
        resposta = None

        for tentativa in range(1, 4):

            try:
                print(
                    f"Tentativa {tentativa}/3 "
                    f"para acessar a página {pagina_numero}..."
                )

                resposta = pagina.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                if resposta and resposta.status == 200:
                    print("Página carregada com sucesso.")
                    break

                print("STATUS HTTP:", resposta.status if resposta else "SEM RESPOSTA")
                print("URL FINAL:", resposta.url if resposta else url)
                print(f"Resposta invalida na tentativa {tentativa}.")

            except Exception as erro:
                print(
                    f"Falha na tentativa {tentativa}: {erro}"
                )

            if tentativa < 3:
                print("Aguardando 3 segundos para tentar novamente...")
                pagina.wait_for_timeout(3000)

        if not resposta or resposta.status != 200:
            raise Exception(
                f"Falha ao acessar página {pagina_numero} "
                f"após 3 tentativas."
            )


        pagina.wait_for_timeout(1000)

        cartoes = pagina.locator(
            ".col-lg-8[onclick*='lote.php?idLote=']"
        )

        quantidade = cartoes.count()

        if quantidade == 0:
            if pagina_numero == 1:
                raise Exception(
                    "Nenhum lote encontrado na primeira página."
                )

            print("Fim da paginação.")
            break

        for i in range(quantidade):

            cartao = cartoes.nth(i)

            comando = cartao.get_attribute("onclick") or ""

            resultado = re.search(
                r"idLote=(\d+)",
                comando
            )

            if not resultado:
                continue

            codigo = resultado.group(1)
            texto_cartao = cartao.inner_text()

            categoria = re.search(
                r"CATEGORIA:\s*([^\r\n]+)",
                texto_cartao,
                re.IGNORECASE
            )

            nome_categoria = (
                limpar(categoria.group(1))
                if categoria else ""
            )

            if normalizar(nome_categoria) != "imoveis":
                continue

            lotes[codigo] = {
                "Codigo_Lote": codigo,
                "Link": urljoin(
                    "https://www.lancenoleilao.com.br/",
                    f"lote.php?idLote={codigo}"
                )
            }

        print(
            f"Imóveis únicos encontrados até agora: {len(lotes)}"
        )

        pagina_numero += 1

    if pagina_numero > MAX_PAGINAS:
        raise Exception(
            "Limite de páginas atingido. Verifique a paginação."
        )

    return list(lotes.values())


# ==========================================================
# EXECUCAO PRINCIPAL
# ==========================================================


def salvar_csv_seguro(caminho, registros, campos):
    temporario = caminho.with_name(caminho.name + ".tmp")

    with open(
        temporario,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos,
            delimiter=";"
        )
        escritor.writeheader()
        escritor.writerows(registros)

    temporario.replace(caminho)


def carregar_csv_existente(caminho):
    if not caminho.exists():
        return []

    with open(
        caminho,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def executar():

    PASTA.mkdir(exist_ok=True)

    resultados = carregar_csv_existente(ARQUIVO_SAIDA)
    erros = carregar_csv_existente(ARQUIVO_ERROS)

    codigos_salvos = {
        registro.get("Codigo_Imovel", "")
        for registro in resultados
    }

    novos = 0
    falhas_novas = 0

    with sync_playwright() as p:

        navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page(locale="pt-BR")

        try:

            lotes = gerar_lista(pagina)

            print("\n====================================")
            print("INICIANDO COLETA COM SALVAMENTO PROGRESSIVO")
            print("====================================")

            for numero, lote in enumerate(lotes, start=1):

                codigo = lote["Codigo_Lote"]
                codigo_imovel = f"LNL-{codigo}"

                print(
                    f"\nImovel {numero}/{len(lotes)}: {codigo}"
                )

                if codigo_imovel in codigos_salvos:
                    print("Ja salvo anteriormente. Pulando.")
                    continue

                try:

                    registro = extrair_imovel(pagina, lote)

                    registro["Situacao_Extracao"] = "OK"

                    resultados.append(registro)
                    codigos_salvos.add(codigo_imovel)

                    erros = [
                        erro for erro in erros
                        if erro.get("Codigo_Lote") != codigo
                    ]

                    salvar_csv_seguro(
                        ARQUIVO_SAIDA,
                        resultados,
                        COLUNAS
                    )

                    salvar_csv_seguro(
                        ARQUIVO_ERROS,
                        erros,
                        ["Codigo_Lote", "Link", "Erro"]
                    )

                    novos += 1
                    print("Salvo com sucesso no CSV.")

                except Exception as erro:

                    erros = [
                        item for item in erros
                        if item.get("Codigo_Lote") != codigo
                    ]

                    erros.append({
                        "Codigo_Lote": codigo,
                        "Link": lote["Link"],
                        "Erro": str(erro)
                    })

                    salvar_csv_seguro(
                        ARQUIVO_ERROS,
                        erros,
                        ["Codigo_Lote", "Link", "Erro"]
                    )

                    falhas_novas += 1
                    print("FALHA:", erro)

        finally:
            navegador.close()

    print("\n====================================")
    print("RESULTADO DA COLETA")
    print("====================================")
    print("Imoveis selecionados nesta execucao:", len(lotes))
    print("Novos registros salvos:", novos)
    print("Total de registros salvos:", len(resultados))
    print("Falhas nesta execucao:", falhas_novas)
    print("Falhas registradas:", len(erros))
    print("Arquivo de dados:", ARQUIVO_SAIDA)
    print("Arquivo de erros:", ARQUIVO_ERROS)

    print("\nEnviando dados ao GitHub...")
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(PASTA / "enviar_lance_github.py")],
        check=True
    )


if __name__ == "__main__":
    executar()
