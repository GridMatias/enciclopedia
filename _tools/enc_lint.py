#!/usr/bin/env python3
"""Integrity linter for the Project Encyclopedia.

Zero dependencies, standard library only, ASCII-only output (safe on Windows
consoles). It NEVER modifies anything: it reports, and the agent proposes the
fix (SKILL.md section 8). That is deliberate - a linter that silently rewrites
your knowledge base would break the one guarantee the protocol makes.

Every run prints a `runId` bound to the state of the tree. An agent that claims
to have run the linter without running it cannot produce a matching id, and
`--verify-run <id>` says so. Report honesty stops being a matter of trust.

Usage:
    python _tools/enc_lint.py                    # whole encyclopedia
    python _tools/enc_lint.py my-app             # one project
    python _tools/enc_lint.py --root _examples   # a different tree
    python _tools/enc_lint.py --json             # machine-readable
    python _tools/enc_lint.py --warnings-as-errors
    python _tools/enc_lint.py --verify-run <id>  # was that report real?

Exit codes: 0 clean (warnings allowed), 1 errors found, 2 bad usage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import enc_fm  # noqa: E402
import enc_secrets  # noqa: E402
from enc_core import (DEFAULT_ROOT, ROOT_DOCS, cget, is_content_page,  # noqa: E402
                      iter_paths, load_config, make_run_id, norm_link,
                      project_dirs, read_text, resolve_root, stray_dirs,
                      utf8_stdout, verify_run_id)

ROOT = DEFAULT_ROOT  # kept as a module attribute for backwards compatibility

REQUIRED_KEYS = ["id", "title", "project", "type", "status", "lang", "created", "updated"]
LIST_KEYS = ["tags", "sources", "related", "supersedes", "aliases", "reviewed_by"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
WIKILINK_RE = re.compile(r"(?<!\\)\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
FENCE_RE = re.compile(r"(?ms)^(`{3,}|~{3,}).*?^\1[^\n]*$")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
CONTRADICTION_RE = re.compile(r"(?m)^\s*[-*]\s*(\d{4}-\d{2}-\d{2})\s*[-\u2014]")
TEMPLATE_BANNER_RE = re.compile(r"<!--\s*\n?TEMPLATE\b", re.IGNORECASE)
CONF_ORDER = {"public": 0, "internal": 1, "restricted": 2}

# Kept importable: _tests and the CI job used to reach for these names.
parse_front_matter = enc_fm.parse_front_matter


class Report:
    def __init__(self) -> None:
        self.items: list = []

    def add(self, level: str, code: str, path: str, msg: str, hint: str = "") -> None:
        self.items.append({"level": level, "code": code, "path": path, "msg": msg, "hint": hint})

    def error(self, *a, **k) -> None:
        self.add("ERROR", *a, **k)

    def warn(self, *a, **k) -> None:
        self.add("WARN", *a, **k)

    @property
    def errors(self) -> int:
        return sum(1 for i in self.items if i["level"] == "ERROR")

    @property
    def warnings(self) -> int:
        return sum(1 for i in self.items if i["level"] == "WARN")


def strip_code(text: str) -> str:
    """Remove fenced blocks and inline code so examples are not linted as links."""
    return INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))


def is_untrusted(rel: Path, cfg: dict) -> bool:
    """Pages derived from material the user did not write: imports, data, originals."""
    marked = set(cget(cfg, "security.untrustedPaths", []) or [])
    return any(part in marked for part in rel.parts)


def needs_trust_flag(rel: Path, cfg: dict) -> bool:
    """Only converted documents must declare `trust: untrusted`: their text was
    written by someone else and may address the agent directly."""
    marked = set(cget(cfg, "security.trustRequiredPaths", ["_imported"]) or [])
    return any(part in marked for part in rel.parts)


def conf_of(fm: dict, cfg: dict) -> str:
    default = cget(cfg, "governance.defaultConfidentiality", "internal")
    value = (fm or {}).get("confidentiality") or default
    return value if value in CONF_ORDER else default


def _root_of(path: Path, rel: Path) -> Path:
    root = path.resolve()
    for _ in rel.parts:
        root = root.parent
    return root


def check_page(path: Path, rel: Path, cfg: dict, rep: Report, ids: dict, today: str,
               allowlist: set = None) -> dict:
    allowlist = allowlist or set()
    root = _root_of(path, rel)
    text = read_text(path)
    lines = text.splitlines()
    rp = rel.as_posix()
    content = is_content_page(rel, cfg)
    untrusted = is_untrusted(rel, cfg)
    info = {"path": rp, "links": [], "images": [], "fm": None, "lines": len(lines),
            "chars": len(text), "content": content, "untrusted": untrusted,
            "conf": conf_of({}, cfg), "sources": []}

    for finding in enc_secrets.scan_secrets(
            text, allowlist,
            float(cget(cfg, "security.secretEntropyBits", 4.0)),
            int(cget(cfg, "security.secretMinLength", 24))):
        rep.add(finding["level"], finding["code"], rp, finding["msg"], finding["hint"])
    for finding in enc_secrets.scan_pii(text, allowlist,
                                        cget(cfg, "security.piiSeverity", "WARN")):
        rep.add(finding["level"], finding["code"], rp, finding["msg"], finding["hint"])
    for finding in enc_secrets.scan_injection(text, allowlist,
                                              "ERROR" if untrusted else "WARN"):
        rep.add(finding["level"], finding["code"], rp, finding["msg"], finding["hint"])

    if not content:
        return info  # protocol documentation: content scanners only, see is_content_page

    if len(lines) > cget(cfg, "thresholds.pageSplitLines", 400):
        rep.warn("LONG-PAGE", rp, f"{len(lines)} lines > {cget(cfg, 'thresholds.pageSplitLines', 400)}",
                 "propose a split by topic (SKILL 9.2)")

    body = strip_code(text)
    image_count = 0
    for m in LINK_RE.finditer(body):
        bang, alt, target = m.group(1), m.group(2), m.group(3)
        if target.startswith(("http://", "https://", "mailto:", "#", "doi:", "tel:", "data:")):
            continue
        if target.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", target) or "\\" in target:
            rep.error("ABSOLUTE-LINK", rp,
                      f"'{target}' is not a relative POSIX link",
                      "links are relative and POSIX-style (SKILL 9.3)")
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        resolved = norm_link(rp, clean)
        if resolved.startswith(".."):
            rep.error("LINK-ESCAPE", rp, f"'{target}' resolves outside the encyclopedia")
            continue
        entry = {"target": resolved, "alt": alt, "raw": clean}
        if bang:
            info["images"].append(entry)
            image_count += 1
        else:
            info["links"].append(entry)
        if not (root / resolved).exists():
            rep.error("MISSING-IMAGE" if bang else "BROKEN-LINK", rp,
                      f"points to '{target}' which does not exist")
        if bang and not alt.strip():
            rep.warn("NO-ALT", rp, f"image '{target}' has no alt text",
                     "alt text is mandatory (image-rules 2)")

    max_images = cget(cfg, "thresholds.maxImagesPerPage", 20)
    if image_count > max_images:
        rep.warn("TOO-MANY-IMAGES", rp, f"{image_count} images > maxImagesPerPage ({max_images})",
                 "split the page by topic or move the gallery to an imported document")

    if TEMPLATE_BANNER_RE.search(text):
        rep.warn("TEMPLATE-BANNER", rp, "the '<!-- TEMPLATE ... -->' header was copied over",
                 "delete it: it is instructions for you, not content of the page")

    wikilinks = WIKILINK_RE.findall(body)
    if wikilinks:
        rep.warn("WIKILINK", rp, f"{len(wikilinks)} Obsidian-style [[wikilink]] found "
                                 f"(first: '{wikilinks[0]}')",
                 "convert to relative links: python _tools/enc_import_vault.py --print <folder>")

    for i, line in enumerate(lines):
        if line.lstrip().startswith("!["):
            nxt = ""
            for j in range(i + 1, min(i + 3, len(lines))):
                if lines[j].strip():
                    nxt = lines[j].strip()
                    break
            if not (nxt.startswith("*") or nxt.startswith("_")):
                rep.warn("NO-CAPTION", rp, f"image on line {i + 1} has no italic caption below",
                         "add '*Fig. N - ...*' (image-rules 2)")

    result = enc_fm.parse(text)
    fm = result.data
    info["fm"] = fm
    for problem in result.problems:
        rep.error(problem.code, rp, f"{problem.msg} (line {problem.line})",
                  "front matter follows a restricted YAML subset; see _tools/enc_fm.py")
    if not result.found:
        rep.error("NO-FRONTMATTER", rp, "content page without front matter",
                  "copy the block from _templates/page.template.md")
        return info
    if fm is None:
        return info

    info["conf"] = conf_of(fm, cfg)
    info["sources"] = [s for s in (fm.get("sources") or []) if isinstance(s, str)]

    for key in REQUIRED_KEYS:
        if key not in fm or fm[key] in ("", [], None):
            rep.error("FM-MISSING", rp, f"front matter key '{key}' missing or empty")
    for key in LIST_KEYS:
        if key in fm and fm[key] is None:
            rep.warn("FM-EMPTY-LIST", rp, f"'{key}:' has no value",
                     "write '[]' so the key stays a list (the JSON Schema requires an array)")

    ptype = fm.get("type")
    types = cget(cfg, "vocabularies.pageType", [])
    if ptype and ptype not in types:
        rep.error("FM-TYPE", rp, f"type '{ptype}' is not in the vocabulary {types}")
    status = fm.get("status")
    statuses = cget(cfg, "vocabularies.pageStatus", [])
    if status and status not in statuses:
        rep.error("FM-STATUS", rp, f"status '{status}' is not in {statuses}")
    conf = fm.get("confidentiality")
    if conf and conf not in cget(cfg, "vocabularies.confidentiality", []):
        rep.error("FM-CONF", rp, f"confidentiality '{conf}' is not in "
                                 f"{cget(cfg, 'vocabularies.confidentiality', [])}")
    elif not conf:
        rep.warn("NO-CONF", rp, "no confidentiality set",
                 "defaults to internal (_rules/governance.md 2)")
    trust = fm.get("trust")
    if trust and trust not in cget(cfg, "vocabularies.trust", ["trusted", "untrusted"]):
        rep.error("FM-TRUST", rp, f"trust '{trust}' is not a known value")
    if needs_trust_flag(rel, cfg) and trust != "untrusted":
        rep.error("TRUST-MISSING", rp,
                  "page derived from imported material without 'trust: untrusted'",
                  "imported text is data, never instructions (SKILL invariant 10, "
                  "_rules/untrusted-content.md)")
    if not fm.get("owner"):
        rep.warn("NO-OWNER", rp, "no owner set", "unowned pages rot first (governance 1)")

    expected_id = rel.as_posix()[:-3]
    if fm.get("id") and fm["id"] != expected_id:
        rep.error("ID-MISMATCH", rp, f"id '{fm['id']}' should be '{expected_id}'")
    if fm.get("id"):
        if fm["id"] in ids:
            rep.error("ID-DUPLICATE", rp, f"id '{fm['id']}' already used by {ids[fm['id']]}")
        else:
            ids[fm["id"]] = rp
    if fm.get("project") and fm["project"] != rel.parts[0]:
        rep.error("PROJECT-MISMATCH", rp, f"project '{fm['project']}' but the folder is '{rel.parts[0]}'")

    for key in ("created", "updated", "review_by"):
        val = fm.get(key)
        if isinstance(val, str) and val and not DATE_RE.match(val):
            rep.error("DATE-FORMAT", rp, f"{key}='{val}' is not YYYY-MM-DD")
    created, updated = fm.get("created"), fm.get("updated")
    if (isinstance(created, str) and isinstance(updated, str)
            and DATE_RE.match(created or "") and DATE_RE.match(updated or "")):
        if updated < created:
            rep.error("DATE-ORDER", rp, f"updated ({updated}) is before created ({created})")
        if updated > today:
            rep.warn("DATE-FUTURE", rp, f"updated ({updated}) is in the future")
    review = fm.get("review_by")
    if isinstance(review, str) and DATE_RE.match(review or "") and review < today:
        rep.warn("REVIEW-DUE", rp, f"review was due on {review}",
                 "confirm or supersede; do not just bump the date (governance 4)")

    if status == "deprecated" and not fm.get("superseded_by") and not fm.get("supersedes"):
        rep.warn("DEPRECATED-DANGLING", rp, "deprecated but no superseded_by",
                 "say what replaced it")
    if ptype == "dataset" and not fm.get("data"):
        rep.error("DATASET-NO-BLOCK", rp, "type dataset without the 'data' front matter block")
    if ptype == "experiment" and not fm.get("experiment"):
        rep.error("EXPERIMENT-NO-BLOCK", rp, "type experiment without the 'experiment' block")
    if ptype == "paper-note" and not fm.get("citation"):
        rep.error("PAPER-NO-CITATION", rp, "type paper-note without the 'citation' block")
    if ptype == "imported" and not info["sources"]:
        rep.error("IMPORT-NO-SOURCE", rp, "type imported without 'sources'",
                  "record the original file name and its sha256 (data-rules 5)")
    return info


def check_records(root: Path, cfg: dict, rep: Report, index_text: str = "") -> None:
    data_name = cget(cfg, "paths.dataDir", "_data")
    orig_name = cget(cfg, "paths.originalsDir", "_originals")
    imported_name = cget(cfg, "paths.importedDir", "_imported")
    images = cget(cfg, "extensions.images", [])
    data_ext = cget(cfg, "extensions.data", [])
    max_bytes = cget(cfg, "thresholds.inlineDataMaxBytes", 1048576)
    max_rows = cget(cfg, "thresholds.inlineDataMaxRows", 5000)
    max_original = cget(cfg, "thresholds.maxOriginalBytes", 26214400)
    max_import_pages = cget(cfg, "thresholds.maxImportPages", 120)

    for proj in project_dirs(root, cfg, index_text):
        data_dir = proj / data_name
        if data_dir.is_dir():
            for ds in sorted(d for d in data_dir.iterdir() if d.is_dir()):
                rp = ds.relative_to(root).as_posix()
                if not (ds / "datasheet.md").exists():
                    rep.error("NO-DATASHEET", rp, "dataset folder without datasheet.md",
                              "copy _templates/dataset-datasheet.template.md (SKILL 11.4)")
                for f in sorted(ds.iterdir()):
                    if f.is_dir() or f.name == "datasheet.md":
                        continue
                    ext = f.suffix.lower()
                    frp = f.relative_to(root).as_posix()
                    if ext in images:
                        continue
                    if ext not in data_ext:
                        rep.error("DATA-EXT", frp, f"'{ext}' is not an allowed inline data format",
                                  "convert to a text format or store a pointer (data-rules 2)")
                        continue
                    size = f.stat().st_size
                    if size > max_bytes:
                        rep.warn("DATA-BIG", frp,
                                 f"{size} bytes > inlineDataMaxBytes ({max_bytes})",
                                 "store a pointer + sha256 instead")
                    elif ext in (".csv", ".tsv"):
                        try:
                            rows = sum(1 for _ in f.open(encoding="utf-8", errors="replace"))
                        except OSError:
                            rows = 0
                        if rows > max_rows:
                            rep.warn("DATA-ROWS", frp, f"{rows} rows > inlineDataMaxRows ({max_rows})")

        orig_dir = proj / orig_name
        if orig_dir.is_dir():
            for f in sorted(orig_dir.iterdir()):
                if f.is_dir() or f.suffix == ".sha256":
                    continue
                frp = f.relative_to(root).as_posix()
                has_sum = (f.with_suffix(f.suffix + ".sha256").exists()
                           or (orig_dir / (f.stem + ".sha256")).exists())
                if not has_sum:
                    rep.error("NO-CHECKSUM", frp,
                              "retained original without a .sha256 sibling",
                              "python _tools/enc_verify.py --print prints the missing digests "
                              "(data-rules 6)")
                if f.stat().st_size > max_original:
                    rep.error("ORIGINAL-TOO-BIG", frp,
                              f"{f.stat().st_size} bytes > maxOriginalBytes ({max_original})",
                              "keep it in git-lfs or an external store and record a pointer "
                              "+ sha256 in the datasheet (data-rules 5)")

        imp_dir = proj / imported_name
        if imp_dir.is_dir():
            for src in sorted(d for d in imp_dir.iterdir() if d.is_dir()):
                pages_n = len([f for f in src.iterdir()
                               if f.suffix.lower() in images and f.name.startswith("page-")])
                if pages_n > max_import_pages:
                    rep.warn("IMPORT-TOO-MANY-PAGES", src.relative_to(root).as_posix(),
                             f"{pages_n} page images > maxImportPages ({max_import_pages})",
                             "keep a '## Sintesi' plus the informative pages, and reference "
                             "the rest by page range in the original (SKILL 11.1)")


def check_structure(root: Path, cfg: dict, rep: Report, pages: list, index_text: str) -> None:
    referenced = set()
    linked_pages = set()
    for info in pages:
        for entry in info["links"] + info["images"]:
            referenced.add(entry["target"])
        for entry in info["links"]:
            linked_pages.add(entry["target"])

    images = cget(cfg, "extensions.images", [])
    never = cget(cfg, "extensions.neverStored", [])
    max_image = cget(cfg, "thresholds.maxImageBytes", 1048576)

    for p, rel in iter_paths(root, cfg):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        rp = rel.as_posix()
        if ext in never:
            rep.error("FORBIDDEN-EXT", rp, f"'{ext}' must never be stored in the encyclopedia")
        if len(rel.parts) == 1 and ext == ".md" and rel.name not in ROOT_DOCS:
            rep.error("STRAY-PAGE", rp, "markdown file at the encyclopedia root",
                      "knowledge lives inside a project folder; root documents are "
                      f"limited to {sorted(ROOT_DOCS)}")
        if ext in images and is_content_page(rel.with_suffix(".md"), cfg):
            if rp not in referenced:
                rep.warn("ORPHAN-IMAGE", rp, "image referenced by no page",
                         "reference it or remove it (image-rules 5)")
            if p.stat().st_size > max_image:
                rep.warn("IMAGE-BIG", rp, f"{p.stat().st_size} bytes > maxImageBytes")

    for stray in stray_dirs(root, cfg, index_text):
        rep.warn("STRAY-FOLDER", stray.relative_to(root).as_posix(),
                 "top-level folder that is neither a project nor infrastructure",
                 "a project needs README.md + CHANGELOG.md and a row in INDEX.md")

    projects = project_dirs(root, cfg, index_text)
    for proj in projects:
        name = proj.name
        for required in ("README.md", "CHANGELOG.md"):
            if not (proj / required).exists():
                rep.error("PROJECT-INCOMPLETE", f"{name}/{required}", "missing",
                          "python _tools/enc_new.py --print " + name)
        if index_text and not re.search(rf"(?m)^\|\s*`?{re.escape(name)}`?\s*\|", index_text):
            rep.error("INDEX-MISSING-ROW", "INDEX.md", f"no row for project '{name}'",
                      "INDEX.md must list every project (SKILL 9.7)")
        for area in sorted(d for d in proj.iterdir() if d.is_dir() and not d.name.startswith("_")):
            page_count = len([f for f in area.glob("*.md") if f.name != "README.md"])
            if page_count > cget(cfg, "thresholds.maxPagesPerHub", 25) and not (area / "README.md").exists():
                rep.warn("HUB-NEEDED", area.relative_to(root).as_posix(),
                         f"{page_count} pages without an area hub",
                         "shard the file map (_rules/scale-rules.md 2)")
        check_contradictions(root, proj, cfg, rep)

    if index_text:
        listed = set(re.findall(r"(?m)^\|\s*`?([a-z0-9][a-z0-9-]*)`?\s*\|", index_text))
        actual = {d.name for d in projects}
        for slug in sorted(listed - actual):
            rep.error("INDEX-GHOST-ROW", "INDEX.md",
                      f"row '{slug}' has no folder", "the tree wins: propose removing the row")

    for info in pages:
        rel = Path(info["path"])
        if not info.get("content"):
            continue
        if rel.name in ("README.md", "CHANGELOG.md", "datasheet.md"):
            continue
        if info["path"] not in linked_pages:
            rep.warn("ORPHAN-PAGE", info["path"], "no hub or page links to it",
                     "add it to the file map (SKILL 9.7)")


def check_contradictions(root: Path, proj: Path, cfg: dict, rep: Report) -> None:
    """Declined cascade items must not fade away after one turn.

    SKILL.md 8 lets the user approve item 1 and refuse its cascade. The page left
    inconsistent is recorded under '## Contraddizioni aperte' in the project hub;
    this check makes the ledger expire loudly instead of quietly.
    """
    hub = proj / "README.md"
    if not hub.exists():
        return
    text = read_text(hub)
    m = re.search(r"(?ms)^##\s+(?:Contraddizioni aperte|Open contradictions)\s*$(.*?)(?=^##\s|\Z)", text)
    if not m:
        return
    max_days = int(cget(cfg, "thresholds.contradictionMaxDays", 30))
    limit = (date.today() - timedelta(days=max_days)).isoformat()
    for found in CONTRADICTION_RE.finditer(m.group(1)):
        when = found.group(1)
        if when < limit:
            rep.error("CONTRADICTION-STALE", hub.relative_to(root).as_posix(),
                      f"open contradiction dated {when} is older than {max_days} days",
                      "resolve it with a proposal or record why it stays open")


def check_governance(cfg: dict, rep: Report, pages: list) -> None:
    """Classification travels upward, never downward (SKILL 15.1)."""
    conf = {info["path"]: info.get("conf") for info in pages if info.get("content")}
    for info in pages:
        if not info.get("content"):
            continue
        mine = CONF_ORDER.get(info.get("conf"), 1)
        for src in info["sources"]:
            target = norm_link(info["path"], src) if not src.startswith(("http", "doi:")) else None
            if target and target in conf and CONF_ORDER.get(conf[target], 1) > mine:
                rep.error("CLASS-LEAK", info["path"],
                          f"derives from '{target}' classified {conf[target]} "
                          f"but is itself {info.get('conf')}",
                          "a page inherits the highest confidentiality of its sources "
                          "(governance 2.1)")
        for entry in info["links"]:
            target = entry["target"]
            # Linking upward is allowed (governance 2.3). Only the two-level jump
            # public -> restricted is worth a reminder; anything less is noise, and
            # noisy warnings are how real warnings get ignored.
            if target in conf and CONF_ORDER.get(conf[target], 1) - mine >= 2:
                rep.warn("CLASS-LINK", info["path"],
                         f"links '{target}' ({conf[target]}) from a {info.get('conf')} page",
                         "linking is allowed, inlining or summarising the content is not")


def run(root: Path, cfg: dict, project: str = None, today: str = None) -> tuple:
    rep = Report()
    today = today or date.today().isoformat()
    ids: dict = {}
    pages: list = []
    allowlist = enc_secrets.load_allowlist(
        root / cget(cfg, "paths.secretAllowlist", "_meta/secret-allowlist.txt"))

    index_path = root / "INDEX.md"
    index_text = read_text(index_path) if index_path.exists() else ""
    if not index_text:
        rep.error("NO-INDEX", "INDEX.md", "missing", "the cheapest file in the system must exist")

    for p, rel in iter_paths(root, cfg):
        if not p.is_file() or p.suffix != ".md":
            continue
        if project and rel.parts[0] != project:
            continue
        pages.append(check_page(p, rel, cfg, rep, ids, today, allowlist))

    if not project:
        check_records(root, cfg, rep, index_text)
        check_structure(root, cfg, rep, pages, index_text)
        check_governance(cfg, rep, pages)
    return rep, pages


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Integrity linter for the Project Encyclopedia")
    ap.add_argument("project", nargs="?", help="limit checks to one project slug")
    ap.add_argument("--root", help="encyclopedia root (default: this repository)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--warnings-as-errors", action="store_true")
    ap.add_argument("--verify-run", metavar="ID",
                    help="check whether a runId was really produced on this tree")
    args = ap.parse_args()

    root = resolve_root(args.root)
    cfg = load_config(root)

    if args.verify_run:
        ok, why = verify_run_id(root, cfg, args.verify_run)
        print(f"enc_lint --verify-run {args.verify_run}: {'OK' if ok else 'FAIL'} - {why}")
        return 0 if ok else 1

    rep, pages = run(root, cfg, args.project)
    run_id = make_run_id(root, cfg)

    if args.json:
        print(json.dumps({"runId": run_id, "root": root.as_posix(),
                          "protocolVersion": cfg.get("protocolVersion", ""),
                          "errors": rep.errors, "warnings": rep.warnings,
                          "pages": len(pages), "items": rep.items}, indent=2))
    else:
        print(f"enc_lint: {len(pages)} markdown files checked in {root}")
        if not rep.items:
            print("OK - no findings")
        for item in sorted(rep.items, key=lambda i: (i["level"] != "ERROR", i["path"])):
            hint = f"  -> {item['hint']}" if item["hint"] else ""
            print(f"[{item['level']}] {item['code']:20} {item['path']}: {item['msg']}{hint}")
        print(f"\n{rep.errors} error(s), {rep.warnings} warning(s)")
        print(f"runId={run_id}  (verify with: python _tools/enc_lint.py --verify-run {run_id})")
        print("This tool never writes: bring the findings to the agent as a proposal (SKILL 8).")

    if rep.errors or (args.warnings_as_errors and rep.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
