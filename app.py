
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
ARQUIVO_BASE = PASTA / "coleta" / "base_consolidada_leiloes.csv"
ARQUIVO_USUARIOS = PASTA / "usuarios.json"

# Manter True durante o desenvolvimento.
# Antes da publicacao, a autenticacao sera obrigatoria.
MODO_TESTE_SEM_LOGIN = False

st.set_page_config(
    page_title="ABIR TI | Leilões Imobiliários",
    page_icon="🏠",
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

    # Primeiro, tenta carregar os usuários dos Secrets na nuvem.
    try:
        usuarios_json = st.secrets.get("usuarios_json")

        if usuarios_json:
            dados = json.loads(usuarios_json)
            return dados.get("usuarios", [])

    except Exception:
        pass

    # Se não houver Secrets, utiliza o arquivo local.
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
            "Acesso indisponível. A configuração dos usuários "
            "precisa ser realizada."
        )
        st.stop()

    if st.session_state.get("autenticado", False):
        return True

    st.markdown("""
    <div class="abir-header">
        <div class="abir-logo">ABIR TI</div>
        <div class="abir-subtitle">
            INTELIGÊNCIA EM LEILÕES IMOBILIÁRIOS
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Acesso à plataforma")
    st.caption("Área restrita para usuários autorizados.")

    with st.form("form_login"):

        usuario = st.text_input("Usuário")
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
            st.error("Usuário ou senha inválidos.")

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
        return "Não informado"

    valor = str(valor).strip()

    if not valor or valor.lower() == "nan":
        return "Não informado"

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

    if valor in ["valido", "valida"]:
        return "Válido"

    if valor == "parcial":
        return "Parcial"

    if valor == "erro":
        return "Erro"

    return valor.title() if valor else "Não informado"


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

    st.error("A base consolidada não foi encontrada ou está vazia.")

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


# ==========================================================
# CABECALHO
# ==========================================================


st.markdown(
    """
    <div class="abir-header">
        <div class="abir-logo">ABIR TI</div>
        <div class="abir-subtitle">
            INTELIGÊNCIA EM LEILÕES IMOBILIÁRIOS
        </div>
        <div class="abir-description">
            Encontre oportunidades imobiliárias.<br>
            Consulte imóveis de leilões judiciais e extrajudiciais
            em diferentes portais, em um só lugar.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


if st.session_state.get("perfil_atual"):

    st.caption(
        f"Usuário conectado: {st.session_state['perfil_atual']}"
    )


# ==========================================================
# MENU LATERAL
# ==========================================================

with st.sidebar:

    st.markdown("## ABIR TI")

    st.caption("Consulta de imóveis em leilão")

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
    df["Classificacao_Exibicao"] == "Válido"
).sum()

parciais = (
    df["Classificacao_Exibicao"] == "Parcial"
).sum()

erros = (
    df["Classificacao_Exibicao"] == "Erro"
).sum()


