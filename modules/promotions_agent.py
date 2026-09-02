import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def analisar_viabilidade_promocao(dados_campanha):
    system_prompt = (
        "Você é um estrategista de e-commerce e especialista em promoções na Amazon Brasil. "
        "Sua função é avaliar se um cupom de desconto ou oferta promocional é viável, "
        "garantindo que o desconto não ultrapasse a margem de segurança do vendedor."
    )

    user_prompt = f"""
    --- DADOS DA PROMOÇÃO E MARGEM ---
    {json.dumps(dados_campanha, indent=2, ensure_ascii=False)}

    --- TAREFAS DE ANÁLISE ---
    1. **Preço Final com Desconto**: Calcule quanto o cliente pagará.
    2. **Nova Margem Líquida**: Demonstre o lucro em R$ e % durante a promoção.
    3. **Aprovação de Margem**: Verifique se a nova margem está acima da margem mínima estipulada.
    4. **Parecer Estratégico**: Dê a recomendação se vale a pena ativar o cupom/oferta.

    Retorne os dados formatados de forma clara e direta.
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
    campanha_exemplo = {
        "sku": "MALETA-PRO-15",
        "preco_atual": 69.90,
        "custo_total_operacional": 49.88,
        "tipo_promocao": "Cupom de Desconto em %",
        "desconto_proposto_pct": 10.0,
        "taxa_fixa_criacao_cupom_amazon": 2.00,
        "margem_minima_seguranca_pct": 10.0
    }

    print("Analisando viabilidade do cupom...\n")
    resultado = analisar_viabilidade_promocao(campanha_exemplo)
    print(resultado)