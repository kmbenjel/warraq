---
title: البدء السريع
description: أول استعلامٍ في turath-catalog، مؤلفو القرن الثامن وطبعات كتبهم.
draft: true
---

## مؤلفو القرن الثامن

```python
import pandas as pd

authors = pd.read_parquet("authors.parquet")
eighth = authors[(authors.death_hijri > 700) & (authors.death_hijri <= 800)]
print(len(eighth))
```

## طبعات عملٍ واحد

```python
editions = pd.read_parquet("editions.parquet")
editions[editions.work_title.str.contains("الآجرومية")]
```

## بالجداول

افتح `works.csv` في أي برنامج جداول. الترميز UTF-8، والفاصل فاصلةٌ إنجليزية.
