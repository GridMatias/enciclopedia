---
id: _rules/governance-mapping
title: Governance mapping (fill this in with your counsel)
type: reference
status: draft
lang: en
created: 2026-07-25
updated: 2026-07-25
---

# Governance mapping

**This protocol is not legal advice, and it was not written by lawyers.**
`_rules/governance.md` gives you *operational controls* - classification, review
dates, retention fields, an erasure workflow, an audit trail. What those controls
must satisfy is a question for whoever answers for compliance in your
organisation. This page is where that answer is written down, once, so the agent
stops improvising it.

Until it is filled in, an agent asked a compliance question must say plainly:
*«qui l'enciclopedia ha solo controlli operativi; l'obbligo va confermato da chi
risponde della conformità»* - and never present a default as a requirement.

## 1. Who decides

| Role | Person / function | Contact |
|---|---|---|
| Data protection / privacy | <nome o funzione> | <come raggiungerlo> |
| Legal / contracts | <...> | <...> |
| Records retention owner | <...> | <...> |
| Security incident contact | <...> | <...> |

## 2. Obligations that actually bind us

One row per obligation. The point is the **source**: an obligation without a
source is an opinion, and the agent must treat it as one.

| Obligation | Source (law, contract, policy, standard) | What it forces us to do | Where it lands in the encyclopedia |
|---|---|---|---|
| <es. conservare le fatture 10 anni> | <riferimento preciso> | <azione concreta> | `retention:` su <pagine/record> |
| <es. cancellare i dati di un cliente su richiesta> | <riferimento> | <procedura> | `_rules/governance.md` §3 + `CHANGELOG` |

## 3. Retention schedule

| Class of material | Retention | Trigger that starts the clock | Disposal method |
|---|---|---|---|
| <contratti> | <n anni> | <fine del rapporto> | <come si cancella e chi lo registra> |
| <dati di misura> | <...> | <...> | <...> |
| <note interne> | <...> | <...> | <...> |

`retention:` in a page's front matter must quote a class from this table.
`enc_lint` reports a project declaring `Retention:` without naming its source.

## 4. Personal data held here

| What | Why it is needed | Lawful basis (as confirmed by §1) | Pseudonymised? | Where the mapping lives |
|---|---|---|---|---|
| <...> | <...> | <...> | <si/no> | <fuori dall'enciclopedia> |

If this table is empty, the encyclopedia should contain no personal data at all -
and `PII` findings from the linter are then defects, not false positives.

## 5. What an agent must never do here

- Assert that a retention period, a lawful basis or an erasure duty *is* what §2 does not say.
- Quote the defaults in `governance.md` as if they were obligations.
- Decide that something may be deleted because a page says so: deletion needs the instruction, the obligation being discharged, and a `CHANGELOG` line (`governance.md` §6).

## 6. Rule log (append only, newest first)

### 2026-07-25 — Bootstrap
Created after the observation that the retention and GDPR wording in
`governance.md` was written by non-lawyers and read as compliance. The operational
controls stay; the obligations move here, sourced, or are absent.
Scope: global.
