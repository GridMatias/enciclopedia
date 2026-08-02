#!/usr/bin/env python3
"""Print the scaffold for a new project or page. It never writes.

`enc: new` used to be a procedure the agent performed by hand, which meant the
front matter was filled by memory: wrong id, missing owner, a template banner
left at the top. This fills the templates deterministically and prints
paste-ready blocks; the agent puts them in a proposal and the user approves
(SKILL.md section 8). Same output in Mode A, B and C.

Usage:
    python _tools/enc_new.py --print my-app
    python _tools/enc_new.py --print my-app --title "My App" --area api --page auth
    python _tools/enc_new.py --print my-app --owner matix --lang it
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from enc_core import cget, load_config, read_text, resolve_root, utf8_stdout  # noqa: E402

BANNER_RE = re.compile(r"(?s)\A\s*<!--.*?-->\s*")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")


def strip_banner(text: str) -> str:
    return BANNER_RE.sub("", text, count=1)


def fill(text: str, mapping: dict) -> str:
    for needle, value in mapping.items():
        text = text.replace(needle, value)
    return text


def set_fm(text: str, overrides: dict, drop: tuple = ()) -> str:
    """Rewrite front matter keys, keeping order and appending what is missing."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return text
    seen, out = set(), []
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:(.*)$", line)
        if m and m.group(1) in drop:
            continue
        if m and m.group(1) in overrides:
            key = m.group(1)
            out.append(f"{key}: {overrides[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in overrides.items():
        if key not in seen:
            out.append(f"{key}: {value}")
    return "\n".join(["---"] + out + ["---"] + lines[end + 1:]) + "\n"


def block(path: str, body: str) -> str:
    """A whole file. Three hashes means 'create this path with exactly this content'."""
    return f"### `{path}`\n\n````markdown\n{body.rstrip()}\n````\n"


def snippet(title: str, body: str) -> str:
    """A line to add to an existing file. Four hashes: never a whole file."""
    return f"#### {title}\n\n````markdown\n{body.rstrip()}\n````\n"


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Print a scaffold for a new project or page")
    ap.add_argument("slug", help="project slug, kebab-case")
    ap.add_argument("--root", help="encyclopedia root")
    ap.add_argument("--print", dest="show", action="store_true", default=True,
                    help="print the files (this tool never writes)")
    ap.add_argument("--title", help="human readable project name")
    ap.add_argument("--purpose", default="<cosa fa e per chi>")
    ap.add_argument("--area", help="first area folder, e.g. api, ricerca, legale")
    ap.add_argument("--page", help="slug of the first page inside that area")
    ap.add_argument("--page-title", help="title of the first page")
    ap.add_argument("--owner", default="unassigned")
    ap.add_argument("--lang", default="it")
    ap.add_argument("--confidentiality", default=None)
    args = ap.parse_args()

    if not SLUG_RE.match(args.slug):
        print(f"enc_new: '{args.slug}' is not a valid slug (kebab-case, ASCII, max 60 chars)")
        return 2

    root = resolve_root(args.root)
    cfg = load_config(root)
    today = date.today().isoformat()
    title = args.title or args.slug.replace("-", " ").capitalize()
    conf = args.confidentiality or cget(cfg, "governance.defaultConfidentiality", "internal")
    templates = root / cget(cfg, "paths.templates", "_templates")

    common = {
        "<project-slug>": args.slug,
        "<Nome progetto>": title,
        "<YYYY-MM-DD>": today,
        "<cosa fa e per chi>": args.purpose,
    }
    fm_common = {"project": args.slug, "lang": args.lang, "created": today,
                 "updated": today, "owner": args.owner, "confidentiality": conf}

    print(f"# Scaffold proposal for `{args.slug}` (nothing has been written)\n")
    print(f"Destinazione: `{args.slug}/` - motivo: nuovo progetto (SKILL 9.6.4 / 12).\n")

    hub = templates / "project-README.template.md"
    if hub.exists():
        body = set_fm(fill(strip_banner(read_text(hub)), common),
                      dict(fm_common, id=f"{args.slug}/README", title=title,
                           type="hub", status="active", tags="[]", aliases="[]"))
        print(block(f"{args.slug}/README.md", body))

    log = templates / "CHANGELOG.template.md"
    if log.exists():
        body = set_fm(fill(strip_banner(read_text(log)), common),
                      dict(fm_common, id=f"{args.slug}/CHANGELOG",
                           title=f"Changelog - {title}", type="log", status="active"))
        body = body.replace("- <YYYY-MM-DD> —", f"- {today} —")
        print(block(f"{args.slug}/CHANGELOG.md", body))

    if args.area and args.page:
        page_title = args.page_title or args.page.replace("-", " ").capitalize()
        page = templates / "page.template.md"
        if page.exists():
            body = fill(strip_banner(read_text(page)),
                        dict(common, **{"<area>": args.area, "<page-slug>": args.page,
                                        "<Titolo della pagina>": page_title}))
            body = set_fm(body, dict(fm_common,
                                     id=f"{args.slug}/{args.area}/{args.page}",
                                     title=page_title, type="note", status="draft",
                                     tags="[]", sources="[]",
                                     related=f'["../README.md"]', supersedes="[]"))
            print(block(f"{args.slug}/{args.area}/{args.page}.md", body))

    print(snippet(f"riga da aggiungere alla tabella dei progetti in `INDEX.md`",
                  f"| `{args.slug}` | `{args.slug}/` | active | {today} | - | {args.purpose} |"))
    if args.area and args.page:
        print(snippet(f"riga da aggiungere alla mappa dei file in `{args.slug}/README.md` "
                      "(sostituisce quella di esempio)",
                      f"| [{args.page}]({args.area}/{args.page}.md) | <una riga> | "
                      f"<quando la richiesta riguarda ...> |"))
    print("Wiring (SKILL 9.7): riga nella mappa dei file, `related` in entrambe le "
          "direzioni, riga di CHANGELOG, riga in INDEX.md.")
    print("\nNothing was written: bring these blocks to the user as a proposal (SKILL 8).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
