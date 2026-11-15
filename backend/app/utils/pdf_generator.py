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
    BaseDocTemplate, Flowable, Frame, KeepTogether, NextPageTemplate, PageTemplate, Paragraph, Spacer,
)

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
    hour = local.strftime("%I").lstrip("0") or "12"
    return f"{local.day} {local.strftime('%b %Y')}, {hour}:{local.strftime('%M')} {local.strftime('%p').lower()} IST"


def _hex(color: colors.Color) -> str:
    return color.hexval().replace("0x", "#")


def _style(name: str, size: float, color: colors.Color, *, font: str = "Helvetica", leading: Optional[float] = None,
           align: int = 0, **extra: Any) -> ParagraphStyle:
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading or size * 1.35,
                          textColor=color, alignment=align, **extra)


ST = {
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
}


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
        self.width = stringWidth(self.text, "Helvetica-Bold", size) + 2 * self.pad + (6.5 if dot else 0)
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
        c.setFillColor(SLATE_900)
        c.roundRect(0, 0, w, h, 9, stroke=0, fill=1)

        text = c.beginText(16, h - 20)
        text.setFont("Helvetica-Bold", 6.8)
        text.setFillColor(EMERALD_400)
        text.setCharSpace(0.9)
        text.textOut("BIOMARKER HOMEOSTASIS SCORE")
        text.setCharSpace(0)  # character spacing would otherwise carry over to the next text drawn
        c.drawText(text)

        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(16, h - 39, f"{optimal} of {self.total} Biomarkers in Target Range")
        c.setFillColor(SLATE_300)
        c.setFont("Helvetica", 8)
        if flagged == 0:
            note = "All tested laboratory biomarkers are balanced within reference intervals."
        else:
            plural = "biomarkers require" if flagged > 1 else "biomarker requires"
            note = f"{flagged} {plural} targeted nutritional repletion through ICMR-NIN bioavailable foods."
        c.drawString(16, h - 52, note)

        c.setFillColor(EMERALD_400)
        c.setFont("Helvetica-Bold", 22)
        c.drawRightString(w - 16, h - 40, f"{round(optimal / self.total * 100)}%")
        index = c.beginText(0, h - 52)
        index.setFont("Helvetica", 6.5)
        index.setCharSpace(0.7)
        label = "OPTIMAL INDEX"
        index.setTextOrigin(w - 16 - stringWidth(label, "Helvetica", 6.5) - 0.7 * (len(label) - 1), h - 52)
        index.setFillColor(SLATE_400)
        index.textOut(label)
        index.setCharSpace(0)
        c.drawText(index)

        bar_x, bar_y, bar_w, bar_h = 16, 15, w - 32, 6
        c.saveState()
        clip = c.beginPath()
        clip.roundRect(bar_x, bar_y, bar_w, bar_h, bar_h / 2)
        c.clipPath(clip, stroke=0, fill=0)
        c.setFillColor(SLATE_700)
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
def _profile_strip(profile: dict) -> Box:
    allergens = [_clean(a).title() for a in profile.get("allergens") or [] if _clean(a)]
    facts = [
        ("AGE", f"{_num(profile.get('age'))} years" if profile.get("age") is not None else "-"),
        ("SEX", _clean(profile.get("gender")).title() or "-"),
        ("DIET", DIET_LABEL.get(profile.get("diet_type"), _clean(profile.get("diet_type")).replace("_", " ").title() or "-")),
        ("ALLERGEN EXCLUSIONS", ", ".join(allergens) if allergens else "None"),
    ]
    cells = [(_stack(Paragraph(label, ST["label"]), Spacer(1, 2), Paragraph(_t(value), ST["value"])), None, "left")
             for label, value in facts]
    return Box([Row(cells, gap=10)], fill=SLATE_50, radius=7, pad_y=9)


def _stat_tiles(counts: dict[str, int]) -> Row:
    tiles = []
    for status in STATUS_ORDER:
        meta = STATUS[status]
        tiles.append((Box([
            Paragraph(meta["label"], ST["tile_label"]),
            Spacer(1, 3),
            Paragraph(str(counts.get(status, 0)), ST["tile_value"]),
            Paragraph(meta["caption"], ST["tile_caption"]),
        ], accent=meta["fill"], pad_y=9), None, "left"))
    return Row(tiles, gap=8, equal_height=True)


