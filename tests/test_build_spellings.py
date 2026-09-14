"""Reading British-to-US spelling pairs out of the English Speller Database.

The database marks, for each sense of a word, which spelling American English
prefers (A) and which British English prefers (B, or Z for the -ize style). A
pair is only safe to convert everywhere when the British form has one US form
and is never itself a preferred American spelling.

The excerpts below are in the database's own format, taken from the kinds of
line that occur in data/scowl-pre.txt.
"""
import unittest

from loader import load

build = load("tools/build-spellings.py")


def pairs_from(text):
    return build.british_to_us(text.splitlines())


class PairsComeFromAmericanAndBritishLines(unittest.TestCase):

    def test_the_lemma_and_its_forms_pair_up(self):
        self.assertEqual(
            {"behaviour": "behavior", "behaviours": "behaviors"},
            pairs_from("35 [12dicts]: A Cv DV: behavior <n>\n"
                       "35 [12dicts]: B C D: behaviour <n>\n"
                       "35 [12dicts]: A Cv DV: - <n>: behaviors\n"
                       "35 [12dicts]: B C D: - <n>: behaviours\n"))

    def test_a_british_spelling_that_american_english_allows_is_still_british(self):
        self.assertEqual(
            {"grey": "gray", "greys": "grays"},
            pairs_from("35 [12dicts]: A Cv: gray <n>: grays\n"
                       "35 [12dicts]: AV B C: grey <n>: greys\n"))

    def test_the_ize_style_british_spelling_shares_the_american_line(self):
        self.assertEqual(
            {"organise": "organize", "organised": "organized", "organising": "organizing"},
            pairs_from("35 [12dicts]: A Z: organize <v>: organized, organizing, -\n"
                       "35 [12dicts]: B: organise <v>: organised, organising, -\n"))

    def test_forms_written_as_alternatives_pair_up(self):
        self.assertEqual(
            {"labelled": "labeled", "labelling": "labeling", "ageing": "aging"},
            pairs_from("35 [12dicts]: label <v>: (A: labeled | B: labelled), (A: labeling | B: labelling), labels\n"
                       "\n"
                       "35 [12dicts]: - <v>: aged, (A Bv C: aging | Av B Cv: ageing), ages\n"))

    def test_groups_are_kept_apart(self):
        # Read as one group, gray and judgement would pair up.
        self.assertEqual(
            {"judgement": "judgment"},
            pairs_from("35 [12dicts]: A: gray <n>\n"
                       "\n"
                       "35 [12dicts]: B Cv: judgement <n>\n"
                       "35 [12dicts]: A Bv C: judgment <n>\n"))


    def test_a_marker_before_the_word_is_not_part_of_it(self):
        self.assertEqual(
            {"anonymise": "anonymize"},
            pairs_from("35 [12dicts]: A Z: !anonymize <v>\n"
                       "35 [12dicts]: B: !anonymise <v>\n"))


class OnlySafePairsAreKept(unittest.TestCase):

    def test_a_british_form_that_american_english_prefers_elsewhere_is_left_out(self):
        self.assertEqual(
            {},
            pairs_from("35 [12dicts]: A B: analogue <n>\n"
                       "\n"
                       "35 [12dicts]: A: analog <aj>\n"
                       "35 [12dicts]: B: analogue <aj>\n"))

    def test_a_capitalized_name_does_not_stop_its_common_word_converting(self):
        self.assertEqual(
            {"grey": "gray"},
            pairs_from("85 [ukacd]: Grey <n/upper>\n"
                       "\n"
                       "35 [12dicts]: A Cv: gray <n>\n"
                       "35 [12dicts]: AV B C: grey <n>\n"))

    def test_a_british_form_with_more_than_one_us_form_is_left_out(self):
        self.assertEqual(
            {},
            pairs_from("35 [12dicts]: A: mat <n>\n"
                       "35 [12dicts]: B: matt <n>\n"
                       "\n"
                       "35 [12dicts]: A: matte <aj>\n"
                       "35 [12dicts]: B: matt <aj>\n"))

    def test_a_form_ranked_above_the_spell_checking_size_is_left_out(self):
        self.assertEqual(
            {},
            pairs_from("70 [3of6]: A Cv: gray <n>\n"
                       "70 [3of6]: AV B C: grey <n>\n"))

    def test_a_form_ranked_at_the_spell_checking_size_is_kept(self):
        self.assertEqual(
            {"grey": "gray"},
            pairs_from("60 [brif] 70 [3of6]: A Cv: gray <n>\n"
                       "60 [brif] 70 [3of6]: AV B C: grey <n>\n"))

    def test_a_form_found_only_on_lines_marked_fixme_is_left_out(self):
        self.assertEqual(
            {},
            pairs_from("60 [brif]: A: perv <n>: pervs\n"
                       "60 [brif]: B: prev <n> # fixme: lemma_rank originally \"-\"\n"))

    def test_a_form_also_found_on_a_line_without_fixme_is_kept(self):
        self.assertEqual(
            {"centre": "center"},
            pairs_from("35 [12dicts]: A: center <v>\n"
                       "35 [12dicts]: B: centre <v> # fixme: check the verb\n"
                       "\n"
                       "35 [12dicts]: A: center <n>\n"
                       "35 [12dicts]: B: centre <n>\n"))

    def test_forms_left_out_after_review_are_never_paired(self):
        for british, american in [("prise", "prize"), ("saki", "sake"), ("manilla", "manila")]:
            with self.subTest(british=british):
                self.assertEqual(
                    {},
                    pairs_from(f"35 [12dicts]: A: {american} <n>\n35 [12dicts]: B: {british} <n>\n"))

    def test_open_compounds_possessives_and_placeholders_are_left_out(self):
        self.assertEqual(
            {},
            pairs_from("70 [3of6]: A: back catalog <n>\n"
                       "70 [3of6]: B: back catalogue <n>\n"
                       "\n"
                       "35 [12dicts]: A: - <n>: gray's\n"
                       "35 [12dicts]: B: - <n>: grey's\n"))

    def test_lines_without_spelling_marks_and_comments_give_nothing(self):
        self.assertEqual(
            {},
            pairs_from("80 [enable]: radiolabel <v>: -, (radiolabeling | radiolabelling), radiolabels"
                       " #! unmarked variants: radiolabeled, radiolabelled\n"
                       "35 [12dicts]: annulus <n>: (annuli | V: annuluses)\n"))


class TheDataFileCarriesItsNotice(unittest.TestCase):
    """The database's license asks for its copyright notice in every copy."""

    def setUp(self):
        self.text = build.render({"grey": "gray", "behaviour": "behavior"}, "en-wl/wordlist data/scowl-pre.txt at 1e5b7d3")

    def test_the_copyright_notice_comes_first(self):
        self.assertIn("Copyright 2000-2026 by Kevin Atkinson", self.text)
        self.assertIn("Permission to use, copy, modify, distribute, and sell", self.text)

    def test_the_source_is_named(self):
        self.assertIn("en-wl/wordlist data/scowl-pre.txt at 1e5b7d3", self.text)

    def test_every_header_line_is_a_comment_and_the_pairs_follow_sorted(self):
        lines = self.text.splitlines()
        data = [line for line in lines if not line.startswith("#")]

        self.assertEqual(["behaviour\tbehavior", "grey\tgray"], data)
        self.assertTrue(lines[0].startswith("#"))


if __name__ == "__main__":
    unittest.main()
