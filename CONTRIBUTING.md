# Contributing

The Project Encyclopedia is a protocol and a set of zero-dependency Python tools.
Both are small on purpose: the protocol fits in one file you can read in ten
minutes, the tools together are under 3000 lines. The bar for a change is that
it fixes a real failure and comes with a test that fails without it.

## Before you write anything

1. **Read `SKILL.md` and `AGENTS.md`.** They define the invariants and the
   workflow. A change that breaks an invariant is not a contribution, it is a
   fork.
2. **Check `_tests/scenarios.md`.** If your change touches behaviour, add or
   update a scenario. A scenario is a promise; a missing scenario is a gap.
3. **Run the suite:**

   ```bash
   python _tests/test_frontmatter.py
   python _tests/test_secrets.py
   python _tests/test_lint.py
   python _tests/test_templates.py
   python _tests/test_tools.py
   python _tests/run_scenarios.py --self-test
   python _tests/bench_retrieval.py --min-hit3 0.75
   python _tools/enc_lint.py
   python _tools/enc_lint.py --root _examples
   python _tools/enc_verify.py --root _examples
   python _tools/enc_bootstrap.py --check
   ```

   On Windows without Git Bash, the pre-commit hook has a PowerShell twin:
   `powershell -ExecutionPolicy Bypass -File _tools\hooks\pre-commit.ps1`.

## What a good change looks like

- **Minimal.** One gap, one fix. A change that touches five files to fix one
  thing is five changes; send them separately.
- **Tested.** A new check in the linter comes with a planted defect in
  `test_lint.py` that fails without the check and passes with it. A new tool
  comes with an entry in `test_tools.py`. A protocol change comes with a
  scenario.
- **Documented.** If the change affects what an agent must do, say so in
  `PROTOCOL-CHANGELOG.md` under a `MAJOR` / `MINOR` / `PATCH` heading, and bump
  `version` in `SKILL.md`, `protocolVersion` in `_meta/config.json`, and
  `version` in `_install/systemPrompt.json`. `enc_bootstrap.py --check` will
  tell you if you forgot one.
- **Zero runtime dependencies.** The tools run on Python 3.9+ with the standard
  library only. PyYAML and check-jsonschema are CI-only, used by
  `test_yaml_differential.py` and the schema job; they are never imported by a
  tool.

## The release checklist

A protocol change is not done until (`enc: release`):

1. `version` in `SKILL.md`, `protocolVersion` in `_meta/config.json` and the
   latest entry in `PROTOCOL-CHANGELOG.md` all match.
2. `_install/systemPrompt.json` has been re-aligned
   (`python _tools/enc_bootstrap.py --check`).
3. Every suite listed above passes, on Python 3.9 and 3.12, on Linux and Windows.
4. `python _tools/enc_lint.py` and `python _tools/enc_lint.py --root _examples`
   are clean.
5. The golden scenarios in `_tests/scenarios.md` have been walked - with a new
   scenario for the change itself.

## What we do not want

- **Cosmetic refactors.** Renaming a function that works is not a contribution.
- **Dependencies.** Adding a library to a tool is a fork. The zero-dependency
  rule is what makes the tools portable; it is not a constraint to work around.
- **Silent behaviour changes.** A check that used to warn and now errors is a
  `MAJOR` change, even if the new behaviour is better. Say so.
- **Weakened tests.** A failing test is a bug in the code or a bug in the test;
  it is never a reason to delete the test.

## Filing an issue

Use the issue templates in `.github/ISSUE_TEMPLATE/`. The bug template asks for
the smallest reproduction: a page, a command, the output you got and the output
you expected. The protocol template asks for the scenario that fails. Without a
reproduction, the issue is a feeling, and feelings do not get fixed.
