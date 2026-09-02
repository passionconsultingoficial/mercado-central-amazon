import streamlit as st
import json
import pandas as pd
from modules.scraper_agent import obter_dados_anuncio_amazon, processar_lote_asins
from modules.listing_agent import analisar_e_otimizar_listing
from modules.pricing_agent import calcular_precificacao_e_breakeven
from modules.promotions_agent import analisar_viabilidade_promocao
from modules.logistics_agent import comparar_modalidades_logisticas
from modules.ads_agent import otimizar_campanha_ppc
from modules.tax_consultant_agent import analisar_planejamento_fiscal
from modules.reconciliation_agent import auditar_conciliacao_extrato
from modules.amazon_spapi import AmazonSPAPIClient
from modules.report_generator import gerar_pdf_diagnostico
from database import init_db, salvar_analise, listar_historico_asin, buscar_analise_por_id

# Inicializa banco de dados e cliente da SP-API
init_db()
sp_api = AmazonSPAPIClient()

st.set_page_config(
    page_title="Central de Marketplace | IA Ops",
    page_icon="⚡",
    layout="wide"
)

# --- ESTILIZAÇÃO CSS AVANÇADA (SAAS DARK THEME) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    section[data-testid="stSidebar"] label, .stMarkdown label, p, span { color: #e6edf3 !important; font-weight: 500 !important; }
    h1, h2, h3, h4 { color: #f0f6fc !important; font-weight: 600 !important; }
    div[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 16px; }
    div[data-testid="stMetricLabel"] p { color: #8b949e !important; font-size: 13px !important; }
    div[data-testid="stMetricValue"] div { color: #58a6ff !important; font-size: 24px !important; font-weight: 700 !important; }
    .stButton>button, .stDownloadButton>button { width: 100%; background-color: #238636; color: #ffffff !important; font-weight: 600; border-radius: 8px; border: 1px solid rgba(240,246,252,0.1); padding: 8px 16px; }
    .stButton>button:hover, .stDownloadButton>button:hover { background-color: #2ea043; border-color: #3fb950; }
    button[data-baseweb="tab"] { background-color: transparent !important; color: #8b949e !important; font-weight: 600 !important; }
    button[aria-selected="true"] { color: #58a6ff !important; border-bottom: 2px solid #58a6ff !important; }
    .stTextInput input, .stNumberInput input, .stSelectbox div { background-color: #0d1117 !important; color: #f0f6fc !important; border: 1px solid #30363d !important; border-radius: 6px !important; }
    button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] { background-color: #21262d !important; color: #c9d1d9 !important; }
    .badge-api-off { background-color: #388bfd15; color: #58a6ff; border: 1px solid #1f6beb; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    .badge-api-on { background-color: #23863615; color: #3fb950; border: 1px solid #238636; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Central de Marketplace")
st.caption("Plataforma Inteligente de Operações e Diagnóstico 360° | Amazon Brasil")

# --- BARRA LATERAL ---
st.sidebar.markdown("### 🔑 Conexão SP-API Amazon")
if sp_api.client_id:
    st.sidebar.markdown('<span class="badge-api-on">● SP-API Conectada</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="badge-api-off">○ Modo Simulação (Sem .env)</span>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Parâmetros Financeiros")
custo_unitario_padrao = st.sidebar.number_input("Custo Unitário (R$)", value=25.0)
regime_tributario = st.sidebar.selectbox("Regime Tributário", ["Lucro Real", "Simples Nacional", "Lucro Presumido"])
imposto_pct = st.sidebar.number_input("Imposto Efetivo (%)", value=12.0)
comissao_pct = st.sidebar.number_input("Comissão Amazon (%)", value=15.0)
tarifa_fixa = st.sidebar.number_input("Tarifa Logística (R$)", value=11.50)
margem_alvo = st.sidebar.number_input("Margem Alvo (%)", value=20.0)

st.markdown("#### 1. Selecione o Modo de Análise")
modo = st.radio("", ["Análise Única (ASIN/Link)", "Análise em Massa (Múltiplos ASINs)"], horizontal=True)

st.markdown("---")

if modo == "Análise Única (ASIN/Link)":
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        url_ou_asin = st.text_input("URL ou ASIN do Anúncio", value="https://www.amazon.com.br/dp/B08N5WRWNW", label_visibility="collapsed")
    with col_btn:
        btn_executar = st.button("⚡ Executar Análise")

    if btn_executar:
        with st.spinner("Processando dados e consultando agentes de IA..."):
            dados_anuncio = obter_dados_anuncio_amazon(url_ou_asin)

            if "erro" in dados_anuncio:
                st.error(dados_anuncio["erro"])
            else:
                sku = dados_anuncio["asin"]
                nome_produto = dados_anuncio["titulo"]
                preco_buy_box = dados_anuncio["preco_buy_box"]
                bullets = "\n".join(dados_anuncio["bullet_points"])

                resumo_spapi = sp_api.obter_resumo_vendas(dias=30)
                liquidacao_spapi = sp_api.obter_relatorio_liquidacao()

                vendas_brutas = liquidacao_spapi.get("total_bruto_rs", 15400.00)
                qtd_pedidos = resumo_spapi.get("pedidos_totais", 220)
                repasse_liquido = liquidacao_spapi.get("repasse_liquido_rs", 11220.00)

                campanha_ppc = {
                    "nome_campanha": f"SP_Exact_{sku}", "acos_meta_pct": 18.0, "acos_atual_pct": 27.4,
                    "investimento_rs": 450.00, "vendas_rs": 1642.34, "cpc_medio_rs": 1.41,
                    "palavras_chave": [
                        {"termo": "maleta de ferramentas", "acos_pct": 14.2, "cpc": 1.35, "vendas_rs": 1100.00},
                        {"termo": "caixa organizadora plastica", "acos_pct": 38.5, "cpc": 1.60, "vendas_rs": 300.00}
                    ]
                }
                dados_fiscais = {
                    "sku": sku, "regime_tributario": regime_tributario, "preco_venda_rs": preco_buy_box,
                    "custo_aquisicao_rs": custo_unitario_padrao, "aliquota_pis_cofins_debito_pct": 9.25,
                    "credito_pis_cofins_compras_pct": 9.25, "comissao_amazon_rs": preco_buy_box * (comissao_pct / 100),
                    "tarifa_frete_dba_rs": 8.50, "uf_origem": "SP", "uf_destino": "RJ"
                }
                extrato_conciliacao = {
                    "periodo": "Último ciclo (30 dias)", 
                    "total_vendas_brutas_rs": vendas_brutas, 
                    "quantidade_pedidos": qtd_pedidos,
                    "tarifas_comissao_retidas_rs": vendas_brutas * (comissao_pct / 100), 
                    "tarifas_logistica_retidas_rs": vendas_brutas * 0.12,
                    "custo_ads_retido_fatura_rs": 1250.00, 
                    "devolucoes_reembolsos_rs": 350.00,
                    "repasse_liquido_depositado_rs": repasse_liquido, 
                    "repasse_liquido_esperado_rs": repasse_liquido
                }

                res_seo = analisar_e_otimizar_listing(nome_produto, bullets, "Nossa Versão Private Label")
                res_precificacao = calcular_precificacao_e_breakeven({
                    "sku": sku, "custo_produto_com_imposto": custo_unitario_padrao,
                    "regime_tributario": regime_tributario, "aliquota_imposto_efetiva_pct": imposto_pct,
                    "comissao_amazon_pct": comissao_pct, "tarifa_fixa_fba_dba": tarifa_fixa,
                    "margem_liquida_alvo_pct": margem_alvo, "preco_buy_box_atual": preco_buy_box
                })
                res_promocoes = analisar_viabilidade_promocao({
                    "sku": sku, "preco_atual": preco_buy_box, "custo_total_operacional": custo_unitario_padrao + tarifa_fixa,
                    "tipo_promocao": "Cupom %", "desconto_proposto_pct": 10.0, "taxa_fixa_criacao_cupom_amazon": 2.00, "margem_minima_seguranca_pct": 10.0
                })
                res_logistica = comparar_modalidades_logisticas({
                    "sku": sku, "peso_kg": 0.85, "dimensoes_cm": {"comprimento": 30, "largura": 20, "altura": 15},
                    "preco_venda": preco_buy_box, "estimativa_custo_dba": 8.50, "estimativa_custo_fba": 11.20, "estimativa_envio_proprio": 15.00
                })
                res_ads = otimizar_campanha_ppc(campanha_ppc)
                res_fiscal = analisar_planejamento_fiscal(dados_fiscais)
                res_conciliacao = auditar_conciliacao_extrato(extrato_conciliacao)

                pacote_resultados = {
                    "seo": res_seo, "precificacao": res_precificacao, "promocoes": res_promocoes,
                    "logistica": res_logistica, "ads": res_ads, "fiscal": res_fiscal, "conciliacao": res_conciliacao
                }
                salvar_analise(sku, preco_buy_box, custo_unitario_padrao, margem_alvo, regime_tributario, pacote_resultados)

                st.session_state["resultado_atual"] = pacote_resultados
                st.session_state["sku_atual"] = sku
                st.session_state["preco_atual"] = preco_buy_box

    # EXIBIÇÃO DOS RESULTADOS
    if "resultado_atual" in st.session_state:
        res = st.session_state["resultado_atual"]
        sku = st.session_state.get("sku_atual", "N/A")
        preco_buy_box = st.session_state.get("preco_atual", 0.0)

        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
        c1.metric("ASIN Alvo", sku)
        c2.metric("Preço Buy Box", f"R$ {preco_buy_box:.2f}")
        c3.metric("Custo Unitário", f"R$ {custo_unitario_padrao:.2f}")
        c4.metric("Regime Tributário", regime_tributario)
        
        with c5:
            st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
            pdf_bytes = gerar_pdf_diagnostico(sku, preco_buy_box, custo_unitario_padrao, regime_tributario, res)
            st.download_button(
                label="📄 Baixar PDF 360°",
                data=pdf_bytes,
                file_name=f"Diagnostico_360_{sku}.pdf",
                mime="application/pdf"
            )

        st.markdown("---")

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📝 SEO & Listing", "💰 Precificação", "🏷️ Promoções", "🚚 Logística", "🎯 Amazon Ads", "⚖️ Fiscal", "📊 Conciliação", "📜 Histórico"
        ])
        
        with tab1: st.markdown(res.get("seo", "Sem dados"))
        with tab2: st.markdown(res.get("precificacao", "Sem dados"))
        with tab3: st.markdown(res.get("promocoes", "Sem dados"))
        with tab4: st.markdown(res.get("logistica", "Sem dados"))
        with tab5: st.markdown(res.get("ads", "Sem dados"))
        with tab6: st.markdown(res.get("fiscal", "Sem dados"))
        with tab7: st.markdown(res.get("conciliacao", "Sem dados"))
        with tab8:
            st.subheader(f"Histórico de Registros para {sku}")
            historico = listar_historico_asin(sku)
            if historico:
                for h in historico:
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        st.caption(f"**ID #{h[0]}** | Data: {h[1]} | Buy Box: R$ {h[2]:.2f} | Custo: R$ {h[3]:.2f} | Regime: {h[4]}")
                    with col_h2:
                        if st.button(f"🔄 Recarregar #{h[0]}", key=f"btn_{h[0]}"):
                            dados_salvos = buscar_analise_por_id(h[0])
                            if dados_salvos:
                                st.session_state["resultado_atual"] = dados_salvos
                                st.rerun()
            else:
                st.info("Nenhum registro localizado.")

else:
    st.subheader("Processamento de Lista em Lote")
    texto_asins = st.text_area("Insira os ASINs ou Links (um por linha):", value="B08N5WRWNW\nB09X123456")
    btn_lote = st.button("🚀 Processar Lote")

    if btn_lote:
        linhas = [l.strip() for l in texto_asins.split("\n") if l.strip()]
        with st.spinner(f"Processando {len(linhas)} itens..."):
            resultados_lote = processar_lote_asins(linhas)
            df_resumo = pd.DataFrame(resultados_lote)
            st.dataframe(df_resumo[["asin", "titulo", "preco_buy_box", "status"]], use_container_width=True)
            
            for item in resultados_lote:
                if "asin" in item:
                    salvar_analise(
                        asin=item["asin"],
                        preco_buy_box=item.get("preco_buy_box", 0.0),
                        custo_unitario=custo_unitario_padrao,
                        margem_alvo=margem_alvo,
                        regime_tributario=regime_tributario,
                        resultado_dict={"status": item.get("status", "sucesso")}
                    )
            st.success("Lote concluído e salvo no banco de dados!")