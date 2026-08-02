#!/usr/bin/env python3
"""Measure retrieval instead of claiming it.

The central thesis of this protocol is that navigating a curated structure beats
dumping a vault into context. It had never been measured. This does, on the sample
vault in `_examples/`, with a fixed query set and gold pages:

    dump       read everything (the cost the protocol exists to avoid)
    ladder     INDEX.md -> project hub -> pages the hub points at
    search     BM25 over the whole vault (_tools/enc_search.py)
    hybrid     routing tier picks the project, then search inside it  <- the protocol

Reported per strategy: characters read per query (a portable proxy for tokens,
~4 chars per token), hit@1 and hit@3 against the gold pages.

    python _tests/bench_retrieval.py
    python _tests/bench_retrieval.py --min-hit3 0.8 --json

Exit 1 when the hybrid strategy falls below --min-hit3: that is the regression
guard for any future change to routing, keywords or ranking.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL_ROOT / "_tools"))

import enc_index  # noqa: E402
import enc_search  # noqa: E402
from enc_core import load_config, read_text, utf8_stdout  # noqa: E402

# query -> the page(s) that actually answer it
QUERIES = {
    "resa dei pannelli a marzo": ["cantiere-solare/ricerca/resa-pannelli.md"],
    "quanto rende in meno la falda nord": ["cantiere-solare/ricerca/resa-pannelli.md"],
    "irraggiamento delle giornate misurate": ["cantiere-solare/ricerca/resa-pannelli.md"],
    "confronto tra le due falde": ["cantiere-solare/ricerca/resa-pannelli.md"],
    "perche due inverter invece di uno": ["cantiere-solare/ricerca/001-scelta-inverter.md"],
    "mppt indipendenti per falda": ["cantiere-solare/ricerca/001-scelta-inverter.md"],
    "alternative scartate per l'inverter": ["cantiere-solare/ricerca/001-scelta-inverter.md"],
    "garanzia di resa del fornitore": ["cantiere-solare/legale/contratto-fornitore.md"],
    "condizioni di pagamento del contratto": ["cantiere-solare/legale/contratto-fornitore.md"],
    "prezzo dei moduli fotovoltaici": [
        "cantiere-solare/_imported/offerta-fornitore/offerta-fornitore.md"],
    "validita dell'offerta": [
        "cantiere-solare/_imported/offerta-fornitore/offerta-fornitore.md"],
    "schema del dataset di resa": ["cantiere-solare/_data/resa-2026/datasheet.md"],
    "unita di misura delle colonne": ["cantiere-solare/_data/resa-2026/datasheet.md"],
    "limiti noti dei dati di resa": ["cantiere-solare/_data/resa-2026/datasheet.md"],
    "dove vivono i refresh token": ["bottega-web/api/auth.md"],
    "durata della sessione del cliente": ["bottega-web/api/auth.md"],
    "cookie httpOnly e xss": ["bottega-web/api/auth.md"],
    # cross-language: the pages are Italian, the question is not
    "where do refresh tokens live": ["bottega-web/api/auth.md"],
    "yield difference between the roof pitches": ["cantiere-solare/ricerca/resa-pannelli.md"],
    "supplier warranty conditions": ["cantiere-solare/legale/contratto-fornitore.md"],
}


def chars_of(root: Path, rel: str) -> int:
    path = root / rel
    return len(read_text(path)) if path.exists() else 0


def strategy_dump(root, cfg, docs, routing, query):
    return [d["path"] for d in docs], sum(d["chars"] for d in docs)


def strategy_ladder(root, cfg, docs, routing, query):
    """INDEX.md, then the hub of every project the hub-level text matches, then the
    pages those hubs link to. A model of the ladder in SKILL.md 5, not the model
    itself: it opens what the file map points at, in hub order."""
    cost = chars_of(root, "INDEX.md")
    opened = []
    terms = set(enc_search.tokenize(query))
    for project in routing["projects"]:
        hub = f"{project['slug']}/README.md"
        cost += chars_of(root, hub)
        hub_doc = next((d for d in docs if d["path"] == hub), None)
        if not hub_doc:
            continue
        # the hub decides: pages whose row mentions a query term
        for doc in docs:
            if not doc["path"].startswith(project["slug"] + "/"):
                continue
            if doc["path"].endswith(("README.md", "CHANGELOG.md")):
                continue
            row_hit = terms & set(enc_search.tokenize(doc["title"]))
            if row_hit and len(opened) < 3:
                opened.append(doc["path"])
                cost += doc["chars"]
    return opened, cost


def strategy_search(root, cfg, docs, routing, query):
    hits = enc_search.search(docs, query, 3)
    return [h["path"] for h in hits], sum(h["chars"] for h in hits)


def pick_project(routing, query):
    terms = set(enc_search.tokenize(query)) | set(
        enc_search.fold(query).replace("'", " ").split())
    scores = {}
    for word, slugs in routing["keywords"].items():
        stem = enc_search.stem(word)
        if word in terms or stem in terms:
            for slug in slugs:
                scores[slug] = scores.get(slug, 0) + 1
    if not scores:
        return None
    best = max(scores.values())
    winners = [slug for slug, score in scores.items() if score == best]
    return winners[0] if len(winners) == 1 else None


def strategy_hybrid(root, cfg, docs, routing, query):
    routing_cost = len(json.dumps(routing, ensure_ascii=False))
    slug = pick_project(routing, query)
    if slug is None:
        return strategy_search(root, cfg, docs, routing, query)[0], routing_cost + sum(
            h["chars"] for h in enc_search.search(docs, query, 3))
    shard = [d for d in docs if d["path"].startswith(slug + "/")]
    shard_cost = 200 + 120 * len(shard)  # the shard record, not the pages
    hits = enc_search.search(shard, query, 3)
    return [h["path"] for h in hits], routing_cost + shard_cost + sum(h["chars"] for h in hits)


STRATEGIES = {
    "dump": strategy_dump,
    "ladder": strategy_ladder,
    "search": strategy_search,
    "hybrid": strategy_hybrid,
}


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Measure retrieval cost and hit rate")
    ap.add_argument("--root", default=str(REAL_ROOT / "_examples"))
    ap.add_argument("--min-hit3", type=float, default=0.75,
                    help="fail below this hit@3 for the hybrid strategy")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    cfg = load_config(root)
    docs = enc_search.collect(root, cfg)
    if not docs:
        print(f"bench_retrieval: no pages under {root}")
        return 2
    routing = enc_index.routing_of(enc_index.build(root, cfg))

    results = {}
    for name, fn in STRATEGIES.items():
        hit1 = hit3 = 0
        cost = 0
        for query, gold in QUERIES.items():
            opened, spent = fn(root, cfg, docs, routing, query)
            cost += spent
            if opened and opened[0] in gold:
                hit1 += 1
            if any(path in gold for path in opened[:3]):
                hit3 += 1
        n = len(QUERIES)
        results[name] = {"charsPerQuery": round(cost / n),
                         "tokensPerQuery": round(cost / n / 4),
                         "hit1": round(hit1 / n, 3), "hit3": round(hit3 / n, 3)}

    if args.json:
        print(json.dumps({"root": root.as_posix(), "queries": len(QUERIES),
                          "pages": len(docs), "results": results}, indent=2))
    else:
        print(f"bench_retrieval: {len(QUERIES)} queries over {len(docs)} pages in {root}\n")
        print(f"{'strategy':10} {'chars/query':>12} {'~tokens':>9} {'hit@1':>7} {'hit@3':>7}")
        for name, res in results.items():
            print(f"{name:10} {res['charsPerQuery']:12} {res['tokensPerQuery']:9} "
                  f"{res['hit1']:7} {res['hit3']:7}")
        dump = results["dump"]["charsPerQuery"] or 1
        hybrid = results["hybrid"]["charsPerQuery"]
        print(f"\nhybrid reads {hybrid * 100 // dump}% of what dumping the vault costs, "
              f"with hit@3 = {results['hybrid']['hit3']}")
        print("Cross-language queries are in the set on purpose: they are where ranking "
              "alone fails and the routing keywords in INDEX.md earn their keep.")

    if results["hybrid"]["hit3"] < args.min_hit3:
        print(f"\nFAIL: hybrid hit@3 {results['hybrid']['hit3']} < {args.min_hit3}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
