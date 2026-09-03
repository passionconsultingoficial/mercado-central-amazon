import os
import re
import requests
import unicodedata
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic

# Limpa o cache do Streamlit
try:
    st.cache_data.clear()
except Exception:
    pass


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


def extrair_dados_e_links_categoria(asin_input: str) -> tuple:
    """
    Identifica o produto base e gera links de categoria/busca seguros na Amazon BR.
    Garante 0% de erro 404 e abre a lista de concorrentes do nicho.
    """
    asin_clean = asin_input.strip().upper()
    token = obter_token_sp_api()
    titulo_referencia = f"Produto ASIN {asin_clean}"

    # 1. Consulta o título real via SP-API
    if token and len(asin_clean) == 10 and asin_clean.isalnum():
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

    # 2. Resolução de palavras-chave para montar links de categoria confiáveis
    if "BQWX" in asin_clean or "PRENSA" in titulo_referencia.upper() or "CAFETEIRA" in titulo_referencia.upper():
        nome_nicho = "Cafeteira Prensa Francesa Vidro Borossilicato"
        termos_busca = [
            ("Prensa Francesa 600ml", "prensa+francesa+600ml"),
            ("Cafeteira de Vidro e Inox", "cafeteira+vidro+inox"),
            ("Prensa Francesa Bodum / Bialetti", "prensa+francesa+bialetti"),
            ("Prensa Francesa Cafeteira Manual", "prensa+francesa+cafeteira"),
            ("Infusor de Café e Chá Vidro", "infusor+cafe+prensa+francesa")
        ]
    else:
        words = [w for w in re.findall(r'\w+', titulo_referencia) if len(w) > 3]
        base_kw = "+".join(words[:3]) if words else asin_clean
        nome_nicho = " ".join(words[:4]).title() if words else titulo_referencia
        termos_busca = [
            (f"Categoria Principal - {nome_nicho}", base_kw),
            (f"Ofertas Similares - {nome_nicho}", f"{base_kw}+modelo"),
            (f"Principais Marcas - {nome_nicho}", f"{base_kw}+premium"),
            (f"Mais Vendidos - {nome_nicho}", f"{base_kw}+oferta"),
            (f"Comparativo de Mercado - {nome_nicho}", f"{base_kw}+opcoes")
        ]

    links_categoria = []
    for rotulo, query in termos_busca:
        links_categoria.append({
            "titulo": rotulo,
            "link": f"https://www.amazon.com.br/s?k={query}"
        })

    return links_categoria, nome_nicho


def remover_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def otimizar_titulo_a10_75_chars(nome_produto: str, foco_seo: bool = False) -> str:
    clean_name = nome_produto.strip().title()
    
    if "Cafeteira" in clean_name or "Prensa" in clean_name or "Allmix" in clean_name:
        sufixo_a = " Prensa Francesa De Vidro Borossilicato 600ml"
        sufixo_b = " Cafeteira Vidro Borossilicato Hermético 600ml"
    elif "Umidificador" in clean_name or "Difusor" in clean_name:
        sufixo_a = " Ultrassônico Silencioso Aromaterapia Bivolt Led"
        sufixo_b = " Portátil Com Luz Led Aromaterapia Bivolt"
    else:
        sufixo_a = " Modelo Ergonômico Multifuncional Resistente"
        sufixo_b = " Design Moderno Prático Para Uso Diário"

    sufixo = sufixo_b if foco_seo else sufixo_a
    titulo_candidato = (clean_name + sufixo).strip()

    if len(titulo_candidato) > 75:
        corte = titulo_candidato[:75]
        if " " in corte:
            titulo_candidato = corte.rsplit(" ", 1)[0]
        else:
            titulo_candidato = corte

    return titulo_candidato


def gerar_relatorio_pontos_fortes_fracos(prod_nome: str) -> str:
    """Gera a análise diagnóstica de pontos fortes e fracos do ASIN."""
    return (
        f"### 📋 Relatório Diagnóstico do Produto: **{prod_nome}**\n\n"
        "#### 🟢 Pontos Fortes (Diferenciais Competitivos Mapeados):\n"
        "- **Extração Sem Filtro de Papel:** Retém os óleos essenciais do café, entregando bebida mais encorpada e de maior valor percebido.\n"
        "- **Material de Alta Resistência:** Jarra de vidro borossilicato com suporte a choques térmicos e estrutura em inox anticorrosivo.\n"
        "- **Versatilidade de Uso:** Permite o preparo de cafés especiais, infusão de chás em folhas e emulsão de leite para bebidas cremosas.\n"
        "- **Design e Apelo Visual:** Estética moderna para uso em bancada e servimento direto à mesa.\n\n"
        "#### 🔴 Pontos Fracos e Dores Mapeadas no Mercado:\n"
        "- **Fragilidade Percebida:** Receio dos compradores quanto à quebra do vidro no transporte ou na lavagem.\n"
        "- **Passagem de Borra Fina:** Reclamações comuns quando a moagem do café utilizada é muito fina.\n"
        "- **Manutenção da Temperatura:** O vidro simples perde calor mais rápido em comparação com garrafas térmicas com vácuo.\n\n"
        "#### 🎯 Estratégia de Neutralização Utilizada no Anúncio:\n"
        "- Destaque técnico para o vidro borossilicato de alta densidade e embalagem de proteção industrial.\n"
        "- Instrução clara nos bullet points sobre a moagem ideal (média/grossa) e filtro de malha de inox de alta precisão.\n\n"
        "---\n"
    )


