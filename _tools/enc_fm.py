#!/usr/bin/env python3
"""Front matter parser for the Project Encyclopedia. Zero dependencies.

It parses a **deliberately restricted subset of YAML** and, when it meets
anything outside that subset, it *says so* instead of guessing. That is the
whole point: a best-effort parser on metadata that carries confidentiality,
provenance and checksums turns a loud failure into a silent one.

Supported
---------
- optional UTF-8 BOM, blank lines and HTML comments before the opening `---`
- `key: scalar`            (string, int, float, true/false, null, ISO date)
- `key: "quoted: scalar"`  (quotes required when the value contains ': ')
- `key: [a, b, "c, d"]`    (inline list, quote aware)
- `key:` + `- item` lines  (block list of scalars)
- `key:` + `- sub: value` (block list of mappings, e.g. `inputs:`)
- `key:` + indented `sub: value` lines (nested map, up to MAX_NESTING levels)
- `key: >` / `key: |`      (folded / literal block scalars)
- `#` comments at the start of a line or after whitespace

Rejected, with an explicit problem instead of a wrong value
-----------------------------------------------------------
tabs for indentation, anchors `&`, aliases `*`, merge keys `<<:`, flow maps
`{}`, single-pair maps inside an inline list (`[gen: "x"]`), duplicate keys,
nesting deeper than MAX_NESTING, unquoted `: ` inside a value, unterminated
front matter.

`_tests/test_frontmatter.py` pins the behaviour; the CI job `parser-differential`
compares every parse against PyYAML and fails on any divergence.
"""

from __future__ import annotations

import re

BOM = "\ufeff"
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*)\s*:(.*)$")
INT_RE = re.compile(r"^-?\d+$")
FLOAT_RE = re.compile(r"^-?\d+\.\d+$")
HTML_COMMENT_OPEN = "<!--"
HTML_COMMENT_CLOSE = "-->"
MAX_FM_LINES = 400
# Levels of nesting allowed under a top-level key. Two is what the schema needs
# (experiment -> environment -> scalars); three would be a data model, not metadata.
MAX_NESTING = 2


class Problem:
    __slots__ = ("code", "msg", "line")

    def __init__(self, code: str, msg: str, line: int) -> None:
        self.code, self.msg, self.line = code, msg, line

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{self.code} L{self.line}: {self.msg}>"


class Result:
    __slots__ = ("data", "problems", "found", "body_line")

    def __init__(self, data, problems, found, body_line) -> None:
        self.data = data
        self.problems = problems
        self.found = found          # a front matter block was present
        self.body_line = body_line  # 1-based line where the body starts

    @property
    def ok(self) -> bool:
        return self.found and not self.problems


def _strip_prelude(text: str) -> tuple[str, int]:
    """Drop BOM, leading blank lines and HTML comments. Returns (text, lines_removed).

    Tolerated because every shipped template used to open with a `<!-- TEMPLATE -->`
    banner and PowerShell writes a BOM: both produced a bogus 'no front matter'.
    """
    if text.startswith(BOM):
        text = text[1:]
    removed = 0
    while True:
        stripped = text.lstrip("\n\r\t ")
        removed += text[:len(text) - len(stripped)].count("\n")
        text = stripped
        if text.startswith(HTML_COMMENT_OPEN):
            end = text.find(HTML_COMMENT_CLOSE)
            if end == -1:
                break
            removed += text[:end].count("\n") + 1
            text = text[end + len(HTML_COMMENT_CLOSE):]
            continue
        break
    return text, removed


