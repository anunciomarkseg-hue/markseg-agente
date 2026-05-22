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

def parse_google_keywords_top(df: pd.DataFrame, top_n: int = 5) -> list:
    """Retorna top N palavras-chave/termos por gasto, com cliques e conversões."""
    kw_col    = col(df, "palavra-chave", "termo de pesquisa", "keyword", "search term")
    gasto_col = col(df, "custo", "cost")
    cliq_col  = col(df, "cliques", "clicks")
    conv_col  = col(df, "conversões", "conversoes", "conversions")
    camp_col  = col(df, "campanha", "campaign")

    if not kw_col or not gasto_col:
        return []

    rows = []
    for _, row in df.iterrows():
        if _is_total_row(row.to_dict()):
            continue
        kw    = str(row.get(kw_col, "")).strip().strip('"')
        gasto = num(row.get(gasto_col, 0))
        cliq  = inteiro(row.get(cliq_col, 0))
        conv  = inteiro(row.get(conv_col, 0))
        if not kw or kw.lower() in ("nan", "", " --", "--") or gasto == 0:
            continue
        camp = str(row.get(camp_col, "")) if camp_col else ""
        rows.append({"kw": kw[:55], "gasto": gasto, "cliques": cliq,
                     "conv": conv, "campanha": camp[:35]})

    # ordena por gasto desc, pega top N
    rows.sort(key=lambda x: x["gasto"], reverse=True)
    return rows[:top_n]


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


# ── Análise inteligente automática (sem API, baseada em regras de negócio) ──

