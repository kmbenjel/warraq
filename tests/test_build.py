import json
import re
from pathlib import Path

from warraq_site.build import build, check_links, load_config
from warraq_site.cli import main
from warraq_site.sync import sync


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_build_drafts_only(site: Path):
    res = build(site)
    out = res.out
    assert res.problems == []
    assert res.upstream == 0
    for path in (
        "index.html",
        "about/index.html",
        "alpha/index.html",
        "alpha/why/index.html",
        "alpha/guides/one/index.html",
        "alpha/media/pic.png",
        "beta/faq/index.html",
        "404.html",
        "CNAME",
        ".nojekyll",
        "sitemap.xml",
        "robots.txt",
        "search.json",
    ):
        assert (out / path).exists(), path
    assert read(out / "CNAME").strip() == "docs.example.org"
    html = read(out / "alpha/index.html")
    assert 'href="/alpha/quickstart/"' in html
    assert 'href="/alpha/faq/#سؤال"' in html
    assert 'name="warraq:draft"' in html  # drafts are marked in the head ...
    visible = re.sub(r"<[^>]+>", " ", html.split("<body", 1)[1])
    assert "draft" not in visible.lower()  # ... never in the visible page
    guide = read(out / "alpha/guides/one/index.html")
    assert 'src="/alpha/media/pic.png"' in guide and 'loading="lazy"' in guide
    assert '<pre dir="ltr"><code class="language-bash">' in read(out / "alpha/quickstart/index.html")
    assert "https://docs.example.org/alpha/why/" in read(out / "sitemap.xml")


def test_sidebar_order_puts_why_after_overview(site: Path):
    out = build(site).out
    html = read(out / "alpha/faq/index.html")
    nav = html.split('class="side-nav"', 1)[1].split("</nav>", 1)[0]
    labels = ["نظرة عامة", "ما الذي يميّزه؟", "البدء السريع", "أدلة", "أسئلة شائعة"]
    positions = [nav.index(label) for label in labels]
    assert positions == sorted(positions)


def test_upstream_overrides_drafts(site: Path):
    reports = {r.slug: r for r in sync(site, load_config(site))}
    assert not reports["alpha"].found
    assert reports["beta"].found and reports["beta"].media == 1
    assert "drafts kept for why.md, quickstart.md, faq.md" in reports["beta"].warnings
    res = build(site)
    assert res.problems == []
    assert res.upstream == 2
    beta = read(res.out / "beta/index.html")
    assert "بيتا" in beta and 'name="warraq:draft"' not in beta
    assert 'href="/beta/install/"' in beta
    assert 'src="/beta/media/card.png"' in beta
    landing = read(res.out / "index.html")
    assert "عرضٌ من المستودع" in landing  # the pitch from the tool's own index.md
    assert 'src="/beta/media/card.png"' in landing  # and its card picture
    assert "عرض ألف" in landing  # the configured pitch for a tool without docs
    assert (res.out / "beta/faq/index.html").exists()  # the draft still fills the gap


def test_no_drafts_leaves_drafts_out(site: Path):
    sync(site, load_config(site))
    res = build(site, drafts=False)
    assert not (res.out / "alpha/index.html").exists()
    assert (res.out / "beta/install/index.html").exists()
    assert (res.out / "index.html").exists()


def test_search_index(site: Path):
    sync(site, load_config(site))
    out = build(site).out
    docs = json.loads(read(out / "search.json"))
    install = [d for d in docs if d["u"].startswith("/beta/install/")]
    assert {d["h"] for d in install} == {"", "من PyPI"}
    sec = next(d for d in install if d["h"])
    assert sec["u"] == "/beta/install/#من-pypi"
    assert "بِيتَا" in sec["x"] and sec["s"] == "beta"
    assert json.loads(read(out / "en/search.json")) == []


def test_broken_links_are_reported(site: Path):
    (site / "content/ar/about.md").write_text("---\ntitle: x\n---\n[لا شيء](nothing.md) [أداة](/gamma/)\n")
    res = build(site)
    assert any("'nothing.md' does not resolve" in p for p in res.problems)
    assert any("broken link /gamma/" in p for p in res.problems)


def test_bad_front_matter_is_reported_not_fatal(site: Path):
    (site / "drafts/alpha/ar/why.md").write_text("---\ntitle: a: b\n---\nنص\n", encoding="utf-8")
    res = build(site)
    assert any("alpha/ar/why.md: bad front matter" in p for p in res.problems)
    assert (res.out / "alpha/why/index.html").exists()


