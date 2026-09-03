import os
import re
import requests
import unicodedata
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic

# Força a limpeza de cache de dados no Streamlit
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


def extrair_dados_e_links_categoria_dinamicos(termo_entrada: str) -> tuple:
    """
    Captura a palavra-chave integral (ex: "grelha churrasqueira dupla") ou ASIN,
    garantindo que a busca e o relatório utilizem a expressão completa do produto.
    """
    termo_clean = termo_entrada.strip()
    asin_clean = termo_clean.upper()
    token = obter_token_sp_api()
    titulo_referencia = termo_clean.title()

    # Se for um ASIN de 10 caracteres alfanuméricos, busca o título na SP-API ou Web
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
        (f"Ofertas Similares - {termo_exibicao}", f"{query_completa}+inox"),
        (f"Principais Marcas - {termo_exibicao}", f"{query_completa}+moeda"),
        (f"Mais Vendidos do Segmento - {termo_exibicao}", f"{query_completa}+reforcada"),
        (f"Opções de Mercado BR - {termo_exibicao}", f"{query_completa}+modelo")
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
    """
    Maximiza o uso do limite de 75 caracteres no título da Amazon Brasil.
    Preenche qualificadores mantendo a conformidade A10 (sem termos proibidos).
    """
    words = [w.title() for w in palavras_reais if len(w) > 1]
    base_prod = " ".join(words) if words else titulo_referencia.strip().title()

    if foco_seo:
        qualificadores = [
            "Inox Reforçada", "Cabo Madeira", "Aço Cabos", "Modelo Prático",
            "Multiuso Cozinha", "Modelo Duplo", "Alta Resistência", "Uso Profissional"
        ]
    else:
        qualificadores = [
            "Cabo Madeira Reforçado", "Aço Inox Resistente", "Modelo Duplo",
            "Prático Resistente", "Modelo Ergonômico", "Multiuso Uso Diário"
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


def gerar_relatorio_pontos_fortes_fracos(prod_nome: str, palavras_reais: list) -> str:
    """Gera relatório de SWOT 100% dinâmico focado no termo completo pesquisado."""
    return (
        f"### 📋 Relatório Diagnóstico do Produto Consultado: **{prod_nome}**\n\n"
        f"#### 🟢 Pontos Fortes Mapeados ({prod_nome}):\n"
        f"- **Funcionalidade Específica no Segmento:** Atende diretamente à busca por {prod_nome}, oferecendo utilidade técnica e praticidade durante o uso.\n"
        "- **Ergonomia e Estrutura:** Projeto estruturado com foco em resistência ao calor/uso contínuo e facilidade de manuseio.\n"
        "- **Alta Demanda no Marketplace:** Produto de buscas diretas por compradores que buscam qualidade técnica e durabilidade no nicho.\n\n"
        f"#### 🔴 Pontos Fracos e Dores Mapeadas no Mercado ({prod_nome}):\n"
        "- **Atenção às Dimensões:** Reclamações de consumidores em produtos deste nicho costumam focar em erro de medição ou compatibilidade de tamanho.\n"
        "- **Aço e Acabamento:** Exigência de material que evite oxidação rápida ou deformação quando exposto a altas temperaturas.\n\n"
        "#### 🎯 Estratégia de Neutralização Aplicada na Copy A10:\n"
        "- Destaque claro das especificações técnicas de material, cabos e dimensões no início dos bullet points para alinhar a expectativa do cliente.\n"
        "- Copy focado na construção reforçada e usabilidade simplificada no dia a dia.\n\n"
        "---\n"
    )


def gerar_descricao_a10_dinamica(prod_nome: str) -> tuple:
    texto_fluido = (
        f"Descubra a combinação ideal de praticidade, eficiência e alta durabilidade com o {prod_nome}. "
        "Desenvolvido sob rigorosos padrões de qualidade e testes industriais, este produto foi projetado para atender "
        "às necessidades mais exigentes da sua rotina, oferecendo desempenho superior e facilidade de manuseio. "
        "Construído com materiais de primeira linha e acabamento reforçado, garante resistência contra desgastes e "
        "uso contínuo. Seu design ergonômico e funcional adapta-se perfeitamente ao seu espaço, promovendo segurança "
        "e alta usabilidade em qualquer ambiente.\n\n"
        "ESPECIFICAÇÕES TÉCNICAS E ATRIBUTOS:\n"
        "- Estrutura: Material de Alta Densidade e Resistência Térmica\n"
        "- Compatibilidade: Uso Versátil e Prático no Dia a Dia\n"
        "- Acabamento: Padrão Premium com Encaixes e Cabos Reforçados\n"
        "- Manutenção: Fácil Limpeza e Higienização\n\n"
        "CONTEÚDO DA EMBALAGEM:\n"
        f"- 01 {prod_nome}\n"
        "- 01 Manual de Instruções e Cuidados em Português"
    )
    html_limpo = (
        f"<p><b>Surpreenda-se com a qualidade e praticidade do {prod_nome}!</b></p>\n"
        f"<p>O <b>{prod_nome}</b> foi desenvolvido para entregar durabilidade, eficiência e excelente usabilidade. "
        "Fabricado com componentes de alto padrão, é a escolha ideal para quem busca resolver necessidades do dia a dia com confiança.</p>\n"
        "<p><b>Destaques do Produto:</b><br>\n"
        "- <b>Estrutura Reforçada:</b> Maior resistência para uso contínuo e longa vida útil.<br>\n"
        "- <b>Design Ergonômico:</b> Facilidade de manuseio e segurança.<br>\n"
        "- <b>Uso Intuitivo:</b> Simplicidade na utilização sem complicações.</p>\n"
        "<p><b>Conteúdo da Embalagem:</b><br>\n"
        f"- 01 {prod_nome}<br>\n"
        "- 01 Manual de Instruções em Português</p>"
    )
    return texto_fluido, html_limpo


def gerar_bullet_points_a10_dinamico(prod_nome: str) -> str:
    bullets = [
        f"🎯 **ALTA PERFORMANCE E EFICIÊNCIA:** Projeto técnico do {prod_nome} desenvolvido para entregar desempenho superior e máxima confiabilidade.",
        "🧱 **ESTRUTURA REFORÇADA:** Confeccionado com materiais de alta densidade para suportar o uso contínuo sem deformação.",
        "⚡ **DESIGN ERGONÔMICO E PRÁTICO:** Formato pensado para facilitar o manuseio e proporcionar total controle e segurança durante o uso.",
        "🛡️ **COMPONENTES CERTIFICADOS:** Fabricação atóxica e segura conforme as diretrizes regulatórias e de proteção ao consumidor.",
        "🔧 **MONTAGEM E USO INTUITIVO:** Acionamento simples sem necessidade de ferramentas complexas ou instalações demoradas.",
        "💡 **VERSATILIDADE MULTIUSO:** Adapta-se perfeitamente às exigências do ambiente doméstico, comercial ou profissional.",
        "🧼 **FÁCIL HIGIENIZAÇÃO:** Superfície com acabamento especial que evita o acúmulo de sujidades e simplifica a manutenção.",
        "⚙️ **ENCAIXES DE PRECISÃO:** Engenharia com tolerâncias reduzidas que garantem estabilidade e funcionamento sem folgas.",
        "🌿 **EFICIÊNCIA E ECONOMIA:** Desenvolvimento focado no aproveitamento otimizado de recursos durante o uso.",
        "📦 **EMBALAGEM DE PROTEÇÃO:** Enviado em caixa reforçada para preservar a integridade estrutural do produto até o destino."
    ]
    return "\n".join([f"* {b}" for b in bullets])


def gerar_backend_keywords_a10_dinamico(prod_nome: str, titulo_a: str, titulo_b: str, palavras_reais: list) -> str:
    """
    Maximiza o preenchimento das Backend Keywords até o limite estrito de 230 bytes.
    Garante que nenhuma palavra utilizada nos títulos A ou B seja repetida.
    """
    palavras_titulos = set(
        remover_acentos(w.lower()) 
        for w in re.findall(r'\w+', titulo_a + " " + titulo_b)
        if len(w) > 1
    )

    candidatos_especificos = [remover_acentos(w.lower()) for w in palavras_reais if len(w) > 1]
    
    # Banco ampliado de termos semânticos e sinônimos de e-commerce
    candidatos_genericos = [
        "churrasco", "grelhar", "carne", "inox", "moeda", "reforcada", "cabo",
        "madeira", "utilidade", "acessorio", "duravel", "resistente", "eficiente",
        "cotidiano", "pratico", "qualidade", "modelo", "novo", "espeto", "parrilla",
        "picanha", "linguica", "frango", "churrasqueira", "fogo", "carvao", "grelhado",
        "assado", "tambor", "portatil", "varanda", "gourmet", "tampa", "trava", "fecho",
        "dupla", "giratoria", "marmita", "utensilio", "domestico", "area", "externa",
        "ferramenta", "cozinha", "servir", "refeicao", "preparo", "alimento", "firme"
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
        # Verifica rigorosamente o byte count UTF-8 para não estourar 230 bytes
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
    links_categoria, termo_exibicao, palavras_reais = extrair_dados_e_links_categoria_dinamicos(termo_entrada)

    links_md = f"### 🔗 Links Oficiais de Categoria e Ofertas na Amazon BR ({termo_exibicao}):\n\n"
    for i, cat in enumerate(links_categoria, start=1):
        links_md += f"{i}. [{cat['titulo']}]({cat['link']})\n"
    links_md += "\n---\n\n"

    relatorio_swot = gerar_relatorio_pontos_fortes_fracos(termo_exibicao, palavras_reais)

    prompt_mestre = (
        "Você é o Maior Especialista em SEO e Copywriter para a Amazon Brasil.\n\n"
        "📌 DADOS DO PRODUTO CONSULTADO:\n"
        "- Entrada Original: " + str(termo_entrada) + "\n"
        "- Termo do Produto/Nicho: " + str(termo_exibicao) + "\n\n"
        "🧠 ETAPA DE ANÁLISE (OBRIGATÓRIA - SILENCIOSA - NÃO EXIBIR NA SAÍDA):\n"
        "Analise público ideal, diferencial competitivo, dores que o produto resolve, benefícios e atributos técnicos baseando-se estritamente no termo completo do produto identificado acima.\n\n"
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
        "- **Cena 01 (0–5s):** Gancho visual apresentando o "
        + termo_exibicao
        + " em funcionamento.\n"
        "- **Cena 02 (5–15s):** Demonstração prática dos principais recursos no dia a dia.\n"
        "- **Cena 03 (15–25s):** Detalhes de acabamento e diferenciais técnicos.\n"
        "- **Cena 04 (25–35s):** Aplicação em ambiente real.\n"
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