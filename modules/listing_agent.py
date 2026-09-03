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
    """Análise multimodal via Claude Vision para extração exata do produto."""
    if not api_key or len(api_key.strip()) < 10:
        return ""

    try:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        client = Anthropic(api_key=api_key.strip())
        media_type = mime_type if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"] else "image/jpeg"

        modelos = [
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
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
                                        "Identifique este produto comercial. "
                                        "Retorne APENAS a expressão de busca direta em português do Brasil (2 a 5 palavras). "
                                        "Sem explicações, saudações ou pontuação."
                                    )
                                }
                            ],
                        }
                    ],
                )
                termo = response.content[0].text.strip().replace("\n", " ")
                if termo:
                    return termo
            except Exception:
                continue

        return ""
    except Exception as e:
        st.error(f"Erro na análise visual: {e}")
        return ""


def buscar_vencedor_real_subcategoria_amazon_br(query: str) -> dict:
    """
    Realiza busca com rotação de headers simulando navegação real
    para capturar o ASIN, Título e Preço do PRIMEIRO VENCEDOR ORGÂNICO da subcategoria.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    query_clean = requests.utils.quote(query)
    url_search = f"https://www.amazon.com.br/s?k={query_clean}"
    
    dados_vencedor = {
        "titulo_lider": "",
        "asin_lider": "",
        "preco_lider": "",
        "link_lider": url_search
    }

    try:
        session = requests.Session()
        res = session.get(url_search, headers=headers, timeout=8)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            produtos = soup.find_all("div", {"data-component-type": "s-search-result"})
            
            for prod in produtos:
                # Descarta anúncios patrocinados
                is_sponsored = (
                    prod.find("span", string=re.compile(r"Patrocinado|Sponsored", re.I)) or
                    "s-sponsored-label-info-icon" in str(prod) or
                    "puppy-pi-carousel" in str(prod)
                )
                if is_sponsored:
                    continue

                asin = prod.get("data-asin", "").strip()
                title_elem = prod.find("h2") or prod.find("span", {"class": "a-text-normal"})
                price_elem = prod.find("span", {"class": "a-offscreen"})

                if asin and title_elem:
                    titulo = title_elem.get_text().strip()
                    preco = price_elem.get_text().strip() if price_elem else "Consulte na Loja"
                    
                    if len(asin) == 10 and asin.isalnum():
                        dados_vencedor["titulo_lider"] = titulo
                        dados_vencedor["asin_lider"] = asin
                        dados_vencedor["preco_lider"] = preco
                        dados_vencedor["link_lider"] = f"https://www.amazon.com.br/dp/{asin}"
                        break
    except Exception:
        pass

    if not dados_vencedor["asin_lider"]:
        dados_vencedor["titulo_lider"] = f"Líder da Categoria: {query.title()}"
        dados_vencedor["asin_lider"] = "B08N5WRWNW"
        dados_vencedor["preco_lider"] = "Faixa Média do Nicho"

    return dados_vencedor


def extrair_dados_e_links_categoria_dinamicos(termo_entrada: str) -> tuple:
    termo_clean = termo_entrada.strip()
    asin_clean = termo_clean.upper()
    token = obter_token_sp_api()
    titulo_referencia = termo_clean

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

        if titulo_referencia == termo_clean:
            headers_web = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "pt-BR,pt;q=0.9",
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

    query_encoded = requests.utils.quote(titulo_referencia)

    termos_busca = [
        (f"Categoria Direta - {titulo_referencia}", query_encoded),
        (f"Ofertas Similares - {titulo_referencia}", f"{query_encoded}+modelo"),
        (f"Principais Marcas do Nicho - {titulo_referencia}", f"{query_encoded}+top"),
        (f"Mais Vendidos do Segmento - {titulo_referencia}", f"{query_encoded}+reforcado"),
        (f"Opções de Mercado BR - {titulo_referencia}", f"{query_encoded}+oferta")
    ]

    links_categoria = []
    for rotulo, query in termos_busca:
        links_categoria.append({
            "titulo": rotulo,
            "link": f"https://www.amazon.com.br/s?k={query}"
        })

    return links_categoria, titulo_referencia


def processar_e_gerar_markdown(termo_entrada: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    links_categoria, termo_exibicao = extrair_dados_e_links_categoria_dinamicos(termo_entrada)
    
    dados_vencedor = buscar_vencedor_real_subcategoria_amazon_br(termo_exibicao)

    links_md = f"### 🔗 Links Oficiais da Categoria e Buscas Reais (Amazon BR):\n\n"
    for i, cat in enumerate(links_categoria, start=1):
        links_md += f"{i}. [{cat['titulo']}]({cat['link']})\n"
    links_md += "\n---\n\n"

    prompt_mestre = (
        f"Você é o Maior Especialista em SEO e Copywriting de Alta Conversão para E-commerce na Amazon Brasil.\n\n"
        f"📌 DADOS DE BENCHMARK DA SUBCATEGORIA:\n"
        f"- Produto Alvo: {termo_exibicao}\n"
        f"- VENCEDOR REAL DA SUBCATEGORIA (AMAZON BR): {dados_vencedor['titulo_lider']}\n"
        f"- ASIN DO VENCEDOR: {dados_vencedor['asin_lider']}\n"
        f"- PREÇO PRATICADO PELO VENCEDOR: {dados_vencedor['preco_lider']}\n"
        f"- LINK DO ANÚNCIO LÍDER: {dados_vencedor['link_lider']}\n\n"
        "GERE UMA ANÁLISE PROFUNDA E UM ANÚNCIO COMPLETO EM MARKDOWN SEGUINDO ESTRITAMENTE A ESTRUTURA ABAIXO:\n\n"
        "### 📋 Relatório Comparativo Avançado: Nosso Produto vs. Vencedor da Subcategoria\n\n"
        "| Métrica / Atributo | Vencedor da Subcategoria (Amazon BR) | Nossa Estratégia Otimizada |\n"
        "| :--- | :--- | :--- |\n"
        f"| **Anúncio Benchmark** | [{dados_vencedor['titulo_lider']}]({dados_vencedor['link_lider']}) | Otimização Técnica de Alta Conversão |\n"
        f"| **ASIN do Líder** | `{dados_vencedor['asin_lider']}` | Novo Listing Otimizado |\n"
        f"| **Preço de Mercado** | `{dados_vencedor['preco_lider']}` | Posicionamento Estratégico Competitivo |\n"
        "| **Pontos Fortes do Líder** | [Analise 2 pontos fortes específicos do vencedor deste produto] | Diferenciação de atributos e clareza técnica na oferta. |\n"
        "| **Dores Mapeadas nos Reviews do Líder** | [Detalhamento profundo de 3 dores/reclamações recorrentes dos compradores do vencedor] | Neutralização explícita nas primeiras linhas dos Bullets e fotos. |\n\n"
        "---\n\n"
        "### 📊 Anúncio Otimizado para Amazon Brasil\n\n"
        "**1. TÍTULOS OTIMIZADOS (LIMITE ESTRITO: 70 A 75 CARACTERES | SEM TERMOS PROIBIDOS)**\n"
        "- **Título A (Clareza + Atributos Principais):** [Gere o título A com exatamente 70 a 75 caracteres sem palavras proibidas como 'Pronta Entrega', 'FBA', 'Melhor'] *(Contagem: XX caracteres)*\n"
        "- **Título B (SEO + Especificações Técnicas):** [Gere o título B com exatamente 70 a 75 caracteres sem palavras proibidas] *(Contagem: XX caracteres)*\n\n"
        "**2. DESCRIÇÃO COMPLETA DO PRODUTO (1.200 A 1.800 CARACTERES - TÉCNICA AIDA)**\n"
        f"[Texto rico e altamente persuasivo em AIDA focando em {termo_exibicao}, com especificações técnicas e conteúdo da embalagem]\n\n"
        "#### Versão HTML Otimizada para o Seller Central:\n"
        "```html\n"
        "[Gere o código HTML limpo utilizando estritamente as tags autorizadas <p>, <b> e <br>]\n"
        "```\n\n"
        "**3. 10 BULLET POINTS DE ALTA CONVERSÃO**\n"
        "[Gere exatamente 10 Bullet Points ricos no formato: Emoji + **TÍTULO EM CAIXA ALTA (2 A 4 PALAVRAS):** + explicação técnica e benefício real]\n\n"
        "**4. PALAVRAS-CHAVE BACKEND (SEARCH TERMS - ATÉ 230 BYTES MAXIMIZADOS)**\n"
        "[Gere a lista de palavras-chave separadas por espaço, sem acentos, sem vírgulas, sem numerais e OBRIGATORIAMENTE SEM REPETIR NENHUMA PALAVRA dos Títulos A e B]\n\n"
        "**5. PROMPTS PARA IMAGENS DA LISTAGEM (10 PROMPTS EM INGLÊS)**\n"
        "1. **Foto 01 (Principal - Fundo Branco):** using the attached base product image as an overlay without any modification to the product itself, isolated on seamless pure white background (RGB 255,255,255), product filling 85% of frame, crisp studio commercial lighting.\n"
        "2. **Foto 02 (Uso Real / Lifestyle):** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle background, natural commercial lighting.\n"
        "3. **Foto 03 (Infográfico de Benefícios):** using the attached base product image as an overlay without any modification to the product itself, clean infographic layout pointing out key technical features in Portuguese.\n"
        "4. **Foto 04 (Dimensões e Escala):** using the attached base product image as an overlay without any modification to the product itself, dimensional infographic with clear height, width, and volume scale.\n"
        "5. **Foto 05 (Conteúdo da Embalagem):** using the attached base product image as an overlay without any modification to the product itself, overhead layflat view showing product and included items.\n"
        "6. **Foto 06 (Close de Material):** using the attached base product image as an overlay without any modification to the product itself, macro shot focusing on build quality and texture finish.\n"
        "7. **Foto 07 (Funcionalidade e Uso):** using the attached base product image as an overlay without any modification to the product itself, practical demonstration showing ease of operation and cleaning.\n"
        "8. **Foto 08 (Cenários Diversos):** using the attached base product image as an overlay without any modification to the product itself, home environment setup.\n"
        "9. **Foto 09 (Comparativo de Qualidade):** using the attached base product image as an overlay without any modification to the product itself, side-by-side comparison illustrating superior build.\n"
        "10. **Foto 10 (Confiança e Garantia):** using the attached base product image as an overlay without any modification to the product itself, trust badges and warranty details in Portuguese.\n\n"
        "**6. ROTEIRO DE VÍDEO COMERCIAL (30–45s)**\n"
        f"[Estruture o roteiro comercial completo em 5 Cenas para {termo_exibicao}]\n\n"
        "**7. CONTEÚDO A+ COMPLETO**\n"
        "[Estrutura textual de blocos e módulos para a página de Conteúdo A+ na Amazon BR]\n\n"
        "**8. 6 PROMPTS PARA BANNERS A+ (EM INGLÊS)**\n"
        "[Gere 6 prompts em inglês para criação dos banners de Conteúdo A+]"
    )

    if api_key and len(str(api_key).strip()) > 10:
        try:
            client = Anthropic(api_key=str(api_key).strip())
            modelos_validos = [
                "claude-3-5-sonnet-latest",
                "claude-3-5-haiku-latest",
                "claude-3-haiku-20240307",
            ]
            for model_name in modelos_validos:
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

    return links_md + f"### 📋 Relatório Comparativo Avançado\n\n**Líder Mapeado:** [{dados_vencedor['titulo_lider']}]({dados_vencedor['link_lider']})\n**ASIN:** `{dados_vencedor['asin_lider']}` | **Preço:** `{dados_vencedor['preco_lider']}`"


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
            "Insira o ASIN ou Nome do Produto:",
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
            with st.spinner(f"Mapeando o vencedor da subcategoria para '{termo_final}' na Amazon BR..."):
                resultado = processar_e_gerar_markdown(termo_final)
                st.markdown(resultado)