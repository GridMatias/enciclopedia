#!/usr/bin/env python3
"""Differential test: our parser against PyYAML, on every page in the repository.

`_tools/enc_fm.py` is hand written because the tools must have zero runtime
dependencies. The risk of a hand-written parser is not that it crashes, it is
that it *quietly disagrees* with the rest of the world. So in CI - where a
dependency is allowed - we parse every front matter twice and fail on any
divergence.

Documented, accepted differences (everything else is a failure):

  1. **Dates.** PyYAML resolves an unquoted `2026-07-25` to `datetime.date`; we
     keep the string. Both are normalised to the ISO string here.
  2. **YAML 1.1 booleans.** PyYAML reads `no`, `yes`, `on`, `off` as booleans;
     we follow the YAML 1.2 core schema and keep them as strings, because
     `lang: no` means Norwegian, not False.

Run:  python _tests/test_yaml_differential.py
      (skipped with exit 0 when PyYAML is not installed)
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

REAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL_ROOT / "_tools"))

import enc_fm  # noqa: E402
from enc_core import iter_paths, load_config, read_text  # noqa: E402

YAML_11_BOOLS = {"no", "yes", "on", "off", "y", "n"}


def normalise(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, bool):
        return f"<bool {value}>"
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, dict):
        return {str(k): normalise(v) for k, v in value.items()}
    if value is None:
        return None
    return str(value)


def acceptable(ours, theirs) -> bool:
    """The two documented divergences, and nothing else."""
    if isinstance(theirs, str) and isinstance(ours, str):
        return False
    if str(theirs).startswith("<bool") and isinstance(ours, str) \
            and ours.lower() in YAML_11_BOOLS:
        return True  # YAML 1.1 booleans: 'no' is a language code here
    return False


def front_matter_text(text: str) -> str:
    body, _removed = enc_fm._strip_prelude(text)
    lines = body.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for i in range(1, min(len(lines), enc_fm.MAX_FM_LINES + 1)):
        if lines[i].strip() in ("---", "..."):
            return "\n".join(lines[1:i])
    return ""


def compare(name: str, text: str, yaml, failures: list) -> bool:
    result = enc_fm.parse(text)
    if not result.found:
        return False
    raw = front_matter_text(text)
    try:
        theirs = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        if not result.problems:
            failures.append(f"{name}: PyYAML rejects this front matter but enc_fm accepted "
                            f"it without a problem ({str(exc).splitlines()[0]})")
        return True
    if result.problems:
        return True  # we already refused it; PyYAML being lenient is not a defect
    if not isinstance(theirs, dict):
        failures.append(f"{name}: PyYAML produced {type(theirs).__name__}, not a mapping")
        return True

    ours_n = normalise(result.data or {})
    theirs_n = normalise(theirs)
    for key in sorted(set(ours_n) | set(theirs_n)):
        a, b = ours_n.get(key, "<missing>"), theirs_n.get(key, "<missing>")
        if a == b or acceptable(a, b):
            continue
        failures.append(f"{name}: key '{key}' -> enc_fm {a!r}, PyYAML {b!r}")
    return True


def main() -> int:
    try:
        import yaml  # type: ignore
    except ImportError:
        print("test_yaml_differential: PyYAML not installed, skipping "
              "(CI installs it; the runtime tools never need it)")
        return 0

    cfg = load_config(REAL_ROOT)
    failures: list = []
    checked = 0
    roots = [REAL_ROOT, REAL_ROOT / "_examples"]
    for root in roots:
        if not root.exists():
            continue
        for path, rel in iter_paths(root, cfg):
            if path.is_file() and path.suffix == ".md":
                if compare(f"{root.name}/{rel.as_posix()}", read_text(path), yaml, failures):
                    checked += 1
    for path in sorted((REAL_ROOT / "_templates").glob("*.template.md")):
        if compare(f"_templates/{path.name}", read_text(path), yaml, failures):
            checked += 1
    for path in sorted((REAL_ROOT / "_rules").glob("*.md")):
        if compare(f"_rules/{path.name}", read_text(path), yaml, failures):
            checked += 1

    print(f"test_yaml_differential: {checked} front matter blocks parsed twice")
    if failures:
        print("\nDIVERGENCES:")
        for problem in failures:
            print(f"  - {problem}")
        print("\nEither enc_fm is wrong, or the divergence is legitimate and must be "
              "documented in this file's docstring and in acceptable().")
        return 1
    print("OK - enc_fm agrees with PyYAML everywhere, or refuses the input by name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
