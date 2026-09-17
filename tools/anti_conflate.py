#!/usr/bin/env python3
"""Refuse a text that collapses two things the corpus keeps apart.

  anti_conflate.py <file|dir> ...

Catches the equation forms an accidental collapse actually takes — "X is Y", "X, the Y",
"X (the Y)", "X = Y" — and reports the line. It is deliberately narrow: a sentence that
DISTINGUISHES the two (contains 'not', 'never', 'distinct', 'differs') passes, because
saying they are different is the point.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(open(os.path.join(os.path.dirname(HERE), "spine", "anti_conflation.json")))
KEEPS = ("not ", "never", "distinct", "differs", "differ ", "is no", "≠", "rather than",
         "do not", "must not", "unlike")


def bare(t):
    """Strip the articles and intensifiers a pair term is written with, so the pattern
    matches the sentence rather than the phrasing of the rule."""
    t = re.sub(r"^(?:a|an|the)\s+", "", t.strip(), flags=re.I)
    t = re.sub(r"\s+(?:itself|alone|position)$", "", t, flags=re.I)
    return t


def forms(a, b):
    A, B = re.escape(bare(a)), re.escape(bare(b))
    return [re.compile(rf"\b{A}\s+(?:is|are)\s+(?:just\s+|merely\s+|simply\s+)?(?:a|an|the)?\s*{B}\b", re.I),
            re.compile(rf"\b{A}\s*[,(]\s*(?:a|an|the)?\s*{B}\b", re.I),
            re.compile(rf"\b{A}\s*=\s*{B}\b", re.I)]


def scan(path):
    hits = []
    for line_no, line in enumerate(open(path, errors="replace"), 1):
        low = line.lower()
        if any(k in low for k in KEEPS):
            continue
        for a, b in RULES["pairs"]:
            for rx in forms(a, b):
                if rx.search(line):
                    hits.append((path, line_no, bare(a), bare(b), line.strip()[:90]))
    return hits


def main():
    args = sys.argv[1:]
    if not args:
        print("anti_conflate: give a file or a directory", file=sys.stderr)
        return 3
    files, hits = [], []
    for a in args:
        if os.path.isdir(a):
            for dp, _, fns in os.walk(a):
                if ".git" in dp:
                    continue
                files += [os.path.join(dp, f) for f in fns
                          if f.endswith((".md", ".json", ".html", ".pni", ".txt"))]
        elif os.path.isfile(a):
            files.append(a)
    if not files:
        print(f"anti_conflate: nothing to read at {args}. Looked and found no text files.",
              file=sys.stderr)
        return 3
    for f in files:
        hits += scan(f)
    for p, n, a, b, line in hits:
        print(f"CONFLATION {p}:{n} — '{a}' equated with '{b}'\n    {line}")
    if hits:
        return 1
    print(f"OK no conflation across {len(files)} file(s), {len(RULES['pairs'])} pairs checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
