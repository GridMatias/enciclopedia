---
id: _rules/OUTPUT-RULES
title: Output rules
type: reference
status: active
updated: 2026-07-25
---

# Output rules

What may be produced, where it goes, and how durable user preferences are
recorded. Read this file whenever a request involves *producing an artifact*
(page, figure, document, export) rather than just answering.

## 1. Artifact classes

| Class | Stored in the encyclopedia? | Location | Notes |
|---|---|---|---|
| Markdown page | yes — it *is* the knowledge | `<project>/<area>/<page>.md` | front matter required (`SKILL.md` §9.1) |
| Image (png/jpg/webp/svg/gif) | yes | next to the referencing page | naming + caption per `image-rules.md` |
| Imported document (pdf, docx, slides) | converted to Markdown | `<project>/_imported/<slug>/` | `SKILL.md` §11.1 |
| Retained original | yes, as a **record** | `<project>/_originals/` | kept with its `sha256` when it has legal, contractual or scientific value — `data-rules.md` §5 |
| Dataset / tabular data | yes, as a **record** | `<project>/_data/<slug>/` | `datasheet.md` mandatory; inline if text and small, pointer otherwise — `data-rules.md` |
| Notebook / script | no | the real repository | documented by a page recording command, commit and outputs — `data-rules.md` §7 |
| Generated document (pdf, docx, pptx, csv, zip) | no — derived output | `_exports/<project>/` | never cited as a source |
| Code / config belonging to a real repo | no | the actual repository | the encyclopedia documents it, does not host it |
| Protocol tooling (linter, hooks, CI) | yes, as **infrastructure** | `_tools/`, `_meta/`, `.github/` | never knowledge, never cited as a source |
| Secrets, credentials, personal data | never | outside the encyclopedia | redact to `<REDACTED>` |

## 2. Hard rules

1. **Knowledge** is only `.md` and image files. **Records** (data, retained originals) are allowed under `_data/` and `_originals/` per `data-rules.md`, always with a datasheet or a checksum. **Infrastructure** is tooling and is never knowledge. Anything else is converted or written to `_exports/`.
2. A generated artifact never becomes a source of truth. If it must be quoted later, the underlying `.md` is quoted instead.
3. `_exports/` is disposable and reproducible: everything in it must be rebuildable from pages + figures + these rules.
4. Every artifact produced in a turn appears in the sync proposal, including images and exports, with its exact path.
5. If a requested format has no rule file yet, ask for the missing specifics **once**, then propose persisting the answer here or in a dedicated `_rules/<format>-rules.md` (`SKILL.md` §11.5).

## 3. Default answer-shape preferences

Applied unless the user says otherwise in the turn:

- Reply in the language of the prompt; keep technical terms untranslated.
- Prefer tables and short bullets to long prose; no filler.
- Show only the relevant excerpt of a file, not the whole file.
- Code blocks always carry a language tag.
- Dates ISO `YYYY-MM-DD`; never invent a date.

## 4. Rule log (append only, newest first)

Durable preferences the user has stated over time. Format:

`### YYYY-MM-DD — <short title>` then the rule, then `Scope:` (global | project slug | format).

### 2026-07-25 — Informed consent on updates
No file is ever touched without an explicit `OK` from the user, granted **per
item**. Every proposal must declare, topic by topic, what the page says now (with
its date) and what it will say, classified `ADD` / `SUPERSEDE` / `REPLACE` /
`REMOVE` / `MOVE`, plus what is lost and which other pages are left
contradicting it. No autonomous writing in any mode, no "auto" shortcut, no
batching that hides a replacement inside an addition. See `SKILL.md` §8.
Scope: global.

### 2026-07-25 — Bootstrap
Encyclopedia created. Markdown + images only. The agent must always propose file
updates and never write without explicit approval.
Scope: global.
