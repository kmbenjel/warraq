# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `scripts/check_walkthrough.py` runs the walk-through's commands in page order on a copy of the sample;
  `scripts/check_commands.py` checks every documented sub-command and option against the tools' `--help`;
  `scripts/audit_site.py` opens every page in Chrome at phone and desktop widths (overflow, console errors, alt
  text, axe-core, Arabic search queries); `scripts/check_external_links.py`; `scripts/make_social_card.py`.
- OpenGraph image and Twitter card on every page, `WebSite` and `BreadcrumbList` structured data, `hreflang` pairs
  with `x-default`, `noindex` on the 404 page and on stand-in pages.
- The link check covers `#fragment` anchors. `build --strict` also fails when a tool's repository does not clone or
  a tool has no pages.
- `nav_title` in front matter: a shorter sidebar label.

### Changed
- The walk-through sample is three books of six or more text pages each (800 KB), so that the crop tool measures
  one box per book; the walk-through's commands are the tools' own and the plan moves the cropped files.
- Search: Escape closes the box, the arrow keys move focus through the results, the result count is announced.
- Tables that overflow are focusable named regions; tables of four columns or more scroll on a phone with their
  first column in view.
- Header links from an English page to an Arabic-only page carry `hreflang`.

### Removed
- The stand-in pages in `drafts/`: every tool writes all its pages.

## [0.1.0] - 2026-11-13

### Added
- `warraq-site` generator: Markdown with front matter → static RTL site; tool docs overlaid on local drafts;
  relative `.md` and media links resolved; root-relative links checked; sitemap, robots, CNAME, 404.
- Arabic-aware client search: one fold shared by the Python index builder and the browser, tested for parity.
- `warraq-site sync` pulls each tool's `docs/ar`, `docs/en` and `docs/media` from sibling checkouts or shallow clones.
- Landing page (path from scans to shelf, the seven tools, what Warraq brings together, the usual way vs Warraq),
  a seven-step walk-through on a generated public-domain sample, and an about page.
- Readex Pro and Kawkab Mono as self-hosted WOFF2 subsets; light and dark themes; phone-first layout.
