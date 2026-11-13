---
title: البدء السريع
description: توحيد نص، وتركيب اسم كتاب، وقراءة سنة وفاة بأداة arabic-bib.
draft: true
---

## جرّب العيّنة

```bash
uvx arabic-bib demo
```

## وحّد نصًّا للبحث

```bash
uvx arabic-bib fold "إِحْيَاءُ عُلُومِ الدِّينِ"
```

```text
احيا علوم الدين
```

## ركّب اسم كتاب

```bash
uvx arabic-bib compose --title "مجموع الفتاوى" --author "ابن تيمية" --editor "عبد الرحمن بن قاسم"
```

```text
مجموع الفتاوى - ابن تيمية - ت عبد الرحمن بن قاسم
```

## اقرأ سنة وفاة

```bash
uvx arabic-bib death "شيخ الإسلام ابن تيمية (ت 728 هـ)"
```

```text
728 هـ = 1328 م
```
