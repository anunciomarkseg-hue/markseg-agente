"""
Template: Ficha de Implantação
Duas páginas com header laranja recorrente + bullet círculo por seção.
"""

from reportlab.platypus import (
    SimpleDocTemplate, Spacer, Table, TableStyle,
    Paragraph, PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Circle
from reportlab.lib.units import mm
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brand.design_system import (
    W, H, CW, MARGIN,
    NAVY, ORANGE, GRAY_LINE, GRAY_DARK, WHITE,
    LOGO_PATH, S, style,
    draw_footer,
)
from reportlab.lib import colors

# ── estilos específicos da ficha ───────────────────────────────────────────
S_FICHA_TITLE = style("ficha_title",  size=13, bold=True, color=ORANGE)
S_FICHA_LABEL = style("ficha_label",  size=10, bold=True, color=NAVY)
S_FICHA_BODY  = style("ficha_body",   size=10, color=GRAY_DARK, leading=15)
S_FICHA_ITEM  = style("ficha_item",   size=10, color=GRAY_DARK, leading=14)

HEADER_H  = 38 * mm   # altura do banner laranja
EMPRESA_H = 12 * mm   # altura da barra cinza


# ── helpers visuais ────────────────────────────────────────────────────────

def _bullet_circle():
    """Círculo laranja preenchido usado como bullet de seção."""
    d = Drawing(7 * mm, 7 * mm)
    d.add(Circle(3.5 * mm, 3.5 * mm, 3.5 * mm, fillColor=ORANGE, strokeColor=None))
    return d


def section_title(titulo: str):
    """Linha com círculo laranja + título em laranja bold."""
    t = Table(
        [[_bullet_circle(), Paragraph(titulo, S_FICHA_TITLE)]],
        colWidths=[9 * mm, CW - 9 * mm],
    )
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 1 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
    ]))
    return t


def bullet_item(texto: str):
    return Paragraph(f"• {texto}", S_FICHA_ITEM)


def label_value(label: str, value: str):
    return Paragraph(f"<b>{label}</b> {value}", S_FICHA_BODY)


# ── callback de página: header laranja + barra empresa ─────────────────────