def _safety_warning(reasons: list) -> Box:
    return Box([
        Paragraph("Clinical Safety Warning — Doctor Consultation Required", ST["warn_title"]),
        Spacer(1, 3),
        Paragraph("One or more biomarkers have reached critical depletion limits where food-first nutrition alone is "
                  "insufficient. Please consult a licensed physician for therapeutic intervention:", ST["warn_body"]),
        Spacer(1, 4),
        *_bullets(reasons, ST["warn_item"]),
    ], fill=RED_50, stroke=RED_200, pad_y=11)


def _delta_text(marker: dict) -> str:
    status, unit = marker.get("status"), _clean(marker.get("unit"))
    value, low, high = (float(marker.get(k) or 0) for k in ("value", "range_low", "range_high"))
    if status == "low":
        return f"{_num(abs(low - value))} {unit} below the healthy range"
    if status == "borderline":
        return f"Close to the lower limit of {_num(low)} {unit}"
    if status == "high":
        return f"{_num(value - high)} {unit} above the healthy range"
    return "Within the healthy range"


def _marker_card(marker: dict) -> Box:
    status = marker.get("status") if marker.get("status") in STATUS else "normal"
    meta = STATUS[status]
    unit = _t(marker.get("unit"))
    delta_style = ParagraphStyle("delta", parent=ST["small"], textColor=SLATE_500 if status == "normal" else meta["text"])
    content = [
        Row([(Paragraph(_t(marker.get("display_name")), ST["card_title"]), None, "left"),
             (Pill(meta["label"], meta["text"], meta["soft"], meta["ring"]), "auto", "right")], gap=6),
        Spacer(1, 1.5),
        Paragraph(_t(_delta_text(marker)), delta_style),
        Spacer(1, 5),
        Paragraph(f'<font name="Helvetica-Bold" size="19" color="{_hex(SLATE_900)}">{_num(marker.get("value"))}</font>'
                  f'&nbsp;<font size="8.5" color="{_hex(SLATE_500)}">{unit}</font>',
                  ParagraphStyle("val", parent=ST["body"], leading=21)),
        Spacer(1, 3),
        RangeBar(marker.get("value"), marker.get("range_low"), marker.get("range_high"), status),
        Spacer(1, 5),
        Row([(Paragraph(f"Healthy range <b>{_num(marker.get('range_low'))}–{_num(marker.get('range_high'))} {unit}</b>",
                        ST["small"]), None, "left"),
             (Paragraph(f"{_num(marker.get('percentage_of_optimal'))}% of optimal", ST["small_right"]), 0.34, "right")],
            gap=6),
    ]
    if _clean(marker.get("clinical_warning")):
        content += [Spacer(1, 7), Box([Paragraph(_md(marker["clinical_warning"]), ST["warn_small"])],
                                      fill=RED_50, stroke=RED_200, radius=5, pad_x=8, pad_y=6)]
    return Box(content, pad_y=11)


def _food_card(food: dict, nutrient: str) -> Box:
    serving = _clean(food.get("serving_size"))
    caption = " per ".join(part for part in (nutrient, serving) if part)
    content = [
        Pill(_clean(food.get("category")) or "Food", SLATE_600, SLATE_100, size=6.3, dot=False),
        Spacer(1, 5),
        Paragraph(_t(food.get("name")), ST["food_name"]),
    ]
    if _clean(food.get("hindi_name")):
        content.append(Paragraph(_t(food["hindi_name"]), ST["food_local"]))
    content += [
        Spacer(1, 6),
        Box([Paragraph(_t(_amount(food.get("key_nutrient_yield"))), ST["nutrient_value"]),
             Paragraph(_t(caption), ST["nutrient_caption"])],
            fill=BRAND_50, stroke=BRAND_100, radius=5, pad_x=7, pad_y=5),
    ]
    if _clean(food.get("preparation_tip")):
        content += [Spacer(1, 6), Paragraph(f"<b>How to eat:</b> {_md(food['preparation_tip'])}", ST["food_tip"])]
    facts = [s for s in food.get("synergies") or [] if _clean(s)]
    if facts:
        content += [Spacer(1, 5), Paragraph(_md(facts[0]), ST["food_fact"])]
    return Box(content, pad_x=10, pad_y=10)


