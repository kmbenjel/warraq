---
title: البدء السريع
description: أول خطةٍ بأداة planfs؛ معاينةٌ ثم تطبيقٌ ثم تراجع.
draft: true
---

## جرّب العيّنة

```bash
uvx planfs demo
```

ينشئ هذا الأمر مجلدًا صغيرًا وخطةً لتسمية ملفاته، ثم يعاينها ويطبّقها ويتراجع عنها أمامك.

## خطتك الأولى

اكتب ملفًّا باسم `rename.tsv`، كل سطرٍ فيه مصدرٌ وهدفٌ وسبب، مفصولةٌ بالجدولة:

```text
IMG_0001.JPG	2024/رحلة-0001.jpg	تسمية بالتاريخ
IMG_0002.JPG	2024/رحلة-0002.jpg	تسمية بالتاريخ
```

عاين:

```bash
uvx planfs apply rename.tsv --dry-run
```

طبّق:

```bash
uvx planfs apply rename.tsv
```

وتراجع إن شئت:

```bash
uvx planfs undo rename
```

## الحذف والعمليات الأخرى

إن أردت عملياتٍ غير النقل، فاجعل أول سطرٍ عناوين الأعمدة:

```text
action	from	to	reason
delete	IMG_0001 (1).JPG		مكرّر IMG_0001.JPG
```
