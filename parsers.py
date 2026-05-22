"""
Parsers de arquivos → dados estruturados para os templates.
Lê CSVs do Meta Ads, Google Ads, planilhas e texto livre.
"""

import re
import math
import pandas as pd


# ── Utilitários ────────────────────────────────────────────────────────────

def num(val, default=0.0):
    """
    Converte valor para float.
    Suporta formato BR (1.234,56), US (1,234.56), NaN, '--', '—' etc.
    """
    try:
        if val is None:
            return default
        if isinstance(val, float):
            return default if (math.isnan(val) or math.isinf(val)) else val
        if isinstance(val, int):
            return float(val)

        s = str(val).strip()
        # textos que significam "sem valor"
        if s.lower() in ("nan", "none", "", "-", "--", "---", " --",
                         "n/a", "—", "–", " —", " –"):
            return default

        # remove moeda e espaços
        s = re.sub(r"[R$\s%]", "", s)
        if not s or s in ("-", "--", "—", "–"):
            return default

        dot_pos   = s.rfind(".")
        comma_pos = s.rfind(",")

        if comma_pos > dot_pos:       # BR: "1.234,56"
            s = s.replace(".", "").replace(",", ".")
        elif dot_pos > comma_pos:     # US: "1,234.56"
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")   # só vírgula

        result = float(s)
        return default if (math.isnan(result) or math.isinf(result)) else result
    except Exception:
        return default


def inteiro(val, default=0):
    """Converte valor para int, tolerando NaN, '--', vírgulas e pontos."""
    try:
        if val is None:
            return default
        if isinstance(val, float):
            return default if (math.isnan(val) or math.isinf(val)) else int(val)
        if isinstance(val, int):
            return val
        s = str(val).strip()
        if s.lower() in ("nan", "none", "", "-", "--", " --", "n/a", "—", "–"):
            return default
        return int(num(s, default))
    except Exception:
        return default


def detectar_tipo_csv(df: pd.DataFrame) -> str:
    """
    Detecta o tipo de relatório com base nas colunas do DataFrame.
    Suporta exports do Meta Ads BR e Google Ads BR.
    """
    cols = [str(c).lower() for c in df.columns]
    cols_set = set(cols)

    # ── Meta Ads ──────────────────────────────────────────────────────────
    # Identifica pelo campo mais específico (de mais específico para menos)
    if any("nome do anúncio" in c or "ad name" in c for c in cols):
        return "meta_anuncios"
    if any("nome do conjunto" in c or "ad set name" in c for c in cols):
        return "meta_conjuntos"
    if any("nome da campanha" in c or "campaign name" in c for c in cols):
        return "meta_campanhas"

    # ── Google Ads ────────────────────────────────────────────────────────
    if any("termo de pesquisa" in c or "search term" in c for c in cols):
        return "google_termos"
    if any("palavra-chave" in c or "keyword" in c for c in cols):
        return "google_keywords"
    # Google campanhas/anúncios — identifica por "campanha" + "cliques"
    tem_cliques = any(c in ("cliques", "clicks", "impr.") for c in cols)
    tem_camp    = any("campanha" in c or "campaign" in c for c in cols)
    if tem_camp and tem_cliques:
        return "google_campanhas"
    if tem_cliques:
        return "google_campanhas"

    return "desconhecido"


def col(df, *opcoes):
    """
    Retorna coluna que contém uma das opções (busca parcial, case-insensitive).
    Prefere correspondência exata; se não, prefere a coluna com nome mais curto
    (evita 'Indicador de resultados' ao buscar 'resultados').
    """
    for op in opcoes:
        op_l = op.lower()
        matches = [c for c in df.columns if op_l in c.lower()]
        if matches:
            exact = [c for c in matches if c.lower() == op_l]
            if exact:
                return exact[0]
            return min(matches, key=len)   # mais curto = mais específico
    return None


def _is_lead_action(indicador_val) -> bool:
    """Retorna True se o 'Indicador de resultados' é uma conversão real (lead)."""
    if not indicador_val or str(indicador_val).strip().lower() in ("nan", "", "—", "–"):
        return False
    s = str(indicador_val).lower()
    # Meta usa "actions:offsite_conversion.*" para leads reais
    # "omni_landing_page_view", "reach", "post_engagement" NÃO são leads
    if "conversion" in s or "lead" in s:
        if "landing_page_view" not in s:
            return True
    return False


