---
title: المخطّط
description: جداول turath-catalog وحقولها والصلات بينها.
order: 1
draft: true
---

## الجداول والصلات

```text
authors ──< works ──< editions >── editors
               │
               └── related_to (شرح / مختصر / حاشية / نظم)
```

## الحقول الأساسية

| الجدول | الحقل | المعنى |
|---|---|---|
| `works` | `work_id` | معرّفٌ ثابت للعمل |
| `works` | `title` | العنوان المشهور |
| `works` | `author_id` | المؤلف |
| `editions` | `edition_id` | معرّفٌ ثابت للطبعة |
| `editions` | `editor` | المحقق |
| `editions` | `publisher`، `city`، `year` | الناشر ومدينته وسنة النشر |
| `editions` | `volumes` | عدد المجلدات |
| `authors` | `death_hijri`، `death_ce` | سنة الوفاة بالتقويمين |

المخطّط الكامل بصيغة JSON Schema في المستودع، وهو المرجع عند الاختلاف.
