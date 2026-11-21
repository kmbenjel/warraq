#!/usr/bin/env python3
"""Draw assets/img/social.png, the 1200x630 picture a shared link to the site shows.

The card is a small HTML page set in the site's own fonts and colours, photographed by headless Chrome:

    python scripts/make_social_card.py            # needs google-chrome (or CHROME=/path/to/chrome)

The title and the line under it come from site.yaml.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STEPS = ("تنظيف الصفحات", "التسمية", "المطابقة والنسبة", "الترتيب", "الفهرسة", "الإشراف")
PAGE = """<!doctype html>
<html lang="ar" dir="rtl"><meta charset="utf-8">
<style>
@font-face {{
  font-family: "Readex Pro"; font-weight: 200 700;
  src: url("{fonts}/readex-pro-var.woff2") format("woff2");
}}
@font-face {{ font-family: "Kawkab Mono"; src: url("{fonts}/kawkab-mono-regular.woff2") format("woff2"); }}
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{
  font-family: "Readex Pro", sans-serif; color: #1f1b16; box-sizing: border-box; padding: 64px 72px;
  background:
    radial-gradient(900px 420px at 88% -12%, rgba(122, 75, 30, 0.2), transparent 70%),
    radial-gradient(760px 400px at 0% 112%, rgba(30, 92, 103, 0.16), transparent 70%), #f7f4ee;
  display: flex; flex-direction: column;
}}
.brand {{ display: flex; align-items: center; gap: 22px; font-size: 76px; font-weight: 650; line-height: 1.2; }}
.kicker {{ margin: 34px 0 0; font-size: 30px; font-weight: 500; color: #9a3e1d; }}
h1 {{ margin: 10px 0 0; font-size: 58px; line-height: 1.45; font-weight: 640; max-width: 1000px; }}
.steps {{ margin-top: auto; display: flex; gap: 10px; font-size: 23px; white-space: nowrap; }}
.steps span {{ background: #fffdf8; border: 2px solid #d3c8b6; border-radius: 999px; padding: 6px 18px; }}
.url {{
  position: absolute; left: 72px; top: 84px; direction: ltr;
  font: 28px "Kawkab Mono", monospace; color: #6b6358;
}}
</style>
<div class="brand">
  <svg width="104" height="104" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#ece2d1"/>
  <rect x="5" y="5" width="54" height="54" rx="11" fill="none" stroke="#1f1b16" stroke-width="3.5"/>
  <path d="M45 17 24 44l-4 7 7-4 21-27a2.1 2.1 0 0 0-3-3Z" fill="none" stroke="#7a4b1e" stroke-width="3.5"
   stroke-linejoin="round"/><path d="M14 48h14" stroke="#1f1b16" stroke-width="3.5" stroke-linecap="round"/></svg>
  <span>{title}</span>
</div>
<div class="url">{host}</div>
<p class="kicker">{kicker}</p>
<h1>{headline}</h1>
<div class="steps">{steps}</div>
</html>
"""


def main() -> int:
    cfg = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    chrome = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        sys.exit("make_social_card.py needs Chrome: set CHROME=/path/to/chrome")
    out = ROOT / "assets" / "img" / "social.png"
    html = PAGE.format(
        fonts=(ROOT / "assets" / "fonts").as_uri(),
        title=escape(cfg["title"]),
        host=escape(cfg["cname"]),
        kicker="أدواتٌ مفتوحةُ المصدر للمكتبات التراثية الرقمية",
        headline="من مجلّدِ المسوح إلى مكتبةٍ مفهرسةٍ في جيبك",
        steps="".join(f"<span>{escape(s)}</span>" for s in STEPS),
    )
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars", "--no-sandbox",
             f"--user-data-dir={tmp}/profile", "--force-device-scale-factor=1", "--window-size=1200,630",
             "--virtual-time-budget=3000", "--allow-file-access-from-files", f"--screenshot={out}", page.as_uri()],
            check=True, capture_output=True,
        )  # fmt: skip
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