def _is_total_row(row_dict: dict) -> bool:
    """Detecta linha de totais ('Total: Campanhas', 'Total: Conta' etc.)."""
    for v in row_dict.values():
        s = str(v).strip()
        if s.lower().startswith("total:") or s.lower().startswith("total "):
            return True
    return False


# ── Parsers Meta Ads ───────────────────────────────────────────────────────

def parse_meta_campanhas(df: pd.DataFrame) -> list:
    resultado = []
    nome_col    = col(df, "nome da campanha", "campaign name")
    gasto_col   = col(df, "valor usado", "amount spent")
    result_col  = col(df, "resultados", "results")
    indic_col   = col(df, "indicador de resultados", "result indicator")
    impr_col    = col(df, "impressões", "impressions", "impressoes")
    alcance_col = col(df, "alcance", "reach")
    cpl_col     = col(df, "custo por resultados", "custo por resultado",
                       "custo por lead", "cost per result", "cost per lead")
    velc_col    = col(df, "veiculação da campanha", "veiculação", "delivery")

    for _, row in df.iterrows():
        row_d = row.to_dict()
        if _is_total_row(row_d):
            continue
        nome = str(row.get(nome_col, "")) if nome_col else ""
        if not nome or nome.lower() in ("nan", "", "total"):
            continue

        gasto  = num(row.get(gasto_col, 0))  if gasto_col  else 0
        impr   = inteiro(row.get(impr_col, 0)) if impr_col   else 0
        alcance= inteiro(row.get(alcance_col,0)) if alcance_col else 0
        status_raw = str(row.get(velc_col, "")) if velc_col else ""
        ativo  = ("active" in status_raw.lower() or "ativ" in status_raw.lower())

        # Distingue leads reais de visualizações de página
        indic  = str(row.get(indic_col, "")) if indic_col else ""
        res_val= inteiro(row.get(result_col, 0)) if result_col else 0
        is_lead= _is_lead_action(indic)
        leads  = res_val if is_lead else 0
        page_views = res_val if not is_lead else 0

        cpl_val= num(row.get(cpl_col, 0)) if cpl_col else 0
        if leads > 0 and cpl_val == 0 and gasto > 0:
            cpl_val = round(gasto / leads, 2)

        resultado.append({
            "nome": nome, "gasto": gasto, "impressoes": impr,
            "alcance": alcance, "cpl": cpl_val, "leads": leads,
            "page_views": page_views, "ativo": ativo,
        })
    return resultado


def parse_meta_conjuntos(df: pd.DataFrame) -> list:
    resultado = []
    nome_col  = col(df, "nome do conjunto de anúncios", "nome do conjunto", "ad set name")
    gasto_col = col(df, "valor usado", "amount spent")
    result_col= col(df, "resultados", "results")
    indic_col = col(df, "indicador de resultados", "result indicator")
    cpl_col   = col(df, "custo por resultados", "custo por resultado",
                      "custo por lead", "cost per result", "cost per lead")
    orc_col   = col(df, "orçamento do conjunto", "orçamento", "budget")
    alc_col   = col(df, "alcance", "reach")
    stat_col  = col(df, "veiculação do conjunto", "veiculação", "delivery")

    for _, row in df.iterrows():
        row_d = row.to_dict()
        if _is_total_row(row_d):
            continue
        nome = str(row.get(nome_col, "")) if nome_col else ""
        if not nome or nome.lower() in ("nan", "", "total"):
            continue

        status_raw = str(row.get(stat_col, "")) if stat_col else ""
        status = "Ativo" if ("active" in status_raw.lower() or
                              "ativ" in status_raw.lower()) else "Inativo"

        indic   = str(row.get(indic_col, "")) if indic_col else ""
        res_val = inteiro(row.get(result_col, 0)) if result_col else 0
        is_lead = _is_lead_action(indic)
        leads   = res_val if is_lead else 0

        gasto   = num(row.get(gasto_col, 0)) if gasto_col else 0
        cpl_val = num(row.get(cpl_col, 0))   if cpl_col  else 0
        if leads > 0 and cpl_val == 0 and gasto > 0:
            cpl_val = round(gasto / leads, 2)

        resultado.append({
            "nome":      nome,
            "status":    status,
            "orcamento": num(row.get(orc_col, 0)) if orc_col else 0,
            "gasto":     gasto,
            "leads":     leads,
            "cpl":       cpl_val,
            "alcance":   inteiro(row.get(alc_col, 0)) if alc_col else 0,
        })
    return resultado


