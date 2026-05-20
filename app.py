"""
Agente de Documentos MarkSeg
Upload de arquivos + texto → PDF no padrão da agência.
"""

import streamlit as st
import os, sys, tempfile, json
import pandas as pd
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

LOGO_PATH = os.path.join(ROOT, "brand", "logo.png")

st.set_page_config(
    page_title="Agente de Documentos MarkSeg",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Base ── */
.stApp { background: #F5F6FA; }
h1, h2, h3 { color: #1B3A6B !important; font-weight: 800 !important; }

.sec-title {
    background: #1B3A6B; color: white; border-radius: 8px;
    padding: 8px 14px; font-weight: 700; font-size: 0.82rem;
    letter-spacing: 0.05em; margin: 20px 0 10px 0;
}
.tip {
    background: #FFF8F2; border-left: 3px solid #F5821E;
    border-radius: 0 8px 8px 0; padding: 10px 14px;
    font-size: 0.82rem; color: #555; margin-bottom: 16px;
    line-height: 1.5;
}

/* ── Botão principal ── */
.stButton > button {
    background: #F5821E !important; color: white !important;
    border: none !important; font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    border-radius: 8px !important; width: 100%;
    min-height: 48px;          /* touch-friendly */
}
.stButton > button:hover { background: #D4691A !important; }

/* botões secundários (Selecionar) */
button[kind="secondary"] {
    font-size: 0.75rem !important;
    padding: 0.3rem 0.5rem !important;
    min-height: 32px !important;
}

/* ── Upload ── */
div[data-testid="stFileUploader"] {
    border: 2px dashed #E0E3EE !important;
    border-radius: 10px !important; padding: 8px !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    border-radius: 8px !important;
    border: 1.5px solid #E0E3EE !important;
    font-size: 0.95rem !important;
    padding: 10px 12px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #F5821E !important;
    box-shadow: 0 0 0 2px rgba(245,130,30,0.15) !important;
}
.stTextArea textarea { min-height: 130px !important; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    border-radius: 8px !important;
    border: 1.5px solid #E0E3EE !important;
    font-size: 0.95rem !important;
}

/* ── Mobile ── */
@media (max-width: 640px) {
    .sec-title { font-size: 0.75rem; padding: 7px 10px; }
    .tip        { font-size: 0.8rem; padding: 8px 10px; }
    .stButton > button { font-size: 0.95rem !important; min-height: 52px; }

    /* empilha colunas do header em mobile */
    [data-testid="column"] { min-width: 100% !important; }

    /* espaçamento geral menor */
    .block-container { padding-left: 12px !important; padding-right: 12px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
c1, c2 = st.columns([1, 5])
with c1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
with c2:
    st.markdown("## Agente de Documentos MarkSeg")
    st.caption("Suba os arquivos ou descreva os dados · gere o PDF no padrão da agência")

st.divider()

# ── Tipo de documento ─────────────────────────────────────────────────────
TIPOS = {
    "📊  Relatório de Performance (Meta + Google)": "relatorio_performance",
    "📱  Relatório de Mídias Sociais":               "relatorio_social",
    "🗺️   Plano de Mídia":                            "plano_de_midia",
    "📈  Apresentação de Resultado Mensal":           "apresentacao_resultado",
    "💼  Proposta Comercial":                         "proposta_comercial",
    "🧭  Planejamento Estratégico":                   "planejamento_estrategico",
}

tipo_label = st.selectbox("**Tipo de documento**", list(TIPOS.keys()))
tipo = TIPOS[tipo_label]

# ── Dados básicos ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">DADOS DO DOCUMENTO</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
cliente     = c1.text_input("Cliente", placeholder="Ex: Faturei Hoje")
periodo     = c2.text_input("Período", placeholder="Ex: 13–19 Mai 2026")
responsavel = c3.text_input("Responsável", value="Rafael")

# ── Upload de arquivos ────────────────────────────────────────────────────
st.markdown('<div class="sec-title">ARQUIVOS COM OS DADOS</div>', unsafe_allow_html=True)
st.markdown('<div class="tip">Suba os relatórios exportados das plataformas (Meta Ads, Google Ads, planilhas). Pode subir vários arquivos de uma vez.</div>', unsafe_allow_html=True)

arquivos = st.file_uploader(
    "Arraste os arquivos aqui",
    type=["csv", "xlsx", "xls", "pdf", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

# preview dos arquivos
dfs = {}
textos_extras = []
if arquivos:
    for arq in arquivos:
        try:
            if arq.name.endswith(".csv"):
                df = pd.read_csv(arq, sep=None, engine="python", on_bad_lines="skip")
                dfs[arq.name] = df
                with st.expander(f"📄 {arq.name}", expanded=False):
                    st.dataframe(df, use_container_width=True, height=200)
            elif arq.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(arq)
                dfs[arq.name] = df
                with st.expander(f"📄 {arq.name}", expanded=False):
                    st.dataframe(df, use_container_width=True, height=200)
            elif arq.name.endswith(".pdf"):
                import pypdf
                reader = pypdf.PdfReader(arq)
                texto = "\n".join(p.extract_text() or "" for p in reader.pages)
                textos_extras.append(f"[{arq.name}]\n{texto}")
                with st.expander(f"📄 {arq.name}", expanded=False):
                    st.text(texto[:1000] + ("..." if len(texto) > 1000 else ""))
            elif arq.name.endswith(".txt"):
                texto = arq.read().decode("utf-8", errors="ignore")
                textos_extras.append(f"[{arq.name}]\n{texto}")
        except Exception as e:
            st.warning(f"{arq.name}: {e}")

# ── Campo de texto livre ──────────────────────────────────────────────────
st.markdown('<div class="sec-title">INFORMAÇÕES ADICIONAIS</div>', unsafe_allow_html=True)
st.markdown('<div class="tip">Adicione contexto, insights, recomendações, frases de resumo — qualquer dado que não esteja nos arquivos.</div>', unsafe_allow_html=True)

texto_livre = st.text_area(
    "Descreva aqui",
    label_visibility="collapsed",
    placeholder=(
        "Ex: Criativo video15 foi o vencedor com CPL R$ 3,39. "
        "Próximos passos: escalar budget em R$ 30/dia. "
        "Frase resumo: 'Google capta, Meta reaquece.'"
    ),
    height=150,
)

st.markdown("")

# ── Gerar ─────────────────────────────────────────────────────────────────
gerar = st.button("⚡ Gerar PDF")

if gerar:
    if not cliente:
        st.error("Preencha o nome do cliente.")
        st.stop()

    with st.spinner("Processando arquivos e gerando PDF..."):
        try:
            from parsers import montar_dados
            import importlib

            dados = montar_dados(
                tipo=tipo,
                cliente=cliente,
                periodo=periodo,
                responsavel=responsavel,
                dfs=dfs,
                textos=textos_extras,
                texto_livre=texto_livre,
            )

            mod = importlib.import_module(f"templates.{tipo}")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False,
                                             prefix=f"markseg_{tipo}_") as tmp:
                output = tmp.name
            mod.gerar(dados, output)

            with open(output, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(output)

            nome_arquivo = (
                f"MarkSeg_{tipo}_{cliente.replace(' ','_')}"
                f"_{periodo.replace(' ','_')}.pdf"
            )

            st.success("PDF gerado com sucesso!")
            st.download_button(
                "⬇️ Baixar PDF",
                data=pdf_bytes,
                file_name=nome_arquivo,
                mime="application/pdf",
                use_container_width=True,
            )

            with st.expander("🔍 Dados extraídos"):
                st.json(dados)

        except Exception as e:
            st.error(f"Erro: {e}")
            import traceback
            st.code(traceback.format_exc())

st.markdown("---")
st.caption("MarkSeg · Agente de Documentos · Todos os documentos no padrão da agência")
