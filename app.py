"""
MarkSeg — Agente de Documentos
Interface Streamlit para geração de PDFs padronizados da agência.
"""

import streamlit as st
import os, sys, tempfile, json
from datetime import date

# garante que o diretório raiz do projeto está no path (necessário no Streamlit Cloud)
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Config da página ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarkSeg · Agente de Documentos",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS customizado ───────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --navy:  #1B3A6B;
    --orange:#F5821E;
    --gray:  #F5F6FA;
}
[data-testid="stSidebar"] {
    background: var(--navy);
}
[data-testid="stSidebar"] * {
    color: white !important;
}
.stSelectbox label, .stTextInput label, .stTextArea label,
.stNumberInput label, .stDateInput label {
    font-weight: 600;
    color: var(--navy) !important;
}
.doc-card {
    background: var(--gray);
    border-left: 4px solid var(--orange);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.section-title {
    background: var(--navy);
    color: white;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 700;
    font-size: 0.85rem;
    margin: 16px 0 8px 0;
    letter-spacing: 0.05em;
}
.stButton > button {
    background: var(--orange) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    padding: 0.6rem 2rem !important;
    border-radius: 6px !important;
    font-size: 1rem !important;
}
.stButton > button:hover {
    background: #D4691A !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "brand", "logo.png")

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=160)
    else:
        st.markdown("## **MarkSeg**")
        st.markdown("*Agência de Tráfego*")

    st.markdown("---")
    st.markdown("### Tipo de Documento")

    tipo = st.selectbox("", [
        "Relatório Semanal de Performance",
        "Relatório Semanal de Mídias Sociais",
        "Plano de Mídia Estratégico",
        "Apresentação de Resultado Mensal",
        "Proposta Comercial",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("#### Dados Gerais")
    cliente     = st.text_input("Nome do Cliente", placeholder="Ex: Faturei Hoje")
    agencia     = st.text_input("Agência", value="MarkSeg Tráfego · Rafael")
    periodo     = st.text_input("Período", placeholder="Ex: 13 a 19 de Mai 2026")

    st.markdown("---")
    st.caption("MarkSeg · Agente de Documentos v1.0")

# ── Cabeçalho principal ───────────────────────────────────────────────────
st.markdown(f"# 🛡️ {tipo}")
st.markdown(f"*Preencha os dados abaixo · cliente: **{cliente or '...'}** · {periodo or '...'}*")
st.divider()

# ─────────────────────────────────────────────────────────────────────────
# FORMULÁRIOS POR TIPO
# ─────────────────────────────────────────────────────────────────────────

dados = {
    "cliente":    cliente,
    "agencia":    agencia,
    "periodo":    periodo,
    "responsavel": "Rafael",
}

# ════════════════════════════════════════════════════════════════════
if tipo == "Relatório Semanal de Performance":

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">📊 RESUMO EXECUTIVO</div>', unsafe_allow_html=True)
        frase_resumo   = st.text_input("Frase de resumo", placeholder="Ex: video15 é o criativo vencedor.")
        frase_destaque = st.text_input("Frase de destaque (laranja)", placeholder="Ex: CPL R$ 3,39 · escalar agora.")
        info_capa      = st.text_input("Subtítulo da capa", placeholder="Análise de performance por funil.")
    with col2:
        st.markdown('<div class="section-title">💰 META ADS · TOTAIS</div>', unsafe_allow_html=True)
        meta_total = st.number_input("Investimento Meta Total (R$)", value=0.0, step=0.01)
        meta_leads = st.number_input("Leads gerados (fundo)", value=0, step=1)
        meta_cpl   = st.number_input("CPL médio fundo (R$)", value=0.0, step=0.01)

    st.markdown('<div class="section-title">📋 CAMPANHAS META · FUNIL</div>', unsafe_allow_html=True)
    st.caption("Adicione cada campanha do funil.")

    n_camp = st.number_input("Quantas campanhas?", 1, 10, 4, key="ncamp")
    meta_campanhas = []
    cols_camp = st.columns(6)
    headers = ["Etapa", "Nome da Campanha", "Verba (R$)", "Resultado", "CPR (R$)", "Impressões"]
    for h, c in zip(headers, cols_camp):
        c.markdown(f"**{h}**")
    for i in range(int(n_camp)):
        cols = st.columns(6)
        etapa   = cols[0].selectbox("", ["TOPO","MEIO","FUNDO"], key=f"et{i}", label_visibility="collapsed")
        nome    = cols[1].text_input("", key=f"cn{i}", label_visibility="collapsed", placeholder="Nome")
        verba   = cols[2].number_input("", key=f"cv{i}", label_visibility="collapsed", value=0.0, step=0.01)
        result  = cols[3].text_input("", key=f"cr{i}", label_visibility="collapsed", placeholder="Resultado")
        cpr     = cols[4].number_input("", key=f"cpr{i}", label_visibility="collapsed", value=0.0, step=0.01)
        impr    = cols[5].number_input("", key=f"ci{i}", label_visibility="collapsed", value=0, step=1)
        meta_campanhas.append({"etapa": etapa, "nome": nome, "verba": verba,
                                "resultado": result, "cpr": cpr, "impressoes": impr})

    st.markdown('<div class="section-title">🎬 CRIATIVOS · FUNDO</div>', unsafe_allow_html=True)
    n_cri = st.number_input("Quantos criativos?", 1, 10, 2, key="ncri")
    criativos = []
    for i in range(int(n_cri)):
        with st.expander(f"Criativo {i+1}", expanded=(i == 0)):
            c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
            nome_c  = c1.text_input("Nome", key=f"crn{i}", placeholder="video15")
            status  = c2.selectbox("Status", ["Ativo","Inativo"], key=f"crs{i}")
            gasto   = c3.number_input("Gasto (R$)", key=f"crg{i}", value=0.0)
            leads_c = c4.number_input("Leads", key=f"crl{i}", value=0)
            cpl_c   = c5.number_input("CPL (R$)", key=f"crp{i}", value=0.0)
            hook    = c6.text_input("Hook Rate", key=f"crh{i}", placeholder="22%")
            aval    = c7.text_input("Avaliação", key=f"cra{i}", placeholder="VENCEDOR")
            dest    = st.checkbox("Marcar como vencedor", key=f"crd{i}")
            criativos.append({"nome": nome_c, "status": status, "gasto": gasto,
                               "leads": leads_c, "cpl": cpl_c, "hook": hook,
                               "avaliacao": aval, "destaque": dest})

    st.markdown('<div class="section-title">📦 CONJUNTOS DE ANÚNCIOS</div>', unsafe_allow_html=True)
    n_conj = st.number_input("Quantos conjuntos?", 1, 10, 2, key="nconj")
    conjuntos = []
    for i in range(int(n_conj)):
        with st.expander(f"Conjunto {i+1}", expanded=(i == 0)):
            c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
            nome_j  = c1.text_input("Nome", key=f"jn{i}", placeholder="Trial 7d Quentes")
            stat_j  = c2.selectbox("Status", ["Ativo","Inativo"], key=f"js{i}")
            orc_j   = c3.number_input("Orç/dia R$", key=f"jo{i}", value=0.0)
            gas_j   = c4.number_input("Gasto R$", key=f"jg{i}", value=0.0)
            led_j   = c5.number_input("Leads", key=f"jl{i}", value=0)
            cpl_j   = c6.number_input("CPL R$", key=f"jp{i}", value=0.0)
            alc_j   = c7.number_input("Alcance", key=f"ja{i}", value=0)
            conjuntos.append({"nome": nome_j, "status": stat_j, "orcamento": orc_j,
                               "gasto": gas_j, "leads": led_j, "cpl": cpl_j, "alcance": alc_j})

    st.markdown('<div class="section-title">🔍 GOOGLE ADS</div>', unsafe_allow_html=True)
    g1,g2,g3,g4,g5,g6 = st.columns(6)
    g_gasto = g1.number_input("Gasto (R$)", key="gg", value=0.0)
    g_cli   = g2.number_input("Cliques", key="gc", value=0)
    g_imp   = g3.number_input("Impressões", key="gi", value=0)
    g_ctr   = g4.text_input("CTR", key="gt", placeholder="13,33%")
    g_conv  = g5.number_input("Conversões", key="gv", value=0)
    g_cpl   = g6.number_input("CPL (R$)", key="gp", value=0.0)

    st.markdown('<div class="section-title">💡 INSIGHTS E PRÓXIMOS PASSOS</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        ins_cri = st.text_area("Insights sobre criativos (1 por linha)",
                                placeholder="video15 concentrou 91% dos leads...", height=100)
        ins_goo = st.text_area("Insights Google (1 por linha)", height=80)
    with col_b:
        suges   = st.text_area("Sugestões de conteúdo (1 por linha)",
                                placeholder="IA mudando a segurança...", height=100)
        proxp   = st.text_area("Próximos passos: acao|responsavel|prazo|impacto (1 por linha)",
                                height=80)

    dados.update({
        "frase_resumo":    frase_resumo,
        "frase_destaque":  frase_destaque,
        "info_capa":       info_capa,
        "meta_total":      meta_total,
        "meta_leads":      int(meta_leads),
        "meta_cpl":        meta_cpl,
        "meta_campanhas":  meta_campanhas,
        "criativos":       criativos,
        "conjuntos":       conjuntos,
        "google_gasto":    g_gasto,
        "google_cliques":  int(g_cli),
        "google_impressoes": int(g_imp),
        "google_ctr":      g_ctr,
        "google_conv":     int(g_conv),
        "google_cpl":      g_cpl,
        "insights_criativos": [l.strip() for l in ins_cri.split("\n") if l.strip()],
        "insights_google":    [l.strip() for l in ins_goo.split("\n") if l.strip()],
        "sugestoes_conteudo": [l.strip() for l in suges.split("\n") if l.strip()],
        "proximos_passos": [
            dict(zip(["acao","responsavel","prazo","impacto"], l.split("|")))
            for l in proxp.split("\n") if "|" in l
        ],
    })
    template_fn = "relatorio_performance"

# ════════════════════════════════════════════════════════════════════
elif tipo == "Relatório Semanal de Mídias Sociais":

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">📊 MÉTRICAS GERAIS</div>', unsafe_allow_html=True)
        seg_atual  = st.number_input("Seguidores atual", value=0)
        seg_novos  = st.number_input("Seguidores novos na semana", value=0)
        alcance    = st.number_input("Alcance total", value=0)
        impressoes = st.number_input("Impressões totais", value=0)
        eng_medio  = st.text_input("Engajamento médio", placeholder="4,2%")
        saves      = st.number_input("Saves totais", value=0)
    with col2:
        st.markdown('<div class="section-title">📝 RESUMO EXECUTIVO</div>', unsafe_allow_html=True)
        frase_resumo   = st.text_input("Frase de resumo", key="fr_s")
        frase_destaque = st.text_input("Frase de destaque", key="fd_s")
        info_capa      = st.text_input("Subtítulo da capa", key="ic_s")

    st.markdown('<div class="section-title">📱 POSTS DA SEMANA</div>', unsafe_allow_html=True)
    n_posts = st.number_input("Quantos posts?", 1, 15, 4, key="nposts")
    posts = []
    for i in range(int(n_posts)):
        with st.expander(f"Post {i+1}", expanded=(i == 0)):
            c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
            data_p  = c1.text_input("Data", key=f"pd{i}", placeholder="13/mai")
            fmt_p   = c2.selectbox("Formato", ["Reels","Carrossel","Estático","Story"], key=f"pf{i}")
            tit_p   = c3.text_input("Título", key=f"pt{i}", placeholder="Post sobre IA")
            alc_p   = c4.number_input("Alcance", key=f"pa{i}", value=0)
            curt_p  = c5.number_input("Curtidas", key=f"pc{i}", value=0)
            sav_p   = c6.number_input("Saves", key=f"ps{i}", value=0)
            eng_p   = c7.text_input("Engaj.", key=f"pe{i}", placeholder="5%")
            dest_p  = st.checkbox("Melhor post da semana", key=f"pde{i}")
            posts.append({"data": data_p, "formato": fmt_p, "titulo": tit_p,
                          "alcance": alc_p, "curtidas": curt_p, "saves": sav_p,
                          "engajamento": eng_p, "destaque": dest_p})

    st.markdown('<div class="section-title">💡 INSIGHTS E PAUTA</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        insights  = st.text_area("Insights da semana (1 por linha)", height=100)
        recomends = st.text_area("Recomendações (1 por linha)", height=80)
    with col_b:
        pauta_txt = st.text_area("Pauta próxima semana: dia|formato|tema|objetivo (1 por linha)",
                                  height=100)

    dados.update({
        "frase_resumo":    frase_resumo, "frase_destaque": frase_destaque,
        "info_capa":       info_capa,
        "seguidores_atual": int(seg_atual), "seguidores_novos": int(seg_novos),
        "alcance_total":   int(alcance),   "impressoes_total": int(impressoes),
        "engajamento_medio": eng_medio,    "saves_total": int(saves),
        "posts":           posts,
        "insights_semana": [l.strip() for l in insights.split("\n") if l.strip()],
        "recomendacoes":   [l.strip() for l in recomends.split("\n") if l.strip()],
        "pauta_proxima": [
            dict(zip(["dia","formato","tema","objetivo"], l.split("|")))
            for l in pauta_txt.split("\n") if "|" in l
        ],
    })
    template_fn = "relatorio_social"

# ════════════════════════════════════════════════════════════════════
elif tipo == "Plano de Mídia Estratégico":

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">💰 INVESTIMENTO</div>', unsafe_allow_html=True)
        investimento   = st.number_input("Investimento mensal (R$)", value=0.0)
        leads_est      = st.text_input("Leads estimados", placeholder="400–650")
        cpl_min        = st.number_input("CPL estimado mínimo (R$)", value=0.0)
        cpl_max        = st.number_input("CPL estimado máximo (R$)", value=0.0)
    with col2:
        st.markdown('<div class="section-title">📝 RESUMO EXECUTIVO</div>', unsafe_allow_html=True)
        frase_resumo   = st.text_input("Frase de resumo", key="fr_p")
        frase_destaque = st.text_input("Frase de destaque", key="fd_p")
        info_capa      = st.text_input("Subtítulo da capa", key="ic_p")

    st.markdown('<div class="section-title">📋 CANAIS E DISTRIBUIÇÃO</div>', unsafe_allow_html=True)
    n_canais = st.number_input("Quantos canais?", 1, 8, 4, key="ncanais")
    canais = []
    for i in range(int(n_canais)):
        c1,c2,c3,c4,c5 = st.columns(5)
        etapa  = c1.selectbox("Etapa", ["Google","Meta","Reserva"], key=f"ce{i}")
        canal  = c2.text_input("Canal", key=f"cc{i}", placeholder="Google · Search Ads")
        funcao = c3.text_input("Função", key=f"cf{i}", placeholder="Captação intenção")
        verba  = c4.number_input("Verba (R$)", key=f"cv{i}", value=0.0)
        pct    = c5.number_input("Part. (%)", key=f"cp{i}", value=0.0)
        canais.append({"etapa": etapa, "canal": canal, "funcao": funcao,
                       "verba": verba, "percentual": pct})

    st.markdown('<div class="section-title">🎯 CRONOGRAMA 4 SEMANAS</div>', unsafe_allow_html=True)
    cronograma = []
    for i in range(4):
        with st.expander(f"Semana {i+1}", expanded=(i == 0)):
            nome_s = st.text_input("Título da semana", key=f"sn{i}",
                                    value=f"SEMANA {i+1}")
            itens_s = st.text_area("Ações (1 por linha)", key=f"si{i}", height=80)
            cronograma.append({"semana": nome_s,
                                "itens": [l.strip() for l in itens_s.split("\n") if l.strip()]})

    col_a, col_b = st.columns(2)
    with col_a:
        infra = st.text_area("Infraestrutura (1 por linha)", height=100)
        kws   = st.text_area("Palavras-chave (1 por linha)", height=60)
    with col_b:
        precisa = st.text_area("O que precisa do cliente (1 por linha)", height=100)

    dados.update({
        "frase_resumo":    frase_resumo, "frase_destaque": frase_destaque,
        "info_capa":       info_capa,    "investimento": investimento,
        "leads_estimados": leads_est,    "cpl_estimado_min": cpl_min,
        "cpl_estimado_max": cpl_max,     "canais": canais,
        "cronograma":      cronograma,
        "infraestrutura":  [l.strip() for l in infra.split("\n") if l.strip()],
        "precisa_cliente": [l.strip() for l in precisa.split("\n") if l.strip()],
        "palavras_chave":  [l.strip() for l in kws.split("\n") if l.strip()],
    })
    template_fn = "plano_de_midia"

# ════════════════════════════════════════════════════════════════════
elif tipo == "Apresentação de Resultado Mensal":

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">📊 KPIs DO MÊS</div>', unsafe_allow_html=True)
        inv_tot  = st.number_input("Investimento total (R$)", value=0.0)
        leads_t  = st.number_input("Leads totais", value=0)
        cpl_m    = st.number_input("CPL médio (R$)", value=0.0)
        taxa_q   = st.text_input("Taxa de qualificação", placeholder="47%")
        roas_v   = st.text_input("ROAS", placeholder="3,2x")
        cac_v    = st.number_input("CAC (R$)", value=0.0)
    with col2:
        st.markdown('<div class="section-title">📝 RESUMO EXECUTIVO</div>', unsafe_allow_html=True)
        frase_resumo   = st.text_input("Frase de resumo", key="fr_r")
        frase_destaque = st.text_input("Frase de destaque", key="fd_r")
        info_capa      = st.text_input("Subtítulo da capa", key="ic_r")

    st.markdown('<div class="section-title">🎯 METAS X REALIZADO</div>', unsafe_allow_html=True)
    n_metas = st.number_input("Quantas métricas?", 1, 10, 4, key="nmetas")
    metas = []
    for i in range(int(n_metas)):
        c1,c2,c3,c4 = st.columns(4)
        met = c1.text_input("Métrica", key=f"mm{i}", placeholder="CPL")
        meta_v = c2.text_input("Meta", key=f"mv{i}", placeholder="R$ 15")
        real_v = c3.text_input("Realizado", key=f"mr{i}", placeholder="R$ 10,50")
        stat_v = c4.selectbox("Status", ["OK","ALERTA","CRITICO"], key=f"ms{i}")
        metas.append({"metrica": met, "meta": meta_v, "realizado": real_v, "status": stat_v})

    col_a, col_b = st.columns(2)
    with col_a:
        aprendef = st.text_area("Aprendizados do mês (1 por linha)", height=100)
    with col_b:
        plano_pm = st.text_area("Plano próximo mês: acao|canal|impacto (1 por linha)", height=100)

    dados.update({
        "frase_resumo":    frase_resumo, "frase_destaque": frase_destaque,
        "info_capa":       info_capa,
        "investimento_total": inv_tot,   "leads_total": int(leads_t),
        "cpl_medio":       cpl_m,        "taxa_qualificacao": taxa_q,
        "roas":            roas_v,        "cac": cac_v,
        "metas":           metas,
        "aprendizados":    [l.strip() for l in aprendef.split("\n") if l.strip()],
        "plano_proximo_mes": [
            dict(zip(["acao","canal","impacto_esperado"], l.split("|")))
            for l in plano_pm.split("\n") if "|" in l
        ],
    })
    template_fn = "apresentacao_resultado"

# ════════════════════════════════════════════════════════════════════
elif tipo == "Proposta Comercial":

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">💼 DADOS DA PROPOSTA</div>', unsafe_allow_html=True)
        data_prop = st.text_input("Data da proposta", value=date.today().strftime("%d/%m/%Y"))
        validade  = st.text_input("Validade", value="30 dias")
        verba_m   = st.number_input("Verba de mídia (R$)", value=0.0)
        honr      = st.number_input("Honorários/gestão (R$)", value=0.0)
    with col2:
        st.markdown('<div class="section-title">📝 RESUMO EXECUTIVO</div>', unsafe_allow_html=True)
        frase_resumo   = st.text_input("Frase de resumo", key="fr_c")
        frase_destaque = st.text_input("Frase de destaque", key="fd_c")
        info_capa      = st.text_input("Subtítulo da capa", key="ic_c")

    st.markdown('<div class="section-title">🔍 DIAGNÓSTICO</div>', unsafe_allow_html=True)
    diag = st.text_area("Diagnóstico do cenário atual (1 ponto por linha)", height=100)

    st.markdown('<div class="section-title">🛠️ SERVIÇOS PROPOSTOS</div>', unsafe_allow_html=True)
    n_svc = st.number_input("Quantos serviços?", 1, 10, 3, key="nsvc")
    servicos = []
    for i in range(int(n_svc)):
        c1,c2,c3,c4 = st.columns(4)
        nm_s  = c1.text_input("Serviço", key=f"sn{i}", placeholder="Gestão de Tráfego")
        desc_s = c2.text_input("Descrição", key=f"sd{i}", placeholder="Google + Meta Ads")
        inv_s  = c3.number_input("Valor (R$)", key=f"sv{i}", value=0.0)
        rec_s  = c4.selectbox("Tipo", ["Mensal","Único"], key=f"st{i}")
        servicos.append({"nome": nm_s, "descricao": desc_s, "investimento": inv_s,
                          "recorrente": rec_s == "Mensal"})

    col_a, col_b = st.columns(2)
    with col_a:
        diferenciais = st.text_area("Diferenciais MarkSeg (1 por linha)", height=100)
    with col_b:
        pp_prop = st.text_area("Próximos passos: passo|prazo (1 por linha)", height=100)

    dados.update({
        "frase_resumo":    frase_resumo, "frase_destaque": frase_destaque,
        "info_capa":       info_capa,    "data_proposta": data_prop,
        "validade":        validade,     "verba_midia": verba_m,
        "honorarios":      honr,         "total_mensal": verba_m + honr,
        "diagnostico":     [l.strip() for l in diag.split("\n") if l.strip()],
        "servicos":        servicos,
        "diferenciais":    [l.strip() for l in diferenciais.split("\n") if l.strip()],
        "proximos_passos": [
            dict(zip(["passo","prazo"], l.split("|")))
            for l in pp_prop.split("\n") if "|" in l
        ],
    })
    template_fn = "proposta_comercial"

# ── Botão de geração ──────────────────────────────────────────────────────
st.divider()
col_btn, col_info = st.columns([1, 3])

with col_btn:
    gerar = st.button("⚡ Gerar PDF", use_container_width=True)

if gerar:
    if not cliente:
        st.error("Preencha o nome do cliente antes de gerar.")
    else:
        with st.spinner("Gerando PDF..."):
            try:
                import importlib
                mod = importlib.import_module(f"templates.{template_fn}")

                with tempfile.NamedTemporaryFile(
                    suffix=".pdf", delete=False,
                    prefix=f"markseg_{template_fn}_{cliente.replace(' ','_')}_"
                ) as tmp:
                    output = tmp.name

                mod.gerar(dados, output)

                with open(output, "rb") as f:
                    pdf_bytes = f.read()

                nome_arquivo = (
                    f"MarkSeg_{tipo.replace(' ','_')}_{cliente.replace(' ','_')}"
                    f"_{periodo.replace(' ','_')}.pdf"
                )

                st.success("PDF gerado com sucesso!")
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                )
                os.unlink(output)

            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
                import traceback
                st.code(traceback.format_exc())
