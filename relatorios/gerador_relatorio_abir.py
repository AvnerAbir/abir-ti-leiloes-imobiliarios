"""Geração de relatórios financeiros e geográficos do ABIR TI.

A pesquisa geográfica usa Nominatim/OSM e Overpass. Os resultados são
proximidades cartográficas, não substituem vistorias nem bases oficiais de
criminalidade, risco hidrológico ou situação urbanística.
"""
from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from datetime import datetime

import requests
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_CACHE = PASTA_PROJETO / "relatorios" / "cache_geografico"
PASTA_CACHE.mkdir(parents=True, exist_ok=True)
CACHE = PASTA_CACHE / "osm_cache.json"
USER_AGENT = "ABIR-TI-Relatorios/1.0 (relatorios imobiliarios)"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"


def _texto(v):
    if v is None:
        return "Não informado"
    s = str(v).strip()
    return s if s and s.lower() not in {"nan", "none", "null"} else "Não informado"


def _numero(v):
    if v is None:
        return None
    s = re.sub(r"[^0-9,.-]", "", str(v)).strip()
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _moeda(v):
    n = _numero(v)
    return "Não informado" if n is None else ("R$ {:,.2f}".format(n).replace(",", "X").replace(".", ",").replace("X", "."))


def _cache_ler():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _cache_salvar(dados):
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CACHE)


def _chave(endereco):
    return re.sub(r"\s+", " ", endereco.casefold()).strip()


def geocodificar(endereco_completo: str, cache: dict):
    chave = "geo:" + _chave(endereco_completo)
    if chave in cache:
        return cache[chave]
    try:
        r = requests.get(NOMINATIM, params={"q": endereco_completo, "format": "jsonv2", "limit": 1, "addressdetails": 1}, headers={"User-Agent": USER_AGENT}, timeout=25)
        r.raise_for_status()
        itens = r.json()
        resultado = None
        if itens:
            item = itens[0]
            resultado = {"lat": float(item["lat"]), "lon": float(item["lon"]), "display_name": item.get("display_name", ""), "importance": item.get("importance")}
        cache[chave] = resultado
        _cache_salvar(cache)
        time.sleep(1.1)  # política de uso do Nominatim: no máximo 1 req/s
        return resultado
    except Exception as exc:
        return {"erro": f"Geocodificação indisponível: {exc.__class__.__name__}"}


def _distancia_m(lat1, lon1, lat2, lon2):
    raio = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*raio*math.atan2(math.sqrt(a), math.sqrt(1-a))


def pesquisar_entorno(lat: float, lon: float, cache: dict, raio_m: int = 1500):
    chave = f"osm:{lat:.5f}:{lon:.5f}:{raio_m}"
    if chave in cache:
        return cache[chave]
    query = f'''[out:json][timeout:35];
    (node(around:{raio_m},{lat},{lon})[amenity~"^(school|college|university|hospital|clinic|doctors|pharmacy)$"];
     way(around:{raio_m},{lat},{lon})[amenity~"^(school|college|university|hospital|clinic|doctors|pharmacy)$"];
     relation(around:{raio_m},{lat},{lon})[amenity~"^(school|college|university|hospital|clinic|doctors|pharmacy)$"];
     node(around:{raio_m},{lat},{lon})[shop~"^(supermarket|convenience|mall)$"];
     way(around:{raio_m},{lat},{lon})[shop~"^(supermarket|convenience|mall)$"];
     node(around:{raio_m},{lat},{lon})[highway=bus_stop];
     node(around:{raio_m},{lat},{lon})[public_transport=platform];);
    out center tags;'''
    try:
        r = requests.post(OVERPASS, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=50)
        r.raise_for_status()
        elementos = r.json().get("elements", [])
        achados = []
        for el in elementos:
            tags = el.get("tags", {})
            centro = el.get("center", {})
            elat = el.get("lat", centro.get("lat"))
            elon = el.get("lon", centro.get("lon"))
            if elat is None or elon is None:
                continue
            tipo = tags.get("amenity") or tags.get("shop") or ("ponto de ônibus" if tags.get("highway") == "bus_stop" else "transporte público")
            nome = tags.get("name") or tags.get("brand") or tags.get("operator") or tipo
            achados.append({"nome": nome, "tipo": tipo, "distancia_m": round(_distancia_m(lat, lon, float(elat), float(elon))), "endereco": " ".join(filter(None, [tags.get("addr:street"), tags.get("addr:housenumber"), tags.get("addr:suburb")]))})
        achados.sort(key=lambda x: x["distancia_m"])
        cache[chave] = {"itens": achados, "raio_m": raio_m, "fonte": "OpenStreetMap/Overpass", "data_consulta": datetime.now().isoformat(timespec="seconds")}
        _cache_salvar(cache)
        time.sleep(1.1)  # reduz carga sobre a instância pública do Overpass
        return cache[chave]
    except Exception as exc:
        return {"erro": f"Consulta de entorno indisponível: {exc.__class__.__name__}", "itens": []}


