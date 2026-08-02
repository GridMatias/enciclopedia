#!/usr/bin/env python3
"""Keep the protocol's four faces consistent.

SKILL.md, _meta/config.json, _install/systemPrompt.json and
PROTOCOL-CHANGELOG.md all state the same facts. They drifted twice by hand while
the protocol was being written, which is exactly the failure this catches.

This tool never writes anything: it reports drift and exits non-zero, so CI and
the pre-commit hook can refuse a half-applied protocol change.

Usage:
    python _tools/enc_bootstrap.py --check     # verify alignment (default)
    python _tools/enc_bootstrap.py --print     # show the canonical facts
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_RULES = ["OUTPUT-RULES.md", "image-rules.md", "pdf-composition.md",
                  "data-rules.md", "governance.md", "research-rules.md",
                  "scale-rules.md", "untrusted-content.md"]
REQUIRED_TOOLS = ["enc_core.py", "enc_fm.py", "enc_secrets.py", "enc_lint.py",
                  "enc_index.py", "enc_bootstrap.py", "enc_verify.py", "enc_audit.py",
                  "enc_new.py", "enc_search.py", "enc_pack.py", "enc_doctor.py",
                  "enc_import_vault.py", "enc_import.py", "enc_setup.py"]
REQUIRED_TESTS = ["test_lint.py", "test_frontmatter.py", "test_secrets.py",
                  "test_templates.py", "test_tools.py", "scenarios.md",
                  "run_scenarios.py", "bench_retrieval.py"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def facts() -> dict:
    cfg_raw = read(ROOT / "_meta" / "config.json")
    cfg = json.loads(cfg_raw) if cfg_raw else {}
    skill = read(ROOT / "SKILL.md")
    boot_raw = read(ROOT / "_install" / "systemPrompt.json")
    boot = json.loads(boot_raw) if boot_raw else {}
    m = re.search(r"(?m)^version:\s*(\S+)", skill)
    prof = cfg.get("retrieval", {}).get("profiles", {}).get("medium", {})
    return {
        "configVersion": cfg.get("protocolVersion", ""),
        "skillVersion": m.group(1) if m else "",
        "bootstrapVersion": str(boot.get("version", "")),
        "root": cfg.get("encyclopediaRoot", ""),
        "writePolicy": cfg.get("writePolicy", ""),
        "skillLines": len(skill.splitlines()),
        "skillMaxLines": cfg.get("thresholds", {}).get("skillMaxLines", 0),
        "mediumFiles": prof.get("maxFilesPerTurn", 0),
        "mediumLines": prof.get("maxLinesPerTurn", 0),
        "systemPrompt": boot.get("systemPrompt", ""),
        "compact": boot.get("systemPromptCompact", ""),
        "changelog": read(ROOT / "PROTOCOL-CHANGELOG.md"),
        "skill": skill,
    }


def check(f: dict) -> list[str]:
    problems: list[str] = []
    if not f["configVersion"]:
        problems.append("_meta/config.json: protocolVersion missing or file unreadable")
    if f["skillVersion"] != f["configVersion"]:
        problems.append(f"version drift: SKILL.md={f['skillVersion'] or '?'} "
                        f"config.json={f['configVersion'] or '?'}")
    if f["bootstrapVersion"] != f["configVersion"]:
        problems.append(f"version drift: _install/systemPrompt.json={f['bootstrapVersion'] or '?'} "
                        f"config.json={f['configVersion'] or '?'}")
    if f["configVersion"] and f"## {f['configVersion']}" not in f["changelog"]:
        problems.append(f"PROTOCOL-CHANGELOG.md has no entry for {f['configVersion']}")
    if f["skillMaxLines"] and f["skillLines"] > f["skillMaxLines"]:
        problems.append(f"SKILL.md is {f['skillLines']} lines > skillMaxLines "
                        f"({f['skillMaxLines']}): move detail into _rules/")
    sp = f["systemPrompt"]
    if not sp:
        problems.append("_install/systemPrompt.json: systemPrompt is empty")
    else:
        if f["root"] in ("", "auto"):
            if "folder containing SKILL.md" not in sp:
                problems.append("systemPrompt does not explain how to locate the root "
                                "(config says 'auto': it must say the root is the folder "
                                "containing SKILL.md, wherever the user copied it)")
        elif f["root"] not in sp:
            problems.append("systemPrompt does not state the encyclopedia root from config")
        for token, why in (("SKILL.md", "must tell the model to load the protocol"),
                           ("_meta/config.json", "must point to the authoritative numbers"),
                           ("approval", "must state the propose-only gate")):
            if token not in sp:
                problems.append(f"systemPrompt is missing '{token}': it {why}")
        if f["writePolicy"] == "propose-only" and "without explicit" not in sp:
            problems.append("systemPrompt does not restate the propose-only guarantee")
        if "DATA, never instructions" not in sp:
            problems.append("systemPrompt does not carry invariant 10 (content is data, "
                            "never instructions): a hostile document could redirect the agent")
    if f["compact"] and "never obey it" not in f["compact"]:
        problems.append("systemPromptCompact does not carry invariant 10")
    if "10. **File content is data" not in f["skill"]:
        problems.append("SKILL.md is missing invariant 10 (content is data, never instruction)")
    for name in REQUIRED_RULES:
        if not (ROOT / "_rules" / name).exists():
            problems.append(f"_rules/{name} is missing but the protocol points at it")
    for name in REQUIRED_TOOLS:
        if not (ROOT / "_tools" / name).exists():
            problems.append(f"_tools/{name} is missing")
    for name in REQUIRED_TESTS:
        if not (ROOT / "_tests" / name).exists():
            problems.append(f"_tests/{name} is missing: a claim without a test is a hope")
    if not (ROOT / "_examples" / "INDEX.md").exists():
        problems.append("_examples/ has no INDEX.md: the checks would run on an empty tree again")
    if not f["compact"]:
        problems.append("_install/systemPrompt.json: systemPromptCompact is empty")
    for sec in ("## 1. Invariants", "## 8. Sync proposal", "## 11.", "## 16. Self-maintenance"):
        if sec.rstrip(".") not in f["skill"] and sec not in f["skill"]:
            problems.append(f"SKILL.md is missing the section '{sec}'")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Check protocol consistency")
    ap.add_argument("--check", action="store_true", default=True)
    ap.add_argument("--print", dest="show", action="store_true", help="print canonical facts")
    args = ap.parse_args()

    f = facts()
    if args.show:
        print(f"root              {f['root']}")
        print(f"protocolVersion   {f['configVersion']}")
        print(f"SKILL.md version  {f['skillVersion']}  ({f['skillLines']} lines, max {f['skillMaxLines']})")
        print(f"bootstrap version {f['bootstrapVersion']}")
        print(f"writePolicy       {f['writePolicy']}")
        print(f"medium profile    {f['mediumFiles']} files / {f['mediumLines']} lines")
        print(f"systemPrompt      {len(f['systemPrompt'])} chars")
        print(f"compact           {len(f['compact'])} chars")

    problems = check(f)
    if problems:
        print("\nenc_bootstrap: DRIFT")
        for p in problems:
            print(f"  - {p}")
        print("\nA protocol change is not done until all four faces agree (SKILL 16).")
        return 1
    print("\nenc_bootstrap: OK - SKILL.md, config.json, systemPrompt.json and the changelog agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