def _strip_comment(s: str) -> str:
    out, quote = [], None
    for i, ch in enumerate(s):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or s[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _split_items(s: str) -> list:
    items, buf, quote, depth = [], [], None, 0
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            items.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if "".join(buf).strip():
        items.append("".join(buf))
    return [i.strip() for i in items]


def _scalar(raw: str, line: int, problems: list, where: str = "value"):
    s = _strip_comment(raw).strip()
    if not s:
        return None
    if s[0] in "&*" or s.startswith("<<"):
        problems.append(Problem("FM-UNSUPPORTED",
                                f"anchors, aliases and merge keys are not supported ({where})", line))
        return s
    if s.startswith("!!"):
        problems.append(Problem("FM-UNSUPPORTED", f"explicit YAML tags are not supported ({where})", line))
        return s
    if len(s) > 1 and s[0] == s[-1] and s[0] in "\"'":
        inner = s[1:-1]
        if s[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        else:
            inner = inner.replace("''", "'")
        return inner
    if s.startswith("{"):
        problems.append(Problem("FM-UNSUPPORTED", f"flow mappings {{...}} are not supported ({where})", line))
        return s
    if ": " in s or s.endswith(":"):
        problems.append(Problem("FM-UNQUOTED-COLON",
                                f"unquoted ':' in a {where}: write it as \"{s}\"", line))
        return s
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~"):
        return None
    if INT_RE.match(s):
        return int(s)
    if FLOAT_RE.match(s):
        return float(s)
    return s


def _inline_list(raw: str, line: int, problems: list) -> list:
    body = raw.strip()[1:-1].strip()
    if not body:
        return []
    out = []
    for item in _split_items(body):
        if item.startswith("[") or item.startswith("{"):
            problems.append(Problem("FM-UNSUPPORTED", "nested collections inside a list", line))
            out.append(item)
            continue
        stripped = _strip_comment(item).strip()
        unquoted = not (len(stripped) > 1 and stripped[0] == stripped[-1] and stripped[0] in "\"'")
        if unquoted and ":" in stripped:
            problems.append(Problem(
                "FM-UNSUPPORTED",
                f"'{stripped}' is a single-pair mapping inside a list; "
                "quote it or use a nested block", line))
            out.append(stripped)
            continue
        out.append(_scalar(item, line, problems, "list item"))
    return out


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _skippable(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _next_content(raw: list, i: int) -> int:
    while i < len(raw) and _skippable(raw[i]):
        i += 1
    return i


def _block_scalar(raw: list, i: int, style: str, own_indent: int) -> tuple:
    collected, block_indent = [], None
    while i < len(raw):
        line = raw[i]
        if not line.strip():
            collected.append("")
            i += 1
            continue
        indent = _indent_of(line)
        if indent <= own_indent:
            break
        if block_indent is None:
            block_indent = indent
        collected.append(line[block_indent:])
        i += 1
    if style == "|":
        return "\n".join(collected).strip("\n"), i
    return " ".join(part.strip() for part in collected if part.strip()), i


def _value_after_key(raw: list, i: int, indent: int, rest: str, base: int,
                     problems: list, depth: int, where: str):
    """Return (value, next_index) for the text following 'key:'."""
    lineno = base + i
    rest = _strip_comment(rest).strip()
    if rest.rstrip("+-") in (">", "|"):
        return _block_scalar(raw, i + 1, rest[0], indent)
    if rest.startswith("["):
        if not rest.endswith("]"):
            problems.append(Problem("FM-SYNTAX", f"unclosed inline list for {where}", lineno))
        return _inline_list(rest, lineno, problems), i + 1
    if rest:
        return _scalar(rest, lineno, problems, where), i + 1

    nxt = _next_content(raw, i + 1)
    if nxt >= len(raw):
        return None, nxt
    child_indent = _indent_of(raw[nxt])
    child = raw[nxt].strip()
    if child.startswith("- ") and child_indent >= indent:
        return _parse_seq(raw, nxt, child_indent, base, problems, depth)
    if child_indent > indent:
        if depth >= MAX_NESTING:
            problems.append(Problem("FM-DEEP-NESTING",
                                    f"more than {MAX_NESTING} levels of nesting under a "
                                    "top-level key", base + nxt))
            while nxt < len(raw) and (_skippable(raw[nxt]) or _indent_of(raw[nxt]) > indent):
                nxt += 1
            return None, nxt
        return _parse_map(raw, nxt, child_indent, base, problems, depth + 1)
    return None, i + 1


def _parse_seq(raw: list, i: int, indent: int, base: int, problems: list, depth: int) -> tuple:
    items: list = []
    while i < len(raw):
        if _skippable(raw[i]):
            i += 1
            continue
        line_indent = _indent_of(raw[i])
        if line_indent < indent:
            break
        stripped = raw[i].strip()
        if not stripped.startswith("- "):
            if line_indent > indent:
                problems.append(Problem("FM-SYNTAX",
                                        f"cannot parse '{stripped}' inside a list", base + i))
                i += 1
                continue
            break
        rest = _strip_comment(stripped[2:]).strip()
        match = KEY_RE.match(rest)
        if match and not (len(rest) > 1 and rest[0] in "\"'"):
            # '- key: value' opens a mapping item; its siblings are indented further.
            sub_lines = [" " * (indent + 2) + rest]
            j = i + 1
            while j < len(raw) and (_skippable(raw[j]) or _indent_of(raw[j]) > indent):
                sub_lines.append(raw[j])
                j += 1
            if depth >= MAX_NESTING:
                problems.append(Problem("FM-DEEP-NESTING",
                                        f"more than {MAX_NESTING} levels of nesting under a "
                                        "top-level key", base + i))
                items.append(rest)
            else:
                value, _ = _parse_map(sub_lines, 0, indent + 2, base + i, problems, depth + 1)
                items.append(value)
            i = j
            continue
        items.append(_scalar(rest, base + i, problems, "list item"))
        i += 1
    return items, i


def _parse_map(raw: list, i: int, indent: int, base: int, problems: list, depth: int) -> tuple:
    data: dict = {}
    while i < len(raw):
        if _skippable(raw[i]):
            i += 1
            continue
        line_indent = _indent_of(raw[i])
        if line_indent < indent:
            break
        stripped = raw[i].strip()
        if line_indent > indent:
            problems.append(Problem("FM-INDENT",
                                    f"unexpected indentation before '{stripped}'", base + i))
            i += 1
            continue
        if stripped.startswith("- "):
            break
        if stripped.startswith("<<"):
            problems.append(Problem("FM-UNSUPPORTED", "merge keys '<<:' are not supported",
                                    base + i))
            i += 1
            continue
        match = KEY_RE.match(stripped)
        if not match:
            problems.append(Problem("FM-SYNTAX", f"cannot parse '{stripped}' as 'key: value'",
                                    base + i))
            i += 1
            continue
        key = match.group(1)
        if key in data:
            problems.append(Problem("FM-DUPLICATE-KEY",
                                    f"key '{key}' appears twice; the second one would win silently",
                                    base + i))
        value, i = _value_after_key(raw, i, indent, match.group(2), base, problems, depth,
                                    f"value of '{key}'")
        data[key] = value
    return data, i


def parse(text: str) -> Result:
    """Parse the front matter of a Markdown document."""
    problems: list = []
    body, removed = _strip_prelude(text)
    lines = body.splitlines()
    if not lines or lines[0].strip() not in ("---", "---\r"):
        return Result(None, problems, False, removed + 1)

    end = None
    for i in range(1, min(len(lines), MAX_FM_LINES + 1)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        problems.append(Problem("FM-UNTERMINATED",
                                "front matter opened with '---' but never closed", removed + 1))
        return Result(None, problems, True, removed + 1)

    base = removed + 2  # line number of raw[0]
    raw = []
    for offset, line in enumerate(lines[1:end]):
        if line.startswith("\t") or (line[:len(line) - len(line.lstrip())].count("\t")):
            problems.append(Problem("FM-TAB", "tabs cannot be used for indentation in YAML",
                                    base + offset))
            line = line.replace("\t", "  ")
        raw.append(line.rstrip("\r"))

    data, _ = _parse_map(raw, 0, 0, base, problems, 0)
    return Result(data, problems, True, removed + end + 2)


def parse_front_matter(text: str):
    """Compatibility helper: the mapping, or None when there is no front matter."""
    return parse(text).data


def has_front_matter(text: str) -> bool:
    return parse(text).found
