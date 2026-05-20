"""
Template: Relatório Semanal de Performance (Meta Ads + Google Ads)
"""

from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.units import mm
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brand.design_system import (
    W, H, CW, CW_MM, MARGIN,
    NAVY, ORANGE, BLUE, GREEN, RED, YELLOW, GRAY_BG, GRAY_LINE, GRAY_LIGHT, WHITE,
    S, PageHeader, SectionHeader, MetricCard, InsightBox, TagBadge,
    make_cards_row, table_style_default, table_total_row,
    chart_barras_horizontais, chart_donut, chart_barras_verticais_duplas,
    draw_footer, draw_cover
)


def gerar(dados: dict, output_path: str):
    """
    dados = {
        "cliente":      str,
        "periodo":      str,
        "agencia":      str,
        "responsavel":  str,

        # Meta Ads - campanhas (lista de dicts)
        "meta_campanhas": [
            {"etapa": "TOPO|MEIO|FUNDO", "nome": str, "verba": float,
             "resultado": str, "cpr": float, "impressoes": int}
        ],
        "meta_total":    float,
        "meta_leads":    int,
        "meta_cpl":      float,

        # Criativos (lista de dicts)
        "criativos": [
            {"nome": str, "status": "Ativo|Inativo", "gasto": float,
             "leads": int, "cpl": float, "hook": str, "hold": str,
             "avaliacao": str, "destaque": bool}
        ],

        # Conjuntos de anúncios (lista de dicts)
        "conjuntos": [
            {"nome": str, "status": str, "orcamento": float,
             "gasto": float, "leads": int, "cpl": float, "alcance": int}
        ],

        # Google Ads
        "google_gasto":      float,
        "google_cliques":    int,
        "google_impressoes": int,
        "google_ctr":        str,
        "google_conv":       int,
        "google_cpl":        float,

        # Insights (listas de strings)
        "insights_criativos": [str, ...],
        "insights_google":    [str, ...],

        # Próximos passos
        "proximos_passos": [
            {"acao": str, "responsavel": str, "prazo": str, "impacto": str}
        ],

        # Conteúdo orgânico
        "sugestoes_conteudo": [str, ...],

        # Estratégia seguidores
        "estrategia_seguidores": [
            {"iniciativa": str, "acao": str, "prioridade": str}
        ],

        # Resumo da capa
        "frase_resumo":    str,
        "frase_destaque":  str,
        "info_capa":       str,
    }
    """
    d = dados
    cliente     = d.get("cliente", "Cliente")
    periodo     = d.get("periodo", "")
    agencia     = d.get("agencia", "MarkSeg Trafego")
    responsavel = d.get("responsavel", "Rafael")
    total_pags  = 3

    doc = SimpleDocTemplate(
        output_path,
        pagesize=(W, H),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )

    story = [PageBreak()]   # página 1 = capa, story começa na pág. 2

    # ── PÁG 2 · META ADS ──────────────────────────────────────────────────
    story.append(PageHeader(cliente, f"Semana · {periodo}", "02 / 03"))
    story.append(Spacer(1, 4 * mm))

    # seção 1 – visão geral meta
    story.append(SectionHeader(1, "META ADS · VISAO GERAL DA SEMANA"))
    story.append(Spacer(1, 4 * mm))

    meta_total  = d.get("meta_total", 0)
    meta_leads  = d.get("meta_leads", 0)
    meta_cpl    = d.get("meta_cpl", 0)
    meta_melhor = min((c["cpl"] for c in d.get("criativos", [])
                       if c.get("leads", 0) >= 5), default=meta_cpl)

    story.append(make_cards_row([
        {"label": "INVESTIMENTO META", "value": f"R$ {meta_total:,.2f}".replace(",","."),
         "sub": "total 7 dias",        "cor": ORANGE},
        {"label": "LEADS GERADOS",     "value": str(meta_leads),
         "sub": "campanha fundo",      "cor": ORANGE},
        {"label": "CPL MEDIO FUNDO",   "value": f"R$ {meta_cpl:,.2f}".replace(",","."),
         "sub": "custo por lead",      "cor": ORANGE},
        {"label": "CPL VENCEDOR",      "value": f"R$ {meta_melhor:,.2f}".replace(",","."),
         "sub": "melhor criativo",     "cor": GREEN},
    ]))
    story.append(Spacer(1, 5 * mm))

    # tabela funil
    story.append(Paragraph("Distribuicao por etapa do funil",
                            S["body_bold"]))
    story.append(Spacer(1, 2 * mm))

    etapa_cores = {"TOPO": NAVY, "MEIO": BLUE, "FUNDO": ORANGE}
    funil_rows = [[
        Paragraph("ETAPA", S["th"]), Paragraph("CAMPANHA", S["th"]),
        Paragraph("VERBA", S["th"]), Paragraph("RESULTADO", S["th"]),
        Paragraph("CPR", S["th"]),   Paragraph("IMP.", S["th"]),
    ]]
    for camp in d.get("meta_campanhas", []):
        etapa_cor = etapa_cores.get(camp.get("etapa", "FUNDO").upper(), NAVY)
        funil_rows.append([
            TagBadge(camp.get("etapa", ""), etapa_cor),
            Paragraph(camp.get("nome", ""), S["td"]),
            Paragraph(f"R$ {camp.get('verba', 0):,.2f}".replace(",","."), S["td_r"]),
            Paragraph(camp.get("resultado", ""), S["td"]),
            Paragraph(f"R$ {camp.get('cpr', 0):,.2f}".replace(",","."), S["td_r"]),
            Paragraph(f"{camp.get('impressoes', 0):,}".replace(",","."), S["td_r"]),
        ])

    total_imp = sum(c.get("impressoes", 0) for c in d.get("meta_campanhas", []))
    funil_rows.append([
        Paragraph("TOTAL", S["th"]), Paragraph("", S["th"]),
        Paragraph(f"R$ {meta_total:,.2f}".replace(",","."), S["th"]),
        Paragraph(f"{meta_leads} leads", S["th"]),
        Paragraph(f"R$ {meta_cpl:,.2f}".replace(",","."), S["th"]),
        Paragraph(f"{total_imp:,}".replace(",","."), S["th"]),
    ])

    funil_cols = [18*mm, 65*mm, 22*mm, 38*mm, 18*mm, 17*mm]
    ft = Table(funil_rows, colWidths=funil_cols, repeatRows=1)
    ft.setStyle(table_style_default())
    ft.setStyle(table_total_row(len(funil_rows) - 1))
    story.append(ft)
    story.append(Spacer(1, 4 * mm))

    # gráfico funil
    graf_funil = chart_barras_horizontais(
        [(c.get("etapa","") + " · " + c.get("nome","")[:25],
          c.get("verba", 0),
          etapa_cores.get(c.get("etapa","FUNDO").upper(), NAVY))
         for c in d.get("meta_campanhas", [])],
        largura_mm=CW_MM, altura_mm=45,
        titulo="Investimento por etapa do funil",
    )
    story.append(graf_funil)
    story.append(Spacer(1, 5 * mm))

    # seção 2 – criativos
    story.append(SectionHeader(2, "ANALISE DE CRIATIVOS · FUNDO DE FUNIL"))
    story.append(Spacer(1, 4 * mm))

    cri_rows = [[
        Paragraph("CRIATIVO", S["th"]), Paragraph("STATUS", S["th"]),
        Paragraph("GASTO", S["th"]),    Paragraph("LEADS", S["th"]),
        Paragraph("CPL", S["th"]),      Paragraph("HOOK RATE", S["th"]),
        Paragraph("AVALIACAO", S["th"]),
    ]]
    for cri in d.get("criativos", []):
        ativo  = cri.get("status", "") == "Ativo"
        dest   = cri.get("destaque", False)
        cri_rows.append([
            Paragraph(cri.get("nome", ""), S["td_bold"] if dest else S["td"]),
            Paragraph(cri.get("status", ""), S["td_green"] if ativo else S["td_red"]),
            Paragraph(f"R$ {cri.get('gasto', 0):,.2f}".replace(",","."), S["td_r"]),
            Paragraph(str(cri.get("leads", 0)),
                      S["td_green"] if dest else S["td"]),
            Paragraph(f"R$ {cri.get('cpl', 0):,.2f}".replace(",","."),
                      S["td_green"] if cri.get("leads", 0) >= 5 else S["td"]),
            Paragraph(cri.get("hook", "—"), S["td_r"]),
            Paragraph(cri.get("avaliacao", ""), S["td_orange"] if dest else S["td"]),
        ])

    cri_cols = [42*mm, 14*mm, 18*mm, 12*mm, 18*mm, 18*mm, 26*mm]
    ct = Table(cri_rows, colWidths=cri_cols, repeatRows=1)
    ct.setStyle(table_style_default())
    story.append(ct)
    story.append(Spacer(1, 4 * mm))

    # gráfico criativos
    cri_graf_dados = [
        (c.get("nome", "")[:15], c.get("leads", 0),
         f"R${c.get('cpl',0):.2f}")
        for c in d.get("criativos", []) if c.get("leads", 0) > 0
    ]
    if cri_graf_dados:
        story.append(chart_barras_verticais_duplas(
            cri_graf_dados, CW_MM, 50,
            label1="Leads", label2="CPL",
            titulo="Comparativo de criativos · leads x CPL",
        ))
        story.append(Spacer(1, 4 * mm))

    if d.get("insights_criativos"):
        story.append(InsightBox("INSIGHT · CRIATIVO VENCEDOR",
                                d["insights_criativos"]))
        story.append(Spacer(1, 5 * mm))

    # seção 3 – conjuntos
    story.append(SectionHeader(3, "CONJUNTOS DE ANUNCIOS · FUNDO"))
    story.append(Spacer(1, 4 * mm))

    conj_rows = [[
        Paragraph("CONJUNTO", S["th"]),   Paragraph("STATUS", S["th"]),
        Paragraph("ORC./DIA", S["th"]),   Paragraph("GASTO", S["th"]),
        Paragraph("LEADS", S["th"]),      Paragraph("CPL", S["th"]),
        Paragraph("ALCANCE", S["th"]),
    ]]
    for conj in d.get("conjuntos", []):
        ativo = conj.get("status", "") == "Ativo"
        cpl   = conj.get("cpl", 0)
        conj_rows.append([
            Paragraph(conj.get("nome", ""), S["td_bold"]),
            Paragraph(conj.get("status", ""), S["td_green"] if ativo else S["td_red"]),
            Paragraph(f"R$ {conj.get('orcamento',0):,.2f}".replace(",","."), S["td_r"]),
            Paragraph(f"R$ {conj.get('gasto',0):,.2f}".replace(",","."), S["td_r"]),
            Paragraph(str(conj.get("leads", 0)), S["td"]),
            Paragraph(f"R$ {cpl:,.2f}".replace(",","."),
                      S["td_green"] if cpl < 10 else S["td_red"]),
            Paragraph(f"{conj.get('alcance',0):,}".replace(",","."), S["td_r"]),
        ])

    conj_cols = [60*mm, 14*mm, 18*mm, 18*mm, 12*mm, 18*mm, 18*mm]
    conj_t = Table(conj_rows, colWidths=conj_cols, repeatRows=1)
    conj_t.setStyle(table_style_default())
    story.append(conj_t)

    # ── PÁG 3 · GOOGLE + SEGUIDORES + PRÓXIMOS PASSOS ────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(PageHeader(cliente, f"Semana · {periodo}", "03 / 03"))
    story.append(Spacer(1, 4 * mm))

    # seção 4 – google
    story.append(SectionHeader(4, "GOOGLE ADS · BRAND SEARCH"))
    story.append(Spacer(1, 4 * mm))

    g_gasto = d.get("google_gasto", 0)
    story.append(make_cards_row([
        {"label": "INVESTIMENTO",  "value": f"R$ {g_gasto:,.2f}".replace(",","."),
         "sub": "7 dias",          "cor": ORANGE},
        {"label": "CLIQUES",       "value": str(d.get("google_cliques", 0)),
         "sub": "brand search",    "cor": ORANGE},
        {"label": "IMPRESSOES",    "value": str(d.get("google_impressoes", 0)),
         "sub": "brand search",    "cor": ORANGE},
        {"label": "CTR",           "value": d.get("google_ctr", "0%"),
         "sub": "taxa de clique",  "cor": GREEN},
        {"label": "CONVERSOES",    "value": str(d.get("google_conv", 0)),
         "sub": f"R$ {d.get('google_cpl',0):,.2f}/conv".replace(",","."), "cor": GREEN},
    ], n_cols=5))
    story.append(Spacer(1, 4 * mm))

    # donut split
    story.append(chart_donut(
        [("Meta Ads", meta_total, ORANGE), ("Google Ads", g_gasto, NAVY)],
        largura_mm=CW_MM, altura_mm=42,
        titulo="Distribuicao do investimento total · semana",
    ))
    story.append(Spacer(1, 4 * mm))

    if d.get("insights_google"):
        story.append(InsightBox("GOOGLE · ANALISE", d["insights_google"],
                                cor=NAVY))
        story.append(Spacer(1, 5 * mm))

    # seção 5 – seguidores
    if d.get("estrategia_seguidores"):
        story.append(SectionHeader(5, "ESTRATEGIA · CRESCIMENTO DE SEGUIDORES"))
        story.append(Spacer(1, 4 * mm))
        seg_rows = [[
            Paragraph("INICIATIVA", S["th"]),
            Paragraph("ACAO", S["th"]),
            Paragraph("PRIORIDADE", S["th"]),
        ]]
        for item in d["estrategia_seguidores"]:
            seg_rows.append([
                Paragraph(item.get("iniciativa", ""), S["td_bold"]),
                Paragraph(item.get("acao", ""), S["td"]),
                Paragraph(item.get("prioridade", ""), S["td_orange"]),
            ])
        seg_t = Table(seg_rows, colWidths=[45*mm, 100*mm, 28*mm], repeatRows=1)
        seg_t.setStyle(table_style_default())
        story.append(seg_t)
        story.append(Spacer(1, 4 * mm))

    if d.get("sugestoes_conteudo"):
        story.append(InsightBox(
            "SUGESTOES DE CONTEUDO · TOPICOS QUE ESTAO FUNCIONANDO",
            d["sugestoes_conteudo"],
        ))
        story.append(Spacer(1, 5 * mm))

    # seção 6 – próximos passos
    story.append(SectionHeader(6, "PROXIMOS PASSOS · SEMANA SEGUINTE"))
    story.append(Spacer(1, 4 * mm))

    pp_rows = [[
        Paragraph("ACAO", S["th"]),        Paragraph("RESPONSAVEL", S["th"]),
        Paragraph("PRAZO", S["th"]),       Paragraph("IMPACTO", S["th"]),
    ]]
    for pp in d.get("proximos_passos", []):
        pp_rows.append([
            Paragraph(pp.get("acao", ""), S["td_bold"]),
            Paragraph(pp.get("responsavel", ""), S["td"]),
            Paragraph(pp.get("prazo", ""), S["td_orange"]),
            Paragraph(pp.get("impacto", ""), S["td"]),
        ])
    pp_t = Table(pp_rows, colWidths=[80*mm, 35*mm, 25*mm, 38*mm], repeatRows=1)
    pp_t.setStyle(table_style_default())
    story.append(pp_t)
    story.append(Spacer(1, 3 * mm))

    # retorno
    ret_t = Table([[Paragraph(
        "->  <b>RETORNO MARKSEG:</b>  Relatorio semanal · updates no WhatsApp"
        " · acesso ao painel · reuniao mensal de calibracao.",
        S["insight"]
    )]], colWidths=[CW])
    ret_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("LEFTPADDING",   (0,0), (-1,-1), 4 * mm),
        ("TOPPADDING",    (0,0), (-1,-1), 3 * mm),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3 * mm),
    ]))
    story.append(ret_t)

    # ── Build ─────────────────────────────────────────────────────────────
    def on_first(canvas, doc):
        draw_cover(
            canvas, doc,
            titulo_doc    = "Relatorio de",
            subtitulo_doc = "Performance Semanal",
            cliente       = cliente,
            agencia       = agencia,
            periodo       = periodo,
            info_extra    = d.get("info_capa", ""),
            frase_resumo  = d.get("frase_resumo", ""),
            frase_destaque= d.get("frase_destaque", ""),
        )

    def on_later(canvas, doc):
        draw_footer(canvas, doc, cliente, total_pags)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return output_path
