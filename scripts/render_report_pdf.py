"""Renderiza docs/informe.md a un PDF sencillo para la entrega."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "informe.md"
OUTPUT = ROOT / "docs" / "informe.pdf"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text: str) -> str:
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


def build() -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleEs", parent=styles["Title"], alignment=TA_CENTER, fontSize=18, leading=22, spaceAfter=12))
    styles.add(ParagraphStyle(name="H2Es", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="BodyEs", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=6))
    styles.add(ParagraphStyle(name="SmallEs", parent=styles["BodyText"], fontSize=8, leading=10, textColor="#444444"))

    story = []
    code = False
    code_lines: list[str] = []
    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if code:
                story.append(Preformatted("\n".join(code_lines), styles["Code"]))
                story.append(Spacer(1, 3 * mm))
                code_lines = []
            code = not code
            continue
        if code:
            code_lines.append(line)
            continue
        if not line:
            story.append(Spacer(1, 2 * mm))
        elif line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), styles["TitleEs"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), styles["H2Es"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), styles["Heading3"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + inline(line[2:]), styles["BodyEs"]))
        elif line.startswith("| "):
            story.append(Paragraph(inline(line.replace("|", "  |  ")), styles["SmallEs"]))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(inline(line), styles["BodyEs"]))
        else:
            story.append(Paragraph(inline(line), styles["BodyEs"]))

    document = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                                 topMargin=16 * mm, bottomMargin=16 * mm, title="Extractor de facturas FEL")
    document.build(story)
    print(f"PDF generado: {OUTPUT}")


if __name__ == "__main__":
    build()