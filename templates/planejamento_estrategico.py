"""
Template: Planejamento Estratégico
"""

from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.units import mm
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brand.design_system import (
    W, H, CW, CW_MM, MARGIN,
    NAVY, ORANGE, BLUE, GREEN, RED, YELLOW, GRAY_BG, GRAY_LINE, GRAY_DARK, WHITE,
    S, PageHeader, SectionHeader, MetricCard, InsightBox, TagBadge,
    make_cards_row, table_style_default, table_total_row,
    chart_barras_horizontais,
    draw_footer, draw_cover
)


def gerar(dados: dict, output_path: str):
    d = dados
    cliente    = d.get("cliente", "Cliente")
    periodo    = d.get("periodo", "")
    agencia    = d.get("agencia", "MarkSeg Trafego")
    horizonte  = d.get("horizonte", periodo or "90 dias")
    total_pags = 3

    doc = SimpleDocTemplate(
        output_path,
        pagesize=(W, H),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )

    story = [PageBreak()]

    # ── Página 2 – Diagnóstico + Objetivos + Pilares ──────────────────────
    story.append(PageHeader(cliente, f"Planejamento Estratégico · {horizonte}", "02 / 03"))
    story.append(Spacer(1, 4 * mm))

    # seção 1 – diagnóstico
    story.append(SectionHeader(1, "DIAGNOSTICO · SITUACAO ATUAL"))
    story.append(Spacer(1, 3 * mm))

    diag = d.get("diagnostico", [])
    if diag:
        linhas = "".join(f"<b>·</b>  {item}<br/>" for item in diag)
        box = Table([[Paragraph(linhas, S["body"])]], colWidths=[CW])
        box.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5 * mm),
            ("TOPPADDING",    (0, 0), (-1, -1), 4 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_LINE),
        ]))
        story.append(box)
    story.append(Spacer(1, 5 * mm))

    # seção 2 – objetivos e metas
    story.append(SectionHeader(2, "OBJETIVOS E METAS"))
    story.append(Spacer(1, 3 * mm))

    objetivos = d.get("objetivos", [])
    if objetivos:
        status_cor = {"OK": GREEN, "ALERTA": YELLOW, "CRITICO": RED}
        rows = [[
            Paragraph("HORIZONTE", S["th"]),
            Paragraph("OBJETIVO", S["th"]),
            Paragraph("KPI", S["th"]),
            Paragraph("META", S["th"]),
        ]]
        for o in objetivos:
            rows.append([
                TagBadge(o.get("prazo", ""), ORANGE),
                Paragraph(o.get("objetivo", ""), S["td_bold"]),
                Paragraph(o.get("kpi", ""), S["td"]),
                Paragraph(o.get("meta", ""), S["td_orange"]),
            ])
        t = Table(rows, colWidths=[28 * mm, 70 * mm, 50 * mm, 35 * mm], repeatRows=1)
        t.setStyle(table_style_default())
        story.append(t)
    story.append(Spacer(1, 5 * mm))

    # seção 3 – pilares estratégicos
    story.append(SectionHeader(3, "PILARES ESTRATEGICOS"))
    story.append(Spacer(1, 3 * mm))

    pilares = d.get("pilares", [])
    if pilares:
        PILAR_CORES = [NAVY, BLUE, ORANGE, GREEN, YELLOW]
        pilar_rows = []
        for i, p in enumerate(pilares):
            cor = PILAR_CORES[i % len(PILAR_CORES)]
            acoes = "".join(f"· {a}<br/>" for a in p.get("acoes", []))
            pilar_rows.append([
                TagBadge(p.get("nome", ""), cor),
                Paragraph(p.get("descricao", ""), S["body"]),
                Paragraph(acoes, S["body"]),
            ])
        pt = Table(pilar_rows, colWidths=[35 * mm, 60 * mm, 88 * mm])
        pt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, GRAY_BG]),
            ("GRID",          (0, 0), (-1, -1), 0.3, GRAY_LINE),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
            ("TOPPADDING",    (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))
        story.append(pt)

    story.append(PageBreak())

    # ── Página 3 – Cronograma + KPIs + Próximos passos ───────────────────
    story.append(PageHeader(cliente, f"Planejamento Estratégico · {horizonte}", "03 / 03"))
    story.append(Spacer(1, 4 * mm))

    # seção 4 – cronograma
    cronograma = d.get("cronograma", [])
    if cronograma:
        story.append(SectionHeader(4, "CRONOGRAMA DE IMPLANTACAO"))
        story.append(Spacer(1, 3 * mm))

        cron_rows = []
        for i in range(0, len(cronograma), 2):
            left = cronograma[i]
            right = cronograma[i + 1] if i + 1 < len(cronograma) else {"semana": "", "itens": []}

            def cell(s):
                itens = "".join(f"· {x}<br/>" for x in s.get("itens", []))
                return Paragraph(
                    f"<b>{s.get('semana','')}</b><br/>{itens}", S["body"]
                )

            cron_rows.append([cell(left), cell(right)])

        ct = Table(cron_rows, colWidths=[CW / 2 - 2 * mm, CW / 2 - 2 * mm])
        ct.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG),
            ("GRID",          (0, 0), (-1, -1), 0.3, GRAY_LINE),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
            ("TOPPADDING",    (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))
        story.append(ct)
        story.append(Spacer(1, 5 * mm))

    # seção 5 – KPIs de acompanhamento
    kpis = d.get("kpis", [])
    if kpis:
        story.append(SectionHeader(5, "KPIS DE ACOMPANHAMENTO"))
        story.append(Spacer(1, 3 * mm))

        kpi_rows = [[
            Paragraph("METRICA",  S["th"]),
            Paragraph("ATUAL",    S["th"]),
            Paragraph("META",     S["th"]),
            Paragraph("PRAZO",    S["th"]),
            Paragraph("CANAL",    S["th"]),
        ]]
        for k in kpis:
            kpi_rows.append([
                Paragraph(k.get("metrica", ""), S["td_bold"]),
                Paragraph(k.get("atual", "—"),  S["td"]),
                Paragraph(k.get("meta", "—"),   S["td_orange"]),
                Paragraph(k.get("prazo", "—"),  S["td"]),
                Paragraph(k.get("canal", "—"),  S["td"]),
            ])
        kt = Table(kpi_rows, colWidths=[55 * mm, 28 * mm, 35 * mm, 28 * mm, 37 * mm], repeatRows=1)
        kt.setStyle(table_style_default())
        story.append(kt)
        story.append(Spacer(1, 5 * mm))

    # seção 6 – riscos
    riscos = d.get("riscos", [])
    if riscos:
        story.append(SectionHeader(6, "RISCOS E MITIGACAO"))
        story.append(Spacer(1, 3 * mm))

        risco_rows = [[
            Paragraph("RISCO", S["th"]),
            Paragraph("MITIGACAO", S["th"]),
        ]]
        for r in riscos:
            risco_rows.append([
                Paragraph(r.get("risco", ""), S["td_bold"]),
                Paragraph(r.get("mitigacao", ""), S["td"]),
            ])
        rt = Table(risco_rows, colWidths=[80 * mm, 103 * mm], repeatRows=1)
        rt.setStyle(table_style_default())
        story.append(rt)
        story.append(Spacer(1, 5 * mm))

    # seção 7 – próximos passos
    proximos = d.get("proximos_passos", [])
    if proximos:
        story.append(SectionHeader(7, "PROXIMOS PASSOS PRIORITARIOS"))
        story.append(Spacer(1, 3 * mm))

        pp_rows = [[
            Paragraph("ACAO",        S["th"]),
            Paragraph("RESPONSAVEL", S["th"]),
            Paragraph("PRAZO",       S["th"]),
            Paragraph("IMPACTO",     S["th"]),
        ]]
        for p in proximos:
            pp_rows.append([
                Paragraph(p.get("acao", ""),        S["td_bold"]),
                Paragraph(p.get("responsavel", ""), S["td"]),
                Paragraph(p.get("prazo", ""),       S["td_orange"]),
                Paragraph(p.get("impacto", ""),     S["td"]),
            ])
        ppt = Table(pp_rows, colWidths=[85 * mm, 30 * mm, 28 * mm, 40 * mm], repeatRows=1)
        ppt.setStyle(table_style_default())
        story.append(ppt)

    def on_first(canvas, doc):
        draw_cover(canvas, doc,
                   titulo_doc="Planejamento", subtitulo_doc="Estrategico",
                   cliente=cliente, agencia=agencia, periodo=horizonte,
                   info_extra=d.get("info_capa", ""),
                   frase_resumo=d.get("frase_resumo", ""),
                   frase_destaque=d.get("frase_destaque", ""))

    def on_later(canvas, doc):
        draw_footer(canvas, doc, cliente, total_pags)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return output_path
