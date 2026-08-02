---
id: bottega-web/api/auth
title: Autenticazione
project: bottega-web
type: spec
status: active
lang: it
confidentiality: internal
owner: matix
created: 2026-06-10
updated: 2026-07-18
review_by: 2027-01-18
tags: [auth, sicurezza, sessione]
sources: []
related: ["../README.md"]
supersedes: []
---

# Autenticazione

## Contesto

Come vive la sessione di un cliente, dove stanno i token e cosa succede quando
scadono. È la pagina da leggere prima di toccare qualunque cosa riguardi il login.

## Contenuto

| Elemento | Dove vive | Durata |
|---|---|---|
| access token | memoria del browser, mai su disco | 15 minuti |
| refresh token | cookie `httpOnly`, `SameSite=Lax`, `Secure` | 30 giorni, ruotato a ogni uso |
| sessione server | tabella `sessions`, una riga per dispositivo | cancellata al logout |

Il valore reale del segreto di firma non sta qui: vive nel gestore di segreti
dell'hosting, e nell'enciclopedia compare solo come `<REDACTED>`.

## Decisioni

Append-only: le decisioni passate non si riscrivono, si superano.

- 2026-07-18 — **I refresh token vivono in cookie `httpOnly`, non in `localStorage`.** Motivo: mitigazione XSS. Supera la decisione del 2026-06-10.
- 2026-06-10 — ~~I refresh token stanno in `localStorage`~~ (superata il 2026-07-18: leggibile da qualunque script iniettato).

## Aperti / TODO

- [ ] Decidere la durata della sessione per i clienti abituali.

## Riferimenti

- `../README.md` — stato del progetto e stack
