 
import csv
import os
from datetime import datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION

ARQUIVO_ENTRADA = "todos_imoveis_detalhados.csv"
ARQUIVO_SAIDA = "relatorio_leiloes_judiciais.docx"


def valor_ou_ausente(valor):
    return valor.strip() if valor and valor.strip() else "Não informado"


def executar():

    if not os.path.exists(ARQUIVO_ENTRADA):
        print("ERRO: arquivo CSV não encontrado.")
        return

    with open(
        ARQUIVO_ENTRADA,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        imoveis = list(leitor)

    documento = Document()

    secao = documento.sections[0]
    secao.top_margin = Cm(2)
    secao.bottom_margin = Cm(2)
    secao.left_margin = Cm(2.5)
    secao.right_margin = Cm(2.5)

    estilos = documento.styles
    estilos["Normal"].font.name = "Arial"
    estilos["Normal"].font.size = Pt(10)

    # CAPA
    titulo = documento.add_heading(
        "RELATÓRIO DE IMÓVEIS EM LEILÕES JUDICIAIS",
        level=0
    )
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitulo = documento.add_paragraph(
        "Levantamento de oportunidades imobiliárias"
    )
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER

    documento.add_paragraph("")
    data = documento.add_paragraph(
        "Data de geração: " + datetime.now().strftime("%d/%m/%Y às %H:%M")
    )
    data.alignment = WD_ALIGN_PARAGRAPH.CENTER

    documento.add_paragraph("")
    resumo = documento.add_paragraph()
    resumo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    resumo.add_run(
        f"Total de imóveis analisados: {len(imoveis)}"
    ).bold = True

    documento.add_page_break()

    # RESUMO
    documento.add_heading("RESUMO GERAL", level=1)

    situacoes = {}

    for imovel in imoveis:
        situacao = valor_ou_ausente(
            imovel.get("Situacao_Leilao", "")
        )
        situacoes[situacao] = situacoes.get(situacao, 0) + 1

    for situacao, quantidade in sorted(situacoes.items()):
        documento.add_paragraph(
            f"{situacao}: {quantidade} imóvel(is)",
            style="List Bullet"
        )

    documento.add_page_break()

    # FICHAS DOS IMÓVEIS
    for numero, imovel in enumerate(imoveis, start=1):

        documento.add_heading(
            f"IMÓVEL {numero:02d} - "
            + valor_ou_ausente(imovel.get("Codigo_Lote", "")),
            level=1
        )

        documento.add_heading("Identificação", level=2)

        campos_identificacao = [
            ("Título", "Titulo"),
            ("Código do lote", "Codigo_Lote"),
            ("Código do leilão", "Codigo_Leilao"),
            ("Endereço", "Endereco"),
            ("Processo judicial", "Processo"),
        ]

        for rotulo, campo in campos_identificacao:
            documento.add_paragraph(
                f"{rotulo}: {valor_ou_ausente(imovel.get(campo, ''))}"
            )

        documento.add_heading("Informações financeiras", level=2)

        campos_financeiros = [
            ("Valor de avaliação", "Valor_Avaliacao"),
            ("Valor da primeira praça", "Valor_Primeira_Praca"),
            ("Valor da segunda praça", "Valor_Segunda_Praca"),
            ("Incremento", "Incremento"),
        ]

        for rotulo, campo in campos_financeiros:
            valor = valor_ou_ausente(imovel.get(campo, ""))
            if valor != "Não informado" and "Valor" in rotulo or rotulo == "Incremento":
                valor = "R$ " + valor
            documento.add_paragraph(f"{rotulo}: {valor}")

        documento.add_heading("Datas e situação", level=2)

        campos_datas = [
            ("Primeira praça", "Primeira_Praca"),
            ("Segunda praça", "Segunda_Praca"),
            ("Situação do leilão", "Situacao_Leilao"),
        ]

        for rotulo, campo in campos_datas:
            documento.add_paragraph(
                f"{rotulo}: {valor_ou_ausente(imovel.get(campo, ''))}"
            )

        documento.add_heading("Consulta do anúncio", level=2)

        link = valor_ou_ausente(imovel.get("Link", ""))
        documento.add_paragraph(link)

        if imovel.get("Erro", "").strip():
            observacao = documento.add_paragraph()
            observacao.add_run("Observação: ").bold = True
            observacao.add_run(imovel["Erro"])

        if numero < len(imoveis):
            documento.add_page_break()

    # RODAPÉ
    for secao in documento.sections:
        rodape = secao.footer.paragraphs[0]
        rodape.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rodape.add_run(
            "Relatório gerado automaticamente - Leilões Judiciais"
        )

    documento.save(ARQUIVO_SAIDA)

    print("\nRELATÓRIO GERADO COM SUCESSO!")
    print("Total de imóveis:", len(imoveis))
    print("Arquivo:", ARQUIVO_SAIDA)


if __name__ == "__main__":
    executar()
