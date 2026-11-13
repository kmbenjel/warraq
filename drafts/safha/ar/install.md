---
title: التثبيت
description: تثبيت safha بأداة uv أو pipx أو pip، وما تحتاج إليه.
draft: true
---

تحتاج safha إلى Python 3.10 أو أحدث.

## دون تثبيت

أسهل طريقةٍ أن تشغّلها بأداة [uv](https://docs.astral.sh/uv/) مباشرة:

```bash
uvx safha --help
```

## تثبيتٌ دائم

```bash
pipx install safha
```

أو داخل بيئةٍ افتراضية:

```bash
pip install safha
```

## من المصدر

```bash
git clone https://github.com/kmbenjel/safha.git
cd safha
uv sync
uv run safha --help
```

## تحقّق

```bash
safha demo
```

يقصّ هذا الأمر كتابًا صغيرًا من الملك العام ويضع الصفحات قبل القصّ وبعده في ملفٍّ للمقارنة.
