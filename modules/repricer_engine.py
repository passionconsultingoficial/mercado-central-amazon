from modules.tax_engine import calcular_impostos_lucro_real
from modules.logistics_engine import calcular_peso_taxavel, calcular_tarifas_amazon

def calcular_piso_e_teto_repricer(
    custo_aquisicao_rs, 
    comissao_amazon_pct=15.0, 
    peso_kg=0.85, 
    dimensoes={"comprimento": 30, "largura": 20, "altura": 15},
    margem_minima_seguranca_pct=10.0,
    regime_tributario="Lucro Real"
):
    """
    Calcula o preço piso (mínimo com margem de segurança) e teto de precificação.
    """
    peso_taxavel = calcular_peso_taxavel(peso_kg, dimensoes["comprimento"], dimensoes["largura"], dimensoes["altura"])
    
    # Estimativa inicial de tarifas para cálculo de iterativo
    tarifas = calcular_tarifas_amazon(peso_taxavel, preco_venda=50.0)
    tarifa_fba = tarifas["tarifa_fba"]

    # Cálculo do Preço Piso
    # Fórmula: Piso = (Custo + Frete) / (1 - (Comissão% + Imposto_Efetivo_Estimado% + Margem_Minima%))
    # Para Lucro Real, consideramos crédito de PIS/COFINS (9.25%) e ICMS
    
    taxa_comissao = comissao_amazon_pct / 100.0
    taxa_margem_min = margem_minima_seguranca_pct / 100.0
    
    if regime_tributario == "Lucro Real":
        # No Lucro Real, imposto líquido médio sobre venda com créditos gira em torno de 8.75% a 10%
        taxa_imposto_liquida = 0.09
    else:
        taxa_imposto_liquida = 0.12

    divisor = 1.0 - (taxa_comissao + taxa_imposto_liquida + taxa_margem_min)
    if divisor <= 0:
        divisor = 0.1

    # Custo base com frete FBA deduzido do crédito
    credito_pis_cofins = custo_aquisicao_rs * 0.0925 if regime_tributario == "Lucro Real" else 0.0
    custo_liquido_real = custo_aquisicao_rs - credito_pis_cofins + tarifa_fba

    preco_piso = custo_liquido_real / divisor
    preco_teto = preco_piso * 1.35  # Teto de +35% sobre o piso para maximização

    return round(preco_piso, 2), round(preco_teto, 2)


def executar_simulacao_repricer(
    preco_buy_box_atual, 
    custo_aquisicao_rs, 
    concorrentes_precos=[], 
    margem_minima_seguranca_pct=10.0,
    regime_tributario="Lucro Real"
):
    """
    Executa a tomada de decisão do Repricer para garantir a Buy Box.
    """
    preco_piso, preco_teto = calcular_piso_e_teto_repricer(
        custo_aquisicao_rs=custo_aquisicao_rs,
        margem_minima_seguranca_pct=margem_minima_seguranca_pct,
        regime_tributario=regime_tributario
    )

    if not concorrentes_precos:
        menor_concorrente = preco_buy_box_atual
    else:
        menor_concorrente = min(concorrentes_precos)

    # Regra 1: Tentar bater a Buy Box em R$ 0,10 abaixo do menor concorrente
    preco_alvo_sugerido = menor_concorrente - 0.10

    status_repricer = ""
    acao_tomada = ""

    if preco_alvo_sugerido >= preco_piso:
        if preco_alvo_sugerido > preco_teto:
            preco_final = preco_teto
            status_repricer = "🟢 Maximizando Margem (No Teto)"
            acao_tomada = f"Ajustado para o Preço Teto de R$ {preco_teto:.2f} (Sem pressão agressiva de concorrência)."
        else:
            preco_final = preco_alvo_sugerido
            status_repricer = "🟢 Ganho de Buy Box Garantido"
            acao_tomada = f"Preço reduzido para R$ {preco_final:.2f} (R$ 0,10 abaixo da Buy Box de R$ {menor_concorrente:.2f})."
    else:
        # Não bate o preço do concorrente pois entraria abaixo da margem de segurança
        preco_final = preco_piso
        status_repricer = "🔴 Trava de Proteção Ativada (Preço Piso Alcançado)"
        acao_tomada = f"Preço mantido no Piso de R$ {preco_piso:.2f}. Bater o concorrente (R$ {menor_concorrente:.2f}) destruiria a margem de segurança de {margem_minima_seguranca_pct}%."

    # Cálculo da margem líquida com o preço final do Repricer
    fiscal = calcular_impostos_lucro_real(preco_final, custo_aquisicao_rs) if regime_tributario == "Lucro Real" else {"impostos_totais": preco_final * 0.12}
    margem_reais = preco_final - (custo_aquisicao_rs + fiscal["impostos_totais"] + (preco_final * 0.15) + 11.50)
    margem_pct = (margem_reais / preco_final) * 100 if preco_final > 0 else 0.0

    return {
        "preco_buy_box_atual": preco_buy_box_atual,
        "menor_concorrente": menor_concorrente,
        "preco_piso": preco_piso,
        "preco_teto": preco_teto,
        "preco_final_sugerido": round(preco_final, 2),
        "status_repricer": status_repricer,
        "acao_tomada": acao_tomada,
        "margem_liquida_reais": round(margem_reais, 2),
        "margem_liquida_pct": round(margem_pct, 2)
    }