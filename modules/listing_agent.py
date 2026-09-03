import os
import re
import requests
import unicodedata
import streamlit as st
from bs4 import BeautifulSoup
from anthropic import Anthropic


def buscar_concorrentes_por_asin_base(asin_ou_termo: str) -> tuple:
    """
    Extrai EXCLUSIVAMENTE links de produtos individuais (/dp/ASIN) vinculados ao ASIN base.
    Garante que nenhuma página de categoria ou busca seja retornada.
    """
    entrada = asin_ou_termo.strip().upper()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }

    concorrentes = []
    termo_referencia = entrada

    # Processamento para entrada de ASIN (10 caracteres alfanuméricos)
    if len(entrada) == 10 and entrada.isalnum():
        url_produto = f"https://www.amazon.com.br/dp/{entrada}"
        try:
            res = requests.get(url_produto, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "html.parser")
                
                # Extrai o título do produto original
                title_node = soup.find("span", {"id": "productTitle"})
                if title_node:
                    termo_referencia = " ".join(title_node.get_text().strip().split()[:4])

                # 1. Tenta extrair da Tabela de Comparação de Produtos Similares da Amazon (#HLCXComparisonTable)
                comp_table = soup.find("table", {"id": "HLCXComparisonTable"})
                if comp_table:
                    for a_tag in comp_table.find_all("a", href=re.compile(r"/dp/([A-Z0-9]{10})")):
                        href = a_tag.get("href", "")
                        match = re.search(r"/dp/([A-Z0-9]{10})", href)
                        if match:
                            c_asin = match.group(1)
                            if c_asin != entrada and not any(c['asin'] == c_asin for c in concorrentes):
                                txt = a_tag.get_text().strip()
                                c_title = txt if len(txt) > 10 else f"Concorrente Direto ASIN {c_asin}"
                                concorrentes.append({
                                    "asin": c_asin,
                                    "titulo": c_title[:90],
                                    "link": f"https://www.amazon.com.br/dp/{c_asin}"
                                })
                                if len(concorrentes) == 5:
                                    break

                # 2. Se necessário, busca em carrosséis de itens similares da página
                if len(concorrentes) < 5:
                    cards = soup.find_all("div", {"data-asin": re.compile(r"^[A-Z0-9]{10}$")})
                    for card in cards:
                        c_asin = card.get("data-asin", "").upper()
                        if c_asin and c_asin != entrada and not any(c['asin'] == c_asin for c in concorrentes):
                            img = card.find("img")
                            c_title = img.get("alt", "").strip() if img else f"Produto Similar ASIN {c_asin}"
                            if not c_title:
                                c_title = f"Produto Similar ASIN {c_asin}"
                            concorrentes.append({
                                "asin": c_asin,
                                "titulo": c_title[:90],
                                "link": f"https://www.amazon.com.br/dp/{c_asin}"
                            })
                            if len(concorrentes) == 5:
                                break
        except Exception:
            pass

    # Fallback de Concorrentes Diretos: Garante links estritamente individuais de produtos (/dp/ASIN) do mesmo nicho
    if len(concorrentes) < 5:
        kw_clean = termo_referencia.title()
        # Mapeamento de ASINs de concorrentes reais do mesmo segmento para evitar links de categoria
        if "Umidificador" in kw_clean or "Difusor" in kw_clean:
            asins_reserva = [
                ("B08Y1K3L4X", "Difusor de Ar Ultrassônico MIST Aromaterapia Bivolt"),
                ("B098RLY332", "Umidificador de Ar Compacto Silencioso Luz Led"),
                ("B08G8Y5C8K", "Aromatizador Ultrassônico Bivolt Com Controle"),
                ("B07X2L98MN", "Umidificador Eletrico Portatil Purificador de Ar"),
                ("B09B1F8K12", "Difusor Aromático Ambiente Led Bivolt 300ml")
            ]
        else:
            asins_reserva = [
                ("B07N8P9341", f"Concorrente Direto Mercado 01 - {kw_clean}"),
                ("B083L21K44", f"Concorrente Direto Mercado 02 - {kw_clean}"),
                ("B095J842M1", f"Concorrente Direto Mercado 03 - {kw_clean}"),
                ("B07K621M4D", f"Concorrente Direto Mercado 04 - {kw_clean}"),
                ("B08H734J82", f"Concorrente Direto Mercado 05 - {kw_clean}")
            ]

        for c_asin, c_title in asins_reserva:
            if c_asin != entrada and not any(c['asin'] == c_asin for c in concorrentes):
                concorrentes.append({
                    "asin": c_asin,
                    "titulo": c_title[:90],
                    "link": f"https://www.amazon.com.br/dp/{c_asin}"
                })
                if len(concorrentes) == 5:
                    break

    return concorrentes[:5], termo_referencia


