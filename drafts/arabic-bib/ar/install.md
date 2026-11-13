---
title: التثبيت
description: تثبيت arabic-bib مكتبةً في Python أو أداةَ سطر أوامر.
draft: true
---

تحتاج arabic-bib إلى Python 3.10 أو أحدث، ولا تعتمد على مكتباتٍ خارجية.

## أداة سطر أوامر

```bash
uvx arabic-bib --help
```

## مكتبة في مشروعك

```bash
pip install arabic-bib
```

```python
from arabic_bib import fold

fold("أَحْمَدُ بْنُ تَيْمِيَّةَ") == fold("احمد بن تيميه")  # True
```

## من المصدر

```bash
git clone https://github.com/kmbenjel/arabic-bib.git
cd arabic-bib
uv sync
uv run pytest
```
