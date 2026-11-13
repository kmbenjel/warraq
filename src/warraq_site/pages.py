"""Collecting pages: front matter, source overlay (upstream docs over local drafts) and URLs."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass, field
from pathlib import Path

import yaml

LANGS = ("ar", "en")
# Fixed sidebar positions of the pages every tool has; guides come between quickstart and faq.
TOOL_ORDER = {"index": 0, "why": 1, "install": 2, "quickstart": 3, "guides": 4, "faq": 9}


class FrontMatterError(ValueError):
    pass


def split_front_matter(text: str, where: str = "") -> tuple[dict, str]:
    """Return (meta, body). A file without a leading `---` block has empty meta."""
    if text.startswith("﻿"):
        text = text[1:]
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            try:
                meta = yaml.safe_load("\n".join(lines[1:i])) or {}
            except yaml.YAMLError as e:
                raise FrontMatterError(f"{where}: bad front matter: {e}") from e
            if not isinstance(meta, dict):
                raise FrontMatterError(f"{where}: front matter is not a mapping")
            return meta, "\n".join(lines[i + 1 :]).lstrip("\n")
    raise FrontMatterError(f"{where}: front matter is not closed with ---")


@dataclass
class Page:
    key: str  # virtual source path, e.g. "safha/ar/guides/crop.md" or "site/ar/about.md"
    file: Path
    lang: str
    url: str  # site path, always starts and ends with "/"
    tool: str | None
    meta: dict
    body: str
    upstream: bool = False  # True when the file came from the tool's own repo
    html: str = ""
    toc: list = field(default_factory=list)

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or self.stem)

    @property
    def stem(self) -> str:
        return posixpath.splitext(posixpath.basename(self.key))[0]

    @property
    def rel(self) -> str:
        """Path inside the language folder: "guides/crop.md"."""
        return self.key.split("/", 2)[2]

    @property
    def draft(self) -> bool:
        return bool(self.meta.get("draft"))

    @property
    def section(self) -> str:
        if self.tool:
            return self.tool
        return self.rel.split("/")[0] if "/" in self.rel else ""

    def sort_key(self) -> tuple:
        rel = self.rel
        if self.tool:
            head = rel.split("/")[0].removesuffix(".md")
            group = TOOL_ORDER.get(head, 5)
            return (group, _num(self.meta.get("order")), rel)
        return (0 if self.stem == "index" else 1, _num(self.meta.get("order")), rel)


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 50.0


def url_for(section_prefix: str, lang: str, rel: str) -> str:
    """Map a source path inside a language folder to a pretty URL."""
    stem = rel.removesuffix(".md")
    if stem == "index":
        stem = ""
    elif stem.endswith("/index"):
        stem = stem[: -len("/index")]
    parts = [p for p in ("en" if lang == "en" else "", section_prefix, stem) if p]
    return "/" + "/".join(parts) + ("/" if parts else "")


def overlay(*roots: Path) -> dict[str, Path]:
    """Relative path → file, later roots winning over earlier ones."""
    out: dict[str, Path] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("*")):
            if f.is_file() and not any(p.startswith(".") for p in f.relative_to(root).parts):
                out[f.relative_to(root).as_posix()] = f
    return out


def collect(root: Path, tools: list[str], upstream_dir: Path) -> tuple[list[Page], dict[str, tuple[str, Path]]]:
    """All pages, and all other files as virtual key → (site path without leading slash, file)."""
    pages: list[Page] = []
    media: dict[str, tuple[str, Path]] = {}
    for lang in LANGS:
        for rel, f in overlay(root / "content" / lang).items():
            if rel.endswith(".md"):
                pages.append(_load(f"site/{lang}/{rel}", f, lang, url_for("", lang, rel), None))
            else:
                media[f"site/{lang}/{rel}"] = (url_for("", lang, rel).strip("/"), f)
    for slug in tools:
        drafts = root / "drafts" / slug
        up = upstream_dir / slug
        for lang in LANGS:
            local = overlay(drafts / lang)
            remote = overlay(up / lang)
            for rel, f in {**local, **remote}.items():
                key = f"{slug}/{lang}/{rel}"
                if rel.endswith(".md"):
                    p = _load(key, f, lang, url_for(slug, lang, rel), slug)
                    p.upstream = rel in remote
                    pages.append(p)
                else:
                    media[key] = (url_for(slug, lang, rel).strip("/"), f)
        for rel, f in {**overlay(drafts / "media"), **overlay(up / "media")}.items():
            media[f"{slug}/media/{rel}"] = (f"{slug}/media/{rel}", f)
    seen: dict[str, str] = {}
    for p in pages:
        if p.url in seen:
            raise ValueError(f"two pages map to {p.url}: {seen[p.url]} and {p.key}")
        seen[p.url] = p.key
    return pages, media


def _load(key: str, f: Path, lang: str, url: str, tool: str | None) -> Page:
    text = f.read_text(encoding="utf-8")
    try:
        meta, body = split_front_matter(text, key)
    except FrontMatterError as e:  # keep building; the problem is reported with the others
        meta, body = {"_error": str(e)}, text.split("\n---", 2)[-1]
    return Page(key=key, file=f, lang=lang, url=url, tool=tool, meta=meta, body=body)


def resolve(page_key: str, href: str, by_key: dict[str, Page], media_keys: dict[str, str]) -> str | None:
    """Resolve a relative link written in a page's source to a site URL (None if unknown).

    `media_keys` maps virtual media paths ("safha/media/a.webp") to site paths.
    """
    path, _, frag = href.partition("#")
    base = posixpath.dirname(page_key)
    target = posixpath.normpath(posixpath.join(base, path)) if path else page_key
    tail = f"#{frag}" if frag else ""
    if target in by_key:
        return by_key[target].url + tail
    if target.endswith("/") or not posixpath.splitext(target)[1]:
        for cand in (target.rstrip("/") + ".md", target.rstrip("/") + "/index.md"):
            if cand in by_key:
                return by_key[cand].url + tail
    if target in media_keys:
        return "/" + media_keys[target] + tail
    return None