def enriquecer_geografia(imovel: dict, cache: dict, consultar: bool = True):
    endereco = ", ".join(x for x in [
        _texto(imovel.get("Endereco")) if _texto(imovel.get("Endereco")) != "Não informado" else "",
        _texto(imovel.get("Bairro")) if _texto(imovel.get("Bairro")) != "Não informado" else "",
        _texto(imovel.get("Municipio")) if _texto(imovel.get("Municipio")) != "Não informado" else "",
        _texto(imovel.get("Estado")) if _texto(imovel.get("Estado")) != "Não informado" else "",
        "Brasil"
    ] if x)
    if not consultar:
        return {"endereco_consultado": endereco, "status": "Pesquisa geográfica não solicitada", "itens": []}
    geo = geocodificar(endereco, cache)
    if not geo:
        return {"endereco_consultado": endereco, "status": "Endereço não localizado com precisão suficiente", "itens": []}
    if geo.get("erro"):
        return {"endereco_consultado": endereco, "status": geo["erro"], "itens": []}
    entorno = pesquisar_entorno(geo["lat"], geo["lon"], cache)
    return {"endereco_consultado": endereco, "status": "Localização aproximada encontrada", "mapa": geo.get("display_name", ""), **entorno}


def _add_bullet(doc, texto):
    doc.add_paragraph(texto, style="List Bullet")


