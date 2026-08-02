---
id: _exports/README
title: Exports
type: reference
status: active
updated: 2026-07-25
---

# `_exports/` — generated artifacts

Renders produced **from** the encyclopedia: PDFs, DOCX, slide decks, CSVs.

- **Not knowledge.** Nothing here is ever read as a source or cited in an answer. The `.md` pages and their images remain the single source of truth.
- **Disposable.** Everything here must be rebuildable from pages + figures + `_rules/`. Deleting the folder must lose nothing.
- **Naming:** `_exports/<project>/<name>-YYYY-MM-DD.<ext>`.
- **Git-ignored** by design (see `.gitignore`).
- Build rules for PDFs live in `_rules/pdf-composition.md`; ask before inventing a house style.
