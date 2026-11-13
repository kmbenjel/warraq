---
title: البدء السريع
description: قصّ أول كتابٍ بأداة safha في دقيقة، ورؤية الفرق قبل القصّ وبعده.
draft: true
---

## جرّب العيّنة

```bash
uvx safha demo
```

## كتابك أنت

قِس أولًا لترى ما ستفعله الأداة:

```bash
uvx safha measure book.pdf
```

ثم قصّ:

```bash
uvx safha crop book.pdf -o book-cropped.pdf
```

وقارن:

```bash
ls -l book.pdf book-cropped.pdf
```

لن يكبر الملف، لأن الصور لم يُعَد ترميزها.

## أوامر أخرى

| الأمر | ما يفعله |
|---|---|
| `safha measure` | يقيس النص والميل في كل صفحة ويقترح المربّع |
| `safha crop` | يقصّ الكتاب بمربّعٍ واحد ويقوّم الميل |
| `safha split` | يفصل الصفحتين المصوّرتين معًا (`--rtl` للكتب العربية) |
| `safha drop` | يحذف صفحاتٍ حذفًا يُرجَع عنه |
| `safha demo` | يشغّل كل ذلك على عيّنةٍ من الملك العام |

لكل أمرٍ شرحٌ مفصّل في `safha <الأمر> --help`.
