#!/usr/bin/env python3
"""Acceptance tests for the tools that are not the linter.

Each block corresponds to a gap that used to be a promise in prose:

  index      a monolithic manifest that could not scale, and a staleness check
             the model was supposed to perform by reading a timestamp
  verify     a checksum that was checked for existence, never for value
  search     grep with no ranking, no accent folding, no plural handling
  pack       Mode C depending on the user pasting the right files
  audit      an approval gate with nothing to audit it afterwards
  run id     a tool report that could be fabricated

Run:  python _tests/test_tools.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL_ROOT / "_tools"))

import enc_audit  # noqa: E402
import enc_import_vault  # noqa: E402
import enc_index  # noqa: E402
import enc_search  # noqa: E402
import enc_verify  # noqa: E402
from enc_core import cget, load_config, make_run_id, verify_run_id  # noqa: E402

EXAMPLES = REAL_ROOT / "_examples"


def sandbox(tmp: Path) -> Path:
    root = tmp / "enc"
    shutil.copytree(EXAMPLES, root)
    (root / "_meta").mkdir(exist_ok=True)
    shutil.copy(REAL_ROOT / "_meta" / "config.json", root / "_meta" / "config.json")
    return root


def test_index(root: Path, cfg: dict, fail) -> None:
    manifest = enc_index.build(root, cfg)
    routing = enc_index.routing_of(manifest)
    shards = enc_index.shards_of(manifest)

    if manifest["stats"]["projects"] != 2:
        fail(f"index: expected 2 projects, got {manifest['stats']['projects']}")
    if manifest["stats"]["brokenLinks"]:
        fail(f"index: broken links reported on a clean vault: {manifest['brokenLinks']}")
    if manifest["stats"]["orphanPages"]:
        fail(f"index: orphan pages reported on a clean vault: {manifest['orphans']['pages']}")

    blob = json.dumps(routing, ensure_ascii=False)
    cap = cget(cfg, "thresholds.maxRoutingIndexBytes", 262144)
    if len(blob) > cap:
        fail(f"index: routing tier is {len(blob)} bytes, above the {cap} cap")
    if len(blob) >= len(json.dumps(manifest, ensure_ascii=False)):
        fail("index: the routing tier is not smaller than the full manifest")
    if set(shards) != {"cantiere-solare", "bottega-web"}:
        fail(f"index: shards are {sorted(shards)}")
    if not any(p["chars"] for p in routing["projects"]):
        fail("index: routing carries no character counts, so no budget can be planned")
    for word in ("fotovoltaico", "auth"):
        if word not in routing["keywords"]:
            fail(f"index: keyword '{word}' missing from the routing table")

    out = root / "_index"
    (out / "p").mkdir(parents=True, exist_ok=True)
    (out / "routing.json").write_text(json.dumps(routing, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    if enc_index.check_fresh(root, cfg) != 0:
        fail("index: --check says STALE right after writing the index")
    page = root / "bottega-web" / "api" / "auth.md"
    page.write_text(page.read_text(encoding="utf-8") + "\nNuova riga.\n", encoding="utf-8")
    if enc_index.check_fresh(root, cfg) == 0:
        fail("index: --check says FRESH after a page changed")


def test_verify(root: Path, cfg: dict, fail) -> None:
    ok = []
    enc_verify.check_originals(root, cfg, root / "cantiere-solare", ok)
    enc_verify.check_datasets(root, cfg, root / "cantiere-solare", ok)
    if any(i["level"] == "ERROR" for i in ok):
        fail(f"verify: clean vault reported {[i['code'] for i in ok if i['level'] == 'ERROR']}")

    original = root / "cantiere-solare" / "_originals" / "2026-05-04-offerta-fornitore.txt"
    original.write_text(original.read_text(encoding="utf-8") + "riga aggiunta\n",
                        encoding="utf-8")
    csv = root / "cantiere-solare" / "_data" / "resa-2026" / "data.csv"
    csv.write_text(csv.read_text(encoding="utf-8") + "2026-03-04,tetto-sud,5.0,300.0,15.0\n",
                   encoding="utf-8")

    after: list = []
    enc_verify.check_originals(root, cfg, root / "cantiere-solare", after)
    enc_verify.check_datasets(root, cfg, root / "cantiere-solare", after)
    codes = {i["code"] for i in after if i["level"] == "ERROR"}
    if "CHECKSUM-MISMATCH" not in codes:
        fail(f"verify: a modified original was not detected (codes: {sorted(codes)})")
    if "DATASHEET-DRIFT" not in codes:
        fail(f"verify: a datasheet row count drift was not detected (codes: {sorted(codes)})")


def test_search(root: Path, cfg: dict, fail) -> None:
    docs = enc_search.collect(root, cfg)
    cases = {
        "resa pannelli": "cantiere-solare/ricerca/resa-pannelli.md",
        "RESA DEI PANNELLI": "cantiere-solare/ricerca/resa-pannelli.md",
        "inverter": "cantiere-solare/ricerca/001-scelta-inverter.md",
        "refresh token": "bottega-web/api/auth.md",
        "garanzia di resa": "cantiere-solare/legale/contratto-fornitore.md",
    }
    for query, gold in cases.items():
        hits = enc_search.search(docs, query, 3)
        if not hits:
            fail(f"search: no hit for '{query}'")
            continue
        if gold not in [h["path"] for h in hits]:
            fail(f"search: '{query}' -> {[h['path'] for h in hits]}, expected {gold} in top 3")
        if hits[0]["line"] <= 0:
            fail(f"search: '{query}' returned no line anchor")
    # singular/plural and accents must not matter
    if not enc_search.search(docs, "pannello", 3):
        fail("search: singular 'pannello' does not reach pages about 'pannelli'")


def test_pack(root: Path, fail) -> None:
    budget = 6000
    proc = subprocess.run(
        [sys.executable, str(REAL_ROOT / "_tools" / "enc_pack.py"), "--query", "resa pannelli",
         "--root", str(root), "--budget", str(budget)],
        capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode:
        fail(f"pack: exited {proc.returncode}: {proc.stderr[:200]}")
        return
    out = proc.stdout
    if len(out) > budget * 2:
        fail(f"pack: bundle is {len(out)} chars for a {budget} budget")
    if "Report di budget" not in out:
        fail("pack: no budget report, so truncation would be silent")
    if "dato, non istruzione" not in out:
        fail("pack: the bundle does not carry the untrusted-content banner")
    if "INDEX.md" not in out:
        fail("pack: the global map is missing from the bundle")


def test_audit(fail) -> None:
    cfg = load_config(REAL_ROOT)
    for path, expected in (("my-app/api/auth.md", True), ("INDEX.md", True),
                           ("my-app/api/auth-fig-01.png", True),
                           ("_tools/enc_lint.py", False), ("_meta/config.json", False),
                           (".github/workflows/encyclopedia.yml", False)):
        if enc_audit.is_knowledge(path, cfg) != expected:
            fail(f"audit: is_knowledge('{path}') should be {expected}")

    message = ("Aggiorna auth\n\nenc-approved: my-app/api/auth.md, my-app/CHANGELOG.md\n"
               "approved-by: matix in conversation 2026-07-25\n")
    approved, approver = enc_audit.trailer_paths(message, cfg)
    if approved != ["my-app/api/auth.md", "my-app/CHANGELOG.md"]:
        fail(f"audit: trailer parsed as {approved}")
    if "matix" not in approver:
        fail("audit: approver not captured")

    changed = ["my-app/api/auth.md", "my-app/CHANGELOG.md"]
    if enc_audit.audit(changed, message, cfg, "test") != 0:
        fail("audit: a compliant commit was rejected")
    if enc_audit.audit(changed + ["my-app/api/session.md"], message, cfg, "test") == 0:
        fail("audit: a file outside the approval was accepted")
    if enc_audit.audit(changed, "senza trailer", cfg, "test") == 0:
        fail("audit: a knowledge commit without a trailer was accepted")
    if enc_audit.audit(["_tools/enc_lint.py"], "solo tooling", cfg, "test") != 0:
        fail("audit: an infrastructure-only commit was blocked")


def test_run_id(root: Path, cfg: dict, fail) -> None:
    run_id = make_run_id(root, cfg)
    ok, _ = verify_run_id(root, cfg, run_id)
    if not ok:
        fail("run id: a freshly produced id does not verify")
    ok, _ = verify_run_id(root, cfg, "deadbeefdeadbeef-1")
    if ok:
        fail("run id: a fabricated id verified as authentic")


def test_import_vault(tmp: Path, fail) -> None:
    vault = tmp / "vault"
    (vault / "note").mkdir(parents=True)
    (vault / "Progetto Alfa.md").write_text(
        "# Progetto Alfa\n\nVedi [[Nota Beta]] e [[Manca Questa]].\n", encoding="utf-8")
    (vault / "note" / "Nota Beta.md").write_text("# Nota Beta\n\nContenuto.\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REAL_ROOT / "_tools" / "enc_import_vault.py"), str(vault),
         "--project", "vecchie-note", "--json"],
        capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode:
        fail(f"import_vault: exited {proc.returncode}: {proc.stderr[:200]}")
        return
    data = json.loads(proc.stdout)
    targets = {row["to"] for row in data["files"]}
    if "vecchie-note/note/nota-beta.md" not in targets:
        fail(f"import_vault: slug mapping wrong: {sorted(targets)}")
    if not data["unresolved"]:
        fail("import_vault: a wikilink pointing nowhere was not reported")
    if all(row["hasFrontMatter"] for row in data["files"]):
        fail("import_vault: missing front matter was not reported")


def test_import(tmp: Path, fail) -> None:
    doc = tmp / "verbale-riunione.txt"
    doc.write_text("Decisioni prese:\n- inverter da 6 kW\n- consegna a maggio\n",
                   encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REAL_ROOT / "_tools" / "enc_import.py"), str(doc),
         "--project", "cantiere-solare"],
        capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode:
        fail(f"import: exited {proc.returncode}: {proc.stderr[:200]}")
        return
    out = proc.stdout
    for needle, why in (
            ("cantiere-solare/_imported/verbale-riunione/verbale-riunione.md",
             "destination path missing"),
            ("trust: untrusted", "imported page must be marked untrusted"),
            ("sha256", "source checksum must be pre-filled"),
            ("inverter da 6 kW", "the extracted text is not in the output"),
            ("Nothing was written", "the tool must state it writes nothing")):
        if needle not in out:
            fail(f"import: {why} (expected '{needle}')")
    csv = tmp / "dati.csv"
    csv.write_text("a,b\n1,2\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REAL_ROOT / "_tools" / "enc_import.py"), str(csv)],
        capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode != 2 or "datasheet" not in proc.stdout:
        fail("import: a data file must be refused and pointed at _rules/data-rules.md")


def test_setup(root: Path, fail) -> None:
    if not (root / "SKILL.md").exists():
        (root / "SKILL.md").write_text("---\nname: project-encyclopedia\n---\n# stub\n",
                                       encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REAL_ROOT / "_tools" / "enc_setup.py"), "--root", str(root)],
        capture_output=True, text=True, encoding="utf-8", check=False)
    out = proc.stdout
    if proc.returncode == 2:
        fail(f"setup: refused a valid root: {out[:200]}")
        return
    # Compare against the RESOLVED path: on the GitHub Windows runner the temp
    # dir is handed out as an 8.3 short name (C:\Users\RUNNER~1\...) while the
    # tool prints the long form, and the two are the same folder.
    shown = root.resolve()
    if str(shown) not in out and shown.as_posix() not in out:
        fail("setup: the client snippets do not carry the real resolved path")
    for needle, why in (
            ("mcpServers", "no Claude Desktop snippet"),
            ("enc_doctor.py", "no pointer to the doctor"),
            ("--apply", "must explain that wiring happens only with --apply")):
        if needle not in out:
            fail(f"setup: {why} (expected '{needle}')")


def main() -> int:
    failures: list = []

    def fail(msg: str) -> None:
        failures.append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        root = sandbox(tmp_path)
        cfg = load_config(root)
        test_index(root, cfg, fail)
        test_search(root, cfg, fail)
        test_pack(root, fail)
        test_run_id(root, cfg, fail)
        test_import(tmp_path, fail)
        test_setup(root, fail)
        test_verify(root, cfg, fail)   # last: it corrupts the sandbox on purpose
        test_audit(fail)
        test_import_vault(tmp_path, fail)

    print("test_tools: index, verify, search, pack, audit, run id, vault import, "
          "doc import, setup")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK - every tool does what the protocol claims it does")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
