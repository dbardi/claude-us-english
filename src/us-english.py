"""Convert British English to US English in the skill text Claude loads.

Plugin skills are written by other people, some in British English, and Claude
picks up the spelling of whatever it reads. Installed as a SessionStart hook, it
reapplies the conversion whenever a plugin update brings British text back:

    python ~/.claude/us-english.py [root ...]

With no roots it patches the installed plugins and ~/.claude/skills. Only
Markdown under a skills, agents or commands folder is touched: that is what
Claude loads. It prints nothing unless it changed a file, because a
SessionStart hook's output is added to Claude's context.

Every rule matches whole words, so US words that share a British stem
(organism, analysis, specialist, cancellation) are left alone.
"""
import pathlib
import re
import sys

CLAUDE = pathlib.Path(__file__).resolve().parent
DEFAULT_ROOTS = (CLAUDE / "plugins" / "cache", CLAUDE / "skills")
LOADED = {"skills", "agents", "commands"}

# Verbs spelled -ise, -yse: the stem, then one of these endings, is required,
# so "emphasis", "analysis" and "specialist" never match.
ISE_STEMS = (
    "apologis authoris capitalis categoris centralis criticis crystallis "
    "customis deserialis emphasis finalis formalis generalis globalis "
    "harmonis hypothesis initialis legalis localis materialis maximis memoris "
    "metastasis minimis modernis normalis optimis organis parallelis "
    "parametris periodis personalis prioritis randomis realis recognis "
    "sanitis serialis specialis stabilis standardis summaris synchronis "
    "theoris tokenis utilis visualis analys catalys paralys").split()
ISE_ENDINGS = "e|ed|es|ing|er|ers|ation|ations"

# Nouns spelled -our. "Glamour" is US English too, so it is not here.
OUR_WORDS = (
    "armour behaviour clamour colour endeavour favour flavour harbour honour "
    "humour labour neighbour odour parlour rigour rumour savour splendour "
    "tumour vapour vigour").split()
OUR_ENDINGS = "|s|ed|ing|al|ally|ful|able|ably|ite|ites|hood|hoods|er|ers|less|ist|ists"

# US English does not double the final l of these before an ending.
DOUBLED_L = (
    "cancel channel counsel dial equal fuel funnel jewel label level marvel "
    "model pencil quarrel revel rival signal spiral total travel tunnel").split()
DOUBLED_L_ENDINGS = "ed|ing|er|ers|or|ors|ous"

WORDS = {
    "acknowledgement": "acknowledgment", "acknowledgements": "acknowledgments",
    "aeroplane": "airplane", "aeroplanes": "airplanes",
    "afterwards": "afterward", "ageing": "aging", "aluminium": "aluminum",
    "amongst": "among", "analogue": "analog", "analogues": "analogs",
    "artefact": "artifact", "artefacts": "artifacts", "bespoke": "custom",
    "calibre": "caliber", "catalogue": "catalog", "catalogues": "catalogs",
    "catalogued": "cataloged", "cataloguing": "cataloging",
    "centre": "center", "centres": "centers", "centred": "centered", "centring": "centering",
    "centrepiece": "centerpiece", "centrepieces": "centerpieces",
    "cheque": "check", "cheques": "checks", "defence": "defense", "defences": "defenses",
    "dreamt": "dreamed", "encyclopaedia": "encyclopedia", "enrol": "enroll",
    "enrols": "enrolls", "enrolment": "enrollment", "fibre": "fiber", "fibres": "fibers",
    "fortnightly": "biweekly", "fulfil": "fulfill", "fulfils": "fulfills",
    "fulfilment": "fulfillment", "grey": "gray", "greys": "grays", "greyed": "grayed",
    "greying": "graying", "greyish": "grayish", "instalment": "installment",
    "instalments": "installments", "jewellery": "jewelry", "judgement": "judgment",
    "judgements": "judgments", "learnt": "learned", "licence": "license",
    "licences": "licenses", "litre": "liter", "litres": "liters",
    "manoeuvre": "maneuver", "manoeuvres": "maneuvers", "manoeuvred": "maneuvered",
    "manoeuvring": "maneuvering", "meagre": "meager", "metre": "meter", "metres": "meters",
    "mould": "mold", "moulds": "molds", "moulded": "molded", "moulding": "molding",
    "offence": "offense", "offences": "offenses", "one-off": "one-time", "one-offs": "one-time pieces",
    "paediatric": "pediatric", "postcode": "postal code", "postcodes": "postal codes",
    "practise": "practice", "practises": "practices", "practised": "practiced",
    "practising": "practicing", "pretence": "pretense", "programme": "program",
    "programmes": "programs", "pyjamas": "pajamas", "sceptic": "skeptic",
    "sceptics": "skeptics", "sceptical": "skeptical", "scepticism": "skepticism",
    "skilful": "skillful", "sombre": "somber", "spectre": "specter", "spelt": "spelled",
    "sulphur": "sulfur", "theatre": "theater", "theatres": "theaters",
    "towards": "toward", "tyre": "tire", "tyres": "tires", "whilst": "while",
    "wilful": "willful",
}


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


def rule(pattern, americanized):
    """A whole-word rule: each match is replaced by americanized(match), in the original's case."""
    compiled = re.compile(rf"\b(?:{pattern})\b", re.IGNORECASE)
    return lambda text: compiled.sub(
        lambda match: matching_case(match.group(0), americanized(match)), text)


RULES = (
    rule(rf"({'|'.join(ISE_STEMS)})({ISE_ENDINGS})",
         lambda m: m.group(1).lower()[:-1] + "z" + m.group(2).lower()),
    rule(rf"({'|'.join(OUR_WORDS)})({OUR_ENDINGS})",
         lambda m: m.group(1).lower()[:-2] + "r" + m.group(2).lower()),
    rule(rf"({'|'.join(DOUBLED_L)})l({DOUBLED_L_ENDINGS})",
         lambda m: m.group(1).lower() + m.group(2).lower()),
    rule("|".join(re.escape(word) for word in WORDS),
         lambda m: WORDS[m.group(0).lower()]),
)


def americanize(text):
    """The text with its British spellings replaced by US ones."""
    for apply in RULES:
        text = apply(text)
    return text


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
