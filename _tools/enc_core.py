#!/usr/bin/env python3
"""Shared primitives for the Project Encyclopedia tools.

Standard library only, ASCII-only output, Windows and Linux alike. Root
resolution, configuration, tree walking, link normalisation, hashing and the
run-id live here so a policy change happens in exactly one place.

NOTHING in this module writes to disk.
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

# Fallbacks used only when _meta/config.json is missing or unreadable. The file
# is the single source of truth; these keep the tools usable on a broken repo.
FALLBACK = {
    "protocolVersion": "unknown",
    "paths": {
        "infrastructure": ["_meta", "_tools", "_tests", "_install", "_examples",
                           ".gitignore", ".github"],
        "rules": "_rules",
        "templates": "_templates",
        "exports": "_exports",
        "machineIndex": "_index",
        "dataDir": "_data",
        "originalsDir": "_originals",
        "importedDir": "_imported",
        "secretAllowlist": "_meta/secret-allowlist.txt",
    },
    "extensions": {
        "knowledge": [".md"],
        "images": [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"],
        "data": [".csv", ".tsv", ".json", ".jsonl", ".yaml", ".yml", ".bib",
                 ".txt", ".geojson"],
        "neverStored": [".exe", ".dll", ".msi", ".apk", ".iso", ".jar"],
    },
    "thresholds": {
        "pageSplitLines": 400,
        "maxImageBytes": 1048576,
        "inlineDataMaxBytes": 1048576,
        "inlineDataMaxRows": 5000,
        "maxPagesPerHub": 25,
        "maxImagesPerPage": 20,
        "maxImportPages": 120,
        "maxOriginalBytes": 26214400,
        "maxRoutingIndexBytes": 262144,
        "contradictionMaxDays": 30,
    },
    "vocabularies": {
        "pageType": ["note", "spec", "decision", "log", "reference", "imported",
                     "experiment", "dataset", "paper-note", "meeting", "policy", "hub"],
        "pageStatus": ["draft", "active", "stable", "deprecated"],
        "confidentiality": ["public", "internal", "restricted"],
        "trust": ["trusted", "untrusted"],
    },
    "security": {
        "untrustedPaths": ["_imported", "_data", "_originals"],
        "secretEntropyBits": 4.0,
        "secretMinLength": 24,
        "piiSeverity": "WARN",
    },
    "audit": {"approvalTrailer": "enc-approved", "approverTrailer": "approved-by"},
}

# Directories never walked: generated, disposable, or tooling.
BASE_SKIP = {".git", ".github", "_exports", "_index", "_tools", "_meta", "_tests",
             "_install", "_examples", "node_modules", ".venv", "__pycache__", ".pytest_cache"}
# Reserved top-level names that are not projects.
RESERVED_TOP = BASE_SKIP | {"_rules", "_templates"}
# Markdown files allowed at the encyclopedia root. Anything else there is stray.
ROOT_DOCS = {"README.md", "SKILL.md", "INDEX.md", "AGENTS.md", "LICENSE.md",
             "PROTOCOL-CHANGELOG.md", "PROTOCOL-ROADMAP.md", "CONTRIBUTING.md",
             "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md", "INDEX-ROUTING.md"}


def utf8_stdout() -> None:
    """Make stdout survive non-ASCII output on a Windows console.

    The default code page there is cp1252: a single 'e accentata' in a page title
    was enough to end a tool run with UnicodeEncodeError. Every CLI calls this
    first; findings stay ASCII, but content quoted from pages does not have to be.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover - old or wrapped streams
            pass


