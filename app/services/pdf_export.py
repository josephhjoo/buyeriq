from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io

DARK_BG    = colors.HexColor('#1a1d27')
ACCENT     = colors.HexColor('#6366f1')
TEXT_MUTED = colors.HexColor('#64748b')
CARD_BG    = colors.HexColor('#0f1117')
GREEN      = colors.HexColor('#34d399')
YELLOW     = colors.HexColor('#fbbf24')
RED        = colors.HexColor('#f87171')


def _confidence_color(score):
    if score >= 70:
        return GREEN
    if score >= 40:
        return YELLOW
    return RED


def generate_buyer_report(search: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.6 * inch, leftMargin=0.6 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    )

    title_style = ParagraphStyle('Title', fontSize=22, fontName='Helvetica-Bold',
                                 textColor=colors.white, leading=26)
    sub_style = ParagraphStyle('Sub', fontSize=10, fontName='Helvetica',
                               textColor=TEXT_MUTED, spaceAfter=2)
    label_style = ParagraphStyle('Label', fontSize=8, fontName='Helvetica-Bold',
                                 textColor=TEXT_MUTED, spaceAfter=6)
    cell_style = ParagraphStyle('Cell', fontSize=8, fontName='Helvetica',
                                textColor=colors.black, leading=11)
    notes_style = ParagraphStyle('Notes', fontSize=9, fontName='Helvetica',
                                 textColor=colors.black, leading=14, spaceAfter=10)

    story = []

    # ── Header ────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(f"<b>Buyer List — {search.get('target_name', 'Confidential')}</b>", title_style),
        Paragraph(f"<b>{len(search.get('buyers', []))}</b><br/>"
                  f"<font size=8 color='#64748b'>BUYERS IDENTIFIED</font>",
                  ParagraphStyle('Count', fontSize=26, fontName='Helvetica-Bold',
                                 textColor=ACCENT, alignment=TA_RIGHT, leading=30)),
    ]]
    header_table = Table(header_data, colWidths=[5.2 * inch, 2.1 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BACKGROUND', (0, 0), (-1, -1), DARK_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (0, -1), 14),
        ('RIGHTPADDING', (-1, 0), (-1, -1), 14),
    ]))
    story.append(header_table)

    meta = (f"{search.get('industry', '—')}  ·  {search.get('geography', '—')}  ·  "
            f"${search.get('revenue_m', '—')}M revenue")
    story.append(Paragraph(meta, sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=14))

    # ── Research notes ────────────────────────────────────────────────────
    if search.get("research_notes"):
        story.append(Paragraph("RESEARCH NOTES", label_style))
        story.append(Paragraph(search["research_notes"], notes_style))

    # ── Buyer table ───────────────────────────────────────────────────────
    story.append(Paragraph("RANKED BUYER LIST", label_style))

    table_data = [['#', 'FIRM', 'TYPE', 'CONTACT', 'CONF.', 'RATIONALE']]
    confidence_colors = []
    for i, b in enumerate(search.get("buyers", [])):
        contact = b.get("contact_name") or "Not found"
        if b.get("contact_title"):
            contact += f"\n{b['contact_title']}"
        table_data.append([
            str(i + 1),
            Paragraph(b.get("firm_name", ""), cell_style),
            (b.get("buyer_type") or "")[:9].title(),
            Paragraph(contact.replace("\n", "<br/>"), cell_style),
            f"{b.get('confidence', 0)}",
            Paragraph(b.get("rationale", ""), cell_style),
        ])
        confidence_colors.append(_confidence_color(b.get("confidence", 0)))

    buyer_table = Table(
        table_data,
        colWidths=[0.3 * inch, 1.5 * inch, 0.7 * inch, 1.6 * inch, 0.5 * inch, 2.7 * inch],
        repeatRows=1,
    )
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    # Color each confidence cell
    for row_idx, conf_color in enumerate(confidence_colors, start=1):
        style.append(('TEXTCOLOR', (4, row_idx), (4, row_idx), conf_color))
        style.append(('FONTNAME', (4, row_idx), (4, row_idx), 'Helvetica-Bold'))
    buyer_table.setStyle(TableStyle(style))
    story.append(buyer_table)

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BG, spaceAfter=6))
    story.append(Paragraph(
        "Generated by BuyerIQ · AI-assisted research — verify contacts before outreach · Confidential",
        ParagraphStyle('Footer', fontSize=7, textColor=TEXT_MUTED, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
