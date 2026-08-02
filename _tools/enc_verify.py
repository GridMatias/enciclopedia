#!/usr/bin/env python3
"""Verify that records still are what the encyclopedia says they are.

The linter checks that a `.sha256` file *exists*. That is not the same as the
checksum being *right*, and a corrupted or swapped original would pass silently -
which for a contract, a lab export or an audited dataset is the whole point of
keeping it. This tool recomputes.

What it verifies:
  1. every retained original in <project>/_originals/ against its .sha256 sibling;
  2. every inline dataset against the `data:` block of its datasheet
     (sha256, row count, column count) - datasheet drift is invisible otherwise.

It never writes and never repairs: `--print` gives you the correct digests so the
agent can turn them into a proposal (SKILL.md section 8).

Usage:
    python _tools/enc_verify.py                 # verify everything
    python _tools/enc_verify.py my-app          # one project
    python _tools/enc_verify.py --print         # print digests for what is missing
    python _tools/enc_verify.py --json
Exit codes: 0 all good, 1 at least one mismatch or missing digest.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import enc_fm  # noqa: E402
from enc_core import (cget, load_config, project_dirs, read_text,  # noqa: E402
                      resolve_root, sha256_file, utf8_stdout)

HEX = "0123456789abcdef"


def read_expected(path: Path) -> str:
    """Accept 'hex', 'hex  name' and 'hex *name' (sha256sum / Get-FileHash)."""
    try:
        first = read_text(path).strip().splitlines()[0]
    except (OSError, IndexError):
        return ""
    token = first.split()[0].strip().lower() if first.split() else ""
    return token if len(token) == 64 and all(c in HEX for c in token) else ""


def sidecar_for(f: Path) -> Path:
    with_suffix = f.with_suffix(f.suffix + ".sha256")
    return with_suffix if with_suffix.exists() else f.with_suffix(".sha256")


def check_originals(root: Path, cfg: dict, proj: Path, out: list) -> None:
    orig = proj / cget(cfg, "paths.originalsDir", "_originals")
    if not orig.is_dir():
        return
    for f in sorted(orig.iterdir()):
        if f.is_dir() or f.suffix == ".sha256":
            continue
        rel = f.relative_to(root).as_posix()
        side = sidecar_for(f)
        actual = sha256_file(f)
        expected = read_expected(side) if side.exists() else ""
        if not expected:
            out.append({"level": "ERROR", "code": "NO-CHECKSUM", "path": rel,
                        "msg": f"no readable .sha256 next to the original",
                        "actual": actual, "expected": ""})
        elif expected != actual:
            out.append({"level": "ERROR", "code": "CHECKSUM-MISMATCH", "path": rel,
                        "msg": f"content changed: recorded {expected[:12]}..., "
                               f"actual {actual[:12]}...",
                        "actual": actual, "expected": expected})
        else:
            out.append({"level": "OK", "code": "CHECKSUM-OK", "path": rel,
                        "msg": f"{actual[:12]}...", "actual": actual, "expected": expected})


def count_table(path: Path, delimiter: str) -> tuple:
    rows, columns = 0, 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if not line.strip():
                continue
            if i == 0:
                columns = len(line.rstrip("\n").split(delimiter))
            else:
                rows += 1
    return rows, columns


def check_datasets(root: Path, cfg: dict, proj: Path, out: list) -> None:
    data_dir = proj / cget(cfg, "paths.dataDir", "_data")
    if not data_dir.is_dir():
        return
    for ds in sorted(d for d in data_dir.iterdir() if d.is_dir()):
        sheet = ds / "datasheet.md"
        if not sheet.exists():
            out.append({"level": "ERROR", "code": "NO-DATASHEET",
                        "path": ds.relative_to(root).as_posix(),
                        "msg": "dataset folder without datasheet.md", "actual": "", "expected": ""})
            continue
        fm = enc_fm.parse_front_matter(read_text(sheet)) or {}
        block = fm.get("data")
        rel_sheet = sheet.relative_to(root).as_posix()
        if not isinstance(block, dict):
            out.append({"level": "ERROR", "code": "DATASET-NO-BLOCK", "path": rel_sheet,
                        "msg": "datasheet without a parsable 'data:' block",
                        "actual": "", "expected": ""})
            continue
        if (block.get("storage") or "").lower() != "inline":
            out.append({"level": "OK", "code": "POINTER", "path": rel_sheet,
                        "msg": f"pointer to {block.get('location', '?')} - "
                               f"checksum recorded, file not held here",
                        "actual": "", "expected": str(block.get("sha256", ""))})
            continue
        target = ds / str(block.get("location") or "")
        if not target.exists():
            out.append({"level": "ERROR", "code": "DATA-MISSING", "path": rel_sheet,
                        "msg": f"declares inline data at '{block.get('location')}' "
                               f"which does not exist", "actual": "", "expected": ""})
            continue
        actual = sha256_file(target)
        expected = str(block.get("sha256") or "").lower()
        rel_target = target.relative_to(root).as_posix()
        if expected and expected != actual:
            out.append({"level": "ERROR", "code": "CHECKSUM-MISMATCH", "path": rel_target,
                        "msg": f"datasheet says {expected[:12]}..., file is {actual[:12]}...",
                        "actual": actual, "expected": expected})
        elif not expected:
            out.append({"level": "ERROR", "code": "NO-CHECKSUM", "path": rel_target,
                        "msg": "datasheet has no sha256 for its inline data",
                        "actual": actual, "expected": ""})
        else:
            out.append({"level": "OK", "code": "CHECKSUM-OK", "path": rel_target,
                        "msg": f"{actual[:12]}...", "actual": actual, "expected": expected})

        if target.suffix.lower() in (".csv", ".tsv"):
            delim = str(block.get("delimiter") or ("\t" if target.suffix.lower() == ".tsv" else ","))
            delim = {"\\t": "\t", "tab": "\t"}.get(delim, delim)
            rows, columns = count_table(target, delim)
            for key, real in (("rows", rows), ("columns", columns)):
                declared = block.get(key)
                if isinstance(declared, int) and declared != real:
                    out.append({"level": "ERROR", "code": "DATASHEET-DRIFT", "path": rel_target,
                                "msg": f"datasheet declares {key}={declared}, file has {real}",
                                "actual": str(real), "expected": str(declared)})


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Verify checksums and datasheet claims")
    ap.add_argument("project", nargs="?", help="limit to one project slug")
    ap.add_argument("--root", help="encyclopedia root")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print the digests that should be recorded")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = resolve_root(args.root)
    cfg = load_config(root)
    index_text = read_text(root / "INDEX.md") if (root / "INDEX.md").exists() else ""

    out: list = []
    for proj in project_dirs(root, cfg, index_text):
        if args.project and proj.name != args.project:
            continue
        check_originals(root, cfg, proj, out)
        check_datasets(root, cfg, proj, out)

    bad = [i for i in out if i["level"] == "ERROR"]
    if args.json:
        print(json.dumps({"checked": len(out), "errors": len(bad), "items": out}, indent=2))
        return 1 if bad else 0

    if not out:
        print("enc_verify: no records to verify (no _originals/, no _data/)")
        return 0
    for item in out:
        mark = "OK  " if item["level"] == "OK" else "FAIL"
        print(f"[{mark}] {item['code']:20} {item['path']}: {item['msg']}")
    if args.show:
        print("\n--- digests as they should be recorded ---")
        for item in out:
            if item["actual"]:
                print(f"{item['actual']}  {Path(item['path']).name}")
    print(f"\n{len(out)} record(s) checked, {len(bad)} problem(s)")
    print("This tool never writes: bring the findings to the agent as a proposal (SKILL 8).")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