def test_check_links_on_tree(tmp_path: Path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a/index.html").write_text('<a href="/a/">x</a><img src="/b.png"><a href="//cdn/x">y</a>')
    assert check_links(tmp_path) == ["a/index.html: broken link /b.png"]


def test_cli(site: Path, capsys):
    assert main(["--root", str(site), "build", "--sync", "--strict"]) == 0
    out = capsys.readouterr().out
    assert "beta             1 pages" not in out and "2 pages, 1 media" in out
    assert "built" in out
    (site / "content/ar/about.md").write_text("---\ntitle: x\n---\n[x](nothing.md)\n")
    assert main(["--root", str(site), "build", "--strict"]) == 1


def test_sync_from_git(site: Path, tmp_path: Path):
    import subprocess

    repo = tmp_path / "siblings" / "beta"
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-C", str(repo)]
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "docs"], check=True)
    cfg = load_config(site)
    cfg["sources"]["git"] = f"file://{tmp_path}/siblings/{{slug}}"
    reports = {r.slug: r for r in sync(site, cfg, mode="git")}
    assert reports["beta"].found and len(reports["beta"].pages) == 2
    assert not reports["alpha"].found  # no such repository: drafts are used
    assert (site / ".cache/upstream/beta/ar/install.md").exists()


def test_head_for_search_engines_and_shared_links(site: Path):
    (site / "assets").unlink()  # the fixture links the real assets; this test wants its own
    (site / "assets/img").mkdir(parents=True)
    (site / "assets/img/social.png").write_bytes(b"\x89PNG\r\n")
    sync(site, load_config(site))
    out = build(site).out
    home = read(out / "index.html")
    assert '<meta property="og:image" content="https://docs.example.org/assets/img/social.png">' in home
    assert '<meta name="twitter:card" content="summary_large_image">' in home
    assert '<meta property="og:type" content="website">' in home
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', home, re.S).group(1))
    assert ld["@type"] == "WebSite" and ld["potentialAction"]["target"]["urlTemplate"].endswith(
        "/?q={search_term_string}"
    )
    beta = read(out / "beta/install/index.html")
    assert (
        '<meta property="og:image" content="https://docs.example.org/beta/media/card.png">' in beta
    )  # the tool's card
    assert '<meta property="og:type" content="article">' in beta
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', beta, re.S).group(1))
    assert [i["name"] for i in ld["itemListElement"]] == ["ورّاق", "beta", "التثبيت"]
    assert ld["itemListElement"][1]["item"] == "https://docs.example.org/beta/"
    nf = read(out / "404.html")
    assert '<meta name="robots" content="noindex">' in nf and 'rel="canonical"' not in nf
    assert "hreflang" not in beta  # no English twin, no alternates


def test_language_alternates_and_header_links(site: Path):
    en = site / "content/en"
    en.mkdir(parents=True)
    ar_landing = (site / "content/ar/index.md").read_text(encoding="utf-8")
    (en / "index.md").write_text(ar_landing.replace("(about.md)", "(../ar/about.md)"), encoding="utf-8")
    res = build(site)
    assert res.problems == []
    ar, eng = read(res.out / "index.html"), read(res.out / "en/index.html")
    for page in (ar, eng):
        assert '<link rel="alternate" hreflang="ar" href="https://docs.example.org/">' in page
        assert '<link rel="alternate" hreflang="en" href="https://docs.example.org/en/">' in page
        assert '<link rel="alternate" hreflang="x-default" href="https://docs.example.org/">' in page
    # the walk-through exists in Arabic only: the English header says so, the Arabic one does not
    assert '<a href="/tutorial/" hreflang="ar" lang="ar">' in eng
    assert '<a href="/tutorial/">' in ar
    assert '<a href="/en/#tools">' in eng


def test_wide_tables_and_heading_links(site: Path):
    tables = "|أ|ب|ج|د|\n|-|-|-|-|\n|1|2|3|4|\n\n|أ|ب|\n|-|-|\n|1|2|\n\n"
    body = f"## قسم\n\n{tables}[إلى القسم](#قسم) [وإلى ألف](/alpha/faq/#سؤال)\n"
    (site / "content/ar/about.md").write_text(f"---\ntitle: عن\n---\n{body}", encoding="utf-8")
    res = build(site)
    assert res.problems == []
    html = read(res.out / "about/index.html")
    assert '<div class="table-wrap wide" data-label="جدول"><table style="--cols:4">' in html
    assert '<div class="table-wrap" data-label="جدول"><table>' in html
    assert 'aria-label="رابط هذا القسم"' in html


def test_broken_fragments_are_reported(site: Path):
    body = "## قسم\n\n[لا قسم](#غائب) [ولا سؤال](/alpha/faq/#غائب) [صحيح](/alpha/faq/#سؤال)\n"
    (site / "content/ar/about.md").write_text(f"---\ntitle: عن\n---\n{body}", encoding="utf-8")
    res = build(site)
    assert sorted(res.problems) == [
        "about/index.html: broken link #غائب (no such heading)",
        "about/index.html: broken link /alpha/faq/#غائب (no such heading)",
    ]


def test_nav_title_overrides_the_sidebar_label(site: Path):
    f = site / "content/ar/tutorial/index.md"
    f.write_text(
        f.read_text(encoding="utf-8").replace("title: دليل عملي", "title: دليل عملي\nnav_title: مقدمة"),
        encoding="utf-8",
    )
    out = build(site).out
    nav = read(out / "tutorial/01-step/index.html").split('class="side-nav"', 1)[1].split("</nav>", 1)[0]
    assert ">مقدمة</a>" in nav and "<title>خطوة" in read(out / "tutorial/01-step/index.html")
