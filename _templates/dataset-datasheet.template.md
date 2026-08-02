<!--
TEMPLATE — copy into <project>/_data/<dataset-slug>/datasheet.md, never edit in place.
This page is the ONLY thing an agent reads by default about the dataset
(SKILL.md §11.4). If a column is undocumented here, it will be misused.
Headings in the project language (here: Italian). Front matter keys stay English.
Delete this comment when you copy the file. The parser tolerates it, the linter
warns (TEMPLATE-BANNER), and `python _tools/enc_new.py --print <slug>` strips it.
-->
---
id: <project-slug>/_data/<dataset-slug>/datasheet
title: Dataset — <nome leggibile>
project: <project-slug>
type: dataset
status: draft | active | stable | deprecated
lang: it
confidentiality: public | internal | restricted
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [dataset, <dominio>]
sources: []          # dataset genitore, DOI, URL, file in _originals/
related: []          # pagine che usano questo dataset
data:
  storage: inline | pointer
  location: "data.csv"            # oppure path assoluto / URL / DOI
  format: csv | tsv | json | jsonl | parquet | xlsx | other
  delimiter: ","
  encoding: utf-8
  rows: <n>
  columns: <n>
  bytes: <n>
  sha256: "<64 hex>"
  obtained: <YYYY-MM-DD>
  snapshot_of: <YYYY-MM-DD o "statico">
  licence: "<licenza o 'proprietario, uso interno'>"
  usage_terms: "<cosa la licenza vieta>"
---

# Dataset — <nome leggibile>

## Identità

| Campo | Valore |
|---|---|
| Slug | `<dataset-slug>` |
| Versione | `<v1>` |
| Responsabile | <chi risponde di questo dato> |
| Dove vive | `<data.csv>` oppure `<path/URL/DOI>` |
| Ottenuto il | <YYYY-MM-DD> |

## Provenienza

- **Origine:** <chi lo ha prodotto, con quale strumento o processo>
- **Metodo di raccolta:** <come, quando, su quale popolazione o sistema>
- **Licenza e vincoli:** <licenza + cosa NON si può fare>
- **Catena:** <se derivato, il dataset genitore e la trasformazione applicata>

## Schema

Ogni colonna va documentata. Una colonna non documentata è un invito all'errore.

| Colonna | Tipo | Unità | Dominio / range | Mancanti | Significato |
|---|---|---|---|---|---|
| `<nome>` | int / float / string / date / bool / cat | <es. mm, kg, EUR, adimensionale> | <es. 0–100, enum: a\|b\|c> | <es. vuoto, `NA`, `-999`> | <cosa misura davvero> |

## Dimensioni e integrità

- Righe: `<n>` · Colonne: `<n>` · Byte: `<n>`
- `sha256`: `<hash>` (verificato il <YYYY-MM-DD>)
- Unità di osservazione: <una riga = cosa>
- Chiave primaria: `<colonna/e>` · Duplicati noti: <n o "nessuno">

## Elaborazioni applicate

In ordine, con il comando esatto: chi rilegge deve poter rifare tutto.

1. <YYYY-MM-DD> — <operazione> — `<comando o script + commit>`

## Limiti, bias, usi vietati

- **Limiti:** <copertura, periodo, granularità>
- **Bias noti:** <selezione, strumento, non risposta>
- **Errori noti:** <valori sospetti, colonne inaffidabili>
- **Non usare per:** <inferenze che il dato non sostiene>

## Statistiche di riferimento

Solo valori calcolati sull'**intero** dataset, con la data e il comando usato.
Mai numeri stimati da un campione.

| Metrica | Valore | Calcolata il | Come |
|---|---|---|---|
| <es. media di `x`> | <valore + unità> | <YYYY-MM-DD> | `<comando>` |

## Chi dipende da questo dato

| Pagina | Cosa afferma basandosi su questo dataset |
|---|---|
| `<area>/<pagina>.md` | <affermazione> |

## Aperti / TODO

- [ ] <verifica, colonna da chiarire, licenza da confermare>
