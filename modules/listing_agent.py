import os
import requests
import inspect
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic


def buscar_concorrentes_nicho(termo_ou_asin: str) -> tuple:
    """Busca dinâmica na Amazon Brasil para identificar os 5 concorrentes do nicho real."""
    termo_limpo = termo_ou_asin.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    concorrentes = []

    if len(termo_limpo) == 10 and termo_limpo.isalnum():
        url_asin = "https://www.amazon.com.br/dp/" + termo_limpo
        try:
            res = requests.get(url_asin, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "html.parser")
                title_node = soup.find("span", {"id": "productTitle"})
                if title_node:
                    termo_limpo = " ".join(
                        title_node.get_text().strip().split()[:5]
                    )
        except Exception:
            pass

    search_url = "https://www.amazon.com.br/s?k=" + requests.utils.quote(termo_limpo)
    try:
        res_search = requests.get(search_url, headers=headers, timeout=6)
        if res_search.status_code == 200:
            soup = BeautifulSoup(res_search.content, "html.parser")
            items = soup.find_all(
                "div", {"data-component-type": "s-search-result"}
            )
            for item in items:
                c_asin = item.get("data-asin")
                if c_asin and c_asin != termo_ou_asin:
                    h2 = item.find("h2")
                    c_title = (
                        h2.get_text().strip()
                        if h2
                        else "Produto Concorrente " + str(c_asin)
                    )
                    concorrentes.append(
                        {
                            "asin": c_asin,
                            "titulo": c_title[:90],
                            "link": "https://www.amazon.com.br/dp/" + str(c_asin),
                        }
                    )
                    if len(concorrentes) == 5:
                        break
    except Exception:
        pass

    if not concorrentes:
        link_gen = "https://www.amazon.com.br/s?k=" + requests.utils.quote(termo_limpo)
        for i in range(1, 6):
            concorrentes.append(
                {
                    "asin": "Nicho-BR-0" + str(i),
                    "titulo": "Concorrente do Nicho (" + termo_limpo[:30] + "...) - Ver na Amazon",
                    "link": link_gen,
                }
            )

    return concorrentes, termo_limpo


def analisar_e_otimizar_listing(
    asin_input: str, produto_nosso: str = "", bullet_points_concorrente: str = ""
) -> str:
    """Gera o listing otimizado com base estrita no Algoritmo A9/A10."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            api_key = ""

    termo_busca = produto_nosso.strip() if produto_nosso.strip() else asin_input.strip()
    concorrentes, termo_referencia = buscar_concorrentes_nicho(termo_busca)

    links_md = "### 🔗 5 Concorrentes Diretos Mapeados no Mercado (Amazon BR):\n\n"
    for i, conc in enumerate(concorrentes[:5], start=1):
        links_md += (
            str(i)
            + ". ["
            + str(conc["titulo"])
            + "]("
            + str(conc["link"])
            + ") - **ASIN:** `"
            + str(conc["asin"])
            + "`\n"
        )
    links_md += "\n---\n"

    # Prompt Mestre A9/A10 limpo e parametrizado
    raw_prompt = """
Você é o Maior Especialista em Algoritmo A9/A10 da Amazon Brasil e Copywriter de Alta Conversão.

📌 DADOS DO PRODUTO:
- ASIN / Entrada: {asin}
- Termo do Nicho / Produto: {termo}

🧠 ETAPA DE ANÁLISE (OBRIGATÓRIA - SILENCIOSA - NÃO EXIBIR NA SAÍDA):
Analise público ideal, dores, benefícios reais, características principais e nível de concorrência no mercado brasileiro.

🚨 REGRAS CRÍTICAS ALGORITMO A10 AMAZON BRASIL:
1. TÍTULOS: Máximo estrito de 75 caracteres cada. Estrutura obrigatória: [Descrição do Produto] + [Benefício] + [Característica]. Sem termos como "frete grátis", "100% garantido", "melhor". Sem caracteres restritos (!, $, ?, _, {{}}, ^, ¬, ¦).
2. DESCRIÇÃO: Texto fluido de até 2.000 caracteres focado em AIDA + Versão HTML limpa para Seller Central (<p>, <b>, <br>).
3. BULLET POINTS: 10 bullets iniciando com Emoji + TÍTULO EM CAIXA ALTA.
4. BACKEND KEYWORDS: Exatamente 20 palavras-chave únicas (máx 230 bytes). Não repetir palavras que já estão nos Títulos. Sem acentos, sem vírgulas.
5. 10 PROMPTS PARA IMAGENS DA LISTAGEM: Iniciando OBRIGATORIAMENTE com "using the attached base product image as an overlay without any modification to the product itself". Foto 01 fundo branco puro (RGB 255,255,255) preenchendo 85%. Textos visuais em português brasileiro.
6. ROTEIRO DE VÍDEO (30–45s) em 5 cenas.
7. CONTEÚDO A+ COMPLETO para quebra de objeções.
8. 6 PROMPTS PARA IMAGENS A+ em inglês iniciando com "using the attached base product image as an overlay without any modification to the product itself".

GERE A SAÍDA ESTRUTURADA EM MARKDOWN:

1. TÍTULO (MÁXIMO 75 CARACTERES CADA)
- Título A (Foco em Clareza - Máx 75 caracteres)
- Título B (Foco em SEO - Máx 75 caracteres)

2. DESCRIÇÃO (ATÉ 2.000 CARACTERES)
[Texto fluido]
#### Versão HTML para o Seller Central:
```html
[HTML limpo]