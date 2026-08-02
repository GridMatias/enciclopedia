---
id: _rules/data-rules
title: Data and originals rules
type: reference
status: active
lang: en
created: 2026-07-25
updated: 2026-07-25
---

# Data and originals rules

Governs **records**: datasets, tabular files, and retained source documents.
Core invariant in `SKILL.md` §11.4; numbers come from `_meta/config.json`.

Why records are a separate class: knowledge is prose you read and cite, data is
evidence you *sample*. Confusing the two is how an agent burns 50k tokens on a
CSV and then hallucinates a mean.

## 1. Layout

```
<project>/_data/<dataset-slug>/
  datasheet.md          # REQUIRED — the only file the agent reads by default
  data.csv              # the data, only if text and under the inline thresholds
  data-fig-01.png       # figures about the data live here, next to the datasheet
<project>/_originals/
  2026-07-25-contratto-fornitore.pdf
  2026-07-25-contratto-fornitore.sha256
```

- One folder per dataset. `datasheet.md` is mandatory and is a normal page (`type: dataset`) with full front matter.
- Never store a data file outside `_data/`, and never store a dataset without its datasheet. A bare file is a defect the linter reports.
- Derived tables (cleaned, aggregated) are new datasets with their own datasheet and a `sources` pointer to the parent. Never overwrite raw data.

## 2. Store inline or point to it?

| Condition | Decision |
|---|---|
| Text format in `extensions.data`, ≤ `inlineDataMaxBytes` (1 MB) and ≤ `inlineDataMaxRows` (5000) | store in place, versioned in git |
| Text but larger | store a **pointer**: absolute path / URL / DOI + `sha256` + row count in the datasheet |
| Binary (`.xlsx`, `.parquet`, `.sav`, `.dta`, `.h5`, images-as-data) | convert to a text format if lossless and small enough, otherwise pointer; the original goes to `_originals/` |
| Personal or restricted data | never inline. Pointer only, `confidentiality: restricted`, and record the lawful basis for holding it |
| Live/streaming source | pointer + query or endpoint + the date of the snapshot the pages rely on |

A pointer is not a weaker record: with `sha256`, row count and schema in the
datasheet, an answer stays verifiable and reproducible without the bytes.

## 3. Reading discipline (this is the token-safety rule)

1. Read `datasheet.md`. In most turns this is enough — schema, units and limits are what the answer needs.
2. If the data itself is needed: read at most `thresholds.dataSampleRows` rows plus the header, and **state in the answer that it was a sample of N rows out of M**.
3. Never compute a statistic from a sample and present it as a property of the dataset. Either the datasheet already records it, or you propose a script and let its output become a page.
4. Never paste raw rows into an answer beyond the minimum needed to illustrate a point; never paste rows containing personal data.
5. If the datasheet and the file disagree (row count, columns), report the drift and propose updating the datasheet. The **file** is the truth about itself.

## 4. Datasheet content (required sections)

Use `_templates/dataset-datasheet.template.md`. Minimum:

- **Identity:** name, slug, version, date obtained, owner.
- **Provenance:** where it comes from, who produced it, how it was collected, licence and the terms of use that bind it.
- **Schema:** every column with type, unit, allowed range, missing-value code, and what it actually means. This is the part that makes the data usable a year later.
- **Size:** rows, columns, bytes, `sha256`.
- **Processing:** every transformation applied, in order, with the script or command.
- **Limits and biases:** sampling frame, known errors, what it must not be used for.
- **Linkage:** which pages, figures and claims depend on it.

An undocumented column is worse than a missing column: it invites silent misuse.

## 5. Originals and retention

- The original file is retained under `<project>/_originals/` whenever it has legal, contractual, scientific or archival value. Conversion to Markdown (§11.1) is *in addition*, never instead.
- Record `sha256` beside it (`<name>.sha256`) and cite it in the importing page's `sources`.
- Naming: `YYYY-MM-DD-<slug>.<ext>` using the document's own date when known.
- Never edit an original. Corrections live in the derived page, with a dated note.
- Large binaries: git-lfs, or an external store referenced by pointer. Never `.gitignore` them into invisibility — that hides an obligation instead of managing it.
- Deletion of an original requires an explicit user instruction and a `CHANGELOG` entry stating who asked and why.

## 6. Checksums

```bash
# PowerShell
Get-FileHash -Algorithm SHA256 data.csv | Select-Object -ExpandProperty Hash
# Python, portable
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" data.csv
```
Record it lowercase, 64 hex chars, in the datasheet field `sha256`.

## 7. Notebooks, scripts and code

- `.ipynb` is not knowledge: keep the notebook in the real repository, and store in the encyclopedia a page describing purpose, inputs, outputs and conclusions, with a link and a commit hash.
- Same for scripts: the encyclopedia documents them and records the exact command and commit used to produce a figure or a table.
- A figure produced by code records, in its caption or the page's `sources`, the script path plus commit and the seed (`_rules/research-rules.md`).

## 8. Rule log (append only, newest first)

### 2026-07-25 — Bootstrap
Records introduced as a third file class alongside knowledge and infrastructure.
Thresholds and extensions as in `_meta/config.json`. Datasheet mandatory,
wholesale reading forbidden, originals retained rather than ignored.
Scope: global.
