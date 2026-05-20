"""
Template: Proposta Comercial
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
    draw_footer, draw_cover
)


def gerar(dados: dict, output_path: str):
    """
    dados = {
        "cliente":        str,
        "periodo":        str,
        "agencia":        str,
        "responsavel":    str,
        "data_proposta":  str,
        "validade":       str,   # ex: "30 dias"

        # Diagnóstico (lista de strings)
        "diagnostico": [str, ...],

        # Serviços propostos
        "servicos": [
            {"nome": str, "descricao": str, "investimento": float,
             "recorrente": bool}
        ],

        # Verba de mídia
        "verba_midia":    float,
        "honorarios":     float,
        "total_mensal":   float,

        # Resultados esperados
        "resultados_esperados": [
            {"metrica": str, "valor": str, "prazo": str}
        ],

        # Diferenciais MarkSeg
        "diferenciais": [str, ...],

        # Próximos passos
        "proximos_passos": [
            {"passo": str, "prazo": str}
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

    story.append(PageHeader(cliente, f"Proposta Comercial · {d.get('data_proposta','')}",
                             "02 / 02"))
    story.append(Spacer(1, 4 * mm))

    # diagnóstico
    if d.get("diagnostico"):
        story.append(SectionHeader(1, "DIAGNOSTICO · CENARIO ATUAL"))
        story.append(Spacer(1, 4 * mm))
        story.append(InsightBox("ANALISE INICIAL", d["diagnostico"],
                                cor=NAVY))
        story.append(Spacer(1, 5 * mm))

    # serviços
    story.append(SectionHeader(2, "SERVICOS PROPOSTOS"))
    story.append(Spacer(1, 4 * mm))

    srv_rows = [[
        Paragraph("SERVICO", S["th"]),
        Paragraph("DESCRICAO", S["th"]),
        Paragraph("INVESTIMENTO", S["th"]),
        Paragraph("TIPO", S["th"]),
    ]]
    for svc in d.get("servicos", []):
        srv_rows.append([
            Paragraph(svc.get("nome", ""), S["td_bold"]),
            Paragraph(svc.get("descricao", ""), S["td"]),
            Paragraph(f"R$ {svc.get('investimento',0):,.0f}".replace(",","."), S["td_r"]),
            Paragraph("Mensal" if svc.get("recorrente") else "Unico", S["td"]),
        ])

    srv_t = Table(srv_rows, colWidths=[45*mm, 90*mm, 30*mm, 18*mm], repeatRows=1)
    srv_t.setStyle(table_style_default())
    story.append(srv_t)
    story.append(Spacer(1, 4 * mm))

    # investimento total
    vm = d.get("verba_midia", 0)
    hon = d.get("honorarios", 0)
    tot = d.get("total_mensal", vm + hon)
    story.append(make_cards_row([
        {"label": "VERBA DE MIDIA",  "value": f"R$ {vm:,.0f}".replace(",","."),
         "sub": "investimento em ads",    "cor": ORANGE},
        {"label": "HONORARIOS",      "value": f"R$ {hon:,.0f}".replace(",","."),
         "sub": "gestao + estrategia",    "cor": ORANGE},
        {"label": "TOTAL MENSAL",    "value": f"R$ {tot:,.0f}".replace(",","."),
         "sub": "investimento total",     "cor": NAVY},
        {"label": "VALIDADE",        "value": d.get("validade", "30 dias"),
         "sub": "desta proposta",         "cor": BLUE},
    ]))
    story.append(Spacer(1, 5 * mm))

    # resultados esperados
    if d.get("resultados_esperados"):
        story.append(SectionHeader(3, "RESULTADOS ESPERADOS"))
        story.append(Spacer(1, 4 * mm))
        res_rows = [[
            Paragraph("METRICA", S["th"]),
            Paragraph("VALOR PROJETADO", S["th"]),
            Paragraph("PRAZO", S["th"]),
        ]]
        for r in d["resultados_esperados"]:
            res_rows.append([
                Paragraph(r.get("metrica", ""), S["td_bold"]),
                Paragraph(r.get("valor", ""), S["td_green"]),
                Paragraph(r.get("prazo", ""), S["td"]),
            ])
        res_t = Table(res_rows, colWidths=[70*mm, 60*mm, 48*mm], repeatRows=1)
        res_t.setStyle(table_style_default())
        story.append(res_t)
        story.append(Spacer(1, 5 * mm))

    # diferenciais
    if d.get("diferenciais"):
        story.append(SectionHeader(4, "POR QUE MARKSEG"))
        story.append(Spacer(1, 4 * mm))
        story.append(InsightBox("NOSSOS DIFERENCIAIS", d["diferenciais"]))
        story.append(Spacer(1, 5 * mm))

    # próximos passos
    if d.get("proximos_passos"):
        story.append(SectionHeader(5, "PROXIMOS PASSOS · COMO COMECAR"))
        story.append(Spacer(1, 4 * mm))
        pp_rows = [[
            Paragraph("PASSO", S["th"]),
            Paragraph("PRAZO", S["th"]),
        ]]
        for i, pp in enumerate(d["proximos_passos"], 1):
            pp_rows.append([
                Paragraph(f"{i}. {pp.get('passo','')}", S["td_bold"]),
                Paragraph(pp.get("prazo", ""), S["td_orange"]),
            ])
        pp_t = Table(pp_rows, colWidths=[CW - 35*mm, 35*mm], repeatRows=1)
        pp_t.setStyle(table_style_default())
        story.append(pp_t)
        story.append(Spacer(1, 3 * mm))

    # rodapé proposta
    assina = Table([[
        Paragraph(
            f"<b>MarkSeg Agencia de Trafego</b>  ·  {d.get('responsavel','')}  "
            f"·  Proposta valida por {d.get('validade','30 dias')}",
            S["insight"]
        )
    ]], colWidths=[CW])
    assina.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("LEFTPADDING",   (0,0), (-1,-1), 4*mm),
        ("TOPPADDING",    (0,0), (-1,-1), 3*mm),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3*mm),
    ]))
    story.append(assina)

    def on_first(canvas, doc):
        draw_cover(canvas, doc,
                   titulo_doc="Proposta", subtitulo_doc="Comercial",
                   cliente=cliente, agencia=agencia, periodo=periodo,
                   info_extra=d.get("info_capa", ""),
                   frase_resumo=d.get("frase_resumo", ""),
                   frase_destaque=d.get("frase_destaque", ""))

    def on_later(canvas, doc):
        draw_footer(canvas, doc, cliente, total_pags)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return output_path
