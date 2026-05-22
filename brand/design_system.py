"""
MarkSeg Design System — base de todos os documentos da agência.
Importar este módulo em qualquer template para garantir consistência visual.
"""

import os
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Flowable, Table, TableStyle, Paragraph, Spacer
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Circle, Wedge, Group, Polygon
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Dimensões ──────────────────────────────────────────────────────────────
W, H = A4
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

# ── Registro de fontes Unicode (suporte a acentos) ─────────────────────────
_FONTS_REG = [
    # Linux / Streamlit Cloud (Ubuntu)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    # macOS
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    # Windows
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]
_FONTS_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
]

def _find_system_fonts():
    """Varre diretórios comuns de fontes e retorna pares (regular, bold)."""
    import glob
    dirs = [
        "/usr/share/fonts/truetype",
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        "/System/Library/Fonts",
        "/Library/Fonts",
        "C:/Windows/Fonts",
    ]
    reg_candidates, bold_candidates = [], []
    for d in dirs:
        for ttf in glob.glob(os.path.join(d, "**", "*.ttf"), recursive=True):
            low = ttf.lower()
            base = os.path.basename(low)
            # rejeita narrow, italic, oblique, condensed, black
            if any(x in low for x in ("italic", "oblique", "narrow", "condensed")):
                continue
            if "bold" in low or "bd." in low or "-b." in low or "heavy" in low:
                bold_candidates.append(ttf)
            else:
                reg_candidates.append(ttf)
    return reg_candidates, bold_candidates


def _try_register(name, paths):
    for p in paths:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(name, p))
                return True
            except Exception:
                continue
    return False


def _register_unicode_fonts():
    """Registra fontes Unicode com suporte a PT/BR. Fallback para busca ampla."""
    # 1) tenta paths conhecidos primeiro
    ok_reg  = _try_register("MKS",      _FONTS_REG)
    ok_bold = _try_register("MKS-Bold", _FONTS_BOLD)
    if ok_reg and ok_bold:
        return True

    # 2) busca ampla no sistema
    reg_list, bold_list = _find_system_fonts()
    if not ok_reg:
        ok_reg  = _try_register("MKS",      reg_list)
    if not ok_bold:
        ok_bold = _try_register("MKS-Bold", bold_list if bold_list else reg_list)

    return ok_reg  # aceitamos mesmo sem bold (reportlab usará regular como fallback)


_has_unicode = _register_unicode_fonts()

FONT_REG  = "MKS"      if _has_unicode else "Helvetica"
FONT_BOLD = "MKS-Bold" if _has_unicode else "Helvetica-Bold"

# ── Paleta MarkSeg ─────────────────────────────────────────────────────────
NAVY        = colors.HexColor("#1B3A6B")   # azul escuro principal
BLUE        = colors.HexColor("#2980B9")   # azul médio
ORANGE      = colors.HexColor("#F5821E")   # laranja MarkSeg
ORANGE_DARK = colors.HexColor("#D4691A")   # laranja escuro (hover/destaque)
GRAY_BG     = colors.HexColor("#F5F6FA")   # fundo de cards
GRAY_LINE   = colors.HexColor("#E0E3EE")   # bordas/divisores
GRAY_DARK   = colors.HexColor("#444444")   # texto secundário
GRAY_LIGHT  = colors.HexColor("#888888")   # texto terciário
WHITE       = colors.white
GREEN       = colors.HexColor("#27AE60")
RED         = colors.HexColor("#E74C3C")
YELLOW      = colors.HexColor("#F39C12")

# ── Tipografia ─────────────────────────────────────────────────────────────
def style(name, font=None, size=10, color=None, align=TA_LEFT,
          leading=None, before=0, after=0, bold=False):
    if color is None:
        color = NAVY
    if font is None:
        font = FONT_BOLD if bold else FONT_REG
    elif font == "Helvetica":
        font = FONT_BOLD if bold else FONT_REG
    elif bold and not font.endswith("-Bold"):
        font = FONT_BOLD
    return ParagraphStyle(
        name=name, fontName=font, fontSize=size, textColor=color,
        alignment=align, leading=leading or round(size * 1.35),
        spaceBefore=before, spaceAfter=after
    )