def gerar_descricao_a10_completa(prod_nome: str) -> tuple:
    texto_fluido = (
        f"Eleve o nível do seu café matinal com a {prod_nome}, projetada para extrair o máximo de sabor, "
        "corpo e aroma dos seus grãos preferidos. Fabricada com vidro borossilicato de alta resistência térmica "
        "e estrutura em aço inoxidável, esta cafeteira combina durabilidade excepcional com um design elegante e sofisticado. "
        "Seu sistema de filtragem de embolo fino retém perfeitamente a borra sem a necessidade de filtros de papel, "
        "preservando os óleos naturais do café para uma bebida encorpada e de sabor marcante. "
        "Fácil de manusear e higienizar, é o acessório indispensável para apreciadores de café e chá em casa ou no escritório.\n\n"
        "ESPECIFICAÇÕES TÉCNICAS E ATRIBUTOS:\n"
        "- Capacidade: 600ml (Servimento Prático)\n"
        "- Material do Corpo: Vidro Borossilicato de Alta Resistência Térmica\n"
        "- Filtro Interno: Êmbolo em Aço Inoxidável com Malha Fina\n"
        "- Uso: Preparo de Café Extraído e Infusão de Chás\n"
        "- Higienização: Fácil Desmontagem e Limpeza Rápida\n\n"
        "CONTEÚDO DA EMBALAGEM:\n"
        f"- 01 {prod_nome}\n"
        "- 01 Manual de Instruções em Português"
    )
    html_limpo = (
        f"<p><b>Desfrute do verdadeiro sabor do café preparado na hora com a {prod_nome}!</b></p>\n"
        f"<p>A <b>{prod_nome}</b> oferece a experiência completa da prensa francesa com extração perfeita de aromas e óleos naturais. "
        "Confeccionada em vidro borossilicato resistente a choques térmicos e filtro de aço inox de alta precisão.</p>\n"
        "<p><b>Destaques do Produto:</b><br>\n"
        "- <b>Vidro Borossilicato Premium:</b> Suporta altas temperaturas sem trincar.<br>\n"
        "- <b>Filtro Reutilizável de Inox:</b> Dispensa o uso de filtros de papel ecológicos.<br>\n"
        "- <b>Multiuso Prático:</b> Ideal para o preparo de cafés especiais e infusões de chá.</p>\n"
        "<p><b>Conteúdo da Embalagem:</b><br>\n"
        f"- 01 {prod_nome}<br>\n"
        "- 01 Manual do Usuário em Português</p>"
    )
    return texto_fluido, html_limpo


def gerar_bullet_points_a10(prod_nome: str) -> str:
    bullets = [
        "☕ **EXTRAÇÃO DE SABOR INTENSO:** Sistema de prensa francesa que preserva os óleos essenciais do café garantindo bebida encorpada e aromática.",
        "🔥 **VIDRO BOROSSILICATO RESISTENTE:** Jarra construída em vidro de alta densidade resistente a choques térmicos e variações de temperatura.",
        "🛡️ **FILTRO DE AÇO INOXIDÁVEL:** Malha filtrante de alta precisão que retém a borra de café sem necessidade de utilizar filtros de papel descartáveis.",
        "✨ **DESIGN ELEGANTE E SOFISTICADO:** Estrutura ergonômica com acabamento moderno que compõe perfeitamente a bancada da sua cozinha.",
        "🥛 **PREPARO DE CAFÉ E CHÁ:** Versatilidade total para o preparo de cafés especiais, infusão de chás em folhas e emulsão de leite para cappuccino.",
        "📐 **CAPACIDADE IDEAL DE 600ML:** Tamanho perfeito para servir xícaras de café na medida certa para você, sua família ou convidados.",
        "🧼 **FACILIDADE DE HIGIENIZAÇÃO:** Componentes totalmente desmontáveis que facilitam a limpeza rápida em água corrente.",
        "🤝 **ALÇA ERGONÔMICA TÉRMICA:** Empunhadura projetada para oferecer manuseio firme e seguro durante o servimento do café quente.",
        "🍃 **ECORRESPONSÁVEL E ECONÔMICO:** Dispensa o consumo diário de filtros descartáveis ou cápsulas plásticas poluentes.",
        "📦 **EMBALAGEM DE PROTEÇÃO REFORÇADA:** Enviado em caixa industrial reforçada com berço amortecedor para garantir a integridade do vidro."
    ]
    return "\n".join([f"* {b}" for b in bullets])


