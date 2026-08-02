---
id: _tools/README
title: Tools
type: reference
status: active
lang: en
created: 2026-07-25
updated: 2026-07-25
---

# `_tools/` — enforcement

Infrastructure, **not knowledge**: never cited as a source, never counted against
the retrieval budget (`SKILL.md` §1.4). Python 3.9+, **zero dependencies**.

| Tool | What it does | Writes? |
|---|---|---|
| `enc_lint.py` | integrity audit: front matter contract, broken links, orphan images and pages, missing captions, secrets, dataset/original discipline, `INDEX.md` drift, review dates, hub sharding | **nothing** |
| `enc_index.py` | builds `_index/manifest.json` and prints a refreshed `INDEX.md` table | only `_index/manifest.json` (disposable, git-ignored) |
| `enc_bootstrap.py` | verifies that `SKILL.md`, `_meta/config.json`, `_install/systemPrompt.json` and `PROTOCOL-CHANGELOG.md` state the same version and facts | **nothing** |
| `enc_import.py` | prints the paste-ready Markdown conversion of an incoming document: pdf/docx/html natively where it can, audio/video via a local whisper if installed, a recipe otherwise; front matter with `trust: untrusted` and the source `sha256` pre-filled | **nothing** |
| `enc_setup.py` | first run of the starter kit: wiring report plus per-client snippets carrying the folder's real path; `--apply` performs git init, hooks and the index build | only with `--apply`, and only git/index wiring — never knowledge |
| `hooks/pre-commit` | runs the self-test, the linter and the consistency check before a commit | nothing |
| `../_tests/test_lint.py` | builds a synthetic encyclopedia with 17 planted defects and asserts the linter catches all of them and flags nothing on the well-formed page | nothing (temp folder only) |

## Why they never fix anything

A tool that silently rewrote pages would break the one guarantee the protocol
makes: **nothing changes without the user's informed `OK`**. So the tools report,
the agent turns findings into a proposal (`SKILL.md` §8), and the user approves.
The single exception is `_index/manifest.json`, which is generated, disposable and
git-ignored — deleting it loses nothing.

## Usage

```bash
python _tools/enc_lint.py                    # whole encyclopedia
python _tools/enc_lint.py my-app             # one project
python _tools/enc_lint.py --json             # machine-readable, for agents
python _tools/enc_lint.py --warnings-as-errors

python _tools/enc_index.py                   # write manifest + print INDEX table
python _tools/enc_index.py --dry-run
python _tools/enc_index.py --stats

python _tools/enc_bootstrap.py --print       # canonical facts
python _tools/enc_bootstrap.py --check       # exit 1 on drift

python _tests/test_lint.py                   # does the linter still catch what it claims?
```

Exit codes: `0` clean, `1` findings that must be addressed, `2` bad usage.

## Enable the git hook

```bash
git config core.hooksPath _tools/hooks
```

One command, no framework. To bypass once: `git commit --no-verify` — and then fix
what you skipped.

## Scope: content pages only

Link, image, caption, length and front matter checks run **only on pages inside a
project folder**. The protocol's own documentation (root files, `_rules/`,
`_templates/`) is prose *about* the encyclopedia: it is full of illustrative paths
and `<placeholder>` values on purpose, so linting it would produce nothing but
false positives. Those files are still scanned for secrets, and examples inside
code fences are excluded everywhere.

## Severity policy

- **ERROR** — the encyclopedia is factually broken: a link that goes nowhere, a duplicated `id`, a dataset without a datasheet, a secret in the text. CI fails.
- **WARN** — it still works but is decaying: orphan page, missing caption, review overdue, hub that needs sharding, unowned page.

New checks are cheap to add and belong here rather than in `SKILL.md`: the
protocol states the rule, the linter proves it.
