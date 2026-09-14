"""Build the British-to-US spelling pairs from the English Speller Database.

    python tools/build-spellings.py SCOWL-PRE OUTPUT SOURCE

SCOWL-PRE is data/scowl-pre.txt from https://github.com/en-wl/wordlist, OUTPUT
is where the pairs are written, and SOURCE names the file and commit they came
from, for the header.

The database marks, for each sense of a word, the spelling American English
prefers (A) and the one British English prefers (B). A British form is written
out only when converting it is safe wherever it appears:

- it has exactly one US form
- American English does not accept it for any sense of any word
- it is ranked at the size the database's author recommends for spell checking,
  so rare and doubtful entries stay out
- it appears on at least one line the author has not marked fixme
- it is not one of the forms left out after review

This tool is not installed. The file it writes is.
"""
import collections
import pathlib
import re
import sys
from typing import NamedTuple

NOTICE = """Copyright 2000-2026 by Kevin Atkinson

Permission to use, copy, modify, distribute, and sell any part of the English
Speller Database (ESDB, previously known as SCOWLv2), or word lists
created from it, is hereby granted without fee, provided that the above
copyright notice appears in all copies and that both the above copyright
notice and this notice appear in supporting documentation.  Kevin Atkinson
makes no representations about the suitability of this database for any
purpose.  It is provided "as is" without express or implied warranty."""

# Sizes run from 35, the most common words, to 85. The author recommends 60 for
# spell checking: the largest size free of misspellings and invalid words.
SPELL_CHECKING_SIZE = 60
UNRANKED = 100

# Real variants that read wrongly once converted: "prise open" would become
# "prize open," the saki monkey would become sake, and Manilla, a town, would
# become Manila.
LEFT_OUT_AFTER_REVIEW = {"prise", "saki", "manilla"}

SPELLING_MARK = re.compile(r"[ABZCD_][.=?v~V\-@x]?")
POS_AND_NOTES = re.compile(r"\s*[<{(].*$")
COMMENT = re.compile(r"\s#")
ANNOTATIONS = "*-@~!†"


class Line(NamedTuple):
    """One line of the database: its spelling marks, its lemma and forms (a
    form written as alternatives is a list of (marks, word)), its size, and
    whether its author marked it fixme."""
    marks: set
    words: list
    size: int
    doubtful: bool


def british_to_us(lines):
    """{british: american} for every pair that is safe to convert everywhere."""
    parsed_groups = [[parse(line) for line in group] for group in groups(lines)]
    accepted_in_us = {word for group in parsed_groups for word in us_accepted(group)}
    americans = collections.defaultdict(set)
    sizes = collections.defaultdict(lambda: UNRANKED)
    confirmed = set()
    for group in parsed_groups:
        for british, american, line in pairs(group):
            americans[british].add(american)
            sizes[british] = min(sizes[british], line.size)
            if not line.doubtful:
                confirmed.add(british)

    def is_safe(british):
        return (len(americans[british]) == 1
                and british not in accepted_in_us
                and sizes[british] <= SPELL_CHECKING_SIZE
                and british in confirmed
                and british not in LEFT_OUT_AFTER_REVIEW)

    return {british: next(iter(us)) for british, us in americans.items() if is_safe(british)}


def render(spellings, source):
    """The pairs as tab-separated lines, sorted, after the database's notice."""
    header = [f"British to US spellings from the English Speller Database: {source}.", ""]
    header += NOTICE.splitlines()
    return "".join([f"# {line}".rstrip() + "\n" for line in header]
                   + [f"{british}\t{american}\n" for british, american in sorted(spellings.items())])


def groups(lines):
    """Runs of lines separated by an empty line. Lines that are only a comment
    are dropped; comments after text stay, for parse to read."""
    group = []
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        if COMMENT.split(line, maxsplit=1)[0].strip():
            group.append(line.rstrip())
        elif group:
            yield group
            group = []
    if group:
        yield group


def parse(line):
    text, *comment = COMMENT.split(line, maxsplit=1)
    parts = split_outside_parentheses(text.rstrip(), ": ")
    marked = len(parts) > 2 and all(SPELLING_MARK.fullmatch(mark) for mark in parts[1].split())
    marks, rest = (set(parts[1].split()), parts[2:]) if marked else (set(), parts[1:])
    lemma = lemma_word(rest[0]) if rest else "-"
    forms = [form(entry) for entry in split_outside_parentheses(rest[1], ", ")] if len(rest) > 1 else []
    return Line(marks, [lemma] + forms, size(parts[0]), "fixme" in "".join(comment).lower())


def size(scowl_info):
    """The smallest size on the line: how common the word is."""
    sizes = [int(number) for number in re.findall(r"\d+", re.sub(r"\[[^\]]*\]", "", scowl_info))]
    return min(sizes, default=UNRANKED)


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
    return re.sub(r"^(?:[-@!] |[@!])", "", word).rstrip(ANNOTATIONS)


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
    line, an American alternative, or a line or alternative with no marks. Case
    is kept, so a capitalized name does not stand in for its common word."""
    for line in group:
        line_accepted = is_american(line.marks) or not line.marks
        for word in line.words:
            if isinstance(word, list):
                yield from (text for alt_marks, text in word
                            if (is_american(alt_marks) or not alt_marks) and line_accepted)
            elif word != "-" and line_accepted:
                yield word


def pairs(group):
    """(british, american, the British line) for the forms that differ between
    American and British lines, and between the alternatives within a form."""
    american_lines = [line for line in group if is_american(line.marks)]
    british_lines = [line for line in group if is_british(line.marks)]
    for american_line, british_line in zip(american_lines, british_lines):
        for american, british in zip(american_line.words, british_line.words):
            if isinstance(american, str) and isinstance(british, str):
                yield from convertible(british, american, british_line)
    for line in group:
        for word in line.words:
            if isinstance(word, list):
                americans = [text for marks, text in word if is_american(marks)]
                britishes = [text for marks, text in word if is_british(marks)]
                for american, british in zip(americans, britishes):
                    yield from convertible(british, american, line)


def convertible(british, american, line):
    if "-" in (british, american) or any(mark in british + american for mark in " '"):
        return
    if british.lower() != american.lower():
        yield british.lower(), american.lower(), line


def main(argv):
    scowl_pre, output, source = argv
    spellings = british_to_us(pathlib.Path(scowl_pre).read_text(encoding="utf-8").splitlines())
    pathlib.Path(output).write_text(render(spellings, source), encoding="utf-8")
    print(f"{len(spellings)} British to US spellings written to {output}")


if __name__ == "__main__":
    main(sys.argv[1:])
