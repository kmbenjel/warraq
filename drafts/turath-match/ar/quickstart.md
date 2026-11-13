---
title: البدء السريع
description: أول مطابقةٍ وأول إثباتٍ للتكرار بأداة turath-match.
draft: true
---

## جرّب العيّنة

```bash
uvx turath-match demo
```

يطابق هذا الأمر قائمةً صغيرةً من الكتب بفهرسٍ صغير، ويعرض لكل كتابٍ حكمه وسببه.

## طابق جدولك

جدول CSV فيه عمودا `title` و`author` على الأقل:

```bash
uvx turath-match works my-books.csv -o matches.csv
```

## اكشف المكرّر

```bash
uvx turath-match dups /path/to/library
```

تخرج مجموعات الملفات المتطابقة، ولكل مجموعةٍ النسخة المقترح إبقاؤها وسبب اختيارها. ولا تحذف الأداة شيئًا؛ بل تكتب خطةً تطبّقها بأداة [planfs](/planfs/).
