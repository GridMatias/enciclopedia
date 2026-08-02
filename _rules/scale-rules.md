---
id: _rules/scale-rules
title: Scale rules
type: reference
status: active
lang: en
created: 2026-07-25
updated: 2026-07-25
---

# Scale rules

How the encyclopedia stays cheap to navigate as it grows from 1 project to 200.
Thresholds live in `_meta/config.json` → `thresholds`.

The failure mode we are preventing: a hub so long that reading it costs more than
the answer, and an `INDEX.md` so wide that routing becomes guessing.

## 1. Growth stages

| Stage | Size | Structure |
|---|---|---|
| **S1 seed** | 1–5 projects, < 25 pages each | flat: `INDEX.md` + project `README.md` + area folders. No area hubs. |
| **S2 working** | 6–40 projects | as S1, plus `_index/manifest.json` regenerated on demand; routing hints become mandatory, not optional |
| **S3 large** | > `maxPagesPerHub` (25) pages in one project | that project's areas get their own `README.md` hub; the project hub lists **areas**, not pages |
| **S4 institutional** | > `maxProjectsPerIndex` (40) projects | `INDEX.md` keeps one row per project but the routing table moves to `INDEX-ROUTING.md`; optional domain indexes `INDEX-<domain>.md`, linked from `INDEX.md` |

Crossing a threshold is a proposal like any other: the agent detects it, explains
the cost, and offers the split. It never reorganises silently.

## 2. Area hubs (S3)

An area hub is a page with `type: hub` that carries only:

- one line on what the area covers,
- the file map of that area with the "read this when…" hint per page,
- open questions local to the area.

Retrieval then reads: `INDEX.md` → project `README.md` → **one** area hub → the pages.
Three cheap files instead of one enormous one. Use `_templates/area-README.template.md`.

The project hub, once sharded, must stop listing individual pages: duplicated
file maps drift within a week and the agent starts trusting the stale one.

## 3. Manifest (all stages from S2)

`python _tools/enc_index.py` writes `_index/manifest.json`: every page's front
matter, headings, outbound links, plus orphan/broken-link statistics. Agents may
read it *instead of* climbing the ladder (`SKILL.md` §5), which turns routing into
one file read regardless of vault size.

It is disposable and git-ignored: regenerate, never hand-edit. If its `generated`
timestamp is older than the newest file it describes, treat it as stale and fall
back to the ladder.

## 4. Splitting pages and projects

- Page > `pageSplitLines` (400) → propose a split by topic, keeping the original as a hub-like index if inbound links are many.
- A project that has grown two clearly independent purposes → propose splitting it into two projects with a shared `related` link, rather than a folder with two personalities.
- Never split to hit a number: split when a reader would have to skip half the page to find the part that matters.

## 5. Archiving

- `status: archived` on the project, moved to the bottom of `INDEX.md` in an `## Archived` section, routing keywords kept (people still ask about dead projects).
- Archived projects are excluded from the default retrieval scope: read them only when named explicitly, and say that the source is archived and possibly obsolete.

## 6. Multi-language routing

Routing hints must carry the keywords in **every language the user actually uses**,
mapped to the same project. A page written in Italian and a question asked in
English must still meet.

## 7. Rule log (append only, newest first)

### 2026-07-25 — Bootstrap
Stages S1–S4, area hubs, manifest-first retrieval, archiving and multilingual
routing adopted. Thresholds in `_meta/config.json`.
Scope: global.
