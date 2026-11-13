"""Build the static site: pages, landing, search index, sitemap, link check."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import pages as P  # noqa: N812
from .render import sections, to_html

PKG = Path(__file__).parent
UI = {
    "ar": {
        "search": "بحث",
        "search_ph": "ابحث في التوثيق…",
        "no_results": "لا نتائج. جرّب كلمة أخرى أو جذرها.",
        "theme": "تبديل السمة",
        "menu": "القائمة",
        "on_page": "في هذه الصفحة",
        "in_section": "في هذا القسم",
        "other_tools": "الأدوات الأخرى",
        "prev": "السابق",
        "next": "التالي",
        "edit": "حرّر هذه الصفحة",
        "tools": "الأدوات",
        "tutorial": "دليل عملي",
        "about": "عن المشروع",
        "home": "الرئيسية",
        "skip": "انتقل إلى المحتوى",
        "switch": "English",
        "footer_code": "الشيفرة بترخيص MIT، والنصوص بترخيص CC BY 4.0.",
        "library": "المكتبة",
        "notfound": "الصفحة غير موجودة",
    },
    "en": {
        "search": "Search",
        "search_ph": "Search the docs…",
        "no_results": "No results. Try another word.",
        "theme": "Toggle theme",
        "menu": "Menu",
        "on_page": "On this page",
        "in_section": "In this section",
        "other_tools": "Other tools",
        "prev": "Previous",
        "next": "Next",
        "edit": "Edit this page",
        "tools": "Tools",
        "tutorial": "Walk-through",
        "about": "About",
        "home": "Home",
        "skip": "Skip to content",
        "switch": "العربية",
        "footer_code": "Code under MIT, text under CC BY 4.0.",
        "library": "The library",
        "notfound": "Page not found",
    },
}


@dataclass
class Result:
    out: Path
    pages: int = 0
    drafts: int = 0
    upstream: int = 0
    problems: list[str] = field(default_factory=list)


def load_config(root: Path) -> dict:
    return yaml.safe_load((root / "site.yaml").read_text(encoding="utf-8"))


def _asset_version(root: Path) -> str:
    h = hashlib.sha1()
    for f in sorted((root / "assets").rglob("*")):
        if f.is_file() and f.suffix in (".css", ".js"):
            h.update(f.read_bytes())
    return h.hexdigest()[:10]


def build(root: Path, out: Path | None = None, *, drafts: bool = True, upstream: Path | None = None) -> Result:
    root = root.resolve()
    cfg = load_config(root)
    out = (out or root / "_site").resolve()
    upstream = upstream or root / ".cache" / "upstream"
    tools = [t["slug"] for t in cfg["tools"]]
    tool_cfg = {t["slug"]: t for t in cfg["tools"]}
    all_pages, media = P.collect(root, tools, upstream)
    res = Result(out=out)
    if not drafts:
        all_pages = [p for p in all_pages if not p.draft or p.meta.get("layout") == "landing"]
    by_key = {p.key: p for p in all_pages}
    by_url = {p.url: p for p in all_pages}
    media_sites = {k: v[0] for k, v in media.items()}

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(root / "assets", out / "assets")
    for _key, (site_path, f) in media.items():
        dst = out / site_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)

    res.problems += [p.meta["_error"] for p in all_pages if "_error" in p.meta]
    for p in all_pages:
        p.html, p.toc, probs = to_html(p.body, lambda href, p=p: P.resolve(p.key, href, by_key, media_sites))
        res.problems += [f"{p.key}: {m}" for m in probs]

    env = Environment(
        loader=FileSystemLoader(PKG / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    version = _asset_version(root)
    site_url = cfg["site_url"].rstrip("/")

    def tool_info(slug: str, lang: str) -> dict:
        t = tool_cfg[slug]
        idx = by_key.get(f"{slug}/{lang}/index.md") or by_key.get(f"{slug}/ar/index.md")
        pitch = (idx.meta.get("pitch") if idx and idx.upstream else None) or (
            t.get("pitch_en") if lang == "en" else t.get("pitch")
        )
        card = next((media[k][0] for k in (f"{slug}/media/card.webp", f"{slug}/media/card.png") if k in media), None)
        url = (idx.url if idx and idx.lang == lang else P.url_for(slug, "ar", "index.md")) if idx else None
        return {
            "slug": slug,
            "gloss": t.get("gloss", ""),
            "step": t.get("step", ""),
            "pitch": pitch,
            "card": "/" + card if card else None,
            "url": url,
        }

    groups: dict[tuple[str, str], list[P.Page]] = {}
    for p in all_pages:
        groups.setdefault((p.lang, p.section), []).append(p)
    for g in groups.values():
        g.sort(key=P.Page.sort_key)

    def nav_for(p: P.Page) -> list[dict]:
        if not p.section:
            return []
        items: list[dict] = []
        guides: dict | None = None
        for q in groups[(p.lang, p.section)]:
            label = q.title
            if p.tool and q.stem in cfg["tool_pages"] and "/" not in q.rel and p.lang == "ar":
                label = cfg["tool_pages"][q.stem]
            entry = {"title": label, "url": q.url, "current": q is p}
            if p.tool and q.rel.startswith("guides/"):
                if guides is None:
                    guides = {"title": cfg["tool_pages"]["guides"] if p.lang == "ar" else "Guides", "children": []}
                    items.append(guides)
                guides["children"].append(entry)
                guides["open"] = guides.get("open") or q is p
            else:
                items.append(entry)
        return items

    def flat(nav: list[dict]) -> list[dict]:
        o: list[dict] = []
        for n in nav:
            o += n.get("children", [n])
        return o

    def twin(p: P.Page) -> str | None:
        other = "en" if p.lang == "ar" else "ar"
        head, _, rest = p.key.split("/", 2)
        q = by_key.get(f"{head}/{other}/{rest}")
        return q.url if q else None

    def edit_url(p: P.Page) -> str:
        head, lang, rest = p.key.split("/", 2)
        gh = cfg["github"].rstrip("/")
        if p.tool and p.upstream:
            return f"{gh}/{p.tool}/blob/main/docs/{lang}/{rest}"
        if p.tool:
            return f"{gh}/warraq/blob/main/drafts/{p.tool}/{lang}/{rest}"
        return f"{gh}/warraq/blob/main/content/{lang}/{rest}"

    search_docs: dict[str, list] = {"ar": [], "en": []}
    for p in all_pages:
        nav = nav_for(p)
        seq = flat(nav)
        pos = next((i for i, n in enumerate(seq) if n["url"] == p.url), None)
        ctx = {
            "cfg": cfg,
            "ui": UI[p.lang],
            "lang": p.lang,
            "dir": "rtl" if p.lang == "ar" else "ltr",
            "page": p,
            "content": p.html,
            "toc": p.toc,
            "nav": nav,
            "prev": seq[pos - 1] if pos else None,
            "next": seq[pos + 1] if pos is not None and pos + 1 < len(seq) else None,
            "twin": twin(p),
            "home": "/en/" if p.lang == "en" else "/",
            "tool": tool_info(p.tool, p.lang) if p.tool else None,
            "tools": [tool_info(s, p.lang) for s in tools],
            "edit": edit_url(p),
            "v": version,
            "canonical": site_url + p.url,
            "description": p.meta.get("description") or cfg["description" if p.lang == "ar" else "description_en"],
        }
        template = "landing.html" if p.meta.get("layout") == "landing" else "page.html"
        html = env.get_template(template).render(**ctx)
        dst = out / p.url.strip("/") / "index.html" if p.url != "/" else out / "index.html"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(html, encoding="utf-8")
        res.pages += 1
        res.drafts += p.draft
        res.upstream += p.upstream
        crumb = tool_cfg[p.tool]["slug"] if p.tool else (UI[p.lang]["tutorial"] if p.section == "tutorial" else "")
        if p.meta.get("layout") != "landing":
            secs = sections(p.html)
            desc = str(p.meta.get("description") or "")
            if not secs or secs[0][0]:
                secs.insert(0, ("", "", desc))
            elif desc:
                secs[0] = ("", "", f"{desc} {secs[0][2]}")
            for anchor, head, text in secs:
                search_docs[p.lang].append(
                    {
                        "u": p.url + (f"#{anchor}" if anchor else ""),
                        "t": p.title,
                        "h": head,
                        "s": crumb,
                        "x": text[:2400],
                    }
                )

    for lang, docs in search_docs.items():
        if docs or lang == "en":
            name = "search.json" if lang == "ar" else "en/search.json"
            (out / name).parent.mkdir(parents=True, exist_ok=True)
            (out / name).write_text(json.dumps(docs, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    nf = env.get_template("404.html").render(
        cfg=cfg,
        ui=UI["ar"],
        lang="ar",
        dir="rtl",
        v=version,
        home="/",
        twin=None,
        page=None,
        tools=[tool_info(s, "ar") for s in tools],
        canonical=site_url + "/404.html",
        description=cfg["description"],
        toc=[],
        nav=[],
    )
    (out / "404.html").write_text(nf, encoding="utf-8")
    (out / "CNAME").write_text(cfg["cname"] + "\n", encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{site_url}{u}</loc></url>" for u in sorted(by_url))
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
        encoding="utf-8",
    )
    res.problems += check_links(out)
    return res


_HREF = re.compile(r'(?:href|src)="(/[^"#?]*)')


def check_links(out: Path) -> list[str]:
    """Every root-relative link in the output must point at a file that exists."""
    problems = []
    for f in sorted(out.rglob("*.html")):
        for target in set(_HREF.findall(f.read_text(encoding="utf-8"))):
            if target.startswith("//"):
                continue
            path = out / target.lstrip("/")
            if target.endswith("/"):
                ok = (path / "index.html").is_file()
            else:
                ok = path.is_file() or (path / "index.html").is_file()
            if not ok:
                problems.append(f"{f.relative_to(out).as_posix()}: broken link {target}")
    return problems
