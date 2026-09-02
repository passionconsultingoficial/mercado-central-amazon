import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def analisar_e_otimizar_listing(titulo_concorrente, bullet_points_concorrente, produto_nosso):
    system_prompt = (
        "Você é um especialista em SEO para Amazon e Copywriting para e-commerce. "
        "Sua função é analisar anúncios de concorrentes, identificar palavras-chave estratégicas "
        "e criar títulos e bullet points altamente otimizados para conversão e algoritmo da Amazon (A9/A10)."
    )

    user_prompt = f"""
    --- ANÚNCIO DO CONCORRENTE ---
    Título: {titulo_concorrente}
    Bullet Points: {bullet_points_concorrente}

    --- NOSSO PRODUTO ---
    Nome/Detalhes: {produto_nosso}

    --- TAREFA ---
    1. Extraia as principais palavras-chave do concorrente.
    2. Crie um TÍTULO otimizado para o nosso produto (max 200 caracteres, incluindo marca, recurso principal e benefício).
    3. Crie 5 BULLET POINTS persuasivos focados em benefícios, especificações técnicas e quebra de objeções.
    
    Responda em formato estruturado e direto.
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
    titulo_rival = "Maleta Organizadora Para Ferramentas Profissional Pró 13 Repartições Arqplast"
    bullets_rival = [
        "Ideal para organizar ferramentas, parafusos e artigos de pesca.",
        "Possui 13 compartimentos e fecho de segurança duplo.",
        "Plástico de alta resistência e alça para transporte."
    ]
    
    nosso_produto = "Maleta Organizadora Multiuso 15 Divisórias Reforçada com Trava Dupla"

    print("Analisando e otimizando listing via Claude...\n")
    resultado = analisar_e_otimizar_listing(
        titulo_concorrente=titulo_rival,
        bullet_points_concorrente="\n".join(bullets_rival),
        produto_nosso=nosso_produto
    )
    
    print(resultado)