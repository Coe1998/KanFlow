"""
KanFlow – PDF Builder
Converts a Markdown string into a styled PDF document using ReportLab.
No external fonts required — uses built-in Helvetica family + Courier.
"""

import io
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import (
    HexColor, white, black, Color
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted, KeepTogether
)
from reportlab.platypus.flowables import Flowable

# ── Colour palette (light theme — readable on white paper) ───────────────────
C_BG        = HexColor("#ffffff")          # page background (white)
C_SURFACE   = HexColor("#f4f4f8")          # subtle grey surface (header/footer bar)
C_SURFACE2  = HexColor("#ebebf0")          # slightly darker surface (table alt row)
C_ACCENT    = HexColor("#4f46e5")          # indigo accent (headings, rules, cover bar)
C_SUCCESS   = HexColor("#059669")          # green (done stats)
C_WARNING   = HexColor("#d97706")          # amber (wip stats)
C_TEXT1     = HexColor("#111118")          # near-black — body text
C_TEXT2     = HexColor("#374151")          # dark grey — secondary text
C_TEXT3     = HexColor("#6b7280")          # medium grey — captions, meta
C_CODE_BG   = HexColor("#1e1e2e")          # dark code block background (keeps contrast)
C_CODE_FG   = HexColor("#e2e8f0")          # light code text inside dark block
C_BORDER    = HexColor("#d1d5db")          # light grey border
C_PURPLE_LT = HexColor("#4f46e5")          # inline code colour (indigo on light bg)

PAGE_W, PAGE_H = A4
MARGIN_L = 2.2 * cm
MARGIN_R = 2.2 * cm
MARGIN_T = 2.5 * cm
MARGIN_B = 2.0 * cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


# ── Custom flowable: filled rounded rectangle for code blocks ─────────────────

class CodeBlock(Flowable):
    """A dark background block that renders preformatted code text."""

    PAD = 10   # padding in points

    def __init__(self, code_lines: list[str], lang: str = ""):
        super().__init__()
        self.code_lines = code_lines
        self.lang       = lang
        self.width      = CONTENT_W
        self._line_h    = 11      # points per line
        self._font_size = 7.5

    def wrap(self, availWidth, availHeight):
        self.width = min(availWidth, CONTENT_W)
        header_h   = 14 if self.lang else 0
        body_h     = len(self.code_lines) * self._line_h + self.PAD * 2
        self.height = header_h + body_h
        return self.width, self.height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        # Background rectangle
        c.setFillColor(C_CODE_BG)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=0)

        # Optional language label bar
        y_offset = 0
        if self.lang:
            bar_h = 14
            c.setFillColor(HexColor("#1a1a24"))
            c.roundRect(0, h - bar_h, w, bar_h, 4, fill=1, stroke=0)
            # cover bottom rounded corners of label bar
            c.rect(0, h - bar_h, w, bar_h / 2, fill=1, stroke=0)
            c.setFillColor(C_TEXT3)
            c.setFont("Courier", 6.5)
            c.drawString(self.PAD, h - bar_h + 4, self.lang.upper())
            y_offset = bar_h

        # Code text
        c.setFont("Courier", self._font_size)
        y = h - y_offset - self.PAD - self._line_h + 2
        for line in self.code_lines:
            c.setFillColor(C_CODE_FG)
            # Simple syntax colouring: strings in light green
            c.drawString(self.PAD, y, line[:120])   # truncate very long lines
            y -= self._line_h
            if y < self.PAD:
                break

        # Thin border
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 4, fill=0, stroke=1)


# ── Style definitions ─────────────────────────────────────────────────────────

def _styles():
    base = dict(
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=C_TEXT1,
        backColor=None,
    )

    def s(name, **kw):
        merged = {**base, **kw}
        return ParagraphStyle(name, **merged)

    return {
        "h1": s("h1",
                fontName="Helvetica-Bold", fontSize=22, leading=28,
                textColor=C_TEXT1, spaceAfter=6, spaceBefore=0),
        "h1_sub": s("h1_sub",
                    fontName="Helvetica", fontSize=10, textColor=C_TEXT2,
                    spaceAfter=16),
        "h2": s("h2",
                fontName="Helvetica-Bold", fontSize=15, leading=20,
                textColor=C_TEXT1, spaceBefore=20, spaceAfter=6),
        "h3": s("h3",
                fontName="Helvetica-Bold", fontSize=11, leading=15,
                textColor=C_TEXT2, spaceBefore=12, spaceAfter=4),
        "body": s("body",
                  alignment=TA_JUSTIFY, spaceAfter=6),
        "body_bold": s("body_bold",
                       fontName="Helvetica-Bold"),
        "li": s("li",
                leftIndent=14, spaceAfter=3, leading=13),
        "li2": s("li2",
                 leftIndent=28, spaceAfter=2, leading=12, fontSize=8.5,
                 textColor=C_TEXT2),
        "caption": s("caption",
                     fontSize=7.5, textColor=C_TEXT3, alignment=TA_CENTER),
        "meta": s("meta",
                  fontSize=8, textColor=C_TEXT3, spaceAfter=2),
        "inline_code": s("inline_code",
                         fontName="Courier", fontSize=8, textColor=C_PURPLE_LT,
                         backColor=C_SURFACE2),
    }