# Estilos prontos
S = {
    "h1":        style("h1",       size=24, bold=True),
    "h2":        style("h2",       size=18, bold=True),
    "h3":        style("h3",       size=13, bold=True),
    "section":   style("section",  size=10, bold=True, color=WHITE),
    "label":     style("label",    size=7,  color=GRAY_LIGHT),
    "value_lg":  style("val_lg",   size=18, bold=True),
    "value_md":  style("val_md",   size=14, bold=True),
    "body":      style("body",     size=9,  color=GRAY_DARK, leading=14),
    "body_bold": style("body_b",   size=9,  bold=True),
    "th":        style("th",       size=8,  bold=True, color=WHITE),
    "td":        style("td",       size=8,  color=GRAY_DARK),
    "td_r":      style("td_r",     size=8,  color=GRAY_DARK, align=TA_RIGHT),
    "td_bold":   style("td_bold",  size=8,  bold=True),
    "td_green":  style("td_gr",    size=8,  bold=True, color=GREEN),
    "td_red":    style("td_rd",    size=8,  bold=True, color=RED),
    "td_orange": style("td_or",    size=8,  bold=True, color=ORANGE),
    "caption":   style("caption",  size=7,  color=GRAY_LIGHT, align=TA_CENTER),
    "insight":   style("insight",  size=9,  color=WHITE, leading=14),
    "footer":    style("footer",   size=7,  color=GRAY_LIGHT, align=TA_CENTER),
    "tag":       style("tag",      size=7,  bold=True, color=WHITE, align=TA_CENTER),
}

# ── Largura de conteúdo padrão ─────────────────────────────────────────────
MARGIN = 20 * mm
CW = W - 2 * MARGIN        # content width em pontos
CW_MM = CW / mm            # em mm

# ── Flowables ──────────────────────────────────────────────────────────────

class PageHeader(Flowable):
    """Cabeçalho interno de página — fundo branco com logo."""
    def __init__(self, cliente, subtitulo, pagina):
        super().__init__()
        self.cliente   = cliente
        self.subtitulo = subtitulo
        self.pagina    = pagina
        self.width     = CW
        self.height    = 16 * mm

    def draw(self):
        c = self.canv
        # fundo branco
        c.setFillColor(WHITE)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        # logo à esquerda
        logo_w = 32 * mm
        if os.path.exists(LOGO_PATH):
            try:
                c.drawImage(LOGO_PATH, 0, 1 * mm,
                            width=logo_w, height=13 * mm,
                            preserveAspectRatio=True, mask="auto")
            except Exception:
                c.setFillColor(NAVY)
                c.setFont(FONT_BOLD, 9)
                c.drawString(0, 5 * mm, "MarkSeg")
                logo_w = 22 * mm
        else:
            c.setFillColor(NAVY)
            c.setFont(FONT_BOLD, 9)
            c.drawString(0, 5 * mm, "MarkSeg")
            logo_w = 22 * mm
        # linha divisória vertical laranja
        c.setStrokeColor(ORANGE)
        c.setLineWidth(1.5)
        c.line(logo_w + 3 * mm, 2 * mm, logo_w + 3 * mm, self.height - 2 * mm)
        # cliente + subtítulo à direita da linha
        tx = logo_w + 6 * mm
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 9)
        c.drawString(tx, 8.5 * mm, self.cliente.upper())
        c.setFillColor(ORANGE)
        c.setFont(FONT_REG, 7)
        c.drawString(tx, 3 * mm, self.subtitulo.upper())
        # número de página à direita
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 8)
        c.drawRightString(self.width, 6 * mm, self.pagina)
        # linha laranja na base
        c.setStrokeColor(ORANGE)
        c.setLineWidth(1)
        c.line(0, 0, self.width, 0)