def parse_meta_anuncios(df: pd.DataFrame) -> list:
    resultado = []
    nome_col  = col(df, "nome do anúncio", "ad name")
    gasto_col = col(df, "valor usado", "amount spent")
    result_col= col(df, "resultados", "results")
    indic_col = col(df, "indicador de resultados", "result indicator")
    cpl_col   = col(df, "custo por resultados", "custo por resultado",
                      "custo por lead", "cost per result", "cost per lead")
    hook_col  = col(df, "hook rate")
    stat_col  = col(df, "veiculação de anúncio", "veiculação", "delivery")
    impr_col  = col(df, "impressões", "impressions", "impressoes")
    alc_col   = col(df, "alcance", "reach")

    for _, row in df.iterrows():
        row_d = row.to_dict()
        if _is_total_row(row_d):
            continue
        nome = str(row.get(nome_col, "")) if nome_col else ""
        if not nome or nome.lower() in ("nan", "", "total"):
            continue

        gasto  = num(row.get(gasto_col, 0)) if gasto_col else 0
        impr   = inteiro(row.get(impr_col, 0)) if impr_col else 0
        alcance= inteiro(row.get(alc_col, 0))  if alc_col  else 0

        indic   = str(row.get(indic_col, "")) if indic_col else ""
        res_val = inteiro(row.get(result_col, 0)) if result_col else 0
        is_lead = _is_lead_action(indic)
        leads   = res_val if is_lead else 0
        page_views = res_val if not is_lead else 0

        cpl_v  = num(row.get(cpl_col, 0)) if cpl_col else 0
        if leads > 0 and cpl_v == 0 and gasto > 0:
            cpl_v = round(gasto / leads, 2)

        hook   = f"{num(row.get(hook_col,0))*100:.1f}%" if hook_col else "—"
        status_raw = str(row.get(stat_col, "")) if stat_col else ""
        status = "Ativo" if ("active" in status_raw.lower() or
                              "ativ" in status_raw.lower()) else "Inativo"
        resultado.append({
            "nome":       nome,
            "status":     status,
            "gasto":      gasto,
            "leads":      leads,
            "page_views": page_views,
            "impressoes": impr,
            "alcance":    alcance,
            "cpl":        cpl_v,
            "hook":       hook,
            "avaliacao":  "",
            "destaque":   False,
        })

    # marca vencedor: melhor CPL com pelo menos 1 lead
    # se nenhum tem lead, marca o que tem mais page_views com menor gasto/pv
    validos = [c for c in resultado if c["leads"] >= 1 and c["gasto"] > 0]
    if not validos:
        validos = [c for c in resultado if c["page_views"] > 0 and c["gasto"] > 0]
        if validos:
            vencedor = min(validos, key=lambda x: x["gasto"] / max(x["page_views"], 1))
            vencedor["avaliacao"] = "DESTAQUE"
            vencedor["destaque"]  = True
    else:
        vencedor = min(validos, key=lambda x: x["cpl"])
        vencedor["avaliacao"] = "VENCEDOR"
        vencedor["destaque"]  = True

    return resultado


# ── Parsers Google Ads ─────────────────────────────────────────────────────

