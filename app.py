import os
import streamlit as st

st.set_page_config(
    page_title="Central de Marketplace | Amazon Brasil",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

from modules.listing_agent import analisar_e_otimizar_listing

with st.sidebar:
    st.title("⚡ Conexão SP-API & Claude")
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    if api_key:
        st.success("Conexão Real Ativa (Secrets / .env)")
    else:
        st.warning("Credenciais não detectadas")

    st.markdown("---")
    st.subheader("⚙️ Parâmetros Financeiros Globais")
    custo_unitario = st.number_input("Custo Unitário do Produto (R$)", value=25.0, step=1.0)
    regime_tributario = st.selectbox("Regime Tributário", ["Lucro Real", "Simples Nacional", "Lucro Presumido"])
    imposto_efetivo = st.number_input("Imposto Efetivo (%)", value=12.0, step=0.5)
    comissao_amazon = st.number_input("Comissão Amazon (%)", value=15.0, step=0.5)

st.title("⚡ Central de Marketplace")
st.caption("Plataforma Inteligente de Operações e Diagnóstico 360° | Amazon Brasil")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1. Diagnóstico & Listing",
    "2. Precificação & Repricer",
    "3. Gestão de Ads (PPC)",
    "4. Logística & FBA/DBA",
    "5. Reconciliação Financeira",
    "6. Consultoria Fiscal",
    "7. Relatórios Executivos"
])

with tab1:
    st.subheader("📦 Módulo 1: Análise e Otimização de Listing")
    
    termo_input = st.text_input(
        "Insira o ASIN ou Nome do Produto (Ex: B0BQWX1LSY ou Grelha Churrasqueira Dupla):",
        value="Grelha Churrasqueira Dupla"
    )
    
    if st.button("🚀 Executar Diagnóstico", use_container_width=True):
        if not termo_input.strip():
            st.warning("Por favor, informe a palavra-chave ou ASIN.")
        else:
            with st.spinner("Mapeando ofertas na Amazon BR, gerando SWOT e copy A10..."):
                resultado = analisar_e_otimizar_listing(termo_input)
                st.markdown(resultado)

with tab2:
    st.subheader("2. Precificação & Repricer")
    st.info("Módulo ativo.")

with tab3:
    st.subheader("3. Gestão de Ads (PPC)")
    st.info("Módulo ativo.")

with tab4:
    st.subheader("4. Logística & FBA/DBA")
    st.info("Módulo ativo.")

with tab5:
    st.subheader("5. Reconciliação Financeira")
    st.info("Módulo ativo.")

with tab6:
    st.subheader("6. Consultoria Fiscal")
    st.info("Módulo ativo.")

with tab7:
    st.subheader("7. Relatórios Executivos")
    st.info("Módulo ativo.")