class SectionHeader(Flowable):
    """Cabeçalho de seção numerado com fundo laranja."""
    def __init__(self, numero, titulo, width=None):
        super().__init__()
        self.numero = str(numero)
        self.titulo = titulo
        self.width  = width or CW
        self.height = 9 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(ORANGE)
        c.roundRect(0, 0, self.width, self.height, 2 * mm, fill=1, stroke=0)
        r = 3.5 * mm
        c.setFillColor(NAVY)
        c.circle(r + 3 * mm, self.height / 2, r, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawCentredString(r + 3 * mm, self.height / 2 - 3, self.numero)
        c.setFont(FONT_BOLD, 10)
        c.drawString(r * 2 + 6 * mm, self.height / 2 - 3.5, self.titulo.upper())


class MetricCard(Flowable):
    """Card de KPI individual."""
    def __init__(self, label, value, sub="", width=40*mm, cor_borda=ORANGE):
        super().__init__()
        self.label     = label
        self.value     = value
        self.sub       = sub
        self.width     = width
        self.cor_borda = cor_borda
        self.height    = 18 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(GRAY_BG)
        c.roundRect(0, 0, self.width, self.height, 1.5 * mm, fill=1, stroke=0)
        c.setStrokeColor(self.cor_borda)
        c.setLineWidth(1.5)
        c.line(0, 0, 0, self.height)
        c.setFillColor(GRAY_LIGHT)
        c.setFont(FONT_REG, 7)
        c.drawString(3 * mm, self.height - 5 * mm, self.label.upper())
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 15)
        c.drawString(3 * mm, self.height - 12 * mm, str(self.value))
        c.setFillColor(GRAY_LIGHT)
        c.setFont(FONT_REG, 7)
        c.drawString(3 * mm, 2 * mm, self.sub)


class InsightBox(Flowable):
    """Caixa de destaque com fundo escuro e tópicos."""
    def __init__(self, titulo, linhas, width=None, cor=NAVY):
        super().__init__()
        self.titulo = titulo
        self.linhas = linhas
        self.width  = width or CW
        self.cor    = cor
        self.height = (len(linhas) * 5.5 + 13) * mm

    def draw(self):
        c = self.canv
        c.setFillColor(self.cor)
        c.roundRect(0, 0, self.width, self.height, 2 * mm, fill=1, stroke=0)
        c.setFillColor(ORANGE)
        c.setFont(FONT_BOLD, 8)
        c.drawString(4 * mm, self.height - 7 * mm, self.titulo.upper())
        c.setFillColor(WHITE)
        c.setFont(FONT_REG, 8)
        y = self.height - 12.5 * mm
        for linha in self.linhas:
            c.drawString(4 * mm, y, str(linha))
            y -= 5.5 * mm


class TagBadge(Flowable):
    """Etiqueta colorida para etapas de funil."""
    PRESETS = {
        "TOPO":    NAVY,
        "MEIO":    BLUE,
        "FUNDO":   ORANGE,
        "GOOGLE":  colors.HexColor("#34A853"),
        "META":    colors.HexColor("#1877F2"),
        "OK":      GREEN,
        "ALERTA":  YELLOW,
        "CRITICO": RED,
    }

    def __init__(self, texto, cor=None, largura=18*mm):
        super().__init__()
        self.texto   = texto
        self.cor     = cor or self.PRESETS.get(texto.upper(), NAVY)
        self.width   = largura
        self.height  = 5 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(self.cor)
        c.roundRect(0, 0.5 * mm, self.width, 4 * mm, 1 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 7)
        c.drawCentredString(self.width / 2, 1.8 * mm, self.texto.upper())


# ── Helpers de tabela ──────────────────────────────────────────────────────

def table_style_default(header_rows=1, alternate=True):
    cmds = [
        ("BACKGROUND",   (0, 0), (-1, header_rows - 1), NAVY),
        ("GRID",         (0, 0), (-1, -1), 0.3, GRAY_LINE),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING",   (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2.5 * mm),
    ]
    if alternate:
        cmds.append(("ROWBACKGROUNDS", (0, header_rows), (-1, -1),
                     [GRAY_BG, WHITE]))
    return TableStyle(cmds)


def table_total_row(row_index):
    return TableStyle([
        ("BACKGROUND",  (0, row_index), (-1, row_index), NAVY),
        ("TEXTCOLOR",   (0, row_index), (-1, row_index), WHITE),
        ("FONTNAME",    (0, row_index), (-1, row_index), "Helvetica-Bold"),
        ("FONTSIZE",    (0, row_index), (-1, row_index), 8),
    ])


def make_cards_row(cards_data, n_cols=None):
    """
    cards_data: lista de dicts {label, value, sub, cor_borda}
    Retorna Table de MetricCards lado a lado.
    """
    n = n_cols or len(cards_data)
    card_w = (CW - (n - 1) * 3 * mm) / n
    row = [MetricCard(d["label"], d["value"], d.get("sub", ""),
                      card_w, d.get("cor", ORANGE))
           for d in cards_data]
    t = Table([row], colWidths=[card_w + 3 * mm] * n)
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    return t


