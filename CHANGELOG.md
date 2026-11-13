# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-13

### Added
- `warraq-site` generator: Markdown with front matter → static RTL site; tool docs overlaid on local drafts;
  relative `.md` and media links resolved; root-relative links checked; sitemap, robots, CNAME, 404.
- Arabic-aware client search: one fold shared by the Python index builder and the browser, tested for parity.
- `warraq-site sync` pulls each tool's `docs/ar`, `docs/en` and `docs/media` from sibling checkouts or shallow clones.
- Landing page (path from scans to shelf, the seven tools, what Warraq brings together, the usual way vs Warraq),
  a seven-step walk-through on a generated public-domain sample, and an about page.
- Readex Pro and Kawkab Mono as self-hosted WOFF2 subsets; light and dark themes; phone-first layout.
