#!/usr/bin/env python3
"""The scaffolding path must produce a page the linter accepts.

Every one of the nine shipped templates used to open with an HTML banner before
the front matter, and the parser required `---` on the first line: copying a
template exactly as instructed produced `NO-FRONTMATTER`, an ERROR, which blocked
the pre-commit hook on the very first project anyone created. Nothing in the test
suite noticed, because the suite never copied a template.

Two assertions:
  1. every template's front matter parses, banner and all;
  2. the output of `enc_new.py --print` lints with zero findings once wired.

Run:  python _tests/test_templates.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL_ROOT / "_tools"))

import enc_fm  # noqa: E402
import enc_lint  # noqa: E402
from enc_core import load_config  # noqa: E402

TODAY = date.today().isoformat()
BLOCK_RE = re.compile(r"(?m)^###\s+`([^`]+)`[^\n]*\n\n````markdown\n(.*?)\n````", re.S)

INDEX = """# Encyclopedia Index

## Projects

| Project (slug) | Path | Status | Updated | Tags | One-line purpose |
|---|---|---|---|---|---|
| `demo-scaffold` | `demo-scaffold/` | active | {today} | - | progetto di prova |
"""


def check_templates(failures: list) -> int:
    templates = sorted((REAL_ROOT / "_templates").glob("*.template.md"))
    for path in templates:
        result = enc_fm.parse(path.read_text(encoding="utf-8"))
        if not result.found:
            failures.append(f"{path.name}: front matter not detected "
                            "(the banner or the first line breaks it)")
            continue
        for problem in result.problems:
            failures.append(f"{path.name}: {problem.code} at line {problem.line} - {problem.msg}")
        for key in ("id", "title", "type"):
            if key not in (result.data or {}):
                failures.append(f"{path.name}: front matter without '{key}'")
    return len(templates)


def check_scaffold(failures: list) -> None:
    proc = subprocess.run(
        [sys.executable, "_tools/enc_new.py", "demo-scaffold", "--print",
         "--title", "Demo scaffold", "--area", "api", "--page", "auth",
         "--page-title", "Autenticazione", "--owner", "matix",
         "--purpose", "progetto di prova"],
        cwd=str(REAL_ROOT), capture_output=True, text=True, check=False)
    if proc.returncode:
        failures.append(f"enc_new.py exited {proc.returncode}: {proc.stderr.strip()[:200]}")
        return

    blocks = BLOCK_RE.findall(proc.stdout)
    if len(blocks) < 3:
        failures.append(f"enc_new.py printed {len(blocks)} file blocks, expected at least 3")
        return

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "enc"
        (root / "_meta").mkdir(parents=True)
        (root / "_meta" / "config.json").write_text(
            (REAL_ROOT / "_meta" / "config.json").read_text(encoding="utf-8"), encoding="utf-8")
        (root / "INDEX.md").write_text(INDEX.format(today=TODAY), encoding="utf-8")

        for rel, body in blocks:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body + "\n", encoding="utf-8")

        # Wiring (SKILL 9.7): the hub must point at the page it owns. enc_new prints
        # this row separately; here we apply it, which is what the user would do.
        hub = root / "demo-scaffold" / "README.md"
        text = hub.read_text(encoding="utf-8")
        text = text.replace(
            "| `<area>/<pagina>.md` | <una riga> | <trigger: la richiesta riguarda X> |",
            "| [auth](api/auth.md) | come funziona il login | la richiesta riguarda "
            "accesso o sessione |")
        hub.write_text(text, encoding="utf-8")

        cfg = load_config(root)
        rep, pages = enc_lint.run(root, cfg, today=TODAY)
        if len(pages) < 3:
            failures.append(f"only {len(pages)} pages materialised from the scaffold")
        for item in rep.items:
            failures.append(f"scaffold is not clean: {item['level']} {item['code']} "
                            f"{item['path']}: {item['msg']}")
        if "TEMPLATE-BANNER" in {i["code"] for i in rep.items}:
            failures.append("enc_new.py did not strip the template banner")


def main() -> int:
    failures: list = []
    n = check_templates(failures)
    check_scaffold(failures)

    print(f"test_templates: {n} templates parsed, scaffold generated and linted")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK - every template parses and the generated scaffold lints clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