def _dos_and_donts(dos: list, donts: list) -> Optional[Row]:
    panels = []
    if [d for d in dos if _clean(d)]:
        panels.append((Box([Paragraph("Bioavailability Catalysts (Absorption Dos)", ST["do_title"]), Spacer(1, 4),
                            *_bullets(dos, ST["do_item"])], fill=BRAND_50, stroke=BRAND_200, pad_y=10), None, "left"))
    if [d for d in donts if _clean(d)]:
        panels.append((Box([Paragraph("Absorption Antagonists (Inhibitors to Space)", ST["dont_title"]), Spacer(1, 4),
                            *_bullets(donts, ST["do_item"])], fill=RED_50, stroke=RED_200, pad_y=10), None, "left"))
    return Row(panels, gap=8, equal_height=True) if panels else None


def _protocol_groups(recommendations: list) -> list[list[dict]]:
    """Plans with the same foods and advice (e.g. Ferritin and Hemoglobin, both iron) are shown once."""
    groups: list[tuple[tuple, list[dict]]] = []
    for plan in recommendations:
        signature = (tuple(f.get("id") or f.get("name") for f in plan.get("recommended_foods") or []),
                     tuple(plan.get("absorption_dos") or []), tuple(plan.get("absorption_donts") or []))
        for existing, plans in groups:
            if existing == signature:
                plans.append(plan)
                break
        else:
            groups.append((signature, [plan]))
    return [plans for _, plans in groups]


def _protocol(plans: list[dict], markers_by_key: dict[str, dict], lead: Optional[list] = None) -> list:
    names = " & ".join(_clean(p.get("biomarker_display_name")) for p in plans)
    statuses = []
    for plan in plans:
        if plan.get("status") in STATUS and plan["status"] not in statuses:
            statuses.append(plan["status"])
    meta = STATUS[statuses[0] if statuses else "low"]
    label = " / ".join(STATUS[s]["label"] for s in statuses) or meta["label"]
    marker = markers_by_key.get(plans[0].get("target_biomarker"), {})
    nutrient = _nutrient_name(marker.get("target_nutrient_key")) or _clean(plans[0].get("biomarker_display_name"))

    header = Box([Row([
        (_stack(Paragraph("TARGET MICRONUTRIENT GOAL", ST["eyebrow"]), Spacer(1, 2),
                Paragraph(f"Nutritional Protocol for {_t(names)}", ST["card_title"])), None, "left"),
        (Pill(f"{label} Status", meta["text"], meta["soft"], meta["ring"]), "auto", "right"),
    ], gap=8, valign="middle")], fill=SLATE_50, pad_y=9)

    foods = plans[0].get("recommended_foods") or []
    rows = _grid([_food_card(food, nutrient) for food in foods]) if foods else [
        Paragraph("No foods matched your diet and allergen settings for this marker. "
                  "Please ask a dietitian for suitable alternatives.", ST["body"])]
    # Keep the header with its first row of foods; the rest may flow onto the next page.
    story: list = [KeepTogether([*(lead or []), header, Spacer(1, 8), rows[0]]), *rows[1:]]
    advice = _dos_and_donts(plans[0].get("absorption_dos") or [], plans[0].get("absorption_donts") or [])
    if advice:
        story += [Spacer(1, 8), advice]
    return story + [Spacer(1, 16)]


def _explanation_parts(explanation: str) -> tuple[str, dict[str, dict[str, str]]]:
    """Pull the executive summary and per-marker notes out of the Markdown explanation."""
    summary, impact, section, current = "", {}, "", None
    for raw in (explanation or "").splitlines():
        line = raw.rstrip()
        heading = re.match(r"^#{2,4}\s+(.*)", line)
        if heading:
            section, current = heading.group(1).strip().lower(), None
            continue
        if "executive" in section and line.strip() and not summary and not line.lstrip().startswith(("-", ">")):
            summary = line.strip()
        elif "physiological" in section:
            item = re.match(r"^-\s+\*\*(.+?)\*\*", line)
            sub = re.match(r"^\s+-\s+\*(.+?):\*\s*(.*)", line)
            if item:
                name = re.sub(r"\s*\([^()]*\)\s*$", "", item.group(1)).strip().lower()
                current = impact.setdefault(name, {})
            elif sub and current is not None:
                current[sub.group(1).strip().lower()] = sub.group(2).strip()
    return summary, impact