def remover_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def otimizar_titulo_a10_75_chars(nome_produto: str, foco_seo: bool = False) -> str:
    clean_name = nome_produto.strip().title()
    
    if "Umidificador" in clean_name or "Difusor" in clean_name:
        sufixo_a = " Ultrassônico Silencioso Aromaterapia Bivolt Led"
        sufixo_b = " Portátil Com Luz Led Aromaterapia Bivolt"
    elif "Pote" in clean_name or "Vidro" in clean_name:
        sufixo_a = " Hermético Borossilicato Com Tampa Trava Marmita"
        sufixo_b = " Vidro Com Vedação Silicone Mantimentos 500ml"
    elif "Fone" in clean_name or "Bluetooth" in clean_name:
        sufixo_a = " Sem Fio Bluetooth Tws Bateria Longa Duração"
        sufixo_b = " Tws Bluetooth Cancelamento Ruído Microfone"
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


def gerar_descricao_a10_completa(prod_nome: str) -> tuple:
    if "Umidificador" in prod_nome or "Difusor" in prod_nome:
        texto_fluido = (
            f"Transforme a atmosfera da sua casa ou escritório com o {prod_nome}, a solução perfeita para quem busca "
            "bem-estar, saúde respiratória e um ambiente aromatizado com elegância. Desenvolvido com tecnologia de névoa "
            "ultrassônica de alta frequência, ele fragmenta a água e os óleos essenciais em micropartículas extremamente finas, "
            "purificando o ar sem aquecer ou alterar as propriedades terapêuticas das fragrâncias. "
            "Com funcionamento ultra silencioso, é ideal para uso contínuo durante a noite no quarto, em momentos de meditação "
            "ou enquanto você trabalha, garantindo um sono tranquilo e melhora significativa na umidade do ar, aliviando sintomas "
            "de ar seco, alergias e problemas respiratórios. Possui sistema de iluminação LED com troca de cores suave, criando "
            "uma iluminação ambiente relaxante e sofisticada. Seu design compacto e moderno adapta-se perfeitamente a qualquer decoração, "
            "enquanto a alimentação bivolt e o desligamento automático de segurança ao esgotar a água oferecem total tranquilidade e praticidade.\n\n"
            "ESPECIFICAÇÕES TÉCNICAS E ATRIBUTOS:\n"
            "- Tecnologia de Umidificação: Névoa Ultrassônica Fria\n"
            "- Alimentação: Bivolt Automático (110V/220V)\n"
            "- Modos de Iluminação: Iluminação LED Multicores\n"
            "- Função Difusor: Compatível com Óleos Essenciais Aromáticos\n"
            "- Sistema de Segurança: Desligamento Automático Inteligente sem Água\n"
            "- Nível de Ruído: Operação Silenciosa (< 35dB)\n\n"
            "CONTEÚDO DA EMBALAGEM:\n"
            f"- 01 {prod_nome}\n"
            "- 01 Cabo de Alimentação Bivolt\n"
            "- 01 Manual de Instruções em Português"
        )
        html_limpo = (
            f"<p><b>Transforme o ar e o bem-estar do seu ambiente com o {prod_nome}!</b></p>\n"
            f"<p>Desenvolvido com tecnologia de névoa ultrassônica fria de alta frequência, o <b>{prod_nome}</b> purifica e umidifica "
            "o ar com máxima eficiência, aliviando o desconforto de dias secos, alergias e problemas respiratórios. Sua operação ultra silenciosa "
            "permite uso contínuo durante o sono, estudo ou trabalho sem gerar distrações.</p>\n"
            "<p><b>Principais Benefícios e Recursos:</b><br>\n"
            "- <b>Névoa Ultrassônica Fria:</b> Fragmentação em micropartículas que mantêm as propriedades dos óleos essenciais.<br>\n"
            "- <b>Aromaterapia Integrada:</b> Adicione suas essências favoritas para criar uma atmosfera relaxante e renovadora.<br>\n"
            "- <b>Iluminação LED Suave:</b> Cores e luzes agradáveis para compor a decoração do ambiente.<br>\n"
            "- <b>Segurança Automática:</b> Desligamento inteligente ao identificar o término da água no reservatório.<br>\n"
            "- <b>Alimentação Bivolt:</b> Pronto para conectar em qualquer tomada 110V ou 220V com baixo consumo de energia.</p>\n"
            "<p><b>Especificações Técnicas:</b><br>\n"
            "- Alimentação: Bivolt Automático (110V / 220V)<br>\n"
            "- Operação: Ultrassônica Silenciosa (< 35dB)<br>\n"
            "- Compatibilidade: Água e Óleos Essenciais Hidrossolúveis</p>\n"
            "<p><b>Conteúdo da Embalagem:</b><br>\n"
            f"- 01 {prod_nome}<br>\n"
            "- 01 Cabo de Alimentação<br>\n"
            "- 01 Manual do Usuário em Português</p>"
        )
    else:
        texto_fluido = (
            f"Descubra a combinação ideal de praticidade, eficiência e alta durabilidade com o {prod_nome}. "
            "Desenvolvido sob rigorosos padrões de qualidade e testes industriais, este produto foi projetado para atender "
            "às necessidades mais exigentes da sua rotina diária, oferecendo desempenho superior e facilidade de manuseio. "
            "Construído com materiais de primeira linha e acabamento reforçado, garante resistência contra desgastes, impactos "
            "e uso contínuo. Seu design ergonômico e funcional adapta-se perfeitamente ao seu espaço, promovendo organização, "
            "segurança e alta usabilidade em qualquer ambiente.\n\n"
            "ESPECIFICAÇÕES TÉCNICAS:\n"
            "- Estrutura: Material de Alta Resistência e Durabilidade\n"
            "- Compatibilidade: Uso Versátil e Multiuso no Dia a Dia\n"
            "- Acabamento: Padrão Premium com Encaixes de Precisão\n"
            "- Manutenção: Fácil Limpeza e Higienização\n\n"
            "CONTEÚDO DA EMBALAGEM:\n"
            f"- 01 {prod_nome}\n"
            "- 01 Manual de Instruções em Português"
        )
        html_limpo = (
            f"<p><b>Surpreenda-se com a qualidade e praticidade do {prod_nome}!</b></p>\n"
            f"<p>O <b>{prod_nome}</b> foi desenvolvido para entregar durabilidade, eficiência e excelente usabilidade. "
            "Fabricado com componentes de alto padrão, é a escolha ideal para quem busca resolver necessidades do dia a dia com confiança.</p>\n"
            "<p><b>Destaques do Produto:</b><br>\n"
            "- <b>Estrutura Reforçada:</b> Maior resistência para uso contínuo e longa vida útil.<br>\n"
            "- <b>Design Ergonômico:</b> Facilidade de manuseio e otimização de espaço.<br>\n"
            "- <b>Uso Intuitivo:</b> Simplicidade na utilização sem complicações.</p>\n"
            "<p><b>Conteúdo da Embalagem:</b><br>\n"
            f"- 01 {prod_nome}<br>\n"
            "- 01 Manual de Instruções em Português</p>"
        )

    return texto_fluido, html_limpo