def _analisar_performance(meta_camp, meta_conj, meta_anun,
                          google, periodo: str, cliente: str) -> dict:
    """
    Lê os dados parseados e gera:
    - resumo_executivo: 2-3 frases sobre o período
    - insights_meta: lista de observações Meta
    - insights_google: lista de observações Google
    - proximos_passos: lista de ações recomendadas
    - frase_resumo / frase_destaque: para a capa
    """
    meta_gasto  = sum(c["gasto"] for c in meta_camp)
    meta_leads  = sum(c["leads"] for c in meta_camp)
    meta_pv     = sum(c.get("page_views", 0) for c in meta_camp)
    meta_impr   = sum(c.get("impressoes", 0) for c in meta_camp)
    meta_cpl    = round(meta_gasto / meta_leads, 2) if meta_leads else 0

    g_gasto  = google.get("gasto", 0)
    g_cliq   = google.get("cliques", 0)
    g_impr   = google.get("impressoes", 0)
    g_conv   = google.get("conv", 0)
    g_cpl    = google.get("cpl", 0)
    g_ctr    = google.get("ctr", "0%")

    total_inv   = meta_gasto + g_gasto
    total_leads = meta_leads + g_conv

    # ── Fase da campanha ────────────────────────────────────────────────────
    camp_ativas = [c for c in meta_camp if c.get("ativo", True)]
    if total_leads == 0 and total_inv > 0:
        fase = "aprendizado"
    elif total_leads > 0 and meta_cpl > 80:
        fase = "otimização"
    else:
        fase = "escala"

    # ── Insights Meta ───────────────────────────────────────────────────────
    ins_meta = []

    if meta_leads > 0:
        ins_meta.append(
            f"{meta_leads} lead{'s' if meta_leads > 1 else ''} captado{'s' if meta_leads > 1 else ''} "
            f"via Meta · CPL médio R$ {meta_cpl:.2f}"
        )
    elif meta_pv > 0:
        cpc_pv = round(meta_gasto / meta_pv, 2) if meta_pv else 0
        ins_meta.append(
            f"Fase de topo de funil: {meta_pv:,} visitas geradas · "
            f"custo/visita R$ {cpc_pv:.4f} · leads ainda em construção"
        )

    # melhor conjunto
    conj_leads = [c for c in meta_conj if c.get("leads", 0) > 0]
    if conj_leads:
        melhor = min(conj_leads, key=lambda x: x["cpl"])
        ins_meta.append(
            f"Melhor conjunto: '{melhor['nome'][:45]}' · "
            f"CPL R$ {melhor['cpl']:.2f} · {melhor['leads']} leads"
        )

    # vencedor criativo
    venc = next((c for c in meta_anun if c.get("avaliacao") == "VENCEDOR"), None)
    dest = next((c for c in meta_anun if c.get("avaliacao") == "DESTAQUE"), None)
    if venc:
        ins_meta.append(
            f"Criativo vencedor: '{venc['nome'][:40]}' · "
            f"R$ {venc['gasto']:.2f} · {venc['leads']} leads · CPL R$ {venc['cpl']:.2f}"
        )
    elif dest:
        ins_meta.append(
            f"Criativo destaque: '{dest['nome'][:40]}' · "
            f"R$ {dest['gasto']:.2f} · {dest.get('page_views', 0):,} visitas"
        )

    # alerta de CPL alto
    if meta_leads > 0 and meta_cpl > 100:
        ins_meta.append(
            f"⚠ CPL acima do alvo (R$ {meta_cpl:.2f}) · "
            f"revisar segmentação e criativos antes de escalar"
        )

    # campanhas pausadas
    pausadas = [c for c in meta_camp if not c.get("ativo", True)]
    if pausadas:
        ins_meta.append(
            f"{len(pausadas)} campanha{'s' if len(pausadas) > 1 else ''} "
            f"inativa{'s' if len(pausadas) > 1 else ''} no período"
        )

    # ── Insights Google ─────────────────────────────────────────────────────
    ins_google = []
    if g_cliq > 0:
        ins_google.append(
            f"R$ {g_gasto:.2f} investidos · {g_cliq} cliques · "
            f"{g_impr:,} impressões · CTR {g_ctr}"
        )
    if g_conv > 0:
        ins_google.append(
            f"{g_conv} {'conversões' if g_conv > 1 else 'conversão'} "
            f"registrada{'s' if g_conv > 1 else ''} · CPL R$ {g_cpl:.2f}"
        )
    elif g_cliq > 0:
        ins_google.append(
            "Fase de aprendizado do Google · sem conversões registradas ainda "
            "(pode levar 7–14 dias para o algoritmo calibrar)"
        )

    camps_g = [c for c in google.get("campanhas", []) if c["gasto"] > 0]
    if camps_g:
        top = max(camps_g, key=lambda x: x["gasto"])
        ins_google.append(
            f"Campanha principal: '{top['nome'][:50]}' · "
            f"R$ {top['gasto']:.2f} · {top['cliques']} cliques"
        )

    # ── Próximos passos automáticos ─────────────────────────────────────────
    proximos = []
    if venc and venc.get("leads", 0) > 0:
        proximos.append({
            "acao": f"Escalar orçamento do criativo '{venc['nome'][:35]}'",
            "responsavel": "Rafael", "prazo": "3 dias",
            "impacto": "Aumentar volume de leads mantendo CPL",
        })
    if meta_leads == 0 and meta_gasto > 0:
        proximos.append({
            "acao": "Ativar campanha de fundo de funil (leads diretos)",
            "responsavel": "Rafael", "prazo": "Esta semana",
            "impacto": "Começar a capturar leads qualificados",
        })
    if g_conv == 0 and g_cliq > 0:
        proximos.append({
            "acao": "Verificar tracking de conversão Google (GA4 + GTM)",
            "responsavel": "Rafael / Cliente", "prazo": "Urgente",
            "impacto": "Dados de conversão precisos para otimização",
        })
    if fase == "otimização":
        proximos.append({
            "acao": "Testar novo criativo para reduzir CPL",
            "responsavel": "Rafael", "prazo": "7 dias",
            "impacto": f"CPL atual R$ {meta_cpl:.2f} · meta abaixo de R$ 60",
        })

    # ── Frases da capa ──────────────────────────────────────────────────────
    if total_leads > 0:
        cpl_g = round(total_inv / total_leads, 2)
        frase_r = f"{total_leads} leads gerados · R$ {total_inv:.2f} investidos"
        frase_d = f"CPL médio R$ {cpl_g:.2f} · Meta + Google · {periodo}"
    elif meta_pv > 0:
        frase_r = f"{meta_pv:,} visitas geradas · R$ {total_inv:.2f} investidos"
        frase_d = f"Fase de construção de audiência · {periodo}"
    else:
        frase_r = f"R$ {total_inv:.2f} investidos no período · {periodo}"
        frase_d = "Dados em processamento · próxima atualização em breve"

    return {
        "insights_meta":    ins_meta,
        "insights_google":  ins_google,
        "proximos_passos":  proximos,
        "frase_resumo":     frase_r,
        "frase_destaque":   frase_d,
        "fase":             fase,
    }


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


# ── Extrator universal por tipo de documento ──────────────────────────────