def _impact_card(marker: dict, notes: dict[str, str]) -> Box:
    status = marker.get("status") if marker.get("status") in STATUS else "low"
    meta = STATUS[status]
    unit = _clean(marker.get("unit"))
    relevance = notes.get("clinical relevance") or (
        f"Value is outside the laboratory's reference range ({_num(marker.get('range_low'))}–"
        f"{_num(marker.get('range_high'))} {unit}) and needs targeted nutritional support.")
    content = [
        Row([(Paragraph(_t(marker.get("display_name")), ST["card_title"]), None, "left"),
             (Pill(f"{meta['label']} ({round(float(marker.get('percentage_of_optimal') or 0))}% optimal)",
                   meta["text"], meta["soft"], meta["ring"], dot=False), "auto", "right")], gap=6),
        Spacer(1, 3),
        Paragraph(_t(f"Reported: {_num(marker.get('value'))} {unit} (Ref: {_num(marker.get('range_low'))} – "
                     f"{_num(marker.get('range_high'))} {unit})"), ST["mono"]),
        Spacer(1, 5),
        Paragraph(_md(relevance), ST["food_tip"]),
    ]
    if notes.get("biological role"):
        content += [Spacer(1, 4), Paragraph(f"<b>Role in the body:</b> {_md(notes['biological role'])}", ST["food_tip"])]
    return Box(content, pad_y=10)


def _synthesis(result: dict, markers: list[dict], counts: dict[str, int]) -> list:
    summary, impact = _explanation_parts(result.get("grounded_explanation") or "")
    flagged = [m for m in markers if m.get("status") != "normal"]
    if not summary:
        if flagged:
            summary = (f"Laboratory analysis reveals that **{len(flagged)} of {len(markers)} parameters** are outside "
                       f"reference intervals ({counts.get('low', 0)} Low, {counts.get('borderline', 0)} Borderline, "
                       f"{counts.get('high', 0)} Elevated). The food protocol above focuses on nutrient-dense Indian "
                       "staples with high absorption bioavailability to support restoration.")
        elif len(markers) == 1:
            summary = "The **tested biomarker** is within its standard reference interval."
        else:
            summary = (f"All **{len(markers)} tested biomarkers** are within standard reference intervals, "
                       "indicating healthy balance across the markers tested.")
    # In the PDF the food protocols come before this summary, not after it.
    summary = summary.replace("strategy below", "strategy in this plan")
    story: list = [KeepTogether([
        SectionTitle("Clinical Synthesis & Metabolic Interpretation",
                     "Physiological evaluation grounded in ICMR-NIN nutritional composition."),
        Spacer(1, 9),
        Box([Paragraph(_md(summary), ST["body"])], fill=SLATE_50, pad_y=11),
    ])]
    if flagged:
        cards = _grid([_impact_card(m, impact.get(_clean(m.get("display_name")).lower(), {})) for m in flagged])
        story += [Spacer(1, 12), KeepTogether([Paragraph("BIOMARKER DEPLETION &amp; PHYSIOLOGICAL IMPACT",
                                                         ST["eyebrow"]), Spacer(1, 6), cards[0]]), *cards[1:]]
    if flagged:
        story += [
            Spacer(1, 12),
            Box([Row([
                (_stack(Paragraph("Follow-up Re-testing Protocol", ST["card_title"]), Spacer(1, 2),
                        Paragraph("Allow 8 to 12 weeks of consistent food-first protocol before repeat laboratory "
                                  "blood testing.", ST["small"])), None, "left"),
                (Pill("Retest in 8–12 Weeks", BRAND_700, BRAND_50, BRAND_200, size=7, dot=False), "auto", "right"),
            ], gap=10, valign="middle")], fill=SLATE_50, pad_y=10),
        ]
    return story