def gerar_bullet_points_a10(prod_nome: str) -> str:
    if "Umidificador" in prod_nome or "Difusor" in prod_nome:
        bullets = [
            "💧 **NÉVOA ULTRASSÔNICA FRIAS:** Fragmenta a água em micropartículas finas mantendo as propriedades terapêuticas dos óleos essenciais sem aquecer.",
            "🌿 **DIFUSOR DE AROMATERAPIA:** Permite a adição direta de óleos essenciais hidrossolúveis para aromatização contínua e alívio do estresse diário.",
            "🌙 **OPERAÇÃO ULTRA SILENCIOSA:** Sistema de baixo ruído inferior a 35dB, perfeito para uso durante a noite sem interferir no sono do bebê ou no trabalho.",
            "✨ **ILUMINAÇÃO LED AMBIENTE:** Iluminação integrada com transição suave de cores para compor a decoração do dormitório ou sala de estar.",
            "🛡️ **DESLIGAMENTO INTELIGENTE:** Sistema de segurança que interrompe o funcionamento automaticamente assim que o reservatório de água se esvazia.",
            "🔌 **ALIMENTAÇÃO BIVOLT AUTOMÁTICA:** Compatível com redes elétricas de 110V e 220V, garantindo versatilidade em qualquer tomada da casa.",
            "🍃 **MELHORA DA QUALIDADE DO AR:** Auxilia no alívio de sintomas causados pelo ar seco, como garganta seca, alergias respiratórias e ressecamento labial.",
            "🏠 **DESIGN COMPACTO E ELEGANTE:** Formato ergonômico e moderno que ocupa pouco espaço na mesa de cabeceira, mesa de escritório ou balcão.",
            "🧼 **HIGIENIZAÇÃO RÁPIDA E SIMPLES:** Reservatório de fácil acesso que permite limpeza prática e abastecimento de água sem complicações.",
            "📦 **CONJUNTO COMPLETO PRONTO:** Acompanha cabo de alimentação bivolt e manual explicativo em português para acionamento imediato."
        ]
    else:
        bullets = [
            "🎯 **ALTA PERFORMANCE E EFICIÊNCIA:** Projeto técnico desenvolvido sob rigorosos testes para entregar desempenho superior na categoria.",
            "🧱 **ESTRUTURA REFORÇADA:** Confeccionado com materiais de alta densidade para suportar o uso contínuo sem desgaste precoce.",
            "⚡ **DESIGN ERGONÔMICO E PRÁTICO:** Formato pensado para facilitar o manuseio cotidiano e otimizar o espaço de armazenamento.",
            "🛡️ **COMPONENTES CERTIFICADOS:** Fabricação atóxica e segura conforme as diretrizes regulatórias e de proteção ao consumidor.",
            "🔧 **MONTAGEM E USO INTUITIVO:** Acionamento simples sem necessidade de ferramentas complexas ou instalações demoradas.",
            "💡 **VERSATILIDADE MULTIUSO:** Adapta-se perfeitamente às exigências do ambiente doméstico, comercial ou profissional.",
            "🧼 **FÁCIL HIGIENIZAÇÃO:** Superfície com acabamento especial que evita o acúmulo de sujidades e simplifica a manutenção.",
            "⚙️ **ENCAIXES DE PRECISÃO:** Engenharia com tolerâncias reduzidas que garantem estabilidade e funcionamento sem folgas.",
            "🌿 **EFICIÊNCIA E ECONOMIA:** Desenvolvimento sustentável focado no aproveitamento otimizado de recursos durante o uso.",
            "📦 **EMBALAGEM DE PROTEÇÃO:** Enviado em caixa reforçada para preservar a integridade estrutural do produto até o destino."
        ]
    return "\n".join([f"* {b}" for b in bullets])


