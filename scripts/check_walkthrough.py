#!/usr/bin/env python3
"""Run the walk-through («دليل عملي») exactly as its pages tell the reader to, and fail if any command fails.

The commands are read from the ```bash blocks of content/ar/tutorial/*.md, in page order, and run on a fresh copy
of sample/warraq-sample. The plan the reader is asked to save is taken from the page too. At the end the folder
must look the way the last pages say it does.

    python scripts/check_walkthrough.py --tools ..          # the tools' checkouts next to this repository
    python scripts/check_walkthrough.py                     # the released tools, through the real `uvx`
    python scripts/check_walkthrough.py --tools .. --keep out --offline

With --tools DIR, `uvx TOOL …` runs DIR/TOOL/.venv/bin/TOOL when that exists, else `uvx --from DIR/TOOL TOOL …`.
Only the standard library is needed here; the tools bring their own dependencies.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "content" / "ar" / "tutorial"
SAMPLE = ROOT / "sample" / "warraq-sample"
_FENCE = re.compile(r"^```(\w*)[^\n]*\n(.*?)^```\s*$", re.S | re.M)

# What the reader does by hand or in a browser, and what this script does in its place.
SKIP = (
    (re.compile(r"^git clone "), "the sample is copied from this checkout"),
    (re.compile(r"sample/make_sample\.py"), "regenerating the sample needs a font file"),
    (re.compile(r"\bdemo\b.*--serve\b"), "starts a server and waits"),
)
NETWORK = re.compile(r"\bfetch openiti\b|\breconcile\b.*openiti:")
ANSWER_YES = re.compile(r"^uvx planfs (apply|undo)\b")  # the reader types «yes» at the prompt
EXPECTED = (
    "متون الحديث/الأربعون النووية - يحيى بن شرف النووي.pdf",
    "الأدب/لامية العرب - الشنفرى.pdf",
    "النحو والصرف/متن الآجرومية - محمد بن محمد بن آجروم الصنهاجي.pdf",
    "الفهرس.html",
)


@dataclass
class Step:
    page: str
    kind: str  # "run", "skip" or "file"
    text: str
    note: str = ""


def blocks(markdown: str) -> list[tuple[str, str, int]]:
    """Fenced blocks of a page as (language, body, offset of the block in the page)."""
    return [(m.group(1), m.group(2), m.start()) for m in _FENCE.finditer(markdown)]


def steps(pages_dir: Path = PAGES, *, offline: bool = False) -> list[Step]:
    """Every command of the walk-through, in reading order, with what to do about it."""
    out: list[Step] = []
    for page in sorted(pages_dir.glob("[0-9][0-9]-*.md")):
        text = page.read_text(encoding="utf-8")
        for lang, body, start in blocks(text):
            if lang == "text" and body.startswith("action\t"):
                # The page names the file to save the plan as, in the sentence just above the block.
                names = re.findall(r"`([^`\n]+\.tsv)`", text[:start])
                if not names:
                    raise SystemExit(f"{page.name}: a plan block without a file name before it")
                out.append(Step(page.name, "file", body, names[-1]))
            elif lang == "bash":
                for line in body.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    why = next((note for rx, note in SKIP if rx.search(line)), "")
                    if not why and offline and NETWORK.search(line):
                        why = "needs the network (--offline)"
                    out.append(Step(page.name, "skip" if why else "run", line, why))
    return out


def shim(bin_dir: Path, tools: Path | None) -> None:
    """A `uvx` that runs the tools from their checkouts, so the pages' commands run unchanged."""
    if tools is None:
        return
    bin_dir.mkdir(parents=True)
    script = bin_dir / "uvx"
    script.write_text(
        "#!/bin/sh\n"
        'tool="$1"; shift\n'
        f'home="{tools}/$tool"\n'
        'if [ -x "$home/.venv/bin/$tool" ]; then exec "$home/.venv/bin/$tool" "$@"; fi\n'
        f'exec "{shutil.which("uvx") or "uvx"}" --from "$home" "$tool" "$@"\n',
        encoding="utf-8",
    )
    script.chmod(0o755)


def run(work: Path, tools: Path | None, *, offline: bool = False, verbose: bool = False) -> list[str]:
    """Run the walk-through in `work`; return the list of failures (empty when all is well)."""
    env = dict(os.environ)
    shim(work / ".bin", tools.resolve() if tools else None)
    if tools:
        env["PATH"] = f"{work / '.bin'}{os.pathsep}{env['PATH']}"
    cwd, failures = work, []
    for s in steps(offline=offline):
        if s.kind == "file":
            target = cwd / s.note
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(s.text, encoding="utf-8")
            print(f"  file  {s.page:16} {s.note}")
            continue
        if s.kind == "skip":
            print(f"  skip  {s.page:16} {s.text}   ({s.note})")
            continue
        cmd = s.text
        if cmd.startswith("cp -r warraq/sample/warraq-sample "):
            shutil.copytree(SAMPLE, cwd / cmd.split()[-1])
            print(f"  ok    {s.page:16} {cmd}")
            continue
        if cmd.startswith("cd "):
            cwd = (cwd / cmd[3:].strip()).resolve()
            continue
        if ANSWER_YES.match(cmd):
            cmd += " --yes"
        cmd = cmd.replace(" --open", "")  # no browser here
        t0 = time.monotonic()
        r = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, capture_output=True, text=True)
        state = "ok" if r.returncode == 0 else "FAIL"
        print(f"  {state:5} {s.page:16} {s.text}   [{time.monotonic() - t0:.1f}s]")
        if verbose or r.returncode:
            print("        " + (r.stdout + r.stderr).strip().replace("\n", "\n        "))
        if r.returncode:
            failures.append(f"{s.page}: `{s.text}` exited {r.returncode}")
    for rel in EXPECTED:
        if not (cwd / rel).is_file():
            failures.append(f"after the walk-through, {rel} is missing")
    if (cwd / "scans").exists() and any((cwd / "scans").iterdir()):
        failures.append("after the walk-through, scans/ still holds files")
    index = cwd / "الفهرس.html"
    if index.is_file() and "pocketshelf" not in index.read_text(encoding="utf-8", errors="replace"):
        failures.append("الفهرس.html does not look like a pocketshelf catalogue")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tools", type=Path, help="folder holding the tools' checkouts (default: the real uvx)")
    ap.add_argument("--keep", type=Path, help="run in this folder and keep it (default: a temporary folder)")
    ap.add_argument("--offline", action="store_true", help="skip the commands that download a catalogue")
    ap.add_argument("-v", "--verbose", action="store_true", help="print each command's output")
    ap.add_argument("--list", action="store_true", help="print the commands and stop")
    a = ap.parse_args()
    if a.list:
        for s in steps(offline=a.offline):
            print(f"{s.kind:5} {s.page:16} {s.note if s.kind == 'file' else s.text}")
        return 0
    if a.keep:
        if a.keep.exists():
            shutil.rmtree(a.keep)
        a.keep.mkdir(parents=True)
        failures = run(a.keep.resolve(), a.tools, offline=a.offline, verbose=a.verbose)
    else:
        with tempfile.TemporaryDirectory(prefix="warraq-walkthrough-") as tmp:
            failures = run(Path(tmp), a.tools, offline=a.offline, verbose=a.verbose)
    for f in failures:
        print(f"! {f}")
    print("walk-through: " + ("FAILED" if failures else "every command ran"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
