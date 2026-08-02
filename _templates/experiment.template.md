<!--
TEMPLATE — copy into <project>/<area>/<experiment-slug>.md, never edit in place.
Rules: _rules/research-rules.md §3. A run without seed and environment is an
anecdote; a result without units and uncertainty is not a result.
Keep "Risultati" (what happened) and "Interpretazione" (what I think it means)
separate: it is the cheapest protection against fooling yourself.
Delete this comment when you copy the file. The parser tolerates it, the linter
warns (TEMPLATE-BANNER), and `python _tools/enc_new.py --print <slug>` strips it.
-->
---
id: <project-slug>/<area>/<experiment-slug>
title: Esperimento — <domanda in breve>
project: <project-slug>
type: experiment
status: draft | active | stable | deprecated
lang: it
confidentiality: public | internal | restricted
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [esperimento, <dominio>]
sources: []          # dataset slug, _originals/, DOI, pagina di preregistrazione
related: []
supersedes: []
experiment:
  hypothesis: "<ipotesi falsificabile>"
  preregistered: true | false          # se true, link in sources
  run_dates: ["<YYYY-MM-DD>"]
  operator: <chi ha eseguito>
  seed: <intero o "n/a">
  commit: "<hash>"
  command: "<comando esatto>"
  environment:
    os: "<Windows 11 26H1 / Ubuntu 24.04>"
    runtime: "<python 3.12.4, numpy 2.1.0>"
    hardware: "<CPU/GPU, RAM>"
    instrument: "<strumento + calibrazione YYYY-MM-DD>"
  inputs:
    - dataset: "<dataset-slug>"
      sha256: "<hash>"
  outputs:
    - "<figura o tabella prodotta>"
  outcome: confermata | smentita | inconcludente
---

# Esperimento — <domanda in breve>

## Domanda e ipotesi

- **Domanda:** <cosa vogliamo sapere>
- **Ipotesi:** <affermazione falsificabile>
- **Come sarebbe smentita:** <criterio deciso PRIMA di guardare i dati>
- **Preregistrazione:** <link alla pagina di piano, oppure "no: analisi esplorativa">

## Metodo

1. <passo, con i parametri espliciti>
2. <passo>

**Comando esatto:** `<comando>` · commit `<hash>` · seed `<n>`

## Ambiente

| Voce | Valore |
|---|---|
| OS / runtime | <...> |
| Librerie rilevanti | <nome versione> |
| Hardware | <...> |
| Strumento e calibrazione | <...> |

## Dati usati

| Dataset | `sha256` | Righe | Nota |
|---|---|---|---|
| `_data/<slug>/` | `<hash>` | <n> | <filtri applicati> |

## Risultati

Solo osservazioni. Unità sempre, incertezza sempre, `n` sempre.

| Metrica | Valore | Incertezza | n |
|---|---|---|---|
| <nome (unità)> | <valore> | ± <valore> (<tipo, k=2 / CI 95%>) | <n> |

`````markdown
![<alt: cosa mostra la figura>](<experiment-slug>-fig-01.png)
*Fig. 1 — <cosa mostra>. Prodotta da `<script>` commit `<hash>`, seed `<n>`, dataset `<slug>`. Barre d'errore = <definizione>.*
`````

## Interpretazione

<Cosa significano i risultati, tenuto separato dai risultati stessi.>

## Esito

- **Ipotesi:** confermata / smentita / inconcludente
- **Cosa esclude questo risultato:** <valore anche se negativo — non cancellare mai un esito negativo>
- **Cosa resta aperto:** <...>

## Deviazioni dal piano

- <YYYY-MM-DD> — <cosa è cambiato rispetto al metodo preregistrato e perché>

## Minacce alla validità

- <confondenti, campione, strumento, analisi multiple, criteri di stop>

## Prossimi passi

- [ ] <esperimento successivo o verifica>

## Riferimenti

- `_data/<slug>/datasheet.md`
- <DOI o pagina di letteratura>
