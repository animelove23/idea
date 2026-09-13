import unittest
from analysis_skeleton.m1_lexical import LexicalRecorder


class LexicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = LexicalRecorder()

    def test_offsets_repeated_words_and_unicode(self):
        text = '  A red car. The car is red! “Café”  '
        r = self.parser.record("x", text)
        for t in r["tokens"]:
            self.assertEqual(text[t["char_start"]:t["char_end"]], t["text"])
        reds = [t for t in r["tokens"] if t["text"] == "red"]
        self.assertEqual(len(reds), 2)
        self.assertNotEqual(reds[0]["char_start"], reds[1]["char_start"])
        self.assertEqual(r["caption"]["lemma_counts"]["car"], 2)
        self.assertIsNone(r["caption"]["model_token_len"])

    def test_empty_and_punctuation_have_no_density(self):
        for text in ("", "  ", "!!!"):
            r = self.parser.record("x", text)
            self.assertEqual(r["caption"]["word_len"], 0)
            self.assertEqual(r["caption"]["pos_per100"], {})
            self.assertTrue(all(t["relative_position"] is None for t in r["tokens"]))

    def test_boundary_example_is_not_an_accuracy_claim(self):
        r = self.parser.record("x", "Two dogs are beside a wooden table.")
        self.assertEqual(next(t for t in r["tokens"] if t["text"] == "dogs")["lemma"], "dog")
        self.assertEqual(next(t for t in r["tokens"] if t["text"] == "wooden")["upos"], "ADJ")
        self.assertNotIn("facts", r)
