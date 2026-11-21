"""
PDF export for NutriLens analyses.

Builds an A4 report that mirrors the on-screen results page: the same sections, status colours and
brand palette, laid out for print with running headers, page numbers and text that wraps instead
of being cut off.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
    TableStyle,
)

from app.engine.rule_engine import BIOMARKERS_CONFIG
from app.utils.pdf_text import LANG, L, font, lang as _lang

# ── Palette (the Tailwind values the website uses) ────────────────────────────
WHITE = colors.white
SLATE_50, SLATE_100, SLATE_200 = colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9"), colors.HexColor("#e2e8f0")
SLATE_300, SLATE_400, SLATE_500 = colors.HexColor("#cbd5e1"), colors.HexColor("#94a3b8"), colors.HexColor("#64748b")
SLATE_600, SLATE_700, SLATE_900 = colors.HexColor("#475569"), colors.HexColor("#334155"), colors.HexColor("#0f172a")
BRAND_50, BRAND_100, BRAND_200 = colors.HexColor("#effaf6"), colors.HexColor("#d7f3e8"), colors.HexColor("#b1e6d3")
BRAND_500, BRAND_600, BRAND_700 = colors.HexColor("#229a7c"), colors.HexColor("#167c64"), colors.HexColor("#136352")
BRAND_800 = colors.HexColor("#124f43")
EMERALD_400, EMERALD_500 = colors.HexColor("#34d399"), colors.HexColor("#10b981")
RED_50, RED_100, RED_200 = colors.HexColor("#fef2f2"), colors.HexColor("#fee2e2"), colors.HexColor("#fecaca")
RED_500, RED_700, RED_800 = colors.HexColor("#ef4444"), colors.HexColor("#b91c1c"), colors.HexColor("#991b1b")
AMBER_50, AMBER_200 = colors.HexColor("#fffbeb"), colors.HexColor("#fde68a")
AMBER_500, AMBER_700 = colors.HexColor("#f59e0b"), colors.HexColor("#b45309")
INDIGO_50, INDIGO_100, INDIGO_200 = colors.HexColor("#eef2ff"), colors.HexColor("#e0e7ff"), colors.HexColor("#c7d2fe")
INDIGO_500, INDIGO_700 = colors.HexColor("#6366f1"), colors.HexColor("#4338ca")

STATUS = {
    "low": {"label": "Low", "caption": "Needs attention", "text": RED_700, "fill": RED_500, "soft": RED_50, "ring": RED_200},
    "borderline": {"label": "Borderline", "caption": "Worth monitoring", "text": AMBER_700, "fill": AMBER_500,
                   "soft": AMBER_50, "ring": AMBER_200},
    "normal": {"label": "Optimal", "caption": "In healthy range", "text": BRAND_700, "fill": BRAND_500,
               "soft": BRAND_50, "ring": BRAND_200},
    "high": {"label": "Elevated", "caption": "Above healthy range", "text": INDIGO_700, "fill": INDIGO_500,
             "soft": INDIGO_50, "ring": INDIGO_200},
}
STATUS_ORDER = ("low", "borderline", "normal", "high")
DIET_LABEL = {"veg": "Vegetarian", "vegan": "Vegan", "eggetarian": "Eggetarian", "non_veg": "Non-vegetarian"}
IST = timezone(timedelta(hours=5, minutes=30))

PAGE_W, PAGE_H = A4
MARGIN_X = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X
FIRST_TOP, LATER_TOP, BOTTOM = 30 * mm, 21 * mm, 19 * mm


# ── Text helpers ──────────────────────────────────────────────────────────────
_REPLACEMENTS = {"μ": "µ", "≥": ">=", "≤": "<=", "→": "->", "←": "<-", "✓": "", "✔": "", "✗": "", "✘": "", "✦": ""}


def _clean(value: Any) -> str:
    """Plain text the built-in PDF fonts can draw (anything else is transliterated or dropped)."""
    text = "" if value is None else str(value)
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    if _lang() != "en":
        return text.strip()  # the Noto fonts draw the Indian scripts and these symbols
    out = []
    for ch in text:
        try:
            ch.encode("cp1252")
            out.append(ch)
        except UnicodeEncodeError:
            out.append(unicodedata.normalize("NFKD", ch).encode("cp1252", "ignore").decode("cp1252"))
    return "".join(out).strip()


def _t(value: Any) -> str:
    """Escaped text for Paragraph markup."""
    return escape(_clean(value))


def _md(value: Any) -> str:
    """Escaped text with Markdown **bold** and *italic* turned into Paragraph markup."""
    text = _t(value)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)


def _num(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _clean(value)
    if number != number:  # NaN
        return "-"
    text = f"{number:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


_UNIT_CASE = {"MG": "mg", "MCG": "mcg", "UG": "mcg", "µG": "mcg", "G": "g", "IU": "IU", "KCAL": "kcal"}


def _amount(text: Any) -> str:
    """'10.0 MG' -> '10 mg'; anything unexpected is returned as-is."""
    cleaned = _clean(text)
    match = re.fullmatch(r"([\d.]+)\s*([A-Za-zµ]+)", cleaned)
    if not match:
        return cleaned
    return f"{_num(match.group(1))} {_UNIT_CASE.get(match.group(2).upper(), match.group(2))}"


def _nutrient_name(key: Any) -> str:
    if _clean(key) in ("glycemic_support", "lipid_support", "hdl_support", ""):
        return ""  # these plans are ranked by food properties, not by one nutrient
    base = re.sub(r"_(mg|mcg|ug|iu|g)$", "", _clean(key), flags=re.I).replace("_", " ").strip()
    return base.title() if base else ""


def _report_time(timestamp: Any) -> str:
    try:
        moment = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(IST)
    if _lang() != "en":
        return f"{local.day}.{local.month}.{local.year}, {local.strftime('%H:%M')} IST"
    hour = local.strftime("%I").lstrip("0") or "12"
    return f"{local.day} {local.strftime('%b %Y')}, {hour}:{local.strftime('%M')} {local.strftime('%p').lower()} IST"


def _width(text: str, fontname: str, size: float) -> float:
    """Width of text as drawn (shaped in Hindi and Telugu, where letters join)."""
    if _lang() == "en":
        return stringWidth(text, fontname, size)
    from reportlab.pdfgen.textobject import bidiShapedText
    return bidiShapedText(text, None, fontName=font(fontname), fontSize=size, shaping=True)[1]


def _spaced(c, x: float, y: float, text: str, fontname: str, size: float, space: float, *, right: bool = False) -> None:
    """Letter-spaced capitals in English; plain text in Hindi and Telugu (spacing would break joined letters)."""
    if _lang() != "en":
        c.setFont(fontname, size)
        (c.drawRightString if right else c.drawString)(x, y, text)
        return
    width = stringWidth(text, fontname, size) + space * (len(text) - 1)
    obj = c.beginText(x - width if right else x, y)
    obj.setFont(fontname, size)
    obj.setCharSpace(space)
    obj.textOut(text)
    obj.setCharSpace(0)  # character spacing would otherwise carry over to the next text drawn
    c.drawText(obj)


def _tr(text: Any) -> str:
    """An analysis text (category, explanation note) in the PDF's language."""
    from app.i18n import tr
    return tr(text, _lang()) if text else ""


