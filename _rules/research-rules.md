---
id: _rules/research-rules
title: Research rules
type: reference
status: active
lang: en
created: 2026-07-25
updated: 2026-07-25
---

# Research rules

For scientific and engineering work where a claim must survive scrutiny months
later. Read before writing an experiment page, a literature note, or any page
that states a measured number. Core duties: `SKILL.md` §15; defaults in
`_meta/config.json` → `research`.

## 1. The claim chain

Every quantitative claim must be walkable backwards:

```
claim (page)  ->  figure or table  ->  dataset (datasheet.md)  ->  raw source (_originals/ or DOI)
```

Each arrow is a `sources` entry. If any arrow is missing, the claim is marked
`assunzione` (`SKILL.md` §7.2) or removed. An agent must refuse to state a number
as established when the chain is broken, and say which link is missing.

## 2. Numbers

- **Units always**, in the text and in table headers (`massa (kg)`), never implied by context.
- **Uncertainty always** for measurements: `12.4 ± 0.3 mm (k=2)` or an explicit interval, plus what kind it is (standard deviation, standard error, CI, instrument spec).
- Significant digits reflect the uncertainty, not the float the tool printed. `3.4 ± 0.2`, never `3.41729 ± 0.2`.
- `n` is stated wherever a statistic appears; a percentage without its denominator is not a result.
- Rounding, exclusions and outlier handling are declared where the number is presented, not buried in a script.
- Never recompute a published number silently: if your calculation disagrees with the page, surface the conflict (`SKILL.md` §7.3).

## 3. Reproducibility

An `experiment` page is complete only with:

| Field | Why |
|---|---|
| hypothesis / question | stops post-hoc storytelling |
| method, step by step | someone else must be able to repeat it |
| parameters, including **seed** | a run without a seed is an anecdote |
| environment (versions, hardware, OS, driver, instrument + calibration date) | most silent failures live here |
| exact command and commit hash | the link between the page and the code |
| inputs (dataset slugs + `sha256`) | the same command on different data is a different result |
| outputs (figures, tables, artefact paths) | what the claim rests on |
| result **and** interpretation, kept visibly separate | protects the observation from the story |

Use `_templates/experiment.template.md`.

## 4. Negative and null results are kept

They are the cheapest knowledge in the encyclopedia and the most often lost.
`status: stable`, `type: experiment`, and a `## Esito` that says plainly what did
not work and what it rules out. Deleting a failed experiment because it is
"noise" is forbidden: the next person will pay for it again.

## 5. Literature

- One page per source (`type: paper-note`), `_templates/paper-note.template.md`.
- Identify by **DOI first**, URL + access date otherwise. Record the citation key used in `references.bib`.
- Separate three layers explicitly: *what the source says*, *what I take from it*, *what I doubt about it*. Never let a quotation drift into your own voice.
- Quotations are marked as quotations with a locator (page, section). Anything else is a paraphrase and must be flagged as such.
- Retracted or superseded sources: `status: deprecated`, keep the page, add why. Never delete a citation that a claim used.
- `references.bib` lives at the project root (`extensions.data` allows `.bib`) and is a record: append-only, keys never reused.

## 6. Preregistration and analysis discipline

- When the analysis plan matters (hypothesis testing, A/B tests, clinical-style work), write it **before** the data arrives, `type: spec`, and never edit it afterwards: deviations go in a dated `## Deviazioni` section of the experiment page.
- Exploratory analysis is labelled exploratory. A hypothesis found in the data is a hypothesis, not a result.
- Multiple comparisons, stopping rules and excluded runs are declared; silent exclusion is data fabrication with extra steps.

## 7. Figures

- A figure is reproducible: caption or `sources` records the script path, commit, seed and dataset slug that produced it (`image-rules.md` §3).
- Axes labelled with units, scale stated, error bars defined in the caption.
- Never re-use a figure whose underlying dataset has been superseded: regenerate or mark the page `status: deprecated`.

## 8. Rule log (append only, newest first)

### 2026-07-25 — Bootstrap
Claim chain, units and uncertainty, reproducibility fields, retention of negative
results, DOI-first literature notes, preregistration discipline and figure
provenance adopted.
Scope: global.
