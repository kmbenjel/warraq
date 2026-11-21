"""Markdown → HTML with link resolution, plus HTML → search sections."""

from __future__ import annotations

import re
from collections.abc import Callable
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

import markdown
from markdown.extensions import Extension
from markdown.extensions.toc import slugify_unicode
from markdown.treeprocessors import Treeprocessor

Resolver = Callable[[str], "str | None"]
_EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)
_LTR_SCRIPT = re.compile(r"^[\x00-˿ -⁯]*$")


LABELS = {
    "ar": {"table": "جدول", "anchor": "رابط هذا القسم"},
    "en": {"table": "Table", "anchor": "Link to this section"},
}


class _Links(Treeprocessor):
    def __init__(self, md, resolver: Resolver, problems: list[str], lang: str = "ar"):
        super().__init__(md)
        self.resolver = resolver
        self.problems = problems
        self.labels = LABELS.get(lang, LABELS["ar"])

    def run(self, root: ET.Element) -> None:
        tables = [(parent, i, el) for parent in root.iter() for i, el in enumerate(parent) if el.tag == "table"]
        for parent, i, el in reversed(tables):
            # A table scrolls sideways inside its wrapper. site.js makes the wrapper a named, focusable region
            # when it really overflows, so that the keyboard can scroll it; data-label is the name it gets.
            wrap = ET.Element("div", {"class": "table-wrap", "data-label": self.labels["table"]})
            cols = max((len(row) for row in el.iter("tr")), default=0)
            if cols >= 4:  # wide tables keep readable columns on a phone and scroll (see .table-wrap in site.css)
                el.set("style", f"--cols:{cols}")
                wrap.set("class", "table-wrap wide")
            parent.remove(el)
            wrap.append(el)
            parent.insert(i, wrap)
        for el in root.iter():
            if el.tag == "a":
                href = el.get("href", "")
                if href and not _EXTERNAL.match(href) and not href.startswith("/"):
                    url = self.resolver(href)
                    if url is None:
                        self.problems.append(f"link {href!r} does not resolve")
                    else:
                        el.set("href", url)
                elif href.startswith(("http://", "https://")):
                    el.set("rel", "noopener")
            elif el.tag == "img":
                src = el.get("src", "")
                if src and not _EXTERNAL.match(src) and not src.startswith("/"):
                    url = self.resolver(src)
                    if url is None:
                        self.problems.append(f"image {src!r} does not resolve")
                    else:
                        el.set("src", url)
                el.set("loading", "lazy")
                el.set("decoding", "async")
            elif el.tag == "code" and (el.text or "") and _LTR_SCRIPT.match(el.text or ""):
                el.set("dir", "ltr")


class LinkExtension(Extension):
    def __init__(self, resolver: Resolver, problems: list[str], lang: str = "ar"):
        super().__init__()
        self.resolver = resolver
        self.problems = problems
        self.lang = lang

    def extendMarkdown(self, md):  # noqa: N802 (Markdown API)
        md.treeprocessors.register(_Links(md, self.resolver, self.problems, self.lang), "warraq_links", 1)


def to_html(body: str, resolver: Resolver, lang: str = "ar") -> tuple[str, list, list[str]]:
    """Return (html, toc tokens, problems)."""
    problems: list[str] = []
    anchor = LABELS.get(lang, LABELS["ar"])["anchor"]
    md = markdown.Markdown(
        extensions=["extra", "admonition", "sane_lists", "toc", LinkExtension(resolver, problems, lang)],
        extension_configs={
            "toc": {
                "slugify": slugify_unicode,
                "permalink": "#",
                "permalink_class": "anchor",
                "permalink_title": anchor,
                "toc_depth": "2-3",
            }
        },
        output_format="html",
    )
    html = md.convert(body)
    html = re.sub(r'<pre><code class="language-([\w-]+)">', r'<pre dir="ltr"><code class="language-\1">', html)
    html = html.replace("<pre><code>", '<pre dir="ltr"><code>')
    # The permalink's visible text is "#": give it a name a screen reader can say.
    html = html.replace('<a class="anchor" ', f'<a class="anchor" aria-label="{anchor}" ')
    return html, md.toc_tokens, problems


class _Sections(HTMLParser):
    """Split rendered HTML into (anchor, heading, text) at every h2/h3."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections: list[list] = [["", "", []]]
        self.in_heading = False
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h2", "h3"):
            self.sections.append([a.get("id", ""), "", []])
            self.in_heading = True
        elif tag == "a" and "anchor" in (a.get("class") or "") or tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("h2", "h3"):
            self.in_heading = False
        elif tag in ("a", "script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_heading:
            self.sections[-1][1] += data
        else:
            self.sections[-1][2].append(data)


def sections(html: str) -> list[tuple[str, str, str]]:
    p = _Sections()
    p.feed(html)
    out = []
    for anchor, head, parts in p.sections:
        text = " ".join(" ".join(parts).split())
        if head.strip() or text:
            out.append((anchor, head.strip(), text))
    return out
