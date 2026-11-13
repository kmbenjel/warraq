from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

SITE_YAML = """
site_url: https://docs.example.org/
cname: docs.example.org
title: ورّاق
title_en: Warraq
description: وصف
description_en: description
main_site: https://example.org/
library_site: https://example.org/library
github: https://github.com/example
sources:
  local: ../siblings
  git: https://example.invalid/{slug}.git
tools:
  - {slug: alpha, gloss: ألف, step: خطوة, pitch: عرض ألف}
  - {slug: beta, gloss: باء, step: خطوة, pitch: عرض باء}
tool_pages:
  index: نظرة عامة
  why: ما الذي يميّزه؟
  install: التثبيت
  quickstart: البدء السريع
  guides: أدلة
  faq: أسئلة شائعة
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def page(title: str, body: str = "", **meta) -> str:
    extra = "".join(f"{k}: {v}\n" for k, v in meta.items())
    return f"---\ntitle: {title}\n{extra}---\n\n{body}\n"


@pytest.fixture
def site(tmp_path: Path) -> Path:
    """A tiny site with two tools: alpha has drafts only, beta has drafts and an upstream checkout."""
    root = tmp_path / "warraq"
    write(root / "site.yaml", SITE_YAML)
    src = Path(__file__).resolve().parents[1]
    (root / "assets").symlink_to(src / "assets")
    landing = (src / "content" / "ar" / "index.md").read_text(encoding="utf-8")
    write(root / "content/ar/index.md", landing.replace("(tutorial/index.md)", "(about.md)"))
    write(root / "content/ar/tutorial/index.md", page("دليل عملي", "[الخطوة](01-step.md)"))
    write(root / "content/ar/tutorial/01-step.md", page("خطوة", "نص", order=1))
    write(root / "content/ar/about.md", page("عن المشروع", "انظر [ألف](/alpha/) و[الصفحة الرئيسية](index.md)."))
    for slug in ("alpha", "beta"):
        d = root / "drafts" / slug / "ar"
        write(d / "index.md", page(slug, "[ابدأ](quickstart.md) · [السؤال](faq.md#سؤال)", draft="true"))
        write(d / "why.md", page("لماذا", "", draft="true"))
        write(d / "quickstart.md", page("البدء", "## الأمر\n\n```bash\nalpha demo\n```", draft="true"))
        write(d / "faq.md", page("أسئلة", "### سؤال\n\nجواب.", draft="true"))
        write(d / "guides/one.md", page("دليل", "![صورة](../../media/pic.png)", draft="true", order=2))
    (root / "drafts/alpha/media").mkdir(parents=True)
    (root / "drafts/alpha/media/pic.png").write_bytes(b"\x89PNG\r\n")
    (root / "drafts/beta/media").mkdir(parents=True)
    (root / "drafts/beta/media/pic.png").write_bytes(b"\x89PNG\r\n")
    sib = tmp_path / "siblings" / "beta" / "docs"
    write(sib / "ar/index.md", page("بيتا", "[ثبّت](install.md) ![بطاقة](../media/card.png)", pitch="عرضٌ من المستودع"))
    write(sib / "ar/install.md", page("التثبيت", "## من PyPI\n\nثبّت `beta` بالأمر الآتي، وتحقّق بـ «بِيتَا».\n"))
    (sib / "media").mkdir(parents=True)
    (sib / "media/card.png").write_bytes(b"\x89PNG\r\n")
    return root
