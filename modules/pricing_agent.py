from modules.tax_engine import calcular_impostos_lucro_real
from modules.repricer_engine import executar_simulacao_repricer

def calcular_precificacao_e_breakeven(dados):
    sku = dados.get("sku", "N/A")
    cost = dados.get("custo_produto_com_imposto", 25.0)
    regime = dados.get("regime_tributario", "Lucro Real")
    comissao_pct = dados.get("comissao_amazon_pct", 15.0)
    tarifa_fba = dados.get("tarifa_fixa_fba_dba", 11.50)
    preco_atual = dados.get("preco_buy_box_atual", 69.90)
    margem_alvo_pct = dados.get("margem_liquida_alvo_pct", 20.0)

    # Executa Simulação do Repricer
    concorrentes_simulados = [preco_atual, preco_atual - 2.00, preco_atual + 5.00]
    res_repricer = executar_simulacao_repricer(
        preco_buy_box_atual=preco_atual,
        custo_aquisicao_rs=cost,
        concorrentes_precos=concorrentes_simulados,
        margem_minima_seguranca_pct=10.0,
        regime_tributario=regime
    )

    # Cálculo Fiscal
    if regime == "Lucro Real":
        fiscal = calcular_impostos_lucro_real(preco_atual, cost)
        imposto_liquido = fiscal["impostos_totais"]
    else:
        imposto_liquido = preco_atual * (dados.get("aliquota_imposto_efetiva_pct", 12.0) / 100)

    comissao_rs = preco_atual * (comissao_pct / 100)
    custo_total_op = cost + imposto_liquido + comissao_rs + tarifa_fba
    lucro_liquido_rs = preco_atual - custo_total_op
    margem_atual_pct = (lucro_liquido_rs / preco_atual) * 100 if preco_atual > 0 else 0

    return f"""
### 💰 Diagnóstico de Precificação & Repricer Inteligente

**1. Estrutura de Custos Unidade (Preço Venda Atual: R$ {preco_atual:.2f}):**
* **Custo de Aquisição (CPV):** R$ {cost:.2f}
* **Imposto Líquido ({regime}):** R$ {imposto_liquido:.2f}
* **Comissão Amazon ({comissao_pct}%):** R$ {comissao_rs:.2f}
* **Tarifa Logística FBA:** R$ {tarifa_fba:.2f}
* **Lucro Líquido Atual:** **R$ {lucro_liquido_rs:.2f} ({margem_atual_pct:.1f}%)**

---

### 🎯 Repricer Automático (Proteção de Buy Box)

* **Status da Operação:** **{res_repricer['status_repricer']}**
* **Menor Oferta Concorrente Identificada:** R$ {res_repricer['menor_concorrente']:.2f}
* **Preço Piso (Margem Mínima de Segurança 10%):** **R$ {res_repricer['preco_piso']:.2f}**
* **Preço Teto Maximizado:** R$ {res_repricer['preco_teto']:.2f}

👉 **Recomendação de Preço Sugerida pelo Agente:** **R$ {res_repricer['preco_final_sugerido']:.2f}**
* **Parecer Técnico:** {res_repricer['acao_tomada']}
* **Margem Líquida Projetada no Novo Preço:** **R$ {res_repricer['margem_liquida_reais']:.2f} ({res_repricer['margem_liquida_pct']}%)**
"""