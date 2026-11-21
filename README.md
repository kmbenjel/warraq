# Warraq — the Arabic documentation site

**The home of the Warraq tools, Arabic first: one site that gathers each tool's own `docs/ar/`, searches Arabic the way librarians type it, and reads well on a phone.**

[![CI](https://github.com/kmbenjel/warraq/actions/workflows/ci.yml/badge.svg)](https://github.com/kmbenjel/warraq/actions/workflows/ci.yml)
[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Docs: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](LICENSE-docs.md)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

Site: **https://warraq.benjelloun.dev/**

<p>
<img src="docs/media/home-desktop.webp" alt="The landing page on a desktop" width="66%">
<img src="docs/media/home-phone.webp" alt="The landing page on a phone" width="28%">
</p>

```bash
uv venv && uv pip install -e ".[dev]"
warraq-site build --sync      # gather the tools' docs from sibling checkouts, build _site/
warraq-site serve             # preview at http://127.0.0.1:8765/
```

## What it is

Warraq (الورّاق, the classical copyist and bookseller) is a family of open-source tools for building and caring for
digital heritage libraries, born from a real 16,700-volume Arabic library:

| Tool | What it does |
|---|---|
| [safha](https://github.com/kmbenjel/safha) | Lossless crop, deskew, split and page-drop for scanned PDFs |
| [arabic-bib](https://github.com/kmbenjel/arabic-bib) | Arabic bibliographic text: normalisation, names, death years, Hijri dates |
| [turath-match](https://github.com/kmbenjel/turath-match) | Catalogue reconciliation and provenance, with evidence |
| [turath-catalog](https://github.com/kmbenjel/turath-catalog) | Open bibliographic dataset: works, editions, authors, editors |
| [planfs](https://github.com/kmbenjel/planfs) | Reviewed, logged, undoable plans of file moves, renames and deletes |
| [pocketshelf](https://github.com/kmbenjel/pocketshelf) | Any folder of PDFs/EPUBs → one offline HTML catalogue |
| [agent-workbench](https://github.com/kmbenjel/agent-workbench) | Human-in-the-loop kit for long AI-agent jobs |

This repository is the documentation site for all of them: the family landing page (the path from scans to shelf,
what Warraq brings together that no single tool does, the usual way against the Warraq way), one section per tool,
and a seven-step walk-through («دليل عملي») on a small public-domain sample that ships here (`sample/warraq-sample/`).
The walk-through is run, command by command, by a script in this repository, and every command on every tool's
pages is checked against the tool itself ([What is checked](#what-is-checked)).

## How the site is put together

```mermaid
flowchart LR
  subgraph tools["each tool repository"]
    A["docs/ar/*.md"]
    M["docs/media/*"]
  end
  D["drafts/&lt;tool&gt;/ar<br>(stand-in pages for a new tool)"]
  C["content/ar, content/en<br>(landing, walk-through, about)"]
  S["warraq-site sync<br>sibling checkouts or shallow git clones"]
  B["warraq-site build<br>overlay · Markdown · link and anchor check · search index"]
  O["_site/ → GitHub Pages<br>warraq.benjelloun.dev"]
  A --> S --> B
  M --> S
  D --> B
  C --> B
  B --> O
```

- **Each tool owns its Arabic docs.** `sync` copies every tool's `docs/ar/`, `docs/en/` and `docs/media/` into
  `.cache/upstream/`. All seven tools write every page themselves. A new tool can start with stand-in pages in
  `drafts/<tool>/ar/`: a page the tool writes replaces the stand-in of the same name.
- **Stand-ins are marked in front matter only** (`draft: true` becomes `<meta name="warraq:draft">` and `noindex` in
  the head, never visible text); `build --no-drafts` leaves them out.
- **Links are checked.** Relative `.md` links and images are resolved from the source tree; every root-relative
  link in the output must hit a file, and every `#fragment` a heading on the page it names. `build --strict` turns
  any problem into a non-zero exit, and so does a tool repository that fails to clone or a tool left without
  pages; CI and the Pages workflow run it.
- **Shared links look right.** Each page carries its own title, description, canonical URL, OpenGraph and Twitter
  card (the tool's card picture on its pages, a drawn card elsewhere), breadcrumb structured data, and `hreflang`
  pairs when a page has an English twin.
- **One layout for every tool** ([CONTRIBUTING.md](CONTRIBUTING.md)): `index`, `why` («ما الذي يميّزه؟», right after
  the overview), `install`, `quickstart`, `guides/*`, `faq`, and `docs/media/card.webp` for the landing card.

## Why a small generator rather than MkDocs Material

MkDocs Material was the obvious candidate: mature, good RTL support, built-in search. We chose a small generator
(about 1,000 lines of Python on Python-Markdown, Jinja2 and PyYAML) for four reasons:

1. **Arabic search that agrees with the tools.** The site's search must fold Arabic exactly as `arabic-bib` does
   (tashkeel and tatweel out, alef forms to ا, ة→ه, ى→ي, ؤ→و, ئ→ي, ء out, presentation forms, Persian letters,
   Eastern digits) and strip attached clitics (و ف ب ك ل ال) from the query. Material's search is built on lunr
   with per-language stemmers; matching our fold rule for rule would have meant a custom tokenizer inside a theme we
   do not control. Here the fold is one Python function and its JavaScript mirror, and a test runs both on the same
   strings (`tests/test_textnorm.py`, with Node). The index is plain JSON (250 KB, 69 KB gzipped), fetched on
   first search.
2. **The sync-and-overlay model is the core need**: seven repositories own their pages, drafts fill the gaps, links
   are checked across repositories. That is a few dozen lines on top of a generator, and awkward as a plugin.
3. **The family look, phone first, RTL first.** The pages share the palette of the library index and of
   benjelloun.dev, use logical CSS properties throughout, and keep a slim sticky bar on phones; one stylesheet, no
   theme to override.
4. **Small and fast**: three runtime dependencies; the whole site (about 80 pages with every tool's docs) builds
   in one second.

The cost is that we own the code and have no plugin ecosystem. The content is plain Markdown with YAML front matter
and Python-Markdown admonitions, so moving to MkDocs later stays cheap.

## Typography and themes

- **Readex Pro** (text) and **Kawkab Mono** (code), both under the SIL Open Font License 1.1, self-hosted as WOFF2
  subsets (Arabic and Latin ranges; 49 KB for the variable Readex Pro, 30 KB per Kawkab weight), with no third-party
  font service. Notices and licence: `assets/fonts/OFL.txt`.
- Light and dark themes follow the system; the moon button overrides it and remembers the choice.
- Arabic body text at 17 px with a 1.9 line height; code blocks run left to right inside right-to-left pages, with a
  copy button.
- Tables of four columns or more keep readable columns on a phone and scroll sideways with their first column in
  view; a table that scrolls is a named region the keyboard can reach.
- Search works from the keyboard: `/` or Ctrl-K opens it, the arrows walk the results, Escape closes it, and the
  number of results is announced to screen readers. `?q=…` in the address opens the site on a search.

<p>
<img src="docs/media/docs-desktop.webp" alt="A documentation page on a desktop" width="66%">
<img src="docs/media/search-phone.webp" alt="Arabic search on a phone" width="28%">
</p>

## Commands

| Command | Does |
|---|---|
| `warraq-site sync [--from local\|git]` | copy each tool's docs into `.cache/upstream/` (local: sibling checkouts next to this repo; git: shallow clones) and report what is missing |
| `warraq-site build [--sync] [--no-drafts] [--strict]` | build `_site/` with sitemap, robots.txt, CNAME, 404 and `search.json` |
| `warraq-site serve [--port N]` | preview on 127.0.0.1 only |
| `python scripts/check_walkthrough.py --tools ..` | run the walk-through's commands in page order on a copy of the sample |
| `python scripts/check_commands.py --tools .. [--readme]` | check every documented command's sub-commands and options against the tools' `--help` |
| `python scripts/audit_site.py --site _site [--axe axe.min.js]` | open every page in Chrome at phone and desktop widths (needs Playwright) |
| `python scripts/check_external_links.py` | ask every external link of the built site |
| `scripts/screenshots.sh OUT [URL] [paths…]` | phone and desktop screenshots with headless Chrome |
| `python scripts/make_social_card.py` | draw `assets/img/social.png`, the picture a shared link shows |
| `python sample/make_sample.py OUT --preview sheet.webp` | regenerate the walk-through sample (Pillow with libraqm) |

## The walk-through sample

`sample/warraq-sample/` holds four small PDFs (800 KB in all) typeset from classical public-domain texts (six
hadiths of al-Nawawī's *Arbaʿūn*, twelve lines of al-Shanfarā's *Lāmiyya*, the opening chapters of the
*Ājurrūmiyya*) and then "scanned" with the faults real scans have: dark scanner margins, slightly tilted pages, a
blank leaf, two-page spreads, an exact duplicate, and uploader-style file names. Each book has six or more pages of
text, enough for `safha` to measure one box for the whole book. `sample/make_sample.py` generates it; it is
released under CC0.

## What is checked

Measured on 2026-11-21 against the seven tools' checkouts, on Ubuntu 24.04 with Chrome 157:

| Check | Script | Result |
|---|---|---|
| The walk-through runs as written | `scripts/check_walkthrough.py` | 23 commands in page order on a copy of the sample, all exit 0; the folder ends as the last page shows it |
| Documented commands exist | `scripts/check_commands.py` | 208 commands on the tools' Arabic pages and on this site: every sub-command and option is in the tool's `--help` (`--readme` reads the English READMEs too) |
| Pages render on a phone and a desktop | `scripts/audit_site.py --axe` | 78 pages at 390 px and 1366 px: no sideways scroll, no console error, no image without alt text, one `h1` each; axe-core 4.10 WCAG A/AA rules pass in the light and the dark theme |
| Arabic search finds what readers type | `scripts/audit_site.py` | six queries with a dropped hamza, a tāʾ marbūṭa as hāʾ, an attached «و» and «ال», full vocalisation and Arabic-Indic digits each find their page |
| Links | `warraq-site build --strict`, `scripts/check_external_links.py` | internal links and anchors: 0 broken; 237 external links asked |

## Deploying

The site is built for GitHub Pages under the custom domain `warraq.benjelloun.dev`, served from the root (the build
writes the `CNAME` file). `.github/workflows/pages.yml` builds from shallow clones of every tool and deploys; it is
started by hand (`workflow_dispatch`), and its push trigger is one uncommented line away.

## Roadmap

- English pages as the tools write `docs/en/` (the language switch appears on a page as soon as its twin exists).
- A `repository_dispatch` from each tool repository so the site rebuilds when its docs change.
- The walk-through run in CI against the released tools (`scripts/check_walkthrough.py` with the real `uvx`).
- Versioned docs per tool once the tools reach 1.0.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Code is MIT; documentation text is CC BY 4.0; the sample is CC0.
