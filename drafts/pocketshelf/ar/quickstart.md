---
title: البدء السريع
description: بناء أول فهرسٍ بأداة pocketshelf وفتحه في المتصفح.
draft: true
---

## جرّب العيّنة

فهرسٌ لكتبٍ تراثيةٍ من بياناتٍ في الملك العام، بواجهةٍ عربية:

```bash
uvx pocketshelf demo --arabic --open
```

## فهرس مكتبتك

```bash
uvx pocketshelf build ~/Books --lang ar
```

يُكتب الفهرس في `~/Books/pocketshelf.html`. وإن كانت أسماء ملفاتك على قاعدة ورّاق، فاستعمل الإعداد الجاهز:

```bash
uvx pocketshelf build ~/Books --profile warraq --lang ar
```

## صحّح ما قرأته الأداة

اكتب ما قرأته في جدول، وصحّحه، ثم أعد البناء به:

```bash
uvx pocketshelf scan ~/Books -o catalog.csv
uvx pocketshelf build ~/Books --sidecar catalog.csv --lang ar
```

## افحص ملفًّا واحدًا

```bash
uvx pocketshelf inspect "~/Books/الأدب/البيان والتبيين - الجاحظ.pdf"
```