def _hex(color: colors.Color) -> str:
    return color.hexval().replace("0x", "#")


def _style(name: str, size: float, color: colors.Color, *, font: str = "Helvetica", leading: Optional[float] = None,
           align: int = 0, **extra: Any) -> ParagraphStyle:
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading or size * 1.35,
                          textColor=color, alignment=align, **extra)


class _Styles(dict):
    """The paragraph styles; in Hindi or Telugu the same styles with the Noto font, shaping and a little more leading."""

    _local: dict = {}

    def __getitem__(self, key):
        style = super().__getitem__(key)
        current = _lang()
        if current == "en":
            return style
        if (key, current) not in self._local:
            self._local[key, current] = ParagraphStyle(f"{style.name}_{current}", parent=style,
                                                       fontName=font(style.fontName), leading=style.leading * 1.18,
                                                       shaping=1)
        return self._local[key, current]


ST = _Styles({
    "title": _style("title", 19, SLATE_900, font="Helvetica-Bold", leading=23),
    "subtitle": _style("subtitle", 9.5, SLATE_500, leading=13),
    "h2": _style("h2", 12.5, SLATE_900, font="Helvetica-Bold", leading=15),
    "h2_sub": _style("h2_sub", 8, SLATE_500, leading=11),
    "eyebrow": _style("eyebrow", 6.6, BRAND_700, font="Helvetica-Bold", leading=8.5),
    "label": _style("label", 6.5, SLATE_500, font="Helvetica-Bold", leading=8.5),
    "value": _style("value", 9.2, SLATE_900, font="Helvetica-Bold", leading=11.5),
    "tile_label": _style("tile_label", 8, SLATE_600, leading=10),
    "tile_value": _style("tile_value", 21, SLATE_900, font="Helvetica-Bold", leading=24),
    "tile_caption": _style("tile_caption", 7, SLATE_500, leading=9),
    "card_title": _style("card_title", 9.5, SLATE_900, font="Helvetica-Bold", leading=12),
    "small": _style("small", 7.4, SLATE_500, leading=10),
    "small_right": _style("small_right", 7.4, SLATE_500, leading=10, align=TA_RIGHT),
    "body": _style("body", 8.6, SLATE_700, leading=12.4),
    "mono": _style("mono", 7.4, SLATE_500, font="Courier", leading=10),
    "food_name": _style("food_name", 9, SLATE_900, font="Helvetica-Bold", leading=11.5),
    "food_local": _style("food_local", 7.4, SLATE_500, leading=9.6),
    "nutrient_value": _style("nutrient_value", 10, BRAND_700, font="Helvetica-Bold", leading=12),
    "nutrient_caption": _style("nutrient_caption", 7, BRAND_700, leading=9),
    "food_tip": _style("food_tip", 7.7, SLATE_600, leading=10.6),
    "food_fact": _style("food_fact", 7.2, BRAND_700, font="Helvetica-Oblique", leading=9.8),
    "warn_title": _style("warn_title", 9.5, RED_800, font="Helvetica-Bold", leading=12),
    "warn_body": _style("warn_body", 8.2, RED_800, leading=11.4),
    "warn_small": _style("warn_small", 7.6, RED_700, leading=10.4),
    "do_title": _style("do_title", 8.4, BRAND_800, font="Helvetica-Bold", leading=11),
    "dont_title": _style("dont_title", 8.4, RED_800, font="Helvetica-Bold", leading=11),
    "do_item": _style("do_item", 7.8, SLATE_700, leading=10.8, leftIndent=9, bulletIndent=0),
    "warn_item": _style("warn_item", 8, RED_800, leading=11, leftIndent=9, bulletIndent=0),
    "disclaimer": _style("disclaimer", 7, SLATE_500, font="Helvetica-Oblique", leading=10),
    "table_head": _style("table_head", 6.6, SLATE_500, font="Helvetica-Bold", leading=8.5),
    "cell": _style("cell", 8, SLATE_700, leading=10.6),
    "cell_bold": _style("cell_bold", 8.2, SLATE_900, font="Helvetica-Bold", leading=10.6),
    "cell_small": _style("cell_small", 6.9, SLATE_500, leading=9),
    "group": _style("group", 7.4, BRAND_800, font="Helvetica-Bold", leading=9.5),
    "plan_title": _style("plan_title", 10.5, SLATE_900, font="Helvetica-Bold", leading=13),
    "count": _style("count", 17, SLATE_900, font="Helvetica-Bold", leading=19),
})


# ── Drawing building blocks ───────────────────────────────────────────────────
def _draw_logo(c: rl_canvas.Canvas, x: float, y: float, size: float, *, fill=BRAND_600, ink=WHITE) -> None:
    """The NutriLens mark: a rounded tile with a leaf outline."""
    c.saveState()
    c.setFillColor(fill)
    c.roundRect(x, y, size, size, size * 0.26, stroke=0, fill=1)
    c.translate(x + size / 2, y + size / 2)
    c.rotate(40)
    c.setStrokeColor(ink)
    c.setLineWidth(max(0.8, size * 0.075))
    c.ellipse(-size * 0.27, -size * 0.14, size * 0.27, size * 0.14, stroke=1, fill=0)
    c.line(-size * 0.34, 0, size * 0.16, 0)
    c.restoreState()


