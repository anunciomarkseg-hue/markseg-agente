"""
Template: Plano de Mídia (14 seções · 100% local, sem API)
Recebe o dict produzido por parsers.parse_plano_midia_texto:
  - secoes: [{num, titulo, linhas:[str]}]  ← conteúdo do briefing por seção
  - extras: investimento, canais, cronograma, cpl_estimado_min/max, leads_estimados
Cada seção vira um cabeçalho + tópicos limpos. Onde há número reconhecido,
adiciona-se o widget certo: tabela de verba + donut (8), grade de cronograma
(12) e cards de KPI (13). Nada fica zerado: o que não é widget vira tópico.
"""

import io
from reportlab.platypus import (
    SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph, PageBreak,
)
from reportlab.lib.units import mm
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brand.design_system import (
    W, H, CW, CW_MM, MARGIN,
    NAVY, ORANGE, BLUE, GREEN, GRAY_BG, GRAY_LINE, WHITE,
    S, SectionHeader, InsightBox, TagBadge,
    make_cards_row, table_style_default, table_total_row,
    chart_donut, draw_footer, draw_cover,
)


# ── helpers ────────────────────────────────────────────────────────────────

def _esc(t) -> str:
    return (str(t).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))


def _brl(v) -> str:
    try:
        return f"R$ {float(v):,.0f}".replace(",", ".")
    except Exception:
        return "R$ 0"


def _topicos(linhas):
    """
    Renderiza as linhas de uma seção como tópicos. Se a linha é 'Rótulo: valor'
    com rótulo curto, o rótulo fica em negrito; senão vira bullet simples.
    """
    partes = []
    for l in linhas:
        l = str(l).strip()
        if not l:
            continue
        if ":" in l:
            rot, val = l.split(":", 1)
            if 0 < len(rot) <= 42 and val.strip():
                partes.append(f"<b>{_esc(rot.strip())}:</b> {_esc(val.strip())}")
                continue
        partes.append(f"• {_esc(l)}")
    return Paragraph("<br/>".join(partes), S["body"])


# ── montagem do corpo (fábrica: story nova a cada chamada) ─────────────────

