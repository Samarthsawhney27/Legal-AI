# courtroom/transcript.py

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


def generate_transcript_pdf(
    case_details: dict,
    prosecution_text: str,
    defense_text: str,
    verdict_text: str,
    sources: list,
) -> bytes:
    """
    Generate a formatted PDF transcript of the courtroom session.
    Returns bytes that can be used with st.download_button()

    case_details: dict with keys: type, accused, victim, location, incident
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CourtTitle",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=colors.HexColor("#444444"),
    )

    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#c0392b"),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#2c2c2c"),
    )

    verdict_style = ParagraphStyle(
        "Verdict",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        backColor=colors.HexColor("#f0f4f8"),
        borderPad=8,
        textColor=colors.HexColor("#1a1a2e"),
    )

    story = []

    # Header
    story.append(Paragraph("HIGH COURT OF INDIA", title_style))
    story.append(
        Paragraph("AI COURTROOM SIMULATOR — TRIAL TRANSCRIPT", subtitle_style)
    )
    story.append(
        Paragraph(
            f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            subtitle_style,
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e"))
    )
    story.append(Spacer(1, 12))

    # Case Details Table
    story.append(Paragraph("CASE DETAILS", section_header_style))
    case_data = [
        ["Case Type", case_details.get("type", "N/A")],
        ["Accused", case_details.get("accused", "N/A")],
        ["Complainant", case_details.get("victim", "N/A")],
        ["Location", case_details.get("location", "N/A")],
    ]
    table = Table(case_data, colWidths=[2 * inch, 5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                (
                    "ROWBACKGROUNDS",
                    (1, 0),
                    (-1, -1),
                    [colors.HexColor("#f8f9fa"), colors.white],
                ),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 8))

    # Case Incident
    story.append(
        Paragraph(
            "FACTS OF THE CASE:",
            ParagraphStyle("Bold", parent=body_style, fontName="Helvetica-Bold"),
        )
    )
    story.append(
        Paragraph(
            case_details.get("incident", "").replace("\n", "<br/>"), body_style
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc"))
    )

    # Prosecution
    story.append(Paragraph("PROSECUTION'S ARGUMENTS", section_header_style))
    story.append(
        Paragraph(prosecution_text.replace("\n", "<br/>"), body_style)
    )
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc"))
    )

    # Defense
    story.append(Paragraph("DEFENSE'S ARGUMENTS", section_header_style))
    story.append(Paragraph(defense_text.replace("\n", "<br/>"), body_style))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc"))
    )

    # Verdict
    story.append(Paragraph("JUDGE'S VERDICT", section_header_style))
    story.append(Paragraph(verdict_text.replace("\n", "<br/>"), verdict_style))
    story.append(Spacer(1, 12))
    story.append(
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e"))
    )

    # Sources
    if sources:
        story.append(Paragraph("LEGAL SOURCES RETRIEVED", section_header_style))
        for i, src in enumerate(sources, 1):
            story.append(
                Paragraph(
                    f"<b>[{i}]</b> {src['source']} | Page: {src['page']}<br/>"
                    f"<i>{src['preview']}</i>",
                    ParagraphStyle(
                        "Source", parent=body_style, fontSize=8, spaceAfter=6
                    ),
                )
            )

    # Footer
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "DISCLAIMER: This is an AI-generated simulation for educational purposes only. "
            "This does not constitute legal advice. Consult a qualified lawyer for actual legal matters.",
            ParagraphStyle(
                "Disclaimer",
                parent=body_style,
                fontSize=8,
                textColor=colors.HexColor("#888888"),
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(story)
    return buffer.getvalue()