class Box(Flowable):
    """A rounded card that stacks flowables vertically (optionally with a coloured top edge)."""

    def __init__(self, content, *, fill=WHITE, stroke=SLATE_200, radius=7.0, pad_x=11.0, pad_y=10.0,
                 accent=None, min_height=0.0, stroke_width=0.8):
        super().__init__()
        self.content = [item for item in content if item is not None]
        self.fill, self.stroke, self.radius = fill, stroke, radius
        self.pad_x, self.pad_y, self.accent = pad_x, pad_y, accent
        self.min_height, self.stroke_width = min_height, stroke_width

    def natural_height(self, avail_w: float) -> float:
        inner = avail_w - 2 * self.pad_x
        self._sizes = [item.wrap(inner, PAGE_H) for item in self.content]
        top = 2.5 if self.accent else 0
        return sum(h for _, h in self._sizes) + 2 * self.pad_y + top

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        self.height = max(self.min_height, self.natural_height(avail_w))
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        if self.fill is not None or self.stroke is not None:
            c.setFillColor(self.fill or WHITE)
            c.setStrokeColor(self.stroke or self.fill)
            c.setLineWidth(self.stroke_width)
            c.roundRect(0, 0, self.width, self.height, self.radius,
                        stroke=1 if self.stroke else 0, fill=1 if self.fill is not None else 0)
        if self.accent:
            clip = c.beginPath()
            clip.roundRect(0, 0, self.width, self.height, self.radius)
            c.clipPath(clip, stroke=0, fill=0)
            c.setFillColor(self.accent)
            c.rect(0, self.height - 3, self.width, 3, stroke=0, fill=1)
        c.restoreState()
        y = self.height - self.pad_y - (2.5 if self.accent else 0)
        for item, (_, h) in zip(self.content, self._sizes):
            y -= h
            item.drawOn(c, self.pad_x, y)


class Row(Flowable):
    """Flowables side by side. Each item is (flowable, width, align): width is a fraction of the row,
    'auto' (the flowable's own width) or None (share what's left)."""

    def __init__(self, items, *, gap=8.0, valign="top", equal_height=False):
        super().__init__()
        self.items = [(f, w, a) for f, w, a in items if f is not None]
        self.gap, self.valign, self.equal_height = gap, valign, equal_height

    def wrap(self, avail_w, avail_h):
        usable = avail_w - self.gap * (len(self.items) - 1)
        widths = []
        for flowable, spec, _ in self.items:
            if spec == "auto":
                widths.append(flowable.wrap(usable, avail_h)[0])
            elif isinstance(spec, (int, float)):
                widths.append(usable * spec)
            else:
                widths.append(None)
        flex = [i for i, w in enumerate(widths) if w is None]
        if flex:
            share = max(0.0, (usable - sum(w for w in widths if w is not None)) / len(flex))
            for i in flex:
                widths[i] = share
        boxes = [(f, w) for (f, _, _), w in zip(self.items, widths) if isinstance(f, Box)]
        if self.equal_height and boxes:
            tallest = max(f.natural_height(w) for f, w in boxes)
            for f, _ in boxes:
                f.min_height = tallest
        self._widths = widths
        self._sizes = [f.wrap(w, avail_h) for (f, _, _), w in zip(self.items, widths)]
        self.width, self.height = avail_w, max(h for _, h in self._sizes)
        return self.width, self.height

    def draw(self):
        x = 0.0
        for (flowable, _, align), width, (fw, fh) in zip(self.items, self._widths, self._sizes):
            dx = width - fw if align == "right" else 0
            if self.valign == "middle":
                dy = (self.height - fh) / 2
            elif self.valign == "bottom":
                dy = 0
            else:
                dy = self.height - fh
            flowable.drawOn(self.canv, x + dx, dy)
            x += width + self.gap


class Pill(Flowable):
    """A rounded status label, optionally with a coloured dot."""

    def __init__(self, text, fg, bg, ring=None, *, size=6.8, dot=True):
        super().__init__()
        self.text, self.fg, self.bg, self.ring, self.size, self.dot = _clean(text), fg, bg, ring, size, dot
        self.pad = 5.0
        self.width = _width(self.text, "Helvetica-Bold", size) + 2 * self.pad + (6.5 if dot else 0)
        self.height = size + 6

    def wrap(self, avail_w, avail_h):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.setStrokeColor(self.ring or self.bg)
        c.setLineWidth(0.6)
        c.roundRect(0, 0, self.width, self.height, self.height / 2, stroke=1 if self.ring else 0, fill=1)
        x = self.pad
        if self.dot:
            c.setFillColor(self.fg)
            c.circle(x + 1.8, self.height / 2, 1.8, stroke=0, fill=1)
            x += 6.5
        c.setFillColor(self.fg)
        c.setFont("Helvetica-Bold", self.size)
        c.drawString(x, (self.height - self.size * 0.7) / 2, self.text)


class RangeBar(Flowable):
    """The website's range slider: below / healthy / above zones with a marker at the value."""

    def __init__(self, value, low, high, status):
        super().__init__()
        self.value, self.low, self.high = float(value or 0), float(low or 0), float(high or 0)
        self.color = STATUS.get(status, STATUS["normal"])["fill"]

    def wrap(self, avail_w, avail_h):
        self.width, self.height = avail_w, 21
        return self.width, self.height

    def draw(self):
        c, w = self.canv, self.width
        vmin = max(0.0, self.low * 0.4)
        vmax = max(self.high, self.low, self.value) * 1.35 or 1.0
        span = (vmax - vmin) or 1.0

        def at(v: float) -> float:
            return max(0.0, min(1.0, (v - vmin) / span)) * w

        track_y, track_h = 11.0, 4.0
        low_x, high_x = at(self.low), at(self.high)
        c.saveState()
        clip = c.beginPath()
        clip.roundRect(0, track_y, w, track_h, track_h / 2)
        c.clipPath(clip, stroke=0, fill=0)
        for x0, x1, color in ((0, low_x, RED_100), (low_x, high_x, BRAND_200), (high_x, w, INDIGO_100)):
            c.setFillColor(color)
            c.rect(x0, track_y, max(0.0, x1 - x0), track_h, stroke=0, fill=1)
        c.restoreState()

        c.setFont("Helvetica", 6.4)
        c.setFillColor(SLATE_400)
        c.drawCentredString(min(max(low_x, 8), w - 8), 1.5, _num(self.low))
        if high_x - low_x > 22:
            c.drawCentredString(min(max(high_x, 8), w - 8), 1.5, _num(self.high))

        c.setFillColor(self.color)
        c.setStrokeColor(WHITE)
        c.setLineWidth(1.4)
        c.circle(min(max(at(self.value), 4.5), w - 4.5), track_y + track_h / 2, 4.2, stroke=1, fill=1)


