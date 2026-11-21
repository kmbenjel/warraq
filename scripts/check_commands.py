#!/usr/bin/env python3
"""Check every documented command against the tools themselves: sub-commands and options must exist.

Reads the ```bash blocks and the `inline code` of each tool's docs/ar pages (and, with --readme, its README.md),
finds the invocations of the Warraq tools, and compares each sub-command and each option with what
`TOOL … --help` prints. Nothing is run except `--help`.

    python scripts/check_commands.py --tools ..            # the tools' checkouts next to this repository
    python scripts/check_commands.py --tools .. --readme   # the English READMEs too
    python scripts/check_commands.py --tools .. safha planfs

A tool is run from DIR/TOOL/.venv/bin/ when that exists, else through `uvx --from DIR/TOOL`.
Exit status 1 when a documented command names something the tool does not have.
"""

from __future__ import annotations

import argparse
import functools
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Command name → repository; the first name is the tool's main command.
COMMANDS = {
    "safha": "safha",
    "arabic-bib": "arabic-bib",
    "turath-match": "turath-match",
    "turath-catalog": "turath-catalog",
    "planfs": "planfs",
    "pocketshelf": "pocketshelf",
    "agent-workbench": "agent-workbench",
    "awb": "agent-workbench",
    "warraq-site": "warraq",
}
_FENCE = re.compile(r"^(\s*)```(\w*)[^\n]*\n(.*?)^\s*```\s*$", re.S | re.M)
_INLINE = re.compile(r"`([^`\n]+)`")
_OPTION = re.compile(r"(?<![\w-])(--[A-Za-z0-9][\w-]*|-[A-Za-z])(?![\w-])")
_SPLIT = re.compile(r"\s*(?:&&|\|\||[|;])\s*")
SHELLS = {"bash", "sh", "shell", "console", "zsh"}
DEFAULT_SUB = {"planfs": "plan"}  # `planfs PLAN …` is `planfs plan PLAN …`