def parse_google_campanhas(df: pd.DataFrame) -> dict:
    """
    Agrega métricas de qualquer relatório Google Ads (campanhas, palavras-chave,
    termos de pesquisa, anúncios). Pula linhas de totais e linhas sem dados.
    """
    gasto_col = col(df, "custo", "cost")
    cliq_col  = col(df, "cliques", "clicks")
    impr_col  = col(df, "impr.", "impressões", "impressoes", "impressions")
    ctr_col   = col(df, "ctr")
    conv_col  = col(df, "conversões", "conversoes", "conversions")
    cpl_col   = col(df, "custo / conv.", "custo / conv", "cost / conv",
                      "cpc méd.", "cpc médio", "avg. cpc")

    totais = {"gasto": 0.0, "cliques": 0, "impressoes": 0,
              "ctr_vals": [], "conv": 0.0, "cpl_vals": [],
              "campanhas": []}

    for _, row in df.iterrows():
        row_d = row.to_dict()
        if _is_total_row(row_d):
            continue

        gasto = num(row.get(gasto_col, 0)) if gasto_col else 0
        cliq  = inteiro(row.get(cliq_col, 0)) if cliq_col else 0
        impr  = inteiro(row.get(impr_col, 0)) if impr_col else 0
        conv  = num(row.get(conv_col, 0))     if conv_col else 0

        # só conta linhas com algum dado
        if gasto == 0 and cliq == 0 and impr == 0:
            continue

        totais["gasto"]      += gasto
        totais["cliques"]    += cliq
        totais["impressoes"] += impr
        totais["conv"]       += conv

        if ctr_col:
            ctr_v = num(row.get(ctr_col, 0))
            if ctr_v > 0:
                totais["ctr_vals"].append(ctr_v)
        if cpl_col:
            cpl_v = num(row.get(cpl_col, 0))
            if cpl_v > 0:
                totais["cpl_vals"].append(cpl_v)

        # nomes de campanha para análise
        camp_col = col(df, "campanha", "campaign")
        if camp_col:
            nome_c = str(row.get(camp_col, ""))
            if nome_c and nome_c.lower() not in ("nan", ""):
                totais["campanhas"].append({
                    "nome": nome_c, "gasto": gasto,
                    "cliques": cliq, "conv": conv,
                })

    # CTR médio ponderado
    if totais["impressoes"] > 0 and totais["cliques"] > 0:
        ctr_calc = totais["cliques"] / totais["impressoes"] * 100
        totais["ctr"] = f"{ctr_calc:.2f}%"
    elif totais["ctr_vals"]:
        totais["ctr"] = f"{sum(totais['ctr_vals'])/len(totais['ctr_vals']):.2f}%"
    else:
        totais["ctr"] = "0%"

    # CPL calculado
    conv_f = float(totais["conv"])
    if conv_f > 0:
        totais["cpl"] = round(totais["gasto"] / conv_f, 2)
    elif totais["cpl_vals"]:
        totais["cpl"] = round(sum(totais["cpl_vals"]) / len(totais["cpl_vals"]), 2)
    else:
        totais["cpl"] = 0

    totais["conv"] = int(round(conv_f))
    return totais


# ── Extrai dados do texto livre ────────────────────────────────────────────

def extrair_do_texto(texto: str) -> dict:
    """Extrai valores numéricos e strings relevantes do texto livre."""
    d = {}
    # CPL
    m = re.search(r"cpl[^R\d]*R?\$?\s*([\d,\.]+)", texto, re.I)
    if m: d["cpl_mencionado"] = num(m.group(1))
    # frase resumo / destaque
    for pat in [r"frase(?:\s+de)?\s+resumo[:\s]+([^\n\.]+)", r"resumo[:\s]+([^\n\.]+)"]:
        m = re.search(pat, texto, re.I)
        if m: d["frase_resumo"] = m.group(1).strip(); break
    for pat in [r"frase(?:\s+de)?\s+destaque[:\s]+([^\n\.]+)", r"destaque[:\s]+([^\n\.]+)"]:
        m = re.search(pat, texto, re.I)
        if m: d["frase_destaque"] = m.group(1).strip(); break
    # todas as linhas não-vazias (não só bullets)
    todas = [l.strip().lstrip("-•·▪*").strip()
             for l in texto.split("\n") if l.strip() and len(l.strip()) > 2]
    if todas:
        d["todas_linhas"] = todas
    # linhas bullet (subconjunto para compatibilidade com outros templates)
    linhas = [l.strip().lstrip("-•·▪*").strip()
              for l in texto.split("\n")
              if l.strip() and l.strip()[0] in ("-","•","·","*","▪") and len(l.strip()) > 3]
    d["linhas_livres"] = linhas or todas
    return d


# ── Parser completo: texto → blocos estruturados ──────────────────────────

