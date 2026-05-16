import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from src.config import Config
import uuid
from xml.sax.saxutils import escape


class PDFGenerator:
    """Converts LLM markdown output into a professional PDF report."""

    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name="CustomBody",
            parent=self.styles["Normal"],
            spaceAfter=8,
            leading=14,
        ))
        self.styles.add(ParagraphStyle(
            name="Citation",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=4,
        ))

    def generate(self, content: str, title: str = "Financial Report") -> str:
        """Convert markdown content to a PDF. Returns the file path."""
        filename = f"{uuid.uuid4().hex[:8]}_report.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        story = []

        # Title
        story.append(Paragraph(escape(title), self.styles["Title"]))
        story.append(Spacer(1, 12))

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Headings
            if line.startswith("### "):
                story.append(Spacer(1, 6))
                story.append(Paragraph(escape(line[4:]), self.styles["Heading3"]))
            elif line.startswith("## "):
                story.append(Spacer(1, 8))
                story.append(Paragraph(escape(line[3:]), self.styles["Heading2"]))
            elif line.startswith("# "):
                story.append(Spacer(1, 10))
                story.append(Paragraph(escape(line[2:]), self.styles["Heading1"]))

            # Markdown table — collect all consecutive | lines
            elif line.strip().startswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1
                i -= 1  # will be incremented at end of loop
                story.append(self._build_table(table_lines))
                story.append(Spacer(1, 8))

            # Citations
            elif line.strip().startswith("[Source:"):
                story.append(Paragraph(escape(line.strip()), self.styles["Citation"]))

            # Regular paragraph
            else:
                safe = escape(line.strip())
                # Bold
                safe = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", safe)
                story.append(Paragraph(safe, self.styles["CustomBody"]))

            i += 1

        doc.build(story)
        return filepath

    @staticmethod
    def _build_table(table_lines: list) -> Table:
        """Parse markdown table lines into a ReportLab Table."""
        rows = []
        for line in table_lines:
            # Skip separator rows like |---|---|
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            rows.append(cells)

        if not rows:
            return Spacer(1, 0)

        t = Table(rows, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t
