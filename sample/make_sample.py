#!/usr/bin/env python3
"""Make the walk-through's sample library: three short public-domain Arabic texts, typeset and "scanned".

The pages carry the faults real scans have, so that every step of the walk-through has work to do:
dark scanner margins, a slight tilt, a blank leaf, a two-page spread, an exact duplicate, and
file names as uploaders leave them. Nothing here is copied from a modern edition: the texts are
classical (the authors died 700 to 1,400 years ago) and the typesetting is generated.

    python sample/make_sample.py [OUT_DIR] [--font PATH]

Needs Pillow built with libraqm (Arabic shaping); `pip install pillow` gives that on most systems.
"""

from __future__ import annotations

import argparse
import csv
import io
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

DPI = 150
W, H = 874, 1240  # A5 at 150 dpi

NAWAWI = [
    "عن أمير المؤمنين أبي حفصٍ عمرَ بن الخطاب رضي الله عنه قال: سمعتُ رسول الله صلى الله عليه وسلم يقول:"
    " «إنما الأعمالُ بالنيات، وإنما لكل امرئٍ ما نوى، فمن كانت هجرتُه إلى الله ورسوله فهجرتُه إلى الله ورسوله،"
    " ومن كانت هجرتُه لدنيا يصيبها أو امرأةٍ ينكحها فهجرتُه إلى ما هاجر إليه».",
    "رواه إماما المحدّثين: أبو عبد الله محمد بن إسماعيل البخاري، وأبو الحسين مسلم بن الحجاج القشيري النيسابوري،"
    " في صحيحيهما اللذين هما أصحّ الكتب المصنّفة.",
]
SHANFARA = [
    ("أقيموا بني أمّي صدورَ مطيّكم", "فإنّي إلى قومٍ سواكم لأميلُ"),
    ("فقد حُمّت الحاجاتُ والليلُ مقمرٌ", "وشُدّت لطيّاتٍ مطايا وأرحُلُ"),
    ("وفي الأرض منأىً للكريم عن الأذى", "وفيها لمن خاف القِلى متعزَّلُ"),
    ("لعمرُك ما بالأرض ضيقٌ على امرئٍ", "سرى راغبًا أو راهبًا وهو يعقلُ"),
]
AJURRUM = [
    "الكلامُ: هو اللفظُ المركّبُ المفيدُ بالوضع. وأقسامه ثلاثة: اسمٌ، وفعلٌ، وحرفٌ جاء لمعنى.",
    "فالاسمُ يُعرف بالخفض، والتنوين، ودخول الألف واللام، وحروف الخفض، وهي: مِن، وإلى، وعن، وعلى، وفي، ورُبّ،"
    " والباء، والكاف، واللام، وحروفِ القسم، وهي: الواو، والباء، والتاء.",
    "والفعلُ يُعرف بقد، والسين، وسوف، وتاء التأنيث الساكنة. والحرفُ ما لا يصلح معه دليلُ الاسم ولا دليلُ الفعل.",
]

# What a cataloguer would record; the naming step composes the file names from these fields.
CATALOG = [
    {
        "file": "scan_0007.pdf",
        "title": "الأربعون النووية",
        "author": "يحيى بن شرف النووي",
        "death_hijri": "676",
        "editor": "",
        "publisher": "عينة ورّاق",
        "pages": "4",
    },
    {
        "file": "lamiya-final(2).pdf",
        "title": "لامية العرب",
        "author": "الشنفرى",
        "death_hijri": "",
        "editor": "",
        "publisher": "عينة ورّاق",
        "pages": "2",
    },
    {
        "file": "ajrumiya_ar.pdf",
        "title": "متن الآجرومية",
        "author": "محمد بن محمد بن آجروم الصنهاجي",
        "death_hijri": "723",
        "editor": "",
        "publisher": "عينة ورّاق",
        "pages": "2",
    },
]


def find_font(explicit: str | None) -> str:
    if explicit:
        return explicit
    for family in ("Amiri", "Noto Naskh Arabic", "Scheherazade New"):
        try:
            r = subprocess.run(["fc-match", "-f", "%{family}\t%{file}", family], capture_output=True, text=True)
        except FileNotFoundError:
            break
        got, _, path = r.stdout.partition("\t")
        if family in got.split(",") and path:
            return path
    raise SystemExit("no Arabic font found: pass --font /path/to/Amiri-Regular.ttf (any OFL Naskh font works)")


