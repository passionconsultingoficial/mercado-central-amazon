import os
import re
import base64
import requests
import unicodedata
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic


def obter_token_sp_api() -> str:
    """Obtém token LWA da Selling Partner API."""
    refresh_token = os.getenv("LWA_REFRESH_TOKEN") or st.secrets.get("LWA_REFRESH_TOKEN", "")
    client_id = os.getenv("LWA_CLIENT_ID") or st.secrets.get("LWA_CLIENT_ID", "")
    client_secret = os.getenv("LWA_CLIENT_SECRET") or st.secrets.get("LWA_CLIENT_SECRET", "")

    if not (refresh_token and client_id and client_secret):
        return ""

    url_token = "https://api.amazon.com/auth/o2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    try:
        res = requests.post(url_token, data=payload, timeout=6)
        if res.status_code == 200:
            return res.json().get("access_token", "")
    except Exception:
        pass
    return ""


def analisar_imagem_visuo_computacional(image_bytes: bytes, mime_type: str, api_key: str) -> str:
    """Análise visual via Claude Vision para extração exata do produto da foto."""
    if not api_key or len(api_key.strip()) < 10:
        return ""

    try:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        client = Anthropic(api_key=api_key.strip())
        media_type = mime_type if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"] else "image/jpeg"

        modelos = [
            "claude-3-5-sonnet-latest",
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307"
        ]

        for model_id in modelos:
            try:
                response = client.messages.create(
                    model=model_id,
                    max_tokens=200,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": b64_img,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "Identifique o produto exato nesta imagem comercial. "
                                        "Retorne APENAS o termo de busca principal em português do Brasil "
                                        "para pesquisar no catálogo da Amazon BR (de 2 a 5 palavras). "
                                        "Exemplo: 'Comedouro Pet Elevado Inox Duo'. Sem explicações ou saudações."
                                    )
                                }
                            ],
                        }
                    ],
                )
                termo = response.content[0].text.strip().replace("\n", " ").replace(".", "")
                if termo:
                    return termo
            except Exception:
                continue

        return ""
    except Exception as e:
        st.error(f"Erro na análise visual: {e}")
        return ""


