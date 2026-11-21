<!-- Thank you. A small change with a clear reason is the easiest to merge. -->

## What changes for a reader or a user

## How it was checked

- [ ] `pytest`, `ruff check` and `warraq-site build --strict` pass
- [ ] a walk-through or tool-page command changed: `scripts/check_walkthrough.py` / `scripts/check_commands.py` ran
- [ ] templates, CSS or JS changed: the page was opened at phone width in light and dark (`scripts/audit_site.py`)
- [ ] `README.md` and `CHANGELOG.md` say the same thing as the code