def parse_texto_completo(texto: str) -> list:
    """
    Converte texto livre numa lista de blocos para renderização no template.
    Tipos de bloco: titulo | secao | subsecao | tabela | bullets | keyvalues | texto
    Garante que NENHUMA linha do texto original se perde.
    """
    if not texto or not texto.strip():
        return []

    blocos = []
    linhas = texto.split("\n")
    n = len(linhas)
    i = 0
    primeiro_bloco = True

    def lx(j):
        return linhas[j].strip() if j < n else ""

    def tem_sep(j):
        l = linhas[j] if j < n else ""
        return "\t" in l or l.count("|") >= 2

    while i < n:
        ln = linhas[i]
        limpa = ln.strip()

        if not limpa:
            i += 1
            continue

        # ── Tabela: linha ATUAL tem separadores (tab ou 2+ pipes) ──────
        if tem_sep(i):
            rows_raw = []
            while i < n and lx(i):
                l = linhas[i]
                ll = l.strip()
                if "\t" in l:
                    row = [c.strip() for c in l.split("\t")]
                elif ll.count("|") >= 2:
                    row = [c.strip() for c in ll.strip("|").split("|")]
                else:
                    break
                if not all(re.match(r"^[-:=]+$", c) for c in row if c):
                    rows_raw.append(row)
                i += 1
            if rows_raw:
                ncols = max(len(r) for r in rows_raw)
                rows_norm = [r + [""] * (ncols - len(r)) for r in rows_raw]
                blocos.append({
                    "tipo": "tabela",
                    "cabecalho": rows_norm[0] if rows_norm else [],
                    "linhas":    rows_norm[1:],
                })
            else:
                i += 1  # garante progresso se nada foi parseado
            continue

        # ── Seção numerada: "1. TITULO" ──────────────────────────────────
        m = re.match(r"^(\d+)\.\s+(.+)$", limpa)
        if m:
            blocos.append({"tipo": "secao", "numero": m.group(1),
                           "texto": m.group(2).strip()})
            primeiro_bloco = False
            i += 1
            continue

        # ── Sub-seção: linha curta toda maiúscula ─────────────────────────
        is_upper = (limpa == limpa.upper() and
                    bool(re.search(r"[A-ZÁÉÍÓÚÃÕÂÊÔÇÀ]{3,}", limpa)) and
                    len(limpa) < 90 and
                    limpa[0] not in "-•*[✅⚠📅🔧→")
        if is_upper and not m:
            blocos.append({"tipo": "subsecao", "texto": limpa})
            primeiro_bloco = False
            i += 1
            continue

        # ── Sub-seção: curta, termina em ":" ─────────────────────────────
        if (limpa.endswith(":") and len(limpa) < 80 and
                limpa[0] not in "-•*✅⚠"):
            blocos.append({"tipo": "subsecao", "texto": limpa.rstrip(":")})
            primeiro_bloco = False
            i += 1
            continue

        # ── Título: primeira linha curta sem marcação especial ─────────────
        if primeiro_bloco and len(limpa) < 100 and limpa[0] not in "-•*✅⚠📅🔧→[":
            blocos.append({"tipo": "titulo", "texto": limpa})
            primeiro_bloco = False
            i += 1
            continue

        # ── Bloco de bullets ─────────────────────────────────────────────
        BULLET_CHARS = set("-•*✅⚠📅🔧→[")
        if limpa[0] in BULLET_CHARS:
            itens = []
            while i < n and lx(i):
                ll = lx(i)
                if ll and ll[0] in BULLET_CHARS:
                    itens.append(ll.lstrip("-•*→✅⚠📅🔧").strip().strip("[]"))
                    i += 1
                else:
                    break
            if itens:
                blocos.append({"tipo": "bullets", "itens": itens})
            continue

        # ── Bloco de key: value (2+ consecutivas) ────────────────────────
        KV_RE = re.compile(r"^([^:\n]{1,60}):\s+(.+)$")
        j, kv_count = i, 0
        while j < n and lx(j):
            if KV_RE.match(lx(j)):
                kv_count += 1
                j += 1
            else:
                break
        if kv_count >= 2:
            kvs = []
            while i < n and lx(i):
                m2 = KV_RE.match(lx(i))
                if m2:
                    kvs.append({"chave": m2.group(1).strip(),
                                "valor": m2.group(2).strip()})
                    i += 1
                else:
                    break
            if kvs:
                blocos.append({"tipo": "keyvalues", "itens": kvs})
            continue

        # ── Parágrafo de texto livre ──────────────────────────────────────
        txt_linhas = []
        while i < n and lx(i):
            ll  = lx(i)
            raw = linhas[i]
            # para se linha seguinte é de outro tipo
            if (re.match(r"^(\d+)\.\s+", ll) or
                    tem_sep(i) or
                    (ll and ll[0] in BULLET_CHARS) or
                    (ll == ll.upper() and bool(re.search(r"[A-Z]{3,}", ll))
                     and len(ll) < 90 and ll[0] not in "-•*[") or
                    (ll.endswith(":") and len(ll) < 80 and ll[0] not in "-•*")):
                break
            txt_linhas.append(ll)
            i += 1
        if txt_linhas:
            blocos.append({"tipo": "texto", "linhas": txt_linhas})
            primeiro_bloco = False
        else:
            i += 1  # garante progresso — evita loop infinito
        continue

    return blocos