def _extrair_por_tipo(texto: str, tipo: str, linhas: list) -> dict:
    """
    Lê o texto colado e extrai campos específicos para cada tipo de documento.
    Funciona para TODOS os 7 tipos — sem API, só regras.
    Retorna um dict que sobrescreve os valores padrão do template.
    """
    blocos = parse_texto_completo(texto) if texto else []

    # ── Índice de KV pairs e bullets de todo o texto ──────────────────────
    kv: dict     = {}   # "chave lower" → "valor"
    bullets: list = []  # todos os bullets do texto
    paragrafos: list = []  # parágrafos de texto

    for b in blocos:
        if b["tipo"] == "keyvalues":
            for item in b["itens"]:
                kv[item["chave"].lower().strip()] = item["valor"].strip()
        elif b["tipo"] == "bullets":
            bullets.extend(b["itens"])
        elif b["tipo"] == "texto":
            paragrafos.extend(b["linhas"])

    def _v(keys: list, fallback="") -> str:
        """Busca valor string por palavras-chave nas chaves KV."""
        for k in keys:
            for kk, vv in kv.items():
                if k.lower() in kk:
                    return vv
        return fallback

    def _n(keys: list) -> float:
        """Busca valor numérico por palavras-chave nas chaves KV."""
        v = _v(keys)
        return num(v) if v else 0.0

    campos: dict = {"conteudo_livre": blocos}

    # ══════════════════════════════════════════════════════════════════════
    if tipo == "proposta_comercial":
        vm  = _n(["verba", "mídia", "media", "google ads", "meta ads",
                   "investimento em mídia"])
        hon = _n(["honorário", "honorario", "gestão", "fee", "management",
                  "agência", "serviço de gestão"])
        tot = vm + hon if (vm or hon) else 0.0

        servicos_raw = [v for k, v in kv.items()
                        if any(x in k for x in
                               ["serviço", "servico", "inclui", "entregável",
                                "produto", "pacote", "atividade"])]
        if not servicos_raw:
            servicos_raw = bullets[:10]

        resultados_raw = [v for k, v in kv.items()
                          if any(x in k for x in
                                 ["resultado", "meta", "lead", "roas",
                                  "cpl", "retorno", "projeção"])]
        if not resultados_raw:
            resultados_raw = [l for l in linhas
                              if any(x in l.lower()
                                     for x in ["lead", "cpl", "r$", "roas", "meta"])][:5]

        diag = paragrafos[:3] or linhas[:3]

        campos.update({
            "verba_midia":          vm,
            "honorarios":           hon,
            "total_mensal":         tot or _n(["total", "valor total", "investimento total"]),
            "diagnostico":          diag,
            "servicos":             [{"servico": s, "descricao": ""} for s in servicos_raw[:8]],
            "resultados_esperados": resultados_raw[:6],
        })

    # ══════════════════════════════════════════════════════════════════════
    elif tipo == "ficha_implantacao":
        # responsáveis: pares "Cargo: Nome" de qualquer KV
        resp_kvs = [(k, v) for k, v in kv.items()
                    if any(x in k for x in
                           ["diretor", "gerente", "marketing", "comercial",
                            "responsável", "responsavel", "contato", "analista",
                            "gestor", "coordenador", "fundador"])]
        responsaveis = [{"cargo": k.title(), "nome": v} for k, v in resp_kvs[:6]]

        # processos: comunicação e fluxos
        proc = [f"{k.title()}: {v}" for k, v in kv.items()
                if any(x in k for x in
                       ["aprovação", "aprovacao", "processo", "frequência",
                        "reunião", "reuniao", "prazo", "entrega", "whatsapp",
                        "grupo", "comunicação"])]

        # comunicação: canais de contato
        com = [f"{k.title()}: {v}" for k, v in kv.items()
               if any(x in k for x in
                      ["canal", "whatsapp", "email", "slack", "drive", "grupo"])]

        campos.update({
            "responsaveis":        responsaveis,
            "postagens_mensais":   _v(["postagens", "posts por", "publicações"]),
            "formato_prioritario": _v(["formato", "prioridade de formato", "tipo de conteúdo"]),
            "linguagem":           _v(["linguagem", "tom de voz", "voz", "comunicação"]),
            "layout_cores":        _v(["layout", "cores", "visual", "identidade visual"]),
            "descricao_empresa":   _v(["descrição", "sobre a empresa", "empresa",
                                        "histórico", "história"]) or "\n".join(paragrafos[:2]),
            "posicionamento":      _v(["posicionamento", "proposta de valor", "diferencial"]),
            "diferenciais":        [v for k, v in kv.items()
                                    if any(x in k for x in
                                           ["diferencial", "vantagem", "ponto forte"])] or bullets[:5],
            "publico_perfis":      _v(["perfil de público", "perfis", "público-alvo",
                                        "segmento", "persona"]),
            "publico_meta":        _v(["público meta", "público prioritário", "target"]),
            "publico_estrategia":  _v(["estratégia de público", "segmentação",
                                        "como atingir"]),
            "leads_canais":        _v(["canais de captação", "canais de lead",
                                        "fontes de lead", "canal de geração"]),
            "leads_estrategia":    _v(["estratégia de leads", "captação",
                                        "geração de leads"]),
            "comunicacao":         com or linhas[:4],
            "processos":           proc or linhas[4:8],
            "obj_curto_prazo":     _v(["curto prazo", "30 dias", "objetivos imediatos",
                                        "mês 1"]),
            "obj_medio_prazo":     _v(["médio prazo", "3 meses", "6 meses",
                                        "objetivos de médio"]),
            "obj_trafego":         _v(["objetivo de tráfego", "meta de leads",
                                        "leads por mês", "cpl meta"]),
        })

    # ══════════════════════════════════════════════════════════════════════
    elif tipo == "relatorio_social":
        seg_atual = int(_n(["seguidores atual", "seguidores hoje", "total de seguidores",
                             "seguidores"]))
        seg_novos = int(_n(["novos seguidores", "crescimento", "seguidores novos",
                             "ganho de seguidores"]))
        alcance   = int(_n(["alcance", "reach"]))
        impr      = int(_n(["impressões", "impressions"]))
        saves     = int(_n(["salvamentos", "saves"]))
        eng       = _v(["engajamento", "taxa de engajamento", "engagement"])

        # posts: procura padrão "Post X: descrição" nos KV
        posts_raw = [{"nome": k.title(), "alcance": 0, "likes": 0,
                      "comments": 0, "saves": 0, "tipo": "Post"}
                     for k, v in kv.items()
                     if any(x in k for x in ["post", "reel", "story", "carrossel"])][:8]

        recomendacoes = [v for k, v in kv.items()
                         if any(x in k for x in ["recomendação", "sugestão", "ação",
                                                   "próximo passo", "melhoria"])]
        if not recomendacoes:
            recomendacoes = bullets[:5]

        pauta = [v for k, v in kv.items()
                 if any(x in k for x in ["pauta", "próxima semana", "conteúdo",
                                          "programar", "agendar"])]
        if not pauta:
            pauta = bullets[5:10]

        campos.update({
            "seguidores_atual":  seg_atual,
            "seguidores_novos":  seg_novos,
            "alcance_total":     alcance,
            "impressoes_total":  impr,
            "engajamento_medio": eng or "—",
            "saves_total":       saves,
            "posts":             posts_raw[:5],
            "reels":             [],
            "insights_semana":   paragrafos or linhas[:6],
            "recomendacoes":     recomendacoes[:6],
            "pauta_proxima":     pauta[:6],
        })

    # ══════════════════════════════════════════════════════════════════════
    elif tipo == "plano_de_midia":
        investimento = _n(["verba total", "investimento total", "budget total",
                            "investimento mensal"])
        leads_est    = _v(["leads estimados", "projeção de leads", "meta de leads"])
        cpl_min      = _n(["cpl mínimo", "cpl min", "cpl de "])
        cpl_max      = _n(["cpl máximo", "cpl max"])

        # canais: KV com valores monetários para canais conhecidos
        canais = []
        for k, v in kv.items():
            vn = num(v)
            for canal in ["google", "meta", "instagram", "facebook",
                          "youtube", "pmax", "search", "remarketing"]:
                if canal in k and vn > 0:
                    canais.append({
                        "canal":       k.title(),
                        "funcao":      _v([k]),
                        "verba":       vn,
                        "percentual":  f"{round(vn/investimento*100)}%" if investimento else "—",
                        "formato":     "",
                    })
                    break

        infra = [f"{k.title()}: {v}" for k, v in kv.items()
                 if any(x in k for x in ["pixel", "ga4", "gtm", "capi",
                                          "tracking", "rd station", "crm"])]
        precisa = [f"{k.title()}: {v}" for k, v in kv.items()
                   if any(x in k for x in ["acesso", "cliente fornece",
                                             "necessário", "precisa"])]
        palavras = [v for k, v in kv.items()
                    if any(x in k for x in ["palavra", "keyword", "termo",
                                             "busca"])]

        # cronograma: blocos com datas ou semanas
        crono = [{"semana": b["texto"] if b["tipo"] in ("secao","subsecao") else "",
                   "acoes": b.get("itens", b.get("linhas", []))}
                 for b in blocos
                 if b["tipo"] in ("secao","subsecao","bullets")
                 and any(x in b.get("texto","").lower()
                         for x in ["semana", "mês", "mes", "fase", "etapa"])]

        campos.update({
            "investimento":       investimento,
            "leads_estimados":    leads_est or "—",
            "cpl_estimado_min":   cpl_min,
            "cpl_estimado_max":   cpl_max,
            "canais":             canais or [],
            "produtos":           bullets[:5],
            "cronograma":         crono[:6],
            "infraestrutura":     infra or linhas[:6],
            "precisa_cliente":    precisa or [],
            "palavras_chave":     palavras or [],
        })

    # ══════════════════════════════════════════════════════════════════════
    elif tipo == "apresentacao_resultado":
        campos.update({
            "aprendizados":      paragrafos or linhas[:6],
            "plano_proximo_mes": bullets[:8],
            "metas":             [{"kpi": k.title(), "realizado": v, "meta": "", "status": ""}
                                  for k, v in kv.items()
                                  if any(x in k for x in ["lead", "cpl", "roas", "cac",
                                                            "taxa", "resultado"])][:6],
        })

    return campos


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
    meta_camp_raw    = []
    meta_conj_raw    = []
    meta_anun_raw    = []
    google_raw       = {}
    google_kw_top    = []   # palavras-chave configuradas (bid keywords)
    google_termos_top = []  # termos reais digitados pelos usuários

    for nome_arq, df in dfs.items():
        tipo_csv = detectar_tipo_csv(df)
        if tipo_csv == "meta_campanhas":
            meta_camp_raw.extend(parse_meta_campanhas(df))
        elif tipo_csv == "meta_conjuntos":
            meta_conj_raw.extend(parse_meta_conjuntos(df))
        elif tipo_csv == "meta_anuncios":
            meta_anun_raw.extend(parse_meta_anuncios(df))
        elif tipo_csv in ("google_campanhas", "google_keywords", "google_termos"):
            novo = parse_google_campanhas(df)
            # usa o arquivo com mais gasto (evita double-count acumulando)
            if novo.get("gasto", 0) >= google_raw.get("gasto", 0):
                google_raw = novo
            # separa palavras-chave (configuradas) de termos de pesquisa (digitados)
            if tipo_csv == "google_keywords" and not google_kw_top:
                google_kw_top = parse_google_keywords_top(df, top_n=5)
            elif tipo_csv == "google_termos" and not google_termos_top:
                google_termos_top = parse_google_keywords_top(df, top_n=5)

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
            # pula campanhas sem nenhuma atividade no período
            if c.get("gasto", 0) == 0 and c.get("impressoes", 0) == 0:
                continue
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

        # ── Top 5 criativos (leads primeiro, depois por gasto) ────────────
        cri_com_lead = sorted(
            [c for c in meta_anun_raw if c.get("leads", 0) > 0],
            key=lambda x: (x["leads"], -x["cpl"]), reverse=True
        )
        cri_sem_lead = sorted(
            [c for c in meta_anun_raw if c.get("leads", 0) == 0 and c.get("gasto", 0) > 0],
            key=lambda x: x["gasto"], reverse=True
        )
        top5_criativos = (cri_com_lead + cri_sem_lead)[:5]

        # ── Análise automática inteligente ────────────────────────────────
        analise = _analisar_performance(
            meta_camp_raw, meta_conj_raw, meta_anun_raw,
            google_raw, dados["periodo"], dados["cliente"]
        )
        # texto do usuário tem prioridade sobre análise automática
        insights_meta   = linhas_livres[:2] + analise["insights_meta"] if linhas_livres \
                          else analise["insights_meta"]
        insights_google = analise["insights_google"]
        proximos        = analise["proximos_passos"]

        g = google_raw
        dados.update({
            "meta_campanhas": campanhas_template,
            "meta_total":     meta_total,
            "meta_leads":     meta_leads,
            "meta_cpl":       meta_cpl,
            "criativos":      top5_criativos,
            "conjuntos":      meta_conj_raw[:8],  # máx 8 conjuntos
            "google_gasto":      g.get("gasto", 0),
            "google_cliques":    g.get("cliques", 0),
            "google_impressoes": g.get("impressoes", 0),
            "google_ctr":        g.get("ctr", "0%"),
            "google_conv":       g.get("conv", 0),
            "google_cpl":        g.get("cpl", 0),
            "google_kw_top":      google_kw_top,
            "google_termos_top":  google_termos_top,
            "insights_criativos": insights_meta[:5],
            "insights_google":    insights_google,
            "sugestoes_conteudo": [],
            "estrategia_seguidores": [],
            "proximos_passos": proximos,
        })

        # frases da capa (texto do usuário ou análise automática)
        if not dados["frase_resumo"]:
            dados["frase_resumo"]   = analise["frase_resumo"]
            dados["frase_destaque"] = analise["frase_destaque"]

    # ── Relatório Social ──────────────────────────────────────────────────
    elif tipo == "relatorio_social":
        defaults = {
            "seguidores_atual": 0, "seguidores_novos": 0,
            "alcance_total": 0, "impressoes_total": 0,
            "engajamento_medio": "—", "saves_total": 0,
            "posts": [], "reels": [],
            "insights_semana": linhas_livres,
            "recomendacoes": [],
            "pauta_proxima": [],
            "conteudo_livre": [],
        }
        dados.update(defaults)
        if texto_livre:
            ext = _extrair_por_tipo(texto_livre, tipo, linhas_livres)
            # só sobrescreve se o extrator encontrou algo real
            for k, v in ext.items():
                if v or v == 0:
                    dados[k] = v

    # ── Plano de Mídia ────────────────────────────────────────────────────
    elif tipo == "plano_de_midia":
        defaults = {
            "investimento": 0, "leads_estimados": "—",
            "cpl_estimado_min": 0, "cpl_estimado_max": 0,
            "canais": [], "produtos": [],
            "cronograma": [], "infraestrutura": linhas_livres,
            "precisa_cliente": [], "palavras_chave": [],
            "conteudo_livre": [],
        }
        dados.update(defaults)
        if texto_livre:
            ext = _extrair_por_tipo(texto_livre, tipo, linhas_livres)
            for k, v in ext.items():
                if v or v == 0:
                    dados[k] = v

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
            "conteudo_livre": [],
        })
        if texto_livre:
            ext = _extrair_por_tipo(texto_livre, tipo, linhas_livres)
            # CSV data tem prioridade; texto enriquece aprendizados, plano e metas
            if ext.get("aprendizados"):
                dados["aprendizados"] = ext["aprendizados"]
            if ext.get("plano_proximo_mes"):
                dados["plano_proximo_mes"] = ext["plano_proximo_mes"]
            if ext.get("metas"):
                dados["metas"] = ext["metas"]
            dados["conteudo_livre"] = ext.get("conteudo_livre", [])

    # ── Ficha de Implantação ──────────────────────────────────────────────
    elif tipo == "ficha_implantacao":
        defaults = {
            "responsaveis":        [],
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
            "conteudo_livre":      [],
        }
        dados.update(defaults)
        if texto_livre:
            ext = _extrair_por_tipo(texto_livre, tipo, linhas_livres)
            for k, v in ext.items():
                if v or v == 0:
                    dados[k] = v

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
        defaults = {
            "data_proposta": periodo or "",
            "validade": "30 dias",
            "verba_midia": 0, "honorarios": 0, "total_mensal": 0,
            "diagnostico": linhas_livres,
            "servicos": [], "resultados_esperados": [],
            "diferenciais": [
                "Gestao especializada em trafego para seguranca eletronica",
                "Google Ads + Meta Ads com estrategia de funil completo",
                "Relatorios semanais com analise de criativos e CPL",
                "Sem mensalidade oculta · transparencia total nos resultados",
            ],
            "proximos_passos": [],
            "conteudo_livre": [],
        }
        dados.update(defaults)
        if texto_livre:
            ext = _extrair_por_tipo(texto_livre, tipo, linhas_livres)
            for k, v in ext.items():
                if v or v == 0:
                    dados[k] = v

    return dados
