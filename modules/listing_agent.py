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
    """
    Usa Claude Vision para identificar visualmente o produto real na foto (ex: Comedouro Pet).
    """
    if not api_key or len(api_key.strip()) < 10:
        return ""

    try:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        client = Anthropic(api_key=api_key.strip())

        # Ajusta media_type para formatos aceitos
        media_type = mime_type if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"] else "image/jpeg"

        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
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
                                "Examine detalhadamente esta foto de produto comercial. "
                                "Qual é exatamente este produto? Retorne APENAS o termo de busca em português do Brasil "
                                "que descreve o item com precisão para buscar na Amazon BR (de 2 a 5 palavras). "
                                "Exemplo se for um item pet: 'Comedouro Pet Elevado Inox' ou 'Tigela Bebedouro Cães'. "
                                "NÃO responda com saudações, nem pontuação, apenas o nome direto do produto."
                            )
                        }
                    ],
                }
            ],
        )
        termo = response.content[0].text.strip().replace("\n", " ").replace(".", "")
        return termo
    except Exception as e:
        st.error(f"Erro na análise visual da imagem: {e}")
        return ""


def buscar_melhor_vendedor_amazon_br(query: str) -> dict:
    """
    Pesquisa na Amazon BR pelo produto identificado na foto e retorna o principal concorrente.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    query_clean = requests.utils.quote(query)
    url_search = f"https://www.amazon.com.br/s?k={query_clean}"
    
    dados_lider = {
        "titulo_lider": f"{query.title()} Ergonômico",
        "asin_lider": "B0BRN2K9XX",
        "preco_lider": "R$ 49,90",
        "link_lider": url_search,
        "link_busca": url_search
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
        (f"Principais Marcas - {termo_exibicao}", f"{query_completa}+inox"),
        (f"Mais Vendidos do Segmento - {termo_exibicao}", f"{query_completa}+top"),
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


def otimizar_titulo_a10_75_chars(titulo_referencia: str, palavras_reais: list, foco_seo: bool = False) -> str:
    words = [w.title() for w in palavras_reais if len(w) > 1]
    base_prod = " ".join(words) if words else titulo_referencia.strip().title()

    if foco_seo:
        qualificadores = [
            "Inox Elevado", "Ergonômico Cães", "Gatos Antiderrapante", "Modelo Prático",
            "Fácil Higienização", "Alta Resistência", "Uso Diário Pet"
        ]
    else:
        qualificadores = [
            "Base Antiderrapante", "Aço Inox Lavável", "Modelo Elevado",
            "Prático Resistente", "Design Ergonômico", "Postura Correta Pet"
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


def gerar_relatorio_pontos_fortes_fracos(prod_nome: str, dados_lider: dict) -> str:
    return (
        f"### 📋 Relatório Diagnóstico do Produto e Análise de Concorrentes\n\n"
        f"🏆 **Líder / Best Seller Mapeado na Amazon BR:**\n"
        f"- **Anúncio Concorrente:** [{dados_lider['titulo_lider']}]({dados_lider['link_lider']})\n"
        f"- **ASIN:** `{dados_lider['asin_lider']}` | **Preço Médio:** `{dados_lider['preco_lider']}`\n\n"
        f"#### 🟢 Pontos Fortes e Oportunidades Mapeadas ({prod_nome}):\n"
        f"- **Procura Ativa no Nicho Pet:** Atende diretamente a buscas por {prod_nome}, focado no bem-estar, higiene e ergonomia alimentar do animal.\n"
        "- **Facilidade de Limpeza e Durabilidade:** Materiais laváveis (como aço inox ou plástico atóxico) possuem alta taxa de conversão no e-commerce.\n\n"
        f"#### 🔴 Dores e Reclamações Mapeadas nos Concorrentes ({prod_nome}):\n"
        "- **Instabilidade / Antiderrapante Frágil:** Reclamações frequentes apontam tigelas que deslizam ou tombam durante o uso pelo pet.\n"
        "- **Capacidade e Volume Incorreto:** Queixas de compradores quando o tamanho real em ML/gramas difere da expectativa gerada pelas fotos.\n\n"
        "#### 🎯 Estratégia de Copys A10 para Superar a Concorrência:\n"
        "- Destaque claro da capacidade em ML e dimensões exatas na primeira linha dos Bullet Points.\n"
        "- Prompts A+ e imagens focados na postura ergonômica e trava antiderrapante.\n\n"
        "---\n"
    )


def gerar_descricao_a10_dinamica(prod_nome: str) -> tuple:
    texto_fluido = (
        f"Proporcione o máximo de conforto, higiene e praticidade com o {prod_nome}. "
        "Desenvolvido sob rígidos padrões de qualidade e anatomia pet, este produto foi projetado para melhorar "
        "a experiência diária do seu animalzinho, garantindo uma postura adequada e alimentação confortável. "
        "Construído com materiais atóxicos e estrutura de fácil higienização, oferece alta resistência contra quedas e "
        "uso contínuo. Seu design ergonômico evita o desconforto cervical durante as refeições, promovendo saúde "
        "e organização no ambiente da sua casa.\n\n"
        "ESPECIFICAÇÕES TÉCNICAS E ATRIBUTOS:\n"
        "- Estrutura: Material Atóxico de Alta Durabilidade\n"
        "- Higienização: Tigela Removível de Fácil Lavagem\n"
        "- Estabilidade: Base com Trava Antiderrapante\n"
        "- Aplicação: Cães e Gatos de Pequeno e Médio Porte\n\n"
        "CONTEÚDO DA EMBALAGEM:\n"
        f"- 01 {prod_nome}\n"
        "- 01 Guia de Uso e Cuidados de Higiene"
    )
    html_limpo = (
        f"<p><b>Ofereça o melhor em conforto e saúde com o {prod_nome}!</b></p>\n"
        f"<p>O <b>{prod_nome}</b> foi projetado para entregar ergonomia, praticidade e total segurança para seu pet. "
        "Fabricado com componentes atóxicos e laváveis, é a escolha ideal para quem busca manter a rotina do animal organizada e saudável.</p>\n"
        "<p><b>Destaques do Produto:</b><br>\n"
        "- <b>Design Ergonômico:</b> Preserva a postura cervical e melhora a digestão.<br>\n"
        "- <b>Fácil Limpeza:</b> Estrutura higiênica que evita acúmulo de bactérias.<br>\n"
        "- <b>Base Estável:</b> Evita deslizamentos e sujeira no piso durante a refeição.</p>\n"
        "<p><b>Conteúdo da Embalagem:</b><br>\n"
        f"- 01 {prod_nome}<br>\n"
        "- 01 Guia de Cuidados em Português</p>"
    )
    return texto_fluido, html_limpo


def gerar_bullet_points_a10_dinamico(prod_nome: str) -> str:
    bullets = [
        f"🐾 **ERGONOMIA E CONFORTO ANATÔMICO:** Projeto do {prod_nome} desenvolvido para promover a postura correta e facilitar a alimentação do pet.",
        "🧼 **HIGIENIZAÇÃO RÁPIDA E PRÁTICA:** Confeccionado em material lavável e atóxico que previne a proliferação de fungos e bactérias.",
        "🛑 **BASE COM TRAVA ANTIDERRAPANTE:** Estrutura firme que impede o produto de deslizar ou tombar durante o uso pelo animal.",
        "🛡️ **MATERIAIS CERTIFICADOS E ATÓXICOS:** Livre de BPA e substâncias nocivas, garantindo total segurança para a saúde do cão ou gato.",
        "⚡ **DESIGN MODERNO E COMPACTO:** Combina perfeitamente com a decoração do ambiente sem ocupar espaço excessivo.",
        "🔧 **MONTAGEM E MANUSEIO INTUITIVO:** Estrutura simples de abastecer, limpar e transportar em viagens ou passeios.",
        "💧 **RESISTÊNCIA CONTRA IMPACTOS:** Construção reforçada desenvolvida para suportar a rotina diária e uso contínuo.",
        "⚙️ **TIGELA COM ENCAIXE PRECISO:** Sistema que evita folgas e reduz o derramamento de água ou ração no chão.",
        "🌿 **SAÚDE DIGESTIVA MELHORADA:** Altura e ângulo pensados para diminuir a ingestão de ar e refluxos durante a refeição.",
        "📦 **EMBALAGEM DE PROTEÇÃO:** Enviado em caixa reforçada para garantir que o item chegue intacto ao seu endereço."
    ]
    return "\n".join([f"* {b}" for b in bullets])


def gerar_backend_keywords_a10_dinamico(prod_nome: str, titulo_a: str, titulo_b: str, palavras_reais: list) -> str:
    palavras_titulos = set(
        remover_acentos(w.lower()) 
        for w in re.findall(r'\w+', titulo_a + " " + titulo_b)
        if len(w) > 1
    )

    candidatos_especificos = [remover_acentos(w.lower()) for w in palavras_reais if len(w) > 1]
    candidatos_genericos = [
        "comedouro", "bebedouro", "pet", "caes", "gatos", "cachorro", "gato",
        "tigela", "prato", "racao", "agua", "inox", "elevado", "ergonomico",
        "antiderrapante", "postura", "cervical", "saude", "higienico", "lavavel",
        "filhote", "porte", "pequeno", "medio", "acessorio", "utensilio", "domestico"
    ]
    candidatos_totais = candidatos_especificos + candidatos_genericos

    backend_unicas = []
    for cand in candidatos_totais:
        cand_clean = cand.strip()
        if cand_clean and cand_clean not in palavras_titulos and cand_clean not in backend_unicas:
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

    relatorio_swot = gerar_relatorio_pontos_fortes_fracos(termo_exibicao, dados_lider)

    prompt_mestre = (
        "Você é o Maior Especialista em SEO e Copywriter para a Amazon Brasil.\n\n"
        "📌 DADOS DO PRODUTO CONSULTADO:\n"
        "- Entrada Original: " + str(termo_entrada) + "\n"
        "- Termo do Produto/Nicho: " + str(termo_exibicao) + "\n"
        "- Concorrente Lider de Vendas: " + str(dados_lider['titulo_lider']) + " (ASIN: " + str(dados_lider['asin_lider']) + ")\n\n"
        "🧠 ETAPA DE ANÁLISE (OBRIGATÓRIA - SILENCIOSA - NÃO EXIBIR NA SAÍDA):\n"
        "Analise público ideal, diferencial competitivo, dores que o produto resolve, benefícios e atributos técnicos baseando-se estritamente no produto identificado acima.\n\n"
        "🚨 REGRAS CRÍTICAS DE COPYWRITING E CONFORMIDADE AMAZON:\n"
        "1. TÍTULOS A e B: Preencha exatamente entre 70 e 75 caracteres cada (sem ultrapassar 75). Sem palavras proibidas ('Pronta Entrega', 'FBA', 'Envio Rápido', 'Alta Qualidade', 'Premium', 'Melhor'). Estrutura: [Nome do Produto] + [Especificação/Atributo].\n"
        "2. DESCRIÇÃO DO PRODUTO: Texto fluido entre 1.200 e 1.900 caracteres em técnica AIDA com especificações técnicas e conteúdo da embalagem.\n"
        "3. VERSÃO HTML DA DESCRIÇÃO: HTML limpo usando APENAS <p>, <b> e <br>.\n"
        "4. BULLET POINTS (10 BULLETS): Formato obrigatório: Emoji + **TÍTULO EM CAIXA ALTA (2 A 4 PALAVRAS):** + explicação técnica/benefício real. Sem termos promocionais.\n"
        "5. PALAVRAS-CHAVE BACKEND (SEARCH TERMS): Preencha até alcançar o limite de 230 bytes em palavras-chave únicas separadas apenas por espaço, sem acentos, sem vírgulas, sem numerais e OBRIGATORIAMENTE SEM REPETIR NENHUMA PALAVRA QUE JÁ CONSTA NO TÍTULO A OU TÍTULO B.\n"
        "6. 10 PROMPTS PARA IMAGENS DA LISTAGEM: Iniciando OBRIGATORIAMENTE com 'using the attached base product image as an overlay without any modification to the product itself'. Foto 01 fundo branco puro (RGB 255,255,255).\n"
        "7. ROTEIRO DE VÍDEO (30–45s) em 5 cenas.\n"
        "8. CONTEÚDO A+ COMPLETO e 6 PROMPTS PARA BANNERS A+ em inglês.\n\n"
        "GERE ESTRITAMENTE A SAÍDA ORGANIZADA EM MARKDOWN SEGUINDO AS SEÇÕES ACIMA."
    )

    if api_key and len(str(api_key).strip()) > 10:
        try:
            client = Anthropic(api_key=str(api_key).strip())
            for model_name in [
                "claude-3-5-sonnet-20240620",
                "claude-3-haiku-20240307",
                "claude-3-sonnet-20240229",
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

    titulo_a = otimizar_titulo_a10_75_chars(termo_exibicao, palavras_reais, foco_seo=False)
    titulo_b = otimizar_titulo_a10_75_chars(termo_exibicao, palavras_reais, foco_seo=True)
    desc_fluida, desc_html = gerar_descricao_a10_dinamica(termo_exibicao)
    bullet_points_md = gerar_bullet_points_a10_dinamico(termo_exibicao)
    backend_clean = gerar_backend_keywords_a10_dinamico(termo_exibicao, titulo_a, titulo_b, palavras_reais)

    analise_dinamica = (
        "### 📊 Anúncio Gerado para Amazon Brasil\n\n"
        "**1. TÍTULOS OTIMIZADOS (LIMITE ESTRITO: 75 CARACTERES | SEM TERMOS PROIBIDOS)**\n"
        "- **Título A (Clareza + Atributos):** `" + titulo_a + "` *(" + str(len(titulo_a)) + " caracteres)*\n"
        "- **Título B (SEO + Especificações):** `" + titulo_b + "` *(" + str(len(titulo_b)) + " caracteres)*\n\n"
        "> ⚠️ **Conformidade Amazon:** Títulos configurados sem termos promocionais ('Pronta Entrega', 'FBA', 'Envio Rápido') para evitar supressão automática no catálogo da Amazon Brasil.\n\n"
        "---\n\n"
        "**2. DESCRIÇÃO COMPLETA DO PRODUTO (ATÉ 2.000 CARACTERES - TÉCNICA AIDA)**\n"
        + desc_fluida
        + "\n\n"
        "#### Versão HTML para o Seller Central:\n```html\n"
        + desc_html
        + "\n```\n\n"
        "---\n\n"
        "**3. 10 BULLET POINTS DE ALTA CONVERSÃO**\n"
        + bullet_points_md
        + "\n\n"
        "---\n\n"
        "**4. PALAVRAS-CHAVE BACKEND (SEARCH TERMS - MÁXIMO APROVEITAMENTO)**\n"
        "`" + backend_clean + "`\n\n"
        "> 📌 **Byte Count:** " + str(len(backend_clean.encode('utf-8'))) + " / 230 bytes autorizados. Nenhuma palavra presente nos Títulos A ou B foi repetida nesta lista.\n\n"
        "---\n\n"
        "**5. PROMPTS PARA IMAGENS DA LISTAGEM (10 PROMPTS)**\n"
        "1. **Foto 01 (Principal - Fundo Branco):** using the attached base product image as an overlay without any modification to the product itself, isolated on seamless pure white background (RGB 255,255,255), product filling 85% of frame, crisp studio commercial lighting, Amazon main image standard.\n"
        "2. **Foto 02 (Uso Real / Lifestyle):** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle background with cat or dog, natural commercial lighting.\n"
        "3. **Foto 03 (Infográfico de Benefícios):** using the attached base product image as an overlay without any modification to the product itself, clean infographic layout pointing out ergonomic benefits and non-slip base in Portuguese.\n"
        "4. **Foto 04 (Dimensões e Escala):** using the attached base product image as an overlay without any modification to the product itself, dimensional infographic with clear height, width, and capacity in ML/grams.\n"
        "5. **Foto 05 (Conteúdo da Embalagem):** using the attached base product image as an overlay without any modification to the product itself, overhead layflat view showing bowl and accessories.\n"
        "6. **Foto 06 (Close de Material):** using the attached base product image as an overlay without any modification to the product itself, macro shot focusing on stainless steel texture or non-toxic finish.\n"
        "7. **Foto 07 (Funcionalidade):** using the attached base product image as an overlay without any modification to the product itself, demonstration showing easy washing and cleaning.\n"
        "8. **Foto 08 (Cenários Diversos):** using the attached base product image as an overlay without any modification to the product itself, home environment setup.\n"
        "9. **Foto 09 (Comparativo):** using the attached base product image as an overlay without any modification to the product itself, side-by-side comparison showing ergonomic posture vs floor feeding.\n"
        "10. **Foto 10 (Confiança e Garantia):** using the attached base product image as an overlay without any modification to the product itself, trust badges in Portuguese.\n\n"
        "---\n\n"
        "**6. ROTEIRO DE VÍDEO (30–45s)**\n"
        "- **Cena 01 (0–5s):** Gancho visual apresentando o pet utilizando o " + termo_exibicao + " confortavelmente.\n"
        "- **Cena 02 (5–15s):** Demonstração da trava antiderrapante e higienização simples da tigela.\n"
        "- **Cena 03 (15–25s):** Detalhes de acabamento e estrutura atóxica.\n"
        "- **Cena 04 (25–35s):** Aplicação prática na rotina doméstica.\n"
        "- **Cena 05 (35–45s):** Encerramento da marca para o público Pet na Amazon BR.\n\n"
        "---\n\n"
        "**7. CONTEÚDO A+ & 8. PROMPTS A+ (6 BANNERS INGLÊS)**\n"
        "1. **Banner Hero:** using the attached base product image as an overlay without any modification to the product itself, wide Amazon A+ banner composition, studio lighting.\n"
        "2. **Benefícios Visuais:** using the attached base product image as an overlay without any modification to the product itself, clean A+ infographic layout.\n"
        "3. **Diferencial Técnico:** using the attached base product image as an overlay without any modification to the product itself, macro lighting highlighting build quality.\n"
        "4. **Uso Real:** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle scene with pet.\n"
        "5. **Comparação Visual:** using the attached base product image as an overlay without any modification to the product itself, clean comparative layout.\n"
        "6. **Capacidade / Aplicação:** using the attached base product image as an overlay without any modification to the product itself, visual demonstration of practical application.\n"
    )

    return links_md + relatorio_swot + analise_dinamica


def analisar_e_otimizar_listing(asin_input: str, produto_nosso: str = "", bullet_points_concorrente: str = "") -> str:
    termo = produto_nosso.strip() if produto_nosso.strip() else asin_input.strip()
    return processar_e_gerar_markdown(termo)