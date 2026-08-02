#!/usr/bin/env python3
"""Bind a knowledge change to the approval that authorised it.

"Nothing is written without your explicit OK" is a behavioural promise: an agent
with write access *can* write. This tool is the part a machine can check
afterwards - the diff must be a **subset** of what was approved.

A commit that touches knowledge (`<project>/**.md`, figures, `INDEX.md`) must
carry a trailer listing the approved paths:

    enc-approved: my-app/api/auth.md, my-app/CHANGELOG.md, INDEX.md
    approved-by: matix in conversation 2026-07-25

Escape hatches, on purpose and visible in history:
    enc-approved: manual        # I edited these files myself, no agent involved
    git commit --no-verify      # and then explain yourself in the message

Usage:
    python _tools/enc_audit.py --commit-msg .git/COMMIT_EDITMSG   # commit-msg hook
    python _tools/enc_audit.py --staged                           # what would be required
    python _tools/enc_audit.py --range HEAD~20..HEAD              # audit history
Exit codes: 0 compliant, 1 violation, 2 git unavailable.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from enc_core import cget, load_config, read_text, reserved_top, resolve_root  # noqa: E402

WILDCARD = {"*", "all", "manual", "none"}


def git(root: Path, *args: str) -> tuple:
    try:
        proc = subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True, check=False)
    except (OSError, FileNotFoundError):
        return 127, "", "git is not available"
    return proc.returncode, proc.stdout, proc.stderr


def is_knowledge(path: str, cfg: dict) -> bool:
    parts = path.split("/")
    if len(parts) == 1:
        return parts[0] in ("INDEX.md",)
    if parts[0] in reserved_top(cfg) or parts[0].startswith("."):
        return False
    suffix = "." + parts[-1].rsplit(".", 1)[-1].lower() if "." in parts[-1] else ""
    return suffix in [".md"] + list(cget(cfg, "extensions.images", []))


def trailer_paths(message: str, cfg: dict) -> tuple:
    key = cget(cfg, "audit.approvalTrailer", "enc-approved")
    who = cget(cfg, "audit.approverTrailer", "approved-by")
    approved, approver = [], ""
    for line in message.splitlines():
        m = re.match(rf"(?i)^\s*{re.escape(key)}\s*:\s*(.+)$", line)
        if m:
            approved += [p.strip() for p in re.split(r"[,\s]+", m.group(1)) if p.strip()]
        m2 = re.match(rf"(?i)^\s*{re.escape(who)}\s*:\s*(.+)$", line)
        if m2:
            approver = m2.group(1).strip()
    return approved, approver


def covered(path: str, approved: list) -> bool:
    for entry in approved:
        if entry in WILDCARD:
            return True
        if entry == path:
            return True
        if entry.endswith("/") and path.startswith(entry):
            return True
        if entry.endswith("/**") and path.startswith(entry[:-2]):
            return True
    return False


def audit(changed: list, message: str, cfg: dict, label: str) -> int:
    knowledge = sorted(p for p in changed if is_knowledge(p, cfg))
    if not knowledge:
        print(f"enc_audit {label}: no knowledge file touched, nothing to approve")
        return 0
    approved, approver = trailer_paths(message, cfg)
    key = cget(cfg, "audit.approvalTrailer", "enc-approved")
    if not approved:
        print(f"enc_audit {label}: BLOCKED - {len(knowledge)} knowledge file(s) changed "
              f"without a '{key}:' trailer")
        for p in knowledge:
            print(f"    {p}")
        print(f"\nAdd to the commit message:\n    {key}: " + ", ".join(knowledge))
        print("    approved-by: <who approved, and when>")
        print("Use 'manual' as the value when no agent was involved.")
        return 1
    missing = [p for p in knowledge if not covered(p, approved)]
    if missing:
        print(f"enc_audit {label}: BLOCKED - these files were changed but not approved:")
        for p in missing:
            print(f"    {p}")
        print(f"\napproved: {', '.join(approved)}")
        print("The diff must be a subset of the approval, never the other way round "
              "(SKILL.md section 8).")
        return 1
    unused = [p for p in approved if p not in WILDCARD and p not in knowledge]
    print(f"enc_audit {label}: OK - {len(knowledge)} knowledge file(s), all approved"
          + (f" (by {approver})" if approver else ""))
    if unused:
        print(f"  note: approved but not changed: {', '.join(unused)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Check that knowledge commits carry their approval")
    ap.add_argument("--root", help="encyclopedia root")
    ap.add_argument("--commit-msg", help="path to the prepared commit message (commit-msg hook)")
    ap.add_argument("--staged", action="store_true", help="report what the commit will require")
    ap.add_argument("--range", dest="rng", help="audit a commit range, e.g. HEAD~10..HEAD")
    args = ap.parse_args()

    root = resolve_root(args.root)
    cfg = load_config(root)
    if not cget(cfg, "audit.knowledgeCommitRequiresApproval", True):
        print("enc_audit: disabled in _meta/config.json (audit.knowledgeCommitRequiresApproval)")
        return 0

    if args.rng:
        code, out, err = git(root, "log", "--format=%H%x00%B%x00", args.rng)
        if code == 127:
            print("enc_audit: git not available")
            return 2
        if code:
            print(f"enc_audit: git log failed: {err.strip()}")
            return 2
        failures = 0
        for chunk in out.split("\x00\n"):
            parts = chunk.split("\x00")
            if len(parts) < 2 or not parts[0].strip():
                continue
            sha, message = parts[0].strip(), parts[1]
            code2, files, _ = git(root, "show", "--pretty=", "--name-only", sha)
            changed = [f for f in files.splitlines() if f.strip()]
            failures += audit(changed, message, cfg, f"{sha[:8]}")
        print(f"\n{failures} commit(s) out of compliance")
        return 1 if failures else 0

    code, out, err = git(root, "diff", "--cached", "--name-only")
    if code == 127:
        print("enc_audit: git not available; skipping")
        return 2
    changed = [f for f in out.splitlines() if f.strip()]
    message = read_text(Path(args.commit_msg)) if args.commit_msg and Path(args.commit_msg).exists() else ""
    if args.staged and not args.commit_msg:
        knowledge = sorted(p for p in changed if is_knowledge(p, cfg))
        if not knowledge:
            print("enc_audit --staged: no knowledge file staged")
            return 0
        key = cget(cfg, "audit.approvalTrailer", "enc-approved")
        print("enc_audit --staged: this commit will need\n    "
              f"{key}: " + ", ".join(knowledge))
        return 0
    return audit(changed, message, cfg, "--commit-msg")


if __name__ == "__main__":
    raise SystemExit(main())
