#!/usr/bin/env python3
"""Plan the migration of an existing Markdown vault (Obsidian, Logseq, plain notes).

Nobody starts from an empty encyclopedia. What stopped people from adopting this
protocol was the first hour: `[[wikilinks]]` that resolve to nothing, front matter
in another dialect, attachments in a global folder. This reads the vault and
prints a migration plan - file mapping, link rewrites, front matter to add,
unresolvable references. It writes nothing: the plan becomes a proposal.

Usage:
    python _tools/enc_import_vault.py --print "C:/Users/me/Obsidian/Vault"
    python _tools/enc_import_vault.py --print <vault> --project my-notes --limit 40
    python _tools/enc_import_vault.py --print <vault> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import enc_fm  # noqa: E402
from enc_core import read_text, utf8_stdout  # noqa: E402

WIKILINK_RE = re.compile(r"(?<!\\)\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")
EMBED_RE = re.compile(r"!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}
SKIP = {".obsidian", ".trash", ".git", "node_modules", ".stfolder"}


def slugify(name: str) -> str:
    folded = "".join(c for c in unicodedata.normalize("NFKD", name)
                     if not unicodedata.combining(c))
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", folded).strip("-").lower()
    return (slug or "pagina")[:60]


def scan(vault: Path) -> tuple:
    notes, assets = {}, {}
    for path in sorted(vault.rglob("*")):
        if any(part in SKIP for part in path.relative_to(vault).parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() == ".md":
            notes[path.stem.lower()] = path
        elif path.suffix.lower() in IMAGE_EXT:
            assets[path.name.lower()] = path
    return notes, assets


def target_for(path: Path, vault: Path, project: str) -> str:
    rel = path.relative_to(vault)
    parts = [slugify(p) for p in rel.parts[:-1]][:1]  # max one area level
    area = parts[0] if parts else "note"
    return f"{project}/{area}/{slugify(rel.stem)}.md"


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Plan the migration of an existing vault")
    ap.add_argument("vault", help="folder to read")
    ap.add_argument("--project", default=None, help="target project slug")
    ap.add_argument("--print", dest="show", action="store_true", default=True)
    ap.add_argument("--limit", type=int, default=25, help="rows to print per table")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        print(f"enc_import_vault: '{vault}' is not a folder")
        return 2
    project = args.project or slugify(vault.name)

    notes, assets = scan(vault)
    mapping = {p: target_for(p, vault, project) for p in notes.values()}
    rows, unresolved, no_fm, embeds = [], [], [], []

    for source, target in sorted(mapping.items(), key=lambda kv: kv[1]):
        text = read_text(source)
        result = enc_fm.parse(text)
        if not result.found:
            no_fm.append(target)
        links = []
        for m in WIKILINK_RE.finditer(text):
            name = m.group(1).strip()
            hit = notes.get(name.lower()) or notes.get(Path(name).stem.lower())
            if hit:
                dest = mapping[hit]
                depth = target.count("/")
                prefix = "../" * (depth - 1) if depth > 1 else ""
                links.append((m.group(0), prefix + "/".join(dest.split("/")[1:])))
            else:
                unresolved.append((target, name))
        for m in EMBED_RE.finditer(text):
            name = m.group(1).strip()
            if Path(name).suffix.lower() in IMAGE_EXT:
                embeds.append((target, name, name.lower() in assets))
        rows.append({"from": source.relative_to(vault).as_posix(), "to": target,
                     "wikilinks": len(links), "hasFrontMatter": result.found,
                     "problems": [p.code for p in result.problems]})

    if args.json:
        print(json.dumps({"project": project, "notes": len(notes), "assets": len(assets),
                          "files": rows, "unresolved": unresolved,
                          "embeds": embeds}, indent=2, ensure_ascii=False))
        return 0

    print(f"# Migration plan: `{vault}` -> project `{project}`\n")
    print(f"- note trovate: **{len(notes)}** · immagini: **{len(assets)}**")
    print(f"- pagine senza front matter: **{len(no_fm)}** (ne va aggiunto uno completo)")
    print(f"- wikilink non risolvibili: **{len(unresolved)}**")
    print(f"- embed di immagini: **{len(embeds)}**\n")

    print("## Mappatura file (prime righe)\n")
    print("| Da | A | wikilink | front matter |")
    print("|---|---|---|---|")
    for row in rows[:args.limit]:
        print(f"| `{row['from']}` | `{row['to']}` | {row['wikilinks']} | "
              f"{'si' if row['hasFrontMatter'] else 'NO'} |")
    if len(rows) > args.limit:
        print(f"| _(+{len(rows) - args.limit} altre)_ | | | |")

    if unresolved:
        print("\n## Wikilink che non puntano a nulla\n")
        for target, name in unresolved[:args.limit]:
            print(f"- `{target}` -> `[[{name}]]` **non esiste**: crea la pagina o rimuovi il link")
    if embeds:
        print("\n## Immagini da spostare accanto alla pagina che le usa\n")
        for target, name, exists in embeds[:args.limit]:
            state = "trovata" if exists else "**mancante**"
            print(f"- `{target}` usa `{name}` ({state}) -> rinominare "
                  f"`<page-slug>-fig-NN.<ext>` nella stessa cartella (image-rules 1)")

    print("\n## Cosa serve per ogni pagina migrata\n")
    print("- front matter completo (`id` uguale al path senza estensione, `project`, "
          "`type`, `status`, `lang`, `created`, `updated`, `owner`, `confidentiality`)")
    print("- `[[wikilink]]` convertiti in link relativi POSIX")
    print("- immagini accanto alla pagina, con alt text e didascalia")
    print("- riga nella mappa dei file del README di progetto e in `INDEX.md`")
    print("\nNiente e' stato scritto: porta questo piano all'utente come proposta (SKILL 8), "
          "un lotto di pagine per volta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
