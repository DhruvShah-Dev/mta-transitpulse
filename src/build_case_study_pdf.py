"""Render the reviewed Markdown case study as a portable executive PDF."""

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports" / "EXECUTIVE_CASE_STUDY.md"
DEST = ROOT / "reports" / "EXECUTIVE_CASE_STUDY.pdf"
NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#177CB8")
PALE = colors.HexColor("#F2F7FA")
MUTED = colors.HexColor("#546B7B")


def register_fonts():
    import reportlab
    fonts = Path(reportlab.__file__).parent / "fonts"
    for name, filename in [("Vera", "Vera.ttf"), ("Vera-Bold", "VeraBd.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily("Vera", normal="Vera", bold="Vera-Bold")


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)",
                  lambda m: f'<link href="{html.escape(m.group(2), quote=True)}" color="#177CB8">{m.group(1)}</link>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font color="#17324D">\1</font>', text)
    return text


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName="Vera-Bold", fontSize=20,
                                leading=25, textColor=NAVY, alignment=TA_LEFT, spaceAfter=12),
        "byline": ParagraphStyle("byline", fontName="Vera", fontSize=8.3, leading=12,
                                 textColor=MUTED, spaceAfter=10),
        "h2": ParagraphStyle("h2", fontName="Vera-Bold", fontSize=12, leading=17,
                             textColor=NAVY, spaceBefore=13, spaceAfter=5, keepWithNext=True),
        "h3": ParagraphStyle("h3", fontName="Vera-Bold", fontSize=10.3, leading=15,
                             textColor=BLUE, spaceBefore=9, spaceAfter=4, keepWithNext=True),
        "body": ParagraphStyle("body", fontName="Vera", fontSize=8.8, leading=13.3,
                               textColor=NAVY, spaceAfter=7),
        "list": ParagraphStyle("list", fontName="Vera", fontSize=8.8, leading=13.3,
                               textColor=NAVY, leftIndent=16, firstLineIndent=-14, spaceAfter=5),
        "caption": ParagraphStyle("caption", fontName="Vera", fontSize=7.6, leading=11,
                                  textColor=MUTED, alignment=TA_CENTER, spaceAfter=10),
        "table_head": ParagraphStyle("table_head", fontName="Vera-Bold", fontSize=7.2,
                                     leading=10, textColor=colors.white),
        "table_cell": ParagraphStyle("table_cell", fontName="Vera", fontSize=7.2,
                                     leading=10, textColor=NAVY),
    }


def table_flow(lines, s, width):
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in lines if not re.match(r"^\|[\s:|\-]+\|$", line)]
    if not rows:
        return None
    n = len(rows[0])
    widths = ([60, 67, 95, 101, 62, width - 385] if n == 6 else [width / n] * n)
    rendered = [[Paragraph(inline(cell), s["table_head"] if i == 0 else s["table_cell"])
                 for cell in row] for i, row in enumerate(rows)]
    t = Table(rendered, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#D6E3EB")),
    ]))
    return t


def make_story():
    s = styles()
    width = A4[0] - 90
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    paragraph = []

    def flush():
        if paragraph:
            text = " ".join(paragraph).replace("  ", " ")
            story.append(Paragraph(inline(text), s["body"]))
            paragraph.clear()

    i = 0
    while i < len(lines):
        raw = lines[i].strip()
        if not raw:
            flush()
            i += 1
            continue
        if raw.startswith("# "):
            flush()
            story.append(Paragraph(inline(raw[2:]), s["title"]))
        elif raw.startswith("## "):
            flush()
            if raw == "## Sources and reproducibility":
                story.append(PageBreak())
            story.append(Paragraph(inline(raw[3:]), s["h2"]))
        elif raw.startswith("### "):
            flush()
            story.append(Paragraph(inline(raw[4:]), s["h3"]))
        elif raw.startswith("!["):
            flush()
            match = re.match(r"!\[([^]]+)\]\(([^)]+)\)", raw)
            if match:
                path = (SOURCE.parent / match.group(2).replace("%20", " ")).resolve()
                image = ImageReader(str(path))
                iw, ih = image.getSize()
                image_width = width * 0.84
                story.append(Image(str(path), width=image_width,
                                   height=image_width * ih / iw, hAlign="CENTER"))
                story.append(Paragraph(match.group(1), s["caption"]))
        elif raw.startswith("|"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            story.append(table_flow(block, s, width))
            story.append(Spacer(1, 9))
            continue
        elif re.match(r"^\d+\. ", raw):
            flush()
            story.append(Paragraph(inline(raw), s["list"]))
        elif raw.startswith("**") and "**" in raw[2:] and "Prepared" in raw:
            flush()
            story.append(Paragraph(inline(raw.replace("  ", "<br/>")), s["byline"]))
        else:
            paragraph.append(raw.rstrip("  "))
        i += 1
    flush()
    return story


def decorate(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 8, w, 8, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#CBDDE8"))
    canvas.line(45, 38, w - 45, 38)
    canvas.setFont("Vera", 7.3)
    canvas.setFillColor(MUTED)
    canvas.drawString(45, 26, "MTA TransitPulse  |  Portfolio case study  |  2022–2025 evidence")
    canvas.drawRightString(w - 45, 26, str(doc.page))
    canvas.restoreState()


def main():
    register_fonts()
    doc = SimpleDocTemplate(str(DEST), pagesize=A4, rightMargin=45, leftMargin=45,
                            topMargin=42, bottomMargin=53,
                            title="MTA TransitPulse | Subway Reliability and Passenger Impact",
                            author="TransitPulse Data Analyst portfolio project")
    doc.build(make_story(), onFirstPage=decorate, onLaterPages=decorate)
    print(f"Wrote {DEST}")


if __name__ == "__main__":
    main()
