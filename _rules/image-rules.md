---
id: _rules/image-rules
title: Image rules
type: reference
status: active
updated: 2026-07-25
---

# Image rules

Extends `SKILL.md` §10. Read before creating, importing or referencing any image.

## 1. Placement and naming

- An image lives in the **same folder as the `.md` that references it**. No global asset folder, no subfolder per page.
- Filename: `<page-slug>-<kind>-NN.<ext>`
  - `kind`: `fig` (generic figure) · `dia` (diagram) · `shot` (screenshot) · `photo` · `logo` · `chart`
  - `NN`: zero-padded, sequential per page and per kind (`auth-fig-01.png`, `auth-shot-03.png`)
  - imported pages use `page-NN.png` for full-page renders
- Never rename an image without fixing every reference in the same proposal.
- Formats: `png` (diagrams, screenshots, transparency), `jpg` (photos), `webp` (large photos), `svg` (vector, only if generated as text), `gif` (only for animation). No `bmp`, `tiff`, `heic`, `pdf`.

## 2. Required markdown pattern

```markdown
![Descrizione utile per chi non vede l'immagine](auth-dia-01.png)
*Fig. 1 — Cosa mostra e perché conta.*
```

- `alt` is mandatory and descriptive; never `![](...)`, never `![image](...)`.
- Caption is mandatory: italic line immediately below, numbered `Fig. N`.
- Numbering is per page, in reading order, and must be renumbered if figures are reordered.
- If the image encodes structure (flow, architecture, schema), the page must also contain a text equivalent (Mermaid, ASCII, or a bullet list) so the knowledge survives without the binary.

## 3. Generated images

When an image is produced by the model:

1. Announce target path, filename (per §1), alt text and caption **before/with** the sync proposal.
2. Include the markdown snippet and the exact insertion point (which section, after which paragraph).
3. Record the generation prompt in the page's `sources` front matter (`sources: [gen: "<prompt>"]`) so it can be reproduced.
4. In read-only / no-filesystem mode, tell the user the exact folder and filename to save it as.
5. Never claim an image exists if it was not actually produced.

## 4. Imported and remote images

- Remote image: download next to the page if possible; otherwise record the URL in `sources` and add `- [ ] scaricare immagine` under `Aperti/TODO`. A hotlink is never the only copy.
- From a PDF/doc: extract only pages/figures that carry information, name them `page-NN.png`, and note the origin page in the caption (`*Fig. 3 — … (pag. 12 dell'originale)*`).
- Screenshots must be cropped to the relevant area; redact tokens, emails, keys, personal data before saving. If redaction is impossible, do not save.

## 5. Hygiene

- **Orphan image** (file present, referenced by no page) → defect: propose a reference or removal.
- **Broken reference** (page points to a missing file) → defect: propose regeneration or removal of the reference.
- Keep files reasonably small (target < 1 MB, < 2000 px on the long side) unless detail is essential.
- Never store the same image twice: reference the existing one with a relative path across folders only if unavoidable, otherwise keep one canonical copy and link the page.
- `enc: check <project>` must report orphans and broken references.

## 6. Rule log (append only, newest first)

### 2026-07-25 — Bootstrap
Conventions above adopted as defaults.
Scope: global.
