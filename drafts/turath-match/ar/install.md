---
title: التثبيت
description: تثبيت turath-match وتجهيز الفهارس التي تطابق بها.
draft: true
---

تحتاج turath-match إلى Python 3.10 أو أحدث.

```bash
uvx turath-match --help
```

أو:

```bash
pipx install turath-match
```

## الفهارس

تأتي الأداة بعيّنةٍ صغيرةٍ من الفهارس للتجربة. وللعمل الحقيقي، تنزّل الأداة فهارس المصادر المفتوحة عند أول استعمال، أو تقرأ ملفات [turath-catalog](/turath-catalog/).

## من المصدر

```bash
git clone https://github.com/kmbenjel/turath-match.git
cd turath-match
uv sync
uv run turath-match --help
```
