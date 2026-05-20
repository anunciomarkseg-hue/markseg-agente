"""
Template: Relatório Semanal de Mídias Sociais
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
    chart_barras_horizontais, chart_barras_verticais_duplas,
    draw_footer, draw_cover
)


def gerar(dados: dict, output_path: str):
    """
    dados = {
        "cliente":   str,
        "periodo":   str,
        "agencia":   str,
        "redes":     ["Instagram", "Facebook", ...],

        # KPIs gerais
        "seguidores_atual":   int,
        "seguidores_novos":   int,
        "alcance_total":      int,
        "impressoes_total":   int,
        "engajamento_medio":  str,   # ex: "4,2%"
        "saves_total":        int,

        # Posts da semana (lista de dicts)
        "posts": [
            {"data": str, "formato": "Reels|Carrossel|Estático",
             "titulo": str, "alcance": int, "impressoes": int,
             "curtidas": int, "comentarios": int, "saves": int,
             "engajamento": str, "destaque": bool}
        ],

        # Top stories
        "top_stories": [
            {"descricao": str, "visualizacoes": int, "saidas": int}
        ],

        # Reels
        "reels": [
            {"titulo": str, "reproducoes": int, "alcance": int,
             "engajamento": str, "destaque": bool}
        ],

        # Insights e recomendações
        "insights_semana":    [str, ...],
        "recomendacoes":      [str, ...],

        # Próximos passos
        "proximos_passos": [
            {"acao": str, "responsavel": str, "prazo": str}
        ],

        # Pauta sugerida próxima semana
        "pauta_proxima": [
            {"dia": str, "formato": str, "tema": str, "objetivo": str}
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

    # ── PÁG 2 ─────────────────────────────────────────────────────────────
    story.append(PageHeader(cliente, f"Social Media · {periodo}", "02 / 02"))
    story.append(Spacer(1, 4 * mm))

    story.append(SectionHeader(1, "VISAO GERAL · SEMANA"))
    story.append(Spacer(1, 4 * mm))

    story.append(make_cards_row([
        {"label": "SEGUIDORES NOVOS",   "value": f"+{d.get('seguidores_novos',0)}",
         "sub": f"total: {d.get('seguidores_atual',0):,}".replace(",","."), "cor": GREEN},
        {"label": "ALCANCE TOTAL",      "value": f"{d.get('alcance_total',0):,}".replace(",","."),
         "sub": "pessoas unicas alcancadas",  "cor": ORANGE},
        {"label": "IMPRESSOES",         "value": f"{d.get('impressoes_total',0):,}".replace(",","."),
         "sub": "total de visualizacoes",     "cor": ORANGE},
        {"label": "ENGAJAMENTO MEDIO",  "value": d.get("engajamento_medio", "—"),
         "sub": "curtidas + coment + saves",  "cor": ORANGE},
        {"label": "SAVES",              "value": str(d.get("saves_total", 0)),
         "sub": "conteudo salvo",             "cor": BLUE},
    ], n_cols=5))
    story.append(Spacer(1, 5 * mm))

    # tabela de posts
    story.append(SectionHeader(2, "POSTS DA SEMANA · PERFORMANCE"))
    story.append(Spacer(1, 4 * mm))

    post_rows = [[
        Paragraph("DATA", S["th"]),        Paragraph("FORMATO", S["th"]),
        Paragraph("TITULO", S["th"]),      Paragraph("ALCANCE", S["th"]),
        Paragraph("CURTIDAS", S["th"]),    Paragraph("SAVES", S["th"]),
        Paragraph("ENGAJ.", S["th"]),
    ]]
    for post in d.get("posts", []):
        dest = post.get("destaque", False)
        post_rows.append([
            Paragraph(post.get("data", ""), S["td"]),
            TagBadge(post.get("formato", "")[:8],
                     ORANGE if "Reels" in post.get("formato","") else NAVY,
                     largura=16*mm),
            Paragraph(post.get("titulo", ""), S["td_bold"] if dest else S["td"]),
            Paragraph(f"{post.get('alcance',0):,}".replace(",","."), S["td_r"]),
            Paragraph(str(post.get("curtidas", 0)), S["td_r"]),
            Paragraph(str(post.get("saves", 0)), S["td_r"]),
            Paragraph(post.get("engajamento", ""), S["td_green"] if dest else S["td"]),
        ])

    post_cols = [16*mm, 18*mm, 65*mm, 20*mm, 18*mm, 14*mm, 16*mm]
    pt = Table(post_rows, colWidths=post_cols, repeatRows=1)
    pt.setStyle(table_style_default())
    story.append(pt)
    story.append(Spacer(1, 4 * mm))

    # gráfico alcance por post
    if d.get("posts"):
        graf = chart_barras_horizontais(
            [(p.get("titulo","")[:30], p.get("alcance",0), ORANGE)
             for p in d.get("posts", [])],
            largura_mm=CW_MM, altura_mm=max(35, len(d["posts"]) * 10),
            formato="{:,.0f}", titulo="Alcance por post",
        )
        story.append(graf)
        story.append(Spacer(1, 5 * mm))

    # reels
    if d.get("reels"):
        story.append(SectionHeader(3, "REELS · PERFORMANCE"))
        story.append(Spacer(1, 4 * mm))
        r_rows = [[
            Paragraph("TITULO", S["th"]),        Paragraph("REPRODUCOES", S["th"]),
            Paragraph("ALCANCE", S["th"]),        Paragraph("ENGAJAMENTO", S["th"]),
        ]]
        for r in d["reels"]:
            dest = r.get("destaque", False)
            r_rows.append([
                Paragraph(r.get("titulo", ""), S["td_bold"] if dest else S["td"]),
                Paragraph(f"{r.get('reproducoes',0):,}".replace(",","."), S["td_r"]),
                Paragraph(f"{r.get('alcance',0):,}".replace(",","."), S["td_r"]),
                Paragraph(r.get("engajamento", ""), S["td_green"] if dest else S["td"]),
            ])
        rt = Table(r_rows, colWidths=[100*mm, 30*mm, 25*mm, 23*mm], repeatRows=1)
        rt.setStyle(table_style_default())
        story.append(rt)
        story.append(Spacer(1, 5 * mm))

    # insights
    if d.get("insights_semana"):
        story.append(InsightBox("INSIGHTS DA SEMANA", d["insights_semana"]))
        story.append(Spacer(1, 4 * mm))

    # pauta próxima semana
    if d.get("pauta_proxima"):
        story.append(SectionHeader(4, "PAUTA · PROXIMA SEMANA"))
        story.append(Spacer(1, 4 * mm))
        ppr = [[
            Paragraph("DIA", S["th"]),        Paragraph("FORMATO", S["th"]),
            Paragraph("TEMA", S["th"]),        Paragraph("OBJETIVO", S["th"]),
        ]]
        for item in d["pauta_proxima"]:
            ppr.append([
                Paragraph(item.get("dia", ""), S["td_bold"]),
                Paragraph(item.get("formato", ""), S["td"]),
                Paragraph(item.get("tema", ""), S["td"]),
                Paragraph(item.get("objetivo", ""), S["td"]),
            ])
        ppt = Table(ppr, colWidths=[18*mm, 22*mm, 90*mm, 48*mm], repeatRows=1)
        ppt.setStyle(table_style_default())
        story.append(ppt)
        story.append(Spacer(1, 4 * mm))

    if d.get("recomendacoes"):
        story.append(InsightBox("RECOMENDACOES ESTRATEGICAS",
                                d["recomendacoes"]))

    def on_first(canvas, doc):
        draw_cover(canvas, doc,
                   titulo_doc="Relatorio de", subtitulo_doc="Midias Sociais",
                   cliente=cliente, agencia=agencia, periodo=periodo,
                   info_extra=d.get("info_capa", ""),
                   frase_resumo=d.get("frase_resumo", ""),
                   frase_destaque=d.get("frase_destaque", ""))

    def on_later(canvas, doc):
        draw_footer(canvas, doc, cliente, total_pags)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return output_path
