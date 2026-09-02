def calcular_impostos_lucro_real(preco_venda, custo_aquisicao, aliquota_icms_venda=0.18, aliquota_icms_compra=0.18):
    """
    Calcula a carga tributária líquida no regime de Lucro Real (Não-Cumulativo)
    para vendas e aquisições em São Paulo.
    """
    # 1. PIS / COFINS (Não-Cumulativo)
    pis_cofins_debito = preco_venda * 0.0925  # 9,25% sobre a venda
    pis_cofins_credito = custo_aquisicao * 0.0925  # 9,25% sobre a compra
    pis_cofins_liquido = max(0.0, pis_cofins_debito - pis_cofins_credito)

    # 2. ICMS (Débito x Crédito)
    icms_debito = preco_venda * aliquota_icms_venda
    icms_credito = custo_aquisicao * aliquota_icms_compra
    icms_liquido = max(0.0, icms_debito - icms_credito)

    # 3. Carga Tributária Total
    impostos_totais = pis_cofins_liquido + icms_liquido
    aliquota_efetiva = (impostos_totais / preco_venda) * 100 if preco_venda > 0 else 0.0

    return {
        "pis_cofins_debito": round(pis_cofins_debito, 2),
        "pis_cofins_credito": round(pis_cofins_credito, 2),
        "pis_cofins_liquido": round(pis_cofins_liquido, 2),
        "icms_debito": round(icms_debito, 2),
        "icms_credito": round(icms_credito, 2),
        "icms_liquido": round(icms_liquido, 2),
        "impostos_totais": round(impostos_totais, 2),
        "aliquota_efetiva_pct": round(aliquota_efetiva, 2)
    }