# claude-us-english

A Claude Code hook that keeps the skill text Claude reads in US English.

Claude picks up the spelling and phrasing of whatever it reads. Plugin skills
are written by many people, some in British English, so "behaviour",
"labelled" and "different to" in a skill turn up in the code, comments and docs
Claude writes for you. An instruction to write US English helps, but the skill
text keeps setting the opposite example.

`us-english.py` rewrites that text in US English, points out the phrasing only a
person can rewrite, and runs at the start of every session so a plugin update
cannot bring the British text back.

## Requirements

- Claude Code
- Python 3.8+

## Install

Copy the script and its two data files into `~/.claude`:

```
git clone https://github.com/dbardi/claude-us-english
cp claude-us-english/src/us-english.py claude-us-english/src/us-english-spellings.tsv claude-us-english/src/us-english-british-phrases.txt ~/.claude/
```

Then add a `SessionStart` hook to `~/.claude/settings.json`, merging it with any
hooks already there:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/us-english.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Use the absolute path of your Python interpreter if `python3` is not on the
path Claude Code starts hooks with.

To convert straight away rather than at the next session, run it once:

```
python3 ~/.claude/us-english.py
```

## What it changes

Markdown that Claude loads as instructions: every `.md` file under a
`skills`, `agents` or `commands` folder, in the installed plugins
(`~/.claude/plugins/cache`) and in your own `~/.claude/skills`. Changelogs,
READMEs and other plugin docs are left alone, as are `node_modules` and any
`*-workspace` folder.

Pass one or more folders to convert those instead:

```
python3 ~/.claude/us-english.py path/to/skills
```

## How it converts

