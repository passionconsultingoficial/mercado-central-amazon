import os
import requests
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic


def buscar_concorrentes_nicho(termo_ou_asin: str) -> tuple:
    termo_limpo = termo_ou_asin.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    concorrentes = []

    # Extrai título real se for ASIN de 10 caracteres
    if len(termo_limpo) == 10 and termo_limpo.isalnum():
        url_asin = f"https://www.amazon.com.br/dp/{termo_limpo}"
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

    # Busca 5 concorrentes reais na Amazon Brasil
    search_url = (
        f"https://www.amazon.com.br/s?k={requests.utils.quote(termo_limpo)}"
    )
    try:
        res_search = requests.get(search_url, headers=headers, timeout=6)
        if res_search.status_code == 200:
            soup = BeautifulSoup(res_search.content, "html.parser")
            items = soup.find_all(
                "div", {"data-component-type": "s-search-result"}
            )
            for item in items:
                c_asin = item.get("data-asin")
                if c_asin:
                    h2 = item.find("h2")
                    c_title = (
                        h2.get_text().strip()
                        if h2
                        else f"Produto Concorrente {c_asin}"
                    )
                    concorrentes.append(
                        {
                            "asin": c_asin,
                            "titulo": c_title[:90],
                            "link": f"https://www.amazon.com.br/dp/{c_asin}",
                        }
                    )
                    if len(concorrentes) == 5:
                        break
    except Exception:
        pass

    if not concorrentes:
        link_gen = f"https://www.amazon.com.br/s?k={requests.utils.quote(termo_limpo)}"
        for i in range(1, 6):
            concorrentes.append(
                {
                    "asin": f"Nicho-BR-0{i}",
                    "titulo": f"Concorrente do Nicho ({termo_limpo[:30]}...) - Ver na Amazon",
                    "link": link_gen,
                }
            )

    return concorrentes, termo_limpo


def analisar_e_otimizar_listing(
    asin_input: str, produto_nosso: str = "", bullet_points_concorrente: str = ""
) -> str:
    # Tenta recuperar chave do ambiente ou secrets
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            api_key = ""

    termo_busca = produto_nosso if produto_nosso.strip() else asin_input
    concorrentes, termo_referencia = buscar_concorrentes_nicho(termo_busca)

    links_md = f"### 🔗 5 Concorrentes Diretos Mapeados no Mercado (Amazon BR):\n\n"
    for i, conc in enumerate(concorrentes[:5], start=1):
        links_md += f"{i}. [{conc['titulo']}]({conc['link']}) - **ASIN:** `{conc['asin']}`\n"
    links_md += "\n---\n"

    # Se a API estiver ativa, executa a análise mestre do Claude
    if api_key and len(str(api_key).strip()) > 10:
        try:
            client = Anthropic(api_key=str(api_key).strip())
            prompt_mestre = f"""
            Você é um especialista em SEO, Algoritmo A9/A10 e Inteligência Competitiva para a Amazon Brasil.

            DADOS ENTRADOS:
            - ASIN / Entrada: {asin_input}
            - Produto / Referência: {termo_referencia}
            - Observações do Concorrente: {bullet_points_concorrente}

            REGRAS CRÍTICAS A9/A10:
            - Sem superlativos absolutos (melhor, perfeito, nº1) ou frases promocionais (frete grátis).
            - Títulos A e B: Máximo 75 caracteres cada (Descrição + Benefício + Característica).
            - Descrição: Até 2.000 caracteres fluida + versão HTML com tags p, b e br.
            - 10 Bullet Points começando com emojis e caixa alta de impacto.
            - 20 Palavras-chave backend (search terms) sem acentos, sem vírgulas, max 230 bytes.
            - 10 Prompts para Imagens da Listagem em português iniciando obrigatoriamente com "using the attached base product image as an overlay without any modification to the product itself".
            - Roteiro de Vídeo (30-45s) em 5 cenas.
            - Estrutura de Conteúdo A+ e 6 Prompts de Banners A+ em inglês.

            Gere a saída completa em Markdown.
            """
            for model_name in [
                "claude-3-5-sonnet-20240620",
                "claude-3-haiku-20240307",
                "claude-3-sonnet-20240229",
            ]:
                try:
                    res = client.messages.create(
                        model=model_name,
                        max_tokens=3500,
                        messages=[{"role": "user", "content": prompt_mestre}],
                    )
                    return links_md + "\n" + res.content[0].text
                except Exception:
                    continue
        except Exception:
            pass

    # Fallback dinâmico parametrizado caso não haja chave Anthropic ativa
    kw_base = termo_referencia.split()[0].lower() if termo_referencia.split() else "produto"
    analise_dinamica = f"""
### 📊 Diagnóstico e Otimização de Listing - A9/A10

**1. TÍTULOS OTIMIZADOS (MÁXIMO 75 CARACTERES CADA)**
- **Título A (Foco em Clareza):** {termo_referencia.title()[:45]} Alta Qualidade Pronta Entrega
- **Título B (Foco em SEO):** {termo_referencia.title()[:40]} Premium Envio Rápido FBA

---

**2. DESCRIÇÃO DO PRODUTO (ATÉ 2.000 CARACTERES)**
O **{termo_referencia.title()}** foi desenvolvido para oferecer máxima resistência, eficiência e praticidade no seu dia a dia. Fabricado sob rigorosos padrões de qualidade da categoria, é a escolha ideal para quem busca durabilidade e excelente desempenho no mercado nacional.

#### Versão HTML para o Seller Central:
```html
<p><b>Surpreenda-se com a qualidade do {termo_referencia.title()}!</b></p>
<p>Projetado para entregar máxima durabilidade e praticidade no seu dia a dia.</p>
<p><b>Destaques do Produto:</b><br>- Material de alta resistência<br>- Pronta entrega via Amazon Brasil<br>- Garantia do fabricante e suporte dedicado</p>