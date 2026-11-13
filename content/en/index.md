---
layout: landing
title: Warraq
tagline: open tools for digital heritage libraries
description: Seven open-source tools to build and care for digital heritage libraries, from a folder of scans to a catalogue that works offline on a phone.
hero:
  kicker: Open-source tools for digital heritage libraries
  title: From a folder of scans to a catalogued library in your pocket
  lead: Seven tools for librarians, students and researchers. Clean scanned pages without touching their pixels, name every book by one bibliographic rule, match it to the big catalogues with evidence, reorganise files with plans you review before they run and can undo, and carry the whole library as one offline catalogue on your phone.
  primary: {label: Start the walk-through, url: /tutorial/}
  secondary: {label: Meet the tools, url: "#tools"}
stats:
  - {label: volumes in the library they were built on, value: "16,700"}
  - {label: independent tools that fit together, value: "7"}
  - {label: open source under, value: MIT}
path:
  title: From scans to shelf
  lead: Each step is a tool that works on its own; together they form one pipeline. Start where you are.
  steps:
    - title: A folder of scans
      text: Scanned PDFs named by uploaders and scan numbers, with black margins, tilted pages and blank leaves. Most personal libraries start here.
    - title: Clean the pages
      text: One crop box for the whole book, deskewed pages, two-page spreads split, extra pages dropped, and every image left exactly as it was.
      tools: [safha]
    - title: Name the books
      text: One rule for every name (title, author, editor, publisher) with death years and Hijri dates, and an audit that flags what breaks the rule.
      tools: [arabic-bib]
    - title: Match and prove
      text: Each file is traced to its source by exact size, each book matched to Shamela, Waqfeya and archive.org, and duplicates proven by sampled bytes.
      tools: [turath-match, turath-catalog]
    - title: Reorganise
      text: Moves, renames and deletes go into a plan you see before it runs, applied to disk, phone or any remote, with a log and an undo.
      tools: [planfs]
    - title: A catalogue in your pocket
      text: The whole folder becomes one HTML file that the phone's browser opens offline, with search, sections and authors by century.
      tools: [pocketshelf]
  note: When an AI agent runs the long jobs, agent-workbench keeps you in charge with review pages whose ticks and comments flow back to the agent.
cards:
  title: The seven tools
  lead: Each tool has full documentation in Arabic, with an English README in its repository.
values:
  title: What no single tool gives you
  lead: Every step has good tools. Warraq brings these seven principles together.
  items:
    - {title: Arabic first, text: "Built for Arabic titles, author names with kunya, nisba and laqab, Hijri dates and right-to-left text, while working in any language and script."}
    - {title: Lossless, text: "Cropped pages are never re-encoded: the frame changes, the pixels do not."}
    - {title: "Planned, logged, reversible", text: "No move, rename or delete without a plan you see first, an append-only log and a one-command undo."}
    - {title: Offline on a phone, text: "The catalogue is one self-contained file that works in an Android browser with no server and no network."}
    - {title: Evidence for every match, text: "A file is tied to a source only by exact size or sampled bytes, never by a similar title."}
    - {title: An open dataset, text: "Works, editions, authors and editors as open data under CC BY 4.0, metadata only."}
    - {title: Proven on a real library, text: "Built and refined on a 16,700-volume library before being made general."}
compare:
  title: The usual way and the Warraq way
  lead: How each step usually goes when a library is managed by hand, and how it goes with Warraq.
  head: [Step, The usual way, With Warraq]
  rows:
    - [Cleaning pages, "Cropping page by page, or an export that redraws the images", "One box per book, images untouched, page drops undoable"]
    - [Naming, "Uploader names and scan numbers, everyone's own style", "One rule for title, author, editor, publisher, audited"]
    - [Matching, "Title search on websites; similar titles let wrong books in", "Exact size ties a file to its source; editions matched by editor and publisher"]
    - [Duplicates, "Deleted by name or size alone", "Deleted after sampled bytes prove them identical"]
    - [Reorganising, "Drag and drop in a file manager, no record", "A reviewed plan, a log of every change, undo"]
    - [Cataloguing, "A spreadsheet, or an app that needs a server", "One HTML file that works offline on a phone"]
    - [Working with an agent, "Watching the terminal, typing notes into the chat", "A review page whose ticks and comments reach the agent"]
story_title: Born from a real library
---

Warraq began as a personal library on an Android phone: Arabic scanned books gathered from open sources such as Waqfeya and archive.org, until it passed sixteen thousand volumes in forty sections. A library that size needs tools — to crop margins for small screens, unify names, prove duplicates, keep a record of every move, and carry the whole collection as a catalogue in a pocket. These tools are what came out of that work, made general: every rule specific to the first library became an optional profile called `warraq`.

The documentation is in Arabic first; each tool's repository has an English README.

[Browse the library they were built on](https://benjelloun.dev/library)
