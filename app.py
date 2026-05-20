"""
Agente de Documentos MarkSeg
Interface conversacional — descreva, gere, baixe.
"""

import streamlit as st
import os, sys, tempfile
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agente de Documentos MarkSeg",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

LOGO_PATH = os.path.join(ROOT, "brand", "logo.png")

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
body, .stApp { background: #F5F6FA; }

.header {
    background: #1B3A6B;
    border-radius: 12px;
    padding: 24px 32px;
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 28px;
}
.header h1 {
    color: white;
    font-size: 1.6rem;
    margin: 0;
    font-weight: 800;
}
.header p {
    color: #aab4cc;
    margin: 4px 0 0 0;
    font-size: 0.9rem;
}

.doc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin: 16px 0 24px 0;
}
.doc-card {
    background: white;
    border: 2px solid #E0E3EE;
    border-radius: 10px;
    padding: 16px 12px;
    text-align: center;
    cursor: pointer;
    transition: all 0.15s;
}
.doc-card:hover, .doc-card.selected {
    border-color: #F5821E;
    box-shadow: 0 2px 12px rgba(245,130,30,0.15);
}
.doc-card .icon { font-size: 1.8rem; }
.doc-card .name {
    font-size: 0.78rem;
    font-weight: 700;
    color: #1B3A6B;
    margin-top: 8px;
    line-height: 1.3;
}

