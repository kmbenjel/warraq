#!/usr/bin/env python3
"""Fetch every external link of the built site and list the ones that do not answer.

    python scripts/check_external_links.py [--site _site] [--also README.md ../safha/README.md …]

Links are read from href/src attributes of the built pages (and from Markdown files given with --also);
the site's own address (its CNAME) is left out, since the build checks internal links itself.
Each URL is asked once (HEAD, then GET when a server refuses HEAD). Exit status 1 when a link is dead.
A 401/403/429 is reported as «refused» and does not fail the run: such servers turn robots away.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

_ATTR = re.compile(r'(?:href|src)="(https?://[^"#]+)')
_MD = re.compile(r"\]\((https?://[^)\s#]+)|<(https?://[^>\s#]+)>|(?:src|href)=\"(https?://[^\"#]+)")
AGENT = "Mozilla/5.0 (compatible; link check)"


def ask(url: str) -> tuple[str, int | str]:
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": AGENT, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return url, r.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue
            return url, e.code
        except Exception as e:  # noqa: BLE001 (DNS, TLS, timeouts: all are a dead link to the reader)
            if method == "GET":
                return url, type(e).__name__
    return url, "no answer"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site", type=Path, default=Path("_site"))
    ap.add_argument("--also", type=Path, nargs="*", default=[], help="Markdown files to read links from as well")
    a = ap.parse_args()
    where: dict[str, set[str]] = {}
    cname = a.site / "CNAME"
    own = f"://{cname.read_text(encoding='utf-8').strip()}/" if cname.is_file() else None  # the site's own address
    for f in sorted(a.site.rglob("*.html")):
        for url in _ATTR.findall(f.read_text(encoding="utf-8")):
            if not (own and own in url + "/"):
                where.setdefault(url, set()).add(f.relative_to(a.site).as_posix())
    for f in a.also:
        for groups in _MD.findall(f.read_text(encoding="utf-8")):
            where.setdefault(next(g for g in groups if g).rstrip(".,"), set()).add(str(f))
    dead = refused = 0
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        for url, status in sorted(pool.map(ask, sorted(where))):
            if status in (401, 403, 429):
                refused += 1
                print(f"refused {status}  {url}")
            elif not (isinstance(status, int) and status < 400):
                dead += 1
                pages = sorted(where[url])
                print(f"DEAD {status}  {url}\n     in {', '.join(pages[:4])}{' …' if len(pages) > 4 else ''}")
    print(f"{len(where)} external links asked, {dead} dead, {refused} refused")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
