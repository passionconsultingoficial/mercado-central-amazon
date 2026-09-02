def calcular_peso_taxavel(peso_kg, comprimento_cm, largura_cm, altura_cm):
    """
    Calcula o peso cubado (C x L x A / 5000) e retorna o maior valor entre peso real e cubado.
    """
    peso_cubado = (comprimento_cm * largura_cm * altura_cm) / 5000.0
    return max(peso_kg, peso_cubado)

def calcular_tarifas_amazon(peso_taxavel_kg, preco_venda):
    """
    Calcula a tarifa de envio estimada para FBA e DBA com base no peso taxável e faixas oficiais ajustadas.
    """
    # Faixas ajustadas para refletir a eficiência de custo do FBA x DBA na Amazon Brasil
    if peso_taxavel_kg <= 0.5:
        tarifa_dba = 8.90
        tarifa_fba = 6.80
    elif peso_taxavel_kg <= 1.0:
        tarifa_dba = 11.50
        tarifa_fba = 8.90
    elif peso_taxavel_kg <= 2.0:
        tarifa_dba = 14.80
        tarifa_fba = 11.50
    elif peso_taxavel_kg <= 5.0:
        tarifa_dba = 22.00
        tarifa_fba = 17.90
    else:
        peso_extra = peso_taxavel_kg - 5.0
        tarifa_dba = 22.00 + (peso_extra * 2.50)
        tarifa_fba = 17.90 + (peso_extra * 2.00)

    # Taxa fixa para itens abaixo da faixa de frete grátis (R$ 79,00)
    taxa_item_barato = 2.00 if preco_venda < 79.00 else 0.00

    return {
        "peso_taxavel_kg": round(peso_taxavel_kg, 2),
        "tarifa_dba": round(tarifa_dba + taxa_item_barato, 2),
        "tarifa_fba": round(tarifa_fba + taxa_item_barato, 2),
        "taxa_item_barato": taxa_item_barato
    }