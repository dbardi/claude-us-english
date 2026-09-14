"""The British phrases to flag, read from hyperreality's British-only word list.

Its keys are sometimes several alternatives in one entry ("barmaid , barman",
"gear-lever / gearstick") or carry notes in parentheses. Only multi-word phrases
are kept for flagging: a single word such as "head" or "flat" would flag
ordinary US text everywhere.
"""
import unittest

from loader import load

build = load("tools/build-british-phrases.py")


def phrases_from(*keys):
    return build.phrases_from({key: "" for key in keys})


class MultiWordPhrasesAreKept(unittest.TestCase):

    def test_a_phrase_is_kept_and_a_single_word_is_not(self):
        self.assertEqual(["car park"], phrases_from("car park", "abseil"))

    def test_alternatives_in_one_entry_are_split(self):
        self.assertEqual(
            ["postage and packing", "provisional driving licence", "provisional licence"],
            phrases_from("postage and packing, p&p",
                         "provisional licence, provisional driving licence"))

    def test_alternatives_that_are_single_words_are_dropped(self):
        self.assertEqual([], phrases_from("barmaid , barman", "gear-lever / gearstick",
                                          "headmaster, headmistress, headteacher, head"))

    def test_notes_in_parentheses_are_not_part_of_the_phrase(self):
        self.assertEqual(["crack on"], phrases_from("crack on(-to)", "jammy (git, cow)",
                                                    "verger (virger, in some churches)"))

    def test_trailing_exclamation_marks_and_extra_spaces_are_dropped(self):
        self.assertEqual(["gordon bennett", "what ho"], phrases_from("gordon bennett!", "what  ho! "))


class PhrasesCommonInUsTextAreLeftOut(unittest.TestCase):

    def test_phrases_left_out_after_review_are_not_flagged(self):
        for phrase in ["nice one", "legacy accounts", "the mains", "the gods",
                       "current account", "economy class"]:
            with self.subTest(phrase=phrase):
                self.assertEqual([], phrases_from(phrase))


class ThePhraseFileCarriesItsNotice(unittest.TestCase):
    """The word list's MIT license asks for its notice in every copy."""

    def setUp(self):
        self.text = build.render(["zebra crossing", "car park"],
                                 "hyperreality/American-British-English-Translator data/british_only.json at 3ec2a6b")

    def test_the_license_notice_comes_first(self):
        self.assertIn("Copyright (c) 2016", self.text)
        self.assertIn("Permission is hereby granted, free of charge", self.text)

    def test_the_source_is_named(self):
        self.assertIn("hyperreality/American-British-English-Translator data/british_only.json at 3ec2a6b", self.text)

    def test_every_header_line_is_a_comment_and_the_phrases_follow_sorted(self):
        lines = self.text.splitlines()

        self.assertEqual(["car park", "zebra crossing"], [line for line in lines if not line.startswith("#")])
        self.assertTrue(lines[0].startswith("#"))


if __name__ == "__main__":
    unittest.main()
