"""warraq-site: sync the tools' Arabic docs, build the site, preview it locally."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import sys
from pathlib import Path

from .build import build, load_config
from .sync import sync


def _root(arg: str | None) -> Path:
    root = Path(arg or ".").resolve()
    if not (root / "site.yaml").is_file():
        sys.exit(f"warraq-site: no site.yaml in {root} (run from the warraq repo or pass --root)")
    return root


def cmd_sync(a) -> int:
    root = _root(a.root)
    failed = 0
    for r in sync(root, load_config(root), a.source):
        state = (
            f"{len(r.pages)} pages, {r.media} media" if r.found else "no docs of its own; this repo's drafts, if any"
        )
        print(f"{r.slug:16} {state}")
        for w in r.warnings:
            print(f"{'':16} ! {w}")
        if r.error:
            failed += 1
            print(f"{'':16} ! {r.error}", file=sys.stderr)
    return 1 if failed else 0


def cmd_build(a) -> int:
    root = _root(a.root)
    unfetched = cmd_sync(a) if a.sync else 0
    res = build(root, Path(a.out) if a.out else None, drafts=not a.no_drafts)
    print(f"built {res.pages} pages into {res.out} ({res.upstream} from the tools' repos, {res.drafts} drafts)")
    for p in res.problems:
        print(f"  ! {p}")
    if unfetched:
        print("  ! a tool's repository could not be fetched (see above)")
    return 1 if (a.strict and (res.problems or unfetched)) else 0


def cmd_serve(a) -> int:
    root = _root(a.root)
    out = Path(a.out) if a.out else root / "_site"
    if not out.is_dir():
        print("no build yet; building first")
        build(root, out)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    with http.server.ThreadingHTTPServer(("127.0.0.1", a.port), handler) as srv:
        print(f"serving {out} at http://127.0.0.1:{a.port}/  (Ctrl-C stops)")
        with contextlib.suppress(KeyboardInterrupt):
            srv.serve_forever()
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="warraq-site",
        description="Build the Warraq Arabic documentation site from the tools' docs/ar folders.",
        epilog="Typical run:  warraq-site build --sync && warraq-site serve",
    )
    ap.add_argument("--root", help="the warraq repo (default: current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sync", help="copy each tool's docs/ar, docs/en and docs/media into .cache/upstream")
    s.add_argument(
        "--from",
        dest="source",
        choices=("local", "git"),
        default="local",
        help="local: sibling checkouts next to this repo; git: shallow clones (CI)",
    )
    s.set_defaults(func=cmd_sync)

    b = sub.add_parser("build", help="build the site into _site/")
    b.add_argument("--out", help="output directory (default: _site)")
    b.add_argument("--sync", action="store_true", help="run sync first")
    b.add_argument("--from", dest="source", choices=("local", "git"), default="local")
    b.add_argument("--no-drafts", action="store_true", help="leave out pages marked draft: true")
    b.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on a broken link, a front-matter problem, a tool without pages or a repository that did not clone",
    )
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("serve", help="preview the built site on 127.0.0.1")
    v.add_argument("--out")
    v.add_argument("--port", type=int, default=8765)
    v.set_defaults(func=cmd_serve)

    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
