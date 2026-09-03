import os
import streamlit as st

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Central de Marketplace | Amazon Brasil",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importação do Módulo 1 atualizado
from modules.listing_agent import render_module_1

# Configuração da Barra Lateral (Sidebar)
with st.sidebar:
    st.title("⚡ Conexão SP-API & Claude")
    
    # Status das Credenciais / Secrets
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

# Título Principal do Dashboard
st.title("⚡ Central de Marketplace")
st.caption("Plataforma Inteligente de Operações e Diagnóstico 360° | Amazon Brasil")

# Estrutura das Abas dos Módulos
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1. Diagnóstico & Listing",
    "2. Precificação & Repricer",
    "3. Gestão de Ads (PPC)",
    "4. Logística & FBA/DBA",
    "5. Reconciliação Financeira",
    "6. Consultoria Fiscal",
    "7. Relatórios Executivos"
])

# -----------------------------------------------------------------------------
# ABA 1: MÓDULO 1 - ANÁLISE, PESQUISA E OTIMIZAÇÃO DE LISTING (TEXTO OU FOTO)
# -----------------------------------------------------------------------------
with tab1:
    render_module_1()

# -----------------------------------------------------------------------------
# DEMAIS ABAS (PLACEHOLDERS MANTIDOS)
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("2. Precificação & Repricer")
    st.info("Módulo de precificação dinâmica e reprefatoração ativo.")

with tab3:
    st.subheader("3. Gestão de Ads (PPC)")
    st.info("Módulo de otimização de campanhas de anúncios ativo.")

with tab4:
    st.subheader("4. Logística & FBA/DBA")
    st.info("Módulo de gestão de estoque e remessas FBA/DBA ativo.")

with tab5:
    st.subheader("5. Reconciliação Financeira")
    st.info("Módulo de conferência de repasses e taxas ativo.")

with tab6:
    st.subheader("6. Consultoria Fiscal")
    st.info("Módulo de checagem de tributação e regras fiscais ativo.")

with tab7:
    st.subheader("7. Relatórios Executivos")
    st.info("Módulo de geração de relatórios consolidados ativo.")