class ScoreCard(Flowable):
    """Dark 'Biomarker Homeostasis Score' banner with the multi-segment bar."""

    def __init__(self, counts: dict[str, int], total: int):
        super().__init__()
        self.counts, self.total = counts, max(total, 1)

    def wrap(self, avail_w, avail_h):
        self.width, self.height = avail_w, 84
        return self.width, self.height

    def draw(self):
        c, w, h = self.canv, self.width, self.height
        optimal = self.counts.get("normal", 0)
        flagged = self.total - optimal
        c.setFillColor(WHITE)  # light card, as on the website
        c.setStrokeColor(SLATE_200)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, w, h, 9, stroke=1, fill=1)

        c.setFillColor(BRAND_700)
        _spaced(c, 16, h - 20, L("HEALTH SCORE"), "Helvetica-Bold", 6.8, 0.9)

        c.setFillColor(SLATE_900)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(16, h - 39, L("{a} of {n} results in range", a=optimal, n=self.total))
        c.setFillColor(SLATE_600)
        c.setFont("Helvetica", 8)
        if flagged == 0:
            note = L("All tested laboratory biomarkers are balanced within reference intervals.")
        else:
            note = L("{n} need attention; see the plan below." if flagged > 1 else "{n} needs attention; see the plan below.",
                     n=flagged)
        c.drawString(16, h - 52, note)

        c.setFillColor(BRAND_600)
        c.setFont("Helvetica-Bold", 22)
        c.drawRightString(w - 16, h - 40, f"{round(optimal / self.total * 100)}%")
        c.setFillColor(SLATE_400)
        _spaced(c, w - 16, h - 52, L("OPTIMAL INDEX"), "Helvetica", 6.5, 0.7, right=True)

        bar_x, bar_y, bar_w, bar_h = 16, 15, w - 32, 6
        c.saveState()
        clip = c.beginPath()
        clip.roundRect(bar_x, bar_y, bar_w, bar_h, bar_h / 2)
        c.clipPath(clip, stroke=0, fill=0)
        c.setFillColor(SLATE_100)
        c.rect(bar_x, bar_y, bar_w, bar_h, stroke=0, fill=1)
        x = bar_x
        for status, color in (("normal", EMERALD_500), ("borderline", AMBER_500), ("low", RED_500), ("high", INDIGO_500)):
            width = bar_w * self.counts.get(status, 0) / self.total
            c.setFillColor(color)
            c.rect(x, bar_y, width, bar_h, stroke=0, fill=1)
            x += width
        c.restoreState()


class SectionTitle(Flowable):
    """Section heading with the brand mark, matching the website's section headers."""

    def __init__(self, title: str, subtitle: Optional[str] = None):
        super().__init__()
        self.title = Paragraph(_t(title), ST["h2"])
        self.subtitle = Paragraph(_t(subtitle), ST["h2_sub"]) if subtitle else None

    def wrap(self, avail_w, avail_h):
        inner = avail_w - 26
        self._title_h = self.title.wrap(inner, avail_h)[1]
        self._sub_h = self.subtitle.wrap(inner, avail_h)[1] if self.subtitle else 0
        self.width, self.height = avail_w, max(20, self._title_h + self._sub_h + 1)
        return self.width, self.height

    def draw(self):
        c = self.canv
        _draw_logo(c, 0, self.height - 19, 19, fill=BRAND_50, ink=BRAND_600)
        c.setStrokeColor(BRAND_100)
        c.setLineWidth(0.6)
        c.roundRect(0, self.height - 19, 19, 19, 19 * 0.26, stroke=1, fill=0)
        self.title.drawOn(c, 26, self.height - self._title_h)
        if self.subtitle:
            self.subtitle.drawOn(c, 26, self.height - self._title_h - self._sub_h - 1)


def _stack(*items):
    """Several flowables as one block with no frame (a borderless Box)."""
    return Box(list(items), fill=None, stroke=None, radius=0, pad_x=0, pad_y=0)


def _bullets(items, style) -> list:
    return [Paragraph(_md(item), style, bulletText="•") for item in items if _clean(item)]


def _grid(cards: list, gap: float = 8.0) -> list:
    """Two-column grid of cards with equal heights per row; page breaks fall between rows."""
    rows = []
    for i in range(0, len(cards), 2):
        pair = cards[i:i + 2]
        items = [(card, 0.5, "left") for card in pair]
        if len(pair) == 1:
            items.append((Spacer(1, 1), 0.5, "left"))
        rows.append(Row(items, gap=gap, equal_height=True))
        rows.append(Spacer(1, gap))
    return rows[:-1]


# ── Report sections ───────────────────────────────────────────────────────────


class MiniBar(Flowable):
    """A slim range bar for table rows: below / healthy / above zones and a dot at the value."""

    def __init__(self, value, low, high, status):
        super().__init__()
        self.value, self.low, self.high = float(value or 0), float(low or 0), float(high or 0)
        self.color = STATUS.get(status, STATUS["normal"])["fill"]

    def wrap(self, avail_w, avail_h):
        self.width, self.height = avail_w, 9
        return self.width, self.height

    def draw(self):
        c, w = self.canv, self.width
        vmin = max(0.0, self.low * 0.4)
        vmax = max(self.high, self.low, self.value) * 1.35 or 1.0
        at = lambda v: max(0.0, min(1.0, (v - vmin) / ((vmax - vmin) or 1.0))) * w
        low_x, high_x = at(self.low), at(self.high)
        c.saveState()
        clip = c.beginPath()
        clip.roundRect(0, 2.5, w, 4, 2)
        c.clipPath(clip, stroke=0, fill=0)
        for x0, x1, color in ((0, low_x, RED_100), (low_x, high_x, BRAND_200), (high_x, w, INDIGO_100)):
            c.setFillColor(color)
            c.rect(x0, 2.5, max(0.0, x1 - x0), 4, stroke=0, fill=1)
        c.restoreState()
        c.setFillColor(self.color)
        c.setStrokeColor(WHITE)
        c.setLineWidth(1.1)
        c.circle(min(max(at(self.value), 3.6), w - 3.6), 4.5, 3.4, stroke=1, fill=1)


