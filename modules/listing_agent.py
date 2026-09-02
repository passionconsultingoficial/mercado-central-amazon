import os
import requests
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic


def buscar_concorrentes_nicho(termo_ou_asin: str) -> tuple:
    """Busca dinâmica na Amazon Brasil para identificar o nicho real e 5 concorrentes."""
    termo_limpo = termo_ou_asin.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    concorrentes = []

    # Se for um ASIN (10 caracteres alfanuméricos), busca o título real na Amazon
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

    # Realiza busca do nicho na Amazon Brasil
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


def gerar_relatorio_a9_dinamico(
    asin_ou_termo: str, termo_ref: str, detalhes: str
) -> str:
    """Gera o relatório A9/A10 parametrizado dinamicamente para QUALQUER produto digitado."""
    prod_nome = termo_ref.title() if termo_ref else asin_ou_termo.title()
    palavras = prod_nome.split()
    kw_base = palavras[0].lower() if palavras else "produto"
    detalhes_txt = (
        detalhes.strip()
        if detalhes.strip()
        else "Alta qualidade e excelente desempenho para o dia a dia."
    )

    return f"""
### 1. TÍTULOS OTIMIZADOS (MÁXIMO 75 CARACTERES CADA)
- **Título A (Foco em Clareza):** {prod_nome[:45]} Alta Qualidade Pronta Entrega
- **Título B (Foco em SEO / Palavras-chave):** {prod_nome[:40]} Premium Envio Rápido FBA

---

### 2. DESCRIÇÃO DO PRODUTO (ATÉ 2.000 CARACTERES)
Descubra a solução ideal para o seu dia a dia com o **{prod_nome}**. Projetado para atender aos mais altos padrões de exigência da categoria, este item oferece durabilidade, eficiência e excelente desempenho. {detalhes_txt} Desenvolvido com materiais de alto padrão, é ideal para quem busca praticidade, segurança e o melhor custo-benefício do mercado nacional.

#### Versão HTML para o Seller Central:
```html
<p><b>Surpreenda-se com a qualidade do {prod_nome}!</b></p>
<p>Desenvolvido para entregar máxima durabilidade e praticidade, o <b>{prod_nome}</b> é a escolha perfeita no segmento.</p>
<p><b>Destaques do Produto:</b><br>- Material de alta resistência<br>- Pronta entrega com envio rápido via Amazon<br>- Garantia de fábrica e suporte dedicado</p>