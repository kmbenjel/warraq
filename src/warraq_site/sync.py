"""Pull each tool's docs/ar, docs/en and docs/media into .cache/upstream/<slug>/.

`--from local` reads sibling checkouts (default: the directory next to this repo);
`--from git` makes shallow clones (what CI does). A tool without docs keeps the site's drafts.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .pages import FrontMatterError, split_front_matter

EXPECTED = ("index.md", "why.md", "install.md", "quickstart.md", "faq.md")
MAX_MEDIA = 3 * 1024 * 1024


@dataclass
class ToolSync:
    slug: str
    found: bool = False
    pages: list[str] = field(default_factory=list)
    media: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str = ""  # set when the tool's repository could not be fetched (a build must not go on without it)


def _copy_tree(src: Path, dst: Path) -> list[Path]:
    if not src.is_dir():
        return []
    copied = []
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src)
        if f.is_file() and not any(part.startswith(".") for part in rel.parts):
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            copied.append(rel)
    return copied


def _checkout(slug: str, cfg: dict, root: Path, mode: str) -> tuple[Path | None, str]:
    """The tool's checkout and, when a clone failed, why."""
    if mode == "local":
        repo = (root / cfg["sources"]["local"] / slug).resolve()
        return (repo if repo.is_dir() else None), ""
    url = cfg["sources"]["git"].format(slug=slug)
    repo = root / ".cache" / "repos" / slug
    if repo.exists():
        shutil.rmtree(repo)
    repo.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", url, str(repo)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        last = (r.stderr.strip().splitlines() or ["git clone failed"])[-1]
        return None, f"could not clone {url}: {last}"
    subprocess.run(["git", "-C", str(repo), "sparse-checkout", "set", "docs"], capture_output=True)
    return repo, ""


def sync(root: Path, cfg: dict, mode: str = "local") -> list[ToolSync]:
    upstream = root / ".cache" / "upstream"
    results = []
    for t in cfg["tools"]:
        slug = t["slug"]
        rep = ToolSync(slug)
        dst = upstream / slug
        if dst.exists():
            shutil.rmtree(dst)
        repo, rep.error = _checkout(slug, cfg, root, mode)
        if repo is None or not (repo / "docs").is_dir():
            results.append(rep)
            continue
        for lang in ("ar", "en"):
            for rel in _copy_tree(repo / "docs" / lang, dst / lang):
                if rel.suffix != ".md":
                    continue
                rep.pages.append(f"{lang}/{rel.as_posix()}")
                try:
                    meta, _ = split_front_matter((dst / lang / rel).read_text(encoding="utf-8"), f"{slug}/{lang}/{rel}")
                except FrontMatterError as e:
                    rep.warnings.append(str(e))
                    continue
                if not meta.get("title"):
                    rep.warnings.append(f"{lang}/{rel}: no title in front matter")
        for rel in _copy_tree(repo / "docs" / "media", dst / "media"):
            rep.media += 1
            if (dst / "media" / rel).stat().st_size > MAX_MEDIA:
                rep.warnings.append(f"media/{rel}: larger than 3 MB")
        rep.found = bool(rep.pages or rep.media)
        if rep.pages:
            missing = [n for n in EXPECTED if f"ar/{n}" not in rep.pages]
            if missing:
                rep.warnings.append("drafts kept for " + ", ".join(missing))
        results.append(rep)
    return results
