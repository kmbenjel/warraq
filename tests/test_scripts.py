"""The two docs checkers: the walk-through runner reads the pages rightly, the command checker catches mistakes."""

import importlib.util
import stat
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


walk = load("check_walkthrough")
cmds = load("check_commands")

FAKE_TOOL = """#!{python}
import argparse
ap = argparse.ArgumentParser(prog="safha")
sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")
c = sub.add_parser("crop", help="crop a book")
c.add_argument("pdf")
c.add_argument("--rtl", action="store_true")
c.add_argument("--drop")
c.add_argument("-o", "--output")
q = sub.add_parser("queue", help="a queue")
qs = q.add_subparsers(dest="q", required=True)
r = qs.add_parser("run")
r.add_argument("--jobs")
ap.parse_args()
"""


@pytest.fixture
def tools(tmp_path: Path):
    exe = tmp_path / "safha" / ".venv" / "bin" / "safha"
    exe.parent.mkdir(parents=True)
    exe.write_text(FAKE_TOOL.format(python=sys.executable), encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    return cmds.Tools(tmp_path)


def test_walkthrough_steps_cover_every_page():
    steps = walk.steps()
    pages = {s.page for s in steps}
    assert {"01-sample.md", "02-clean.md", "03-name.md", "04-match.md", "05-plan.md", "06-catalog.md"} <= pages
    run = [s.text for s in steps if s.kind == "run"]
    assert run[0].startswith("cp -r warraq/sample/warraq-sample ") and run[1] == "cd my-library"
    assert all(s.note for s in steps if s.kind == "skip")
    assert any("--drop 2" in c for c in run) and any(c.endswith("--rtl") for c in run)


def test_walkthrough_plan_is_a_real_tsv():
    (plan,) = [s for s in walk.steps() if s.kind == "file"]
    assert plan.note == "plans/001-sample-names.tsv"
    rows = [line.split("\t") for line in plan.text.splitlines()]
    assert rows[0] == ["action", "from", "to", "reason"]
    assert all(len(r) == 4 for r in rows)
    assert {r[0] for r in rows[1:]} == {"move", "delete"}
    assert all(r[2] == "" for r in rows[1:] if r[0] == "delete")
    # every file the plan touches is one the earlier steps leave behind
    made = {"scans/scan_0007.safha.pdf", "scans/lamiya-final(2).safha.pdf", "scans/ajrumiya_ar.safha.pdf"}
    shipped = {f"scans/{p.name}" for p in (walk.SAMPLE / "scans").iterdir()}
    assert {r[1] for r in rows[1:]} == made | shipped
    assert {r[2] for r in rows[1:] if r[0] == "move"} == set(walk.EXPECTED) - {"الفهرس.html"}


def test_walkthrough_offline_skips_downloads():
    online = [s.text for s in walk.steps() if s.kind == "run"]
    offline = [s.text for s in walk.steps(offline=True) if s.kind == "run"]
    assert set(online) - set(offline) == {c for c in online if "openiti" in c}


def test_invocations_strip_uvx_prompts_and_pipes():
    assert cmds.invocations("$ uvx safha crop a.pdf --rtl") == [["safha", "crop", "a.pdf", "--rtl"]]
    assert cmds.invocations("uvx --from git+https://example.org/safha safha demo") == [["safha", "demo"]]
    assert cmds.invocations("LANG=C safha crop a.pdf && planfs apply p.tsv | tee log") == [
        ["safha", "crop", "a.pdf"],
        ["planfs", "apply", "p.tsv"],
    ]
    assert cmds.invocations("pip install safha") == []


def test_parse_subcommands_both_argparse_styles():
    listed = (
        "usage: t [-h] COMMAND ...\n\npositional arguments:\n  COMMAND\n    crop      crop\n"
        "    same-scan\n              long help\n\noptions:\n"
    )
    assert cmds.parse_subcommands(listed) == {"crop", "same-scan"}
    braces = "usage: t [-h] [--split {auto,never}] {build,scan} ...\n\npositional arguments:\n  {build,scan}\n"
    assert cmds.parse_subcommands(braces) == {"build", "scan"}
    assert cmds.parse_subcommands("usage: t [-h] pdf\n\npositional arguments:\n  pdf\n") == set()


def test_check_catches_unknown_subcommand_and_option(tools):
    assert cmds.check(["safha", "crop", "a.pdf", "--rtl", "-o", "b.pdf"], tools) == []
    assert cmds.check(["safha", "crop", "a.pdf", "--drop=2"], tools) == []
    assert cmds.check(["safha", "queue", "run", "--jobs", "3"], tools) == []
    assert cmds.check(["safha", "measure", "a.pdf"], tools) == ["`safha` has no sub-command measure"]
    assert cmds.check(["safha", "crop", "a.pdf", "--deskew"], tools) == ["`safha crop` has no option --deskew"]
    assert cmds.check(["safha", "queue", "run", "--rtl"], tools) == ["`safha queue run` has no option --rtl"]
    assert cmds.check(["safha", "crop", "a.pdf", "--", "other", "--flag"], tools) == []


def test_scan_reads_blocks_and_inline_code(tmp_path: Path):
    page = tmp_path / "p.md"
    page.write_text(
        "نص `safha crop a.pdf --rtl` ثم `safha` وحده.\n\n```bash\nuvx safha crop b.pdf \\\n  --drop 2\n```\n\n"
        "```text\nsafha crop c.pdf\n```\n",
        encoding="utf-8",
    )
    assert cmds.scan(page) == [(4, "uvx safha crop b.pdf --drop 2"), (1, "safha crop a.pdf --rtl")]
