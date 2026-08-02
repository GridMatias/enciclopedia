<!--
TEMPLATE — copy into <project>/<area>/<citation-key>.md, never edit in place.
One page per source. Rules: _rules/research-rules.md §5.
Keep the three voices separate and never let them blend:
  "Cosa dice" = the source · "Cosa ne prendo" = you · "Dubbi" = your critique.
Delete this comment when you copy the file. The parser tolerates it, the linter
warns (TEMPLATE-BANNER), and `python _tools/enc_new.py --print <slug>` strips it.
-->
---
id: <project-slug>/<area>/<citation-key>
title: <Autore Anno> — <titolo breve>
project: <project-slug>
type: paper-note
status: draft | active | stable | deprecated
lang: it
confidentiality: public | internal | restricted
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [letteratura, <tema>]
sources:
  - "doi:<10.xxxx/xxxxx>"
  - "<url> (letto <YYYY-MM-DD>)"
related: []
citation:
  key: "<autore2026parola>"        # chiave in references.bib, mai riusata
  authors: "<Cognome, N.; Cognome, N.>"
  year: <YYYY>
  venue: "<rivista / conferenza / preprint>"
  doi: "<10.xxxx/xxxxx>"
  type: article | preprint | book | chapter | report | standard | thesis | dataset
  peer_reviewed: true | false
  retracted: false
  original_file: "_originals/<YYYY>-<citation-key>.pdf"
---

# <Autore Anno> — <titolo breve>

## Identificazione

| Campo | Valore |
|---|---|
| Autori | <...> |
| Anno / sede | <YYYY> — <rivista> |
| DOI | `<10.xxxx/xxxxx>` |
| Peer review | sì / no (preprint) |
| Chiave BibTeX | `<citation-key>` |
| Originale | `_originals/<file>.pdf` (`sha256` nel file affianco) |

## Cosa dice la fonte

Voce dell'autore. Le citazioni letterali sono marcate con il locatore.

- **Domanda affrontata:** <...>
- **Metodo:** <disegno, campione, n, strumenti>
- **Risultati principali:** <con unità e incertezza come riportate>
- **Conclusione degli autori:** <...>

> «<citazione letterale>» (p. <n>)

## Cosa ne prendo per il progetto

Voce tua. Cosa cambia per noi, concretamente.

- <implicazione operativa o teorica>
- **Numeri che potrei riusare:** <valore + unità + dove nell'originale>
- **Metodo che potrei riusare:** <...>

## Dubbi e limiti

- **Validità:** <campione, confondenti, generalizzabilità>
- **Conflitti di interesse / finanziamento:** <...>
- **Cosa NON dimostra:** <l'inferenza che qualcuno potrebbe fare a torto>
- **Fonti in disaccordo:** `<altra-paper-note>.md`

## Stato nella letteratura

- Citato da / risponde a: <...>
- Superato da: <...> *(se sì, `status: deprecated` e nota qui, mai cancellare)*

## Riferimenti

- `references.bib` → `<citation-key>`
- Pagine che si appoggiano a questa fonte: `<area>/<pagina>.md`