def _draw_page_header(canvas, cliente):
    canvas.saveState()

    # banner laranja
    canvas.setFillColor(ORANGE)
    canvas.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)

    # texto "FICHA DE IMPLANTAÇÃO"
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 22)
    canvas.drawString(MARGIN, H - 17 * mm, "FICHA DE")
    canvas.drawString(MARGIN, H - 31 * mm, "IMPLANTACAO")

    # logo sobre o banner laranja (lado direito)
    if os.path.exists(LOGO_PATH):
        try:
            canvas.drawImage(
                LOGO_PATH,
                W - MARGIN - 45 * mm, H - 34 * mm,
                width=45 * mm, height=28 * mm,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass
    else:
        # fallback texto
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawRightString(W - MARGIN, H - 20 * mm, "MarkSeg")

    # barra cinza com nome da empresa
    canvas.setFillColor(colors.HexColor("#E8E8E8"))
    canvas.rect(0, H - HEADER_H - EMPRESA_H, W, EMPRESA_H, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(W / 2, H - HEADER_H - EMPRESA_H + 4 * mm,
                             f"Empresa:  {cliente.upper()}")

    canvas.restoreState()


# ── gerador principal ──────────────────────────────────────────────────────

def gerar(dados: dict, output_path: str):
    d = dados
    cliente = d.get("cliente", "Cliente")
    agencia = d.get("agencia", "MarkSeg Trafego")
    total_pags = 2

    # topMargin precisa limpar o banner (38mm) + barra empresa (12mm) + respiro
    doc = SimpleDocTemplate(
        output_path,
        pagesize=(W, H),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=HEADER_H + EMPRESA_H + 8 * mm,
        bottomMargin=15 * mm,
    )

    sp = lambda n=4: Spacer(1, n * mm)

    story = []

    # ── Página 1 ──────────────────────────────────────────────────────────

    # RESPONSÁVEIS INTERNOS
    responsaveis = d.get("responsaveis", [])
    if responsaveis:
        story.append(section_title("RESPONSAVEIS INTERNOS:"))
        story.append(sp(2))
        for r in responsaveis:
            cargo = r.get("cargo", "")
            nome  = r.get("nome", "")
            story.append(bullet_item(f"{cargo}: {nome}" if cargo else nome))
        story.append(sp(5))

    # ORIENTAÇÕES PARA CONTEÚDO
    story.append(KeepTogether([
        section_title("ORIENTACOES PARA CONTEUDO"),
        sp(2),
        label_value("Postagens mensais:", d.get("postagens_mensais", "")),
        label_value("Formato prioritario:", d.get("formato_prioritario", "")),
        label_value("Linguagem:", d.get("linguagem", "")),
        label_value("Layout:", d.get("layout_cores", "")),
        sp(5),
    ]))

    # SOBRE A EMPRESA
    sobre = []
    sobre.append(section_title("SOBRE A EMPRESA:"))
    sobre.append(sp(2))
    if d.get("descricao_empresa"):
        sobre.append(Paragraph(f"<b>{d['descricao_empresa']}</b>", S_FICHA_BODY))
        sobre.append(sp(2))
    if d.get("posicionamento"):
        sobre.append(Paragraph(
            f"<b>Posicionamento:</b> {d['posicionamento']}", S_FICHA_BODY))
        sobre.append(sp(2))
    diferenciais = d.get("diferenciais", [])
    if diferenciais:
        sobre.append(Paragraph("<b>Diferenciais:</b>", S_FICHA_LABEL))
        for dif in diferenciais:
            sobre.append(Paragraph(f"- {dif}", S_FICHA_ITEM))
    sobre.append(sp(5))
    story.extend(sobre)

    # PÚBLICO-ALVO E METAS
    publico = []
    publico.append(section_title("PUBLICO-ALVO E METAS:"))
    publico.append(sp(2))
    if d.get("publico_perfis"):
        publico.append(bullet_item(f"Perfis: {d['publico_perfis']}"))
    if d.get("publico_meta"):
        publico.append(bullet_item(f"Meta: {d['publico_meta']}"))
    if d.get("publico_estrategia"):
        publico.append(bullet_item(f"Estrategia: {d['publico_estrategia']}"))
    publico.append(sp(3))
    story.extend(publico)

    story.append(PageBreak())

    # ── Página 2 ──────────────────────────────────────────────────────────

    # GERAÇÃO DE LEADS
    story.append(section_title("GERACAO DE LEADS:"))
    story.append(sp(2))
    if d.get("leads_canais"):
        story.append(bullet_item(f"Canais: {d['leads_canais']}"))
    if d.get("leads_estrategia"):
        story.append(bullet_item(f"Estrategia: {d['leads_estrategia']}"))
    story.append(sp(5))

    # ESTRATÉGIA DE COMUNICAÇÃO
    comunicacao = d.get("comunicacao", [])
    story.append(section_title("ESTRATEGIA DE COMUNICACAO:"))
    story.append(sp(2))
    for item in comunicacao:
        story.append(bullet_item(item))
    story.append(sp(5))

    # PROCESSOS OPERACIONAIS
    processos = d.get("processos", [])
    story.append(section_title("PROCESSOS OPERACIONAIS:"))
    story.append(sp(2))
    for item in processos:
        story.append(Paragraph(f"<b>{item}</b>", S_FICHA_BODY))
    story.append(sp(5))

    # OBJETIVOS DE MARKETING
    story.append(section_title("OBJETIVOS DE MARKETING:"))
    story.append(sp(2))
    if d.get("obj_curto_prazo"):
        story.append(label_value("Curto prazo:", d["obj_curto_prazo"]))
    if d.get("obj_medio_prazo"):
        story.append(label_value("Medio prazo:", d["obj_medio_prazo"]))
    if d.get("obj_trafego"):
        story.append(label_value("Trafego:", d["obj_trafego"]))

    # callbacks de página
    def on_page(canvas, doc):
        _draw_page_header(canvas, cliente)
        # rodapé minimalista
        canvas.saveState()
        canvas.setFillColor(ORANGE)
        canvas.rect(0, 0, W, 8 * mm, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawCentredString(W / 2, 2.5 * mm, "MARKSEG · AGENCIA DE TRAFEGO")
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(W - MARGIN, 2.5 * mm,
                               f"PAG. {doc.page:02d} / {total_pags:02d}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output_path