def resolve_root(arg: str | None = None) -> Path:
    """Encyclopedia root: --root, then ENCYCLOPEDIA_ROOT, then the repo itself."""
    if arg:
        return Path(arg).expanduser().resolve()
    env = os.environ.get("ENCYCLOPEDIA_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_ROOT


def load_config(root: Path) -> dict:
    """Merge _meta/config.json over FALLBACK, one level deep per section."""
    cfg = json.loads(json.dumps(FALLBACK))
    path = root / "_meta" / "config.json"
    if not path.exists():
        path = DEFAULT_ROOT / "_meta" / "config.json"
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[WARN] {path}: invalid JSON ({exc}); using built-in defaults")
            raw = {}
        for key, val in raw.items():
            if isinstance(val, dict) and isinstance(cfg.get(key), dict):
                cfg[key].update(val)
            else:
                cfg[key] = val
    return cfg


def cget(cfg: dict, dotted: str, default=None):
    """cget(cfg, 'thresholds.maxImagesPerPage', 20)"""
    node = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def skip_dirs(cfg: dict) -> set:
    infra = set(cget(cfg, "paths.infrastructure", []) or [])
    return BASE_SKIP | {p for p in infra if not p.startswith(".")} | {".github", ".git"}


def reserved_top(cfg: dict) -> set:
    return skip_dirs(cfg) | {cget(cfg, "paths.rules", "_rules"),
                             cget(cfg, "paths.templates", "_templates")}


def iter_paths(root: Path, cfg: dict):
    """Yield (absolute path, relative Path) for everything that is not skipped."""
    skip = skip_dirs(cfg)
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in skip for part in rel.parts):
            continue
        yield p, rel


def is_content_page(rel: Path, cfg: dict) -> bool:
    """True only for .md pages inside a project folder.

    Protocol documentation (root files, _rules/, _templates/) is prose ABOUT the
    encyclopedia: full of illustrative paths and placeholders on purpose. Linting
    it as content would produce nothing but false positives. It is still scanned
    for secrets and injection markers.
    """
    parts = rel.parts
    return len(parts) > 1 and parts[0] not in reserved_top(cfg) and rel.suffix == ".md"


def project_dirs(root: Path, cfg: dict, index_text: str = "") -> list:
    """Top-level folders that really are projects.

    A folder counts as a project when it holds a hub or a log, or when INDEX.md
    already lists it. Everything else is a stray folder, reported as such instead
    of being audited as a broken project (that used to turn `allegati/` into two
    spurious ERRORs).
    """
    out = []
    reserved = reserved_top(cfg)
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name in reserved or d.name.startswith("."):
            continue
        if (d / "README.md").exists() or (d / "CHANGELOG.md").exists():
            out.append(d)
        elif index_text and f"`{d.name}`" in index_text:
            out.append(d)
    return out


def stray_dirs(root: Path, cfg: dict, index_text: str = "") -> list:
    projects = {d.name for d in project_dirs(root, cfg, index_text)}
    reserved = reserved_top(cfg)
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and d.name not in reserved
                  and not d.name.startswith(".") and d.name not in projects)


def norm_link(page_rel: str, target: str) -> str:
    """Resolve a markdown link target against the page that carries it.

    posixpath.normpath collapses '..', without which every cross-folder link
    looked broken and every cross-folder image looked orphaned.
    """
    base = posixpath.dirname(page_rel)
    joined = posixpath.join(base, target) if not target.startswith("/") else target.lstrip("/")
    return posixpath.normpath(joined).replace("\\", "/")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree_hash(root: Path, cfg: dict) -> str:
    """Cheap fingerprint of the knowledge tree: path, size, mtime. Stat only."""
    h = hashlib.sha256()
    for p, rel in iter_paths(root, cfg):
        if not p.is_file():
            continue
        st = p.stat()
        h.update(f"{rel.as_posix()}|{st.st_size}|{st.st_mtime_ns}\n".encode("utf-8"))
    return h.hexdigest()


def make_run_id(root: Path, cfg: dict) -> str:
    """Identifier a tool prints so a *claimed* run can be challenged.

    It binds the output to the state of the tree at the moment of the run. An
    agent that fabricates a report cannot produce a matching id, and
    `enc_lint.py --verify-run <id>` says so. It proves the tree state, not the
    honesty of the summary - which is exactly what it claims.
    """
    return f"{tree_hash(root, cfg)[:16]}-{int(time.time()):x}"


def verify_run_id(root: Path, cfg: dict, run_id: str) -> tuple[bool, str]:
    current = tree_hash(root, cfg)[:16]
    claimed = (run_id or "").split("-", 1)[0].strip().lower()
    if not claimed:
        return False, "empty run id"
    if claimed == current:
        return True, "authentic: this id was produced on the tree as it stands now"
    return False, (f"no match: current tree is {current}, the id claims {claimed}. "
                   "Either the tree changed after the run, or the run never happened. "
                   "Re-run the tool and compare.")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_text(path: Path) -> str:
    """Read UTF-8 (with or without BOM) without ever raising on bad bytes."""
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.decode("utf-8", errors="replace")


def rel_posix(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
