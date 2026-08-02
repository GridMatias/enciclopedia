# `_examples/` — a working encyclopedia, in miniature

Infrastructure, **not knowledge**: this folder is never read as context by an
agent working on your real projects (`_meta/config.json` → `paths.infrastructure`).
It exists for three reasons:

1. **The checks run against real content.** Before this folder existed, the whole
   test suite ran on an empty tree: the linter proved things about itself, not
   about the encyclopedia. CI now lints this vault on every push.
2. **You can see what "done right" looks like** before writing your first page:
   front matter, file map with read-this-when hints, a dataset behind a datasheet,
   a retained original with its checksum, an imported document marked untrusted,
   a restricted page that is linked and never inlined.
3. **The retrieval benchmark needs a corpus.** `_tests/bench_retrieval.py` answers
   30 questions against this vault and reports characters read and hit rate.

## Run everything against it

```bash
python _tools/enc_lint.py   --root _examples      # expected: 0 error
python _tools/enc_verify.py --root _examples      # expected: every record OK
python _tools/enc_index.py  --root _examples --dry-run
python _tools/enc_search.py "resa pannelli" --root _examples
python _tools/enc_pack.py --query "inverter" --root _examples --budget 12000
python _tests/bench_retrieval.py
```

## What is deliberately imperfect

| Where | What | Why it is left in |
|---|---|---|
| `cantiere-solare/_imported/offerta-fornitore/` | the source document contains a sentence addressed to the agent | it is the injection case: quoted, marked `trust: untrusted`, never obeyed |
| `cantiere-solare/README.md` | an open contradiction in the ledger | shows what an approved item whose cascade was refused looks like |

Both are annotated in place. Nothing here is a real supplier, a real price or a
real person: the offer, the plant and the readings are invented.
