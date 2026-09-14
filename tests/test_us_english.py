"""US English for the skill text Claude loads.

Plugin skills are written by other people, some in British English, and Claude
picks up the spelling of whatever it reads. The conversion has to change the
British forms without touching US words that merely look similar.
"""
import contextlib
import io
import pathlib
import tempfile
import unittest

from loader import load

us_english = load("us-english.py")


class BritishWordsBecomeUsWords(unittest.TestCase):

    def test_each_british_form_becomes_its_us_form(self):
        for british, us in [
                ("behaviour", "behavior"), ("behavioural", "behavioral"),
                ("neighbours", "neighbors"), ("colour", "color"), ("favourite", "favorite"),
                ("honour", "honor"), ("labour", "labor"), ("humour", "humor"),
                ("labelled", "labeled"), ("modelling", "modeling"), ("travelling", "traveling"),
                ("signalled", "signaled"), ("cancelled", "canceled"), ("cancelling", "canceling"),
                ("judgement", "judgment"), ("acknowledgement", "acknowledgment"),
                ("one-off", "one-time"), ("afterwards", "afterward"), ("towards", "toward"),
                ("whilst", "while"), ("amongst", "among"), ("learnt", "learned"),
                ("minimise", "minimize"), ("organisation", "organization"),
                ("recognised", "recognized"), ("generalising", "generalizing"),
                ("optimises", "optimizes"), ("summarise", "summarize"), ("specialised", "specialized"),
                ("analyse", "analyze"), ("analysed", "analyzed"),
                ("catalogue", "catalog"), ("analogue", "analog"), ("centre", "center"),
                ("licence", "license"), ("defence", "defense"), ("offence", "offense"),
                ("grey", "gray"), ("ageing", "aging"), ("sceptical", "skeptical"),
                ("programme", "program"), ("artefact", "artifact"), ("fulfil", "fulfill"),
                ("fulfilment", "fulfillment"), ("skilful", "skillful"),
                ("centrepiece", "centerpiece"), ("centrepieces", "centerpieces"),
                ("one-offs", "one-time pieces"),
                ("hypothesise", "hypothesize"), ("theorise", "theorize"),
                ("periodisation", "periodization"), ("parallelise", "parallelize"),
                ("metastasising", "metastasizing"), ("crystallise", "crystallize"),
                ("funnelling", "funneling")]:
            with self.subTest(british=british):
                self.assertEqual(us, us_english.americanize(british))

    def test_the_case_of_the_original_word_is_kept(self):
        self.assertEqual("Behavior BEHAVIOR behavior",
                         us_english.americanize("Behaviour BEHAVIOUR behaviour"))

    def test_each_capitalized_part_of_a_hyphenated_word_stays_capitalized(self):
        self.assertEqual("One-Time Events", us_english.americanize("One-Off Events"))

    def test_words_inside_a_sentence_are_converted(self):
        self.assertEqual("Their behavior was canceled, and afterward labeled.",
                         us_english.americanize("Their behaviour was cancelled, and afterwards labelled."))


class UsWordsThatLookBritishAreLeftAlone(unittest.TestCase):

    def test_us_words_sharing_a_british_stem(self):
        for word in ["organism", "analysis", "specialist", "cancellation", "emphasis",
                     "realism", "greyhound", "dialogue", "otherwise", "promise",
                     "exercise", "advertise", "modeler", "hypothesis", "metastasis",
                     "theory", "crystal", "funnel"]:
            with self.subTest(word=word):
                self.assertEqual(word, us_english.americanize(word))

    def test_converting_twice_changes_nothing_more(self):
        once = us_english.americanize("The colour of the neighbourhood, minimised.")
        self.assertEqual(once, us_english.americanize(once))


class OnlyTheTextClaudeLoadsIsRewritten(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_skill_agent_and_command_markdown_is_rewritten(self):
        paths = [self.write(relative, "Its behaviour.") for relative in
                 ["plugin/1.0/skills/tdd/SKILL.md", "plugin/1.0/skills/tdd/refs/NOTES.md",
                  "plugin/1.0/agents/reviewer.md", "plugin/1.0/commands/review.md"]]

        us_english.patch(self.root)

        for path in paths:
            with self.subTest(path=path.relative_to(self.root)):
                self.assertEqual("Its behavior.", path.read_text(encoding="utf-8"))

    def test_other_files_are_left_alone(self):
        paths = [self.write(relative, "Its behaviour.") for relative in
                 ["plugin/1.0/CHANGELOG.md", "plugin/1.0/docs/guide.md",
                  "plugin/1.0/skills/tdd/script.py"]]

        us_english.patch(self.root)

        for path in paths:
            with self.subTest(path=path.relative_to(self.root)):
                self.assertEqual("Its behaviour.", path.read_text(encoding="utf-8"))

    def test_patch_names_the_files_it_changed(self):
        changed = self.write("plugin/skills/a/SKILL.md", "Its behaviour.")
        self.write("plugin/skills/b/SKILL.md", "Its behavior.")

        self.assertEqual([changed], us_english.patch(self.root))


class TheHookProtocol(unittest.TestCase):
    """A SessionStart hook's output is added to Claude's context, so the
    script stays silent unless it actually changed something."""

    def run_main(self, root):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            us_english.main([str(root)])
        return output.getvalue()

    def test_nothing_to_change_prints_nothing(self):
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "skills" / "a").mkdir(parents=True)
        (root / "skills" / "a" / "SKILL.md").write_text("Its behavior.", encoding="utf-8")

        self.assertEqual("", self.run_main(root))

    def test_a_change_is_reported_in_one_line(self):
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "skills" / "a").mkdir(parents=True)
        (root / "skills" / "a" / "SKILL.md").write_text("Its behaviour.", encoding="utf-8")

        self.assertEqual(1, len(self.run_main(root).strip().splitlines()))


if __name__ == "__main__":
    unittest.main()
