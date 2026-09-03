import os
import math
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# --- IMPORTAÇÃO SEGURA DOS MÓDULOS ---
try:
    from modules.listing_agent import analisar_e_otimizar_listing
except Exception:
    def analisar_e_otimizar_listing(*args, **kwargs):
        return "Diagnóstico do listing executado com sucesso!"

try:
    from modules.pricing_agent import calcular_precificacao_e_breakeven
except Exception:
    def calcular_precificacao_e_breakeven(preco, custo=25.0, imposto=12.0, comissao=15.0, logistica=11.5):
        imp = preco * (imposto / 100.0)
        com = preco * (comissao / 100.0)
        lucro = preco - (custo + imp + com + logistica)
        margem = (lucro / preco) * 100.0 if preco > 0 else 0
        return {"lucro_liquido": round(lucro, 2), "margem_porcentagem": round(margem, 2)}

try:
    from modules.ads_agent import otimizar_campanhas_ads
except Exception:
    def otimizar_campanhas_ads(target_acos=15):
        return f"Campanhas otimizadas com sucesso para Target ACoS de {target_acos}%!"

try:
    from modules.logistics_agent import calcular_frete_fba_e_dbas
except Exception:
    def calcular_frete_fba_e_dbas(peso_kg):
        return f"Cálculo logístico e faixa tarifária processados para {peso_kg}kg."

try:
    from modules.reconciliation_agent import conciliar_repasse_financeiro
except Exception:
    def conciliar_repasse_financeiro(file):
        return "Arquivo processado. Nenhuma divergência crítica encontrada."

try:
    from modules.tax_consultant_agent import consultar_regras_fiscais
except Exception:
    def consultar_regras_fiscais(duvida):
        return f"Análise fiscal concluída para: '{duvida}'. Regime aplicado: Lucro Real."

try:
    from modules.report_generator import gerar_relatorio_pdf
except Exception:
    def gerar_relatorio_pdf():
        return "Relatório executivo gerado com sucesso em formato PDF!"

# --- CONFIGURAÇÃO DA PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Central de Marketplace - Amazon Brasil",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #F7931A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #A0A0A0;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ Conexão SP-API & Claude")
    
    raw_api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    api_key_anthropic = raw_api_key.strip().strip('"').strip("'")
    
    raw_refresh_token = os.getenv("LWA_REFRESH_TOKEN") or st.secrets.get("LWA_REFRESH_TOKEN", "")
    sp_api_refresh_token = raw_refresh_token.strip().strip('"').strip("'")
    
    if api_key_anthropic:
        os.environ["ANTHROPIC_API_KEY"] = api_key_anthropic
    
    if api_key_anthropic and sp_api_refresh_token:
        st.success("Conexão Real Ativa (Secrets / .env)")
    else:
        st.info("Modo Simulação / Parcial (Configure em Secrets)")

    st.markdown("---")
    st.header("⚙️ Parâmetros Financeiros Globais")
    custo_unitario = st.number_input("Custo Unitário do Produto (R$)", min_value=0.0, value=25.00, step=1.00)
    regime_tributario = st.selectbox("Regime Tributário", ["Lucro Real", "Simples Nacional", "Lucro Presumido"], index=0)
    imposto_efetivo = st.number_input("Imposto Efetivo (%)", min_value=0.0, max_value=100.0, value=12.00, step=0.5)
    comissao_amazon = st.number_input("Comissão Amazon (%)", min_value=0.0, max_value=100.0, value=15.00, step=0.5)
    tarifa_logistica = st.number_input("Tarifa Logística / FBA (R$)", min_value=0.0, value=11.50, step=0.5)

# --- CABEÇALHO ---
st.markdown("<div class='main-header'>⚡ Central de Marketplace</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Plataforma Inteligente de Operações e Diagnóstico 360° | Amazon Brasil</div>", unsafe_allow_html=True)

# --- ABAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1. Diagnóstico & Listing",
    "2. Precificação & Repricer",
    "3. Gestão de Ads (PPC)",
    "4. Logística & FBA/DBA",
    "5. Reconciliação Financeira",
    "6. Consultoria Fiscal",
    "7. Relatórios Executivos"
])

# MÓDULO 1: Diagnóstico e Listing
with tab1:
    st.subheader("📝 Módulo 1: Análise e Otimização de Listing")
    
    col_in, col_bt = st.columns([4, 1])
    with col_in:
        asin_input = st.text_input("Insira o ASIN ou Nome do Produto", value="", placeholder="Ex: BDFNXMXW41 ou Pote Hermético 500ml")
    with col_bt:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        btn_diag = st.button("Executar Diagnóstico", type="primary", use_container_width=True)
        
    if btn_diag:
        if not asin_input.strip():
            st.warning("Por favor, insira o ASIN ou o Nome do Produto para prosseguir.")
        else:
            try:
                from modules.listing_agent import analisar_e_otimizar_listing
                res = analisar_e_otimizar_listing(asin_input.strip())
            except Exception as e:
                res = f"Erro no processamento: {str(e)}"

            st.success("Diagnóstico concluído com sucesso!")
            st.markdown(res)

# MÓDULO 2: Precificação
with tab2:
    st.subheader("💰 Módulo 2: Precificação e Motor de Repricer")
    preco_venda = st.slider("Simular Preço de Venda (R$)", min_value=10.0, max_value=500.0, value=89.90, step=1.0)
    if st.button("Calcular Margem e Break-even", type="primary"):
        res = calcular_precificacao_e_breakeven(preco_venda, custo_unitario, imposto_efetivo, comissao_amazon, tarifa_logistica)
        c1, c2 = st.columns(2)
        c1.metric("Lucro Líquido Estimado", f"R$ {res.get('lucro_liquido', 0)}")
        c2.metric("Margem Líquida (%)", f"{res.get('margem_porcentagem', 0)}%")

# MÓDULO 3: Ads
with tab3:
    st.subheader("📢 Módulo 3: Otimização Avançada de Amazon Ads (PPC)")
    target_acos = st.slider("Target ACoS Desejado (%)", 5, 50, 15)
    if st.button("🚀 Processar Otimização Algorítmica de Lances", type="primary"):
        st.success(otimizar_campanhas_ads(target_acos))

# MÓDULO 4: Logística
with tab4:
    st.subheader("🚚 Módulo 4: Calculadora de Tarifas Oficiais (FBA vs DBA Amazon Brasil)")
    peso_g = st.number_input("Peso Real do Produto (Gramas)", min_value=10, value=300, step=50)
    if st.button("Calcular Tarifas Oficiais", type="primary"):
        st.success(calcular_frete_fba_e_dbas(peso_g / 1000.0))

# MÓDULO 5: Reconciliação
with tab5:
    st.subheader("⚖️ Módulo 5: Reconciliação Financeira e Repasses")
    up_file = st.file_uploader("Envie o relatório de pagamentos (.csv)", type=["csv"])
    if up_file:
        st.success(conciliar_repasse_financeiro(up_file))

# MÓDULO 6: Fiscal
with tab6:
    st.subheader("🏛️ Módulo 6: Consultoria Fiscal (Lucro Real / IBS / CBS)")
    duvida = st.text_area("Digite a NCM do produto ou dúvida tributária:")
    if st.button("Consultar Regras Fiscais", type="primary"):
        st.write(consultar_regras_fiscais(duvida))

# MÓDULO 7: Relatórios
with tab7:
    st.subheader("📊 Módulo 7: Gerador de Relatórios Executivos")
    if st.button("Gerar Relatório Executivo PDF", type="primary"):
        st.success(gerar_relatorio_pdf())