def _build_story(d):
    invest = d.get("investimento", 0) or 0
    canais = d.get("canais") or []
    crono = d.get("cronograma") or []
    story = [PageBreak()]

    for s in d.get("secoes", []):
        num = s.get("num", 0)
        titulo = s.get("titulo", "")
        linhas = s.get("linhas", []) or []

        story.append(SectionHeader(num, titulo))
        story.append(Spacer(1, 4 * mm))

        # ── seção 13: cards de KPI antes dos tópicos ─────────────────────
        if num == 13:
            story.append(make_cards_row([
                {"label": "INVESTIMENTO/MÊS", "value": _brl(invest),
                 "sub": "verba de mídia", "cor": ORANGE},
                {"label": "LEADS ESTIMADOS", "value": d.get("leads_estimados", "—") or "—",
                 "sub": "hipótese mês 1", "cor": ORANGE},
                {"label": "CPL MÍN", "value": _brl(d.get("cpl_estimado_min", 0)),
                 "sub": "custo por lead", "cor": GREEN},
                {"label": "CPL MÁX", "value": _brl(d.get("cpl_estimado_max", 0)),
                 "sub": "custo por lead", "cor": ORANGE},
            ]))
            story.append(Spacer(1, 4 * mm))

        # tópicos do texto da seção
        if linhas:
            story.append(_topicos(linhas))
            story.append(Spacer(1, 4 * mm))

        # ── seção 8: tabela de verba + donut ─────────────────────────────
        if num == 8 and canais:
            etapa_cores = {"GOOGLE": GREEN, "META": BLUE, "RESERVA": NAVY}
            rows = [[Paragraph("ETAPA", S["th"]), Paragraph("CANAL", S["th"]),
                     Paragraph("FUNÇÃO", S["th"]), Paragraph("VERBA", S["th"]),
                     Paragraph("PART.", S["th"])]]
            for c in canais:
                cor = etapa_cores.get(str(c.get("etapa", "")).upper(), NAVY)
                rows.append([
                    TagBadge(str(c.get("etapa", "")) or "-", cor),
                    Paragraph(_esc(c.get("canal", "")), S["td_bold"]),
                    Paragraph(_esc(c.get("funcao", "")), S["td"]),
                    Paragraph(_brl(c.get("verba", 0)), S["td_r"]),
                    Paragraph(f"{c.get('percentual', 0):.0f}%", S["td_r"]),
                ])
            total = sum(float(c.get("verba", 0) or 0) for c in canais)
            rows.append([Paragraph("TOTAL", S["th"]), Paragraph("", S["th"]),
                         Paragraph("Investimento total", S["th"]),
                         Paragraph(_brl(total), S["th"]), Paragraph("100%", S["th"])])
            ct = Table(rows, colWidths=[20 * mm, 45 * mm, 65 * mm, 25 * mm, 15 * mm],
                       repeatRows=1)
            ct.setStyle(table_style_default())
            ct.setStyle(table_total_row(len(rows) - 1))
            story.append(ct)
            story.append(Spacer(1, 4 * mm))

            graf = [(f"{c.get('etapa', '')} · {c.get('canal', '')}",
                     float(c.get("verba", 0) or 0),
                     etapa_cores.get(str(c.get("etapa", "")).upper(), NAVY))
                    for c in canais if float(c.get("verba", 0) or 0) > 0]
            if graf:
                story.append(chart_donut(graf, CW_MM, 48,
                                         titulo="Distribuição do investimento"))
                story.append(Spacer(1, 4 * mm))

        # ── seção 12: grade de cronograma ────────────────────────────────
        if num == 12 and crono:
            sem = list(crono)
            while len(sem) % 2 != 0:
                sem.append({"semana": "", "itens": []})

            def _cell(x):
                itens = x.get("itens", x.get("acoes", [])) or []
                body = "<br/>".join(f"• {_esc(i)}" for i in itens)
                return Paragraph(f"<b>{_esc(x.get('semana', ''))}</b><br/>{body}", S["body"])

            rows = [[_cell(sem[i]), _cell(sem[i + 1])] for i in range(0, len(sem), 2)]
            g = Table(rows, colWidths=[CW / 2 - 2 * mm, CW / 2 - 2 * mm])
            g.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG),
                ("GRID",          (0, 0), (-1, -1), 0.3, GRAY_LINE),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING",    (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]))
            story.append(g)
            story.append(Spacer(1, 4 * mm))

        story.append(Spacer(1, 2 * mm))

    # palavras-chave (se houver)
    if d.get("palavras_chave"):
        kws = "  ·  ".join(d["palavras_chave"])
        ret = Table([[Paragraph(
            f"<b>PALAVRAS-CHAVE PRIORITÁRIAS:</b>  {_esc(kws)}", S["insight"]
        )]], colWidths=[CW])
        ret.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
            ("TOPPADDING",    (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))
        story.append(Spacer(1, 3 * mm))
        story.append(ret)

    return story


def gerar(dados: dict, output_path: str):
    d = dados
    cliente = d.get("cliente", "Cliente")
    periodo = d.get("periodo", "")
    agencia = d.get("agencia", "MarkSeg Tráfego")

    def _novo_doc(destino):
        return SimpleDocTemplate(
            destino, pagesize=(W, H),
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=16 * mm, bottomMargin=16 * mm,
        )

    def on_first(canvas, doc):
        draw_cover(canvas, doc,
                   titulo_doc="Plano de", subtitulo_doc="Mídia",
                   cliente=cliente, agencia=agencia, periodo=periodo,
                   info_extra=d.get("info_capa", ""),
                   frase_resumo=d.get("frase_resumo", ""),
                   frase_destaque=d.get("frase_destaque", ""))

    # passo 1 — conta as páginas (documento tem tamanho variável)
    total_pags = 2
    try:
        contador = {"n": 0}
        def _cont(canvas, doc):
            contador["n"] = doc.page
        _novo_doc(io.BytesIO()).build(
            _build_story(d), onFirstPage=_cont, onLaterPages=_cont)
        total_pags = max(contador["n"], 1)
    except Exception:
        total_pags = 2

    def on_later(canvas, doc):
        draw_footer(canvas, doc, cliente, total_pags)

    # passo 2 — build final com o total correto no rodapé
    _novo_doc(output_path).build(
        _build_story(d), onFirstPage=on_first, onLaterPages=on_later)
    return output_path
