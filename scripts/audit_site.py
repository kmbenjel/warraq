#!/usr/bin/env python3
"""Open every built page in headless Chrome at phone and desktop widths and report what a reader would trip on.

Per page and width: horizontal overflow, elements that stick out of the viewport, console errors and failed
requests, images without alt text, pages without exactly one h1, small tap targets in the header, and (with --axe)
the WCAG A/AA rules of axe-core in the light and the dark theme. Then the search box is tried with Arabic queries
typed the way readers type them.

    python scripts/audit_site.py --site _site --out audit          # serves _site itself
    python scripts/audit_site.py --site _site --axe axe.min.js --shots / /safha/ /tutorial/02-clean/

Needs `pip install playwright` and a Chrome on the machine (`--channel chrome`, the default) or
`playwright install chromium` with `--channel ""`. axe.min.js: https://github.com/dequelabs/axe-core (MPL 2.0).
Exit status 1 when a page overflows, logs an error or breaks an axe rule.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import json
import re
import sys
import threading
from pathlib import Path

WIDTHS = {"phone": (390, 844), "desktop": (1366, 900)}
# Queries a reader would type, and a page each must find: spelling variants, clitics, digits, Latin.
QUERIES = (
    ("الاسئله الشائعه", "/faq/"),  # hamza and ta marbuta left out
    ("والتثبيت", "/install/"),  # attached conjunction and article
    ("ما الذى يميزه", "/why/"),  # alef maqsura for ya
    ("تَرَاجُع", "/planfs/"),  # fully vocalised
    ("planfs undo", "/planfs/"),
    ("٦٧٦", "/tutorial/"),  # Arabic-Indic digits
)

PROBE = """
() => {
  const vw = document.documentElement.clientWidth;
  const out = { overflow: document.documentElement.scrollWidth - vw, wide: [], noAlt: [], h1: 0, small: [], ids: [] };
  const scrolls = (el) => {
    for (let p = el.parentElement; p; p = p.parentElement) {
      const o = getComputedStyle(p).overflowX;
      if (o === "auto" || o === "scroll" || o === "hidden") return true;
    }
    return false;
  };
  const box = (r) => Math.round(r.left) + ".." + Math.round(r.right);
  for (const el of document.body.querySelectorAll("*")) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height || el.closest("dialog") || el.classList.contains("skip")) continue;
    if ((r.right > vw + 1 || r.left < -1) && !scrolls(el))
      out.wide.push(el.tagName.toLowerCase() + "." + el.className + " " + box(r));
  }
  for (const img of document.images) if (!img.hasAttribute("alt")) out.noAlt.push(img.getAttribute("src"));
  out.h1 = document.querySelectorAll("h1").length;
  for (const el of document.querySelectorAll("header a, header button")) {
    const r = el.getBoundingClientRect();
    const label = (el.textContent.trim() || el.getAttribute("aria-label") || "").slice(0, 20);
    if (r.width && (r.width < 24 || r.height < 24))
      out.small.push(label + " " + Math.round(r.width) + "x" + Math.round(r.height));
  }
  const seen = new Set();
  for (const el of document.querySelectorAll("[id]")) { if (seen.has(el.id)) out.ids.push(el.id); seen.add(el.id); }
  out.wide = out.wide.slice(0, 5);
  return out;
}
"""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # the audit prints its own report
        pass


@contextlib.contextmanager
def served(site: Path):
    handler = functools.partial(_Quiet, directory=str(site))
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            yield f"http://127.0.0.1:{srv.server_address[1]}"
        finally:
            srv.shutdown()


def page_paths(site: Path) -> list[str]:
    locs = re.findall(r"<loc>https?://[^/]+(/[^<]*)</loc>", (site / "sitemap.xml").read_text(encoding="utf-8"))
    return sorted(set(locs))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site", type=Path, default=Path("_site"), help="the built site (default: _site)")
    ap.add_argument("--out", type=Path, default=Path("audit"), help="where the report and screenshots go")
    ap.add_argument("--axe", type=Path, help="path to axe.min.js; runs the WCAG A/AA rules on every page")
    ap.add_argument("--shots", nargs="*", default=[], help="paths to screenshot at both widths, light and dark")
    ap.add_argument("--channel", default="chrome", help='browser channel ("" for Playwright\'s own Chromium)')
    ap.add_argument("--only", nargs="*", help="audit only these paths")
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("audit_site.py needs Playwright: pip install playwright")
    paths = a.only or page_paths(a.site)
    a.out.mkdir(parents=True, exist_ok=True)
    axe_src = a.axe.read_text(encoding="utf-8") if a.axe else None
    report: dict = {"pages": {}, "search": [], "axe": {}}
    problems: list[str] = []
    with served(a.site.resolve()) as base, sync_playwright() as pw:
        browser = pw.chromium.launch(channel=a.channel or None)
        for name, (w, h) in WIDTHS.items():
            for scheme in ("light", "dark") if axe_src else ("light",):
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, locale="ar")
                page = ctx.new_page()
                errors: list[str] = []
                page.on("console", lambda m, errors=errors: errors.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
                page.on("requestfailed", lambda r, errors=errors: errors.append(f"failed: {r.url}"))
                page.on(
                    "response",
                    lambda r, errors=errors: errors.append(f"{r.status}: {r.url}") if r.status >= 400 else None,
                )
                for path in paths:
                    errors.clear()
                    page.goto(base + path, wait_until="load")
                    page.evaluate("document.fonts.ready")
                    key = f"{path} [{name}]"
                    if scheme == "light":
                        got = page.evaluate(PROBE)
                        got["errors"] = list(errors)
                        report["pages"][key] = got
                        if got["overflow"] > 1:
                            problems.append(f"{key}: the page scrolls sideways by {got['overflow']} px")
                        problems += [f"{key}: sticks out: {x}" for x in got["wide"]]
                        problems += [f"{key}: {e}" for e in got["errors"]]
                        problems += [f"{key}: image without alt: {s}" for s in got["noAlt"]]
                        problems += [f"{key}: duplicate id {i}" for i in got["ids"]]
                        if got["h1"] != 1:
                            problems.append(f"{key}: {got['h1']} h1 headings")
                        problems += [f"{key}: small tap target: {s}" for s in got["small"]]
                    if axe_src:
                        page.evaluate(axe_src)
                        res = page.evaluate(
                            "() => axe.run(document, {runOnly: ['wcag2a','wcag2aa','wcag21aa','wcag22aa']})"
                            ".then(r => r.violations.map(v => ({id: v.id, impact: v.impact, n: v.nodes.length,"
                            " first: v.nodes[0].target.join(' '), why: v.nodes[0].failureSummary})))"
                        )
                        for v in res:
                            slot = report["axe"].setdefault(v["id"], {"impact": v["impact"], "pages": {}})
                            slot["pages"][f"{key} {scheme}"] = {"nodes": v["n"], "first": v["first"], "why": v["why"]}
                    if path in a.shots:
                        # lazy images load when they come into view: walk down the page before the picture
                        page.evaluate(
                            "async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) {"
                            " scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } scrollTo(0, 0); }"
                        )
                        page.wait_for_load_state("networkidle")
                        shot = re.sub(r"[^a-z0-9]+", "-", path.strip("/")) or "home"
                        page.screenshot(path=str(a.out / f"{shot}-{name}-{scheme}.png"), full_page=name == "phone")
                ctx.close()
        # Search, on a phone: open the dialog, type, read the results.
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, locale="ar")
        page = ctx.new_page()
        page.goto(base + "/")
        for query, want in QUERIES:
            page.click("[data-search-open]")
            page.fill("#q", query)
            page.wait_for_timeout(350)
            hits = page.eval_on_selector_all("#results a", "els => els.map(a => a.getAttribute('href'))")
            ok = any(want in h for h in hits[:8])
            report["search"].append({"q": query, "want": want, "hits": len(hits), "top": hits[:3], "ok": ok})
            if not ok:
                problems.append(f"search «{query}»: no result under {want} in the first eight ({len(hits)} hits)")
            page.keyboard.press("Escape")
            if page.evaluate("document.getElementById('search').open"):
                problems.append(f"search «{query}»: Escape did not close the search box")
                page.evaluate("document.getElementById('search').close()")
        if "/" in a.shots:
            page.click("[data-search-open]")
            page.fill("#q", "الاسئله الشائعه")
            page.wait_for_timeout(350)
            page.screenshot(path=str(a.out / "search-phone.png"))
        ctx.close()
        browser.close()
    for rule, slot in sorted(report["axe"].items()):
        first_page, first = next(iter(slot["pages"].items()))
        problems.append(
            f"axe {rule} ({slot['impact']}) on {len(slot['pages'])} page views, e.g. {first_page}: {first['first']}"
        )
    (a.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for p in problems:
        print(f"! {p}")
    print(f"{len(paths)} pages x {len(WIDTHS)} widths audited, {len(problems)} problem(s); report: {a.out}/report.json")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
