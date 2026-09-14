"""Build the British-to-US spelling pairs from the English Speller Database.

    python tools/build-spellings.py SCOWL-PRE OUTPUT SOURCE

SCOWL-PRE is data/scowl-pre.txt from https://github.com/en-wl/wordlist, OUTPUT
is where the pairs are written, and SOURCE names the file and commit they came
from, for the header.

The database marks, for each sense of a word, the spelling American English
prefers (A) and the one British English prefers (B). A British form is written
out only when it has exactly one US form and is not a spelling American English
accepts anywhere in the database, so converting it is safe wherever it appears.

This tool is not installed. The file it writes is.
"""
import collections
import pathlib
import re
import sys

NOTICE = """Copyright 2000-2026 by Kevin Atkinson

Permission to use, copy, modify, distribute, and sell any part of the English
Speller Database (ESDB, previously known as SCOWLv2), or word lists
created from it, is hereby granted without fee, provided that the above
copyright notice appears in all copies and that both the above copyright
notice and this notice appear in supporting documentation.  Kevin Atkinson
makes no representations about the suitability of this database for any
purpose.  It is provided "as is" without express or implied warranty."""

SPELLING_MARK = re.compile(r"[ABZCD_][.=?v~V\-@x]?")
POS_AND_NOTES = re.compile(r"\s*[<{(].*$")
ANNOTATIONS = "*-@~!†"


def british_to_us(lines):
    """{british: american} for every pair that is safe to convert everywhere."""
    lines_by_group = [[parse(line) for line in group] for group in groups(lines)]
    accepted_in_us = {word for group in lines_by_group for word in us_accepted(group)}
    candidates = collections.defaultdict(set)
    for group in lines_by_group:
        for british, american in pairs(group):
            candidates[british].add(american)
    return {british: next(iter(americans)) for british, americans in candidates.items()
            if len(americans) == 1 and british not in accepted_in_us}


def render(spellings, source):
    """The pairs as tab-separated lines, sorted, after the database's notice."""
    header = [f"British to US spellings from the English Speller Database: {source}.", ""]
    header += NOTICE.splitlines()
    return "".join([f"# {line}".rstrip() + "\n" for line in header]
                   + [f"{british}\t{american}\n" for british, american in sorted(spellings.items())])


def groups(lines):
    """Runs of lines separated by an empty line, with comments removed."""
    group = []
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        text = re.split(r"\s#", line, maxsplit=1)[0].rstrip()
        if text:
            group.append(text)
        elif group:
            yield group
            group = []
    if group:
        yield group


def parse(line):
    """(spelling marks, words) for a line: its lemma, then each form, where a
    form written as alternatives is a list of (marks, word)."""
    parts = split_outside_parentheses(line, ": ")
    marked = len(parts) > 2 and all(SPELLING_MARK.fullmatch(mark) for mark in parts[1].split())
    marks, rest = (set(parts[1].split()), parts[2:]) if marked else (set(), parts[1:])
    lemma = lemma_word(rest[0]) if rest else "-"
    forms = [form(entry) for entry in split_outside_parentheses(rest[1], ", ")] if len(rest) > 1 else []
    return marks, [lemma] + forms


def split_outside_parentheses(text, separator):
    parts, depth, start, index = [], 0, 0, 0
    while index < len(text):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
        elif depth == 0 and text.startswith(separator, index):
            parts.append(text[start:index])
            index += len(separator)
            start = index
            continue
        index += 1
    parts.append(text[start:])
    return parts


def lemma_word(text):
    word = POS_AND_NOTES.sub("", text).strip()
    if word == "-":
        return word
    return re.sub(r"^[-@!] ", "", word).rstrip(ANNOTATIONS)


def form(entry):
    entry = entry.strip()
    if not entry.startswith("("):
        return entry if entry == "-" else entry.rstrip(ANNOTATIONS)
    return [alternative(text) for text in entry.strip("()").split("|")]


def alternative(text):
    marks, _, word = text.strip().rpartition(": ")
    return set(marks.split()), word.strip().rstrip(ANNOTATIONS)


def is_american(marks):
    return "A" in marks


def is_british(marks):
    return "B" in marks and "A" not in marks


def us_accepted(group):
    """Every word in the group that American English accepts: on an American
    line, an American alternative, or a line or alternative with no marks."""
    for marks, words in group:
        line_accepted = is_american(marks) or not marks
        for word in words:
            if isinstance(word, list):
                yield from (text.lower() for alt_marks, text in word
                            if (is_american(alt_marks) or not alt_marks) and line_accepted)
            elif word != "-" and line_accepted:
                yield word.lower()


def pairs(group):
    """(british, american) for the forms that differ between American and British lines,
    and between the alternatives within a form."""
    american_lines = [words for marks, words in group if is_american(marks)]
    british_lines = [words for marks, words in group if is_british(marks)]
    for american_words, british_words in zip(american_lines, british_lines):
        for american, british in zip(american_words, british_words):
            if isinstance(american, str) and isinstance(british, str):
                yield from convertible(british, american)
    for _, words in group:
        for word in words:
            if isinstance(word, list):
                americans = [text for marks, text in word if is_american(marks)]
                britishes = [text for marks, text in word if is_british(marks)]
                for american, british in zip(americans, britishes):
                    yield from convertible(british, american)


def convertible(british, american):
    if "-" in (british, american) or any(mark in british + american for mark in " '"):
        return
    if british.lower() != american.lower():
        yield british.lower(), american.lower()


def main(argv):
    scowl_pre, output, source = argv
    spellings = british_to_us(pathlib.Path(scowl_pre).read_text(encoding="utf-8").splitlines())
    pathlib.Path(output).write_text(render(spellings, source), encoding="utf-8")
    print(f"{len(spellings)} British to US spellings written to {output}")


if __name__ == "__main__":
    main(sys.argv[1:])
