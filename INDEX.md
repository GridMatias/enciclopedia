---
id: INDEX
title: Encyclopedia Index
type: reference
updated: 2026-07-25
projects: 0
---

# Encyclopedia Index

Global map of every project. **This is the first file to read and, most turns,
the only one needed to decide what else to read.** Keep it small: one row per
project, no prose. Details live in `<project>/README.md`.

## Projects

| Project (slug) | Path | Status | Updated | Tags | One-line purpose |
|---|---|---|---|---|---|
| _(nessun progetto ancora)_ | | | | | |

Status vocabulary: `idea` · `active` · `paused` · `shipped` · `archived`.

## Routing hints

Keyword → project. Used to route a request without opening files. Add every
term, alias, product name, client name, filename or acronym the user actually
says. Ambiguous terms must list all candidates so the agent knows to ask.

| Keyword / alias | Project(s) |
|---|---|
| _(vuoto)_ | |

## Cross-project references

Shared assets, conventions or decisions that span projects.

| Topic | Where it lives | Used by |
|---|---|---|
| Output rules (md, immagini, pdf) | `_rules/OUTPUT-RULES.md`, `image-rules.md`, `pdf-composition.md` | tutti |
| Dati, dataset, originali conservati | `_rules/data-rules.md` | progetti con dati |
| Riservatezza, revisioni, flusso PR | `_rules/governance.md` | progetti condivisi |
| Metodo scientifico, citazioni, riproducibilità | `_rules/research-rules.md` | progetti di ricerca |
| Soglie di scala e hub per area | `_rules/scale-rules.md` | progetti grandi |
| Page/project skeletons | `_templates/` | tutti |
| Numeri, path e vocabolari autoritativi | `_meta/config.json` | tutti |
| Linter e generatore di indice | `_tools/` | manutenzione |

## Maintenance

- Every project creation, rename, archival or significant update must patch this
  file in the same sync proposal (`SKILL.md` §8).
- If this file disagrees with the folder tree, the tree wins: propose a
  correction here.
- `enc: check` audits rows against the tree.
