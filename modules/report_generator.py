import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf_diagnostico(sku, preco_buy_box, custo_unitario, regime, resultados_dict):
    """
    Gera um relatório executivo em PDF estilizado contendo a análise 360° do SKU.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0d1117'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1f6beb'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#24292f')
    )

    # Cabeçalho
    story.append(Paragraph(f"⚡ Relatório Executivo de Operações — ASIN {sku}", title_style))
    story.append(Spacer(1, 10))

    # Tabela Metricas Principais
    dados_tabela = [
        ["ASIN", "Preço Buy Box", "Custo Unitário", "Regime Tributário"],
        [sku, f"R$ {preco_buy_box:.2f}", f"R$ {custo_unitario:.2f}", regime]
    ]
    t = Table(dados_tabela, colWidths=[120, 120, 120, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#161b22')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f6f8fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d7de')),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Adicionar Seções das Análises
    secoes = [
        ("📝 SEO & Otimização de Listing", resultados_dict.get("seo", "")),
        ("💰 Precificação & Repricer Guard", resultados_dict.get("precificacao", "")),
        ("🚚 Comparativo Logístico FBA/DBA", resultados_dict.get("logistica", "")),
        ("⚖️ Planejamento Fiscal (Lucro Real)", resultados_dict.get("fiscal", ""))
    ]

    for titulo, conteudo in secoes:
        story.append(Paragraph(titulo, h2_style))
        # Limpar formatacao markdown basica para o PDF
        texto_limpo = conteudo.replace("### ", "").replace("**", "").replace("* ", "• ")
        for linha in texto_limpo.split("\n"):
            if linha.strip():
                story.append(Paragraph(linha.strip(), body_style))
                story.append(Spacer(1, 2))
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer