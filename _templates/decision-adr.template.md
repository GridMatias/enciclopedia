<!--
TEMPLATE — copy into <project>/<area>/<NNN>-<decision-slug>.md, never edit in place.
For decisions with consequences: architecture, vendors, contracts, methods.
A decision page is APPEND-ONLY: never rewrite a past decision, create a new page
with `supersedes` pointing here and set this one to `status: deprecated`
(SKILL.md §9.2).
The value of this page is the REASONING, not the conclusion: in six months the
conclusion will be obvious and the reasoning will be the only thing that helps.
Delete this comment when you copy the file. The parser tolerates it, the linter
warns (TEMPLATE-BANNER), and `python _tools/enc_new.py --print <slug>` strips it.
-->
---
id: <project-slug>/<area>/<NNN>-<decision-slug>
title: <NNN> — <decisione in una riga>
project: <project-slug>
type: decision
status: draft | active | stable | deprecated
lang: it
confidentiality: public | internal | restricted
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [decisione, <ambito>]
owner: <chi risponde di questa decisione>
sources: []
related: []
supersedes: []       # decisioni che questa sostituisce
superseded_by: ""    # compilato quando verrà sostituita
decision:
  date: <YYYY-MM-DD>
  status: proposta | accettata | rifiutata | sostituita
  deciders: [<chi ha deciso>]
  reversible: facile | costosa | irreversibile
  review_by: <YYYY-MM-DD o "">
---

# <NNN> — <decisione in una riga>

## Contesto

<Qual era il problema, quali vincoli erano dati (tempo, budget, normativa,
competenze), cosa era già stato deciso e non si poteva rimettere in discussione.>

## Opzioni valutate

| Opzione | Pro | Contro | Costo | Rischio |
|---|---|---|---|---|
| **A — <nome>** | <...> | <...> | <...> | <...> |
| **B — <nome>** | <...> | <...> | <...> | <...> |

## Decisione

**Scegliamo <opzione>.** <Formulazione precisa di cosa faremo.>

- **Perché:** <il criterio che ha deciso, non l'elenco dei pro>
- **Perché non le altre:** <la ragione specifica dello scarto, per ciascuna>
- **Reversibilità:** <facile | costosa | irreversibile> — <cosa servirebbe per tornare indietro>

## Conseguenze

- **Accettiamo:** <i costi e i limiti che questa scelta impone>
- **Si abilita:** <cosa diventa possibile>
- **Impatta:** `<area>/<pagina>.md` <cosa va allineato>

## Assunzioni da verificare

- [ ] <assunzione su cui la decisione poggia, e come la verificheremo>

## Quando riaprire questa decisione

<Il segnale concreto che la invaliderebbe: una metrica, una scadenza, un evento.>

## Riferimenti

- <fonti, benchmark, preventivi, pagine correlate>
