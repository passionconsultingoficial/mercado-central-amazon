from modules.tax_engine import calcular_impostos_lucro_real

def analisar_planejamento_fiscal(dados):
    sku = dados.get("sku", "N/A")
    regime = dados.get("regime_tributario", "Lucro Real")
    preco_venda = dados.get("preco_venda_rs", 0.0)
    custo_compra = dados.get("custo_aquisicao_rs", 0.0)

    if regime == "Lucro Real":
        fiscal = calcular_impostos_lucro_real(preco_venda, custo_compra)
        
        return f"""
### ⚖️ Diagnóstico Fiscal — Lucro Real (SP)

**Resumo Tributário Líquido (Por Unidade):**
* **Preço de Venda (Buy Box):** R$ {preco_venda:.2f}
* **Custo de Aquisição (CPV):** R$ {custo_compra:.2f}

---

**1. PIS / COFINS (Não-Cumulativo — 9,25%):**
* **Débito sobre Vendas:** R$ {fiscal['pis_cofins_debito']:.2f}
* **Crédito sobre Compras:** R$ {fiscal['pis_cofins_credito']:.2f}
* **PIS/COFINS Líquido a Recolher:** **R$ {fiscal['pis_cofins_liquido']:.2f}**

**2. ICMS (Operação Interna SP — 18%):**
* **Débito sobre Vendas:** R$ {fiscal['icms_debito']:.2f}
* **Crédito sobre Compras:** R$ {fiscal['icms_credito']:.2f}
* **ICMS Líquido a Recolher:** **R$ {fiscal['icms_liquido']:.2f}**

---

**3. Consolidação Fiscal:**
* **Total de Impostos Líquidos:** **R$ {fiscal['impostos_totais']:.2f}**
* **Alíquota Efetiva Real:** **{fiscal['aliquota_efetiva_pct']:.2f}%**
"""
    else:
        imposto_est = preco_venda * (dados.get("aliquota_imposto_efetiva_pct", 12.0) / 100)
        return f"""
### ⚖️ Diagnóstico Fiscal — {regime}

* **Preço de Venda:** R$ {preco_venda:.2f}
* **Imposto Estimado:** R$ {imposto_est:.2f}
* **Alíquota Informada:** {dados.get('aliquota_imposto_efetiva_pct', 12.0)}%
"""