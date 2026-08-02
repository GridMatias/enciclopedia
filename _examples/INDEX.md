---
id: INDEX
title: Encyclopedia Index (example vault)
type: reference
updated: 2026-07-25
projects: 2
---

# Encyclopedia Index

Global map of every project. **This is the first file to read and, most turns,
the only one needed to decide what else to read.**

## Projects

| Project (slug) | Path | Status | Updated | Tags | One-line purpose |
|---|---|---|---|---|---|
| `cantiere-solare` | `cantiere-solare/` | active | 2026-07-20 | energia, misure | Impianto fotovoltaico sul capannone: misure di resa e scelta dei componenti. |
| `bottega-web` | `bottega-web/` | active | 2026-07-18 | web, api | Negozio online della bottega: catalogo, ordini, autenticazione. |

Status vocabulary: `idea` · `active` · `paused` · `shipped` · `archived`.

## Routing hints

Keyword → project. Ambiguous terms list every candidate, so the agent knows it
must ask instead of guessing. Keywords are listed **in every language actually
used** (`_rules/scale-rules.md` §6).

| Keyword / alias | Project(s) |
|---|---|
| fotovoltaico, pannelli, panels, resa, yield, irraggiamento | `cantiere-solare` |
| inverter, moduli, kwp | `cantiere-solare` |
| fornitore, offerta, contratto, supplier, contract | `cantiere-solare` |
| shop, negozio, catalogo, catalogue, ordini, orders | `bottega-web` |
| auth, autenticazione, login, token, sessione, session | `bottega-web` |
| costi, costs, budget | `cantiere-solare`, `bottega-web` |

## Cross-project references

| Topic | Where it lives | Used by |
|---|---|---|
| Regole di output e immagini | `_rules/` della vera enciclopedia | tutti |
| Dati e originali conservati | `_rules/data-rules.md` | `cantiere-solare` |

## Maintenance

- Every project creation, rename, archival or significant update patches this
  file in the same sync proposal (`SKILL.md` §8).
- If this file disagrees with the folder tree, the tree wins.
