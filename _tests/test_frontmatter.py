#!/usr/bin/env python3
"""Pin the front matter grammar: what must parse, and what must fail loudly.

The old parser was best-effort on a YAML subset. Measured, it turned
`tags: ["a, b", "c"]` into three items, a folded `title: >` into an empty list, a
duplicate key into a silent overwrite, and a UTF-8 BOM into "this page has no
front matter". Every one of those is a wrong value that nothing downstream could
detect - the schema, the index and the classification all read the same lie.

The rule now: parse the documented subset exactly, and refuse everything else
with a named problem. This file is the contract.

Run:  python _tests/test_frontmatter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL_ROOT / "_tools"))

import enc_fm  # noqa: E402

BOM = "\ufeff"


def fm(body: str) -> str:
    return "---\n" + body + "\n---\n\n# Titolo\n"


# name -> (document, expected data subset)
VALID = {
    "plain scalars": (fm("id: p/a/x\ntitle: Nota\nlang: it"),
                      {"id": "p/a/x", "title": "Nota", "lang": "it"}),
    "quoted comma inside a list": (fm('tags: ["a, b", "c"]'),
                                   {"tags": ["a, b", "c"]}),
    "empty inline list": (fm("sources: []"), {"sources": []}),
    "block list": (fm("related:\n  - ../README.md\n  - ../altra/pagina.md"),
                   {"related": ["../README.md", "../altra/pagina.md"]}),
    "block list at column zero": (fm("tags:\n- alfa\n- beta"),
                                  {"tags": ["alfa", "beta"]}),
    "nested map": (fm('data:\n  storage: inline\n  rows: 6\n  sha256: "abc"'),
                   {"data": {"storage": "inline", "rows": 6, "sha256": "abc"}}),
    "nested map, four spaces": (fm("experiment:\n    seed: 42\n    outcome: confermata"),
                                {"experiment": {"seed": 42, "outcome": "confermata"}}),
    "two levels of nesting": (fm("experiment:\n  seed: 42\n  environment:\n"
                                 '    os: "Windows 11"\n    runtime: "python 3.12"'),
                              {"experiment": {"seed": 42,
                                              "environment": {"os": "Windows 11",
                                                              "runtime": "python 3.12"}}}),
    "list of mappings": (fm('inputs:\n  - dataset: "resa-2026"\n    sha256: "abc"'),
                         {"inputs": [{"dataset": "resa-2026", "sha256": "abc"}]}),
    "nested list of scalars": (fm("data:\n  columns:\n    - data\n    - resa"),
                               {"data": {"columns": ["data", "resa"]}}),
    "folded scalar": (fm("description: >\n  prima riga\n  seconda riga"),
                      {"description": "prima riga seconda riga"}),
    "literal scalar": (fm("description: |\n  prima\n  seconda"),
                       {"description": "prima\nseconda"}),
    "quoted colon": (fm('title: "Auth: la sessione"'), {"title": "Auth: la sessione"}),
    "hash inside a value": (fm("title: C# e derivati"), {"title": "C# e derivati"}),
    "trailing comment": (fm("lang: it  # lingua della pagina"), {"lang": "it"}),
    "booleans and numbers": (fm("draft: true\nrows: 12\nratio: 0.75"),
                             {"draft": True, "rows": 12, "ratio": 0.75}),
    "quoted date stays a string": (fm('updated: "2026-07-25"'), {"updated": "2026-07-25"}),
    "two-letter code that looks boolean": (fm("lang: no"), {"lang": "no"}),
    "UTF-8 BOM": (BOM + fm("id: p/a/x"), {"id": "p/a/x"}),
    "leading blank lines": ("\n\n" + fm("id: p/a/x"), {"id": "p/a/x"}),
    "leading HTML comment (template banner)":
        ("<!--\nTEMPLATE - copy me\n-->\n" + fm("id: p/a/x"), {"id": "p/a/x"}),
    "CRLF line endings": (fm("id: p/a/x\ntitle: Nota").replace("\n", "\r\n"),
                          {"id": "p/a/x", "title": "Nota"}),
    "closing dots": ("---\nid: p/a/x\n...\n\n# Titolo\n", {"id": "p/a/x"}),
}

# name -> (document, expected problem code)
INVALID = {
    "unquoted colon": (fm("title: Auth: la sessione"), "FM-UNQUOTED-COLON"),
    "duplicate key": (fm("title: Primo\ntitle: Secondo"), "FM-DUPLICATE-KEY"),
    "duplicate nested key": (fm("data:\n  rows: 1\n  rows: 2"), "FM-DUPLICATE-KEY"),
    "tab indentation": (fm("tags:\n\t- alfa"), "FM-TAB"),
    "anchor": (fm("base: &ancora valore"), "FM-UNSUPPORTED"),
    "alias": (fm("copia: *ancora"), "FM-UNSUPPORTED"),
    "merge key": (fm("<<: *base"), "FM-UNSUPPORTED"),
    "flow mapping": (fm('data: {rows: 6}'), "FM-UNSUPPORTED"),
    "single-pair map in a list": (fm('sources: [gen: "un prompt"]'), "FM-UNSUPPORTED"),
    "unterminated front matter": ("---\nid: p/a/x\n\n# Titolo\n", "FM-UNTERMINATED"),
    "nesting beyond the limit": (fm("data:\n  block:\n    piu:\n      giu: troppo"),
                                 "FM-DEEP-NESTING"),
    "garbage line": (fm("id: p/a/x\nquesta riga non e' una coppia"), "FM-SYNTAX"),
}

NO_FRONT_MATTER = {
    "plain markdown": "# Solo un titolo\n\nTesto.\n",
    "html comment only": "<!-- nota -->\n\n# Titolo\n",
}


def main() -> int:
    failures = []

    for name, (doc, expected) in VALID.items():
        result = enc_fm.parse(doc)
        if not result.found:
            failures.append(f"VALID '{name}': no front matter detected")
            continue
        if result.problems:
            failures.append(f"VALID '{name}': unexpected problems "
                            f"{[p.code for p in result.problems]}")
        for key, want in expected.items():
            got = (result.data or {}).get(key, "<missing>")
            if got != want:
                failures.append(f"VALID '{name}': {key} = {got!r}, expected {want!r}")

    for name, (doc, code) in INVALID.items():
        result = enc_fm.parse(doc)
        codes = [p.code for p in result.problems]
        if code not in codes:
            failures.append(f"INVALID '{name}': expected {code}, got {codes or 'nothing'}")

    for name, doc in NO_FRONT_MATTER.items():
        if enc_fm.parse(doc).found:
            failures.append(f"NO-FM '{name}': front matter reported where there is none")

    total = len(VALID) + len(INVALID) + len(NO_FRONT_MATTER)
    print(f"test_frontmatter: {total} cases "
          f"({len(VALID)} valid, {len(INVALID)} must fail, {len(NO_FRONT_MATTER)} absent)")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK - the documented subset parses exactly, everything else is refused by name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
