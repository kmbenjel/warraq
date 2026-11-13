---
title: التثبيت
description: تثبيت planfs بأداة uv أو pipx أو pip.
draft: true
---

تحتاج planfs إلى Python 3.10 أو أحدث، ولا تعتمد على مكتباتٍ خارجية للعمل على القرص المحلي.

```bash
uvx planfs --help
```

أو تثبيتٌ دائم:

```bash
pipx install planfs
```

## للتخزين البعيد

- للعمل عبر rclone: ثبّت [rclone](https://rclone.org/) واضبط فيه الوجهة التي تريد.
- للعمل عبر SFTP: يكفي مفتاح SSH للوجهة.
- FTP مدعومٌ دون إضافات.

## من المصدر

```bash
git clone https://github.com/kmbenjel/planfs.git
cd planfs
uv sync
uv run planfs --help
```
