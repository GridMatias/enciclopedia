---
id: _rules/governance
title: Governance rules
type: reference
status: active
lang: en
created: 2026-07-25
updated: 2026-07-25
---

# Governance rules

For encyclopedias shared by more than one person, or holding material with legal,
contractual or personal-data weight. A solo user can ignore §4–§6 until needed;
§2 and §3 apply from day one because retrofitting classification is painful.

Core duties are in `SKILL.md` §15; vocabularies and defaults in
`_meta/config.json` → `governance`.

## 1. Roles

| Role | Duty |
|---|---|
| **Owner** (`owner` front matter) | one named person per page or project: answers for accuracy, reviews on schedule |
| **Contributor** | proposes changes; may write only after the owner's or the user's approval |
| **Approver** | the person whose `OK` an agent waits for; by default the user driving the conversation |
| **Agent** | never an owner, never an approver. It proposes, quotes, and records |

`owner: unassigned` is allowed but is a defect the linter reports: unowned pages
rot first.

## 2. Classification

| Level | Meaning | Handling |
|---|---|---|
| `public` | can be published as-is | no restriction |
| `internal` | fine inside the organisation | not quoted into `public` pages or public exports |
| `restricted` | contracts, personal data, security material, unpublished results | never inlined elsewhere; linked only; excluded from exports unless explicitly requested and recorded |

Rules:

1. **Classification travels upward, never downward.** A page inherits the highest level of anything it quotes. An export inherits the highest of its sources; if that is `restricted`, the export must say so on the cover.
2. Default for a new page: `governance.defaultConfidentiality` (`internal`). Downgrading a page requires an explicit instruction and a `CHANGELOG` line.
3. A `public` page may **link** to a `restricted` page; it may not summarise its restricted content. When in doubt, link and say the detail is restricted.
4. Redact rather than exclude when the useful part is separable: keep the fact, drop the identifier.

## 3. Personal data

- Store the minimum: no identifiers that the page does not need to make its point.
- Pseudonymise (`Cliente A`, `Soggetto 07`) and keep the mapping **outside** the encyclopedia. Record in the page that a mapping exists and who holds it.
- Never store special-category data (health, biometrics, beliefs, sexual life, criminal records) unless the project explicitly requires it, with `confidentiality: restricted` and the lawful basis written in the page.
- Screenshots and figures: crop and redact before saving (`image-rules.md` §4).
- On a deletion request from a data subject: find every page and record referencing the person (`enc: check` + grep on the pseudonym), propose the removals as one batch, and record the erasure in `CHANGELOG.md` without restating the deleted data.

## 4. Review cycle

- Front matter `review_by: <YYYY-MM-DD>` on pages whose truth decays (prices, processes, dependencies, roadmaps). Default horizon `governance.reviewIntervalDays` (180 days).
- `reviewed_by: [<name>, <YYYY-MM-DD>]` records who last confirmed it.
- The linter lists pages past `review_by`. An agent asked about such a page must say `⚠ scaduta la revisione il <date>` before using it as ground truth.
- Reviewing means confirming or superseding, never bumping the date to silence the warning.

## 5. Change flow with more than one person

```
proposal (agent, SKILL.md §8)
  -> branch enc/<topic>
  -> commit: one topic per commit, message = the proposal's "why"
  -> pull request: the proposal table pasted in the description
  -> review by the page owner (CODEOWNERS routes it)
  -> merge
```

- Approval is recorded where it can be audited: PR review, or the commit message when working solo (`approved-by: <user> in conversation <date>`).
- Never mix a protocol change (`SKILL.md`, `_rules/`, `_meta/`) with a content change in the same PR: they have different reviewers and different risk.
- Conflicting edits on the same page: the owner decides; the losing version is preserved as a dated note if it carries reasoning worth keeping.

## 6. Retention and deletion

- Retention is declared per project in its `README.md` (`Retention:` line) and per record in its datasheet.
- `retention: permanent | <n> years | until <event>` on pages holding contractual or regulatory material.
- Deleting anything with a retention obligation requires an explicit instruction naming the obligation being discharged; the deletion is recorded in `CHANGELOG.md`.
- Prefer `status: deprecated` + `supersedes` over deletion: the encyclopedia's value is that it remembers why things changed.

## 7. Audit trail

Three layers, all mandatory:

1. **git** — who changed what, when, reversible.
2. **`<project>/CHANGELOG.md`** — why, in human language, with the paths touched.
3. **the proposal** — what was replaced by what, and who approved it.

An agent that applies changes without leaving all three is out of compliance with
this file, regardless of the quality of the content.

## 8. Rule log (append only, newest first)

### 2026-07-25 — Bootstrap
Roles, three-level classification with upward-only travel, PII minimisation,
review cycle, branch/PR flow, retention and the three-layer audit trail adopted.
Scope: global.