def _table(rows: list, widths: list[float], *, head: bool = True, zebra: bool = False, extra: Optional[list] = None) -> Table:
    """A clean report table: light header, hairline row rules, generous padding, rows never split."""
    table = Table(rows, colWidths=[CONTENT_W * w for w in widths], repeatRows=1 if head else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, SLATE_200),
    ]
    if head:
        style += [("BACKGROUND", (0, 0), (-1, 0), SLATE_50), ("LINEABOVE", (0, 0), (-1, 0), 0.5, SLATE_200),
                  ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 4)]
    if zebra:
        style.append(("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [WHITE, SLATE_50]))
    table.setStyle(TableStyle(style + (extra or [])))
    return table


def _status_pill(status: Any) -> Pill:
    meta = STATUS.get(status, STATUS["normal"])
    return Pill(L(meta["label"]), meta["text"], meta["soft"], meta["ring"])


def _range_text(marker: dict) -> str:
    lab_low = marker.get("lab_range_low")
    lab_high = marker.get("lab_range_high")
    low = lab_low if lab_low is not None else marker.get("range_low")
    high = lab_high if lab_high is not None else marker.get("range_high")
    unit = _clean(marker.get("unit"))
    if not float(low or 0):
        base = L("Up to {x}", x=f"{_num(high)} {unit}".strip())
    else:
        base = f"{_num(low)} – {_num(high)} {unit}".strip()
    gt = marker.get("guideline_threshold")
    if gt:
        base = L("{x} (Guideline: {y})", x=base, y=gt)
    return base


def _result_cell(marker: dict) -> Paragraph:
    return Paragraph(f'<font name="{font("Helvetica-Bold")}" size="9" color="{_hex(SLATE_900)}">{_num(marker.get("value"))}</font>'
                     f'&nbsp;<font size="7" color="{_hex(SLATE_500)}">{_t(marker.get("unit"))}</font>', ST["cell"])


def _short(name: Any) -> str:
    return " ".join(re.sub(r"\s*\([^)]*\)", "", _clean(name)).split())


def _profile_strip(profile: dict) -> Box:
    allergens = [L(_clean(a).title()) for a in profile.get("allergens") or [] if _clean(a)]
    facts = [
        ("AGE", L("{n} years", n=_num(profile.get("age"))) if profile.get("age") is not None else "-"),
        ("SEX", L(_clean(profile.get("gender")).title()) or "-"),
        ("DIET", L(DIET_LABEL.get(profile.get("diet_type"),
                                  _clean(profile.get("diet_type")).replace("_", " ").title() or "-"))),
        ("FOODS EXCLUDED", ", ".join(allergens) if allergens else L("None")),
    ]
    cells = [(_stack(Paragraph(L(label), ST["label"]), Spacer(1, 2), Paragraph(_t(value), ST["value"])), None, "left")
             for label, value in facts]
    return Box([Row(cells, gap=10)], fill=SLATE_50, radius=6, pad_y=8)


def _summary(counts: dict[str, int], total: int) -> Row:
    """Score banner beside four compact status counts."""
    tiles = []
    for status in STATUS_ORDER:
        meta = STATUS[status]
        tiles.append(Box([Paragraph(L(meta["label"]).upper(), ST["label"]), Spacer(1, 2),
                          Paragraph(f'<font color="{_hex(meta["text"])}">{counts.get(status, 0)}</font>',
                                    ST["count"])],
                         accent=meta["fill"], pad_x=9, pad_y=7))
    grid = _stack(Row([(tiles[0], None, "left"), (tiles[1], None, "left")], gap=6, equal_height=True), Spacer(1, 6),
                  Row([(tiles[2], None, "left"), (tiles[3], None, "left")], gap=6, equal_height=True))
    return Row([(ScoreCard(counts, total), 0.62, "left"), (grid, None, "left")], gap=8)


def _safety_warning(reasons: list) -> Box:
    return Box([
        Paragraph(L("Please review these results with a doctor"), ST["warn_title"]),
        Spacer(1, 3),
        Paragraph(L("Food changes can support your health, but the following results need medical advice:"), ST["warn_body"]),
        Spacer(1, 4),
        *_bullets(list(dict.fromkeys(reasons)), ST["warn_item"]),
    ], fill=RED_50, stroke=RED_200, pad_y=10)


def _plan_note(marker: dict, improve_plans: list[dict], doctor_only: set) -> str:
    if marker.get("biomarker_key") in doctor_only:
        return "Doctor review"
    name = _short(marker.get("display_name"))
    for plan in improve_plans:
        if plan.get("target_biomarker") == marker.get("biomarker_key") or name in _short(plan.get("biomarker_display_name")):
            return "Food plan" + (" + doctor" if _clean(marker.get("clinical_warning")) else "")
    return "Monitor"


def _at_a_glance(flagged: list[dict], improve_plans: list[dict], doctor_only: set) -> list:
    rows = [[Paragraph(L(h), ST["table_head"]) for h in ("TEST", "YOUR RESULT", "HEALTHY RANGE", "STATUS", "WHAT NEXT")]]
    for m in flagged:
        rows.append([Paragraph(_t(m.get("display_name")), ST["cell_bold"]), _result_cell(m), Paragraph(_t(_range_text(m)), ST["cell"]),
                     _status_pill(m.get("status")), Paragraph(_t(L(_plan_note(m, improve_plans, doctor_only))), ST["cell"])])
    return [KeepTogether([SectionTitle(L("Results That Need Attention"),
                                       L("{n} of your results are outside the healthy range.", n=len(flagged))),
                          Spacer(1, 8), _table(rows, [0.32, 0.17, 0.21, 0.14, 0.16])])]


def _all_results(markers: list[dict]) -> list:
    groups: dict[str, list[dict]] = {}
    for m in markers:
        category = BIOMARKERS_CONFIG.get(m.get("biomarker_key"), {}).get("category") or "Other Tests"
        groups.setdefault(category, []).append(m)
    head = [Paragraph(L(h), ST["table_head"]) for h in ("TEST", "RESULT", "HEALTHY RANGE", "STATUS", "POSITION IN RANGE")]
    rows, extra = [head], []
    for category, items in groups.items():
        extra += [("SPAN", (0, len(rows)), (-1, len(rows))), ("BACKGROUND", (0, len(rows)), (-1, len(rows)), BRAND_50),
                  ("TOPPADDING", (0, len(rows)), (-1, len(rows)), 4), ("BOTTOMPADDING", (0, len(rows)), (-1, len(rows)), 4)]
        rows.append([Paragraph(_t(_tr(category) or L(category)).upper(), ST["group"]), "", "", "", ""])
        for m in items:
            rows.append([Paragraph(_t(m.get("display_name")), ST["cell"]), _result_cell(m), Paragraph(_t(_range_text(m)), ST["cell"]),
                         _status_pill(m.get("status")),
                         MiniBar(m.get("value"), m.get("range_low"), m.get("range_high"), m.get("status"))])
    table = _table(rows, [0.33, 0.15, 0.2, 0.13, 0.19], extra=extra)
    return [SectionTitle(L("All Test Results"), L("Grouped by panel and compared with the report's reference ranges or "
                                                  "clinical guidelines.")), Spacer(1, 8), table]


def _food_cell(food: dict) -> list:
    parts = [Paragraph(_t(food.get("name")), ST["cell_bold"])]
    local = _clean(food.get("hindi_name")) if _lang() == "en" else ""  # romanised; the name is already translated
    sub = " · ".join(p for p in (local, _clean(food.get("category"))) if p)
    if sub:
        parts.append(Paragraph(_t(sub), ST["cell_small"]))
    return parts


def _provides(food: dict, nutrient: str) -> Paragraph:
    amount = _amount(food.get("key_nutrient_yield"))
    if re.search(r"\d", amount):
        text = f'<font name="{font("Helvetica-Bold")}" color="{_hex(BRAND_700)}">{_t(amount)}</font>'
        if nutrient:
            text += f'<br/><font size="6.9" color="{_hex(SLATE_500)}">{_t(nutrient)}</font>'
        return Paragraph(text, ST["cell"])
    return Paragraph(f'<font color="{_hex(BRAND_700)}"><b>{_t(amount)}</b></font>', ST["cell"])


def _dos_and_donts(dos: list, donts: list) -> Optional[Row]:
    panels = []
    if [d for d in dos if _clean(d)]:
        panels.append((Box([Paragraph(L("Helpful habits"), ST["do_title"]), Spacer(1, 4), *_bullets(dos, ST["do_item"])],
                           fill=BRAND_50, stroke=BRAND_200, pad_y=9), None, "left"))
    if [d for d in donts if _clean(d)]:
        panels.append((Box([Paragraph(L("Limit or avoid"), ST["dont_title"]), Spacer(1, 4), *_bullets(donts, ST["do_item"])],
                           fill=RED_50, stroke=RED_200, pad_y=9), None, "left"))
    return Row(panels, gap=8, equal_height=True) if panels else None


def _food_plan(plan: dict, markers_by_key: dict[str, dict], number: int) -> list:
    status = plan.get("status") if plan.get("status") in STATUS else "low"
    marker = markers_by_key.get(plan.get("target_biomarker"), {})
    nutrient = L(_nutrient_name(marker.get("target_nutrient_key")))
    title = Row([
        (Paragraph(f'<font color="{_hex(BRAND_700)}">{number}.</font>&nbsp; ' + L("For {name}", name=_t(plan.get("biomarker_display_name"))),
                   ST["plan_title"]), None, "left"),
        (_status_pill(status), "auto", "right"),
    ], gap=8, valign="middle")
    foods = plan.get("recommended_foods") or []
    if foods:
        rows = [[Paragraph(L(h), ST["table_head"]) for h in ("FOOD", "SERVING", "PROVIDES", "HOW TO EAT IT")]]
        for food in foods:
            rows.append([_food_cell(food), Paragraph(_t(food.get("serving_size")), ST["cell"]), _provides(food, nutrient),
                         Paragraph(_md(food.get("preparation_tip")), ST["cell"])])
        body = _table(rows, [0.31, 0.18, 0.15, 0.36], extra=[("VALIGN", (0, 1), (-1, -1), "TOP")])
    else:
        body = Paragraph(L("No foods matched your diet and allergen settings for this result. "
                           "Please ask a dietitian for suitable alternatives."), ST["body"])
    advice = _dos_and_donts(plan.get("absorption_dos") or [], plan.get("absorption_donts") or [])
    # A plan (title, foods and habits) stays on one page so its advice is never separated from its foods.
    return [KeepTogether([title, Spacer(1, 6), body, *([Spacer(1, 7), advice] if advice else [])]), Spacer(1, 16)]


def _maintain(plans: list[dict]) -> list:
    rows = [[Paragraph(L(h), ST["table_head"]) for h in ("RESULT", "FOODS TO INCLUDE REGULARLY", "TIP")]]
    for plan in plans:
        foods = ", ".join(_clean(f.get("name")) for f in plan.get("recommended_foods") or [])
        tip = (plan.get("absorption_dos") or [""])[0]
        rows.append([Paragraph(_t(_short(plan.get("biomarker_display_name"))), ST["cell_bold"]), Paragraph(_t(foods), ST["cell"]),
                     Paragraph(_md(tip), ST["cell_small"])])
    return [KeepTogether([SectionTitle(L("Keep Your Healthy Results Healthy"),
                                       L("These results are within range. Including these foods regularly helps keep them there.")),
                          Spacer(1, 8), _table(rows, [0.24, 0.4, 0.36], extra=[("VALIGN", (0, 1), (-1, -1), "TOP")])]),
            Spacer(1, 16)]


STYLE_NAMES = {"familiar": "Familiar", "nutritious": "Most nutritious", "regional": "Regional"}
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _diet_plan(plan: dict) -> list:
    """The 7-day diet plan chosen on the results page: one row per day, one column per meal, then the shopping list."""
    from app.utils.diet_plan_pdf import localize_words, portion
    from app.plan.ingredient_local import NAMES

    current = _lang()
    days = [d for d in plan.get("days") or [] if isinstance(d, dict)][:7]
    if not days:
        return []

    def dishes(items: list) -> Paragraph:
        lines = []
        for item in items or []:
            name = ((item.get("names") or {}).get(current) if current != "en" else None) or item.get("name", "")
            amount = localize_words(portion(item.get("servings", 1), str(item.get("serving", ""))), current)
            lines.append(f'<b>{_t(name)}</b><br/><font size="6.6" color="{_hex(SLATE_500)}">{_t(amount)}</font>')
        return Paragraph("<br/>".join(lines) or "-", ST["cell_small"])

    rows = [[Paragraph(L(h), ST["table_head"]) for h in ("DAY", "BREAKFAST", "LUNCH", "EVENING SNACK", "DINNER")]]
    for i, day in enumerate(days):
        meals = day.get("meals") or {}
        kcal = round((day.get("totals") or {}).get("energy_kcal", 0))
        rows.append([Paragraph(f'{_t(L(DAYS[i]))}<br/><font size="6.6" color="{_hex(SLATE_500)}">{kcal} kcal</font>',
                               ST["cell_bold"]),
                     *[dishes(meals.get(slot)) for slot in ("breakfast", "lunch", "snack", "dinner")]])
    style = L(STYLE_NAMES.get(plan.get("style"), "Familiar"))
    story = [SectionTitle(L("Your 7-day diet plan"), L("Plan style: {style}. Amounts are per person and each day is built "
                                                       "for your calorie, protein and nutrient targets.", style=style)),
             Spacer(1, 8),
             _table(rows, [0.12, 0.2, 0.28, 0.16, 0.24], zebra=True, extra=[("VALIGN", (0, 1), (-1, -1), "TOP")]),
             Spacer(1, 12)]
    items = [i for i in plan.get("shopping_list") or [] if isinstance(i, dict) and i.get("buy_g", 0) >= 5]
    if items:
        def label(item: dict) -> str:
            name = item.get("name", "")
            if current != "en":
                name = (item.get("names") or {}).get(current) or NAMES.get(name, (name, name))[current == "te"]
            grams = item.get("buy_g", 0)
            weight = f"{round(grams / 1000, 1)} kg" if grams >= 1000 else f"{-(-grams // 10) * 10} g"
            return f"{_t(name[:1].upper() + name[1:])}: {weight}"

        cells = [Paragraph(label(i), ST["cell"]) for i in items]
        grid = [cells[j:j + 4] + [""] * (4 - len(cells[j:j + 4])) for j in range(0, len(cells), 4)]
        story += [KeepTogether([Paragraph(L("Shopping list for the week"), ST["card_title"]), Spacer(1, 2),
                                Paragraph(L("Weights as bought, before peeling and cleaning."), ST["small"]), Spacer(1, 6),
                                _table(grid, [0.25] * 4, head=False)])]
    return story + [Spacer(1, 16)]


def _explanation_parts(explanation: str) -> dict[str, dict[str, str]]:
    """Per-marker notes ('Biological Role', 'Clinical Relevance') from the Markdown explanation."""
    impact, section, current = {}, "", None
    for raw in (explanation or "").splitlines():
        line = raw.rstrip()
        heading = re.match(r"^#{2,4}\s+(.*)", line)
        if heading:
            section, current = heading.group(1).strip().lower(), None
            continue
        if "physiological" in section:
            item = re.match(r"^-\s+\*\*(.+?)\*\*", line)
            sub = re.match(r"^\s+-\s+\*(.+?):\*\s*(.*)", line)
            if item:
                name = re.sub(r"\s*\([^()]*\)\s*$", "", item.group(1)).strip().lower()
                current = impact.setdefault(name, {})
            elif sub and current is not None:
                current[sub.group(1).strip().lower()] = sub.group(2).strip()
    return impact


def _meanings(flagged: list[dict], notes: dict[str, dict[str, str]]) -> list:
    """notes: per biomarker key, from the English explanation (its headings are what the parser reads)."""
    rows = [[Paragraph(L(h), ST["table_head"]) for h in ("TEST", "WHAT IT DOES", "WHAT YOUR RESULT MAY MEAN")]]
    for m in flagged:
        note = notes.get(m.get("biomarker_key"), {})
        role, meaning = _tr(note.get("biological role", "")), _tr(note.get("clinical relevance", ""))
        if not (role or meaning):
            continue
        rows.append([Paragraph(_t(m.get("display_name")), ST["cell_bold"]), Paragraph(_md(role), ST["cell"]),
                     Paragraph(_md(meaning), ST["cell"])])
    if len(rows) == 1:
        return []
    return [SectionTitle(L("What Your Results Mean"), L("Plain-language notes for the results outside the healthy range.")),
            Spacer(1, 8), _table(rows, [0.24, 0.33, 0.43], extra=[("VALIGN", (0, 1), (-1, -1), "TOP")]), Spacer(1, 16)]


def _closing(flagged: bool) -> list:
    story = []
    if flagged:
        story += [Box([Row([
            (_stack(Paragraph(L("Follow-up"), ST["card_title"]), Spacer(1, 2),
                    Paragraph(L("Follow the food plan consistently for 8 to 12 weeks, then repeat the tests that were "
                                "outside the healthy range, or earlier if your doctor advises."), ST["small"])), None, "left"),
            (Pill(L("Retest in 8–12 weeks"), BRAND_700, BRAND_50, BRAND_200, size=7, dot=False), "auto", "right"),
        ], gap=10, valign="middle")], fill=SLATE_50, pad_y=10), Spacer(1, 10)]
    story.append(Paragraph(L(
        "Disclaimer: NutriLens is an educational nutrition-support tool based on ICMR-NIN food composition data and "
        "published clinical reference ranges. It does not diagnose or treat any condition. Please consult a qualified "
        "doctor before changing your diet, medicines or supplements."), ST["disclaimer"]))
    return story


# ── Page furniture ────────────────────────────────────────────────────────────
class _NumberedCanvas(rl_canvas.Canvas):
    """Adds 'Page X of Y' and the footer once the total page count is known."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages: list[dict] = []

    def setFont(self, psfontname, size, leading=None):
        super().setFont(font(psfontname), size, leading)

    def drawString(self, x, y, text, *args, **kwargs):
        super().drawString(x, y, text, *args, **{**kwargs, "shaping": _lang() != "en"})

    def drawRightString(self, x, y, text, *args, **kwargs):
        super().drawRightString(x, y, text, *args, **{**kwargs, "shaping": _lang() != "en"})

    def drawCentredString(self, x, y, text, *args, **kwargs):
        super().drawCentredString(x, y, text, *args, **{**kwargs, "shaping": _lang() != "en"})

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            self.setStrokeColor(SLATE_200)
            self.setLineWidth(0.6)
            self.line(MARGIN_X, 13 * mm, PAGE_W - MARGIN_X, 13 * mm)
            self.setFont("Helvetica", 6.8)
            self.setFillColor(SLATE_400)
            self.drawString(MARGIN_X, 9 * mm, L("NutriLens is an educational nutrition tool. It does not replace "
                                                "medical diagnosis or treatment."))
            self.setFillColor(SLATE_500)
            self.setFont("Helvetica", 7)
            self.drawRightString(PAGE_W - MARGIN_X, 9 * mm, L("Page {page} of {total}", page=self._pageNumber, total=total))
            super().showPage()
        super().save()


def _first_page(ref: str, when: str):
    def draw(c: rl_canvas.Canvas, _doc) -> None:
        top = PAGE_H - 12 * mm
        _draw_logo(c, MARGIN_X, top - 22, 22)
        c.setFillColor(SLATE_900)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(MARGIN_X + 30, top - 10, "NutriLens")
        c.setFillColor(SLATE_500)
        c.setFont("Helvetica", 7.6)
        c.drawString(MARGIN_X + 30, top - 20, L("Evidence-based nutrition guidance from your lab report"))
        c.setFillColor(SLATE_700)
        c.setFont("Helvetica", 8.4)
        if when:
            c.drawRightString(PAGE_W - MARGIN_X, top - 9, when)
        c.setFillColor(SLATE_500)
        c.setFont("Helvetica", 7.6)
        c.drawRightString(PAGE_W - MARGIN_X, top - 20, L("Ref #{ref}", ref=ref))
        c.setStrokeColor(SLATE_200)
        c.setLineWidth(0.6)
        c.line(MARGIN_X, PAGE_H - 25 * mm, PAGE_W - MARGIN_X, PAGE_H - 25 * mm)
    return draw


def _later_pages(ref: str):
    def draw(c: rl_canvas.Canvas, _doc) -> None:
        top = PAGE_H - 10 * mm
        _draw_logo(c, MARGIN_X, top - 12, 12)
        c.setFillColor(SLATE_900)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN_X + 17, top - 9, "NutriLens")
        c.setFillColor(SLATE_500)
        c.setFont("Helvetica", 7)
        c.drawRightString(PAGE_W - MARGIN_X, top - 9, f"{L('Personalized Clinical Nutrition Plan')}  |  {L('Ref #{ref}', ref=ref)}")
        c.setStrokeColor(SLATE_200)
        c.setLineWidth(0.6)
        c.line(MARGIN_X, PAGE_H - 16 * mm, PAGE_W - MARGIN_X, PAGE_H - 16 * mm)
    return draw


# ── Entry point ───────────────────────────────────────────────────────────────
def generate_plan_pdf(analysis_data: dict[str, Any], lang: str = "en") -> bytes:
    """Build the A4 PDF for a FullAnalysisResponse (as a JSON-ready dict) in English, Hindi or Telugu."""
    lang = lang if lang in ("hi", "te") else "en"
    token = LANG.set(lang)
    try:
        return _build(analysis_data or {}, lang)
    finally:
        LANG.reset(token)


def _build(result: dict[str, Any], lang: str) -> bytes:
    english = [m for m in result.get("marker_analyses") or [] if isinstance(m, dict)]
    parts = _explanation_parts(result.get("grounded_explanation") or "")
    notes = {m.get("biomarker_key"): parts.get(_clean(m.get("display_name")).lower(), {}) for m in english}
    doctor_only = {m.get("biomarker_key") for m in english
                   if "does not give food advice" in str(m.get("clinical_warning") or "")}
    if lang != "en":
        from app.i18n import localize_analysis
        result = localize_analysis(result, lang)
    markers = [m for m in result.get("marker_analyses") or [] if isinstance(m, dict)]
    profile = result.get("user_profile") or {}
    ref = re.sub(r"[^A-Za-z0-9]", "", str(result.get("analysis_id") or ""))[:8] or "--------"
    counts = {status: sum(1 for m in markers if m.get("status") == status) for status in STATUS_ORDER}
    markers_by_key = {m.get("biomarker_key"): m for m in markers}
    flagged = [m for m in markers if m.get("status") != "normal"]
    plans = [p for p in result.get("recommendations") or [] if isinstance(p, dict)]
    improve = [p for p in plans if (p.get("purpose") or "improve") == "improve"]
    maintain = [p for p in plans if p.get("purpose") == "maintain"]

    diet = DIET_LABEL.get(profile.get("diet_type"), _clean(profile.get("diet_type")).replace("_", " "))
    diet = diet.lower() if lang == "en" else L(diet)
    allergens = [_clean(a).lower() if lang == "en" else L(_clean(a).title())
                 for a in profile.get("allergens") or [] if _clean(a)]
    exclusions = L("excluding {list}", list=", ".join(allergens)) if allergens else L("with no food exclusions")

    story: list = [
        NextPageTemplate("later"),
        Paragraph(L("Personalized Clinical Nutrition Plan"), ST["title"]),
        Spacer(1, 2),
        Paragraph(L("Based on {n} laboratory results, for a <b>{diet}</b> diet {exclusions}.", n=len(markers),
                    diet=_t(diet or L("personal")), exclusions=_t(exclusions)), ST["subtitle"]),
        Spacer(1, 10),
        _profile_strip(profile),
        Spacer(1, 10),
        _summary(counts, len(markers)),
        Spacer(1, 14),
    ]
    reasons = [r for r in result.get("consult_reasons") or [] if _clean(r)]
    if result.get("requires_physician_consult") and reasons:
        story += [_safety_warning(reasons), Spacer(1, 14)]
    if isinstance(result.get("diet_plan"), dict):
        story += _diet_plan(result["diet_plan"])
    if flagged:
        story += _at_a_glance(flagged, improve, doctor_only) + [Spacer(1, 16)]

    plan_section = [SectionTitle(L("Your Food Plan"), L("Indian foods chosen for each result, matched to your diet and "
                                                       "food exclusions. Servings are typical household portions.")),
                    Spacer(1, 10)]
    if improve:
        for number, plan in enumerate(improve, 1):
            part = _food_plan(plan, markers_by_key, number)
            if number == 1:
                part[0] = KeepTogether([*plan_section, *part[0]._content])
            story += part
    else:
        message = L("None of your results needs a corrective food plan. Please review any results marked for a doctor."
                    if flagged else "All your results are within healthy ranges, so no corrective food plan is needed.")
        story += [KeepTogether([*plan_section, Box([Paragraph(message, ST["body"])], fill=BRAND_50, stroke=BRAND_200,
                                                    pad_y=10)]), Spacer(1, 16)]
    if maintain:
        story += _maintain(maintain)
    if flagged:
        story += _meanings(flagged, notes)
    if markers:
        story += [PageBreak()] + _all_results(markers) + [Spacer(1, 16)]
    story += _closing(bool(flagged))

    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=LATER_TOP, bottomMargin=BOTTOM,
        title="NutriLens - Personalized Clinical Nutrition Plan", author="NutriLens",
        subject="Personalized nutrition plan from laboratory results",
    )
    frame = dict(leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate("first", [Frame(MARGIN_X, BOTTOM, CONTENT_W, PAGE_H - BOTTOM - FIRST_TOP, id="first", **frame)],
                     onPage=_first_page(ref, _report_time(result.get("timestamp")))),
        PageTemplate("later", [Frame(MARGIN_X, BOTTOM, CONTENT_W, PAGE_H - BOTTOM - LATER_TOP, id="later", **frame)],
                     onPage=_later_pages(ref)),
    ])
    doc.build(story, canvasmaker=_NumberedCanvas)
    return buffer.getvalue()
