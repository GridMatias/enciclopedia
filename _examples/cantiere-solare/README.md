---
id: cantiere-solare/README
title: Cantiere solare
project: cantiere-solare
type: hub
status: active
lang: it
confidentiality: internal
owner: matix
created: 2026-03-01
updated: 2026-07-20
tags: [energia, misure, fotovoltaico]
aliases: [impianto capannone, solar yard]
related: []
---

# Cantiere solare

**Scopo in una riga:** documentare l'impianto fotovoltaico del capannone, dalle misure di resa alla scelta dei componenti.

## Stato attuale

- **Fase:** in esercizio, monitoraggio
- **Ultimo avanzamento:** 2026-07-20 — chiusa la campagna di misure di marzo
- **Prossimo passo:** confrontare la resa estiva con quella dichiarata dal fornitore
- **Bloccanti:** nessuno

## Contesto e vincoli

- **Perché esiste:** decidere se ampliare l'impianto sul lato nord conviene davvero
- **Vincoli:** budget 6.000 EUR, nessun intervento strutturale sul tetto
- **Non-obiettivi:** accumulo a batteria, che è un progetto separato

## Mappa dei file — *quando leggere cosa*

| Pagina | Contenuto | Leggila quando... |
|---|---|---|
| [resa dei pannelli](ricerca/resa-pannelli.md) | misure di marzo 2026, resa per falda | la domanda riguarda produzione, irraggiamento o confronto tra falde |
| [001 — scelta dell'inverter](ricerca/001-scelta-inverter.md) | decisione sull'inverter, con alternative scartate | qualcuno chiede perché due inverter da 6 kW e non uno da 12 |
| [contratto fornitore](legale/contratto-fornitore.md) | condizioni, prezzi, garanzie (**riservato**) | servono clausole, garanzie o scadenze contrattuali |
| [offerta fornitore (importata)](_imported/offerta-fornitore/offerta-fornitore.md) | trascrizione dell'offerta originale | serve il testo esatto di quanto proposto dal fornitore |
| [dataset resa-2026](_data/resa-2026/datasheet.md) | schema, provenienza e limiti delle misure | prima di usare qualunque numero di resa |

## Decisioni chiave

| Data | Decisione | Dove |
|---|---|---|
| 2026-05-12 | Due inverter da 6 kW invece di uno da 12 kW | `ricerca/001-scelta-inverter.md` |

## Contraddizioni aperte

Voci registrate quando un item della cascata non è stato approvato (`SKILL.md` §8).
Ognuna va risolta o motivata: oltre `thresholds.contradictionMaxDays` diventa un errore del linter.

- 2026-07-20 — `ricerca/resa-pannelli.md` cita ancora la resa nominale di 400 Wp mentre il datasheet del fornitore dice 420 Wp: l'aggiornamento della pagina è stato approvato, quello della sintesi nel README no. Da chiudere alla prossima revisione.

## Glossario

| Termine | Significato |
|---|---|
| falda | una delle due superfici inclinate del tetto (nord, sud) |
| Wp | watt di picco: potenza nominale in condizioni standard |
| resa | energia prodotta in un giorno, in kWh |

## Domande aperte

- [ ] La resa della falda nord giustifica l'ampliamento? Servono i dati di giugno.

## Retention

`Retention:` documenti contrattuali → 10 anni dalla fine del rapporto (`_rules/governance.md` §6).

## Storico

Vedi `CHANGELOG.md`.
