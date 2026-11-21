#!/usr/bin/env python3
"""Make the walk-through's sample library: three short public-domain Arabic books, typeset and "scanned".

The pages carry the faults real scans have, so that every step of the walk-through has work to do:
dark scanner margins, tilted pages, a blank leaf, two-page spreads, an exact duplicate, and
file names as uploaders leave them. Each book has enough pages (six or more of text) for a crop tool to
measure one box for the whole book. Nothing here is copied from a modern edition: the texts are
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

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, features

DPI = 150
W, H = 620, 874  # A6 at 150 dpi: a pocket-size book
PARA = 30  # body type in pixels: large type on a small page, about six words to the line

# Each hadith: its number in the book, the text, and the note on who transmitted it.
NAWAWI = [
    (
        "الحديث الأول",
        "عن أمير المؤمنين أبي حفصٍ عمرَ بن الخطاب رضي الله عنه قال: سمعتُ رسول الله صلى الله عليه وسلم يقول:"
        " «إنما الأعمالُ بالنيات، وإنما لكل امرئٍ ما نوى، فمن كانت هجرتُه إلى الله ورسوله فهجرتُه إلى الله ورسوله،"
        " ومن كانت هجرتُه لدنيا يصيبها أو امرأةٍ ينكحها فهجرتُه إلى ما هاجر إليه».",
        "رواه إماما المحدّثين: أبو عبد الله محمد بن إسماعيل البخاري، وأبو الحسين مسلم بن الحجاج القشيري النيسابوري،"
        " في صحيحيهما اللذين هما أصحّ الكتب المصنّفة.",
    ),
    (
        "الحديث الثالث",
        "عن أبي عبد الرحمن عبد الله بن عمر بن الخطاب رضي الله عنهما قال: سمعتُ رسول الله صلى الله عليه وسلم يقول:"
        " «بُني الإسلامُ على خمس: شهادةِ أن لا إله إلا الله وأن محمدًا رسول الله، وإقامِ الصلاة، وإيتاءِ الزكاة،"
        " وحجِّ البيت، وصومِ رمضان».",
        "رواه البخاري ومسلم.",
    ),
    (
        "الحديث الخامس",
        "عن أم المؤمنين أم عبد الله عائشة رضي الله عنها قالت: قال رسول الله صلى الله عليه وسلم:"
        " «من أحدث في أمرنا هذا ما ليس منه فهو ردّ».",
        "رواه البخاري ومسلم. وفي روايةٍ لمسلم: «من عمل عملًا ليس عليه أمرنا فهو ردّ».",
    ),
    (
        "الحديث السابع",
        "عن أبي رقيّة تميم بن أوسٍ الداري رضي الله عنه أن النبي صلى الله عليه وسلم قال: «الدينُ النصيحة»."
        " قلنا: لمن؟ قال: «لله، ولكتابه، ولرسوله، ولأئمة المسلمين وعامّتهم».",
        "رواه مسلم.",
    ),
    (
        "الحديث التاسع",
        "عن أبي هريرة عبد الرحمن بن صخرٍ رضي الله عنه قال: سمعتُ رسول الله صلى الله عليه وسلم يقول:"
        " «ما نهيتُكم عنه فاجتنبوه، وما أمرتُكم به فأتوا منه ما استطعتم، فإنما أهلك الذين من قبلكم كثرةُ مسائلهم"
        " واختلافُهم على أنبيائهم».",
        "رواه البخاري ومسلم.",
    ),
    (
        "الحديث الثالث عشر",
        "عن أبي حمزة أنس بن مالكٍ رضي الله عنه، خادمِ رسول الله صلى الله عليه وسلم، عن النبي صلى الله عليه وسلم قال:"
        " «لا يؤمن أحدُكم حتى يحبَّ لأخيه ما يحبُّ لنفسه».",
        "رواه البخاري ومسلم.",
    ),
]
SHANFARA = [
    ("أقيموا بني أمّي صدورَ مطيّكم", "فإنّي إلى قومٍ سواكم لأميلُ"),
    ("فقد حُمّت الحاجاتُ والليلُ مقمرٌ", "وشُدّت لطيّاتٍ مطايا وأرحُلُ"),
    ("وفي الأرض منأىً للكريم عن الأذى", "وفيها لمن خاف القِلى متعزَّلُ"),
    ("لعمرُك ما بالأرض ضيقٌ على امرئٍ", "سرى راغبًا أو راهبًا وهو يعقلُ"),
    ("ولي دونكم أهلون سِيدٌ عملَّسٌ", "وأرقطُ زُهلولٌ وعرفاءُ جيألُ"),
    ("هم الأهلُ لا مستودعُ السرِّ ذائعٌ", "لديهم ولا الجاني بما جرَّ يُخذلُ"),
    ("وكلٌّ أبيٌّ باسلٌ غير أنني", "إذا عرضت أولى الطرائد أبسلُ"),
    ("وإن مُدّت الأيدي إلى الزاد لم أكن", "بأعجلهم إذ أجشعُ القوم أعجلُ"),
    ("وما ذاك إلا بسطةٌ عن تفضّلٍ", "عليهم وكان الأفضلَ المتفضّلُ"),
    ("وإني كفاني فقدَ من ليس جازيًا", "بحسنى ولا في قربه متعلَّلُ"),
    ("ثلاثةُ أصحابٍ فؤادٌ مشيَّعٌ", "وأبيضُ إصليتٌ وصفراءُ عيطلُ"),
    ("هتوفٌ من المُلس المتون يزينها", "رصائعُ قد نيطت إليها ومِحملُ"),
]
# One printed page each: the chapter heading (when a chapter opens on the page) and its paragraphs.
AJURRUM = [
    (
        "باب الكلام",
        [
            "الكلامُ: هو اللفظُ المركّبُ المفيدُ بالوضع. وأقسامه ثلاثة: اسمٌ، وفعلٌ، وحرفٌ جاء لمعنى.",
            "فالاسمُ يُعرف بالخفض، والتنوين، ودخول الألف واللام، وحروف الخفض، وهي: مِن، وإلى، وعن، وعلى، وفي،"
            " ورُبّ، والباء، والكاف، واللام، وحروفِ القسم، وهي: الواو، والباء، والتاء.",
            "والفعلُ يُعرف بقد، والسين، وسوف، وتاء التأنيث الساكنة. والحرفُ ما لا يصلح معه دليلُ الاسم ولا دليلُ الفعل.",
        ],
    ),
    (
        "باب الإعراب",
        [
            "الإعرابُ: هو تغيير أواخر الكلم لاختلاف العوامل الداخلة عليها لفظًا أو تقديرًا.",
            "وأقسامه أربعة: رفعٌ، ونصبٌ، وخفضٌ، وجزمٌ. فللأسماء من ذلك الرفعُ والنصبُ والخفضُ ولا جزمَ فيها،"
            " وللأفعال من ذلك الرفعُ والنصبُ والجزمُ ولا خفضَ فيها.",
        ],
    ),
    (
        "باب معرفة علامات الإعراب",
        [
            "للرفع أربعُ علامات: الضمة، والواو، والألف، والنون.",
            "فأما الضمة فتكون علامةً للرفع في أربعة مواضع: في الاسم المفرد، وجمع التكسير، وجمع المؤنث السالم،"
            " والفعل المضارع الذي لم يتصل بآخره شيء.",
            "وأما الواو فتكون علامةً للرفع في موضعين: في جمع المذكر السالم، وفي الأسماء الخمسة، وهي: أبوك،"
            " وأخوك، وحموك، وفوك، وذو مال.",
        ],
    ),
    (
        None,
        [
            "وأما الألف فتكون علامةً للرفع في تثنية الأسماء خاصة.",
            "وأما النون فتكون علامةً للرفع في الفعل المضارع إذا اتصل به ضميرُ تثنية، أو ضميرُ جمع، أو ضميرُ"
            " المؤنثة المخاطبة.",
            "وللنصب خمسُ علامات: الفتحة، والألف، والكسرة، والياء، وحذف النون.",
        ],
    ),
    (
        None,
        [
            "فأما الفتحة فتكون علامةً للنصب في ثلاثة مواضع: في الاسم المفرد، وجمع التكسير، والفعل المضارع إذا"
            " دخل عليه ناصبٌ ولم يتصل بآخره شيء.",
            "وأما الألف فتكون علامةً للنصب في الأسماء الخمسة، نحو: رأيتُ أباك وأخاك، وما أشبه ذلك.",
            "وأما الكسرة فتكون علامةً للنصب في جمع المؤنث السالم.",
        ],
    ),
    (
        None,
        [
            "وأما الياء فتكون علامةً للنصب في التثنية والجمع.",
            "وأما حذف النون فيكون علامةً للنصب في الأفعال الخمسة التي رفعُها بثبات النون.",
            "وللخفض ثلاثُ علامات: الكسرة، والياء، والفتحة. فأما الكسرة فتكون علامةً للخفض في ثلاثة مواضع: في"
            " الاسم المفرد المنصرف، وجمع التكسير المنصرف، وجمع المؤنث السالم.",
        ],
    ),
    (
        None,
        [
            "وأما الياء فتكون علامةً للخفض في ثلاثة مواضع: في الأسماء الخمسة، والتثنية، والجمع. وأما الفتحة"
            " فتكون علامةً للخفض في الاسم الذي لا ينصرف.",
            "وللجزم علامتان: السكون، والحذف. فأما السكون فيكون علامةً للجزم في الفعل المضارع الصحيح الآخر."
            " وأما الحذف فيكون علامةً للجزم في الفعل المضارع المعتلّ الآخر، وفي الأفعال الخمسة التي رفعُها بثبات"
            " النون.",
        ],
    ),
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
        "pages": "8",
    },
    {
        "file": "lamiya-final(2).pdf",
        "title": "لامية العرب",
        "author": "الشنفرى",
        "death_hijri": "",
        "editor": "",
        "publisher": "عينة ورّاق",
        "pages": "7",
    },
    {
        "file": "ajrumiya_ar.pdf",
        "title": "متن الآجرومية",
        "author": "محمد بن محمد بن آجروم الصنهاجي",
        "death_hijri": "723",
        "editor": "",
        "publisher": "عينة ورّاق",
        "pages": "8",
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
        margin, y = 74, 96
        for kind, value in blocks:
            if kind == "title":
                f = self.font(46)
                d.text((W // 2, y + 150), str(value), font=f, fill=25, anchor="mm", direction="rtl", language="ar")
                y += 240
            elif kind == "sub":
                f = self.font(28)
                d.text((W // 2, y + 22), str(value), font=f, fill=45, anchor="mm", direction="rtl", language="ar")
                y += 72
            elif kind == "para":
                for line in self.wrap(d, str(value), PARA, W - 2 * margin):
                    d.text(
                        (W - margin, y),
                        line,
                        font=self.font(PARA),
                        fill=20,
                        anchor="ra",
                        direction="rtl",
                        language="ar",
                    )
                    y += int(PARA * 1.85)
                y += 14
            elif kind == "verse":
                a, b = value  # type: ignore[misc]
                f = self.font(28)
                d.text((W - margin, y + 30), a, font=f, fill=20, anchor="ra", direction="rtl", language="ar")
                d.text((margin, y + 86), b, font=f, fill=20, anchor="la", direction="rtl", language="ar")
                y += 150
        if folio is not None:
            d.text((W // 2, H - 62), str(folio), font=self.font(22), fill=60, anchor="mm")
        return img


def to_pdf(images: list[Image.Image], path: Path) -> None:
    rgb = [im.convert("L") for im in images]
    buf = io.BytesIO()
    rgb[0].save(buf, "PDF", resolution=DPI, save_all=True, append_images=rgb[1:], quality=72)
    path.write_bytes(buf.getvalue())


def spread(a: Image.Image, b: Image.Image) -> Image.Image:
    """Two pages scanned side by side on one image (right-hand page first, as an Arabic book opens).

    The pages meet at the gutter, where the paper curves away from the glass and reads a little darker.
    """
    img = Image.new("L", (a.width + b.width, max(a.height, b.height)), 38)
    img.paste(a, (b.width, 0))
    img.paste(b, (0, 0))
    shade = Image.new("L", img.size, 255)
    d = ImageDraw.Draw(shade)
    for i in range(26):
        tone = 205 + 2 * i  # 205 at the fold, paper white 26 px away
        d.line([(b.width - i, 0), (b.width - i, img.height)], fill=tone)
        d.line([(b.width + i, 0), (b.width + i, img.height)], fill=tone)
    return ImageChops.multiply(img, shade)


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

    # Tilts (degrees) and dark scanner margins (left, top, right, bottom) differ from page to page.
    tilts = (0.3, -0.25, 0.2, -0.35, 0.3, -0.2, 0.25)
    beds = ((50, 28, 18, 32), (46, 32, 22, 28), (42, 28, 22, 36), (52, 26, 20, 30), (48, 30, 18, 34), (44, 32, 22, 30))

    def scanned(pages: list[Image.Image], first: int = 0) -> list[Image.Image]:
        return [bed(pg, tilts[(first + i) % len(tilts)], beds[(first + i) % len(beds)]) for i, pg in enumerate(pages)]

    nawawi = [
        bed(
            ts.page([("title", "الأربعون النووية"), ("sub", "للإمام يحيى بن شرف النووي"), ("sub", "ت 676 هـ")], None),
            0.0,
            (28, 28, 22, 36),
        ),
        bed(Image.new("L", (W, H), 246), 0.0, (28, 28, 22, 36)),  # the blank verso of the title leaf
        *scanned(
            [
                ts.page([("sub", head), ("para", text), ("para", note)], n)
                for n, (head, text, note) in enumerate(NAWAWI, 1)
            ]
        ),
    ]
    lamiya = [
        bed(ts.page([("title", "لامية العرب"), ("sub", "للشنفرى الأزدي")], None), 0.6, (28, 50, 28, 22)),
        *scanned([ts.page([("verse", v) for v in SHANFARA[i : i + 2]], i // 2 + 1) for i in range(0, 12, 2)], 2),
    ]
    leaves = [ts.page([("title", "متن الآجرومية"), ("sub", "لابن آجروم الصنهاجي"), ("sub", "ت 723 هـ")], None)]
    for n, (head, paras) in enumerate(AJURRUM, 1):
        leaves.append(ts.page([*([("sub", head)] if head else []), *(("para", t) for t in paras)], n))
    spread_tilts = (0.25, -0.3, 0.3, -0.25)
    ajurrum = [
        bed(spread(leaves[i], leaves[i + 1]), spread_tilts[i // 2], (36, 36, 36, 36)) for i in range(0, len(leaves), 2)
    ]

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
        "Texts (public domain): al-Nawawi (d. 676 AH), al-Arba'un, hadiths 1, 3, 5, 7, 9 and 13; al-Shanfara"
        " (6th c. CE), Lamiyyat al-Arab, lines 1-12; Ibn Ajurrum (d. 723 AH), al-Ajurrumiyya, the chapters on speech,"
        " inflection and the signs of inflection.\n"
        "Typeset and 'scanned' by make_sample.py in the warraq repository; released under CC0.\n",
        encoding="utf-8",
    )
    if a.preview:
        # Two rows that read right to left: the first book's opening pages, then the other two files.
        rows = [nawawi[:4], [*lamiya[:2], ajurrum[0]]]
        thumbs = [[im.copy() for im in row] for row in rows]
        for t in (t for row in thumbs for t in row):
            t.thumbnail((300, 300))
        width = max(sum(t.width for t in row) + 16 * (len(row) + 1) for row in thumbs)
        sheet = Image.new("L", (width, len(thumbs) * 316 + 16), 230)
        for r, row in enumerate(thumbs):
            x = width - 16
            for t in row:
                x -= t.width
                sheet.paste(t, (x, 16 + r * 316 + (300 - t.height) // 2))
                x -= 16
        sheet.convert("RGB").save(a.preview, quality=82)
    total = sum(p.stat().st_size for p in (out / "scans").iterdir())
    print(f"wrote {len(files) + 1} PDFs ({total // 1024} KB) and catalog.csv to {out}/")


if __name__ == "__main__":
    main()
