
import json
import hashlib
import hmac
import unicodedata
import math
from pathlib import Path

import pandas as pd
import streamlit as st


# ==========================================================
# CONFIGURACOES
# ==========================================================

PASTA = Path(__file__).parent
ARQUIVO_BASE = PASTA / "coleta" / "base_consolidada_com_caixa.csv"
ARQUIVO_USUARIOS = PASTA / "usuarios.json"

# Manter True durante o desenvolvimento.
# Antes da publicacao, a autenticacao sera obrigatoria.
MODO_TESTE_SEM_LOGIN = False

st.set_page_config(
    page_title="ABIR TI | LeilÃµes ImobiliÃ¡rios",
    page_icon="ðŸ ",
    layout="wide"
)


# ==========================================================
# IDENTIDADE VISUAL
# ==========================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F6F9;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

.abir-header {
    background: #142B46;
    padding: 28px 32px;
    border-radius: 12px;
    margin-bottom: 25px;
    color: white;
}

.abir-logo {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 3px;
}

.abir-subtitle {
    color: #D6E2EF;
    font-size: 13px;
    letter-spacing: 1px;
}

.abir-description {
    color: white;
    font-size: 15px;
    margin-top: 20px;
}

.metric-card {
    background: white;
    border: 1px solid #E1E7EF;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
}

.metric-label {
    color: #65758A;
    font-size: 13px;
}

.metric-value {
    color: #142B46;
    font-size: 27px;
    font-weight: 750;
}

.section-title {
    color: #142B46;
    font-weight: 700;
}

.property-title {
    color: #142B46;
    font-size: 19px;
    font-weight: 700;
}

.property-info {
    color: #536579;
    font-size: 14px;
}


.stButton > button,
.stDownloadButton > button {
    background-color: #006B70 !important;
    color: #FFFFFF !important;
    border: 1px solid #006B70 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #004F54 !important;
    color: #FFFFFF !important;
    border-color: #004F54 !important;
}

.stButton > button:focus,
.stDownloadButton > button:focus {
    box-shadow: 0 0 0 2px #80B8BA !important;
}
footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# FUNCOES DE AUTENTICACAO
# ==========================================================

def calcular_hash_senha(senha, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        600000
    ).hex()

def carregar_usuarios():

    # Primeiro, tenta carregar os usuÃ¡rios dos Secrets na nuvem.
    try:
        usuarios_json = st.secrets.get("usuarios_json")

        if usuarios_json:
            dados = json.loads(usuarios_json)
            return dados.get("usuarios", [])

    except Exception:
        pass

    # Se nÃ£o houver Secrets, utiliza o arquivo local.
    if not ARQUIVO_USUARIOS.exists():
        return None

    try:
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        return dados.get("usuarios", [])

    except Exception:
        return []


def validar_login(usuario, senha):

    usuarios = carregar_usuarios()

    if not usuarios:
        return False, None

    for cadastro in usuarios:

        usuario_cadastrado = cadastro.get("usuario", "")
        salt = cadastro.get("salt", "")
        hash_armazenado = cadastro.get("senha_hash", "")

        if usuario.casefold() == usuario_cadastrado.casefold():

            hash_digitado = calcular_hash_senha(senha, salt)

            if hmac.compare_digest(hash_digitado, hash_armazenado):
                return True, cadastro.get("perfil", usuario)

    return False, None


