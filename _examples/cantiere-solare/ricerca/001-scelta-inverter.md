---
id: cantiere-solare/ricerca/001-scelta-inverter
title: 001 — Due inverter da 6 kW invece di uno da 12 kW
project: cantiere-solare
type: decision
status: active
lang: it
confidentiality: internal
owner: matix
created: 2026-05-12
updated: 2026-05-12
tags: [decisione, inverter, impianto]
sources: ["../_imported/offerta-fornitore/offerta-fornitore.md"]
related: ["../README.md", "resa-pannelli.md"]
supersedes: []
decision:
  date: 2026-05-12
  status: accettata
  deciders: [matix]
  reversible: "difficilmente: cablaggio e staffe sono dimensionati sui due apparati"
---

# 001 — Due inverter da 6 kW invece di uno da 12 kW

## Contesto

Le due falde hanno esposizione e ombreggiamento diversi. L'offerta del fornitore
propone entrambe le configurazioni allo stesso prezzo complessivo.

## Decisione

- 2026-05-12 — **Due inverter trifase da 6 kW, uno per falda.** Motivo: MPPT indipendenti, così l'ombreggiamento della falda nord non trascina giù la sud; e un guasto lascia in esercizio metà impianto.

## Alternative scartate

| Alternativa | Perché scartata |
|---|---|
| Un inverter da 12 kW | un solo MPPT sulle due falde: l'ombreggiamento mattutino della nord penalizza tutto l'impianto |
| Micro-inverter per modulo | costo superiore al budget e 24 punti di guasto sul tetto |

## Conseguenze

- Manutenzione: due apparati da monitorare invece di uno.
- Misure: la resa è leggibile per falda, che è ciò che rende confrontabile `resa-pannelli.md`.

## Riferimenti

- `../_imported/offerta-fornitore/offerta-fornitore.md` — testo dell'offerta su cui si è deciso
- `resa-pannelli.md` — le misure che questa scelta ha reso possibili