Each word is looked up in `us-english-spellings.tsv`, about 2,500 British
spellings with their US forms, taken from the
[English Speller Database](https://github.com/en-wl/wordlist), the word list
behind the aspell and hunspell English dictionaries and the successor to
VarCon:

| British | US |
| --- | --- |
| behaviour, colour, armour | behavior, color, armor |
| organise, organisation, analyse | organize, organization, analyze |
| labelled, cancelled, channelled | labeled, canceled, channeled |
| judgement, catalogue, grey, programme | judgment, catalog, gray, program |
| ploughed, cognisance, skilful | plowed, cognizance, skillful |

A British form is in the data only when converting it is safe wherever it
appears. So "analogue", "backwards" and "practised", which US English accepts,
are left as they are, and so are US words that only look British, such as
organism, analysis and specialist. See [Spelling data](#spelling-data) for how
the data is chosen.

A few British words are not in the data: some are vocabulary rather than
spelling variants, and some are rarer spellings the data leaves out. The script
converts these itself: afterwards, bespoke, dreamt, encyclopaedia, fortnightly,
hypercalcaemia, one-off, parallelise, periodisation, postcode, towards, tyres
and whilst.

British phrases with a single US form are rewritten the same way:

| British | US |
| --- | --- |
| different to | different from |
| at the weekend, at weekends | on the weekend, on weekends |
| Monday to Friday | Monday through Friday |
| in future, (at the end of a clause) | in the future, |
| straight away | right away |
| have got to | have to |
| take a decision | make a decision |
| in hospital | in the hospital |

A capitalized word stays capitalized, including each part of a hyphenated one:
One-Off becomes One-Time. Converting is idempotent, so running it every session
costs a quick scan and changes nothing once the text is US English.

## Phrasing for a person to rewrite

Some British phrases have no single US form, because the right one depends on the
sentence. These are never changed. They are reported instead:

- a short list in the script: have a go, fortnight, full stop, was sat, was
  stood, at university, needs fixing, on holiday, chase it up, sense-check,
  rubbish, reckon, fancy a
- `us-english-british-phrases.txt`, about 200 multi-word British phrases such as
  car park, mobile phone, zebra crossing and driving licence, matched in their US
  spelling because a file is converted before it is reviewed

To list each phrase with its file and line, without changing anything:

```
python3 ~/.claude/us-english.py --review
```

## Output

A `SessionStart` hook's output is added to Claude's context, so the script
prints nothing unless it changed a file or found phrasing to review. Each of
those is one line:

```
us-english: converted British spelling to US English in 37 skill files
us-english: 2 British phrasings in skill text need to be rewritten; list them with: python3 ~/.claude/us-english.py --review
```

## Plugin updates

The conversion edits files in the plugin cache, and a plugin update replaces
them with the original text. The hook converts them again at the next session
start.

## Spelling data

`src/us-english-spellings.tsv` is generated by `tools/build-spellings.py` from
`data/scowl-pre.txt` in the English Speller Database, at commit
[`1e5b7d3`](https://github.com/en-wl/wordlist/tree/1e5b7d3a72f47a71da5d28686c1dd4b397178485).
To rebuild it from a newer commit:

```
curl -L -o scowl-pre.txt https://raw.githubusercontent.com/en-wl/wordlist/<commit>/data/scowl-pre.txt
python3 tools/build-spellings.py scowl-pre.txt src/us-english-spellings.tsv "en-wl/wordlist data/scowl-pre.txt at <commit>"
```

The database marks, for each sense of a word, the spelling American English
prefers and the one British English prefers. The build pairs them up, including
forms written as alternatives, and keeps a British form only when:

- it has exactly one US form
- American English does not accept it for any sense of any word; a capitalized
  name does not count, so the surname Grey does not stop grey becoming gray
- it is ranked at size 60 or below, the size the database's author recommends
  for spell checking, on a scale from 35 for the most common words to 85; rarer
  entries include obscure and doubtful pairs
- it appears on at least one line the author has not marked `fixme`
- it is not prise, saki or manilla, which read wrongly once converted: "prise
  open" would become "prize open," the saki monkey would become sake, and
  Manilla, a town, would become Manila

The data carries the database's copyright notice, which it asks to appear in
supporting documentation too:

> Copyright 2000-2026 by Kevin Atkinson
>
> Permission to use, copy, modify, distribute, and sell any part of the English
> Speller Database (ESDB, previously known as SCOWLv2), or word lists
> created from it, is hereby granted without fee, provided that the above
> copyright notice appears in all copies and that both the above copyright
> notice and this notice appear in supporting documentation.  Kevin Atkinson
> makes no representations about the suitability of this database for any
> purpose.  It is provided "as is" without express or implied warranty.

## Phrase data

`src/us-english-british-phrases.txt` is generated by
`tools/build-british-phrases.py` from `data/british_only.json` in
[hyperreality/American-British-English-Translator](https://github.com/hyperreality/American-British-English-Translator),
at commit
[`3ec2a6b`](https://github.com/hyperreality/American-British-English-Translator/tree/3ec2a6b9820f22e4c8d5e9b49871fe1022005527).
To rebuild it from a newer commit:

```
curl -L -o british_only.json https://raw.githubusercontent.com/hyperreality/American-British-English-Translator/<commit>/data/british_only.json
python3 tools/build-british-phrases.py british_only.json src/us-english-british-phrases.txt "hyperreality/American-British-English-Translator data/british_only.json at <commit>"
```

Only multi-word phrases are kept, because a single British word such as "flat"
or "head" is also an ordinary US word. Alternatives written in one entry are
split, notes in parentheses are dropped, and a few phrases that also appear in
US technical writing are left out: current account, economy class, legacy
accounts, nice one, the gods and the mains.

The word list is published under the MIT License, whose notice the phrase file
carries:

> (The MIT License)
>
> Copyright (c) 2016
>
> Permission is hereby granted, free of charge, to any person obtaining
> a copy of this software and associated documentation files (the
> 'Software'), to deal in the Software without restriction, including
> without limitation the rights to use, copy, modify, merge, publish,
> distribute, sublicense, and/or sell copies of the Software, and to
> permit persons to whom the Software is furnished to do so, subject to
> the following conditions:
>
> The above copyright notice and this permission notice shall be
> included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
> EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
> MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
> IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
> CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
> TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
> SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Tests

```
python3 -m unittest discover -s tests
```

No dependencies beyond the standard library.

| Area | Covers |
| --- | --- |
| Conversion | British forms from the data and the vocabulary list, case, hyphenated words, words in a sentence |
| Look-alikes | US words that share a British stem, words US English accepts, and forms left out of the data stay as they are; converting twice changes nothing more |
| Phrasing | phrases with one US form are rewritten, and US sentences with similar words are left alone |
| Flagging | ambiguous phrases and the listed ones are reported, in their US spelling, and US text is not |
| Data files | reading each file past its notice, and that both sit beside the script |
| Building the spelling data | pairing American and British lines and alternatives, keeping groups apart, and leaving out forms US English accepts, forms with several US forms, compounds, possessives, capitalized names, forms ranked above the spell-checking size, forms found only on `fixme` lines, and forms left out after review; the notice comes first |
| Building the phrase data | keeping multi-word phrases, splitting alternatives, dropping notes and punctuation, leaving out phrases common in US text; the notice comes first |
| Scope | skill, agent and command Markdown is rewritten and reviewed; other files are not |
| Hook protocol | silent when nothing changed, one line for conversions, one line for phrasing to review, and `--review` listing each phrase by file and line without changing it |
