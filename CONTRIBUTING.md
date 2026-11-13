# Contributing

## Writing docs for a tool

Each tool owns its Arabic documentation in its own repository; this site only gathers it.

```
docs/ar/index.md           overview (front matter also has `pitch:` for the landing card)
docs/ar/why.md             ما الذي يميّزه؟ — the comparison with alternatives, with evidence
docs/ar/install.md         التثبيت
docs/ar/quickstart.md      البدء السريع
docs/ar/guides/<slug>.md   one guide per task (ASCII slugs)
docs/ar/faq.md             أسئلة شائعة (### per question)
docs/media/                images; docs/media/card.webp (≈1200×750, ≤ 200 KB) is the landing card
docs/en/                   the English twin of any page, same file name
```

Every page starts with YAML front matter:

```yaml
---
title: البدء السريع
description: جملة واحدة تصف الصفحة
order: 2          # position among guides
draft: true       # optional
---
```

Link to your own pages with relative `.md` paths (`quickstart.md`, `../faq.md`) and to another tool with
`/<tool>/` (for example `/planfs/quickstart/`). Images: `../media/x.webp` from `docs/ar/`, `../../media/x.webp`
from `docs/ar/guides/`. A file you write replaces the site's draft of the same name.

Write Modern Standard Arabic for librarians and students: say what the reader does and why, keep one command per
line, and never translate an English page word for word.

## Working on the site

```bash
uv venv && uv pip install -e ".[dev]"
warraq-site build --sync      # sibling checkouts next to this repo
warraq-site serve             # http://127.0.0.1:8765/
pytest && ruff check src tests sample
```

`warraq-site build --strict` fails on any broken link or bad front matter; CI runs it.
