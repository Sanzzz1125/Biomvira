"""Build the fonts the PDFs use for Hindi and Telugu.

ReportLab draws a paragraph in one font, so each language needs one font that has both Latin (numbers, units,
test names such as HbA1c) and the Indian script. This joins a Latin subset of Noto Sans with Noto Sans Devanagari
or Noto Sans Telugu (all SIL Open Font License 1.1) and writes backend/app/fonts/NotoSansHi-*.ttf / NotoSansTe-*.ttf.

Run from the repository root:  python evaluation/build_pdf_fonts.py   (needs fonttools; evaluation/font_sources holds the sources)
"""
from pathlib import Path

from fontTools import subset
from fontTools.merge import Merger
from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parents[1] / "backend" / "app" / "fonts"
SOURCES = Path(__file__).resolve().parent / "font_sources"  # the original Noto files (Google Fonts / notofonts)
LATIN = "U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2013-2014,U+2018-201E,U+2022,U+2026," \
        "U+2032-2033,U+2190-2193,U+2212,U+2264-2265,U+00B5,U+03BC,U+20B9"
SCRIPTS = {"Hi": ("NotoSansDevanagari", "U+0900-097F,U+1CD0-1CFF,U+A8E0-A8FF,U+200C-200D,U+25CC"),
           "Te": ("NotoSansTelugu", "U+0C00-0C7F,U+200C-200D,U+25CC")}


def _subset(path: Path, unicodes: str, out: Path) -> Path:
    options = subset.Options()
    options.hinting = False          # the two fonts' hinting programs can't be merged
    options.layout_features = ["*"]  # keep every shaping feature (conjuncts, vowel signs)
    options.name_IDs = ["*"]
    options.notdef_outline = True
    font = TTFont(path)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=subset.parse_unicodes(unicodes))
    subsetter.subset(font)
    font.save(out)
    return out


def main() -> None:
    tmp = FONTS / "_tmp"
    tmp.mkdir(exist_ok=True)
    for code, (family, script_range) in SCRIPTS.items():
        for weight in ("Regular", "Bold"):
            indic = _subset(SOURCES / f"{family}-{weight}.ttf", script_range, tmp / f"{family}-{weight}.ttf")
            latin = _subset(SOURCES / f"NotoSans-{weight}.ttf", LATIN, tmp / f"NotoSans-{weight}.ttf")
            merged = Merger().merge([str(indic), str(latin)])
            name = f"NotoSans{code}-{weight}"
            for record in merged["name"].names:
                if record.nameID in (1, 4, 6):
                    record.string = name if record.nameID == 6 else name.replace("-", " ")
            merged.save(FONTS / f"{name}.ttf")
            print(name, (FONTS / f"{name}.ttf").stat().st_size // 1024, "KB")
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()


if __name__ == "__main__":
    main()