def verificar_acesso():

    usuarios = carregar_usuarios()

    if usuarios is None and MODO_TESTE_SEM_LOGIN:

        st.session_state["autenticado"] = True
        st.session_state["perfil_atual"] = "Desenvolvimento"

        return True

    if not usuarios:

        st.error(
            "Acesso indisponÃ­vel. A configuraÃ§Ã£o dos usuÃ¡rios "
            "precisa ser realizada."
        )
        st.stop()

    if st.session_state.get("autenticado", False):
        return True

    st.markdown("""
    <div class="abir-header">
        <div class="abir-logo">ABIR TI</div>
        <div class="abir-subtitle">
            INTELIGÃŠNCIA EM LEILÃ•ES IMOBILIÃRIOS
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Acesso Ã  plataforma")
    st.caption("Ãrea restrita para usuÃ¡rios autorizados.")

    with st.form("form_login"):

        usuario = st.text_input("UsuÃ¡rio")
        senha = st.text_input("Senha", type="password")

        entrar = st.form_submit_button(
            "Entrar",
            use_container_width=True
        )

    if entrar:

        sucesso, perfil = validar_login(usuario.strip(), senha)

        if sucesso:

            st.session_state["autenticado"] = True
            st.session_state["perfil_atual"] = perfil

            st.rerun()

        else:
            st.error("UsuÃ¡rio ou senha invÃ¡lidos.")

    st.stop()


# ==========================================================
# CARREGAMENTO DA BASE
# ==========================================================

@st.cache_data(ttl=60)
def carregar_imoveis():

    if not ARQUIVO_BASE.exists():
        return pd.DataFrame()

    df = pd.read_csv(
        ARQUIVO_BASE,
        encoding="utf-8-sig",
        dtype=str
    )

    return df.fillna("")


# ==========================================================
# FUNCOES AUXILIARES
# ==========================================================

def opcoes_coluna(df, coluna):

    if coluna not in df.columns:
        return []

    valores = df[coluna].astype(str).str.strip()

    valores = valores[
        (valores != "") &
        (valores.str.lower() != "nan")
    ]

    return sorted(
        valores.unique().tolist(),
        key=str.casefold
    )


def mostrar_valor(valor):

    if pd.isna(valor):
        return "NÃ£o informado"

    valor = str(valor).strip()

    if not valor or valor.lower() == "nan":
        return "NÃ£o informado"

    return valor


def normalizar_texto(texto):

    texto = str(texto).strip().casefold()

    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


def classificar_registro(valor):

    valor = normalizar_texto(valor)
    valor = valor.replace("?", "a")

    if valor in ["valido", "valida"]:
        return "V\u00e1lido"

    if valor == "parcial":
        return "Parcial"

    if valor == "erro":
        return "Erro"

    return valor.title() if valor else "N\u00e3o informado"



def classificar_modalidade(valor):

    valor = normalizar_texto(valor)

    if valor in ["leilao sfi", "extrajudicial", "judicial"]:
        return "Leil\u00e3o"

    if valor == "venda direta online":
        return "Venda direta"

    if valor == "venda online":
        return "Venda online"

    if valor == "licitacao aberta":
        return "Licita\u00e7\u00e3o"

    return "N\u00e3o identificada"


def numero_formatado(valor):

    return f"{valor:,}".replace(",", ".")


# ==========================================================
# AUTENTICACAO
# ==========================================================

verificar_acesso()


# ==========================================================
# CARREGAR DADOS
# ==========================================================

df = carregar_imoveis()

if df.empty:

    st.error("A base consolidada nÃ£o foi encontrada ou estÃ¡ vazia.")

    st.info(
        "Verifique o arquivo "
        "coleta/base_consolidada_leiloes.csv"
    )

    st.stop()


# ==========================================================
# GARANTIR COLUNAS
# ==========================================================

colunas_necessarias = [
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
    "Classificacao"
]

for coluna in colunas_necessarias:

    if coluna not in df.columns:
        df[coluna] = ""


df["Classificacao_Exibicao"] = (
    df["Classificacao"].apply(classificar_registro)
)

df["Categoria_Modalidade"] = (
    df["Modalidade"].apply(classificar_modalidade)
)


# ==========================================================
# CABECALHO
# ==========================================================


st.markdown(
    """
    <div class="abir-header">
        <div class="abir-logo">ABIR TI</div>
        <div class="abir-subtitle">
            INTELIGÃŠNCIA EM LEILÃ•ES IMOBILIÃRIOS
        </div>
        <div class="abir-description">
            Encontre oportunidades imobiliÃ¡rias.<br>
            Consulte imÃ³veis de leilÃµes judiciais e extrajudiciais
            em diferentes portais, em um sÃ³ lugar.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


if st.session_state.get("perfil_atual"):

    st.caption(
        f"UsuÃ¡rio conectado: {st.session_state['perfil_atual']}"
    )


# ==========================================================
# MENU LATERAL
# ==========================================================

with st.sidebar:

    st.markdown("## ABIR TI")

    st.caption("Consulta de imÃ³veis em leilÃ£o")

    st.divider()

    st.subheader("Filtros de pesquisa")

    if st.button("Sair da plataforma", use_container_width=True):

        st.session_state["autenticado"] = False
        st.session_state["perfil_atual"] = None

        st.rerun()


# ==========================================================
# INDICADORES
# ==========================================================

total = len(df)

validos = (
    df["Classificacao_Exibicao"] == "VÃ¡lido"
).sum()

parciais = (
    df["Classificacao_Exibicao"] == "Parcial"
).sum()

erros = (
    df["Classificacao_Exibicao"] == "Erro"
).sum()


st.markdown(
    '<h3 class="section-title">VisÃ£o geral da base</h3>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

indicadores = [
    (col1, "Total de imÃ³veis", total),
    (col2, "Cadastros vÃ¡lidos", validos),
    (col3, "Cadastros parciais", parciais),
    (col4, "Registros com erro", erros)
]

for coluna, titulo, valor in indicadores:

    with coluna:

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{titulo}</div>
            <div class="metric-value">
                {numero_formatado(valor)}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==========================================================
# FILTROS
# ==========================================================

st.divider()

st.markdown(
    '<h3 class="section-title">Localize seu imÃ³vel</h3>',
    unsafe_allow_html=True
)


with st.sidebar:

    estados = ["Todos"] + opcoes_coluna(df, "Estado")

    estado = st.selectbox(
        "Estado (UF)",
        estados
    )

    base_municipios = df.copy()

    if estado != "Todos":

        base_municipios = base_municipios[
            base_municipios["Estado"] == estado
        ]

    municipios = ["Todos"] + opcoes_coluna(
        base_municipios,
        "Municipio"
    )

    municipio = st.selectbox(
        "MunicÃ­pio",
        municipios
    )

    base_bairros = base_municipios.copy()

    if municipio != "Todos":

        base_bairros = base_bairros[
            base_bairros["Municipio"] == municipio
        ]

    bairros = ["Todos"] + opcoes_coluna(
        base_bairros,
        "Bairro"
    )

    bairro = st.selectbox(
        "Bairro",
        bairros
    )

    portais = ["Todos"] + opcoes_coluna(
        df,
        "Site_Origem"
    )

    portal = st.selectbox(
        "Portal",
        portais
    )

    tipos = ["Todos"] + opcoes_coluna(
        df,
        "Tipo_Imovel"
    )

    tipo = st.selectbox(
        "Tipo de imÃ³vel",
        tipos
    )

    categorias = ["Todas"] + opcoes_coluna(
        df,
        "Categoria_Modalidade"
    )

    categoria_modalidade = st.selectbox(
        "Categoria da oportunidade",
        categorias
    )

    situacoes = [
        "VÃ¡lidos e parciais",
        "Somente vÃ¡lidos",
        "Somente parciais",
        "Todos, incluindo erros"
    ]

    situacao = st.selectbox(
        "ClassificaÃ§Ã£o do cadastro",
        situacoes
    )


# ==========================================================
# APLICAR FILTROS
# ==========================================================

resultado = df.copy()

if estado != "Todos":

    resultado = resultado[
        resultado["Estado"] == estado
    ]

if municipio != "Todos":

    resultado = resultado[
        resultado["Municipio"] == municipio
    ]

if bairro != "Todos":

    resultado = resultado[
        resultado["Bairro"] == bairro
    ]

if portal != "Todos":

    resultado = resultado[
        resultado["Site_Origem"] == portal
    ]

if tipo != "Todos":

    resultado = resultado[
        resultado["Tipo_Imovel"] == tipo
    ]

if categoria_modalidade != "Todas":

    resultado = resultado[
        resultado["Categoria_Modalidade"] == categoria_modalidade
    ]


if situacao == "VÃ¡lidos e parciais":

    resultado = resultado[
        resultado["Classificacao_Exibicao"].isin(
            ["VÃ¡lido", "Parcial"]
        )
    ]

elif situacao == "Somente vÃ¡lidos":

    resultado = resultado[
        resultado["Classificacao_Exibicao"] == "VÃ¡lido"
    ]

elif situacao == "Somente parciais":

    resultado = resultado[
        resultado["Classificacao_Exibicao"] == "Parcial"
    ]


# ==========================================================
# PESQUISA LIVRE
# ==========================================================

pesquisa = st.text_input(
    "Pesquisar por endereÃ§o, cÃ³digo, processo ou palavra-chave",
    placeholder="Ex.: apartamento, BrasÃ­lia, 235138..."
)

if pesquisa.strip():

    termo = normalizar_texto(pesquisa)

    colunas_busca = [
        "Codigo_Imovel",
        "Codigo_Leilao",
        "Numero_Lote",
        "Tipo_Imovel",
        "Estado",
        "Municipio",
        "Bairro",
        "Endereco",
        "Processo",
        "Matricula",
        "Site_Origem",
        "Modalidade"
    ]

    mascara = pd.Series(
        False,
        index=resultado.index
    )

    for coluna in colunas_busca:

        mascara |= (
            resultado[coluna]
            .apply(normalizar_texto)
            .str.contains(
                termo,
                regex=False,
                na=False
            )
        )

    resultado = resultado[mascara]


# ==========================================================
# RESULTADOS
# ==========================================================

st.divider()

st.markdown(
    '<h3 class="section-title">ImÃ³veis encontrados</h3>',
    unsafe_allow_html=True
)

total_resultados = len(resultado)

st.write(
    f"**{numero_formatado(total_resultados)} imÃ³veis encontrados**"
)


if resultado.empty:

    st.info("Nenhum imÃ³vel corresponde aos filtros selecionados.")

else:

    resultado = resultado.reset_index(drop=True)

    # ------------------------------------------------------
    # DOWNLOAD
    # ------------------------------------------------------

    csv_resultado = resultado.drop(
        columns=["Classificacao_Exibicao"],
        errors="ignore"
    ).to_csv(
        index=False,
        sep=";"
    ).encode("utf-8-sig")

    st.download_button(
        "ðŸ“¥ Baixar resultados da pesquisa",
        data=csv_resultado,
        file_name="resultado_leiloes.csv",
        mime="text/csv"
    )


    # ------------------------------------------------------
    # PAGINACAO
    # ------------------------------------------------------

    por_pagina = 10

    total_paginas = math.ceil(
        total_resultados / por_pagina
    )

    if total_paginas > 1:

        pagina = st.selectbox(
            "PÃ¡gina de resultados",
            list(range(1, total_paginas + 1))
        )

    else:
        pagina = 1

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    resultados_pagina = resultado.iloc[inicio:fim]

    st.caption(
        f"Exibindo {inicio + 1} atÃ© "
        f"{min(fim, total_resultados)} "
        f"de {numero_formatado(total_resultados)} imÃ³veis."
    )

    # ------------------------------------------------------
    # CARTOES DOS IMOVEIS
    # ------------------------------------------------------

    def _chave_selecao_abir(registro, indice):
        codigo = str(registro.get("Codigo_Imovel", "")).strip()
        codigo = codigo.replace(" ", "_")
        return f"abir_selecionar_{codigo or 'sem_codigo'}_{indice}"

    chaves_selecao_pagina = []

    for indice_resultado, registro in resultados_pagina.iterrows():
        chave = _chave_selecao_abir(registro, indice_resultado)
        chaves_selecao_pagina.append(chave)

        if chave not in st.session_state:
            st.session_state[chave] = False

    def _marcar_pagina_abir():
        for chave in chaves_selecao_pagina:
            st.session_state[chave] = True

    def _limpar_pagina_abir():
        for chave in chaves_selecao_pagina:
            st.session_state[chave] = False

    col_marcar, col_limpar = st.columns(2)

    with col_marcar:
        st.button(
            "Selecionar todos desta p?gina",
            key=f"abir_marcar_pagina_{pagina}",
            on_click=_marcar_pagina_abir,
            use_container_width=True
        )

    with col_limpar:
        st.button(
            "Limpar sele??o desta p?gina",
            key=f"abir_limpar_pagina_{pagina}",
            on_click=_limpar_pagina_abir,
            use_container_width=True
        )

    for indice_resultado, registro in resultados_pagina.iterrows():

        chave_selecao = _chave_selecao_abir(registro, indice_resultado)

        with st.container(border=True):

            col_esquerda, col_direita = st.columns([3, 1])

            with col_esquerda:

                st.checkbox(
                    "Selecionar este im?vel para o relat?rio",
                    key=chave_selecao
                )


            col_esquerda, col_direita = st.columns([3, 1])

            with col_esquerda:

                st.markdown(
                    f"**{mostrar_valor(registro['Tipo_Imovel'])}**"
                    f" â€” {mostrar_valor(registro['Municipio'])}/"
                    f"{mostrar_valor(registro['Estado'])}"
                )

                st.caption(
                    f"{mostrar_valor(registro['Site_Origem'])} "
                    f" | {mostrar_valor(registro['Modalidade'])}"
                )

                st.write(
                    f"**Bairro:** {mostrar_valor(registro['Bairro'])}"
                )

                st.write(
                    f"**EndereÃ§o:** {mostrar_valor(registro['Endereco'])}"
                )

                st.write(
                    f"**CÃ³digo:** {mostrar_valor(registro['Codigo_Imovel'])}"
                )

            with col_direita:

                classificacao = mostrar_valor(
                    registro["Classificacao_Exibicao"]
                )

                st.write("**Cadastro**")

                st.write(classificacao)

                st.write("**AvaliaÃ§Ã£o**")

                st.write(
                    mostrar_valor(registro["Valor_Avaliacao"])
                )

                link = str(registro["Link"]).strip()

                if link.startswith(("http://", "https://")):

                    st.link_button(
                        "Abrir anÃºncio",
                        link,
                        use_container_width=True
                    )


    # ------------------------------------------------------
    # RELATORIOS INTELIGENTES ABIR TI
    # ------------------------------------------------------

    indices_selecionados = [
        indice
        for indice, linha in resultado.iterrows()
        if st.session_state.get(
            _chave_selecao_abir(linha, indice), False
        )
    ]

    dados_selecionados = resultado.loc[indices_selecionados].copy()
    quantidade_selecionada = len(dados_selecionados)

    st.divider()

    with st.expander(
        "\U0001F4CA Relat\u00f3rios Inteligentes ? financeiro e geogr\u00e1fico",
        expanded=False
    ):

        st.write(
            f"Im\u00f3veis selecionados: **{quantidade_selecionada}**"
        )

        if quantidade_selecionada == 0:
            st.info(
                "Selecione os im\u00f3veis desejados nos cart\u00f5es acima."
            )

        elif quantidade_selecionada > 100:
            st.warning(
                "O limite \u00e9 de 100 im\u00f3veis por relat\u00f3rio. "
                "Reduza a sele\u00e7\u00e3o para continuar."
            )

        incluir_geografia = st.checkbox(
            "Incluir pesquisa geogr\u00e1fica no OpenStreetMap",
            value=False,
            key="geografia_relatorio_abir"
        )

        if incluir_geografia:
            st.info(
                "A pesquisa geogr\u00e1fica ser\u00e1 limitada aos primeiros "
                "20 im\u00f3veis selecionados. Os dados cartogr\u00e1ficos "
                "n\u00e3o comprovam criminalidade, enchentes ou riscos geol\u00f3gicos."
            )

        if st.button(
            "Gerar relat\u00f3rio Word",
            key="gerar_relatorio_abir",
            disabled=quantidade_selecionada == 0 or quantidade_selecionada > 100
        ):

            try:
                from relatorios.gerador_relatorio_abir import gerar_relatorio

                with st.spinner("Gerando relat\u00f3rio inteligente..."):
                    arquivo_docx = gerar_relatorio(
                        dados_selecionados,
                        consultar_geografia=incluir_geografia,
                        limite_geografia=20 if incluir_geografia else None
                    )

                st.success("Relat\u00f3rio gerado com sucesso!")

                st.download_button(
                    "\U0001F4E5 Baixar relat\u00f3rio Word",
                    data=arquivo_docx,
                    file_name="relatorio_inteligencia_abir.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_relatorio_abir"
                )

            except Exception as exc:
                st.error(
                    f"N\u00e3o foi poss\u00edvel gerar o relat\u00f3rio: {exc}"
                )

    # ------------------------------------------------------
    # FICHA COMPLETA
    # ------------------------------------------------------

    st.divider()

    st.markdown(
        '<h3 class="section-title">Ficha completa do imÃ³vel</h3>',
        unsafe_allow_html=True
    )

    opcoes_imoveis = []

    for indice, linha in resultado.iterrows():

        codigo = mostrar_valor(
            linha["Codigo_Imovel"]
        )

        municipio_item = mostrar_valor(
            linha["Municipio"]
        )

        estado_item = mostrar_valor(
            linha["Estado"]
        )

        tipo_item = mostrar_valor(
            linha["Tipo_Imovel"]
        )

        opcoes_imoveis.append(
            f"{indice + 1} - {codigo} | "
            f"{tipo_item} | {municipio_item}/{estado_item}"
        )

    selecionado = st.selectbox(
        "Selecione um imÃ³vel para visualizar todos os detalhes",
        opcoes_imoveis
    )

    posicao = opcoes_imoveis.index(selecionado)

    registro = resultado.iloc[posicao]

    with st.container(border=True):

        st.subheader(
            mostrar_valor(registro["Tipo_Imovel"])
        )

        c1, c2 = st.columns(2)

        with c1:

            st.write(
                f"**Portal:** {mostrar_valor(registro['Site_Origem'])}"
            )

            st.write(
                f"**Modalidade:** {mostrar_valor(registro['Modalidade'])}"
            )

            st.write(
                f"**CÃ³digo do imÃ³vel:** {mostrar_valor(registro['Codigo_Imovel'])}"
            )

            st.write(
                f"**CÃ³digo do leilÃ£o:** {mostrar_valor(registro['Codigo_Leilao'])}"
            )

            st.write(
                f"**NÃºmero do lote:** {mostrar_valor(registro['Numero_Lote'])}"
            )

            st.write(
                f"**Estado:** {mostrar_valor(registro['Estado'])}"
            )

            st.write(
                f"**MunicÃ­pio:** {mostrar_valor(registro['Municipio'])}"
            )

            st.write(
                f"**Bairro:** {mostrar_valor(registro['Bairro'])}"
            )

            st.write(
                f"**EndereÃ§o:** {mostrar_valor(registro['Endereco'])}"
            )

        with c2:

            st.write(
                f"**AvaliaÃ§Ã£o:** {mostrar_valor(registro['Valor_Avaliacao'])}"
            )

            st.write(
                f"**Primeira praÃ§a:** {mostrar_valor(registro['Valor_Primeira_Praca'])}"
            )

            st.write(
                f"**Data da primeira praÃ§a:** {mostrar_valor(registro['Data_Primeira_Praca'])}"
            )

            st.write(
                f"**Segunda praÃ§a:** {mostrar_valor(registro['Valor_Segunda_Praca'])}"
            )

            st.write(
                f"**Data da segunda praÃ§a:** {mostrar_valor(registro['Data_Segunda_Praca'])}"
            )

            st.write(
                f"**Lance inicial:** {mostrar_valor(registro['Lance_Inicial'])}"
            )

            st.write(
                f"**Incremento:** {mostrar_valor(registro['Incremento'])}"
            )

            st.write(
                f"**Ãrea do terreno:** {mostrar_valor(registro['Area_Terreno'])}"
            )

            st.write(
                f"**Ãrea construÃ­da:** {mostrar_valor(registro['Area_Construida'])}"
            )

        with st.expander("InformaÃ§Ãµes adicionais"):

            st.write(
                f"**MatrÃ­cula:** {mostrar_valor(registro['Matricula'])}"
            )

            st.write(
                f"**Processo:** {mostrar_valor(registro['Processo'])}"
            )

            st.write(
                f"**OcupaÃ§Ã£o:** {mostrar_valor(registro['Ocupacao'])}"
            )

            st.write(
                f"**SituaÃ§Ã£o da extraÃ§Ã£o:** {mostrar_valor(registro['Situacao_Extracao'])}"
            )

            st.write(
                f"**ClassificaÃ§Ã£o:** {mostrar_valor(registro['Classificacao'])}"
            )

            st.write(
                f"**Link da relaÃ§Ã£o do leilÃ£o:** "
                f"{mostrar_valor(registro['Link_Relacao_Leilao'])}"
            )

        link = str(registro["Link"]).strip()

        if link.startswith(("http://", "https://")):

            st.link_button(
                "ðŸ”— Abrir anÃºncio original do imÃ³vel",
                link,
                use_container_width=True
            )


# ==========================================================
# RODAPE
# ==========================================================

st.divider()

st.markdown("""
<div style="
    text-align:center;
    color:#718096;
    padding:25px;
    font-size:13px;
">
    <strong>ABIR TI</strong><br>
    InteligÃªncia em LeilÃµes ImobiliÃ¡rios<br><br>
    PÃ¡gina desenvolvida por Petercley
</div>
""", unsafe_allow_html=True)

