#!/usr/bin/env python3
"""One command that tells a newcomer whether the encyclopedia is wired correctly.

Everything here is a read or a subprocess call to the other tools; nothing is
modified. It exists because "clone it and follow the README" is where most
adoptions die: the hook is not enabled, python is the Store stub, the config is
invalid, and nobody notices until something silently stops being checked.

Usage:
    python _tools/enc_doctor.py            # environment + structure
    python _tools/enc_doctor.py --full     # also run tests, linter, index check
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from enc_core import (cget, load_config, project_dirs, read_text,  # noqa: E402
                      resolve_root, utf8_stdout)

REQUIRED = ["SKILL.md", "INDEX.md", "AGENTS.md", "README.md", "PROTOCOL-CHANGELOG.md",
            "_meta/config.json", "_meta/frontmatter.schema.json",
            "_install/systemPrompt.json", "_tools/enc_lint.py", "_tests/test_lint.py"]
TOOLS = ["enc_core.py", "enc_fm.py", "enc_secrets.py", "enc_lint.py", "enc_index.py",
         "enc_bootstrap.py", "enc_verify.py", "enc_audit.py", "enc_new.py",
         "enc_search.py", "enc_pack.py", "enc_import_vault.py", "enc_doctor.py",
         "enc_import.py", "enc_setup.py"]

OK, WARN, BAD = "ok  ", "warn", "FAIL"


def line(status: str, what: str, detail: str = "") -> None:
    print(f"[{status}] {what}" + (f" - {detail}" if detail else ""))


def run(root: Path, args: list) -> tuple:
    try:
        proc = subprocess.run([sys.executable] + args, cwd=str(root),
                              capture_output=True, text=True, check=False)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except OSError as exc:
        return 127, str(exc)


def git(root: Path, *args: str) -> tuple:
    try:
        proc = subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip()
    except (OSError, FileNotFoundError):
        return 127, ""


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Check that the encyclopedia is wired correctly")
    ap.add_argument("--root", help="encyclopedia root")
    ap.add_argument("--full", action="store_true", help="also run the tools")
    args = ap.parse_args()

    root = resolve_root(args.root)
    problems = 0
    print(f"enc_doctor: {root}\n")

    v = sys.version_info
    line(OK if v >= (3, 9) else BAD, f"python {v.major}.{v.minor}.{v.micro}",
         "" if v >= (3, 9) else "3.9+ required")
    problems += 0 if v >= (3, 9) else 1
    line(OK, f"platform {platform.system()} {platform.release()}")

    cfg = load_config(root)
    if cfg.get("protocolVersion", "unknown") == "unknown":
        line(BAD, "_meta/config.json", "unreadable or missing protocolVersion")
        problems += 1
    else:
        line(OK, "_meta/config.json", f"protocol {cfg['protocolVersion']}")

    for rel in REQUIRED:
        if (root / rel).exists():
            line(OK, rel)
        else:
            line(BAD, rel, "missing")
            problems += 1
    missing_tools = [t for t in TOOLS if not (root / "_tools" / t).exists()]
    line(OK if not missing_tools else BAD, f"_tools/ ({len(TOOLS) - len(missing_tools)}/{len(TOOLS)})",
         "missing: " + ", ".join(missing_tools) if missing_tools else "")
    problems += 1 if missing_tools else 0

    code, out = git(root, "rev-parse", "--is-inside-work-tree")
    if code == 127:
        line(WARN, "git", "not installed: no history, no safety net, no audit trail")
    elif code or out != "true":
        line(WARN, "git", "this folder is not a repository - run: git init && git add -A "
                          "&& git commit -m \"encyclopedia\"")
    else:
        line(OK, "git repository")
        code, hooks = git(root, "config", "--get", "core.hooksPath")
        if hooks == "_tools/hooks":
            line(OK, "git hooks", "core.hooksPath=_tools/hooks")
        else:
            line(WARN, "git hooks", "run: git config core.hooksPath _tools/hooks")

    index_text = read_text(root / "INDEX.md") if (root / "INDEX.md").exists() else ""
    projects = project_dirs(root, cfg, index_text)
    if projects:
        line(OK, f"{len(projects)} project(s)", ", ".join(p.name for p in projects[:8]))
    else:
        line(WARN, "0 projects", "the protocol has never run on real knowledge here; "
                                 "start with: python _tools/enc_new.py --print <slug>")

    idx = root / cget(cfg, "paths.machineIndex", "_index") / "routing.json"
    line(OK if idx.exists() else WARN, "_index/routing.json",
         "" if idx.exists() else "not built yet: python _tools/enc_index.py")

    if args.full:
        print("\n--- running the tools ---")
        for label, argv in (("linter self-test", ["_tests/test_lint.py"]),
                            ("front matter tests", ["_tests/test_frontmatter.py"]),
                            ("secret tests", ["_tests/test_secrets.py"]),
                            ("template tests", ["_tests/test_templates.py"]),
                            ("tool tests", ["_tests/test_tools.py"]),
                            ("integrity lint", ["_tools/enc_lint.py"]),
                            ("protocol consistency", ["_tools/enc_bootstrap.py", "--check"]),
                            ("record verification", ["_tools/enc_verify.py"])):
            if not (root / argv[0]).exists():
                line(WARN, label, f"{argv[0]} not present")
                continue
            code, out = run(root, argv)
            tail = (out.strip().splitlines() or [""])[-1][:100]
            line(OK if code == 0 else BAD, label, tail)
            problems += 1 if code else 0

    print(f"\n{problems} problem(s).")
    if problems:
        print("Fix the FAIL lines first; warnings are safe to postpone but not to forget.")
    else:
        print("Ready. Next: python _tools/enc_new.py --print <slug> to propose your "
              "first project.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
