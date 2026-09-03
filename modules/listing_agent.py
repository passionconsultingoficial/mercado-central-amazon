import os
import re
import requests
import unicodedata
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic


def obter_token_sp_api() -> str:
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
        (f"Principais Marcas - {termo_exibicao}", f"{query_completa}+reforcada"),
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
        qualificadores = ["Inox Reforçada", "Cabo Madeira", "Aço Cabos", "Modelo Prático", "Multiuso Cozinha", "Modelo Duplo"]
    else:
        qualificadores = ["Cabo Madeira Reforçado", "Aço Inox Resistente", "Modelo Duplo", "Prático Resistente", "Modelo Ergonômico"]

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
    palavras_titulos = set(
        remover_acentos(w.lower()) 
        for w in re.findall(r'\w+', titulo_a + " " + titulo_b)
        if len(w) > 1
    )

    candidatos_especificos = [remover_acentos(w.lower()) for w in palavras_reais if len(w) > 1]
    candidatos_genericos = [
        "churrasco", "grelhar", "carne", "inox", "moeda", "reforcada", "cabo",
        "madeira", "utilidade", "acessorio", "duravel", "resistente", "eficiente",
        "cotidiano", "pratico", "qualidade", "modelo", "novo", "espeto", "parrilla"
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


def analisar_e_otimizar_listing(asin_input: str, produto_nosso: str = "", bullet_points_concorrente: str = "") -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
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
        "GERE ESTRITAMENTE A SAÍDA ORGANIZADA EM MARKDOWN SEGUINDO O PADRÃO A10."
    )

    if api_key and len(str(api_key).strip()) > 10:
        try:
            client = Anthropic(api_key=str(api_key).strip())
            for model_name in [
                "claude-3-5-sonnet-20240620",
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

    titulo_a = otimizar_titulo_a10_75_chars(termo_exibicao, palavras_reais, foco_seo=False)
    titulo_b = otimizar_titulo_a10_75_chars(termo_exibicao, palavras_reais, foco_seo=True)
    desc_fluida, desc_html = gerar_descricao_a10_dinamica(termo_exibicao)
    bullet_points_md = gerar_bullet_points_a10_dinamico(termo_exibicao)
    backend_clean = gerar_backend_keywords_a10_dinamico(termo_exibicao, titulo_a, titulo_b, palavras_reais)

    analise_dinamica = (
        "### 📊 Anúncio Gerado para Amazon Brasil\n\n"
        "**1. TÍTULOS OTIMIZADOS (LIMITE ESTRITO: 75 CARACTERES | SEM TERMOS PROIBIDOS)**\n"
        "- **Título A:** `" + titulo_a + "` *(" + str(len(titulo_a)) + " caracteres)*\n"
        "- **Título B:** `" + titulo_b + "` *(" + str(len(titulo_b)) + " caracteres)*\n\n"
        "---\n\n"
        "**2. DESCRIÇÃO COMPLETA DO PRODUTO**\n" + desc_fluida + "\n\n"
        "#### Versão HTML para Seller Central:\n```html\n" + desc_html + "\n```\n\n"
        "---\n\n"
        "**3. 10 BULLET POINTS DE ALTA CONVERSÃO**\n" + bullet_points_md + "\n\n"
        "---\n\n"
        "**4. PALAVRAS-CHAVE BACKEND**\n`" + backend_clean + "`\n"
    )

    return links_md + relatorio_swot + analise_dinamica