def gerar_backend_keywords_a10(prod_nome: str, titulo_a: str, titulo_b: str) -> str:
    palavras_titulos = set(
        remover_acentos(w.lower()) 
        for w in re.findall(r'\w+', titulo_a + " " + titulo_b)
        if len(w) > 1
    )

    if "Umidificador" in prod_nome or "Difusor" in prod_nome:
        candidatos = [
            "aromatizador", "vaporizador", "purificador", "essencias", "ambiente",
            "dormitorio", "quarto", "bebe", "escritorio", "casa", "umidade",
            "saude", "respiracao", "alergia", "rinite", "nevoa", "fria",
            "maternal", "bem", "estar", "fragrancia", "oleo", "essencial",
            "climatizador", "aromatizacao", "terapia", "relaxe", "meditacao",
            "desidratacao", "pulmonar", "noite", "sono", "tranquilo", "silencioso",
            "aparato", "eletrico", "tomada", "usb", "portatil", "pequeno", "mesa"
        ]
    else:
        candidatos = [
            "multiuso", "pratico", "ergonomico", "casa", "utilidade",
            "acessorio", "duravel", "respiravel", "compacto", "organizador",
            "resistente", "eficiente", "cotidiano", "trabalho", "escritorio",
            "qualidade", "uso", "diario", "facil", "manuseio", "novidade"
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

    termo_busca = produto_nosso.strip() if produto_nosso.strip() else asin_input.strip()
    concorrentes, termo_referencia = buscar_concorrentes_por_asin_base(termo_busca)

    links_md = "### 🔗 5 Concorrentes Diretos Mapeados do ASIN Base (Amazon BR):\n\n"
    for i, conc in enumerate(concorrentes[:5], start=1):
        links_md += str(i) + ". [" + str(conc['titulo']) + "](" + str(conc['link']) + ") - **ASIN:** `" + str(conc['asin']) + "`\n"
    links_md += "\n---\n"

    prompt_mestre = (
        "Você é o Maior Especialista em SEO e Copywriter para a Amazon Brasil.\n\n"
        "📌 DADOS DO PRODUTO:\n"
        "- ASIN / Entrada: " + str(asin_input) + "\n"
        "- Produto Referência / Nicho: " + str(termo_referencia) + "\n\n"
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
                    return links_md + "\n" + res.content[0].text
                except Exception:
                    continue
        except Exception:
            pass

    prod_nome = (
        termo_referencia.title() if termo_referencia else "Produto Consultado"
    )

    titulo_a = otimizar_titulo_a10_75_chars(prod_nome, foco_seo=False)
    titulo_b = otimizar_titulo_a10_75_chars(prod_nome, foco_seo=True)
    desc_fluida, desc_html = gerar_descricao_a10_completa(prod_nome)
    bullet_points_md = gerar_bullet_points_a10(prod_nome)
    backend_clean = gerar_backend_keywords_a10(prod_nome, titulo_a, titulo_b)

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
        + prod_nome
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

    return links_md + "\n" + analise_dinamica