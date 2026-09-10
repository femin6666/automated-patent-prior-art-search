import os
import uuid
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.app.models.models import Search, SearchResult, Patent

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "generated_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_pdf_report(search: Search, results: list) -> str:
    """
    Generate a clean PDF prior-art search report using ReportLab.
    Returns absolute path of generated PDF file.
    """
    filename = f"patentlens_report_{search.id[:8]}_{int(datetime.now(timezone.utc).timestamp())}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#475569')
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E293B'),
        fontName='Helvetica-Bold',
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B'),
        fontName='Helvetica-Oblique'
    )

    elements = []

    # 1. Header & Branding
    elements.append(Paragraph("PATENTLENS AI", title_style))
    elements.append(Paragraph("AI-Powered Semantic Prior-Art Search Report", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563EB'), spaceAfter=15))

    # 2. Metadata Table
    meta_data = [
        [Paragraph("<b>Invention Title:</b>", body_style), Paragraph(search.invention_title, body_style)],
        [Paragraph("<b>Technology Domain:</b>", body_style), Paragraph(search.domain, body_style)],
        [Paragraph("<b>Search Date:</b>", body_style), Paragraph(search.created_at.strftime("%Y-%m-%d %H:%M UTC"), body_style)],
        [Paragraph("<b>Prior-Art Risk Level:</b>", body_style), Paragraph(f"<font color='#DC2626'><b>{search.risk_level}</b></font>", body_style)],
        [Paragraph("<b>Highest Similarity Score:</b>", body_style), Paragraph(f"<b>{search.highest_similarity}%</b>", body_style)],
    ]
    t_meta = Table(meta_data, colWidths=[140, 390])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 15))

    # 3. Invention Summary
    elements.append(Paragraph("Invention Summary & Problem Solved", section_style))
    elements.append(Paragraph(f"<b>Problem Statement:</b> {search.problem_statement}", body_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>Detailed Description:</b> {search.description}", body_style))
    if search.keywords:
        elements.append(Spacer(1, 4))
        kw_str = ", ".join(search.keywords)
        elements.append(Paragraph(f"<b>User Keywords:</b> {kw_str}", body_style))
    elements.append(Spacer(1, 15))

    # 4. Search Methodology
    elements.append(Paragraph("AI Search Methodology & Scoring Formula", section_style))
    methodology_text = (
        "This prior-art assessment utilizes SBERT vector embedding retrieval, Lens Patent API multi-path search, "
        "and an authoritative 5-factor scoring architecture: (25% SBERT Semantic Similarity) + (35% Technical Feature Overlap) + "
        "(20% Evidence Verification Strength) + (10% Distinctive Concepts) + (10% Domain & CPC Classification Alignment). "
        "Scores are subject to transparent data availability caps and evidence verification gating."
    )
    elements.append(Paragraph(methodology_text, body_style))
    elements.append(Spacer(1, 15))

    # 5. Top Patent Results Table
    elements.append(Paragraph("Top 5 Similar Patent Results", section_style))
    
    table_data = [
        [
            Paragraph("<b>Rank</b>", body_style),
            Paragraph("<b>Patent Number & Title</b>", body_style),
            Paragraph("<b>Domain</b>", body_style),
            Paragraph("<b>Semantic</b>", body_style),
            Paragraph("<b>Canonical Score</b>", body_style)
        ]
    ]

    for item in results[:5]:
        pat = item.patent if hasattr(item, "patent") else item.get("patent")
        pat_num = pat.patent_number if hasattr(pat, "patent_number") else pat.get("patent_number")
        pat_title = pat.title if hasattr(pat, "title") else pat.get("title")
        pat_domain = pat.domain if hasattr(pat, "domain") else pat.get("domain")
        rank_val = getattr(item, "rank", 1)
        sem_val = getattr(item, "semantic_score", 0.0)
        final_val = getattr(item, "final_score", 0.0)

        p_info = f"<b>{pat_num}</b><br/>{pat_title}"
        table_data.append([
            Paragraph(f"#{rank_val}", body_style),
            Paragraph(p_info, body_style),
            Paragraph(pat_domain, body_style),
            Paragraph(f"{sem_val}%", body_style),
            Paragraph(f"<b>{final_val}%</b>", body_style)
        ])

    t_results = Table(table_data, colWidths=[40, 260, 90, 70, 70])
    t_results.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_results)
    elements.append(Spacer(1, 20))

    # 6. Legal Disclaimer
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    disclaimer_notice = (
        "<b>IMPORTANT LEGAL DISCLAIMER:</b> PatentLens AI provides AI-assisted preliminary prior-art search results "
        "for informational and research purposes only. The results do not constitute legal advice, a patentability "
        "determination, or a professional patent opinion. All search findings are based on vector dataset analysis."
    )
    elements.append(Paragraph(disclaimer_notice, disclaimer_style))

    doc.build(elements)
    return filepath
