"""Convert British English to US English in the skill text Claude loads.

Plugin skills are written by other people, some in British English, and Claude
picks up the spelling of whatever it reads. Installed as a SessionStart hook, it
reapplies the conversion whenever a plugin update brings British text back:

    python ~/.claude/us-english.py [root ...]

With no roots it patches the installed plugins and ~/.claude/skills. Only
Markdown under a skills, agents or commands folder is touched: that is what
Claude loads. It prints nothing unless it changed a file, because a
SessionStart hook's output is added to Claude's context.

Spellings come from us-english-spellings.tsv beside this script, built from the
English Speller Database by tools/build-spellings.py. It holds only British
forms that have one US form, that American English does not accept, and that
are common enough for spell checking, so a word is converted only when it is
British wherever it appears. British words the data does not carry, such as
whilst, one-off and a few rarer spellings, are listed here.
"""
import pathlib
import re
import sys

CLAUDE = pathlib.Path(__file__).resolve().parent
DEFAULT_ROOTS = (CLAUDE / "plugins" / "cache", CLAUDE / "skills")
LOADED = {"skills", "agents", "commands"}
SPELLINGS_FILE = CLAUDE / "us-english-spellings.tsv"

# A word, or words joined by hyphens, so one-off is looked up whole.
WORD = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")

# British words the spelling data does not carry: vocabulary that is not a
# spelling variant, and spellings ranked rarer than its spell-checking size.
VOCABULARY = {
    "afterwards": "afterward", "bespoke": "custom", "dreamt": "dreamed",
    "encyclopaedia": "encyclopedia", "fortnightly": "biweekly",
    "hypercalcaemia": "hypercalcemia", "one-off": "one-time", "one-offs": "one-time pieces",
    "parallelise": "parallelize", "periodisation": "periodization",
    "postcode": "postal code", "postcodes": "postal codes", "spelt": "spelled",
    "towards": "toward", "tyres": "tires", "whilst": "while",
}


def spellings_from(path):
    """{british: american} from a file of tab-separated pairs that follow # comments."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return dict(line.split("\t") for line in lines if line and not line.startswith("#"))


SPELLINGS = {**spellings_from(SPELLINGS_FILE), **VOCABULARY}


def matching_case(original, replacement):
    """The replacement, capitalized the way the original word was, part by
    part when both are hyphenated alike, so One-Off becomes One-Time."""
    if len(original) > 1 and original.isupper():
        return replacement.upper()
    original_parts, replacement_parts = original.split("-"), replacement.split("-")
    if len(original_parts) != len(replacement_parts):
        return capitalized_like(original, replacement)
    return "-".join(map(capitalized_like, original_parts, replacement_parts))


def capitalized_like(original, replacement):
    if original[:1].isupper() and replacement:
        return replacement[0].upper() + replacement[1:]
    return replacement


def americanize(text):
    """The text with its British spellings and vocabulary replaced by US ones."""
    return WORD.sub(lambda match: americanized(match.group(0)), text)


def americanized(word):
    """The word in US English: whole when it is listed, otherwise part by part
    when it is hyphenated, otherwise as it is."""
    if word.lower() in SPELLINGS:
        return matching_case(word, SPELLINGS[word.lower()])
    if "-" in word:
        return "-".join(americanized(part) for part in word.split("-"))
    return word


def is_loaded_by_claude(root, path):
    parts = (root.name, *path.relative_to(root).parts)
    return (bool(LOADED.intersection(parts))
            and "node_modules" not in parts
            and not any(part.endswith("-workspace") for part in parts))


def patch(root):
    """Rewrite the skill text under root in US English, and name each file changed."""
    changed = []
    for path in sorted(root.rglob("*.md")):
        if not is_loaded_by_claude(root, path):
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        converted = americanize(original)
        if converted != original:
            path.write_text(converted, encoding="utf-8")
            changed.append(path)
    return changed


def main(argv=()):
    roots = [pathlib.Path(arg) for arg in argv] or [root for root in DEFAULT_ROOTS if root.is_dir()]
    changed = [path for root in roots for path in patch(root)]
    if changed:
        print(f"us-english: converted British spelling to US English in {len(changed)} skill files")


if __name__ == "__main__":
    main(sys.argv[1:])
