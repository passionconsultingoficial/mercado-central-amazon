import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def auditar_conciliacao_extrato(extrato_repasse):
    system_prompt = (
        "Você é um auditor financeiro especializado em marketplace e conciliação de extratos da Amazon. "
        "Sua função é confrontar o faturamento bruto com os valores repassados na conta bancária, "
        "identificando discrepâncias em comissões, tarifas de frete incorretas, cobranças duplicadas ou despesas não previstas."
    )

    user_prompt = f"""
    --- EXTRATO FINANCEIRO E REPASSE AMAZON ---
    {json.dumps(extrato_repasse, indent=2, ensure_ascii=False)}

    --- TAREFAS DE AUDITORIA ---
    1. **Resumo da Conciliação**: Mostre Faturamento Bruto, Retenções Totais e Repasse Líquido Esperado vs. Recebido.
    2. **Identificação de Divergências**: Apunte se houve tarifas acima da tabela estipulada ou retenções indevidas.
    3. **Plano de Ação de Cobrança**: Caso existam discrepâncias, indique como abrir chamado de contestação no suporte do Seller Central.

    Retorne o parecer de conciliação de forma estruturada.
    """

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1500,
        thinking={"type": "disabled"},
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.content[0].text

if __name__ == "__main__":
    extrato_exemplo = {
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

    print("Auditando extrato e conciliação financeira...\n")
    resultado = auditar_conciliacao_extrato(extrato_exemplo)
    print(resultado)