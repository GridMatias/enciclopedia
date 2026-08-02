---
id: _rules/pdf-composition
title: PDF composition rules
type: reference
status: active
updated: 2026-07-25
---

# PDF composition rules

Read **before** generating any PDF (`SKILL.md` §11.2). The encyclopedia never
stores PDFs as knowledge: a PDF is a *render* of selected `.md` pages plus their
figures, written to `_exports/<project>/<name>-YYYY-MM-DD.pdf`.

Everything below marked `default` is a provisional convention: the user's own
dated entries in §5 override it. When a needed aspect is undefined, **ask once**
and propose persisting the answer in §5.

## 1. Pre-build checklist (mandatory)

1. Which pages, in which order? List them explicitly and get confirmation.
2. Which figures are included, and do all referenced images exist?
3. Language, title, subtitle, author, date on the cover.
4. Target: print (margins, no dark backgrounds) or screen (links clickable)?
5. Any user rule in §5 that applies to this project or document type?
6. Restate the plan in one short block, then build.

## 2. Structure (default)

- Cover page: title, subtitle, project, date `YYYY-MM-DD`, no page number.
- Table of contents when the document exceeds 4 pages or 3 source pages.
- Body: each source `.md` starts on a new page; its `# H1` becomes the chapter title.
- Heading depth: include up to `###` in the TOC.
- Figures keep their `Fig. N` numbering, renumbered continuously across the whole document; captions are kept below the image.
- Tables are not split across pages when they fit on one page.
- Footer: `<document title> · <page>/<total>`; header: current chapter.
- Final page: `Fonti` — the list of source pages with their `updated` dates, so the render is traceable.

## 3. Style (default)

- A4 portrait, margins 20 mm (25 mm inner for print/binding).
- Body 11 pt serif or system sans, line height 1.4; code 9.5 pt monospace with light background.
- Monochrome-safe: never rely on colour alone to convey meaning.
- Images centred, max width = text width, never upscaled beyond native resolution.
- No decorative graphics, no watermark unless requested.

## 4. Build recipe (default, Pandoc)

If a converter is unavailable, output the assembled Markdown plus this command
instead of pretending the PDF was produced.

```bash
pandoc pagina-1.md pagina-2.md \
  --resource-path=.:./area1:./area2 \
  --toc --toc-depth=3 --number-sections \
  -V geometry:a4paper,margin=20mm -V lang=it \
  --metadata title="Titolo" --metadata date="2026-07-25" \
  -o "../_exports/<project>/<name>-2026-07-25.pdf"
```

Notes: `--resource-path` must include every folder holding referenced images,
because image paths are relative to their own page.

## 5. User rules (append only, newest first)

Format: `### YYYY-MM-DD — <title>` · rule · `Scope: global | <project> | <doc type>`.

### 2026-07-25 — Bootstrap
No user-specific PDF rules yet. Ask before assuming a house style; defaults in
§2–§4 apply meanwhile.
Scope: global.
