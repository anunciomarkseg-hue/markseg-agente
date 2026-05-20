"""
Template: Planejamento Estratégico
Renderiza qualquer texto estruturado — headers, tabelas, bullets, parágrafos.
"""

from reportlab.platypus import (
    SimpleDocTemplate, Spacer, Table, TableStyle,
    Paragraph, PageBreak, KeepTogether
)
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brand.design_system import (
    W, H, CW, MARGIN,
    NAVY, ORANGE, BLUE, GREEN, GRAY_BG, GRAY_LINE, GRAY_DARK, WHITE,
    S, style, PageHeader, SectionHeader,
    draw_footer, draw_cover,
)

# estilos locais
S_TITULO   = style("plan_titulo",   size=16, bold=True, color=NAVY)
S_SUBSEC   = style("plan_subsec",   size=11, bold=True, color=NAVY)
S_BODY     = style("plan_body",     size=9,  color=GRAY_DARK, leading=14)
S_BULLET   = style("plan_bullet",   size=9,  color=GRAY_DARK, leading=14)
S_KV_KEY   = style("plan_kv_key",   size=9,  bold=True, color=NAVY)
S_KV_VAL   = style("plan_kv_val",   size=9,  color=GRAY_DARK, leading=13)
S_TH       = style("plan_th",       size=8,  bold=True, color=WHITE)
S_TD       = style("plan_td",       size=8,  color=GRAY_DARK, leading=12)


def _sp(n=3):
    return Spacer(1, n * mm)


def _render_bloco(bloco: dict) -> list:
    """Converte um bloco de dados em flowables ReportLab."""
    tipo = bloco.get("tipo", "texto")
    out  = []

    if tipo == "titulo":
        out.append(Paragraph(bloco["texto"], S_TITULO))
        out.append(_sp(2))

    elif tipo == "secao":
        out.append(_sp(3))
        out.append(SectionHeader(bloco.get("numero", ""), bloco["texto"]))
        out.append(_sp(3))

    elif tipo == "subsecao":
        out.append(_sp(2))
        # faixa azul escuro fina
        faixa = Table([[Paragraph(bloco["texto"].upper(), S_SUBSEC)]],
                      colWidths=[CW])
        faixa.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
            ("TOPPADDING",    (0, 0), (-1, -1), 2.5 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("LINEBELOW",     (0, 0), (-1, -1), 1.5, ORANGE),
        ]))
        out.append(faixa)
        out.append(_sp(2))

    elif tipo == "tabela":
        cab  = bloco.get("cabecalho", [])
        rows = bloco.get("linhas", [])
        if not cab and not rows:
            return out
        ncols = max(len(cab), max((len(r) for r in rows), default=0))
        if ncols == 0:
            return out
        col_w = CW / ncols
        col_widths = [col_w] * ncols

        def pad_row(r):
            return r + [""] * (ncols - len(r))

        table_rows = []
        if cab:
            table_rows.append([Paragraph(str(c), S_TH) for c in pad_row(cab)])
        for r in rows:
            table_rows.append([Paragraph(str(c), S_TD) for c in pad_row(r)])

        t = Table(table_rows, colWidths=col_widths, repeatRows=1 if cab else 0)
        style_cmds = [
            ("BACKGROUND",    (0, 0), (-1, 0 if cab else -1), NAVY),
            ("BACKGROUND",    (0, 1), (-1, -1), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_BG]),
            ("GRID",          (0, 0), (-1, -1), 0.3, GRAY_LINE),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3 * mm),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2 * mm),
            ("TOPPADDING",    (0, 0), (-1, -1), 2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
        ]
        if not cab:
            style_cmds[0] = ("BACKGROUND", (0, 0), (-1, -1), WHITE)
        t.setStyle(TableStyle(style_cmds))
        out.append(t)
        out.append(_sp(3))

    elif tipo == "bullets":
        for item in bloco.get("itens", []):
            out.append(Paragraph(f"<bullet>&bull;</bullet> {item}", S_BULLET))
        out.append(_sp(2))

    elif tipo == "keyvalues":
        for kv in bloco.get("itens", []):
            chave = kv.get("chave", "")
            valor = kv.get("valor", "")
            out.append(Paragraph(f"<b>{chave}:</b> {valor}", S_KV_VAL))
        out.append(_sp(2))

    elif tipo == "texto":
        for ln in bloco.get("linhas", []):
            if ln.strip():
                out.append(Paragraph(ln, S_BODY))
        out.append(_sp(2))

    return out


def gerar(dados: dict, output_path: str):
    d       = dados
    cliente = d.get("cliente", "Cliente")
    periodo = d.get("periodo", "")
    agencia = d.get("agencia", "MarkSeg Trafego")
    blocos  = d.get("blocos", [])

    doc = SimpleDocTemplate(
        output_path,
        pagesize=(W, H),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )

    story = [PageBreak()]   # reserva pág 1 para a capa

    # cabeçalho da primeira página de conteúdo
    story.append(PageHeader(cliente, f"Planejamento Estrategico · {periodo}", ""))
    story.append(_sp(4))

    if not blocos:
        story.append(Paragraph("Nenhum conteudo fornecido.", S_BODY))
    else:
        for bloco in blocos:
            elements = _render_bloco(bloco)
            story.extend(elements)

    def on_first(canvas, doc):
        draw_cover(canvas, doc,
                   titulo_doc="Planejamento", subtitulo_doc="Estrategico",
                   cliente=cliente, agencia=agencia, periodo=periodo,
                   info_extra=d.get("info_capa", ""),
                   frase_resumo=d.get("frase_resumo", ""),
                   frase_destaque=d.get("frase_destaque", ""))

    def on_later(canvas, doc):
        # rodapé sem total de páginas (documento de tamanho variável)
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN, 3 * mm, f"MarkSeg x {cliente.upper()}")
        canvas.drawCentredString(W / 2, 3 * mm, "MARKSEG · AGENCIA DE TRAFEGO")
        from brand.design_system import ORANGE
        canvas.setFillColor(ORANGE)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawRightString(W - MARGIN, 3 * mm, f"PAG. {doc.page:02d}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return output_path