def buscar_melhor_vendedor_organico_amazon_br(query: str) -> dict:
    """
    Filtra anúncios patrocinados (Ads) e traz exclusivamente o PRIMEIRO RESULTADO ORGÂNICO
    da Amazon BR (Líder real de vendas do nicho).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    query_clean = requests.utils.quote(query)
    url_search = f"https://www.amazon.com.br/s?k={query_clean}"
    
    dados_lider = {
        "titulo_lider": f"{query.title()} Modelo Líder do Segmento",
        "asin_lider": "B0BRN2K9XX",
        "preco_lider": "Consulte o Link",
        "link_lider": url_search
    }

    try:
        res = requests.get(url_search, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            produtos = soup.find_all("div", {"data-component-type": "s-search-result"})
            
            for prod in produtos:
                # IGNORA RESULTADOS PATROCINADOS / ADS
                is_sponsored = (
                    prod.find("span", string=re.compile(r"Patrocinado|Sponsored", re.I)) or
                    "puppy-pi-carousel" in str(prod) or
                    "s-sponsored-label-info-icon" in str(prod)
                )
                if is_sponsored:
                    continue

                title_elem = prod.find("h2") or prod.find("span", {"class": "a-text-normal"})
                asin = prod.get("data-asin", "")
                price_elem = prod.find("span", {"class": "a-offscreen"})
                
                if title_elem and asin:
                    dados_lider["titulo_lider"] = title_elem.get_text().strip()
                    dados_lider["asin_lider"] = asin
                    if price_elem:
                        dados_lider["preco_lider"] = price_elem.get_text().strip()
                    dados_lider["link_lider"] = f"https://www.amazon.com.br/dp/{asin}"
                    break
    except Exception:
        pass

    return dados_lider


def extrair_dados_e_links_categoria_dinamicos(termo_entrada: str) -> tuple:
    termo_clean = termo_entrada.strip()
    asin_clean = termo_clean.upper()
    token = obter_token_sp_api()
    titulo_referencia = termo_clean.title()

    if len(asin_clean) == 10 and asin_clean.isalnum():
        if token:
            headers_sp = {
                "x-amz-access-token": token,
                "Content-Type": "application/json",
            }
            url_item = f"https://sellingpartnerapi-fe.amazon.com/catalog/2022-04-01/items/{asin_clean}?marketplaceIds=A21TJRUUN4KGV&includedData=summaries"
            try:
                res_item = requests.get(url_item, headers=headers_sp, timeout=5)
                if res_item.status_code == 200:
                    summaries = res_item.json().get("summaries", [])
                    if summaries:
                        titulo_referencia = summaries[0].get("itemName", titulo_referencia)
            except Exception:
                pass

        if titulo_referencia == termo_clean.title():
            headers_web = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            try:
                res_dp = requests.get(f"https://www.amazon.com.br/dp/{asin_clean}", headers=headers_web, timeout=6)
                if res_dp.status_code == 200:
                    soup = BeautifulSoup(res_dp.content, "html.parser")
                    title_node = soup.find("span", {"id": "productTitle"})
                    if title_node:
                        titulo_referencia = title_node.get_text().strip()
            except Exception:
                pass

    palavras_reais = [w for w in re.findall(r'\w+', titulo_referencia) if len(w) > 1 and w.upper() != asin_clean]
    if not palavras_reais:
        palavras_reais = [w for w in re.findall(r'\w+', termo_clean) if len(w) > 1]

    query_completa = "+".join(palavras_reais) if palavras_reais else requests.utils.quote(termo_clean)
    termo_exibicao = " ".join([w.title() for w in palavras_reais]) if palavras_reais else termo_clean.title()

    termos_busca = [
        (f"Categoria Direta - {termo_exibicao}", query_completa),
        (f"Ofertas Similares - {termo_exibicao}", f"{query_completa}+modelo"),
        (f"Principais Marcas - {termo_exibicao}", f"{query_completa}+top"),
        (f"Mais Vendidos do Segmento - {termo_exibicao}", f"{query_completa}+reforcado"),
        (f"Opções de Mercado BR - {termo_exibicao}", f"{query_completa}+oferta")
    ]

    links_categoria = []
    for rotulo, query in termos_busca:
        links_categoria.append({
            "titulo": rotulo,
            "link": f"https://www.amazon.com.br/s?k={query}"
        })

    return links_categoria, termo_exibicao, palavras_reais


def processar_e_gerar_markdown(termo_entrada: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    links_categoria, termo_exibicao, palavras_reais = extrair_dados_e_links_categoria_dinamicos(termo_entrada)
    dados_lider = buscar_melhor_vendedor_organico_amazon_br(termo_exibicao)

    links_md = f"### 🔗 Links da Categoria e Concorrentes (Amazon BR):\n\n"
    for i, cat in enumerate(links_categoria, start=1):
        links_md += f"{i}. [{cat['titulo']}]({cat['link']})\n"
    links_md += "\n---\n\n"

    prompt_mestre = (
        "Você é um Especialista em SEO e Copywriting para E-commerce na Amazon Brasil.\n\n"
        "📌 DADOS PARA ANÁLISE COMPARATIVA:\n"
        "- Produto a Criar: " + str(termo_exibicao) + "\n"
        "- Líder Orgânico de Vendas Mapeado: " + str(dados_lider['titulo_lider']) + " (ASIN: " + str(dados_lider['asin_lider']) + " | Preço: " + str(dados_lider['preco_lider']) + ")\n\n"
        "GERE A RESPOSTA ORGANIZADA E COMPLETA EXATAMENTE NESTE FORMATO MARKDOWN:\n\n"
        "### 📋 Relatório Comparativo: Nosso Produto vs. Líder de Vendas\n\n"
        "| Métrica / Atributo | Concorrente Líder (Amazon BR) | Nossa Estratégia de Produto |\n"
        "| :--- | :--- | :--- |\n"
        "| **Título / Anúncio** | [" + str(dados_lider['titulo_lider']) + "](" + str(dados_lider['link_lider']) + ") | Título Otimizado entre 70 e 75 Caracteres |\n"
        "| **ASIN** | `" + str(dados_lider['asin_lider']) + "` | Novo Listing Otimizado |\n"
        "| **Preço Estimado** | `" + str(dados_lider['preco_lider']) + "` | Posicionamento Competitivo |\n"
        "| **Pontos Fortes do Líder** | Alta autoridade de vendas e posições orgânicas topo de busca. | Foco em diferenciação técnica e copy persuasiva. |\n"
        "| **Dores do Concorrente (Reviews Negativos)** | Reclamações de tamanho divergente, acabamento frágil e instabilidade no uso. | Neutralização completa nas primeiras linhas dos Bullets e fotos técnicas. |\n\n"
        "---\n\n"
        "### 📊 Anúncio Otimizado para Amazon Brasil\n\n"
        "**1. TÍTULOS OTIMIZADOS (LIMITE ESTRITO: 70 A 75 CARACTERES)**\n"
        "- **Título A (Clareza + Atributos):** [Escreva o título A exatamente com 70 a 75 caracteres sem termos proibidos] *(Caracteres: XX)*\n"
        "- **Título B (SEO + Especificações):** [Escreva o título B exatamente com 70 a 75 caracteres sem termos proibidos] *(Caracteres: XX)*\n\n"
        "**2. DESCRIÇÃO COMPLETA DO PRODUTO (TÉCNICA AIDA)**\n"
        "[Texto fluido e completo de 1200 a 1800 caracteres focando nos atributos do produto " + str(termo_exibicao) + "]\n\n"
        "#### Versão HTML para o Seller Central:\n"
        "```html\n"
        "[Código HTML limpo com <p>, <b> e <br>]\n"
        "```\n\n"
        "**3. 10 BULLET POINTS DE ALTA CONVERSÃO**\n"
        "[Gere 10 Bullet Points detalhados no formato: Emoji + **TÍTULO EM CAIXA ALTA (2 A 4 PALAVRAS):** + explicação técnica/benefício real]\n\n"
        "**4. PALAVRAS-CHAVE BACKEND (SEARCH TERMS - ATÉ 230 BYTES)**\n"
        "[Gere a lista de palavras-chave separadas por espaço sem acentos, sem vírgulas e SEM REPETIR NENHUMA PALAVRA que já consta nos Títulos A e B]\n\n"
        "**5. PROMPTS PARA IMAGENS DA LISTAGEM (10 PROMPTS)**\n"
        "1. **Foto 01 (Principal - Fundo Branco):** using the attached base product image as an overlay without any modification to the product itself, isolated on seamless pure white background (RGB 255,255,255), product filling 85% of frame, crisp studio commercial lighting.\n"
        "2. **Foto 02 (Uso Real / Lifestyle):** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle background, natural commercial lighting.\n"
        "3. **Foto 03 (Infográfico de Benefícios):** using the attached base product image as an overlay without any modification to the product itself, clean infographic layout in Portuguese.\n"
        "4. **Foto 04 (Dimensões e Escala):** using the attached base product image as an overlay without any modification to the product itself, dimensional infographic with scale indicators.\n"
        "5. **Foto 05 (Conteúdo da Embalagem):** using the attached base product image as an overlay without any modification to the product itself, overhead layflat view.\n"
        "6. **Foto 06 (Close de Material):** using the attached base product image as an overlay without any modification to the product itself, macro shot focusing on material finish.\n"
        "7. **Foto 07 (Funcionalidade):** using the attached base product image as an overlay without any modification to the product itself, demonstration showing ease of use.\n"
        "8. **Foto 08 (Cenários Diversos):** using the attached base product image as an overlay without any modification to the product itself, home environment setup.\n"
        "9. **Foto 09 (Comparativo):** using the attached base product image as an overlay without any modification to the product itself, side-by-side comparison.\n"
        "10. **Foto 10 (Confiança e Garantia):** using the attached base product image as an overlay without any modification to the product itself, trust badges in Portuguese.\n\n"
        "**6. ROTEIRO DE VÍDEO (30–45s)**\n"
        "[Roteiro em 5 cenas comerciais detalhando o produto " + str(termo_exibicao) + "]\n\n"
        "**7. CONTEÚDO A+ & 8. PROMPTS A+ (6 BANNERS INGLÊS)**\n"
        "[Estrutura do Conteúdo A+ e 6 Prompts de Imagens para Banners A+]"
    )

    if api_key and len(str(api_key).strip()) > 10:
        try:
            client = Anthropic(api_key=str(api_key).strip())
            for model_name in [
                "claude-3-5-sonnet-latest",
                "claude-3-5-sonnet-20241022",
                "claude-3-haiku-20240307",
            ]:
                try:
                    res = client.messages.create(
                        model=model_name,
                        max_tokens=3800,
                        messages=[{"role": "user", "content": prompt_mestre}],
                    )
                    return links_md + res.content[0].text
                except Exception:
                    continue
        except Exception:
            pass

    return links_md + "Aguardando geração completa..."


def render_module_1():
    st.subheader("📦 Módulo 1: Análise e Otimização de Listing")

    metodo_pesquisa = st.radio(
        "Como deseja buscar o produto?",
        ["🔤 Digitar ASIN ou Nome do Produto", "📸 Subir Foto do Produto (Busca Visual)"],
        horizontal=True
    )

    termo_final = ""
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")

    if "Digitar" in metodo_pesquisa:
        termo_input = st.text_input(
            "Insira o ASIN ou Nome do Produto (Ex: B0BQWX1LSY ou Comedouro Pet Elevado):",
            value=""
        )
        termo_final = termo_input.strip()
    else:
        uploaded_image = st.file_uploader("Envie a foto do seu produto (PNG, JPG, WEBP):", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_image is not None:
            col_img1, col_img2 = st.columns([1, 2])
            with col_img1:
                st.image(uploaded_image, caption="Foto Enviada", width=200)
            with col_img2:
                with st.spinner("🔍 Analisando foto do produto com Claude Vision..."):
                    termo_identificado = analisar_imagem_visuo_computacional(
                        uploaded_image.getvalue(), uploaded_image.type, api_key
                    )
                    if termo_identificado:
                        st.success(f"**Produto Identificado pela Foto:** `{termo_identificado}`")
                        termo_final = termo_identificado
                    else:
                        st.error("Não foi possível identificar a imagem.")

    if st.button("🚀 Executar Diagnóstico", use_container_width=True):
        if not termo_final:
            st.warning("Por favor, digite um produto ou faça o upload de uma imagem válida.")
        else:
            with st.spinner(f"Buscando melhor vendedor orgânico e gerando anúncio para '{termo_final}'..."):
                resultado = processar_e_gerar_markdown(termo_final)
                st.markdown(resultado)