st.markdown(
    '<h3 class="section-title">Visão geral da base</h3>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

indicadores = [
    (col1, "Total de imóveis", total),
    (col2, "Cadastros válidos", validos),
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
    '<h3 class="section-title">Localize seu imóvel</h3>',
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
        "Município",
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
        "Tipo de imóvel",
        tipos
    )

    modalidades = ["Todas"] + opcoes_coluna(
        df,
        "Modalidade"
    )

    modalidade = st.selectbox(
        "Modalidade",
        modalidades
    )

    situacoes = [
        "Válidos e parciais",
        "Somente válidos",
        "Somente parciais",
        "Todos, incluindo erros"
    ]

    situacao = st.selectbox(
        "Classificação do cadastro",
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

if modalidade != "Todas":

    resultado = resultado[
        resultado["Modalidade"] == modalidade
    ]


if situacao == "Válidos e parciais":

    resultado = resultado[
        resultado["Classificacao_Exibicao"].isin(
            ["Válido", "Parcial"]
        )
    ]

elif situacao == "Somente válidos":

    resultado = resultado[
        resultado["Classificacao_Exibicao"] == "Válido"
    ]

elif situacao == "Somente parciais":

    resultado = resultado[
        resultado["Classificacao_Exibicao"] == "Parcial"
    ]


# ==========================================================
# PESQUISA LIVRE
# ==========================================================

pesquisa = st.text_input(
    "Pesquisar por endereço, código, processo ou palavra-chave",
    placeholder="Ex.: apartamento, Brasília, 235138..."
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
    '<h3 class="section-title">Imóveis encontrados</h3>',
    unsafe_allow_html=True
)

total_resultados = len(resultado)

st.write(
    f"**{numero_formatado(total_resultados)} imóveis encontrados**"
)


if resultado.empty:

    st.info("Nenhum imóvel corresponde aos filtros selecionados.")

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
        "📥 Baixar resultados da pesquisa",
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
            "Página de resultados",
            list(range(1, total_paginas + 1))
        )

    else:
        pagina = 1

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    resultados_pagina = resultado.iloc[inicio:fim]

    st.caption(
        f"Exibindo {inicio + 1} até "
        f"{min(fim, total_resultados)} "
        f"de {numero_formatado(total_resultados)} imóveis."
    )

    # ------------------------------------------------------
    # CARTOES DOS IMOVEIS
    # ------------------------------------------------------

    for _, registro in resultados_pagina.iterrows():

        with st.container(border=True):

            col_esquerda, col_direita = st.columns([3, 1])

            with col_esquerda:

                st.markdown(
                    f"**{mostrar_valor(registro['Tipo_Imovel'])}**"
                    f" — {mostrar_valor(registro['Municipio'])}/"
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
                    f"**Endereço:** {mostrar_valor(registro['Endereco'])}"
                )

                st.write(
                    f"**Código:** {mostrar_valor(registro['Codigo_Imovel'])}"
                )

            with col_direita:

                classificacao = mostrar_valor(
                    registro["Classificacao_Exibicao"]
                )

                st.write("**Cadastro**")

                st.write(classificacao)

                st.write("**Avaliação**")

                st.write(
                    mostrar_valor(registro["Valor_Avaliacao"])
                )

                link = str(registro["Link"]).strip()

                if link.startswith(("http://", "https://")):

                    st.link_button(
                        "Abrir anúncio",
                        link,
                        use_container_width=True
                    )


    # ------------------------------------------------------
    # FICHA COMPLETA
    # ------------------------------------------------------

    st.divider()

    st.markdown(
        '<h3 class="section-title">Ficha completa do imóvel</h3>',
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
        "Selecione um imóvel para visualizar todos os detalhes",
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
                f"**Código do imóvel:** {mostrar_valor(registro['Codigo_Imovel'])}"
            )

            st.write(
                f"**Código do leilão:** {mostrar_valor(registro['Codigo_Leilao'])}"
            )

            st.write(
                f"**Número do lote:** {mostrar_valor(registro['Numero_Lote'])}"
            )

            st.write(
                f"**Estado:** {mostrar_valor(registro['Estado'])}"
            )

            st.write(
                f"**Município:** {mostrar_valor(registro['Municipio'])}"
            )

            st.write(
                f"**Bairro:** {mostrar_valor(registro['Bairro'])}"
            )

            st.write(
                f"**Endereço:** {mostrar_valor(registro['Endereco'])}"
            )

        with c2:

            st.write(
                f"**Avaliação:** {mostrar_valor(registro['Valor_Avaliacao'])}"
            )

            st.write(
                f"**Primeira praça:** {mostrar_valor(registro['Valor_Primeira_Praca'])}"
            )

            st.write(
                f"**Data da primeira praça:** {mostrar_valor(registro['Data_Primeira_Praca'])}"
            )

            st.write(
                f"**Segunda praça:** {mostrar_valor(registro['Valor_Segunda_Praca'])}"
            )

            st.write(
                f"**Data da segunda praça:** {mostrar_valor(registro['Data_Segunda_Praca'])}"
            )

            st.write(
                f"**Lance inicial:** {mostrar_valor(registro['Lance_Inicial'])}"
            )

            st.write(
                f"**Incremento:** {mostrar_valor(registro['Incremento'])}"
            )

            st.write(
                f"**Área do terreno:** {mostrar_valor(registro['Area_Terreno'])}"
            )

            st.write(
                f"**Área construída:** {mostrar_valor(registro['Area_Construida'])}"
            )

        with st.expander("Informações adicionais"):

            st.write(
                f"**Matrícula:** {mostrar_valor(registro['Matricula'])}"
            )

            st.write(
                f"**Processo:** {mostrar_valor(registro['Processo'])}"
            )

            st.write(
                f"**Ocupação:** {mostrar_valor(registro['Ocupacao'])}"
            )

            st.write(
                f"**Situação da extração:** {mostrar_valor(registro['Situacao_Extracao'])}"
            )

            st.write(
                f"**Classificação:** {mostrar_valor(registro['Classificacao'])}"
            )

            st.write(
                f"**Link da relação do leilão:** "
                f"{mostrar_valor(registro['Link_Relacao_Leilao'])}"
            )

        link = str(registro["Link"]).strip()

        if link.startswith(("http://", "https://")):

            st.link_button(
                "🔗 Abrir anúncio original do imóvel",
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
    Inteligência em Leilões Imobiliários<br><br>
    Página desenvolvida por Petercley
</div>
""", unsafe_allow_html=True)
