---
id: _meta/README
title: Meta — machine configuration
type: reference
status: active
lang: en
created: 2026-07-25
updated: 2026-07-25
---

# `_meta/` — machine configuration

Infrastructure, **not knowledge**. Never cited as a source in an answer, never
counted against the retrieval budget as a "page", never translated.

| File | Purpose |
|---|---|
| `config.json` | single source of truth: paths, retrieval budgets and profiles, thresholds, controlled vocabularies, conventions |
| `frontmatter.schema.json` | JSON Schema for page front matter (phase 2, used by `_tools/enc_lint.py`) |

## Rules

- Change a path, a budget, a threshold or a vocabulary **here first**, then align `SKILL.md` and regenerate `_install/systemPrompt.json`.
- Bump `protocolVersion` together with the `version` in `SKILL.md` front matter and add an entry to `PROTOCOL-CHANGELOG.md`.
- JSON only, no comments: use `$comment` keys when something needs explaining.
- If `SKILL.md` and this file disagree, **this file wins for numbers and vocabularies**; `SKILL.md` wins for behaviour and invariants. Report the mismatch instead of silently picking one.