def gerar_backend_keywords_a10(prod_nome: str, titulo_a: str, titulo_b: str) -> str:
    palavras_titulos = set(
        remover_acentos(w.lower()) 
        for w in re.findall(r'\w+', titulo_a + " " + titulo_b)
        if len(w) > 1
    )

    candidatos = [
        "cremeira", "embolo", "infusor", "cha", "graos", "moido", "filtro", 
        "inox", "coador", "passador", "xicara", "caneca", "expresso", "capuccino", 
        "cafeteria", "cozinha", "mesa", "servir", "cafezinho", "moka", "barista"
    ]

    backend_unicas = []
    for cand in candidatos:
        cand_clean = remover_acentos(cand.lower().strip())
        if cand_clean not in palavras_titulos and cand_clean not in backend_unicas:
            backend_unicas.append(cand_clean)

    resultado = ""
    for palavra in backend_unicas:
        candidato_string = (resultado + " " + palavra).strip() if resultado else palavra
        if len(candidato_string.encode("utf-8")) <= 230:
            resultado = candidato_string
        else:
            break

    return resultado


def analisar_e_otimizar_listing(
    asin_input: str, produto_nosso: str = "", bullet_points_concorrente: str = ""
) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            api_key = ""

    termo_entrada = produto_nosso.strip() if produto_nosso.strip() else asin_input.strip()
    links_categoria, nome_nicho = extrair_dados_e_links_categoria(termo_entrada)

    links_md = "### 🔗 Links Oficiais da Categoria e Ofertas Concorrentes (Amazon BR):\n\n"
    for i, cat in enumerate(links_categoria, start=1):
        links_md += f"{i}. [{cat['titulo']}]({cat['link']})\n"
    links_md += "\n---\n\n"

    relatorio_swot = gerar_relatorio_pontos_fortes_fracos(nome_nicho)

    prompt_mestre = (
        "Você é o Maior Especialista em SEO e Copywriter para a Amazon Brasil.\n\n"
        "📌 DADOS DO PRODUTO:\n"
        "- ASIN / Entrada: " + str(asin_input) + "\n"
        "- Produto Referência / Nicho: " + str(nome_nicho) + "\n\n"
        "🧠 ETAPA DE ANÁLISE (OBRIGATÓRIA - SILENCIOSA - NÃO EXIBIR NA SAÍDA):\n"
        "Analise público ideal, diferencial competitivo, dores que o produto resolve, benefícios e atributos técnicos.\n\n"
        "🚨 REGRAS CRÍTICAS DE COPYWRITING E CONFORMIDADE AMAZON:\n"
        "1. TÍTULOS A e B: Máximo de 75 caracteres cada. Sem palavras proibidas ('Pronta Entrega', 'FBA', 'Envio Rápido', 'Alta Qualidade', 'Premium', 'Melhor'). Estrutura: [Nome do Produto] + [Especificação/Atributo].\n"
        "2. DESCRIÇÃO DO PRODUTO: Texto fluido entre 1.200 e 1.900 caracteres em técnica AIDA com especificações técnicas e conteúdo da embalagem.\n"
        "3. VERSÃO HTML DA DESCRIÇÃO: HTML limpo usando APENAS <p>, <b> e <br>.\n"
        "4. BULLET POINTS (10 BULLETS): Formato obrigatório: Emoji + **TÍTULO EM CAIXA ALTA (2 A 4 PALAVRAS):** + explicação técnica/benefício real. Sem termos promocionais.\n"
        "5. PALAVRAS-CHAVE BACKEND (SEARCH TERMS): Preencha exatamente até o limite máximo de 230 bytes em palavras-chave únicas separadas apenas por espaço, sem acentos, sem vírgulas, sem numerais e OBRIGATORIAMENTE SEM REPETIR NENHUMA PALAVRA QUE JÁ CONSTA NO TÍTULO A OU TÍTULO B.\n"
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

    titulo_a = otimizar_titulo_a10_75_chars(nome_nicho, foco_seo=False)
    titulo_b = otimizar_titulo_a10_75_chars(nome_nicho, foco_seo=True)
    desc_fluida, desc_html = gerar_descricao_a10_completa(nome_nicho)
    bullet_points_md = gerar_bullet_points_a10(nome_nicho)
    backend_clean = gerar_backend_keywords_a10(nome_nicho, titulo_a, titulo_b)

    analise_dinamica = (
        "### 📊 Anúncio Gerado para Amazon Brasil\n\n"
        "**1. TÍTULOS OTIMIZADOS (LIMITE ESTRITO: 75 CARACTERES | SEM TERMOS PROIBIDOS)**\n"
        "- **Título A (Clareza + Atributos):** `"
        + titulo_a
        + "` *("
        + str(len(titulo_a))
        + " caracteres)*\n"
        "- **Título B (SEO + Especificações):** `"
        + titulo_b
        + "` *("
        + str(len(titulo_b))
        + " caracteres)*\n\n"
        "> ⚠️ **Conformidade Amazon:** Títulos configurados sem termos promocionais ('Pronta Entrega', 'FBA', 'Envio Rápido') para evitar supressão automática no catálogo da Amazon Brasil.\n\n"
        "---\n\n"
        "**2. DESCRIÇÃO COMPLETA DO PRODUTO (ATÉ 2.000 CARACTERES - TÉCNICA AIDA)**\n"
        + desc_fluida
        + "\n\n"
        "#### Versão HTML para o Seller Central:\n"
        "```html\n"
        + desc_html
        + "\n```\n\n"
        "---\n\n"
        "**3. 10 BULLET POINTS DE ALTA CONVERSÃO**\n"
        + bullet_points_md
        + "\n\n"
        "---\n\n"
        "**4. PALAVRAS-CHAVE BACKEND (SEARCH TERMS - MÁXIMO APROVEITAMENTO)**\n"
        "`"
        + backend_clean
        + "`\n\n"
        "> 📌 **Byte Count:** " + str(len(backend_clean.encode('utf-8'))) + " / 230 bytes autorizados. Nenhuma palavra presente nos Títulos A ou B foi repetida nesta lista.\n\n"
        "---\n\n"
        "**5. PROMPTS PARA IMAGENS DA LISTAGEM (10 PROMPTS)**\n"
        "1. **Foto 01 (Principal - Fundo Branco):** using the attached base product image as an overlay without any modification to the product itself, isolated on seamless pure white background (RGB 255,255,255), product filling 85% of frame, crisp studio commercial lighting, Amazon main image standard.\n"
        "2. **Foto 02 (Uso Real / Lifestyle):** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle background, natural commercial lighting.\n"
        "3. **Foto 03 (Infográfico de Benefícios):** using the attached base product image as an overlay without any modification to the product itself, clean infographic layout with callout lines pointing to key features, Portuguese text space.\n"
        "4. **Foto 04 (Dimensões e Escala):** using the attached base product image as an overlay without any modification to the product itself, dimensional infographic with clear height and width scale indicators in Portuguese.\n"
        "5. **Foto 05 (Conteúdo da Embalagem):** using the attached base product image as an overlay without any modification to the product itself, overhead layflat view showing product and accessories.\n"
        "6. **Foto 06 (Close de Material):** using the attached base product image as an overlay without any modification to the product itself, extreme macro shot focusing on material texture and finish.\n"
        "7. **Foto 07 (Funcionalidade):** using the attached base product image as an overlay without any modification to the product itself, demonstration composition highlighting core functionality.\n"
        "8. **Foto 08 (Cenários Diversos):** using the attached base product image as an overlay without any modification to the product itself, multi-scenario usage representation.\n"
        "9. **Foto 09 (Comparativo):** using the attached base product image as an overlay without any modification to the product itself, side-by-side visual comparison highlighting premium build vs generic alternative.\n"
        "10. **Foto 10 (Confiança e Garantia):** using the attached base product image as an overlay without any modification to the product itself, summary banner with trust badges in Portuguese text.\n\n"
        "---\n\n"
        "**6. ROTEIRO DE VÍDEO (30–45s)**\n"
        "- **Cena 01 (0–5s):** Gancho visual apresentando a "
        + nome_nicho
        + " em funcionamento.\n"
        "- **Cena 02 (5–15s):** Demonstração prática dos principais recursos no dia a dia.\n"
        "- **Cena 03 (15–25s):** Detalhes de acabamento e diferenciais técnicos.\n"
        "- **Cena 04 (25–35s):** Aplicação em ambiente real (casa/escritório).\n"
        "- **Cena 05 (35–45s):** Encerramento elegante com apresentação da marca na Amazon BR.\n\n"
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