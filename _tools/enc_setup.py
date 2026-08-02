#!/usr/bin/env python3
"""First run of the starter kit on a new machine.

The kit is the `Enciclopedia` folder itself: the user copies it anywhere on any
disk, points a client at it (or just asks the agent to run `enc: setup`), and
this tool does the deterministic part. It discovers where the folder actually
is and prints the per-client snippets with the REAL path filled in - which is
why nothing in the kit needs a hardcoded location.

By default it only reports and prints (like every other tool). The two wiring
steps that require touching state are applied only with --apply, which is the
user's explicit consent expressed as a flag:

    python _tools/enc_setup.py            # report + client snippets, writes nothing
    python _tools/enc_setup.py --apply    # also: git init, hooks, build the index

Exit codes: 0 ready (or made ready), 1 something still to fix, 2 bad usage.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from enc_core import load_config, resolve_root, utf8_stdout  # noqa: E402


def run(root: Path, cmd: list) -> tuple:
    try:
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, check=False)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except (OSError, FileNotFoundError) as exc:
        return 127, str(exc)


def git_state(root: Path) -> tuple:
    code, out = run(root, ["git", "rev-parse", "--is-inside-work-tree"])
    if code == 127:
        return "no-git", ""
    if code or out.strip() != "true":
        return "no-repo", ""
    _, hooks = run(root, ["git", "config", "--get", "core.hooksPath"])
    return "repo", hooks.strip()


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="First-run setup for the starter kit")
    ap.add_argument("--root", help="encyclopedia root")
    ap.add_argument("--apply", action="store_true",
                    help="apply the wiring steps (git init, hooks, index) instead of printing them")
    args = ap.parse_args()

    root = resolve_root(args.root)
    if not (root / "SKILL.md").exists():
        print(f"enc_setup: no SKILL.md in {root} - run me from inside the Enciclopedia folder")
        return 2
    cfg = load_config(root)
    posix = root.as_posix()
    todo = 0

    print(f"enc_setup: starter kit at  {root}\n")
    print(f"[ok  ] protocol {cfg.get('protocolVersion', '?')} - root resolves to this folder, "
          "no configuration needed for the tools")

    state, hooks = git_state(root)
    if state == "no-git":
        print("[warn] git not installed - the safety net and the approval audit are off; "
              "install git and rerun")
        todo += 1
    elif state == "no-repo":
        if args.apply:
            run(root, ["git", "init"])
            run(root, ["git", "config", "core.hooksPath", "_tools/hooks"])
            run(root, ["git", "add", "-A"])
            run(root, ["git", "commit", "-m", "starter kit: first commit\n\nenc-approved: manual\napproved-by: enc_setup --apply"])
            print("[ok  ] git repository created, hooks wired, first commit made")
        else:
            print("[todo] no git repository - with --apply I will run: git init && "
                  "git config core.hooksPath _tools/hooks && git add -A && git commit")
            todo += 1
    else:
        print("[ok  ] git repository")
        if hooks != "_tools/hooks":
            if args.apply:
                run(root, ["git", "config", "core.hooksPath", "_tools/hooks"])
                print("[ok  ] hooks wired (core.hooksPath=_tools/hooks)")
            else:
                print("[todo] hooks not wired - with --apply I will run: "
                      "git config core.hooksPath _tools/hooks")
                todo += 1
        else:
            print("[ok  ] git hooks (core.hooksPath=_tools/hooks)")

    idx = root / "_index" / "routing.json"
    if idx.exists():
        print("[ok  ] _index/routing.json")
    elif args.apply:
        code, _ = run(root, [sys.executable, "_tools/enc_index.py"])
        print("[ok  ] index built" if code == 0 else "[FAIL] enc_index.py failed")
        todo += 0 if code == 0 else 1
    else:
        print("[todo] index not built - with --apply I will run: python _tools/enc_index.py")
        todo += 1

    print("\n--- point your client at this copy (snippets carry the real path) ---\n")

    print("## Claude Desktop - %APPDATA%\\Claude\\claude_desktop_config.json "
          "(merge, then restart from the tray)\n")
    print(json.dumps({"mcpServers": {"filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(root)]}}}, indent=2))

    print("\n## Windsurf / Codex / Devin (agentic IDEs)\n")
    print(f"Open the folder  {root}  as a workspace: AGENTS.md is picked up by itself.")
    print(f"Devin Knowledge entry: \"Project encyclopedia at {posix} - "
          "read SKILL.md before answering.\"")

    print("\n## ChatGPT desktop / any client with custom instructions\n")
    print("Paste the value of `systemPrompt` from _install/systemPrompt.json into the")
    print(f"project instructions, and tell it once where the folder lives: {posix}")

    print("\n--- next ---\n")
    print("Verify:   python _tools/enc_doctor.py --full")
    print("First project: ask the agent, or: python _tools/enc_new.py --print <slug>")
    if todo and not args.apply:
        print(f"\n{todo} step(s) pending - rerun with --apply to perform them, "
              "or do them by hand.")
    return 1 if todo else 0


if __name__ == "__main__":
    raise SystemExit(main())
