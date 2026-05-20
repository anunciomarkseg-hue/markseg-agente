"""
Template: Apresentação de Resultado Mensal
"""

from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.units import mm
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brand.design_system import (
    W, H, CW, CW_MM, MARGIN,
    NAVY, ORANGE, BLUE, GREEN, RED, YELLOW, GRAY_BG, GRAY_LINE, WHITE,
    S, PageHeader, SectionHeader, MetricCard, InsightBox, TagBadge,
    make_cards_row, table_style_default, table_total_row,
    chart_barras_horizontais, chart_donut, chart_barras_verticais_duplas,
    draw_footer, draw_cover
)


def gerar(dados: dict, output_path: str):
    """
    dados = {
        "cliente":      str,
        "periodo":      str,   # ex: "Maio 2026"
        "agencia":      str,
        "responsavel":  str,

        # KPIs principais do mês
        "investimento_total": float,
        "leads_total":        int,
        "cpl_medio":          float,
        "taxa_qualificacao":  str,   # ex: "47%"
        "roas":               str,   # ex: "3,2x"
        "cac":                float,

        # Evolução semana a semana
        "evolucao": [
            {"semana": str, "leads": int, "gasto": float, "cpl": float}
        ],

        # Canal breakdown
        "canais": [
            {"canal": str, "gasto": float, "leads": int, "cpl": float,
             "taxa_qual": str, "avaliacao": str}
        ],

        # Top criativos do mês
        "top_criativos": [
            {"nome": str, "leads": int, "cpl": float, "hook": str}
        ],

        # Metas vs realizado
        "metas": [
            {"metrica": str, "meta": str, "realizado": str,
             "status": "OK|ALERTA|CRITICO"}
        ],

        # Insights e aprendizados
        "aprendizados": [str, ...],

        # Plano próximo mês
        "plano_proximo_mes": [
            {"acao": str, "canal": str, "impacto_esperado": str}
        ],

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

    doc = SimpleDocTemplate(
        output_path,
        pagesize=(W, H),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )

    story = [PageBreak()]

    story.append(PageHeader(cliente, f"Resultado Mensal · {periodo}", "02 / 02"))
    story.append(Spacer(1, 4 * mm))

    # seção 1 – KPIs
    story.append(SectionHeader(1, "RESULTADO DO MES · VISAO GERAL"))
    story.append(Spacer(1, 4 * mm))

    inv  = d.get("investimento_total", 0)
    leads = d.get("leads_total", 0)
    cpl   = d.get("cpl_medio", 0)

    story.append(make_cards_row([
        {"label": "INVESTIMENTO TOTAL", "value": f"R$ {inv:,.2f}".replace(",","."),
         "sub": "total do mes",          "cor": ORANGE},
        {"label": "LEADS TOTAIS",       "value": str(leads),
         "sub": "todos os canais",       "cor": ORANGE},
        {"label": "CPL MEDIO",          "value": f"R$ {cpl:,.2f}".replace(",","."),
         "sub": "custo por lead",        "cor": ORANGE},
        {"label": "TX. QUALIFICACAO",   "value": d.get("taxa_qualificacao", "—"),
         "sub": "meta: acima de 40%",    "cor": GREEN},
        {"label": "ROAS",               "value": d.get("roas", "—"),
         "sub": "retorno sobre investim","cor": GREEN},
        {"label": "CAC",                "value": f"R$ {d.get('cac',0):,.2f}".replace(",","."),
         "sub": "custo de aquisicao",    "cor": BLUE},
    ], n_cols=6))
    story.append(Spacer(1, 5 * mm))

    # metas vs realizado
    if d.get("metas"):
        story.append(SectionHeader(2, "METAS X REALIZADO"))
        story.append(Spacer(1, 4 * mm))
        m_rows = [[
            Paragraph("METRICA", S["th"]),
            Paragraph("META", S["th"]),
            Paragraph("REALIZADO", S["th"]),
            Paragraph("STATUS", S["th"]),
        ]]
        status_map = {"OK": GREEN, "ALERTA": YELLOW, "CRITICO": RED}
        for m in d["metas"]:
            sc = status_map.get(m.get("status","OK").upper(), GREEN)
            m_rows.append([
                Paragraph(m.get("metrica",""), S["td_bold"]),
                Paragraph(m.get("meta",""), S["td"]),
                Paragraph(m.get("realizado",""), S["td_bold"]),
                TagBadge(m.get("status","OK"), sc, largura=20*mm),
            ])
        mt = Table(m_rows, colWidths=[70*mm, 40*mm, 40*mm, 28*mm], repeatRows=1)
        mt.setStyle(table_style_default())
        story.append(mt)
        story.append(Spacer(1, 5 * mm))

    # canal breakdown
    if d.get("canais"):
        story.append(SectionHeader(3, "RESULTADO POR CANAL"))
        story.append(Spacer(1, 4 * mm))
        c_rows = [[
            Paragraph("CANAL", S["th"]),     Paragraph("GASTO", S["th"]),
            Paragraph("LEADS", S["th"]),     Paragraph("CPL", S["th"]),
            Paragraph("TX. QUAL.", S["th"]), Paragraph("AVALIACAO", S["th"]),
        ]]
        for c in d["canais"]:
            c_rows.append([
                Paragraph(c.get("canal",""), S["td_bold"]),
                Paragraph(f"R$ {c.get('gasto',0):,.2f}".replace(",","."), S["td_r"]),
                Paragraph(str(c.get("leads",0)), S["td_r"]),
                Paragraph(f"R$ {c.get('cpl',0):,.2f}".replace(",","."), S["td_r"]),
                Paragraph(c.get("taxa_qual","—"), S["td_r"]),
                Paragraph(c.get("avaliacao",""), S["td_orange"]),
            ])
        can_t = Table(c_rows, colWidths=[40*mm, 25*mm, 20*mm, 25*mm, 25*mm, 43*mm],
                      repeatRows=1)
        can_t.setStyle(table_style_default())
        story.append(can_t)
        story.append(Spacer(1, 4 * mm))

        # gráfico canais
        story.append(chart_barras_horizontais(
            [(c.get("canal",""), c.get("gasto",0), ORANGE)
             for c in d["canais"]],
            largura_mm=CW_MM, altura_mm=40,
            titulo="Distribuicao de gasto por canal",
        ))
        story.append(Spacer(1, 5 * mm))

    # evolução semana a semana
    if d.get("evolucao"):
        story.append(SectionHeader(4, "EVOLUCAO · SEMANA A SEMANA"))
        story.append(Spacer(1, 4 * mm))
        story.append(chart_barras_verticais_duplas(
            [(e.get("semana",""), e.get("leads",0), f"R${e.get('cpl',0):.2f}")
             for e in d["evolucao"]],
            largura_mm=CW_MM, altura_mm=55,
            label1="Leads", label2="CPL",
            titulo="Leads por semana vs CPL",
        ))
        story.append(Spacer(1, 5 * mm))

    # aprendizados
    if d.get("aprendizados"):
        story.append(InsightBox("APRENDIZADOS E OTIMIZACOES DO MES",
                                d["aprendizados"]))
        story.append(Spacer(1, 5 * mm))

    # plano próximo mês
    if d.get("plano_proximo_mes"):
        story.append(SectionHeader(5, "PLANO · PROXIMO MES"))
        story.append(Spacer(1, 4 * mm))
        pl_rows = [[
            Paragraph("ACAO", S["th"]),
            Paragraph("CANAL", S["th"]),
            Paragraph("IMPACTO ESPERADO", S["th"]),
        ]]
        for p in d["plano_proximo_mes"]:
            pl_rows.append([
                Paragraph(p.get("acao",""), S["td_bold"]),
                Paragraph(p.get("canal",""), S["td"]),
                Paragraph(p.get("impacto_esperado",""), S["td_green"]),
            ])
        pl_t = Table(pl_rows, colWidths=[80*mm, 30*mm, 68*mm], repeatRows=1)
        pl_t.setStyle(table_style_default())
        story.append(pl_t)

    def on_first(canvas, doc):
        draw_cover(canvas, doc,
                   titulo_doc="Resultado", subtitulo_doc="Mensal",
                   cliente=cliente, agencia=agencia, periodo=periodo,
                   info_extra=d.get("info_capa", ""),
                   frase_resumo=d.get("frase_resumo", ""),
                   frase_destaque=d.get("frase_destaque", ""))

    def on_later(canvas, doc):
        draw_footer(canvas, doc, cliente, total_pags)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return output_path
