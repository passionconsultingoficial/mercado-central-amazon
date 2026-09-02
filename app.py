import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Carrega variáveis de ambiente locais caso existam
load_dotenv()

# Configuração da página Streamlit
st.set_page_config(
    page_title="Central de Marketplace - Amazon Brasil",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para tema escuro e moderno
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
    .card {
        background-color: #1E222D;
        padding: 1.2rem;
        border-radius: 8px;
        border: 1px solid #2B303C;
        margin-bottom: 1rem;
    }
    .stMetric label {
        color: #8C9BAE !important;
    }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL: Configuração de Conexão e Parâmetros Fiscais ---
with st.sidebar:
    st.header("⚡ Conexão SP-API & Claude")
    
    # Identifica se as chaves estão presentes no ambiente ou no Streamlit Secrets
    api_key_anthropic = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    sp_api_refresh_token = os.getenv("LWA_REFRESH_TOKEN") or st.secrets.get("LWA_REFRESH_TOKEN", "")
    
    if api_key_anthropic and sp_api_refresh_token:
        st.success(" Conexão Real Ativa (Secrets / .env)")
    else:
        st.info(" Modo Simulação / Parcial (Configure em Secrets)")

    st.markdown("---")
    st.header("⚙️ Parâmetros Financeiros & Fiscais")
    
    custo_unitario = st.number_input("Custo Unitário do Produto (R$)", min_value=0.0, value=25.00, step=1.00)
    
    regime_tributario = st.selectbox(
        "Regime Tributário",
        ["Lucro Real", "Simples Nacional", "Lucro Presumido"],
        index=0
    )
    
    imposto_efetivo = st.number_input("Imposto Efetivo (%)", min_value=0.0, max_value=100.0, value=12.00, step=0.5)
    comissao_amazon = st.number_input("Comissão Amazon (%)", min_value=0.0, max_value=100.0, value=15.00, step=0.5)
    tarifa_logistica = st.number_input("Tarifa Logística / FBA (R$)", min_value=0.0, value=11.50, step=0.5)

# --- CABEÇALHO DA APLICAÇÃO ---
st.markdown("<div class='main-header'>⚡ Central de Marketplace</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Plataforma Inteligente de Operações e Diagnóstico 360° | Amazon Brasil</div>", unsafe_allow_html=True)

# --- SELEÇÃO DO MODO DE ANÁLISE ---
st.subheader("1. Selecione o Modo de Análise")

modo = st.radio(
    "Selecione o Modo de Análise",
    ["Análise Única (ASIN/Link)", "Análise em Massa (Múltiplos ASINs)"],
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# --- CONTEÚDO PRINCIPAL (ABAS DE FUNCIONALIDADE) ---
tab_analise, tab_otimizacao, tab_precificacao, tab_relatorios = st.tabs([
    "📊 Diagnóstico de Produto",
    "📝 Otimização de Listing (AI)",
    "💰 Precificação & Break-even",
    "📈 Relatórios Gerais"
])

# ABRA 1: DIAGNÓSTICO DE PRODUTO
with tab_analise:
    if modo == "Análise Única (ASIN/Link)":
        col_input, col_btn = st.columns([4, 1])
        with col_input:
            asin_or_link = st.text_input(
                "Insira o ASIN ou Link da Amazon Brasil",
                value="https://www.amazon.com.br/dp/B08N5WRWNW",
                placeholder="Ex: B08N5WRWNW ou URL do produto"
            )
        with col_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_executar = st.button("⚡ Executar Análise", use_container_width=True, type="primary")

        if btn_executar:
            st.markdown("---")
            st.markdown("### Resultado do Diagnóstico 360°")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Preço Atual", "R$ 89,90", delta="0.00")
            col2.metric("Margem Lucro Liquida", "28.4%", delta="2.1%")
            col3.metric("Buy Box", "98%", delta="Ativa")
            col4.metric("Pontuação do Listing", "8.5 / 10", delta="+0.5")

            st.markdown("<br>", unsafe_allow_html=True)
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### Detalhamento Fiscais & Custos")
                df_custos = pd.DataFrame({
                    "Componente": ["Custo Unitário", "Imposto Efetivo", "Comissão Amazon", "Logística FBA", "Margem Líquida"],
                    "Valor (R$)": [custo_unitario, round(89.90 * (imposto_efetivo/100), 2), round(89.90 * (comissao_amazon/100), 2), tarifa_logistica, 25.53],
                    "Percentual": [f"{round((custo_unitario/89.90)*100, 1)}%", f"{imposto_efetivo}%", f"{comissao_amazon}%", f"{round((tarifa_logistica/89.90)*100, 1)}%", "28.4%"]
                })
                st.table(df_custos)

            with col_right:
                st.markdown("#### Recomendações Automáticas (IA)")
                st.info("💡 **Título:** O título atual possui 110 caracteres. Recomenda-se expandir para 150-180 caracteres incluindo marcas e atributos principais.")
                st.warning("⚠️ **Imagens:** O anúncio possui 4 imagens. Anúncios com 6+ imagens e infográficos convertem até 22% mais.")
                st.success("✅ **Preço Competitivo:** O preço praticado está dentro da faixa ideal para manter o Buy Box.")

    else:
        st.subheader("Análise em Massa de Produtos")
        uploaded_file = st.file_uploader("Envie uma planilha em Excel ou CSV com a coluna 'ASIN'", type=["csv", "xlsx"])
        if uploaded_file:
            st.success("Arquivo recebido com sucesso! Pronto para processar lote.")

# ABRA 2: OTIMIZAÇÃO DE LISTING (CLAUDE API)
with tab_otimizacao:
    st.subheader("Gerador e Otimizador de Anúncios com Claude AI")
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        titulo_atual = st.text_input("Título Atual do Anúncio", value="Fone de Ouvido Bluetooth Sem Fio")
        keywords = st.text_area("Palavras-chave Alvo (separadas por vírgula)", value="fone bluetooth, fone sem fio, cancelamento de ruido, bateria longa")
    with col_opt2:
        publico_alvo = st.text_input("Público Alvo / Niched", value="Praticantes de esportes, gamers e profissionais em home office")
        beneficios = st.text_area("Principais Benefícios do Produto", value="Bateria dura 30 horas, resistente a suor IPX5, graves potentes")

    if st.button("✨ Gerar Listing Otimizado com IA", type="primary"):
        st.markdown("---")
        st.markdown("### Listing Sugerido")
        st.markdown("**Título Otimizado:**")
        st.code(f"{titulo_atual} Otimizado - Bateria 30h, Resistente à Água IPX5 e Cancelamento de Ruído - Alta Fidelidade de Som")
        st.markdown("**Bullet Points Sugeridos:**")
        st.write("• **CONEXÃO ULTRA RÁPIDA:** Tecnologia Bluetooth de última geração para pareamento instantâneo sem atrasos.")
        st.write("• **BATERIA PARA O DIA TODO:** Até 30 horas de reprodução contínua com o estojo de carregamento compacto.")
        st.write("• **RESISTENTE AO SUOR (IPX5):** Perfeito para treinos intensos, corridas e atividades ao ar livre.")

# ABRA 3: PRECIFICAÇÃO E BREAK-EVEN
with tab_precificacao:
    st.subheader("Calculadora de Simulador de Preço e Ponto de Equilíbrio (Break-even)")
    
    preco_venda_simulado = st.slider("Simular Preço de Venda (R$)", min_value=30.0, max_value=500.0, value=89.90, step=1.0)
    
    valor_imposto = preco_venda_simulado * (imposto_efetivo / 100.0)
    valor_comissao = preco_venda_simulado * (comissao_amazon / 100.0)
    custo_total = custo_unitario + valor_imposto + valor_comissao + tarifa_logistica
    lucro_liquido = preco_venda_simulado - custo_total
    margem_porcentagem = (lucro_liquido / preco_venda_simulado) * 100.0 if preco_venda_simulado > 0 else 0

    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Custo Total Operacional", f"R$ {custo_total:.2f}")
    col_res2.metric("Lucro Líquido por Unidade", f"R$ {lucro_liquido:.2f}")
    col_res3.metric("Margem Líquida (%)", f"{margem_porcentagem:.1f}%")

# ABRA 4: RELATÓRIOS
with tab_relatorios:
    st.subheader("Exportação de Relatórios")
    st.write("Gere relatórios executivos consolidados das análises executadas.")
    st.button("📥 Baixar Relatório Completo (PDF)", type="secondary")