# ── Inline markup helper ──────────────────────────────────────────────────────

def _inline(text: str) -> str:
    """Convert inline Markdown markup to ReportLab XML tags."""
    # Escape XML special chars first (except already-converted sequences)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Inline code  `foo`
    text = re.sub(
        r'`([^`]+)`',
        lambda m: (
            f'<font name="Courier" size="8" color="{C_PURPLE_LT.hexval()}">'
            f'{m.group(1)}</font>'
        ),
        text
    )
    # Bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__',     r'<b>\1</b>', text)
    # Italic *text* or _text_
    text = re.sub(r'\*(.+?)\*',  r'<i>\1</i>', text)
    text = re.sub(r'_([^_]+)_',  r'<i>\1</i>', text)

    return text


# ── Markdown → Flowables parser ───────────────────────────────────────────────

def _parse_markdown(md: str, styles: dict) -> list:
    """Parse Markdown text into a list of ReportLab Flowables."""
    flowables = []
    lines     = md.splitlines()
    i         = 0

    while i < len(lines):
        line = lines[i]

        # ── Fenced code block ─────────────────────────────────────────────
        fence_match = re.match(r'^```(\w*)', line)
        if fence_match:
            lang        = fence_match.group(1)
            code_lines  = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            flowables.append(Spacer(1, 4))
            flowables.append(CodeBlock(code_lines, lang))
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # ── H1 ────────────────────────────────────────────────────────────
        h1 = re.match(r'^# (.+)', line)
        if h1:
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph(_inline(h1.group(1)), styles["h1"]))
            flowables.append(
                HRFlowable(width="100%", thickness=1, color=C_ACCENT,
                           spaceAfter=8, spaceBefore=2)
            )
            i += 1
            continue

        # ── H2 ────────────────────────────────────────────────────────────
        h2 = re.match(r'^## (.+)', line)
        if h2:
            flowables.append(
                HRFlowable(width="100%", thickness=0.3, color=C_BORDER,
                           spaceBefore=4, spaceAfter=2)
            )
            flowables.append(Paragraph(_inline(h2.group(1)), styles["h2"]))
            i += 1
            continue

        # ── H3 ────────────────────────────────────────────────────────────
        h3 = re.match(r'^### (.+)', line)
        if h3:
            flowables.append(Paragraph(_inline(h3.group(1)), styles["h3"]))
            i += 1
            continue

        # ── Horizontal rule ───────────────────────────────────────────────
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', line.strip()):
            flowables.append(
                HRFlowable(width="100%", thickness=0.5, color=C_BORDER,
                           spaceBefore=8, spaceAfter=8)
            )
            i += 1
            continue

        # ── Unordered list item ───────────────────────────────────────────
        li = re.match(r'^(\s*)[-*+] (.+)', line)
        if li:
            indent = len(li.group(1))
            style  = styles["li2"] if indent >= 2 else styles["li"]
            bullet = "◦" if indent >= 2 else "•"
            flowables.append(
                Paragraph(f"{bullet}  {_inline(li.group(2))}", style)
            )
            i += 1
            continue

        # ── Ordered list item ─────────────────────────────────────────────
        oli = re.match(r'^(\s*)\d+\. (.+)', line)
        if oli:
            flowables.append(
                Paragraph(f"  {_inline(oli.group(2))}", styles["li"])
            )
            i += 1
            continue

        # ── Blockquote ────────────────────────────────────────────────────
        bq = re.match(r'^> (.+)', line)
        if bq:
            bq_style = ParagraphStyle(
                "bq", parent=styles["body"],
                leftIndent=12, borderPad=6,
                borderColor=C_ACCENT, borderWidth=2,
                textColor=C_TEXT2, fontName="Helvetica-Oblique"
            )
            flowables.append(Paragraph(_inline(bq.group(1)), bq_style))
            i += 1
            continue

        # ── Blank line ────────────────────────────────────────────────────
        if line.strip() == "":
            flowables.append(Spacer(1, 5))
            i += 1
            continue

        # ── Regular paragraph ─────────────────────────────────────────────
        flowables.append(Paragraph(_inline(line), styles["body"]))
        i += 1

    return flowables


# ── Page template (header/footer) ─────────────────────────────────────────────

