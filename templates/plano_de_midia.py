"""
Template: Plano de Mídia Estratégico
"""

from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.units import mm
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brand.design_system import (
    W, H, CW, CW_MM, MARGIN,
    NAVY, ORANGE, BLUE, GREEN, RED, GRAY_BG, GRAY_LINE, WHITE,
    S, PageHeader, SectionHeader, MetricCard, InsightBox, TagBadge,
    make_cards_row, table_style_default, table_total_row,
    chart_barras_horizontais, chart_donut,
    draw_footer, draw_cover
)


def gerar(dados: dict, output_path: str):
    """
    dados = {
        "cliente":       str,
        "periodo":       str,    # ex: "90 dias Mai → Jul 2026"
        "agencia":       str,
        "responsavel":   str,
        "investimento":  float,

        # Funil (lista de dicts)
        "canais": [
            {"etapa": "Google|Meta|Reserva", "canal": str, "funcao": str,
             "verba": float, "percentual": float}
        ],

        # Métricas previstas
        "cpl_estimado_min": float,
        "cpl_estimado_max": float,
        "leads_estimados":  str,   # ex: "400–650"

        # Cronograma (lista de dicts)
        "cronograma": [
            {"semana": str, "itens": [str, ...]}
        ],

        # Infraestrutura (lista de strings)
        "infraestrutura":   [str, ...],

        # O que precisa do cliente (lista de strings)
        "precisa_cliente":  [str, ...],

        # Estratégia por produto (lista de dicts)
        "produtos": [
            {"nome": str, "tipo": str, "prioridade": str,
             "descricao": str}
        ],

        # Palavras-chave principais
        "palavras_chave": [str, ...],

        "frase_resumo":    str,
        "frase_destaque":  str,
        "info_capa":       str,
    }
    """
    d = dados
    cliente    = d.get("cliente", "Cliente")
    periodo    = d.get("periodo", "")
    agencia    = d.get("agencia", "MarkSeg Trafego")
    total_pags = 2
    invest     = d.get("investimento", 0)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=(W, H),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )

    story = [PageBreak()]

    story.append(PageHeader(cliente, f"Plano de Midia · {periodo}", "02 / 02"))
    story.append(Spacer(1, 4 * mm))

    # seção 1 – funil
    story.append(SectionHeader(1, "FUNIL DE MIDIA"))
    story.append(Spacer(1, 4 * mm))

    etapa_cores = {"GOOGLE": GREEN, "META": BLUE, "RESERVA": NAVY}
    canal_rows = [[
        Paragraph("ETAPA", S["th"]),     Paragraph("CANAL", S["th"]),
        Paragraph("FUNCAO", S["th"]),    Paragraph("VERBA", S["th"]),
        Paragraph("PART.", S["th"]),
    ]]
    for c in d.get("canais", []):
        cor = etapa_cores.get(c.get("etapa","").upper(), NAVY)
        canal_rows.append([
            TagBadge(c.get("etapa", ""), cor),
            Paragraph(c.get("canal", ""), S["td_bold"]),
            Paragraph(c.get("funcao", ""), S["td"]),
            Paragraph(f"R$ {c.get('verba',0):,.0f}".replace(",","."), S["td_r"]),
            Paragraph(f"{c.get('percentual',0):.0f}%", S["td_r"]),
        ])

    total_canais = sum(c.get("verba", 0) for c in d.get("canais", []))
    canal_rows.append([
        Paragraph("TOTAL", S["th"]), Paragraph("", S["th"]),
        Paragraph(f"Investimento total", S["th"]),
        Paragraph(f"R$ {total_canais:,.0f}".replace(",","."), S["th"]),
        Paragraph("100%", S["th"]),
    ])

    ct = Table(canal_rows, colWidths=[20*mm, 50*mm, 80*mm, 20*mm, 13*mm], repeatRows=1)
    ct.setStyle(table_style_default())
    ct.setStyle(table_total_row(len(canal_rows) - 1))
    story.append(ct)
    story.append(Spacer(1, 4 * mm))

    # gráfico donut
    graf_dados = [(c.get("etapa","") + " · " + c.get("canal",""),
                   c.get("verba", 0),
                   etapa_cores.get(c.get("etapa","").upper(), NAVY))
                  for c in d.get("canais", []) if c.get("verba", 0) > 0]
    story.append(chart_donut(graf_dados, CW_MM, 50,
                              titulo="Distribuicao do investimento"))
    story.append(Spacer(1, 5 * mm))

    # seção 2 – produtos
    if d.get("produtos"):
        story.append(SectionHeader(2, "PRODUTOS E PRIORIDADE DE CAMPANHA"))
        story.append(Spacer(1, 4 * mm))
        prod_rows = [[
            Paragraph("PRODUTO", S["th"]),   Paragraph("TIPO", S["th"]),
            Paragraph("PRIORIDADE", S["th"]), Paragraph("DESCRICAO", S["th"]),
        ]]
        for p in d["produtos"]:
            prod_rows.append([
                Paragraph(p.get("nome", ""), S["td_bold"]),
                Paragraph(p.get("tipo", ""), S["td"]),
                Paragraph(p.get("prioridade", ""), S["td_orange"]),
                Paragraph(p.get("descricao", ""), S["td"]),
            ])
        prt = Table(prod_rows, colWidths=[40*mm, 25*mm, 25*mm, 88*mm], repeatRows=1)
        prt.setStyle(table_style_default())
        story.append(prt)
        story.append(Spacer(1, 5 * mm))

    # seção 3 – métricas estimadas
    story.append(SectionHeader(3, "METRICAS ESTIMADAS · MES 1"))
    story.append(Spacer(1, 4 * mm))
    story.append(make_cards_row([
        {"label": "INVESTIMENTO/MES", "value": f"R$ {invest:,.0f}".replace(",","."),
         "sub": "verba de midia",      "cor": ORANGE},
        {"label": "LEADS ESTIMADOS",  "value": d.get("leads_estimados", "—"),
         "sub": "hipotese mes 1",      "cor": ORANGE},
        {"label": "CPL ESTIMADO MIN", "value": f"R$ {d.get('cpl_estimado_min',0):,.0f}".replace(",","."),
         "sub": "custo por lead",      "cor": GREEN},
        {"label": "CPL ESTIMADO MAX", "value": f"R$ {d.get('cpl_estimado_max',0):,.0f}".replace(",","."),
         "sub": "custo por lead",      "cor": ORANGE},
    ]))
    story.append(Spacer(1, 5 * mm))

    # seção 4 – cronograma
    if d.get("cronograma"):
        story.append(SectionHeader(4, "CRONOGRAMA · PRIMEIRAS 4 SEMANAS"))
        story.append(Spacer(1, 4 * mm))

        # grid 2x2
        sem = d["cronograma"]
        while len(sem) < 4:
            sem.append({"semana": "", "itens": []})

        def sem_cell(s):
            items = "\n".join(f"- {i}" for i in s.get("itens", []))
            return Paragraph(
                f"<b>{s.get('semana','')}</b><br/>{items.replace(chr(10),'<br/>')}",
                S["body"]
            )

        half = len(sem) // 2
        rows = []
        for i in range(0, len(sem), 2):
            rows.append([sem_cell(sem[i]),
                         sem_cell(sem[i+1]) if i+1 < len(sem) else Paragraph("", S["body"])])

        cron_t = Table(rows, colWidths=[CW/2 - 2*mm, CW/2 - 2*mm])
        cron_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), GRAY_BG),
            ("GRID",          (0,0), (-1,-1), 0.3, GRAY_LINE),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",   (0,0), (-1,-1), 4*mm),
            ("TOPPADDING",    (0,0), (-1,-1), 3*mm),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3*mm),
        ]))
        story.append(cron_t)
        story.append(Spacer(1, 5 * mm))

    # seção 5 – infraestrutura
    half_cw = CW / 2 - 2 * mm

    if d.get("infraestrutura") or d.get("precisa_cliente"):
        story.append(SectionHeader(5, "INFRAESTRUTURA E O QUE PRECISAMOS"))
        story.append(Spacer(1, 4 * mm))
        infra = "\n".join(f"- {i}" for i in d.get("infraestrutura", []))
        precisa = "\n".join(f"- {i}" for i in d.get("precisa_cliente", []))
        grid = Table(
            [[Paragraph(f"<b>PRONTO ANTES DE SUBIR</b><br/>{infra.replace(chr(10),'<br/>')}",
                        S["body"]),
              Paragraph(f"<b>O QUE PRECISAMOS DO CLIENTE</b><br/>{precisa.replace(chr(10),'<br/>')}",
                        S["body"])]],
            colWidths=[half_cw, half_cw],
        )
        grid.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), GRAY_BG),
            ("GRID",          (0,0), (-1,-1), 0.3, GRAY_LINE),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",   (0,0), (-1,-1), 4*mm),
            ("TOPPADDING",    (0,0), (-1,-1), 3*mm),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4*mm),
        ]))
        story.append(grid)
        story.append(Spacer(1, 3 * mm))

    # palavras-chave
    if d.get("palavras_chave"):
        kws = "  ·  ".join(d["palavras_chave"])
        ret = Table([[Paragraph(
            f"<b>PALAVRAS-CHAVE PRIORITARIAS:</b>  {kws}", S["insight"]
        )]], colWidths=[CW])
        ret.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), NAVY),
            ("LEFTPADDING",   (0,0), (-1,-1), 4*mm),
            ("TOPPADDING",    (0,0), (-1,-1), 3*mm),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3*mm),
        ]))
        story.append(ret)

    def on_first(canvas, doc):
        draw_cover(canvas, doc,
                   titulo_doc="Plano de", subtitulo_doc="Midia",
                   cliente=cliente, agencia=agencia, periodo=periodo,
                   info_extra=d.get("info_capa", ""),
                   frase_resumo=d.get("frase_resumo", ""),
                   frase_destaque=d.get("frase_destaque", ""))

    def on_later(canvas, doc):
        draw_footer(canvas, doc, cliente, total_pags)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return output_path
