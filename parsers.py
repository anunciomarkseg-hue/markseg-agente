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
    Suporta formato brasileiro (1.234,56), americano (1,234.56) e nan/None.
    """
    try:
        # NaN nativo de Python/pandas
        if val is None:
            return default
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                return default
            return val
        if isinstance(val, int):
            return float(val)

        s = str(val).strip()
        # strings vazias / nan textuais
        if s.lower() in ("nan", "none", "", "-", "--", "n/a", "—"):
            return default

        # remove símbolos de moeda e espaços
        s = re.sub(r"[R$\s]", "", s)
        if not s:
            return default

        # detecta formato pelo último separador
        dot_pos   = s.rfind(".")
        comma_pos = s.rfind(",")

        if comma_pos > dot_pos:
            # formato BR: "1.234,56"  →  "1234.56"
            s = s.replace(".", "").replace(",", ".")
        elif dot_pos > comma_pos:
            # formato US: "1,234.56"  →  "1234.56"
            s = s.replace(",", "")
        else:
            # sem separador ou só vírgula sem ponto: trata vírgula como decimal
            s = s.replace(",", ".")

        result = float(s)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except Exception:
        return default


def inteiro(val, default=0):
    """Converte valor para int, tolerando NaN, vírgulas e pontos."""
    try:
        if val is None:
            return default
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                return default
            return int(val)
        if isinstance(val, int):
            return val
        s = str(val).strip()
        if s.lower() in ("nan", "none", "", "-", "--", "n/a", "—"):
            return default
        return int(num(s, default))
    except Exception:
        return default


def detectar_tipo_csv(df: pd.DataFrame) -> str:
    """Detecta se um DataFrame é de campanhas, conjuntos ou anúncios do Meta, ou Google Ads."""
    cols = [str(c).lower() for c in df.columns]

    tem_campanha  = any("nome da campanha" in c or "campaign name" in c for c in cols)
    tem_conjunto  = any("nome do conjunto" in c or "ad set name" in c or
                        "conjunto de anúncios" in c for c in cols)
    tem_anuncio   = any("nome do anúncio" in c or "ad name" in c for c in cols)
    tem_google    = any("keyword" in c or "palavra-chave" in c or
                        "search term" in c or "termo de pesquisa" in c for c in cols)

    # Meta Ads — prioridade pelo campo mais específico
    if tem_anuncio:
        return "meta_anuncios"
    if tem_conjunto and not tem_campanha:
        return "meta_conjuntos"
    if tem_conjunto and tem_campanha:
        return "meta_conjuntos"
    if tem_campanha:
        return "meta_campanhas"

    # Google Ads
    if tem_google:
        return "google_keywords"
    if any("cliques" in c or "clicks" in c for c in cols):
        return "google_campanhas"
    if any("campanha" in c or "campaign" in c for c in cols):
        return "google_campanhas"

    return "desconhecido"


def col(df, *opcoes):
    """Retorna o nome da coluna que corresponde a uma das opções."""
    for op in opcoes:
        for c in df.columns:
            if op.lower() in c.lower():
                return c
    return None


# ── Parsers Meta Ads ───────────────────────────────────────────────────────

def parse_meta_campanhas(df: pd.DataFrame) -> list:
    resultado = []
    nome_col    = col(df, "nome da campanha", "campaign name", "campanha")
    gasto_col   = col(df, "valor usado", "amount spent", "gasto", "verba")
    result_col  = col(df, "resultados", "results")
    impr_col    = col(df, "impressões", "impressions", "impressoes")
    alcance_col = col(df, "alcance", "reach")
    cpl_col     = col(df, "custo por resultado", "custo por lead", "cost per lead",
                       "cost per result", "custo por result", "cpr")
    leads_col   = col(df, "leads", "resultados", "results")

    for _, row in df.iterrows():
        nome = str(row.get(nome_col, "")) if nome_col else ""
        if not nome or nome.lower() in ("nan", "", "total"):
            continue
        gasto   = num(row.get(gasto_col, 0)) if gasto_col else 0
        impr    = inteiro(row.get(impr_col, 0)) if impr_col else 0
        cpl_val = num(row.get(cpl_col, 0)) if cpl_col else 0
        leads   = inteiro(row.get(leads_col, 0)) if leads_col else 0
        resultado.append({
            "nome": nome, "gasto": gasto, "impressoes": impr,
            "cpl": cpl_val, "leads": leads,
        })
    return resultado


def parse_meta_conjuntos(df: pd.DataFrame) -> list:
    resultado = []
    nome_col  = col(df, "nome do conjunto", "ad set name", "conjunto de anúncios", "conjunto")
    gasto_col = col(df, "valor usado", "amount spent", "gasto", "verba")
    leads_col = col(df, "resultados", "results", "leads")
    cpl_col   = col(df, "custo por resultado", "custo por result", "custo por lead",
                      "cost per result", "cost per lead", "cost per")
    orc_col   = col(df, "orçamento", "orcamento", "budget")
    alc_col   = col(df, "alcance", "reach")
    stat_col  = col(df, "veiculação", "veiculacao", "delivery", "status")

    for _, row in df.iterrows():
        nome = str(row.get(nome_col, "")) if nome_col else ""
        if not nome or nome.lower() in ("nan", "", "total"):
            continue
        status = "Ativo" if "active" in str(row.get(stat_col,"")).lower() or "ativ" in str(row.get(stat_col,"")).lower() else "Inativo"
        resultado.append({
            "nome":      nome,
            "status":    status,
            "orcamento": num(row.get(orc_col, 0)) if orc_col else 0,
            "gasto":     num(row.get(gasto_col, 0)) if gasto_col else 0,
            "leads":     inteiro(row.get(leads_col, 0)) if leads_col else 0,
            "cpl":       num(row.get(cpl_col, 0)) if cpl_col else 0,
            "alcance":   inteiro(row.get(alc_col, 0)) if alc_col else 0,
        })
    return resultado


def parse_meta_anuncios(df: pd.DataFrame) -> list:
    resultado = []
    nome_col  = col(df, "nome do anúncio", "ad name", "anuncio", "anúncio")
    gasto_col = col(df, "valor usado", "amount spent", "gasto", "verba")
    leads_col = col(df, "resultados", "results", "leads")
    cpl_col   = col(df, "custo por resultado", "custo por lead", "custo por result",
                      "cost per lead", "cost per result", "cost per")
    hook_col  = col(df, "hook rate")
    stat_col  = col(df, "veiculação", "veiculacao", "delivery", "status")

    for _, row in df.iterrows():
        nome = str(row.get(nome_col, "")) if nome_col else ""
        if not nome or nome.lower() in ("nan", "", "total"):
            continue
        gasto  = num(row.get(gasto_col, 0)) if gasto_col else 0
        leads  = inteiro(row.get(leads_col, 0)) if leads_col else 0
        cpl_v  = num(row.get(cpl_col, 0)) if cpl_col else 0
        hook   = f"{num(row.get(hook_col,0))*100:.1f}%" if hook_col else "—"
        status = "Ativo" if "active" in str(row.get(stat_col,"")).lower() or "ativ" in str(row.get(stat_col,"")).lower() else "Inativo"
        resultado.append({
            "nome":      nome,
            "status":    status,
            "gasto":     gasto,
            "leads":     leads,
            "cpl":       cpl_v,
            "hook":      hook,
            "avaliacao": "",
            "destaque":  False,
        })

    # marca vencedor (melhor CPL com leads >= 5)
    validos = [c for c in resultado if c["leads"] >= 5]
    if validos:
        vencedor = min(validos, key=lambda x: x["cpl"])
        vencedor["avaliacao"] = "VENCEDOR"
        vencedor["destaque"]  = True
    return resultado


# ── Parsers Google Ads ─────────────────────────────────────────────────────

def parse_google_campanhas(df: pd.DataFrame) -> dict:
    gasto_col  = col(df, "custo", "cost", "valor gasto", "valor", "spend")
    cliq_col   = col(df, "cliques", "clicks")
    impr_col   = col(df, "impressões", "impressoes", "impr", "impressions")
    ctr_col    = col(df, "ctr")
    conv_col   = col(df, "conversões", "conversoes", "conversions", "conv.")
    cpc_col    = col(df, "custo / conv", "cost / conv", "cpc médio", "avg. cpc",
                       "cpc", "cost/conv")

    totais = {"gasto": 0, "cliques": 0, "impressoes": 0,
              "ctr": "0%", "conv": 0, "cpl": 0}
    for _, row in df.iterrows():
        totais["gasto"]     += num(row.get(gasto_col, 0)) if gasto_col else 0
        totais["cliques"]   += inteiro(row.get(cliq_col, 0)) if cliq_col else 0
        totais["impressoes"]+= inteiro(row.get(impr_col, 0)) if impr_col else 0
        totais["conv"]      += inteiro(row.get(conv_col, 0)) if conv_col else 0

    if ctr_col:
        try:
            totais["ctr"] = f"{num(df[ctr_col].iloc[0]):.2f}%"
        except Exception:
            pass
    if cpc_col and totais["conv"] > 0:
        try:
            totais["cpl"] = num(df[cpc_col].iloc[0])
        except Exception:
            pass
    elif totais["conv"] > 0:
        totais["cpl"] = round(totais["gasto"] / totais["conv"], 2)
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
        elif tipo_csv in ("google_campanhas", "google_keywords"):
            google_raw = parse_google_campanhas(df)

    # ── Relatório de Performance ──────────────────────────────────────────
    if tipo == "relatorio_performance":

        # etapas do funil a partir dos nomes de campanha
        ETAPA_MAP = {
            "topo": "TOPO", "top": "TOPO",
            "meio": "MEIO", "mid": "MEIO",
            "fundo": "FUNDO", "bottom": "FUNDO", "conv": "FUNDO",
            "lead": "FUNDO", "trial": "FUNDO",
            "tráfego": "MEIO", "trafego": "MEIO",
        }
        campanhas_template = []
        for c in meta_camp_raw:
            etapa = "FUNDO"
            for k, v in ETAPA_MAP.items():
                if k in c["nome"].lower():
                    etapa = v
                    break
            campanhas_template.append({
                "etapa": etapa, "nome": c["nome"],
                "verba": c["gasto"], "resultado": f"{c['leads']} leads" if c["leads"] else f"{c['impressoes']:,} impr.",
                "cpr":   c["cpl"] if c["leads"] else 0,
                "impressoes": c["impressoes"],
            })

        meta_total = sum(c["gasto"] for c in meta_camp_raw)
        meta_leads = sum(c["leads"] for c in meta_camp_raw)
        meta_cpl   = round(meta_total / meta_leads, 2) if meta_leads else 0

        dados.update({
            "meta_campanhas": campanhas_template,
            "meta_total":     meta_total,
            "meta_leads":     meta_leads,
            "meta_cpl":       meta_cpl,
            "criativos":      meta_anun_raw,
            "conjuntos":      meta_conj_raw,
            "google_gasto":      google_raw.get("gasto", 0),
            "google_cliques":    google_raw.get("cliques", 0),
            "google_impressoes": google_raw.get("impressoes", 0),
            "google_ctr":        google_raw.get("ctr", "0%"),
            "google_conv":       google_raw.get("conv", 0),
            "google_cpl":        google_raw.get("cpl", 0),
            "insights_criativos": linhas_livres[:4] if linhas_livres else [],
            "insights_google":    [],
            "sugestoes_conteudo": [],
            "estrategia_seguidores": [],
            "proximos_passos": [],
        })

        # frase automática se não foi digitada
        if not dados["frase_resumo"] and meta_anun_raw:
            vencedor = next((c for c in meta_anun_raw if c.get("destaque")), None)
            if vencedor:
                dados["frase_resumo"]   = f"{vencedor['nome']} é o criativo vencedor."
                dados["frase_destaque"] = f"CPL R$ {vencedor['cpl']:.2f} · escalar agora."
        if not dados["frase_resumo"] and meta_leads:
            dados["frase_resumo"]   = f"{meta_leads} leads gerados na semana."
            dados["frase_destaque"] = f"CPL médio R$ {meta_cpl:.2f} · investimento R$ {meta_total:.2f}."

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
