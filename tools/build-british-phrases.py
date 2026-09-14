"""Build the list of British phrases to flag from hyperreality's British-only word list.

    python tools/build-british-phrases.py BRITISH-ONLY OUTPUT SOURCE

BRITISH-ONLY is data/british_only.json from
https://github.com/hyperreality/American-British-English-Translator, OUTPUT is
where the phrases are written, and SOURCE names the file and commit they came
from, for the header.

Only multi-word phrases are kept. A single British word such as "flat" or
"head" is also an ordinary US word, so flagging it would report US text.
Alternatives written in one entry are split, notes in parentheses are dropped,
and a few phrases that also appear in US technical writing are left out after
review.

This tool is not installed. The file it writes is.
"""
import json
import pathlib
import re
import sys

NOTICE = """(The MIT License)

Copyright (c) 2016

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""

# Phrases that also appear in ordinary US technical writing, so flagging them
# would report US text.
LEFT_OUT_AFTER_REVIEW = {
    "current account", "economy class", "legacy accounts", "nice one", "the gods", "the mains",
}


def phrases_from(entries):
    """The multi-word British phrases named by the word list's entries, sorted."""
    phrases = {phrase for key in entries for phrase in alternatives(key)}
    return sorted(phrase for phrase in phrases if " " in phrase and phrase not in LEFT_OUT_AFTER_REVIEW)


def alternatives(key):
    """Each alternative an entry names, lowercased, without notes in parentheses."""
    without_notes = re.sub(r"\([^)]*\)", "", key)
    for alternative in re.split(r"[,/]", without_notes):
        yield " ".join(alternative.strip().rstrip("!").split()).lower()


def render(phrases, source):
    """The phrases one per line, sorted, after the word list's license notice."""
    header = [f"British phrases to flag, from hyperreality's British-only word list: {source}.", ""]
    header += NOTICE.splitlines()
    return "".join([f"# {line}".rstrip() + "\n" for line in header]
                   + [f"{phrase}\n" for phrase in sorted(phrases)])


def main(argv):
    british_only, output, source = argv
    entries = json.loads(pathlib.Path(british_only).read_text(encoding="utf-8"))
    phrases = phrases_from(entries)
    pathlib.Path(output).write_text(render(phrases, source), encoding="utf-8")
    print(f"{len(phrases)} British phrases written to {output}")


if __name__ == "__main__":
    main(sys.argv[1:])
