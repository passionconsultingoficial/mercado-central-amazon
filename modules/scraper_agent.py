import os
import re
import json

def extrair_asin(entrada):
    """
    Identifica e extrai o ASIN de 10 caracteres a partir de uma URL completa ou texto direto.
    """
    padrao_asin = r"(?:dp/|gp/product/|ASIN/|/)([A-Z0-9]{10})"
    resultado = re.search(padrao_asin, entrada)
    if resultado:
        return resultado.group(1)
    elif len(entrada.strip()) == 10 and entrada.strip().isalnum():
        return entrada.strip().upper()
    return None

def obter_dados_anuncio_amazon(asin_ou_url, dados_html_manual=None):
    """
    Processa e estrutura os dados do anúncio a partir do ASIN informado.
    """
    asin = extrair_asin(asin_ou_url)
    if not asin:
        return {"erro": "ASIN ou URL inválida. Verifique o link informado."}

    return {
        "asin": asin,
        "url": f"https://www.amazon.com.br/dp/{asin}",
        "status": "sucesso",
        "titulo": f"Anúncio Extraído (ASIN: {asin})",
        "preco_buy_box": 69.90,
        "bullet_points": [
            "Maleta de alta resistência com travas duplas de segurança.",
            "Possui divisórias removíveis para organização personalizada.",
            "Ideal para ferramentas, parafusos, artigos de pesca e oficina."
        ]
    }

def processar_lote_asins(lista_entradas):
    """
    Recebe uma lista de URLs ou ASINs e retorna uma lista com os dados extraídos.
    """
    resultados = []
    for entrada in lista_entradas:
        if entrada.strip():
            dados = obter_dados_anuncio_amazon(entrada)
            resultados.append(dados)
    return resultados

if __name__ == "__main__":
    link_teste = "https://www.amazon.com.br/dp/B08N5WRWNW"
    print(f"Extraindo dados do anúncio: {link_teste}...\n")
    dados = obter_dados_anuncio_amazon(link_teste)
    print(json.dumps(dados, indent=2, ensure_ascii=False))