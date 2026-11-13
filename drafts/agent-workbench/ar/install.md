---
title: التثبيت
description: تثبيت agent-workbench أداةَ سطر أوامر وإضافةً لـ Claude Code.
draft: true
---

تحتاج agent-workbench إلى Python 3.10 أو أحدث.

```bash
uvx agent-workbench --help
```

أو تثبيتٌ دائم، فيصير الأمر المختصر `awb` متاحًا:

```bash
pipx install agent-workbench
```

## في مشروعك

```bash
awb init
```

يكتب هذا الأمر ملف إعدادٍ مشروحًا في المجلد الحالي.

## إضافة Claude Code

في المستودع مجلد `skills` فيه مهارةٌ تعلّم الوكيل كيف يبني الصفحات ويتابع الملاحظات ويغلق البطاقات. طريقة إضافتها في ملف README في المستودع.
