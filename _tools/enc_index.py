#!/usr/bin/env python3
"""Build the machine index of the encyclopedia and print a refreshed INDEX table.

Two tiers, because one monolithic manifest does not scale: measured on synthetic
trees it reached ~526 KB at 1000 pages, i.e. ~2.5 MB and ~650k tokens at 5000 -
"read one file instead of climbing the ladder" collapses exactly where it was
supposed to help.

    _index/routing.json      projects, areas, keywords, sizes. Small by design,
                             capped by thresholds.maxRoutingIndexBytes. THIS is
                             what an agent reads first.
    _index/p/<slug>.json     one shard per project: its pages with title, tags,
                             headings, links and char count.
    _index/manifest.json     the full graph, for tooling (bench, doctor, audits),
                             not for context windows.

All three are generated, disposable and git-ignored - the only writes in the
whole toolchain (SKILL.md invariant 1). INDEX.md is never touched: the table is
printed for the agent to propose.

Staleness is answered by a command instead of by the model guessing from a
timestamp: `--check` recomputes the tree fingerprint (stat only) and exits 1 when
the index no longer describes the tree.

Usage:
    python _tools/enc_index.py               # write index + print INDEX table
    python _tools/enc_index.py --dry-run     # print only, write nothing
    python _tools/enc_index.py --stats       # one-line summary
    python _tools/enc_index.py --check       # FRESH / STALE, exit 0 / 1
    python _tools/enc_index.py --root <dir>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import enc_fm  # noqa: E402
from enc_core import (cget, is_content_page, iter_paths, load_config,  # noqa: E402
                      norm_link, project_dirs, read_text, resolve_root,
                      tree_hash, utc_now, utf8_stdout)

HEADING_RE = re.compile(r"(?m)^(#{1,3})\s+(.+?)\s*$")
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
WORD_RE = re.compile(r"[a-z0-9]{3,}")


def page_record(path: Path, rel: Path) -> dict:
    text = read_text(path)
    fm = enc_fm.parse_front_matter(text) or {}
    rp = rel.as_posix()
    links, images = [], []
    for m in LINK_RE.finditer(text):
        bang, target = m.group(1), m.group(3).split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "doi:", "tel:")):
            continue
        resolved = norm_link(rp, target)
        (images if bang else links).append(resolved)
    tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
    return {
        "path": rp,
        "id": fm.get("id", "") or "",
        "title": fm.get("title", "") or "",
        "type": fm.get("type", "") or "",
        "status": fm.get("status", "") or "",
        "lang": fm.get("lang", "") or "",
        "confidentiality": fm.get("confidentiality", "") or "",
        "trust": fm.get("trust", "") or "",
        "owner": fm.get("owner", "") or "",
        "updated": fm.get("updated", "") or "",
        "review_by": fm.get("review_by", "") or "",
        "tags": [t for t in tags if isinstance(t, str)],
        "lines": len(text.splitlines()),
        "chars": len(text),
        "headings": [h[1] for h in HEADING_RE.findall(text)][:12],
        "links": links,
        "images": images,
    }


def build(root: Path, cfg: dict) -> dict:
    index_text = read_text(root / "INDEX.md") if (root / "INDEX.md").exists() else ""
    pages = []
    for p, rel in iter_paths(root, cfg):
        if p.is_file() and p.suffix == ".md" and is_content_page(rel, cfg):
            pages.append(page_record(p, rel))

    data_dir_name = cget(cfg, "paths.dataDir", "_data")
    projects = []
    for proj in project_dirs(root, cfg, index_text):
        hub = proj / "README.md"
        fm, purpose = {}, ""
        if hub.exists():
            text = read_text(hub)
            fm = enc_fm.parse_front_matter(text) or {}
            m = (re.search(r"(?m)^\*\*Scopo in una riga:\*\*\s*(.+)$", text)
                 or re.search(r"(?m)^\*\*(?:Purpose|Scopo)[^:]*:\*\*\s*(.+)$", text))
            purpose = m.group(1).strip() if m else ""
        own = [r for r in pages if r["path"].startswith(proj.name + "/")]
        areas = {}
        for rec in own:
            parts = rec["path"].split("/")
            area = parts[1] if len(parts) > 2 else "-"
            slot = areas.setdefault(area, {"name": area, "pages": 0, "chars": 0})
            slot["pages"] += 1
            slot["chars"] += rec["chars"]
        tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
        aliases = fm.get("aliases") if isinstance(fm.get("aliases"), list) else []
        projects.append({
            "slug": proj.name,
            "path": proj.name + "/",
            "title": fm.get("title", proj.name) or proj.name,
            "status": fm.get("status", "") or "",
            "updated": max([r["updated"] for r in own if r["updated"]] or [""]),
            "tags": [t for t in tags if isinstance(t, str)],
            "aliases": [a for a in aliases if isinstance(a, str)],
            "langs": sorted({r["lang"] for r in own if r["lang"]}),
            "purpose": purpose,
            "pageCount": len(own),
            "chars": sum(r["chars"] for r in own),
            "areas": [areas[k] for k in sorted(areas)],
            "shard": f"_index/p/{proj.name}.json",
            "datasets": sorted(d.name for d in (proj / data_dir_name).iterdir()
                               if d.is_dir()) if (proj / data_dir_name).is_dir() else [],
        })

    linked = {t for r in pages for t in r["links"]}
    image_refs = {t for r in pages for t in r["images"]}
    all_images = [rel.as_posix() for p, rel in iter_paths(root, cfg)
                  if p.is_file() and p.suffix.lower() in cget(cfg, "extensions.images", [])
                  and is_content_page(rel.with_suffix(".md"), cfg)]
    broken = sorted({t for r in pages for t in r["links"] + r["images"]
                     if not (root / t).exists()})
    orphan_pages = sorted(r["path"] for r in pages if r["path"] not in linked
                          and Path(r["path"]).name not in ("README.md", "CHANGELOG.md",
                                                           "datasheet.md"))

    return {
        "$comment": "Generated by _tools/enc_index.py. Disposable, git-ignored, never "
                    "hand-edited. Agents read _index/routing.json first, then the shard "
                    "of the project they need. Check freshness with --check.",
        "generated": utc_now(),
        "inputsHash": tree_hash(root, cfg),
        "protocolVersion": cfg.get("protocolVersion", "unknown"),
        "root": root.as_posix(),
        "stats": {
            "projects": len(projects),
            "pages": len(pages),
            "chars": sum(r["chars"] for r in pages),
            "images": len(all_images),
            "orphanPages": len(orphan_pages),
            "orphanImages": len([i for i in all_images if i not in image_refs]),
            "brokenLinks": len(broken),
        },
        "projects": projects,
        "pages": pages,
        "orphans": {"pages": orphan_pages,
                    "images": sorted(i for i in all_images if i not in image_refs)},
        "brokenLinks": broken,
    }


def keywords_of(manifest: dict) -> dict:
    """keyword -> [project slugs]. Ambiguous terms keep every candidate, which is
    what lets an agent know it must ask instead of guessing (SKILL.md P1)."""
    table: dict = {}
    for proj in manifest["projects"]:
        words = set()
        for source in ([proj["slug"], proj["title"], proj["purpose"]]
                       + proj["tags"] + proj["aliases"]
                       + [a["name"] for a in proj["areas"]]):
            words.update(WORD_RE.findall((source or "").lower()))
        for page in manifest["pages"]:
            if page["path"].startswith(proj["slug"] + "/"):
                words.update(t.lower() for t in page["tags"])
        for word in words:
            table.setdefault(word, [])
            if proj["slug"] not in table[word]:
                table[word].append(proj["slug"])
    return {k: table[k] for k in sorted(table)}


def routing_of(manifest: dict) -> dict:
    return {
        "$comment": "Cheap routing tier: projects, areas and keywords only. Read this, "
                    "pick the project, then read its shard in _index/p/<slug>.json. "
                    "Never hand-edited; regenerate with _tools/enc_index.py.",
        "generated": manifest["generated"],
        "inputsHash": manifest["inputsHash"],
        "protocolVersion": manifest["protocolVersion"],
        "stats": manifest["stats"],
        "projects": [{k: p[k] for k in ("slug", "path", "title", "status", "updated",
                                        "tags", "aliases", "langs", "purpose",
                                        "pageCount", "chars", "areas", "datasets", "shard")}
                     for p in manifest["projects"]],
        "keywords": keywords_of(manifest),
    }


def shards_of(manifest: dict) -> dict:
    out: dict = {}
    for proj in manifest["projects"]:
        prefix = proj["slug"] + "/"
        out[proj["slug"]] = {
            "$comment": "Per-project shard. One read routes inside a project without "
                        "loading the whole vault.",
            "slug": proj["slug"],
            "generated": manifest["generated"],
            "inputsHash": manifest["inputsHash"],
            "pages": [{k: rec[k] for k in ("path", "title", "type", "status", "lang",
                                           "confidentiality", "trust", "owner", "updated",
                                           "review_by", "tags", "lines", "chars",
                                           "headings", "links", "images")}
                      for rec in manifest["pages"] if rec["path"].startswith(prefix)],
        }
    return out


def index_table(manifest: dict) -> str:
    rows = ["| Project (slug) | Path | Status | Updated | Tags | One-line purpose |",
            "|---|---|---|---|---|---|"]
    for p in manifest["projects"]:
        rows.append("| `{slug}` | `{path}` | {status} | {updated} | {tags} | {purpose} |".format(
            slug=p["slug"], path=p["path"], status=p["status"] or "-",
            updated=p["updated"] or "-", tags=", ".join(p["tags"]) or "-",
            purpose=p["purpose"] or "-"))
    if len(rows) == 2:
        rows.append("| _(nessun progetto ancora)_ | | | | | |")
    return "\n".join(rows)


def check_fresh(root: Path, cfg: dict) -> int:
    routing_path = root / cget(cfg, "paths.machineIndex", "_index") / "routing.json"
    if not routing_path.exists():
        print("enc_index --check: MISSING - no _index/routing.json; run python _tools/enc_index.py")
        return 1
    try:
        stored = json.loads(routing_path.read_text(encoding="utf-8")).get("inputsHash", "")
    except json.JSONDecodeError:
        print("enc_index --check: CORRUPT - routing.json is not valid JSON; regenerate it")
        return 1
    current = tree_hash(root, cfg)
    if stored == current:
        print(f"enc_index --check: FRESH - index matches the tree ({current[:12]})")
        return 0
    print(f"enc_index --check: STALE - tree is {current[:12]}, index was built on "
          f"{stored[:12] or '?'}; regenerate before trusting it")
    return 1


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Build the encyclopedia machine index")
    ap.add_argument("--root", help="encyclopedia root (default: this repository)")
    ap.add_argument("--dry-run", action="store_true", help="print only, write nothing")
    ap.add_argument("--stats", action="store_true", help="one-line summary only")
    ap.add_argument("--check", action="store_true", help="is the index still fresh?")
    args = ap.parse_args()

    root = resolve_root(args.root)
    cfg = load_config(root)

    if args.check:
        return check_fresh(root, cfg)

    manifest = build(root, cfg)
    routing = routing_of(manifest)
    shards = shards_of(manifest)
    s = manifest["stats"]

    if args.stats:
        print("projects={projects} pages={pages} chars={chars} images={images} "
              "orphanPages={orphanPages} orphanImages={orphanImages} "
              "brokenLinks={brokenLinks}".format(**s))
        return 0

    routing_blob = json.dumps(routing, indent=2, ensure_ascii=False)
    cap = cget(cfg, "thresholds.maxRoutingIndexBytes", 262144)

    if not args.dry_run:
        out = root / cget(cfg, "paths.machineIndex", "_index")
        (out / "p").mkdir(parents=True, exist_ok=True)
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                           encoding="utf-8")
        (out / "routing.json").write_text(routing_blob, encoding="utf-8")
        for slug, shard in shards.items():
            (out / "p" / f"{slug}.json").write_text(
                json.dumps(shard, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote _index/routing.json ({len(routing_blob)} bytes), "
              f"{len(shards)} shard(s) and manifest.json "
              f"({s['pages']} pages, {s['projects']} projects)")
    else:
        print(f"dry-run: {s['pages']} pages, {s['projects']} projects, "
              f"routing would be {len(routing_blob)} bytes, nothing written")

    if len(routing_blob) > cap:
        print(f"[WARN] routing.json is {len(routing_blob)} bytes > maxRoutingIndexBytes ({cap}): "
              "propose splitting the routing table (_rules/scale-rules.md 1, stage S4)")

    print("\n--- proposed INDEX.md projects table (nothing was written to INDEX.md) ---")
    print(index_table(manifest))
    if manifest["brokenLinks"]:
        print("\nbroken links:", ", ".join(manifest["brokenLinks"][:20]))
    if manifest["orphans"]["pages"]:
        print("orphan pages:", ", ".join(manifest["orphans"]["pages"][:20]))
    print("\nBring changes to INDEX.md as a proposal (SKILL 8): this tool does not write it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
