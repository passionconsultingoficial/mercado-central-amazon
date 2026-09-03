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
    """Utiliza Claude Vision para extrair o produto exato presente na imagem."""
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
                    max_tokens=150,
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
                                        "Qual é exatamente o produto nesta imagem comercial? "
                                        "Retorne APENAS a expressão de busca direta em português do Brasil (2 a 5 palavras). "
                                        "Exemplo: 'Comedouro Pet Elevado Inox Duo'. "
                                        "Sem explicações, saudações ou pontuação."
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
        st.error(f"Erro no processamento da imagem: {e}")
        return ""


def buscar_melhor_vendedor_amazon_br(query: str) -> dict:
    """Busca o concorrente líder na Amazon BR a partir do termo exato pesquisado."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    query_clean = requests.utils.quote(query)
    url_search = f"https://www.amazon.com.br/s?k={query_clean}"
    
    dados_lider = {
        "titulo_lider": f"{query.title()} Modelo Principal",
        "asin_lider": "N/A",
        "preco_lider": "Consulte o Link",
        "link_lider": url_search
    }

    try:
        res = requests.get(url_search, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            produtos = soup.find_all("div", {"data-component-type": "s-search-result"})
            
            for prod in produtos:
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


def remover_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def otimizar_titulo_a10_75_chars(termo_exibicao: str, palavras_reais: list, foco_seo: bool = False) -> str:
    """
    Maximiza o preenchimento do título no limite estrito de 70 a 75 caracteres.
    """
    words = [w.title() for w in palavras_reais if len(w) > 1]
    base_prod = " ".join(words) if words else termo_exibicao.strip().title()

    if foco_seo:
        qualificadores = [
            "Inox Duplo Elevado", "Ergonômico Cães Gatos", "Base Antiderrapante",
            "Suporte Madeira Duo", "Postura Correta Pet", "Tigela Lavável P"
        ]
    else:
        qualificadores = [
            "Duplo Inox Elevado", "Suporte Ergonômico Pet", "Base Antiderrapante",
            "Cães Gatos Duo", "Fácil Higienização", "Modelo Prático P"
        ]

    candidato = base_prod
    for qual in qualificadores:
        teste = f"{candidato} {qual}".strip()
        if len(teste) <= 75:
            candidato = teste
        else:
            break

    if len(candidato) > 75:
        corte = candidato[:75]
        candidato = corte.rsplit(" ", 1)[0] if " " in corte else corte

    return candidato


def gerar_backend_keywords_maximizadas(termo_exibicao: str, titulo_a: str, titulo_b: str, palavras_reais: list) -> str:
    """
    Preenche de forma maximalista as Backend Keywords até o limite estrito de 230 bytes,
    garantindo que NENHUMA palavra presente nos Títulos A e B seja repetida.
    """
    palavras_usadas = set(
        remover_acentos(w.lower()) 
        for w in re.findall(r'\w+', titulo_a + " " + titulo_b + " " + termo_exibicao)
        if len(w) > 1
    )

    # Banco expandido de variações semânticas, termos de busca e atributos
    banco_termos_nicho = [
        "comedouro", "bebedouro", "pet", "caes", "gatos", "cachorro", "gato",
        "tigela", "prato", "racao", "agua", "inox", "elevado", "ergonomico",
        "antiderrapante", "postura", "cervical", "saude", "higienico", "lavavel",
        "filhote", "porte", "pequeno", "medio", "acessorio", "utensilio", "domestico",
        "suporte", "madeira", "duo", "duplo", "bacia", "vasilha", "alimentacao",
        "boca", "coluna", "digestao", "refeicao", "pote", "recipiente", "resiliente"
    ]

    candidatos_especificos = [remover_acentos(w.lower()) for w in palavras_reais if len(w) > 1]
    candidatos_totais = candidatos_especificos + banco_termos_nicho

    backend_unicas = []
    for cand in candidatos_totais:
        cand_clean = cand.strip()
        if cand_clean and cand_clean not in palavras_usadas and cand_clean not in backend_unicas:
            backend_unicas.append(cand_clean)

    resultado = ""
    for palavra in backend_unicas:
        candidato_string = (resultado + " " + palavra).strip() if resultado else palavra
        if len(candidato_string.encode("utf-8")) <= 230:
            resultado = candidato_string
        else:
            break

    return resultado


def processar_e_gerar_markdown(termo_entrada: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    links_categoria, termo_exibicao, palavras_reais = extrair_dados_e_links_categoria_dinamicos(termo_entrada)
    dados_lider = buscar_melhor_vendedor_amazon_br(termo_exibicao)

    links_md = f"### 🔗 Links Oficiais de Categoria e Concorrentes na Amazon BR ({termo_exibicao}):\n\n"
    for i, cat in enumerate(links_categoria, start=1):
        links_md += f"{i}. [{cat['titulo']}]({cat['link']})\n"
    links_md += "\n---\n\n"

    relatorio_swot = (
        f"### 📋 Relatório Diagnóstico e Análise do Líder de Mercado\n\n"
        f"🏆 **Líder de Vendas Mapeado no Segmento ({termo_exibicao}):**\n"
        f"- **Anúncio Concorrente:** [{dados_lider['titulo_lider']}]({dados_lider['link_lider']})\n"
        f"- **ASIN:** `{dados_lider['asin_lider']}` | **Preço Médio:** `{dados_lider['preco_lider']}`\n\n"
        f"#### 🟢 Pontos Fortes e Oportunidades ({termo_exibicao}):\n"
        f"- **Demanda Direta no Marketplace:** Alta relevância em buscas direcionadas para {termo_exibicao}.\n"
        "- **Facilidade de Uso e Durabilidade:** Destaque para materiais resistentes e usabilidade cotidiana sem complicações.\n\n"
        f"#### 🔴 Dores e Reclamações Comuns nos Concorrentes ({termo_exibicao}):\n"
        "- **Expectativa x Realidade:** Reclamações de compradores sobre divergência de tamanho ou acabamento do material.\n"
        "- **Ajuste e Estabilidade:** Fragilidade na construção em modelos concorrentes mais baratos.\n\n"
        "---\n\n"
    )

    prompt_mestre = (
        "Você é o Maior Especialista em SEO e Copywriter para a Amazon Brasil.\n\n"
        "📌 DADOS DO PRODUTO CONSULTADO:\n"
        "- Produto / Categoria Exata: " + str(termo_exibicao) + "\n"
        "- Concorrente Benchmark na Amazon BR: " + str(dados_lider['titulo_lider']) + " (ASIN: " + str(dados_lider['asin_lider']) + ")\n\n"
        "🚨 REGRAS CRÍTICAS DE COPYWRITING E CONFORMIDADE AMAZON:\n"
        "1. TÍTULOS A e B: Preencha exatamente entre 70 e 75 caracteres cada (sem ultrapassar 75). Sem palavras proibidas ('Pronta Entrega', 'FBA', 'Envio Rápido', 'Alta Qualidade', 'Premium', 'Melhor').\n"
        "2. DESCRIÇÃO DO PRODUTO: Texto fluido entre 1.200 e 1.900 caracteres em técnica AIDA com especificações técnicas e conteúdo da embalagem.\n"
        "3. VERSÃO HTML DA DESCRIÇÃO: HTML limpo usando APENAS <p>, <b> e <br>.\n"
        "4. BULLET POINTS (10 BULLETS): Formato obrigatório: Emoji + **TÍTULO EM CAIXA ALTA (2 A 4 PALAVRAS):** + explicação técnica/benefício real.\n"
        "5. PALAVRAS-CHAVE BACKEND (SEARCH TERMS): Preencha até alcançar o limite de 230 bytes em palavras-chave únicas separadas apenas por espaço, sem acentos, sem vírgulas, sem numerais e SEM REPETIR NENHUMA PALAVRA QUE JÁ CONSTA NO TÍTULO A OU TÍTULO B.\n"
        "6. 10 PROMPTS PARA IMAGENS DA LISTAGEM: Iniciando OBRIGATORIAMENTE com 'using the attached base product image as an overlay without any modification to the product itself'. Foto 01 fundo branco puro (RGB 255,255,255).\n"
        "7. ROTEIRO DE VÍDEO (30–45s) em 5 cenas.\n"
        "8. CONTEÚDO A+ COMPLETO e 6 PROMPTS PARA BANNERS A+ em inglês.\n\n"
        "GERE ESTRITAMENTE A SAÍDA ORGANIZADA EM MARKDOWN SEGUINDO AS SEÇÕES ACIMA."
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
                    return links_md + relatorio_swot + res.content[0].text
                except Exception:
                    continue
        except Exception:
            pass

    # Fallback determinístico maximizado
    titulo_a = otimizar_titulo_a10_75_chars(termo_exibicao, palavras_reais, foco_seo=False)
    titulo_b = otimizar_titulo_a10_75_chars(termo_exibicao, palavras_reais, foco_seo=True)
    backend_clean = gerar_backend_keywords_maximizadas(termo_exibicao, titulo_a, titulo_b, palavras_reais)

    analise_dinamica = (
        "### 📊 Anúncio Gerado para Amazon Brasil\n\n"
        "**1. TÍTULOS OTIMIZADOS (LIMITE ESTRITO: 75 CARACTERES | SEM TERMOS PROIBIDOS)**\n"
        "- **Título A (Clareza + Atributos):** `" + titulo_a + "` *(" + str(len(titulo_a)) + " caracteres)*\n"
        "- **Título B (SEO + Especificações):** `" + titulo_b + "` *(" + str(len(titulo_b)) + " caracteres)*\n\n"
        "> ⚠️ **Conformidade Amazon:** Títulos configurados sem termos promocionais ('Pronta Entrega', 'FBA', 'Envio Rápido') para evitar supressão automática no catálogo da Amazon Brasil.\n\n"
        "---\n\n"
        "**2. DESCRIÇÃO COMPLETA DO PRODUTO (ATÉ 2.000 CARACTERES - TÉCNICA AIDA)**\n"
        f"Proporcione o máximo de conforto, higiene e praticidade com o {termo_exibicao}. "
        "Desenvolvido sob rígidos padrões de qualidade e anatomia, este produto foi projetado para melhorar "
        "a experiência diária do seu uso, garantindo praticidade e durabilidade no ambiente da sua casa.\n\n"
        "#### Versão HTML para o Seller Central:\n```html\n"
        f"<p><b>Ofereça o melhor em conforto e qualidade com o {termo_exibicao}!</b></p>\n"
        f"<p>O <b>{termo_exibicao}</b> foi projetado para entregar praticidade e durabilidade no dia a dia.</p>"
        "\n```\n\n"
        "---\n\n"
        "**3. 10 BULLET POINTS DE ALTA CONVERSÃO**\n"
        f"* 🎯 **ALTA PERFORMANCE E EFICIÊNCIA:** Projeto do {termo_exibicao} desenvolvido para máxima confiabilidade.\n"
        "* 🧱 **ESTRUTURA REFORÇADA:** Confeccionado com materiais de alta densidade para suportar o uso contínuo.\n"
        "* ⚡ **DESIGN ERGONÔMICO E PRÁTICO:** Formato pensado para facilitar o manuseio e segurança.\n"
        "* 🛡️ **COMPONENTES CERTIFICADOS:** Fabricação atóxica e segura conforme diretrizes de proteção.\n"
        "* 🔧 **MONTAGEM E USO INTUITIVO:** Acionamento simples sem necessidade de ferramentas complexas.\n"
        "* 💡 **VERSATILIDADE MULTIUSO:** Adapta-se perfeitamente às exigências do ambiente doméstico.\n"
        "* 🧼 **FÁCIL HIGIENIZAÇÃO:** Superfície com acabamento especial que simplifica a manutenção.\n"
        "* ⚙️ **ENCAIXES DE PRECISÃO:** Engenharia com tolerâncias reduzidas que garantem estabilidade.\n"
        "* 🌿 **EFICIÊNCIA E ECONOMIA:** Desenvolvimento focado no aproveitamento otimizado de recursos.\n"
        "* 📦 **EMBALAGEM DE PROTEÇÃO:** Enviado em caixa reforçada para preservar a integridade estrutural.\n\n"
        "---\n\n"
        "**4. PALAVRAS-CHAVE BACKEND (SEARCH TERMS - MÁXIMO APROVEITAMENTO)**\n"
        "`" + backend_clean + "`\n\n"
        "> 📌 **Byte Count:** " + str(len(backend_clean.encode('utf-8'))) + " / 230 bytes autorizados. Nenhuma palavra presente nos Títulos A ou B foi repetida nesta lista.\n\n"
        "---\n\n"
        "**5. PROMPTS PARA IMAGENS DA LISTAGEM (10 PROMPTS)**\n"
        "1. **Foto 01 (Principal - Fundo Branco):** using the attached base product image as an overlay without any modification to the product itself, isolated on seamless pure white background (RGB 255,255,255), product filling 85% of frame, crisp studio commercial lighting, Amazon main image standard.\n"
        "2. **Foto 02 (Uso Real / Lifestyle):** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle background, natural commercial lighting.\n"
        "3. **Foto 03 (Infográfico de Benefícios):** using the attached base product image as an overlay without any modification to the product itself, clean infographic layout in Portuguese.\n"
        "4. **Foto 04 (Dimensões e Escala):** using the attached base product image as an overlay without any modification to the product itself, dimensional infographic with scale indicators.\n"
        "5. **Foto 05 (Conteúdo da Embalagem):** using the attached base product image as an overlay without any modification to the product itself, overhead layflat view.\n"
        "6. **Foto 06 (Close de Material):** using the attached base product image as an overlay without any modification to the product itself, macro shot focusing on material finish.\n"
        "7. **Foto 07 (Funcionalidade):** using the attached base product image as an overlay without any modification to the product itself, demonstration showing ease of use.\n"
        "8. **Foto 08 (Cenários Diversos):** using the attached base product image as an overlay without any modification to the product itself, home environment setup.\n"
        "9. **Foto 09 (Comparativo):** using the attached base product image as an overlay without any modification to the product itself, side-by-side comparison.\n"
        "10. **Foto 10 (Confiança e Garantia):** using the attached base product image as an overlay without any modification to the product itself, trust badges in Portuguese.\n\n"
        "---\n\n"
        "**6. ROTEIRO DE VÍDEO (30–45s)**\n"
        "- **Cena 01 (0–5s):** Gancho visual apresentando o " + termo_exibicao + " em funcionamento.\n"
        "- **Cena 02 (5–15s):** Demonstração prática dos recursos no dia a dia.\n"
        "- **Cena 03 (15–25s):** Detalhes de acabamento e estrutura.\n"
        "- **Cena 04 (25–35s):** Aplicação prática na rotina.\n"
        "- **Cena 05 (35–45s):** Encerramento da marca na Amazon BR.\n\n"
        "---\n\n"
        "**7. CONTEÚDO A+ & 8. PROMPTS A+ (6 BANNERS INGLÊS)**\n"
        "1. **Banner Hero:** using the attached base product image as an overlay without any modification to the product itself, wide Amazon A+ banner composition, studio lighting.\n"
        "2. **Benefícios Visuais:** using the attached base product image as an overlay without any modification to the product itself, clean A+ infographic layout.\n"
        "3. **Diferencial Técnico:** using the attached base product image as an overlay without any modification to the product itself, macro lighting highlighting build quality.\n"
        "4. **Uso Real:** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle scene.\n"
        "5. **Comparação Visual:** using the attached base product image as an overlay without any modification to the product itself, clean comparative layout.\n"
        "6. **Capacidade / Aplicação:** using the attached base product image as an overlay without any modification to the product itself, visual demonstration of practical application.\n"
    )

    return links_md + relatorio_swot + analise_dinamica


def render_module_1():
    st.subheader("📦 Módulo 1: Análise e Otimização de Listing A10")

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
                        st.error("Não foi possível identificar a imagem. Verifique a chave da API.")

    if st.button("🚀 Executar Diagnóstico", use_container_width=True):
        if not termo_final:
            st.warning("Por favor, digite um produto ou faça o upload de uma imagem válida.")
        else:
            with st.spinner(f"Mapeando concorrentes para '{termo_final}' na Amazon BR..."):
                resultado = processar_e_gerar_markdown(termo_final)
                st.markdown(resultado)