def gerar_relatorio(df, consultar_geografia: bool = True, limite_geografia: int | None = None) -> bytes:
    """Gera relatório DOCX a partir das linhas filtradas no painel."""
    registros = df.fillna("").to_dict(orient="records")
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.8)
    sec.left_margin, sec.right_margin = Cm(2), Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(9)

    titulo = doc.add_heading("RELATÓRIO DE INTELIGÊNCIA IMOBILIÁRIA — ABIR TI", 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Imóveis incluídos: {len(registros)}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("1. Análise financeira consolidada", level=1)
    avaliacoes, ofertas, descontos = [], [], []
    for row in registros:
        av = _numero(row.get("Valor_Avaliacao"))
        lance = _numero(row.get("Lance_Inicial"))
        p1 = _numero(row.get("Valor_Primeira_Praca"))
        p2 = _numero(row.get("Valor_Segunda_Praca"))
        referencia = lance if lance is not None else (p1 if p1 is not None else p2)
        if av and av > 0:
            avaliacoes.append(av)
            if referencia is not None:
                ofertas.append(referencia)
                descontos.append((av-referencia)/av*100)
    doc.add_paragraph(f"Imóveis analisados: {len(registros)}")
    doc.add_paragraph(f"Imóveis com avaliação numérica: {len(avaliacoes)}")
    doc.add_paragraph(f"Imóveis com preço de referência comparável: {len(descontos)}")
    if descontos:
        doc.add_paragraph(f"Deságio médio indicativo: {sum(descontos)/len(descontos):.2f}%")
        doc.add_paragraph(f"Deságio mediano indicativo: {sorted(descontos)[len(descontos)//2]:.2f}%")
    else:
        doc.add_paragraph("Não há dados numéricos suficientes para calcular deságio.")
    doc.add_paragraph("Critério: (avaliação − preço de referência) ÷ avaliação. O preço de referência prioriza lance inicial; na ausência, usa 1ª praça e depois 2ª praça. Conferir as condições do edital e custos adicionais antes de decisão de investimento.")

    doc.add_heading("2. Fichas individualizadas", level=1)
    # INTEGRACAO GEOGRAFICA ABIR TI
    correspondencias = {}
    import sqlite3
    banco_geo = Path('relatorios/base_geografica.db')
    if banco_geo.exists():
        try:
            with sqlite3.connect(banco_geo) as con:
                dados_geo = con.execute('SELECT codigo_imovel, municipio, logradouro, nome_via_osm, classificacao FROM correspondencias_vias').fetchall()
            correspondencias = {str(x[0]): x[1:] for x in dados_geo}
        except sqlite3.Error as erro:
            print(f'AVISO: base geografica: {erro}')
    cache = _cache_ler()
    # INTEGRACAO POIS GO ABIR TI
    pontos_por_imovel = {}
    try:
        import sqlite3
        with sqlite3.connect('relatorios/base_geografica.db') as con:
            dados_poi = con.execute("SELECT codigo_imovel, categoria, nome, distancia_m FROM pontos_interesse_proximidade_go WHERE nome IS NOT NULL AND TRIM(nome) <> '' AND LOWER(TRIM(nome)) NOT IN ('nan','none','null') ORDER BY codigo_imovel, categoria, distancia_m").fetchall()
        for cod, categoria, nome, distancia in dados_poi:
            pontos_por_imovel.setdefault(str(cod), []).append((categoria, nome, distancia))
    except Exception as erro:
        print(f'AVISO: pontos de interesse n?o carregados: {erro}')
    for i, row in enumerate(registros, 1):
        doc.add_heading(f"Imóvel {i:03d} — código {_texto(row.get('Codigo_Imovel'))}", level=2)
        doc.add_paragraph(f"{_texto(row.get('Tipo_Imovel'))} | {_texto(row.get('Bairro'))} | {_texto(row.get('Municipio'))}/{_texto(row.get('Estado'))}")
        doc.add_paragraph(f"Endereço: {_texto(row.get('Endereco'))}")
        codigo_poi = _texto(row.get('Codigo_Imovel'))
        pontos_proximos = pontos_por_imovel.get(codigo_poi, [])
        if pontos_proximos:
            doc.add_paragraph('Pontos de interesse pr?ximos ? refer?ncia aproximada da via')
            for categoria_poi, nome_poi, distancia_poi in pontos_proximos:
                doc.add_paragraph(f'{categoria_poi}: {nome_poi} ? aproximadamente {distancia_poi} m')
        else:
            doc.add_paragraph('Pontos de interesse pr?ximos: sem correspond?ncia calculada para este im?vel.')
        codigo_geo = _texto(row.get('Codigo_Imovel'))
        referencia_geo = correspondencias.get(codigo_geo)
        estado_geo = _texto(row.get('Estado')).strip().upper()
        if referencia_geo:
            municipio_geo, logradouro_geo, via_osm, classificacao_geo = referencia_geo
            doc.add_paragraph('Refer?ncia geogr?fica: IBGE + OpenStreetMap')
            doc.add_paragraph(f'Logradouro no cadastro: {logradouro_geo}')
            doc.add_paragraph(f'Via correspondente no OpenStreetMap: {via_osm}')
            doc.add_paragraph('Precis?o: logradouro identificado; coordenada exata do im?vel n?o confirmada.')
        elif estado_geo in ('GO', 'GOIAS', 'GOI?S'):
            doc.add_paragraph('Refer?ncia geogr?fica: logradouro n?o identificado na base consultada.')
        else:
            doc.add_paragraph('Refer?ncia geogr?fica deste estado ainda n?o processada.')
        doc.add_paragraph(f"Origem/modalidade: {_texto(row.get('Site_Origem'))} / {_texto(row.get('Modalidade'))}")
        doc.add_paragraph(f"Avaliação: {_moeda(row.get('Valor_Avaliacao'))} | 1ª praça: {_moeda(row.get('Valor_Primeira_Praca'))} | 2ª praça: {_moeda(row.get('Valor_Segunda_Praca'))} | Lance inicial: {_moeda(row.get('Lance_Inicial'))}")
        av = _numero(row.get("Valor_Avaliacao"))
        ref = _numero(row.get("Lance_Inicial")) or _numero(row.get("Valor_Primeira_Praca")) or _numero(row.get("Valor_Segunda_Praca"))
        if av and av > 0 and ref is not None:
            doc.add_paragraph(f"Deságio indicativo sobre a avaliação: {(av-ref)/av*100:.2f}%")
        doc.add_paragraph(f"Ocupação informada na fonte: {_texto(row.get('Ocupacao'))} | Matrícula: {_texto(row.get('Matricula'))}")
        link = _texto(row.get("Link"))
        if link.startswith("http"):
            doc.add_paragraph(f"Anúncio: {link}")

        doc.add_heading("Realidade geográfica do entorno", level=3)
        geo = enriquecer_geografia(row, cache, consultar_geografia and (limite_geografia is None or i <= limite_geografia))
        doc.add_paragraph(f"Endereço pesquisado: {geo.get('endereco_consultado', '')}")
        doc.add_paragraph(f"Resultado da localização: {geo.get('status', 'Não consultado')}")
        if geo.get("mapa"):
            doc.add_paragraph(f"Referência cartográfica: {geo['mapa']}")
        itens = geo.get("itens", [])
        if itens:
            grupos = {
                "Educação": {"school", "college", "university"},
                "Saúde": {"hospital", "clinic", "doctors", "pharmacy"},
                "Comércio": {"supermarket", "convenience", "mall"},
                "Transporte": {"ponto de ônibus", "transporte público"},
            }
            for rotulo, tipos in grupos.items():
                grupo = [x for x in itens if x["tipo"] in tipos]
                if grupo:
                    nomes = "; ".join(f"{x['nome']} ({x['distancia_m']} m)" for x in grupo[:5])
                    _add_bullet(doc, f"{rotulo}: {nomes}.")
                else:
                    _add_bullet(doc, f"{rotulo}: nenhum equipamento identificado no OpenStreetMap no raio pesquisado; isso não prova inexistência.")
        else:
            doc.add_paragraph("Não foi possível identificar equipamentos próximos com os dados cartográficos consultados. Não inferir ausência de serviços.")
        doc.add_paragraph("Limites: OpenStreetMap é uma base colaborativa e pode estar incompleta. Esta consulta não confirma criminalidade, presença de comunidades, histórico de enchentes, risco geológico, qualidade de serviços, distância por rota ou condição específica do imóvel. Esses temas exigem bases oficiais complementares.")
        if i < len(registros):
            doc.add_page_break()

    doc.add_heading("3. Conclusão e limitações", level=1)
    doc.add_paragraph("Este relatório organiza os dados existentes na base do ABIR TI e apresenta indicadores financeiros indicativos e proximidades cartográficas. Não constitui laudo de avaliação, parecer jurídico, vistoria ou recomendação de investimento. Validar edital, matrícula, débitos, ocupação e condições locais antes de qualquer lance.")
    doc.add_paragraph("Fonte geográfica: OpenStreetMap (Nominatim e Overpass API), quando disponível. Os dados são consultados sob demanda e armazenados em cache local para reduzir chamadas repetidas.")
    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.add_run("ABIR TI | Relatório gerado automaticamente")
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
