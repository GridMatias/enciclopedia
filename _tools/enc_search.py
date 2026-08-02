#!/usr/bin/env python3
"""Ranked, accent-folded, bilingual search over the encyclopedia.

The protocol's fallback used to be plain grep: no ranking, no accent folding, no
singular/plural, no bridge between a page written in Italian and a question asked
in English - while `_rules/scale-rules.md` 6 *requires* multilingual routing.
This is the missing half of retrieval-by-navigation: navigation finds what you
can name, this finds what you can only describe.

BM25 over weighted fields (title x3, tags x3, headings x2, body x1), standard
library only, no index to maintain: a 5000-page tree scans in a couple of seconds
and the result carries line anchors so the agent can cite precisely.

Usage:
    python _tools/enc_search.py "refresh token"
    python _tools/enc_search.py "resa pannelli" --project cantiere-solare --limit 5
    python _tools/enc_search.py "confidentiality" --json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import enc_fm  # noqa: E402
from enc_core import (is_content_page, iter_paths, load_config, read_text,  # noqa: E402
                      resolve_root, utf8_stdout)

WORD_RE = re.compile(r"[a-z0-9]+")
HEADING_RE = re.compile(r"(?m)^#{1,6}\s+(.+?)\s*$")
STOPWORDS = {
    # italian
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in",
    "con", "su", "per", "tra", "fra", "e", "ed", "o", "ma", "se", "che", "chi",
    "cui", "non", "come", "dove", "quando", "quale", "quali", "del", "della",
    "dei", "delle", "degli", "nel", "nella", "sul", "sulla", "al", "alla", "ai",
    "questo", "questa", "questi", "queste", "essere", "sono", "stato", "piu",
    # english
    "the", "a", "an", "of", "to", "in", "on", "for", "with", "and", "or", "but",
    "is", "are", "was", "were", "be", "been", "it", "its", "this", "that", "these",
    "those", "as", "at", "by", "from", "what", "which", "who", "how", "when",
    "where", "not", "do", "does", "did", "can", "could", "should", "would",
}
SUFFIXES = ("zioni", "zione", "amente", "mente", "ing", "ers", "ed", "es")


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower())
                   if not unicodedata.combining(c))


def stem(word: str) -> str:
    for suffix in SUFFIXES:
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    if len(word) > 4 and word[-1] in "aeio":
        return word[:-1]  # pannello / pannelli, regola / regole
    if len(word) > 4 and word.endswith("s"):
        return word[:-1]
    return word


def tokenize(text: str) -> list:
    return [stem(w) for w in WORD_RE.findall(fold(text))
            if w not in STOPWORDS and len(w) > 1]


def collect(root: Path, cfg: dict, project: str = None) -> list:
    docs = []
    for p, rel in iter_paths(root, cfg):
        if not (p.is_file() and p.suffix == ".md" and is_content_page(rel, cfg)):
            continue
        if project and rel.parts[0] != project:
            continue
        text = read_text(p)
        fm = enc_fm.parse_front_matter(text) or {}
        tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
        title = str(fm.get("title") or rel.stem)
        headings = " ".join(HEADING_RE.findall(text))
        weighted = " ".join([title] * 3 + [" ".join(str(t) for t in tags)] * 3
                            + [headings] * 2 + [text])
        docs.append({
            "path": rel.as_posix(), "title": title, "lang": fm.get("lang", ""),
            "type": fm.get("type", ""), "updated": fm.get("updated", ""),
            "confidentiality": fm.get("confidentiality", ""),
            "chars": len(text), "tokens": tokenize(weighted), "text": text,
        })
    return docs


def search(docs: list, query: str, limit: int = 8) -> list:
    terms = tokenize(query)
    if not terms or not docs:
        return []
    n = len(docs)
    freqs = []
    df: dict = {}
    for doc in docs:
        counts: dict = {}
        for tok in doc["tokens"]:
            counts[tok] = counts.get(tok, 0) + 1
        freqs.append(counts)
        for tok in set(counts):
            df[tok] = df.get(tok, 0) + 1
    avg = sum(len(d["tokens"]) for d in docs) / n
    k1, b = 1.5, 0.75

    scored = []
    for doc, counts in zip(docs, freqs):
        length = len(doc["tokens"]) or 1
        score = 0.0
        hits = 0
        for term in terms:
            tf = counts.get(term, 0)
            if not tf:
                continue
            hits += 1
            idf = math.log(1 + (n - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5))
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * length / avg))
        if not score:
            continue
        score *= 1 + 0.25 * (hits - 1)  # reward covering more of the query
        scored.append((score, doc))
    scored.sort(key=lambda s: (-s[0], s[1]["path"]))

    out = []
    for score, doc in scored[:limit]:
        line_no, excerpt = 0, ""
        for i, line in enumerate(doc["text"].splitlines(), start=1):
            folded = set(tokenize(line))
            if folded & set(terms):
                line_no, excerpt = i, line.strip()[:160]
                break
        out.append({"path": doc["path"], "title": doc["title"], "score": round(score, 3),
                    "lang": doc["lang"], "type": doc["type"], "updated": doc["updated"],
                    "confidentiality": doc["confidentiality"], "chars": doc["chars"],
                    "line": line_no, "excerpt": excerpt})
    return out


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Ranked search over the encyclopedia")
    ap.add_argument("query", nargs="+", help="what you are looking for")
    ap.add_argument("--root", help="encyclopedia root")
    ap.add_argument("--project", help="limit to one project slug")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = resolve_root(args.root)
    cfg = load_config(root)
    query = " ".join(args.query)
    hits = search(collect(root, cfg, args.project), query, args.limit)

    if args.json:
        print(json.dumps({"query": query, "hits": hits}, indent=2, ensure_ascii=False))
        return 0
    if not hits:
        print(f"enc_search: no page matches '{query}'")
        print("Try fewer words, or a synonym in the other language: routing hints in "
              "INDEX.md are what make cross-language questions land.")
        return 0
    print(f"enc_search: {len(hits)} hit(s) for '{query}'\n")
    for h in hits:
        print(f"{h['score']:7.3f}  {h['path']}:L{h['line']}  [{h['lang'] or '?'}] {h['title']}")
        if h["excerpt"]:
            print(f"         {h['excerpt']}")
    print("\nOpen only what you need: cite as `path:L<line>` (SKILL 7.2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
