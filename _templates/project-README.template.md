<!--
TEMPLATE — copy into <project>/README.md, never edit in place.
Replace every <...>. Delete sections that are truly not applicable.
Section headings are written in the project's language (here: Italian).
This file is the project hub: the agent reads it on EVERY request about the
project, so it must stay accurate and short. Details go in the pages.
Delete this comment when you copy the file. The parser tolerates it, the linter
warns (TEMPLATE-BANNER), and `python _tools/enc_new.py --print <slug>` strips it.
-->
---
id: <project-slug>/README
title: <Nome progetto>
project: <project-slug>
type: reference
status: idea | active | paused | shipped | archived
lang: it
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [<tag>, <tag>]
aliases: [<altri nomi con cui chiamo questo progetto>]
---

# <Nome progetto>

**Scopo in una riga:** <cosa fa e per chi>.

## Stato attuale

- **Fase:** <idea | prototipo | sviluppo | in produzione | fermo>
- **Ultimo avanzamento:** <YYYY-MM-DD> — <cosa è cambiato>
- **Prossimo passo:** <la prossima azione concreta>
- **Bloccanti:** <cosa impedisce di procedere, o "nessuno">

## Contesto e vincoli

- **Perché esiste:** <problema che risolve>
- **Vincoli:** <budget, tempo, tecnici, legali>
- **Non-obiettivi:** <cosa esplicitamente NON facciamo>

## Stack / strumenti

| Ambito | Scelta | Note |
|---|---|---|
| <es. frontend> | <es. React> | <perché> |

## Mappa dei file — *quando leggere cosa*

| Pagina | Contenuto | Leggila quando... |
|---|---|---|
| `<area>/<pagina>.md` | <una riga> | <trigger: la richiesta riguarda X> |

## Decisioni chiave

Le decisioni vivono nelle pagine; qui solo i link, dal più recente.

| Data | Decisione | Dove |
|---|---|---|
| <YYYY-MM-DD> | <sintesi in una riga> | `<area>/<pagina>.md#decisioni` |

## Glossario

| Termine | Significato |
|---|---|
| <termine> | <definizione breve> |

## Domande aperte

- [ ] <domanda che serve risolvere, con chi/cosa la sblocca>

## Riferimenti esterni

- `[<Titolo>](<url>) (letto <YYYY-MM-DD>)` — <perché conta; togli i backtick quando l'URL è reale>

## Storico

Vedi `CHANGELOG.md`.
