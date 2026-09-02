from modules.logistics_engine import calcular_peso_taxavel, calcular_tarifas_amazon

def comparar_modalidades_logisticas(dados):
    sku = dados.get("sku", "N/A")
    peso_kg = dados.get("peso_kg", 0.85)
    dim = dados.get("dimensoes_cm", {"comprimento": 30, "largura": 20, "altura": 15})
    preco_venda = dados.get("preco_venda", 69.90)

    peso_taxavel = calcular_peso_taxavel(
        peso_kg, 
        dim.get("comprimento", 0), 
        dim.get("largura", 0), 
        dim.get("altura", 0)
    )
    
    tarifas = calcular_tarifas_amazon(peso_taxavel, preco_venda)

    return f"""
### 🚚 Comparativo Logístico — FBA vs DBA vs Envio Próprio

**Parâmetros de Carga & Cubagem:**
* **Peso Real:** {peso_kg:.2f} kg
* **Dimensões:** {dim['comprimento']}x{dim['largura']}x{dim['altura']} cm
* **Peso Taxável (Considerado):** **{tarifas['peso_taxavel_kg']:.2f} kg**

---

**Estimativa de Carga Operacional por Unidade:**
* **FBA (Fulfillment by Amazon):** **R$ {tarifas['tarifa_fba']:.2f}** *(Inclui picking, packing e atendimento)*
* **DBA (Delivery by Amazon):** **R$ {tarifas['tarifa_dba']:.2f}** *(Exige embalagem e manuseio no seu galpão)*
* **Envio Próprio (Correios/Transportadora):** R$ {dados.get('estimativa_envio_proprio', 18.00):.2f}

---

**💡 Análise de Eficiência Operacional:**
1. **Vantagem de Escala do FBA:** O custo do FBA é menor por unidade enviada devido aos contratos diretos da Amazon com grandes transportadoras nacionais e automação dos CDs.
2. **Redução de Custo Fixo Operacional:** O FBA elimina a necessidade de comprar caixas de papelão, fita adesiva e alocar funcionários para empacotamento.
3. **Impulso em Vendas (Prime):** O FBA garante o selo Prime Nacional com entregas rápidas, aumentando sensivelmente a taxa de conversão e a eficiência das campanhas de PPC.
"""