class _PageDecor:
    def __init__(self, project_name: str, generated_on: str):
        self.project_name = project_name
        self.generated_on = generated_on

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        # Top stripe
        canvas.setFillColor(C_SURFACE)
        canvas.rect(0, h - 1.4 * cm, w, 1.4 * cm, fill=1, stroke=0)
        canvas.setFillColor(C_ACCENT)
        canvas.rect(0, h - 1.4 * cm, 3, 1.4 * cm, fill=1, stroke=0)

        # Header text
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(C_TEXT1)
        canvas.drawString(MARGIN_L, h - 0.85 * cm, self.project_name)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(C_TEXT3)
        canvas.drawRightString(w - MARGIN_R, h - 0.85 * cm, "Documentazione tecnica")

        # Footer stripe
        canvas.setFillColor(C_SURFACE)
        canvas.rect(0, 0, w, 1.2 * cm, fill=1, stroke=0)
        canvas.setFillColor(C_TEXT3)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN_L, 0.45 * cm, f"Generato il {self.generated_on} • KanFlow")
        canvas.drawRightString(
            w - MARGIN_R, 0.45 * cm,
            f"Pagina {doc.page}"
        )

        canvas.restoreState()


# ── Cover page ────────────────────────────────────────────────────────────────

def _make_cover(project_name: str, generated_on: str,
                task_stats: dict, styles: dict) -> list:
    flows = []

    # Large vertical spacer to push content down
    flows.append(Spacer(1, 3.5 * cm))

    # Accent bar left
    flows.append(
        HRFlowable(width="100%", thickness=3, color=C_ACCENT,
                   spaceBefore=0, spaceAfter=20)
    )

    # Title
    cover_title = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold", fontSize=30, leading=36,
        textColor=C_TEXT1, alignment=TA_LEFT
    )
    flows.append(Paragraph(project_name, cover_title))
    flows.append(Spacer(1, 8))

    # Subtitle
    cover_sub = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica", fontSize=12,
        textColor=C_TEXT2, alignment=TA_LEFT
    )
    flows.append(Paragraph("Documentazione Tecnica", cover_sub))
    flows.append(Spacer(1, 40))

    # Stats table
    done = task_stats.get("done", 0)
    wip  = task_stats.get("in_progress", 0)
    todo = task_stats.get("todo", 0)
    tot  = done + wip + todo
    pct  = round(done / tot * 100) if tot > 0 else 0

    cell_style = ParagraphStyle("cs", fontName="Helvetica-Bold",
                                fontSize=22, textColor=C_TEXT1, alignment=TA_CENTER)
    label_style = ParagraphStyle("ls", fontName="Helvetica",
                                 fontSize=7.5, textColor=C_TEXT3, alignment=TA_CENTER)
    data = [[
        Paragraph(str(tot),  cell_style),
        Paragraph(str(done), cell_style),
        Paragraph(str(wip),  cell_style),
        Paragraph(str(todo), cell_style),
        Paragraph(f"{pct}%", cell_style),
    ],[
        Paragraph("Task totali",    label_style),
        Paragraph("Completate",     label_style),
        Paragraph("In corso",       label_style),
        Paragraph("Da fare",        label_style),
        Paragraph("Completamento",  label_style),
    ]]

    col_w = CONTENT_W / 5
    tbl = Table(data, colWidths=[col_w] * 5, rowHeights=[30, 16])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), C_SURFACE),
        ("BACKGROUND",  (1, 0), (1, 1),   HexColor("#d1fae5")),   # green tint for done
        ("BACKGROUND",  (4, 0), (4, 1),   HexColor("#ede9fe")),   # violet tint for pct
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_SURFACE, C_SURFACE2]),
        ("BOX",         (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID",   (0, 0), (-1, -1), 0.3, C_BORDER),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    flows.append(tbl)
    flows.append(Spacer(1, 40))

    # Generated on date
    meta_style = ParagraphStyle(
        "cover_meta", fontName="Helvetica", fontSize=8.5,
        textColor=C_TEXT3, alignment=TA_LEFT
    )
    flows.append(Paragraph(f"Generato il {generated_on} con KanFlow", meta_style))
    flows.append(Spacer(1, 8))

    flows.append(
        HRFlowable(width="100%", thickness=0.5, color=C_BORDER,
                   spaceBefore=0, spaceAfter=0)
    )
    flows.append(PageBreak())
    return flows


# ── Public entry point ────────────────────────────────────────────────────────

def markdown_to_pdf(markdown_text: str, project_name: str, task_stats: dict) -> bytes:
    """
    Convert a Markdown string to a styled PDF.

    Args:
        markdown_text: Full documentation Markdown (including H1 title).
        project_name:  Used in header/footer and cover page.
        task_stats:    {"done": n, "in_progress": n, "todo": n}

    Returns:
        PDF bytes, ready to be served or written to disk.
    """
    from datetime import datetime
    generated_on = datetime.now().strftime("%d %B %Y, %H:%M")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T + 0.5 * cm,
        bottomMargin=MARGIN_B + 0.5 * cm,
        title=f"Documentazione – {project_name}",
        author="KanFlow",
    )

    page_decor = _PageDecor(project_name, generated_on)
    st         = _styles()

    # Build story
    all_flows = []

    # Cover page
    all_flows += _make_cover(project_name, generated_on, task_stats, st)

    # Parse and add Markdown content
    all_flows += _parse_markdown(markdown_text, st)

    doc.build(
        all_flows,
        onFirstPage=page_decor,
        onLaterPages=page_decor,
    )

    return buf.getvalue()
