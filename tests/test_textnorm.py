import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from warraq_site.textnorm import fold, stem, tokens

CASES = [
    ("إِحْيَاءُ عُلُومِ الدِّينِ", "احيا علوم الدين"),
    ("مكتبةٌ", "مكتبه"),
    ("مستشفى", "مستشفي"),
    ("مؤلّف", "مولف"),
    ("قراءة", "قراه"),
    ("رئيس", "رييس"),
    ("كتـــاب", "كتاب"),
    ("سنة ٧٢٨ هـ", "سنه 728 ه"),
    ("۱۴۰۰", "1400"),
    ("فارسی و کتاب", "فارسي و كتاب"),
    ("ﻻ إله", "لا اله"),
    ("Planfs, Dry-Run!", "planfs dry run"),
    ("a_b", "a b"),
    ("  مسافات   كثيرة  ", "مسافات كثيره"),
]


@pytest.mark.parametrize(("raw", "want"), CASES)
def test_fold(raw, want):
    assert fold(raw) == want


def test_stem_strips_one_prefix_only_when_three_letters_remain():
    assert stem("والكتب") == "كتب"
    assert stem("الكتاب") == "كتاب"
    assert stem("بالكتاب") == "كتاب"
    assert stem("بالله") == "الله"  # «بال» would leave two letters, so only «ب» goes
    assert stem("ولد") == "ولد"
    assert stem("الى") == "الى"


def test_tokens():
    assert tokens("والمؤلفون في الكتب") == ["مولفون", "في", "كتب"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_fold_matches_python():
    js = (Path(__file__).resolve().parents[1] / "assets/js/site.js").read_text(encoding="utf-8")
    code = re.search(r"/\* fold:start \*/(.*?)/\* fold:end \*/", js, re.S).group(1)
    inputs = [raw for raw, _ in CASES] + ["الأَرْبَعُونَ النَّوَوِيَّةُ", "ابن آجُرُّوم (ت 723 هـ)"]
    prog = code + f"\nprocess.stdout.write(JSON.stringify({json.dumps(inputs, ensure_ascii=False)}.map(fold)));"
    out = subprocess.run(["node", "-e", prog], capture_output=True, text=True, check=True).stdout
    assert json.loads(out) == [fold(s) for s in inputs]
