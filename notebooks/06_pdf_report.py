from __future__ import annotations

from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "notebooks" / "outputs"
COUNTRY_FILE = DATA_DIR / "country_metrics.csv"
INSIGHTS_FILE = DATA_DIR / "strategic_insights.txt"
PDF_OUTPUT = OUTPUTS_DIR / "IKEA_Executive_Report.pdf"


def create_executive_report() -> None:
    """Generate professional PDF executive report with insights and metrics."""
    
    doc = SimpleDocTemplate(str(PDF_OUTPUT), pagesize=letter, 
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=6,
        alignment=1,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#ff7f0e'),
        spaceAfter=12,
    )
    
    # Title & metadata
    story.append(Paragraph("IKEA Global Pricing Strategy", title_style))
    story.append(Paragraph("Executive Report", styles['Heading2']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Key metrics section
    country_df = pd.read_csv(COUNTRY_FILE)
    
    story.append(Paragraph("Executive Summary", heading_style))
    metrics_data = [
        ["Metric", "Value"],
        ["Total Countries Analyzed", str(country_df["country"].nunique())],
        ["Global Average Price (USD)", f"${country_df['avg_price_usd'].mean():,.2f}"],
        ["Most Expensive Market", f"{country_df.loc[country_df['avg_price_usd'].idxmax(), 'country']} (${country_df['avg_price_usd'].max():,.2f})"],
        ["Most Affordable Market", f"{country_df.loc[country_df['avg_price_usd'].idxmin(), 'country']} (${country_df['avg_price_usd'].min():,.2f})"],
        ["Average Product Rating", f"{country_df['avg_rating'].mean():.2f}/5.0"],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 3.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Strategic insights
    story.append(Paragraph("Strategic Insights & Recommendations", heading_style))
    
    if INSIGHTS_FILE.exists():
        insights_text = INSIGHTS_FILE.read_text()
        for line in insights_text.split("\n"):
            if line.strip() and not line.startswith("IKEA"):
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Top markets table
    story.append(PageBreak())
    story.append(Paragraph("Market Rankings", heading_style))
    
    top_5 = country_df.nlargest(5, "avg_price_usd")[["country", "avg_price_usd", "price_index", "affordability_index"]]
    top_data = [["Country", "Avg Price", "Price Index", "Affordability Index"]]
    for _, row in top_5.iterrows():
        top_data.append([
            row["country"],
            f"${row['avg_price_usd']:,.2f}",
            f"{row['price_index']:.2f}",
            f"{row['affordability_index']:.4f}",
        ])
    
    top_table = Table(top_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff7f0e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
    ]))
    story.append(top_table)
    
    # Build PDF
    doc.build(story)
    print(f"Executive report saved to: {PDF_OUTPUT}")


if __name__ == "__main__":
    create_executive_report()
