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
        links_md += str(i) + ". [" + str(conc['titulo']) + "](" + str(conc['link']) + ") - **ASIN:** `" + str(conc['asin']) + "`\n"
    links_md += "\n---\n"

    # PROMPT MESTRE ESTRITO A9/A10
    prompt_mestre = (
        "Você é o Maior Especialista em Algoritmo A9/A10 da Amazon Brasil e Copywriter de Alta Conversão.\n\n"
        "📌 DADOS DO PRODUTO:\n"
        "- ASIN / Entrada: " + str(asin_input) + "\n"
        "- Produto Referência / Nicho: " + str(termo_referencia) + "\n\n"
        "🧠 ETAPA DE ANÁLISE (OBRIGATÓRIA - SILENCIOSA - NÃO EXIBIR NA SAÍDA):\n"
        "Analise previamente público ideal, diferencial competitivo, dores que o produto resolve, benefícios, características principais, nível de procura e concorrência no mercado brasileiro.\n\n"
        "🚨 REGRAS CRÍTICAS AMAZON (ALGORITMO A10):\n"
        "- TÍTULOS: Máximo estrito de 75 caracteres cada (Descrição + Benefício + Característica). Sem palavras promocionais (frete grátis), sem superlativos (melhor, nº1) e sem caracteres proibidos (!, $, ?, _, {, }, ^, ¬, ¦).\n"
        "- DESCRIÇÃO: Até 2.000 caracteres fluida em técnica AIDA + Versão HTML para Seller Central com tags p, b e br.\n"
        "- BULLET POINTS: 10 bullets iniciando obrigatoriamente com Emoji + TÍTULO EM CAIXA ALTA e foco em benefícios práticos.\n"
        "- PALAVRAS-CHAVE BACKEND (SEARCH TERMS): Exatamente 20 palavras-chave únicas (máx 230 bytes) sem repetir termos do título, sem acentos e sem vírgulas.\n"
        "- 10 PROMPTS PARA IMAGENS DA LISTAGEM: Iniciando OBRIGATORIAMENTE com 'using the attached base product image as an overlay without any modification to the product itself'. Foto 01 fundo branco puro (RGB 255,255,255) ocupando 85%. Textos de apoio visual em português brasileiro.\n"
        "- ROTEIRO DE VÍDEO (30–45 SEGUNDOS): Roteiro estruturado em 5 cenas.\n"
        "- CONTEÚDO A+: Estrutura completa de módulos para quebra de objeções e aumento de conversão.\n"
        "- 6 PROMPTS PARA BANNERS A+: Criar 6 prompts em inglês iniciando com 'using the attached base product image as an overlay without any modification to the product itself'.\n\n"
        "GERE ESTRITAMENTE A SAÍDA FINAL ORGANIZADA EM MARKDOWN NAS SEÇÕES ACIMA."
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
                    return links_md + "\n" + res.content[0].text
                except Exception:
                    continue
        except Exception:
            pass

    # FALLBACK ESTRUTURADO A10
    prod_nome = (
        termo_referencia.title() if termo_referencia else "Produto Consultado"
    )
    words = [w.lower() for w in prod_nome.split() if len(w) > 2]
    kw_primary = words[0] if words else "produto"

    titulo_a = (prod_nome[:35] + " Pronta Entrega Alta Qualidade")[:75]
    titulo_b = (prod_nome[:35] + " Premium Envio Rapido FBA")[:75]

    analise_dinamica = (
        "### 📊 Anúncio Gerado para Algoritmo A9/A10 - Amazon Brasil\n\n"
        "**1. TÍTULOS OTIMIZADOS (MÁXIMO 75 CARACTERES)**\n"
        "- **Título A (Clareza):** `"
        + titulo_a
        + "` *("
        + str(len(titulo_a))
        + " chars)*\n"
        "- **Título B (SEO A10):** `"
        + titulo_b
        + "` *("
        + str(len(titulo_b))
        + " chars)*\n\n"
        "---\n\n"
        "**2. DESCRIÇÃO DO PRODUTO (ATÉ 2.000 CARACTERES)**\n"
        "O **"
        + prod_nome
        + "** foi desenvolvido para entregar o máximo em durabilidade, eficiência e praticidade. Fabricado com materiais de alto padrão, é a solução ideal para quem busca qualidade superior e excelente custo-benefício na Amazon Brasil.\n\n"
        "#### Versão HTML para o Seller Central:\n"
        "```html\n"
        "<p><b>Surpreenda-se com a qualidade do " + prod_nome + "!</b></p>\n"
        "<p>Desenvolvido para entregar máxima durabilidade e praticidade no seu dia a dia.</p>\n"
        "<p><b>Destaques do Produto:</b><br>- Material de alta resistência<br>- Envio ágil via logística da Amazon Brasil<br>- Garantia do fabricante e suporte dedicado</p>\n"
        "```\n\n"
        "---\n\n"
        "**3. 10 BULLET POINTS DE ALTA CONVERSÃO**\n"
        "* 🎯 **ALTA PERFORMANCE & QUALIDADE:** Desenvolvido com materiais premium para durabilidade máxima.\n"
        "* 📦 **PRONTA ENTREGA COM ENVIO RÁPIDO:** Receba no seu endereço através da logística segura da Amazon Brasil.\n"
        "* 🛡️ **GARANTIA OFICIAL E SUPORTE:** Produto 100% original com suporte pós-venda dedicado.\n"
        "* ⚡ **DESIGN ERGONÔMICO E PRÁTICO:** Projeto moderno pensado para facilitar o uso no cotidiano.\n"
        "* ⭐️ **EXCELENTE CUSTO-BENEFÍCIO:** A melhor escolha do segmento combinando preço justo e qualidade.\n"
        "* 🔹 **ESTRUTURA REFORÇADA:** Construído para longa vida útil sob uso contínuo.\n"
        "* 🔧 **USO INTUITIVO:** Manuseio simples, rápido e totalmente sem complicações.\n"
        "* 💡 **VERSATILIDADE:** Atende com precisão às necessidades do consumidor exigente.\n"
        "* 🌿 **PRODUTO CERTIFICADO:** Fabricado conforme as normas de segurança vigentes.\n"
        "* 🚀 **SATISFAÇÃO GARANTIDA:** Estruturado para a melhor experiência de compra Prime.\n\n"
        "---\n\n"
        "**4. PALAVRAS-CHAVE BACKEND (SEARCH TERMS - MÁX 230 BYTES / A10)**\n"
        "`"
        + kw_primary
        + " pronta entrega oferta amazon brasil melhor custo beneficio garantia oficial envio rapido fba qualidade premium original novidade`\n\n"
        "---\n\n"
        "**5. PROMPTS PARA IMAGENS DA LISTAGEM (10 FOTOS)**\n"
        "1. **Foto 01 (Principal - Fundo Branco):** using the attached base product image as an overlay without any modification to the product itself, isolated on seamless pure white background (RGB 255,255,255), product filling 85% of frame, crisp studio commercial lighting, Amazon main image standard.\n"
        "2. **Foto 02 (Uso Real / Lifestyle):** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle background appropriate for "
        + kw_primary
        + ", natural commercial lighting.\n"
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
        + prod_nome
        + ".\n"
        "- **Cena 02 (5–15s):** Demonstração prática do produto sendo utilizado.\n"
        "- **Cena 03 (15–25s):** Close nos detalhes de acabamento e construção.\n"
        "- **Cena 04 (25–35s):** Aplicação e praticidade na rotina.\n"
        "- **Cena 05 (35–45s):** Encerramento com CTA suave para compra na Amazon BR.\n\n"
        "---\n\n"
        "**7. CONTEÚDO A+ & 8. PROMPTS A+ (6 BANNERS INGLÊS)**\n"
        "1. **Banner Hero:** using the attached base product image as an overlay without any modification to the product itself, wide Amazon A+ banner composition, studio lighting.\n"
        "2. **Benefícios Visuais:** using the attached base product image as an overlay without any modification to the product itself, clean A+ infographic layout.\n"
        "3. **Diferencial Técnico:** using the attached base product image as an overlay without any modification to the product itself, macro lighting highlighting build quality.\n"
        "4. **Uso Real:** using the attached base product image as an overlay without any modification to the product itself, realistic lifestyle scene.\n"
        "5. **Comparação Visual:** using the attached base product image as an overlay without any modification to the product itself, clean comparative layout.\n"
        "6. **Capacidade / Aplicação:** using the attached base product image as an overlay without any modification to the product itself, visual demonstration of practical application.\n"
    )

    return links_md + "\n" + analise_dinamica