# ── Gráficos ───────────────────────────────────────────────────────────────

def chart_barras_horizontais(dados, largura_mm, altura_mm,
                              formato="R$ {:,.2f}", titulo=None):
    """
    dados: lista de (rótulo, valor, cor)
    """
    d = Drawing(largura_mm * mm, altura_mm * mm)
    d.add(Rect(0, 0, largura_mm * mm, altura_mm * mm,
               fillColor=GRAY_BG, strokeColor=None))
    th = 0
    if titulo:
        th = 7 * mm
        d.add(String(4 * mm, altura_mm * mm - 5 * mm, titulo.upper(),
                     fontName="Helvetica-Bold", fontSize=8, fillColor=ORANGE))
    n = len(dados) or 1
    area_h   = altura_mm * mm - th - 4 * mm
    bar_tot  = area_h / n
    bar_h    = bar_tot * 0.55
    label_w  = 55 * mm
    val_w    = 24 * mm
    bar_max  = largura_mm * mm - label_w - val_w - 4 * mm
    max_v    = (max(x[1] for x in dados) * 1.15) if dados else 1
    max_v    = max_v if max_v > 0 else 1
    for i, (rot, val, cor) in enumerate(dados):
        y = altura_mm * mm - th - (i + 1) * bar_tot + (bar_tot - bar_h) / 2
        d.add(String(4 * mm, y + bar_h / 2 - 3, rot,
                     fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
        d.add(Rect(label_w, y, bar_max, bar_h,
                   fillColor=colors.HexColor("#E8EAF2"), strokeColor=None))
        w = max(2, bar_max * (val / max_v))
        d.add(Rect(label_w, y, w, bar_h, fillColor=cor, strokeColor=None))
        d.add(String(label_w + bar_max + 3, y + bar_h / 2 - 3,
                     formato.format(val),
                     fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
    return d


def chart_donut(dados, largura_mm, altura_mm, titulo=None):
    """
    dados: lista de (rótulo, valor, cor)
    """
    d = Drawing(largura_mm * mm, altura_mm * mm)
    d.add(Rect(0, 0, largura_mm * mm, altura_mm * mm,
               fillColor=GRAY_BG, strokeColor=None))
    if titulo:
        d.add(String(4 * mm, altura_mm * mm - 5 * mm, titulo.upper(),
                     fontName="Helvetica-Bold", fontSize=8, fillColor=ORANGE))
    total = sum(x[1] for x in dados) or 1
    cy  = altura_mm * mm / 2 - 2 * mm
    cx  = (altura_mm - 14) * mm / 2 + 4 * mm
    r_o = (altura_mm - 14) * mm / 2
    r_i = r_o * 0.6
    start = 90
    for rot, val, cor in dados:
        sweep = -(val / total) * 360
        # Wedge com ângulo 0 ou ±360 causa ZeroDivisionError no ReportLab
        if abs(sweep) < 0.5 or abs(abs(sweep) - 360) < 0.5:
            start += sweep
            continue
        d.add(Wedge(cx, cy, r_o, start + sweep, start,
                    fillColor=cor, strokeColor=WHITE, strokeWidth=1.5))
        start += sweep
    d.add(Circle(cx, cy, r_i, fillColor=GRAY_BG, strokeColor=None))
    d.add(String(cx, cy + 2, "TOTAL",
                 fontName="Helvetica", fontSize=6, fillColor=GRAY_LIGHT,
                 textAnchor="middle"))
    d.add(String(cx, cy - 6, f"R$ {total:,.0f}".replace(",", "."),
                 fontName="Helvetica-Bold", fontSize=10, fillColor=NAVY,
                 textAnchor="middle"))
    lx = cx + r_o + 8 * mm
    ly = altura_mm * mm - 14 * mm
    for rot, val, cor in dados:
        pct = val / total * 100
        d.add(Rect(lx, ly, 3 * mm, 3 * mm, fillColor=cor, strokeColor=None))
        d.add(String(lx + 5 * mm, ly + 0.5, rot,
                     fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
        d.add(String(lx + 5 * mm, ly - 4,
                     f"R$ {val:,.2f} ({pct:.0f}%)".replace(",", "."),
                     fontName="Helvetica", fontSize=7, fillColor=GRAY_DARK))
        ly -= 10 * mm
    return d


def chart_barras_verticais_duplas(dados, largura_mm, altura_mm,
                                   label1="Leads", label2="CPL",
                                   cor1=ORANGE, cor2=GREEN, titulo=None):
    """
    dados: lista de (rótulo, val1, val2_formatado_str)
    """
    d = Drawing(largura_mm * mm, altura_mm * mm)
    d.add(Rect(0, 0, largura_mm * mm, altura_mm * mm,
               fillColor=GRAY_BG, strokeColor=None))
    if titulo:
        d.add(String(4 * mm, altura_mm * mm - 5 * mm, titulo.upper(),
                     fontName="Helvetica-Bold", fontSize=8, fillColor=ORANGE))
    n = len(dados)
    bottom = 14 * mm
    top    = altura_mm * mm - 10 * mm
    ch     = top - bottom
    grp_w  = (largura_mm * mm - 8 * mm) / n
    bw     = grp_w * 0.3
    max1   = (max(x[1] for x in dados) * 1.2) if dados else 1
    max1   = max1 if max1 > 0 else 1
    for i, item in enumerate(dados):
        rot = item[0]
        v1  = item[1]
        v2s = item[2] if len(item) > 2 else ""
        cx  = 4 * mm + grp_w * (i + 0.5)
        h1  = ch * (v1 / max1)
        x1  = cx - bw - 1 * mm
        d.add(Rect(x1, bottom, bw, h1, fillColor=cor1, strokeColor=None))
        d.add(String(x1 + bw / 2, bottom + h1 + 2, str(v1),
                     fontName="Helvetica-Bold", fontSize=8,
                     fillColor=NAVY, textAnchor="middle"))
        if v2s:
            d.add(Rect(cx + 1 * mm, bottom, bw, h1 * 0.6,
                       fillColor=cor2, strokeColor=None))
            d.add(String(cx + 1 * mm + bw / 2, bottom + h1 * 0.6 + 2, v2s,
                         fontName="Helvetica-Bold", fontSize=8,
                         fillColor=NAVY, textAnchor="middle"))
        d.add(String(cx, bottom - 5, rot,
                     fontName="Helvetica-Bold", fontSize=8,
                     fillColor=NAVY, textAnchor="middle"))
    # legenda
    lx = largura_mm * mm - 55 * mm
    ly = altura_mm * mm - 6 * mm
    d.add(Rect(lx, ly, 3 * mm, 3 * mm, fillColor=cor1, strokeColor=None))
    d.add(String(lx + 5 * mm, ly + 0.5, label1,
                 fontName="Helvetica", fontSize=7, fillColor=NAVY))
    d.add(Rect(lx + 28 * mm, ly, 3 * mm, 3 * mm, fillColor=cor2, strokeColor=None))
    d.add(String(lx + 33 * mm, ly + 0.5, label2,
                 fontName="Helvetica", fontSize=7, fillColor=NAVY))
    return d


# ── Rodapé de página ───────────────────────────────────────────────────────

def draw_footer(canvas, doc, cliente, total_pags):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_REG, 7)
    canvas.drawString(MARGIN, 3 * mm, f"MarkSeg x {cliente.upper()}")
    canvas.drawCentredString(W / 2, 3 * mm, "MARKSEG · AGENCIA DE TRAFEGO")
    canvas.setFillColor(ORANGE)
    canvas.setFont(FONT_BOLD, 7)
    canvas.drawRightString(W - MARGIN, 3 * mm,
                           f"PAG. {doc.page:02d} / {total_pags:02d}")
    canvas.restoreState()


# ── Capa padrão ────────────────────────────────────────────────────────────

def draw_cover(canvas, doc, titulo_doc, subtitulo_doc,
               cliente, agencia, periodo, info_extra="",
               frase_resumo="", frase_destaque=""):
    """Renderiza a capa completa no canvas."""
    canvas.saveState()

    # faixa topo navy (só a metade direita)
    canvas.setFillColor(NAVY)
    canvas.rect(W / 2, H - 28 * mm, W / 2, 28 * mm, fill=1, stroke=0)

    # área branca esquerda com logo
    canvas.setFillColor(WHITE)
    canvas.rect(0, H - 28 * mm, W / 2, 28 * mm, fill=1, stroke=0)

    # logo na área branca
    if os.path.exists(LOGO_PATH):
        try:
            canvas.drawImage(LOGO_PATH, MARGIN, H - 24 * mm,
                             width=50 * mm, height=18 * mm,
                             preserveAspectRatio=True, mask="auto")
        except Exception:
            canvas.setFillColor(NAVY)
            canvas.setFont(FONT_BOLD, 14)
            canvas.drawString(MARGIN, H - 14 * mm, "MarkSeg")
    else:
        canvas.setFillColor(NAVY)
        canvas.setFont(FONT_BOLD, 14)
        canvas.drawString(MARGIN, H - 14 * mm, "MarkSeg")
        canvas.setFillColor(ORANGE)
        canvas.setFont(FONT_BOLD, 9)
        canvas.drawString(MARGIN, H - 21 * mm, "Agencia de Trafego")

    # tag direita (laranja) sobre fundo navy
    canvas.setFillColor(ORANGE)
    canvas.rect(W - 55 * mm, H - 28 * mm, 55 * mm, 28 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_BOLD, 8)
    canvas.drawCentredString(W - 27 * mm, H - 10 * mm, titulo_doc.upper())
    canvas.setFont(FONT_REG, 7)
    canvas.drawCentredString(W - 27 * mm, H - 16 * mm, agencia)
    canvas.drawCentredString(W - 27 * mm, H - 21 * mm, periodo)

    # linha separadora embaixo do header
    canvas.setFillColor(GRAY_LINE)
    canvas.rect(0, H - 29 * mm, W, 1, fill=1, stroke=0)

    # barra laranja vertical
    canvas.setFillColor(ORANGE)
    canvas.rect(MARGIN, H - 85 * mm, 1.5 * mm, 45 * mm, fill=1, stroke=0)

    # título principal
    canvas.setFillColor(NAVY)
    canvas.setFont(FONT_BOLD, 28)
    canvas.drawString(MARGIN + 6 * mm, H - 55 * mm, titulo_doc)
    canvas.setFillColor(ORANGE)
    canvas.setFont(FONT_BOLD, 28)
    canvas.drawString(MARGIN + 6 * mm, H - 69 * mm, subtitulo_doc)
    canvas.setFillColor(NAVY)
    canvas.setFont(FONT_BOLD, 18)
    canvas.drawString(MARGIN + 6 * mm, H - 82 * mm, cliente + ".")

    # subtítulo descritivo
    canvas.setFillColor(GRAY_DARK)
    canvas.setFont(FONT_REG, 9)
    canvas.drawString(MARGIN + 6 * mm, H - 92 * mm, info_extra)

    # cards de info
    info = [("CLIENTE", cliente), ("AGENCIA", agencia), ("PERIODO", periodo)]
    bw = (W - 2 * MARGIN) / len(info)
    y0 = H - 132 * mm
    for i, (lbl, val) in enumerate(info):
        x0 = MARGIN + i * bw
        canvas.setFillColor(GRAY_BG)
        canvas.roundRect(x0, y0, bw - 3 * mm, 22 * mm, 2 * mm,
                          fill=1, stroke=0)
        canvas.setFillColor(ORANGE)
        canvas.setFont(FONT_BOLD, 7)
        canvas.drawString(x0 + 3 * mm, y0 + 14 * mm, lbl)
        canvas.setFillColor(NAVY)
        canvas.setFont(FONT_BOLD, 9)
        canvas.drawString(x0 + 3 * mm, y0 + 7 * mm, val)

    # caixa de resumo
    if frase_resumo or frase_destaque:
        canvas.setFillColor(NAVY)
        canvas.roundRect(MARGIN, H - 178 * mm, W - 2 * MARGIN, 30 * mm,
                          2 * mm, fill=1, stroke=0)
        canvas.setFillColor(ORANGE)
        canvas.setFont(FONT_BOLD, 7)
        canvas.drawString(MARGIN + 5 * mm, H - 153 * mm,
                           "RESUMO EXECUTIVO · EM UMA FRASE")
        canvas.setFillColor(WHITE)
        canvas.setFont(FONT_BOLD, 13)
        canvas.drawString(MARGIN + 5 * mm, H - 163 * mm, frase_resumo)
        canvas.setFillColor(ORANGE)
        canvas.setFont(FONT_BOLD, 13)
        canvas.drawString(MARGIN + 5 * mm, H - 174 * mm, frase_destaque)

    # rodapé
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_REG, 7)
    canvas.drawString(MARGIN, 3 * mm, f"MarkSeg x {cliente.upper()}")
    canvas.setFillColor(ORANGE)
    canvas.setFont(FONT_BOLD, 7)
    canvas.drawRightString(W - MARGIN, 3 * mm, "PAG. 01")

    canvas.restoreState()


# ── Renderizador de blocos de texto livre (usado por todos os templates) ───

_S_BLK_TITULO  = style("blk_titulo",  size=13, bold=True,  color=NAVY)
_S_BLK_SUBSEC  = style("blk_subsec",  size=10, bold=True,  color=NAVY)
_S_BLK_BODY    = style("blk_body",    size=9,  color=GRAY_DARK, leading=14)
_S_BLK_BULLET  = style("blk_bullet",  size=9,  color=GRAY_DARK, leading=14)
_S_BLK_KV_VAL  = style("blk_kv_val",  size=9,  color=GRAY_DARK, leading=13)
_S_BLK_TH      = style("blk_th",      size=8,  bold=True,  color=WHITE)
_S_BLK_TD      = style("blk_td",      size=8,  color=GRAY_DARK, leading=12)


def render_blocos(blocos: list, cw: float = None) -> list:
    """
    Converte lista de blocos (saida de parse_texto_completo) em flowables ReportLab.
    Parametro cw: largura disponivel em pontos (padrao: CW).
    Retorna lista de flowables pronta para adicionar ao story.
    """
    if cw is None:
        cw = CW
    out = []

    for bloco in blocos:
        tipo = bloco.get("tipo", "texto")

        if tipo == "titulo":
            out.append(Spacer(1, 3 * mm))
            out.append(Paragraph(bloco.get("texto", ""), _S_BLK_TITULO))
            out.append(Spacer(1, 2 * mm))

        elif tipo == "secao":
            out.append(Spacer(1, 3 * mm))
            num  = bloco.get("numero", "")
            txt  = bloco.get("texto", "")
            faixa = Table(
                [[Paragraph(f"{num}. {txt}" if num else txt, _S_BLK_SUBSEC)]],
                colWidths=[cw],
            )
            faixa.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING",    (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]))
            out.append(faixa)
            out.append(Spacer(1, 2 * mm))

        elif tipo == "subsecao":
            out.append(Spacer(1, 2 * mm))
            faixa = Table(
                [[Paragraph(bloco.get("texto", "").upper(), _S_BLK_SUBSEC)]],
                colWidths=[cw],
            )
            faixa.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), GRAY_BG),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING",    (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("LINEBELOW",     (0, 0), (-1, -1), 1.5, ORANGE),
            ]))
            out.append(faixa)
            out.append(Spacer(1, 2 * mm))

        elif tipo == "tabela":
            cab  = bloco.get("cabecalho", [])
            rows = bloco.get("linhas", [])
            if not cab and not rows:
                continue
            ncols = max(len(cab), max((len(r) for r in rows), default=0))
            if ncols == 0:
                continue
            col_w  = cw / ncols
            col_ws = [col_w] * ncols

            def pad(r, n=ncols):
                return r + [""] * (n - len(r))

            trows = []
            if cab:
                trows.append([Paragraph(str(c), _S_BLK_TH) for c in pad(cab)])
            for r in rows:
                trows.append([Paragraph(str(c), _S_BLK_TD) for c in pad(r)])

            t = Table(trows, colWidths=col_ws, repeatRows=1 if cab else 0)
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, GRAY_BG]),
                ("GRID",          (0, 0), (-1, -1), 0.3, GRAY_LINE),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",   (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 2 * mm),
                ("TOPPADDING",    (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ]))
            out.append(t)
            out.append(Spacer(1, 3 * mm))

        elif tipo == "bullets":
            for item in bloco.get("itens", []):
                out.append(Paragraph(f"<bullet>&bull;</bullet> {item}",
                                     _S_BLK_BULLET))
            out.append(Spacer(1, 2 * mm))

        elif tipo == "keyvalues":
            for kv in bloco.get("itens", []):
                chave = kv.get("chave", "")
                valor = kv.get("valor", "")
                out.append(Paragraph(f"<b>{chave}:</b> {valor}", _S_BLK_KV_VAL))
            out.append(Spacer(1, 2 * mm))

        elif tipo == "texto":
            for ln in bloco.get("linhas", []):
                if ln.strip():
                    out.append(Paragraph(ln, _S_BLK_BODY))
            out.append(Spacer(1, 2 * mm))

    return out
