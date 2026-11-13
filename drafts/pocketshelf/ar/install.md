---
title: التثبيت
description: تثبيت pocketshelf بأداة uv أو pipx أو pip.
draft: true
---

تحتاج pocketshelf إلى Python 3.10 أو أحدث.

```bash
uvx pocketshelf --help
```

أو تثبيتٌ دائم:

```bash
pipx install pocketshelf
```

## من المصدر

```bash
git clone https://github.com/kmbenjel/pocketshelf.git
cd pocketshelf
uv sync
uv run pocketshelf --help
```

لا يحتاج الفهرس الناتج إلى أي تثبيت: يكفيه متصفح.