# ── Page furniture ────────────────────────────────────────────────────────────
class _NumberedCanvas(rl_canvas.Canvas):
    """Adds 'Page X of Y' and the footer once the total page count is known."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages: list[dict] = []

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
            self.drawString(MARGIN_X, 9 * mm, "NutriLens is an educational nutrition tool. It does not replace "
                                              "medical diagnosis or treatment.")
            self.setFillColor(SLATE_500)
            self.setFont("Helvetica", 7)
            self.drawRightString(PAGE_W - MARGIN_X, 9 * mm, f"Page {self._pageNumber} of {total}")
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
        c.drawString(MARGIN_X + 30, top - 20, "Evidence-based nutrition guidance from your lab report")
        c.setFillColor(SLATE_700)
        c.setFont("Helvetica", 8.4)
        if when:
            c.drawRightString(PAGE_W - MARGIN_X, top - 9, when)
        c.setFillColor(SLATE_500)
        c.setFont("Helvetica", 7.6)
        c.drawRightString(PAGE_W - MARGIN_X, top - 20, f"Ref #{ref}")
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
        c.drawRightString(PAGE_W - MARGIN_X, top - 9, f"Personalized Clinical Nutrition Plan  |  Ref #{ref}")
        c.setStrokeColor(SLATE_200)
        c.setLineWidth(0.6)
        c.line(MARGIN_X, PAGE_H - 16 * mm, PAGE_W - MARGIN_X, PAGE_H - 16 * mm)
    return draw


# ── Entry point ───────────────────────────────────────────────────────────────
def generate_plan_pdf(analysis_data: dict[str, Any]) -> bytes:
    """Build the A4 PDF for a FullAnalysisResponse (as a JSON-ready dict) and return its bytes."""
    result = analysis_data or {}
    markers = [m for m in result.get("marker_analyses") or [] if isinstance(m, dict)]
    profile = result.get("user_profile") or {}
    ref = re.sub(r"[^A-Za-z0-9]", "", str(result.get("analysis_id") or ""))[:8] or "--------"
    counts = {status: sum(1 for m in markers if m.get("status") == status) for status in STATUS_ORDER}
    markers_by_key = {m.get("biomarker_key"): m for m in markers}

    diet = DIET_LABEL.get(profile.get("diet_type"), _clean(profile.get("diet_type")).replace("_", " ")).lower()
    allergens = [_clean(a).lower() for a in profile.get("allergens") or [] if _clean(a)]
    exclusions = f"excluding {', '.join(allergens)}" if allergens else "with zero dietary exclusions"

    story: list = [
        NextPageTemplate("later"),
        Paragraph("Personalized Clinical Nutrition Plan", ST["title"]),
        Spacer(1, 2),
        Paragraph(f"Formulated for a <b>{_t(diet or 'personal')}</b> diet, {_t(exclusions)}.", ST["subtitle"]),
        Spacer(1, 10),
        _profile_strip(profile),
        Spacer(1, 10),
        ScoreCard(counts, len(markers)),
        Spacer(1, 10),
        _stat_tiles(counts),
        Spacer(1, 12),
    ]
    reasons = [r for r in result.get("consult_reasons") or [] if _clean(r)]
    if result.get("requires_physician_consult") and reasons:
        story += [_safety_warning(reasons), Spacer(1, 14)]

    if markers:
        rows = _grid([_marker_card(m) for m in markers])
        story += [
            KeepTogether([SectionTitle("Laboratory Biomarker Evaluations",
                                       "Your values calibrated against printed laboratory reference intervals and "
                                       "clinical guidelines."), Spacer(1, 9), rows[0]]),
            *rows[1:],
            Spacer(1, 18),
        ]

    plans = [p for p in result.get("recommendations") or [] if isinstance(p, dict)]
    section = [SectionTitle("Targeted Nutritional Repletion Protocols",
                            "Prioritized by ICMR-NIN nutrient density per 100g, bioavailability co-factors, and "
                            "strict allergen safety."), Spacer(1, 9)]
    if plans:
        for index, group in enumerate(_protocol_groups(plans)):
            story += _protocol(group, markers_by_key, lead=section if index == 0 else None)
    else:
        story += [KeepTogether([*section, Box([Paragraph(
            "All tested biomarkers are within healthy ranges, so no targeted repletion protocol is needed. "
            "Keep following a balanced diet.", ST["body"])], fill=BRAND_50, stroke=BRAND_200, pad_y=11)]),
            Spacer(1, 16)]

    story += _synthesis(result, markers, counts)
    story += [
        Spacer(1, 12),
        Paragraph("Disclaimer: NutriLens is an educational nutrition-support tool grounded in ICMR-NIN reference data. "
                  "It does not provide medical diagnoses, treatment plans, or clinical pharmaceutical prescriptions. "
                  "Always consult a qualified physician or healthcare provider before altering your health regimen.",
                  ST["disclaimer"]),
    ]

    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=LATER_TOP, bottomMargin=BOTTOM,
        title="NutriLens - Personalized Clinical Nutrition Plan", author="NutriLens",
        subject="Personalized nutrition plan from laboratory biomarkers",
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
