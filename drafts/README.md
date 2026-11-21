# drafts/

A page placed at `drafts/<tool>/ar/<name>.md` (or `drafts/<tool>/media/<file>`) is used for a tool until the tool's
own repository has a `docs/ar/<name>.md`; the tool's file then replaces it. Mark such a page `draft: true` in its
front matter: the build then keeps it out of search engines and `build --no-drafts` leaves it out.

Every tool writes its own pages today, so this folder holds no page.
