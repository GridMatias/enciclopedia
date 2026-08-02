---
id: bottega-web/README
title: Bottega web
project: bottega-web
type: hub
status: active
lang: it
confidentiality: internal
owner: matix
created: 2026-06-02
updated: 2026-07-18
tags: [web, api, negozio]
aliases: [shop, negozio online, bottega]
related: []
---

# Bottega web

**Scopo in una riga:** il negozio online della bottega: catalogo, ordini e autenticazione dei clienti.

## Stato attuale

- **Fase:** sviluppo
- **Ultimo avanzamento:** 2026-07-18 — rivista la gestione della sessione
- **Prossimo passo:** collegare il catalogo al gestionale
- **Bloccanti:** nessuno

## Contesto e vincoli

- **Perché esiste:** vendere anche fuori dall'orario del negozio fisico
- **Vincoli:** un solo sviluppatore, hosting condiviso, niente carte salvate in casa
- **Non-obiettivi:** app mobile nativa

## Stack / strumenti

| Ambito | Scelta | Note |
|---|---|---|
| backend | Python + FastAPI | già noto, deploy semplice |
| database | PostgreSQL | transazioni sugli ordini |
| pagamenti | provider esterno | nessun dato di carta sui nostri server |

## Mappa dei file — *quando leggere cosa*

| Pagina | Contenuto | Leggila quando... |
|---|---|---|
| [autenticazione](api/auth.md) | come vivono sessione e token | la richiesta riguarda login, sessione, scadenze o sicurezza dell'accesso |

## Decisioni chiave

| Data | Decisione | Dove |
|---|---|---|
| 2026-07-18 | Refresh token in cookie httpOnly | `api/auth.md#decisioni` |

## Glossario

| Termine | Significato |
|---|---|
| refresh token | credenziale a vita lunga che rinnova la sessione |
| httpOnly | cookie non leggibile da JavaScript |

## Domande aperte

- [ ] Quanto deve durare la sessione di un cliente abituale?

## Storico

Vedi `CHANGELOG.md`.
