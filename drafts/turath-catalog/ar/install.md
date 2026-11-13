---
title: الحصول على البيانات
description: تنزيل turath-catalog بصيغة CSV أو Parquet، أو تحميلها في Python.
draft: true
---

## ملفاتٌ جاهزة

كل إصدارٍ منشورٌ في صفحة الإصدارات في المستودع، بصيغتي CSV وParquet.

## في Python

```bash
pip install turath-catalog
```

```python
import turath_catalog

works = turath_catalog.load("works")
```

## من Hugging Face

```python
from datasets import load_dataset

ds = load_dataset("kmbenjel/turath-catalog", "works")
```