class Typesetter:
    def __init__(self, font_path: str):
        self.path = font_path
        self.fonts: dict[int, ImageFont.FreeTypeFont] = {}

    def font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self.fonts:
            self.fonts[size] = ImageFont.truetype(self.path, size, layout_engine=ImageFont.Layout.RAQM)
        return self.fonts[size]

    def wrap(self, draw: ImageDraw.ImageDraw, text: str, size: int, width: int) -> list[str]:
        words, lines, cur = text.split(), [], ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if draw.textlength(trial, font=self.font(size), direction="rtl", language="ar") <= width:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def page(self, blocks: list[tuple[str, object]], folio: int | None) -> Image.Image:
        img = Image.new("L", (W, H), 246)
        d = ImageDraw.Draw(img)
        margin, y = 110, 150
        d.rectangle([margin - 30, 100, W - margin + 30, H - 120], outline=60, width=2)
        for kind, value in blocks:
            if kind == "title":
                f = self.font(54)
                d.text((W // 2, y + 160), str(value), font=f, fill=25, anchor="mm", direction="rtl", language="ar")
                y += 260
            elif kind == "sub":
                f = self.font(32)
                d.text((W // 2, y + 40), str(value), font=f, fill=45, anchor="mm", direction="rtl", language="ar")
                y += 90
            elif kind == "para":
                for line in self.wrap(d, str(value), 30, W - 2 * margin):
                    d.text(
                        (W - margin, y), line, font=self.font(30), fill=20, anchor="ra", direction="rtl", language="ar"
                    )
                    y += 56
                y += 24
            elif kind == "verse":
                a, b = value  # type: ignore[misc]
                f = self.font(30)
                d.text((W - margin, y), a, font=f, fill=20, anchor="ra", direction="rtl", language="ar")
                d.text((margin, y + 58), b, font=f, fill=20, anchor="la", direction="rtl", language="ar")
                y += 140
        if folio is not None:
            d.text((W // 2, H - 80), str(folio), font=self.font(26), fill=60, anchor="mm")
        return img


def to_pdf(images: list[Image.Image], path: Path) -> None:
    rgb = [im.convert("L") for im in images]
    buf = io.BytesIO()
    rgb[0].save(buf, "PDF", resolution=DPI, save_all=True, append_images=rgb[1:], quality=72)
    path.write_bytes(buf.getvalue())


def spread(a: Image.Image, b: Image.Image) -> Image.Image:
    """Two pages scanned side by side on one image (right-hand page first, as an Arabic book opens)."""
    img = Image.new("L", (a.width + b.width + 20, max(a.height, b.height)), 38)
    img.paste(a, (b.width + 20, 0))
    img.paste(b, (0, 0))
    return img


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", nargs="?", default="warraq-sample", help="output folder (default: warraq-sample)")
    ap.add_argument("--font", help="an Arabic Naskh font file (default: Amiri or Noto Naskh Arabic via fc-match)")
    ap.add_argument("--preview", help="also write a contact sheet of every page to this image file")
    a = ap.parse_args()
    if not features.check("raqm"):
        raise SystemExit(
            "Pillow was built without libraqm, so Arabic cannot be shaped; install a Pillow wheel from PyPI"
        )
    ts = Typesetter(find_font(a.font))
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "scans").mkdir(parents=True)

    def bed(img: Image.Image, tilt: float, dark: tuple[int, int, int, int]) -> Image.Image:
        left, top, right, bottom = dark
        b = Image.new("L", (img.width + left + right, img.height + top + bottom), 38)
        b.paste(img, (left, top))
        return b.rotate(tilt, resample=Image.BICUBIC, fillcolor=38).filter(ImageFilter.GaussianBlur(0.35))

    nawawi = [
        bed(
            ts.page([("title", "الأربعون النووية"), ("sub", "للإمام يحيى بن شرف النووي"), ("sub", "ت 676 هـ")], None),
            0.0,
            (60, 40, 30, 50),
        ),
        bed(Image.new("L", (W, H), 246), 0.0, (60, 40, 30, 50)),  # the blank verso of the title leaf
        bed(ts.page([("sub", "الحديث الأول"), ("para", NAWAWI[0])], 1), 1.4, (70, 40, 25, 45)),
        bed(ts.page([("para", NAWAWI[1])], 2), -1.1, (65, 45, 30, 40)),
    ]
    lamiya = [
        bed(ts.page([("title", "لامية العرب"), ("sub", "للشنفرى الأزدي")], None), 0.6, (40, 70, 40, 30)),
        bed(ts.page([("verse", v) for v in SHANFARA], 1), -0.9, (45, 65, 35, 30)),
    ]
    p1 = ts.page([("title", "متن الآجرومية"), ("sub", "لابن آجروم الصنهاجي"), ("sub", "ت 723 هـ")], None)
    p2 = ts.page([("sub", "باب الكلام"), *(("para", t) for t in AJURRUM)], 1)
    ajurrum = [bed(spread(p1, p2), 0.8, (50, 50, 50, 50))]

    files = {
        "scan_0007.pdf": nawawi,
        "lamiya-final(2).pdf": lamiya,
        "ajrumiya_ar.pdf": ajurrum,
    }
    for name, pages in files.items():
        to_pdf(pages, out / "scans" / name)
    shutil.copy2(out / "scans" / "lamiya-final(2).pdf", out / "scans" / "lamiya-final(2) - Copy.pdf")

    with (out / "catalog.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(CATALOG[0]))
        w.writeheader()
        w.writerows(CATALOG)
    (out / "SOURCES.txt").write_text(
        "Texts (public domain): al-Nawawi (d. 676 AH), al-Arba'un, hadith 1; al-Shanfara (6th c. CE), Lamiyyat al-Arab,"
        " lines 1-4; Ibn Ajurrum (d. 723 AH), al-Ajurrumiyya, opening chapter.\n"
        "Typeset and 'scanned' by make_sample.py in the warraq repository; released under CC0.\n",
        encoding="utf-8",
    )
    if a.preview:
        thumbs = [im.copy() for pages in files.values() for im in pages]
        for t in thumbs:
            t.thumbnail((260, 300))
        sheet = Image.new("L", (sum(t.width for t in thumbs) + 16 * (len(thumbs) + 1), 300 + 32), 230)
        x = 16
        for t in reversed(thumbs):  # right to left, as the book is read
            sheet.paste(t, (x, 16 + (300 - t.height) // 2))
            x += t.width + 16
        sheet.convert("RGB").save(a.preview, quality=82)
    total = sum(p.stat().st_size for p in (out / "scans").iterdir())
    print(f"wrote {len(files) + 1} PDFs ({total // 1024} KB) and catalog.csv to {out}/")


if __name__ == "__main__":
    main()
