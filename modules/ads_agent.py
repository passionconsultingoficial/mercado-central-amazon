import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def otimizar_campanha_ppc(dados_campanha):
    system_prompt = (
        "Você é um especialista em Amazon Ads (PPC) focado em margem de lucro. "
        "Sua função é analisar relatórios de campanhas patrocinadas, comparar o ACoS atual com o ACoS meta "
        "e indicar ajustes práticos de lances (bids), palavras-chave negativas e alocação de orçamento."
    )

    user_prompt = f"""
    --- MÉTRICAS DA CAMPANHA DE ADS ---
    {json.dumps(dados_campanha, indent=2, ensure_ascii=False)}

    --- TAREFAS DE OTIMIZAÇÃO ---
    1. **Análise de ACoS**: Classifique a performance frente à meta estipulada.
    2. **Ajuste de Lances (Bids)**: Indique quais palavras-chave devem ter o lance aumentado, reduzido ou mantido.
    3. **Ações para Termos Sem Conversão**: Identifique palavras-chave que estão consumindo verba sem gerar vendas e recomende o bloqueio/negativação.
    4. **Recomendação de Orçamento**: Avalie se o orçamento diário deve ser ajustado.

    Retorne uma análise curta e focada em ação.
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
        "nome_campanha": "SP_Exact_Maleta_Organizadora",
        "sku": "MALETA-PRO-15",
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
    }

    print("Analisando campanha de Ads...\n")
    resultado = otimizar_campanha_ppc(campanha_exemplo)
    print(resultado)