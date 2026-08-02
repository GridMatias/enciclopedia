---
id: cantiere-solare/_data/resa-2026/datasheet
title: Dataset — resa impianto marzo 2026
project: cantiere-solare
type: dataset
status: stable
lang: it
confidentiality: internal
owner: matix
created: 2026-03-04
updated: 2026-07-20
tags: [dataset, resa, misure]
sources: []
related: ["../../ricerca/resa-pannelli.md"]
data:
  storage: inline
  location: "data.csv"
  format: csv
  delimiter: ","
  encoding: utf-8
  rows: 6
  columns: 5
  bytes: 281
  sha256: "830177a7c06def13da7d2e9761a8741affa06a2d13cd7726b6c2c7c2de31f318"
  obtained: 2026-03-04
  snapshot_of: statico
  licence: "dati propri, uso interno"
  usage_terms: "non pubblicabili senza anonimizzare l'indirizzo dell'impianto"
---

# Dataset — resa impianto marzo 2026

## Identità

| Campo | Valore |
|---|---|
| Slug | `resa-2026` |
| Versione | `v1` |
| Responsabile | matix |
| Dove vive | `data.csv`, qui accanto |
| Ottenuto il | 2026-03-04 |

## Provenienza

- **Origine:** log dell'inverter, esportati manualmente dal portale del costruttore.
- **Metodo di raccolta:** una riga per giorno e per falda, tre giornate consecutive di marzo 2026.
- **Licenza e vincoli:** dati propri; l'indirizzo dell'impianto non compare e non va aggiunto.
- **Catena:** dato grezzo, nessuna trasformazione applicata.

## Schema

| Colonna | Tipo | Unità | Dominio / range | Mancanti | Significato |
|---|---|---|---|---|---|
| `data` | date | ISO `YYYY-MM-DD` | 2026-03-01 … 2026-03-03 | nessuno | giorno della misura |
| `impianto` | cat | — | `tetto-nord` \| `tetto-sud` | nessuno | falda del tetto |
| `irraggiamento_kwh_m2` | float | kWh/m² | 0 … 8 | nessuno | irraggiamento giornaliero sul piano dei moduli |
| `resa_kwh` | float | kWh | 0 … 400 | nessuno | energia prodotta nella giornata |
| `temperatura_c` | float | °C | −10 … 45 | nessuno | temperatura media dell'aria |

Una riga = una falda in un giorno.

## Dimensioni e integrità

- Righe: `6` (esclusa l'intestazione) · Colonne: `5` · Byte: `281`
- `sha256`: `830177a7c06def13da7d2e9761a8741affa06a2d13cd7726b6c2c7c2de31f318` (verificato il 2026-07-20 con `python _tools/enc_verify.py`)
- Chiave primaria: `data` + `impianto` · Duplicati noti: nessuno

## Elaborazioni applicate

1. 2026-03-04 — esportazione dal portale, nessuna correzione — `export manuale, nessun comando`

## Limiti, bias, usi vietati

- **Limiti:** tre giornate soltanto, tutte di marzo; una coperta (03/03).
- **Bias noti:** il sensore di irraggiamento è montato sulla falda sud, quindi il valore della nord è stimato dal costruttore.
- **Non usare per:** stimare la produzione annua o dimensionare un ampliamento.

## Statistiche di riferimento

Solo valori calcolati sull'**intero** dataset.

| Metrica | Valore | Calcolata il | Come |
|---|---|---|---|
| Somma `resa_kwh` tetto-sud | 784.4 kWh | 2026-07-20 | somma diretta delle 3 righe |
| Somma `resa_kwh` tetto-nord | 573.1 kWh | 2026-07-20 | somma diretta delle 3 righe |

## Chi dipende da questo dato

| Pagina | Cosa afferma basandosi su questo dataset |
|---|---|
| `../../ricerca/resa-pannelli.md` | la falda nord rende il 27% in meno della sud |

## Aperti / TODO

- [ ] Aggiungere la campagna di giugno come dataset separato, con `sources` verso questo.
