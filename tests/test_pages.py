from pathlib import Path

import pytest

from warraq_site.pages import FrontMatterError, Page, overlay, resolve, split_front_matter, url_for


def test_front_matter_parsed():
    meta, body = split_front_matter("---\ntitle: البدء\norder: 2\ndraft: true\n---\n\nنص")
    assert meta == {"title": "البدء", "order": 2, "draft": True}
    assert body == "نص"


def test_no_front_matter_and_bom():
    assert split_front_matter("نص فقط") == ({}, "نص فقط")
    assert split_front_matter("﻿---\ntitle: x\n---\nb")[0] == {"title": "x"}


@pytest.mark.parametrize("bad", ["---\ntitle: a: b\n---\n", "---\ntitle: x\n", "---\n- a\n---\n"])
def test_bad_front_matter(bad):
    with pytest.raises(FrontMatterError):
        split_front_matter(bad, "x.md")


@pytest.mark.parametrize(
    ("prefix", "lang", "rel", "url"),
    [
        ("", "ar", "index.md", "/"),
        ("", "en", "index.md", "/en/"),
        ("", "ar", "about.md", "/about/"),
        ("", "ar", "tutorial/index.md", "/tutorial/"),
        ("", "ar", "tutorial/01-sample.md", "/tutorial/01-sample/"),
        ("safha", "ar", "index.md", "/safha/"),
        ("safha", "ar", "guides/crop.md", "/safha/guides/crop/"),
        ("safha", "en", "faq.md", "/en/safha/faq/"),
    ],
)
def test_url_for(prefix, lang, rel, url):
    assert url_for(prefix, lang, rel) == url


def test_overlay_later_wins_and_hidden_skipped(tmp_path: Path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        (d / ".git").mkdir(parents=True)
        (d / ".git" / "x.md").write_text("x")
    (a / "one.md").write_text("a")
    (a / "two.md").write_text("a")
    (b / "two.md").write_text("b")
    got = overlay(a, b, tmp_path / "missing")
    assert sorted(got) == ["one.md", "two.md"]
    assert got["two.md"].read_text() == "b"


def _page(key, url):
    return Page(key=key, file=Path(key), lang="ar", url=url, tool=None, meta={}, body="")


def test_resolve():
    pages = {
        "safha/ar/index.md": _page("safha/ar/index.md", "/safha/"),
        "safha/ar/faq.md": _page("safha/ar/faq.md", "/safha/faq/"),
        "safha/ar/guides/crop.md": _page("safha/ar/guides/crop.md", "/safha/guides/crop/"),
    }
    media = {"safha/media/a.webp": "safha/media/a.webp"}
    r = lambda key, href: resolve(key, href, pages, media)  # noqa: E731
    assert r("safha/ar/index.md", "faq.md") == "/safha/faq/"
    assert r("safha/ar/index.md", "faq.md#سؤال") == "/safha/faq/#سؤال"
    assert r("safha/ar/guides/crop.md", "../faq.md") == "/safha/faq/"
    assert r("safha/ar/guides/crop.md", "../index.md") == "/safha/"
    assert r("safha/ar/guides/crop.md", "../../media/a.webp") == "/safha/media/a.webp"
    assert r("safha/ar/index.md", "../media/a.webp") == "/safha/media/a.webp"
    assert r("safha/ar/index.md", "guides/crop") == "/safha/guides/crop/"
    assert r("safha/ar/index.md", "missing.md") is None


def test_leading_h1_becomes_heading(tmp_path: Path):
    from warraq_site.pages import _load

    f = tmp_path / "x.md"
    f.write_text("---\ntitle: قصير\n---\n\n# عنوانٌ أطول\n\nنص\n", encoding="utf-8")
    p = _load("site/ar/x.md", f, "ar", "/x/", None)
    assert p.meta["heading"] == "عنوانٌ أطول" and p.title == "قصير"
    assert p.body.strip() == "نص"
