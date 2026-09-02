import os
import json
from modules.listing_agent import analisar_e_otimizar_listing
from modules.pricing_agent import calcular_precificacao_e_breakeven
from modules.promotions_agent import analisar_viabilidade_promocao
from modules.logistics_agent import comparar_modalidades_logisticas
from modules.ads_agent import otimizar_campanha_ppc
from modules.tax_consultant_agent import analisar_planejamento_fiscal
from modules.reconciliation_agent import auditar_conciliacao_extrato

def executar_central_marketplace(payload):
    print("=" * 70)
    print(f"CENTRAL DE MARKETPLACE - ANÁLISE 360° DO SKU: {payload['sku']}")
    print("=" * 70)

    # 1. Listing & SEO
    print("\n[1/7] SEO & COPYWRITING (LISTING)")
    print(analisar_e_otimizar_listing(
        payload["concorrente_titulo"],
        "\n".join(payload["concorrente_bullets"]),
        payload["nosso_produto_nome"]
    ))

    # 2. Precificação
    print("\n" + "-" * 70)
    print("[2/7] PRECIFICAÇÃO E MARGEM LÍQUIDA")
    print(calcular_precificacao_e_breakeven({
        "sku": payload["sku"],
        "custo_produto_com_imposto": payload["custo_unitario"],
        "regime_tributario": payload["regime_tributario"],
        "aliquota_imposto_efetiva_pct": payload["imposto_pct"],
        "comissao_amazon_pct": payload["comissao_pct"],
        "tarifa_fixa_fba_dba": payload["tarifa_fixa"],
        "margem_liquida_alvo_pct": payload["margem_alvo_pct"],
        "preco_buy_box_atual": payload["preco_buy_box"]
    }))

    # 3. Promoções
    print("\n" + "-" * 70)
    print("[3/7] ANÁLISE DE PROMOÇÕES E CUPONS")
    print(analisar_viabilidade_promocao({
        "sku": payload["sku"],
        "preco_atual": payload["preco_buy_box"],
        "custo_total_operacional": payload["custo_unitario"] + payload["tarifa_fixa"],
        "tipo_promocao": "Cupom de Desconto em %",
        "desconto_proposto_pct": 10.0,
        "taxa_fixa_criacao_cupom_amazon": 2.00,
        "margem_minima_seguranca_pct": 10.0
    }))

    # 4. Logística
    print("\n" + "-" * 70)
    print("[4/7] COMPARATIVO DE LOGÍSTICA")
    print(comparar_modalidades_logisticas({
        "sku": payload["sku"],
        "peso_kg": payload["peso_kg"],
        "dimensoes_cm": payload["dimensoes"],
        "preco_venda": payload["preco_buy_box"],
        "estimativa_custo_dba": 8.50,
        "estimativa_custo_fba": 11.20,
        "estimativa_envio_proprio": 15.00
    }))

    # 5. Amazon Ads (PPC)
    print("\n" + "-" * 70)
    print("[5/7] OTIMIZAÇÃO DE TRÁFEGO PAGO (ADS)")
    print(otimizar_campanha_ppc(payload["campanha_ppc"]))

    # 6. Planejamento Fiscal
    print("\n" + "-" * 70)
    print("[6/7] CONSULTORIA FISCAL E CRÉDITOS")
    print(analisar_planejamento_fiscal(payload["dados_fiscais"]))

    # 7. Conciliação Financeira
    print("\n" + "-" * 70)
    print("[7/7] AUDITORIA E CONCILIAÇÃO FINANCEIRA")
    print(auditar_conciliacao_extrato(payload["extrato_conciliacao"]))

if __name__ == "__main__":
    dados_mestre = {
        "sku": "MALETA-PRO-15",
        "nosso_produto_nome": "Maleta Organizadora Multiuso 15 Divisórias Reforçada com Trava Dupla",
        "custo_unitario": 25.00,
        "regime_tributario": "Lucro Real",
        "imposto_pct": 12.0,
        "comissao_pct": 15.0,
        "tarifa_fixa": 6.00,
        "margem_alvo_pct": 20.0,
        "preco_buy_box": 69.90,
        "peso_kg": 0.85,
        "dimensoes": {"comprimento": 30, "largura": 20, "altura": 15},
        "concorrente_titulo": "Maleta Organizadora Para Ferramentas Profissional Pró 13 Repartições Arqplast",
        "concorrente_bullets": [
            "Ideal para organizar ferramentas, parafusos e artigos de pesca.",
            "Possui 13 compartimentos e fecho de segurança duplo.",
            "Plástico de alta resistência e alça para transporte."
        ],
        "campanha_ppc": {
            "nome_campanha": "SP_Exact_Maleta_Organizadora",
            "acos_meta_pct": 18.0,
            "acos_atual_pct": 27.4,
            "investimento_rs": 450.00,
            "vendas_rs": 1642.34,
            "cpc_medio_rs": 1.41,
            "palavras_chave": [
                {"termo": "maleta de ferramentas", "acos_pct": 14.2, "cpc": 1.35, "vendas_rs": 1100.00},
                {"termo": "caixa organizadora plastica", "acos_pct": 38.5, "cpc": 1.60, "vendas_rs": 300.00},
                {"termo": "maleta parafusos", "acos_pct": 0.0, "cpc": 1.20, "cliques_sem_venda": 42}
            ]
        },
        "dados_fiscais": {
            "sku": "MALETA-PRO-15",
            "regime_tributario": "Lucro Real",
            "preco_venda_rs": 69.90,
            "custo_aquisicao_rs": 25.00,
            "aliquota_pis_cofins_debito_pct": 9.25,
            "credito_pis_cofins_compras_pct": 9.25,
            "comissao_amazon_rs": 10.49,
            "tarifa_frete_dba_rs": 8.50,
            "uf_origem": "SP",
            "uf_destino": "RJ"
        },
        "extrato_conciliacao": {
            "periodo": "15/08/2026 a 31/08/2026",
            "total_vendas_brutas_rs": 15400.00,
            "quantidade_pedidos": 220,
            "tarifas_comissao_retidas_rs": 2310.00,
            "tarifas_logistica_retidas_rs": 1870.00,
            "custo_ads_retido_fatura_rs": 1250.00,
            "devolucoes_reembolsos_rs": 350.00,
            "repasse_liquido_depositado_rs": 9620.00,
            "repasse_liquido_esperado_rs": 9620.00
        }
    }

    executar_central_marketplace(dados_mestre)