# claude-us-english

A Claude Code hook that keeps the skill text Claude reads in US English.

Claude picks up the spelling of whatever it reads. Plugin skills are written by
many people, some in British English, so "behaviour", "labelled" and
"minimise" in a skill turn up in the code, comments and docs Claude writes for
you. An instruction to write US English helps, but the skill text keeps setting
the opposite example.

`us-english.py` rewrites that text in US English, and runs at the start of
every session so a plugin update cannot bring the British spelling back.

## Requirements

- Claude Code
- Python 3.8+

## Install

Copy the script into `~/.claude`:

```
git clone https://github.com/dbardi/claude-us-english
cp claude-us-english/src/us-english.py ~/.claude/
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

| British | US | Rule |
| --- | --- | --- |
| organise, organisation, analyse | organize, organization, analyze | an `-ise` or `-yse` stem followed by an ending |
| behaviour, colour, neighbourhood | behavior, color, neighborhood | `-our` words and their endings |
| labelled, modelling, cancelled | labeled, modeling, canceled | no doubled final `l` before an ending |
| judgement, catalogue, grey, one-off | judgment, catalog, gray, one-time | a list of individual words |

Every rule matches whole words, and the `-ise` rule needs an ending, so US
words that share a British stem stay as they are: organism, analysis,
specialist, realistic, cancellation, emphasis. A capitalized word stays
capitalized, including each part of a hyphenated one: One-Off becomes
One-Time.

Converting is idempotent, so running it every session costs a quick scan and
changes nothing once the text is US English.

## Output

A `SessionStart` hook's output is added to Claude's context, so the script
prints nothing unless it changed a file. When it did, it prints one line:

```
us-english: converted British spelling to US English in 37 skill files
```

## Plugin updates

The conversion edits files in the plugin cache, and a plugin update replaces
them with the original text. The hook converts them again at the next session
start.

## Tests

```
python3 -m unittest discover -s tests
```

No dependencies beyond the standard library.

| Area | Covers |
| --- | --- |
| Conversion | each British form and its US form, case, hyphenated words, words in a sentence |
| Look-alikes | US words that share a British stem are left alone, and converting twice changes nothing more |
| Scope | skill, agent and command Markdown is rewritten; other files are not |
| Hook protocol | silent when nothing changed, one line when something did |