class Tools:
    def __init__(self, base: Path):
        self.base = base

    def argv(self, command: str) -> list[str]:
        repo = self.base / COMMANDS[command]
        local = repo / ".venv" / "bin" / command
        if local.exists():
            return [str(local)]
        return [shutil.which("uvx") or "uvx", "--from", str(repo), command]

    @functools.cache  # noqa: B019 (one short-lived object per run)
    def help(self, command: str, path: tuple[str, ...]) -> str | None:
        """The --help text of `command path…`, or None when that sub-command does not exist."""
        try:
            r = subprocess.run(
                [*self.argv(command), *path, "--help"], capture_output=True, text=True, timeout=120, check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return r.stdout + r.stderr if r.returncode == 0 else None

    def subcommands(self, command: str, path: tuple[str, ...]) -> set[str]:
        return parse_subcommands(self.help(command, path) or "")


def parse_subcommands(help_text: str) -> set[str]:
    """Sub-command names in an argparse help text: the {a,b,c} group and the indented list under it."""
    found: set[str] = set()
    for group in re.findall(r"\{([\w,-]+)\}\s+\.\.\.", help_text.split("\n\n", 1)[0]):
        found.update(group.split(","))
    block = re.search(r"^positional arguments:\n(.*?)(?:\n\S|\n\n|\Z)", help_text, re.S | re.M)
    if block:
        lines = block.group(1).splitlines()
        heads = [m for m in (re.match(r"^( +)(\S+)", ln) for ln in lines) if m]
        if heads:
            first = len(heads[0].group(1))
            deeper = {m.group(2) for m in heads if len(m.group(1)) > first and not m.group(2).startswith("{")}
            # `COMMAND` followed by an indented list: the list holds the names. Wrapped description lines sit deeper.
            if deeper and re.fullmatch(r"[A-Za-z_]+|\{.*\}", heads[0].group(2)):
                level = min(len(m.group(1)) for m in heads if len(m.group(1)) > first)
                found.update(m.group(2) for m in heads if len(m.group(1)) == level)
    return {f for f in found if re.fullmatch(r"[a-z][a-z0-9-]*", f)}


def invocations(line: str) -> list[list[str]]:
    """Token lists of every tool invocation on a shell line (prompts, env assignments and `uvx` dropped)."""
    out = []
    for part in _SPLIT.split(line.strip().removeprefix("$ ")):
        try:
            tokens = shlex.split(part, comments=True)
        except ValueError:
            continue
        while tokens and re.fullmatch(r"[A-Z_][A-Z0-9_]*=.*", tokens[0]):
            tokens.pop(0)
        if tokens[:1] == ["uvx"]:
            tokens = tokens[1:]
            while tokens and tokens[0] in ("--from", "--with", "--python") and len(tokens) > 1:
                tokens = tokens[2:]
        if tokens and tokens[0] in COMMANDS:
            out.append(tokens)
    return out


def check(tokens: list[str], tools: Tools) -> list[str]:
    """Problems with one invocation: an unknown sub-command or an option the tool does not list."""
    command, args = tokens[0], tokens[1:]
    top = tools.help(command, ())
    if top is None:
        return [f"`{command} --help` does not run"]
    path: tuple[str, ...] = ()
    known = set(_OPTION.findall(top))
    if command in DEFAULT_SUB and not (args and args[0] in tools.subcommands(command, ())):
        known |= set(_OPTION.findall(tools.help(command, (DEFAULT_SUB[command],)) or ""))
    problems = []
    for i, tok in enumerate(args):
        subs = tools.subcommands(command, path)
        if tok == "--":
            break  # what follows is another program's command line
        if tok.startswith("-"):
            name = tok.split("=", 1)[0]
            if name in ("-", "--") or re.fullmatch(r"-\d.*", name):
                continue
            if name not in known and not (
                re.fullmatch(r"-[A-Za-z]{2,}", name) and all(f"-{c}" in known for c in name[1:])
            ):
                where = " ".join((command, *path))
                problems.append(f"`{where}` has no option {name}")
        elif tok in subs:
            path = (*path, tok)
            known |= set(_OPTION.findall(tools.help(command, path) or ""))
        elif subs and not path and i == 0 and re.fullmatch(r"[a-z][a-z0-9-]*", tok) and command not in DEFAULT_SUB:
            # A bare first word that is not a sub-command: a mistake unless the tool takes a positional here.
            usage = top.split("\n\n", 1)[0]
            if not re.search(r"\b(?!COMMAND\b)[A-Z]{3,}\b", usage.replace("usage:", "")):
                problems.append(f"`{command}` has no sub-command {tok}")
    return problems


def sources(tools_dir: Path, slugs: list[str], readme: bool) -> list[Path]:
    files: list[Path] = []
    for slug in slugs:
        repo = ROOT if slug == "warraq" else tools_dir / slug
        files += (
            sorted((repo / "docs" / "ar").rglob("*.md"))
            if slug != "warraq"
            else sorted((ROOT / "content").rglob("*.md"))
        )
        if readme and (repo / "README.md").is_file():
            files.append(repo / "README.md")
    return files


def scan(path: Path) -> list[tuple[int, str]]:
    """(line number, shell line) for every shell block line and every inline code span that names a tool."""
    text = path.read_text(encoding="utf-8")
    found: list[tuple[int, str]] = []
    covered: list[tuple[int, int]] = []
    for m in _FENCE.finditer(text):
        covered.append(m.span())
        if m.group(2) in SHELLS or (m.group(2) == "" and any(c in m.group(3) for c in COMMANDS)):
            line0 = text.count("\n", 0, m.start(3)) + 1
            joined = re.sub(r"\s*\\\n\s*", " ", m.group(3))
            for n, line in enumerate(joined.splitlines()):
                found.append((line0 + n, line))
    for m in _INLINE.finditer(text):
        if any(a <= m.start() < b for a, b in covered):
            continue
        code = m.group(1).strip()
        if code.split(" ", 1)[0] in (*COMMANDS, "uvx") and " " in code and "…" not in code and "..." not in code:
            found.append((text.count("\n", 0, m.start()) + 1, code))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slugs", nargs="*", help="tools to check (default: all, and this site's own pages)")
    ap.add_argument("--tools", type=Path, default=ROOT.parent, help="folder holding the tools' checkouts")
    ap.add_argument("--readme", action="store_true", help="also check each README.md")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every command checked")
    a = ap.parse_args()
    slugs = a.slugs or [*dict.fromkeys(COMMANDS.values())]
    tools = Tools(a.tools.resolve())
    checked = bad = 0
    for path in sources(a.tools.resolve(), slugs, a.readme):
        try:
            shown = path.relative_to(a.tools.resolve())
        except ValueError:
            shown = path
        for lineno, line in scan(path):
            for tokens in invocations(line):
                checked += 1
                problems = check(tokens, tools)
                if a.verbose and not problems:
                    print(f"ok  {shown}:{lineno}: {' '.join(tokens)}")
                for p in problems:
                    bad += 1
                    print(f"{shown}:{lineno}: {p}\n    {line.strip()}")
    print(f"{checked} documented commands checked, {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