# ── Segmentação simples (mantida para compatibilidade) ─────────────────────

def segmentar_texto(texto: str) -> dict:
    """Fallback simples — agrupa linhas por seção detectada."""
    secoes: dict = {}
    secao_atual = "geral"
    for linha in texto.split("\n"):
        limpa = linha.strip()
        if not limpa:
            continue
        conteudo = limpa.lstrip("-•·▪*#").strip()
        if conteudo:
            secoes.setdefault(secao_atual, []).append(conteudo)
    return secoes


# ── Montador principal ─────────────────────────────────────────────────────

def montar_dados(tipo, cliente, periodo, responsavel,
                 dfs: dict, textos: list, texto_livre: str) -> dict:

    dados = {
        "cliente":     cliente or "Cliente",
        "periodo":     periodo or "",
        "agencia":     "MarkSeg Tráfego · Rafael",
        "responsavel": responsavel or "Rafael",
        "info_capa":   f"Análise de performance · {periodo}",
        "frase_resumo":    "",
        "frase_destaque":  "",
    }

    # texto livre
    extras = extrair_do_texto(texto_livre) if texto_livre else {}
    dados["frase_resumo"]   = extras.get("frase_resumo", "")
    dados["frase_destaque"] = extras.get("frase_destaque", "")
    linhas_livres = extras.get("linhas_livres", [])

    # classifica e parseia cada DataFrame
    meta_camp_raw  = []
    meta_conj_raw  = []
    meta_anun_raw  = []
    google_raw     = {}

    for nome_arq, df in dfs.items():
        tipo_csv = detectar_tipo_csv(df)
        if tipo_csv == "meta_campanhas":
            meta_camp_raw.extend(parse_meta_campanhas(df))
        elif tipo_csv == "meta_conjuntos":
            meta_conj_raw.extend(parse_meta_conjuntos(df))
        elif tipo_csv == "meta_anuncios":
            meta_anun_raw.extend(parse_meta_anuncios(df))
        elif tipo_csv in ("google_campanhas", "google_keywords", "google_termos"):
            # agrega — usa o que já tem mais dados (mais gasto/cliques)
            novo = parse_google_campanhas(df)
            if novo.get("gasto", 0) > google_raw.get("gasto", 0):
                google_raw = novo
            elif novo.get("cliques", 0) > google_raw.get("cliques", 0):
                google_raw = novo

    # ── Relatório de Performance ──────────────────────────────────────────
    if tipo == "relatorio_performance":

        ETAPA_MAP = {
            "topo": "TOPO",  "top": "TOPO",   "tráfego": "MEIO",
            "trafego": "MEIO", "meio": "MEIO", "mid": "MEIO",
            "fundo": "FUNDO", "bottom": "FUNDO", "conv": "FUNDO",
            "lead": "FUNDO",  "form": "FUNDO",  "quiz": "FUNDO",
        }
        campanhas_template = []
        for c in meta_camp_raw:
            etapa = "FUNDO"
            for k, v in ETAPA_MAP.items():
                if k in c["nome"].lower():
                    etapa = v
                    break
            if c["leads"] > 0:
                result_str = f"{c['leads']} leads"
                cpr_val    = c["cpl"]
            elif c.get("page_views", 0) > 0:
                result_str = f"{c['page_views']:,} vis."
                cpr_val    = round(c["gasto"] / c["page_views"], 4) if c["page_views"] else 0
            else:
                result_str = f"{c['impressoes']:,} impr."
                cpr_val    = 0
            campanhas_template.append({
                "etapa": etapa, "nome": c["nome"],
                "verba": c["gasto"], "resultado": result_str,
                "cpr":   cpr_val,   "impressoes": c["impressoes"],
            })

        meta_total = sum(c["gasto"] for c in meta_camp_raw)
        meta_leads = sum(c["leads"] for c in meta_camp_raw)
        meta_cpl   = round(meta_total / meta_leads, 2) if meta_leads else 0

        # ── Insights automáticos ──────────────────────────────────────────
        insights_meta = list(linhas_livres[:3])  # prioriza texto do usuário

        # top criativo
        vencedor = next((c for c in meta_anun_raw if c.get("destaque")), None)
        if vencedor and not insights_meta:
            insights_meta.append(
                f"Criativo '{vencedor['nome']}' {"vencedor" if vencedor.get('leads',0) > 0 else "destaque"}"
                f" · R$ {vencedor['gasto']:.2f} gastos · "
                f"{vencedor['leads']} leads" if vencedor.get('leads', 0) > 0
                else f" · {vencedor.get('page_views', 0):,} visitas"
            )
        # conjunto com melhor CPL
        conj_com_lead = [c for c in meta_conj_raw if c.get("leads", 0) > 0]
        if conj_com_lead:
            melhor_conj = min(conj_com_lead, key=lambda x: x["cpl"])
            insights_meta.append(
                f"Conjunto '{melhor_conj['nome'][:40]}' · CPL R$ {melhor_conj['cpl']:.2f} "
                f"· {melhor_conj['leads']} leads"
            )
        # alerta se sem leads
        if meta_leads == 0 and meta_total > 0:
            total_pv = sum(c.get("page_views", 0) for c in meta_camp_raw)
            insights_meta.append(
                f"Semana de topo de funil: {total_pv:,} visitas geradas · "
                f"R$ {meta_total:.2f} investidos · nenhuma conversão direta"
            )

        # insights Google
        g = google_raw
        insights_google = []
        if g.get("cliques", 0) > 0:
            insights_google.append(
                f"R$ {g['gasto']:.2f} investidos · {g['cliques']} cliques · "
                f"CTR {g['ctr']}"
            )
        if g.get("conv", 0) > 0:
            insights_google.append(
                f"{g['conv']} conversões geradas · CPL médio R$ {g['cpl']:.2f}"
            )
        # campanha com mais gasto
        camps_g = g.get("campanhas", [])
        if camps_g:
            top_camp = max(camps_g, key=lambda x: x["gasto"])
            if top_camp["gasto"] > 0:
                insights_google.append(
                    f"Campanha principal: '{top_camp['nome'][:45]}' · "
                    f"R$ {top_camp['gasto']:.2f} · {top_camp['cliques']} cliques"
                )

        dados.update({
            "meta_campanhas": campanhas_template,
            "meta_total":     meta_total,
            "meta_leads":     meta_leads,
            "meta_cpl":       meta_cpl,
            "criativos":      meta_anun_raw,
            "conjuntos":      meta_conj_raw,
            "google_gasto":      g.get("gasto", 0),
            "google_cliques":    g.get("cliques", 0),
            "google_impressoes": g.get("impressoes", 0),
            "google_ctr":        g.get("ctr", "0%"),
            "google_conv":       g.get("conv", 0),
            "google_cpl":        g.get("cpl", 0),
            "insights_criativos": insights_meta,
            "insights_google":    insights_google,
            "sugestoes_conteudo": [],
            "estrategia_seguidores": [],
            "proximos_passos": [],
        })

        # frase automática na capa
        if not dados["frase_resumo"]:
            total_inv = meta_total + g.get("gasto", 0)
            total_leads = meta_leads + g.get("conv", 0)
            if total_leads > 0:
                cpl_geral = round(total_inv / total_leads, 2) if total_leads else 0
                dados["frase_resumo"]   = f"{total_leads} leads gerados · CPL médio R$ {cpl_geral:.2f}"
                dados["frase_destaque"] = f"Total investido R$ {total_inv:.2f} · Meta + Google"
            elif meta_total > 0:
                total_pv = sum(c.get("page_views", 0) for c in meta_camp_raw)
                dados["frase_resumo"]   = f"R$ {total_inv:.2f} investidos · {total_pv:,} visitas geradas"
                dados["frase_destaque"] = f"Fase de aprendizado · conversões em construção"

    # ── Relatório Social ──────────────────────────────────────────────────
    elif tipo == "relatorio_social":
        dados.update({
            "seguidores_atual": 0, "seguidores_novos": 0,
            "alcance_total": 0, "impressoes_total": 0,
            "engajamento_medio": "—", "saves_total": 0,
            "posts": [], "reels": [],
            "insights_semana": linhas_livres,
            "recomendacoes": [],
            "pauta_proxima": [],
        })

    # ── Plano de Mídia ────────────────────────────────────────────────────
    elif tipo == "plano_de_midia":
        dados.update({
            "investimento": 0, "leads_estimados": "—",
            "cpl_estimado_min": 0, "cpl_estimado_max": 0,
            "canais": [], "produtos": [],
            "cronograma": [], "infraestrutura": linhas_livres,
            "precisa_cliente": [], "palavras_chave": [],
        })

    # ── Resultado Mensal ──────────────────────────────────────────────────
    elif tipo == "apresentacao_resultado":
        meta_total = sum(c["gasto"] for c in meta_camp_raw)
        meta_leads = sum(c["leads"] for c in meta_camp_raw)
        meta_cpl   = round(meta_total / meta_leads, 2) if meta_leads else 0
        g_gasto    = google_raw.get("gasto", 0)
        g_leads    = google_raw.get("conv", 0)
        total_inv  = meta_total + g_gasto
        total_leads= meta_leads + g_leads
        cpl_geral  = round(total_inv / total_leads, 2) if total_leads else 0

        canais = []
        if meta_total > 0:
            canais.append({"canal": "Meta Ads", "gasto": meta_total,
                           "leads": meta_leads, "cpl": meta_cpl,
                           "taxa_qual": "—", "avaliacao": "OK"})
        if g_gasto > 0:
            canais.append({"canal": "Google Ads", "gasto": g_gasto,
                           "leads": g_leads, "cpl": google_raw.get("cpl",0),
                           "taxa_qual": "—", "avaliacao": "OK"})
        dados.update({
            "investimento_total": total_inv,
            "leads_total": total_leads, "cpl_medio": cpl_geral,
            "taxa_qualificacao": "—", "roas": "—", "cac": 0,
            "metas": [], "canais": canais, "evolucao": [],
            "aprendizados": linhas_livres,
            "plano_proximo_mes": [],
            "frase_resumo":   f"R$ {total_inv:.2f} investidos · {total_leads} leads gerados.",
            "frase_destaque": f"CPL médio R$ {cpl_geral:.2f} · resultado do mês.",
        })

    # ── Ficha de Implantação ──────────────────────────────────────────────
    elif tipo == "ficha_implantacao":
        # tenta extrair responsáveis do texto livre (padrão "Cargo: Nome")
        responsaveis = []
        for linha in linhas_livres:
            if ":" in linha:
                partes = linha.split(":", 1)
                responsaveis.append({"cargo": partes[0].strip(), "nome": partes[1].strip()})
        dados.update({
            "responsaveis":        responsaveis,
            "postagens_mensais":   "",
            "formato_prioritario": "",
            "linguagem":           "",
            "layout_cores":        "",
            "descricao_empresa":   "",
            "posicionamento":      "",
            "diferenciais":        [],
            "publico_perfis":      "",
            "publico_meta":        "",
            "publico_estrategia":  "",
            "leads_canais":        "",
            "leads_estrategia":    "",
            "comunicacao":         [],
            "processos":           [],
            "obj_curto_prazo":     "",
            "obj_medio_prazo":     "",
            "obj_trafego":         "",
        })

    # ── Planejamento Estratégico ──────────────────────────────────────────
    elif tipo == "planejamento_estrategico":
        # converte TODO o texto colado em blocos para renderização
        blocos = parse_texto_completo(texto_livre) if texto_livre else []

        # também inclui texto extraído de PDFs/TXTs enviados como arquivo
        for txt in textos:
            blocos_arq = parse_texto_completo(txt)
            if blocos_arq:
                blocos.append({"tipo": "subsecao", "texto": "ARQUIVO ANEXADO"})
                blocos.extend(blocos_arq)

        dados.update({
            "horizonte":      periodo or "",
            "blocos":         blocos,
            "frase_resumo":   extras.get("frase_resumo", ""),
            "frase_destaque": extras.get("frase_destaque", ""),
            "info_capa":      f"Planejamento estrategico · {periodo}" if periodo else "",
        })

    # ── Proposta Comercial ────────────────────────────────────────────────
    elif tipo == "proposta_comercial":
        dados.update({
            "data_proposta": periodo or "",
            "validade": "30 dias",
            "verba_midia": 0, "honorarios": 0, "total_mensal": 0,
            "diagnostico": linhas_livres,
            "servicos": [], "resultados_esperados": [],
            "diferenciais": [
                "Gestão especializada em tráfego para segurança eletrônica",
                "Google Ads + Meta Ads com estratégia de funil completo",
                "Relatórios semanais com análise de criativos e CPL",
                "Sem mensalidade oculta · transparência total nos resultados",
            ],
            "proximos_passos": [],
        })

    return dados
