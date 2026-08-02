<!--
TEMPLATE — copy into <project>/<area>/README.md, never edit in place.
Create an area hub ONLY past the sharding threshold (_rules/scale-rules.md §2).
Once it exists, the project README must list AREAS, not the pages of this area:
two file maps for the same pages will drift and the agent will trust the stale one.
Keep this file short: it is read on almost every request about the area.
Delete this comment when you copy the file. The parser tolerates it, the linter
warns (TEMPLATE-BANNER), and `python _tools/enc_new.py --print <slug>` strips it.
-->
---
id: <project-slug>/<area>/README
title: <Area> — <progetto>
project: <project-slug>
type: hub
status: active
lang: it
confidentiality: public | internal | restricted
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [hub, <area>]
related: ["../README.md"]
---

# <Area> — <progetto>

**Cosa copre quest'area, in una riga:** <ambito e confini>.

## Mappa dei file — *quando leggere cosa*

| Pagina | Contenuto | Leggila quando... |
|---|---|---|
| `<pagina>.md` | <una riga> | <trigger concreto> |

## Decisioni locali

| Data | Decisione | Dove |
|---|---|---|
| <YYYY-MM-DD> | <sintesi> | `<pagina>.md#decisioni` |

## Domande aperte dell'area

- [ ] <domanda>

## Fuori scope

<Cosa NON sta qui e dove sta invece: `../<altra-area>/README.md`.>