.input-box {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    border: 1px solid #E0E3EE;
    margin-bottom: 16px;
}
.input-box h3 {
    color: #1B3A6B;
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0 0 12px 0;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.tip-box {
    background: #EEF2FF;
    border-left: 3px solid #F5821E;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #444;
    margin-bottom: 16px;
}

.stButton > button {
    background: #F5821E !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.65rem 2.5rem !important;
    border-radius: 8px !important;
    width: 100%;
}
.stButton > button:hover {
    background: #D4691A !important;
}

.result-box {
    background: #1B3A6B;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    margin-top: 20px;
}
.result-box h3 { color: #F5821E; margin: 0 0 6px 0; }
.result-box p  { color: #aab4cc; margin: 0; font-size: 0.85rem; }

.stTextArea textarea {
    border-radius: 8px !important;
    border: 1.5px solid #E0E3EE !important;
    font-size: 0.95rem !important;
    min-height: 140px !important;
}
.stTextArea textarea:focus {
    border-color: #F5821E !important;
    box-shadow: 0 0 0 2px rgba(245,130,30,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=120)
with col_title:
    st.markdown("""
    <div style="padding-top:8px">
        <h1 style="color:#1B3A6B;font-size:1.7rem;margin:0;font-weight:800">
            Agente de Documentos
        </h1>
        <p style="color:#888;margin:2px 0 0 0;font-size:0.9rem">
            MarkSeg · Descreva · Gere · Baixe
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Seleção de tipo ───────────────────────────────────────────────────────
TIPOS = {
    "relatorio_performance":    ("📊", "Relatório\nde Performance"),
    "relatorio_social":         ("📱", "Relatório\nMídias Sociais"),
    "plano_de_midia":           ("🗺️",  "Plano de\nMídia"),
    "apresentacao_resultado":   ("📈", "Apresentação\nde Resultado"),
    "proposta_comercial":       ("💼", "Proposta\nComercial"),
}

if "tipo_sel" not in st.session_state:
    st.session_state.tipo_sel = "relatorio_performance"

st.markdown("**Qual documento você quer gerar?**")

cols = st.columns(len(TIPOS))
for col, (key, (icon, nome)) in zip(cols, TIPOS.items()):
    with col:
        selecionado = st.session_state.tipo_sel == key
        border = "#F5821E" if selecionado else "#E0E3EE"
        bg     = "#FFF8F2" if selecionado else "white"
        st.markdown(f"""
        <div style="background:{bg};border:2px solid {border};border-radius:10px;
                    padding:14px 8px;text-align:center;cursor:pointer">
            <div style="font-size:1.6rem">{icon}</div>
            <div style="font-size:0.75rem;font-weight:700;color:#1B3A6B;
                        margin-top:6px;line-height:1.3">{nome}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Selecionar", key=f"btn_{key}",
                     use_container_width=True,
                     type="primary" if selecionado else "secondary"):
            st.session_state.tipo_sel = key
            st.rerun()

tipo_atual = st.session_state.tipo_sel
icon_atual, nome_atual = TIPOS[tipo_atual]

st.divider()

# ── Dica contextual ───────────────────────────────────────────────────────
DICAS = {
    "relatorio_performance": (
        "Fale os números da semana: cliente, período, quanto investiu no Meta e Google, "
        "quantos leads gerou, qual o CPL, quais criativos rodaram e qual foi o melhor. "
        "Pode colar os dados brutos — o agente interpreta tudo."
    ),
    "relatorio_social": (
        "Informe: cliente, período, seguidores novos, alcance, engajamento, "
        "quais posts foram publicados, qual teve melhor resultado e o que planeja para a próxima semana."
    ),
    "plano_de_midia": (
        "Descreva: cliente, investimento mensal, quais canais usar (Google/Meta), "
        "qual o produto principal, período do plano e as metas esperadas."
    ),
    "apresentacao_resultado": (
        "Informe o mês, os resultados gerais (investimento, leads, CPL, ROAS), "
        "o que bateu meta, o que não bateu, e o que vai mudar no próximo mês."
    ),
    "proposta_comercial": (
        "Descreva o cliente, o diagnóstico do cenário atual, quais serviços vai oferecer, "
        "valores de gestão e mídia, e os resultados que pretende entregar."
    ),
}

st.markdown(f"""
<div class="tip-box">
    <b>{icon_atual} {nome_atual.replace(chr(10), ' ')}</b> — {DICAS[tipo_atual]}
</div>
""", unsafe_allow_html=True)

# ── Entrada de dados ──────────────────────────────────────────────────────
st.markdown("**Descreva os dados do documento:**")

descricao = st.text_area(
    label="descricao",
    label_visibility="collapsed",
    placeholder=(
        "Ex: Relatório da semana de 13 a 19 de maio do cliente Faturei Hoje. "
        "Investimos R$ 563 no Meta e R$ 29 no Google. Geramos 51 leads a R$ 4,79 de CPL. "
        "O criativo video15 foi o vencedor com 37 leads a R$ 3,39..."
    ),
    height=180,
    key="descricao_input",
)

# upload de arquivo opcional
with st.expander("📎 Anexar planilha ou CSV com dados (opcional)"):
    arquivo = st.file_uploader("Arraste o arquivo", type=["csv", "xlsx", "txt"],
                                label_visibility="collapsed")
    if arquivo:
        import pandas as pd
        try:
            if arquivo.name.endswith(".csv"):
                df = pd.read_csv(arquivo, sep=None, engine="python")
            else:
                df = pd.read_excel(arquivo)
            st.dataframe(df.head(10), use_container_width=True)
            # adiciona resumo dos dados à descrição
            extra = f"\n\nDADOS DO ARQUIVO ({arquivo.name}):\n{df.to_string(index=False, max_rows=50)}"
            descricao = descricao + extra
        except Exception as e:
            st.warning(f"Não foi possível ler o arquivo: {e}")

st.markdown("")

# ── Botão gerar ───────────────────────────────────────────────────────────
gerar = st.button(f"⚡ Gerar {nome_atual.replace(chr(10), ' ')}",
                   use_container_width=True)

if gerar:
    if not descricao.strip():
        st.error("Descreva os dados do documento antes de gerar.")
    else:
        # verifica API key
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            st.error("ANTHROPIC_API_KEY não configurada. "
                     "Adicione nas configurações de Secrets do Streamlit Cloud.")
            st.stop()

        with st.spinner("Interpretando os dados..."):
            try:
                from agent import extrair_dados
                dados = extrair_dados(tipo_atual, descricao)
            except Exception as e:
                st.error(f"Erro ao interpretar dados: {e}")
                st.stop()

        with st.spinner("Gerando PDF no padrão MarkSeg..."):
            try:
                import importlib
                mod = importlib.import_module(f"templates.{tipo_atual}")

                with tempfile.NamedTemporaryFile(
                    suffix=".pdf", delete=False,
                    prefix=f"markseg_{tipo_atual}_"
                ) as tmp:
                    output = tmp.name

                mod.gerar(dados, output)

                with open(output, "rb") as f:
                    pdf_bytes = f.read()
                os.unlink(output)

                cliente = dados.get("cliente", "cliente")
                periodo = dados.get("periodo", date.today().strftime("%d%m%Y"))
                nome_arquivo = (
                    f"MarkSeg_{nome_atual.replace(chr(10),'_').replace(' ','_')}"
                    f"_{cliente.replace(' ','_')}_{periodo.replace(' ','_')}.pdf"
                )

                st.success("PDF gerado!")
                st.markdown("""
                <div class="result-box">
                    <h3>Documento pronto</h3>
                    <p>Clique no botão abaixo para baixar</p>
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                )

                # mostra preview dos dados extraídos
                with st.expander("🔍 Ver dados interpretados pelo agente"):
                    import json
                    st.json(dados)

            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
                import traceback
                st.code(traceback.format_exc())

# ── Rodapé ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#aaa;font-size:0.75rem'>"
    "MarkSeg · Agente de Documentos · Todos os documentos no padrão da agência"
    "</p>",
    unsafe_allow_html=True
)
